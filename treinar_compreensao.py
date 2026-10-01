"""Treina do zero o encoder contextual e seus papéis literais com NumPy.

O split de validação é desenvolvimento: pode escolher uma época e ajusta
uma temperatura de confiança. Ele não é um teste cego. Não se consultam
as sondas finais, o conhecimento factual nem conversas do servidor.
O currículo autoral declara seus limites.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time

from compreensao_neural import (CompreensaoNeural, ORIGENS, ROTAS, VERSAO, assinatura_entrada,
                               decodificar_bio, preparar_entrada)


def assinatura(dados):
    return hashlib.sha256(json.dumps(dados, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def assinatura_supervisao(dados):
    """A autoria de respostas não faz parte dos alvos deste encoder."""
    campos = ("id", "split", "familia", "grupo", "contexto", "ato", "spans")
    return assinatura({"atos": dados["atos"], "papeis": dados["papeis"],
                       "exemplos": [{k: e[k] for k in campos} for e in dados["exemplos"]]})


def preparar_dados(dados, baldes=2048, max_atual=96, max_historico=64):
    atos, papeis = dados.get("atos"), dados.get("papeis")
    if (dados.get("versao") != 1 or not isinstance(atos, list) or not isinstance(papeis, list) or
            len(atos) != len(set(atos)) or len(papeis) != len(set(papeis)) or
            not isinstance(dados.get("exemplos"), list)):
        raise ValueError("Currículo contextual inválido")
    grupos = {"treino": [], "validacao": []}
    familias = {k: set() for k in grupos}
    dialogos = {k: set() for k in grupos}
    pares = {k: set() for k in grupos}
    ids = set()
    for exemplo in dados["exemplos"]:
        split = exemplo.get("split")
        if (split not in grupos or exemplo.get("ato") not in atos or
                not isinstance(exemplo.get("id"), str) or exemplo["id"] in ids or
                not isinstance(exemplo.get("familia"), str) or
                not isinstance(exemplo.get("grupo"), str) or not isinstance(exemplo.get("spans"), list)):
            raise ValueError("Exemplo de compreensão inválido")
        ids.add(exemplo["id"])
        contexto = exemplo.get("contexto")
        if not isinstance(contexto, dict):
            raise ValueError("Contexto do currículo inválido")
        texto, historico = contexto.get("mensagem"), contexto.get("historico", [])
        entrada = preparar_entrada(texto, historico, baldes, max_atual, max_historico)
        if not texto.strip() or entrada["contexto_truncado"]:
            raise ValueError("Pedido vazio ou mais longo que o limite de treino")
        etiquetas = [0] * len(entrada["offsets"])
        ocupados = set()
        for span in exemplo["spans"]:
            papel, inicio, fim = span.get("papel"), span.get("inicio"), span.get("fim")
            if (papel not in papeis or not isinstance(inicio, int) or not isinstance(fim, int) or
                    not 0 <= inicio < fim <= len(texto) or span.get("texto") != texto[inicio:fim]):
                raise ValueError("Span de compreensão não é um trecho literal")
            indices = [i for i, offset in enumerate(entrada["offsets"])
                       if offset is not None and offset[0] >= inicio and offset[1] <= fim]
            if (not indices or entrada["offsets"][indices[0]][0] != inicio or
                    entrada["offsets"][indices[-1]][1] != fim or ocupados.intersection(indices)):
                raise ValueError("Spans sobrepostos ou desalinhados aos tokens")
            ocupados.update(indices)
            etiqueta = 1 + 2 * papeis.index(papel)
            for j, indice in enumerate(indices):
                etiquetas[indice] = etiqueta if j == 0 else etiqueta + 1
        chave = assinatura({"mensagem": texto, "historico": historico})
        if chave in pares[split]:
            raise ValueError("Pedido/histórico duplicado na mesma partição")
        pares[split].add(chave)
        familias[split].add(exemplo["familia"])
        dialogos[split].add(exemplo["grupo"])
        grupos[split].append({"exemplo": exemplo, "entrada": entrada, "etiquetas": etiquetas,
                              "ato_indice": atos.index(exemplo["ato"])})
    if (not grupos["treino"] or not grupos["validacao"] or
            familias["treino"] & familias["validacao"] or
            dialogos["treino"] & dialogos["validacao"] or pares["treino"] & pares["validacao"]):
        raise ValueError("Famílias, diálogos ou pedidos misturados entre partições")
    if {c["exemplo"]["ato"] for c in grupos["treino"]} != set(atos):
        raise ValueError("O treino deve cobrir todos os atos declarados")
    return grupos["treino"], grupos["validacao"]


def inicializar(atos, papeis, ocultos=40, embeddings=24, baldes=2048, semente=2718):
    import numpy as np
    rng = np.random.default_rng(semente)
    h, e = ocultos, embeddings
    p = {"E": rng.normal(0, .08, (baldes, e)).astype("float32"),
         "R": rng.normal(0, .08, (len(ORIGENS), e)).astype("float32"),
         "q": rng.normal(0, .06, (2 * h,)).astype("float32"),
         "A": rng.normal(0, .08, (2 * h, len(atos))).astype("float32"),
         "ba": np.zeros(len(atos), dtype="float32"),
         "S": rng.normal(0, .08, (2 * h, 1 + 2 * len(papeis))).astype("float32"),
         "bs": np.zeros(1 + 2 * len(papeis), dtype="float32")}
    p["E"][0] = 0
    for pref in ("a", "b"):
        for g in "zrn":
            p[pref + "W" + g] = rng.normal(0, 1 / math.sqrt(e), (e, h)).astype("float32")
            p[pref + "U" + g] = rng.normal(0, 1 / math.sqrt(h), (h, h)).astype("float32")
            p[pref + "b" + g] = np.zeros(h, dtype="float32")
    return p


def lote(casos):
    import numpy as np
    b, t = len(casos), max(len(c["entrada"]["unidades"]) for c in casos)
    k = max(len(us) for c in casos for us in c["entrada"]["unidades"])
    ids = np.zeros((b, t, k), dtype="int64")
    norma = np.ones((b, t, 1), dtype="float32")
    origens = np.zeros((b, t), dtype="int64")
    mascara = np.zeros((b, t, 1), dtype="float32")
    atuais = np.zeros((b, t), dtype="float32")
    tags = np.zeros((b, t), dtype="int64")
    for i, c in enumerate(casos):
        entrada = c["entrada"]
        for j, us in enumerate(entrada["unidades"]):
            ids[i, j, :len(us)] = us
            norma[i, j, 0] = math.sqrt(len(us))
            mascara[i, j, 0] = 1
            atuais[i, j] = entrada["offsets"][j] is not None
        origens[i, :len(entrada["origens"])] = entrada["origens"]
        tags[i, :len(c["etiquetas"])] = c["etiquetas"]
    alvos = np.asarray([c["ato_indice"] for c in casos])
    return ids, norma, origens, mascara, atuais, tags, alvos


def _recorrencia(p, emb, mascara, pref, inversa=False):
    import numpy as np
    b, t, _ = emb.shape
    h = np.zeros((b, p[pref + "Uz"].shape[0]), dtype=emb.dtype)
    saidas = np.zeros((b, t, h.shape[1]), dtype=emb.dtype)
    caches = []
    ordem = reversed(range(t)) if inversa else range(t)
    for i in ordem:
        x, anterior = emb[:, i], h
        z = 1 / (1 + np.exp(-np.clip(x @ p[pref + "Wz"] + h @ p[pref + "Uz"] + p[pref + "bz"], -40, 40)))
        r = 1 / (1 + np.exp(-np.clip(x @ p[pref + "Wr"] + h @ p[pref + "Ur"] + p[pref + "br"], -40, 40)))
        n = np.tanh(x @ p[pref + "Wn"] + (r * h) @ p[pref + "Un"] + p[pref + "bn"])
        proposta = (1 - z) * h + z * n
        h = proposta * mascara[:, i] + h * (1 - mascara[:, i])
        saidas[:, i] = h
        caches.append((i, x, anterior, z, r, n))
    return saidas, caches


def _retropropagar(p, grad, caches, mascara, dsaidas, pref):
    import numpy as np
    dh = np.zeros((len(mascara), dsaidas.shape[2]), dtype=dsaidas.dtype)
    de = np.zeros((len(mascara), mascara.shape[1], p["E"].shape[1]), dtype=dsaidas.dtype)
    for i, x, anterior, z, r, n in reversed(caches):
        dh += dsaidas[:, i]
        ativo = dh * mascara[:, i]
        seguinte = dh * (1 - mascara[:, i]) + ativo * (1 - z)
        dn = ativo * z * (1 - n * n)
        dz = ativo * (n - anterior) * z * (1 - z)
        drh = dn @ p[pref + "Un"].T
        dr = drh * anterior * r * (1 - r)
        seguinte += drh * r
        for g, dg, rec in (("n", dn, r * anterior), ("z", dz, anterior), ("r", dr, anterior)):
            grad[pref + "W" + g] += x.T @ dg
            grad[pref + "U" + g] += rec.T @ dg
            grad[pref + "b" + g] += dg.sum(axis=0)
            de[:, i] += dg @ p[pref + "W" + g].T
            if g != "n":
                seguinte += dg @ p[pref + "U" + g].T
        dh = seguinte
    return de


def prever_lote(p, dados_lote, mascara_embedding=None, mascara_saida=None, mascara_lexical=None):
    import numpy as np
    ids, norma, origens, mascara, atuais, _, _ = dados_lote
    emb = p["E"][ids].sum(axis=2) / norma
    if mascara_lexical is not None:
        emb *= mascara_lexical
    emb += p["R"][origens]
    if mascara_embedding is not None:
        emb = emb * mascara_embedding
    ida, ca = _recorrencia(p, emb, mascara, "a")
    volta, cb = _recorrencia(p, emb, mascara, "b", True)
    hs = np.concatenate((ida, volta), axis=2)
    if mascara_saida is not None:
        hs = hs * mascara_saida
    scores = hs @ p["q"] - 1e6 * (1 - atuais)
    alpha = np.exp(scores - scores.max(axis=1, keepdims=True))
    alpha /= alpha.sum(axis=1, keepdims=True)
    pool = (hs * alpha[:, :, None]).sum(axis=1)
    logits = pool @ p["A"] + p["ba"]
    atos = np.exp(logits - logits.max(axis=1, keepdims=True))
    atos /= atos.sum(axis=1, keepdims=True)
    logits_tags = hs @ p["S"] + p["bs"]
    tags = np.exp(logits_tags - logits_tags.max(axis=2, keepdims=True))
    tags /= tags.sum(axis=2, keepdims=True)
    return atos, tags, (emb, hs, alpha, pool, ca, cb)


def perda_gradientes(p, dados_lote, peso_spans=.8, pesos_etiquetas=None,
                    mascara_embedding=None, mascara_saida=None, pesos_atos=None,
                    mascara_lexical=None, suavizacao_atos=.1):
    """Entropia cruzada conjunta e BPTT analítica nas duas direções."""
    import numpy as np
    ids, norma, origens, mascara, atuais, ytags, y = dados_lote
    atos, tags, (_, hs, alpha, pool, ca, cb) = prever_lote(p, dados_lote,
                                                       mascara_embedding, mascara_saida, mascara_lexical)
    b, t = ytags.shape
    pos_b, pos_t = np.arange(b)[:, None], np.arange(t)[None, :]
    peso = atuais.copy()
    if pesos_etiquetas is not None:
        peso *= np.asarray(pesos_etiquetas)[ytags]
    denom = max(float(peso.sum()), 1.0)
    pesos_ato = np.ones(b) if pesos_atos is None else np.asarray(pesos_atos)[y]
    norma_atos = max(float(pesos_ato.sum()), 1e-12)
    alvos_atos = np.full_like(atos, suavizacao_atos / atos.shape[1])
    alvos_atos[np.arange(b), y] += 1 - suavizacao_atos
    perda = float(-(np.log(np.maximum(atos, 1e-12)) * alvos_atos * pesos_ato[:, None]).sum() / norma_atos)
    perda -= peso_spans * float((np.log(np.maximum(tags[pos_b, pos_t, ytags], 1e-12)) * peso).sum()) / denom
    grad = {k: np.zeros_like(v) for k, v in p.items()}
    da = atos - alvos_atos
    da *= (pesos_ato / norma_atos)[:, None]
    grad["A"] = pool.T @ da
    grad["ba"] = da.sum(axis=0)
    dpool = da @ p["A"].T
    dh = dpool[:, None, :] * alpha[:, :, None]
    dalpha = (hs * dpool[:, None, :]).sum(axis=2)
    dscore = alpha * (dalpha - (dalpha * alpha).sum(axis=1, keepdims=True))
    grad["q"] = (hs * dscore[:, :, None]).sum(axis=(0, 1))
    dh += dscore[:, :, None] * p["q"][None, None, :]
    dtags = tags.copy()
    dtags[pos_b, pos_t, ytags] -= 1
    dtags *= (peso * peso_spans / denom)[:, :, None]
    grad["S"] = hs.reshape(-1, hs.shape[2]).T @ dtags.reshape(-1, dtags.shape[2])
    grad["bs"] = dtags.sum(axis=(0, 1))
    dh += dtags @ p["S"].T
    if mascara_saida is not None:
        dh *= mascara_saida
    h = hs.shape[2] // 2
    de = _retropropagar(p, grad, ca, mascara, dh[:, :, :h], "a")
    de += _retropropagar(p, grad, cb, mascara, dh[:, :, h:], "b")
    if mascara_embedding is not None:
        de *= mascara_embedding
    np.add.at(grad["R"], origens, de)
    if mascara_lexical is not None:
        de *= mascara_lexical
    flat_ids = ids.reshape(-1)
    for j in range(de.shape[2]):
        ponderados = np.broadcast_to((de[:, :, j] / norma[:, :, 0])[:, :, None], ids.shape)
        grad["E"][:, j] = np.bincount(flat_ids, weights=ponderados.reshape(-1), minlength=p["E"].shape[0])
    grad["E"][0] = 0
    return perda, grad


def _spans_indices(etiquetas, offsets, papeis):
    spans, inicio = [], None
    for i in range(len(etiquetas) + 1):
        tag = etiquetas[i] if i < len(etiquetas) else 0
        if inicio is not None and (tag == 0 or tag % 2 or tag != etiquetas[inicio] + 1):
            spans.append((papeis[(etiquetas[inicio] - 1) // 2], offsets[inicio][0], offsets[i - 1][1]))
            inicio = None
        if tag and tag % 2:
            inicio = i
    return set(spans)


def avaliar(p, casos, atos, papeis, limiar=.65, margem_minima=.15, limiar_span=.55,
            temperatura=1.0):
    import numpy as np
    corretos = aceitos = aceitos_corretos = tags_total = tags_corretas = exatos = 0
    spans_previstos = spans_reais = spans_corretos = 0
    emitidos = emitidos_corretos = pedidos_emitidos_exatos = 0
    erros, por_ato = [], {}
    for inicio in range(0, len(casos), 48):
        batch = casos[inicio:inicio + 48]
        dados_lote = lote(batch)
        ps, pts, _ = prever_lote(p, dados_lote)
        logits_calibrados = np.log(np.maximum(ps, 1e-30)) / temperatura
        ps = np.exp(logits_calibrados - logits_calibrados.max(axis=1, keepdims=True))
        ps /= ps.sum(axis=1, keepdims=True)
        for j, caso in enumerate(batch):
            indices = sorted(range(len(atos)), key=lambda k: ps[j, k], reverse=True)
            obtido, real = indices[0], caso["ato_indice"]
            confianca = float(ps[j, obtido])
            margem = confianca - float(ps[j, indices[1]])
            correto, aceito = obtido == real, confianca >= limiar and margem >= margem_minima
            linha = por_ato.setdefault(atos[real], {"total": 0, "acertos": 0, "aceitos": 0, "aceitos_corretos": 0})
            linha["total"] += 1
            linha["acertos"] += correto
            linha["aceitos"] += aceito
            linha["aceitos_corretos"] += correto and aceito
            corretos += correto
            aceitos += aceito
            aceitos_corretos += correto and aceito
            atuais = [i for i, offset in enumerate(caso["entrada"]["offsets"]) if offset is not None]
            probabilidades = pts[j, atuais].tolist()
            bio = decodificar_bio(probabilidades, papeis)
            alvos = [caso["etiquetas"][i] for i in atuais]
            tags_total += len(alvos)
            tags_corretas += sum(a == b for a, b in zip(bio, alvos))
            offsets = [caso["entrada"]["offsets"][i] for i in atuais]
            previsto, verdade = _spans_indices(bio, offsets, papeis), _spans_indices(alvos, offsets, papeis)
            confiaveis = set()
            for papel, comeco, fim in previsto:
                indices_span = [k for k, offset in enumerate(offsets)
                                if offset[0] >= comeco and offset[1] <= fim]
                confianca_span = math.exp(sum(math.log(max(probabilidades[k][bio[k]], 1e-12))
                                               for k in indices_span) / len(indices_span))
                if confianca_span >= limiar_span:
                    confiaveis.add((papel, comeco, fim))
            emitidos += len(confiaveis)
            emitidos_corretos += len(confiaveis & verdade)
            pedidos_emitidos_exatos += confiaveis == verdade
            spans_previstos += len(previsto)
            spans_reais += len(verdade)
            spans_corretos += len(previsto & verdade)
            exatos += previsto == verdade
            if not correto:
                erros.append({"id": caso["exemplo"]["id"], "mensagem": caso["exemplo"]["contexto"]["mensagem"],
                              "esperado": atos[real], "obtido": atos[obtido],
                              "confianca": confianca, "margem": margem, "aceita": aceito})
    precisao = spans_corretos / max(1, spans_previstos)
    revocacao = spans_corretos / max(1, spans_reais)
    precisao_emitidos = emitidos_corretos / max(1, emitidos)
    revocacao_emitidos = emitidos_corretos / max(1, spans_reais)
    return {"total": len(casos), "acertos": corretos, "aceitos": aceitos, "aceitos_corretos": aceitos_corretos,
            "tokens_bio": tags_total, "tokens_bio_corretos": tags_corretas,
            "pedidos_com_spans_exatos": exatos, "spans_previstos": spans_previstos,
            "spans_reais": spans_reais, "spans_corretos": spans_corretos,
            "precisao_spans": precisao, "revocacao_spans": revocacao,
            "f1_spans": 2 * precisao * revocacao / max(1e-12, precisao + revocacao),
            "spans_emitidos": emitidos, "spans_emitidos_corretos": emitidos_corretos,
            "precisao_spans_emitidos": precisao_emitidos, "revocacao_spans_emitidos": revocacao_emitidos,
            "f1_spans_emitidos": 2 * precisao_emitidos * revocacao_emitidos /
                                max(1e-12, precisao_emitidos + revocacao_emitidos),
            "pedidos_com_spans_emitidos_exatos": pedidos_emitidos_exatos,
            "por_ato": por_ato, "erros": erros}


def calibrar_temperatura(p, casos):
    """Ajusta só uma temperatura com o split de desenvolvimento declarado."""
    import numpy as np
    probabilidades, alvos = [], []
    for inicio in range(0, len(casos), 48):
        batch = casos[inicio:inicio + 48]
        ps, _, _ = prever_lote(p, lote(batch))
        probabilidades.extend(ps.tolist())
        alvos.extend(c["ato_indice"] for c in batch)
    return _calibrar_probabilidades(probabilidades, alvos)


def _calibrar_probabilidades(probabilidades, alvos):
    import numpy as np
    logits = np.log(np.maximum(np.asarray(probabilidades), 1e-30))
    linhas = np.arange(len(alvos))

    def medir(temperatura):
        z = logits / temperatura
        ps = np.exp(z - z.max(axis=1, keepdims=True))
        ps /= ps.sum(axis=1, keepdims=True)
        nll = float(-np.log(np.maximum(ps[linhas, alvos], 1e-30)).mean())
        indices = ps.argmax(axis=1)
        confiancas = ps[linhas, indices]
        acertos = indices == np.asarray(alvos)
        ece = 0.0
        for i in range(10):
            faixa = (confiancas >= i / 10) & (confiancas <= (i + 1) / 10 if i == 9
                                             else confiancas < (i + 1) / 10)
            if faixa.any():
                ece += float(faixa.mean() * abs(confiancas[faixa].mean() - acertos[faixa].mean()))
        return nll, ece

    temperaturas = np.exp(np.linspace(math.log(.5), math.log(5.0), 81))
    melhor = min(temperaturas, key=lambda t: medir(t)[0])
    nll_antes, ece_antes = medir(1.0)
    nll_depois, ece_depois = medir(melhor)
    return {"temperatura": float(melhor), "exemplos": len(alvos),
            "nll_antes": nll_antes, "nll_depois": nll_depois,
            "ece_dez_faixas_antes": ece_antes, "ece_dez_faixas_depois": ece_depois,
            "metodo": "Uma temperatura minimiza entropia cruzada no desenvolvimento. Não muda ranking nem pesos do encoder; não reduz limiares.",
            "uso_do_split": "validacao usada no desenvolvimento e na calibração; não é um teste cego"}


def _representacoes_rota(p, casos, atos):
    import numpy as np
    representacoes, alvos = [], []
    for inicio in range(0, len(casos), 48):
        batch = casos[inicio:inicio + 48]
        _, _, cache = prever_lote(p, lote(batch))
        representacoes.extend(cache[3].tolist())
        for c in batch:
            ato = atos[c["ato_indice"]]
            alvos.append(ROTAS.index(ato if ato in ("consulta", "escrita") else "conversa"))
    return np.asarray(representacoes, dtype="float32"), np.asarray(alvos)


def _probabilidades_rota(p, representacoes, temperatura=1.0):
    import numpy as np
    logits = (representacoes @ p["L"] + p["bl"]) / temperatura
    ps = np.exp(logits - logits.max(axis=1, keepdims=True))
    return ps / ps.sum(axis=1, keepdims=True)


def _avaliar_rota(ps, alvos, limiar=.8, margem=.15):
    import numpy as np
    confusao = np.zeros((len(ROTAS), len(ROTAS)), dtype=int)
    previstos = ps.argmax(axis=1)
    np.add.at(confusao, (alvos, previstos), 1)
    conf = ps.max(axis=1)
    segundos = np.partition(ps, -2, axis=1)[:, -2]
    aceitos = (conf >= limiar) & (conf - segundos >= margem)
    por_rota = {}
    for i, rota in enumerate(ROTAS):
        tp, total, previstos_n = int(confusao[i, i]), int(confusao[i].sum()), int(confusao[:, i].sum())
        por_rota[rota] = {"total": total, "acertos": tp, "previstos": previstos_n,
                          "precisao": tp / max(1, previstos_n), "revocacao": tp / max(1, total),
                          "aceitos": int(((alvos == i) & aceitos).sum()),
                          "previstos_aceitos": int(((previstos == i) & aceitos).sum()),
                          "aceitos_corretos": int(((alvos == i) & (previstos == i) & aceitos).sum())}
        r = por_rota[rota]
        r["precisao_aceitos"] = r["aceitos_corretos"] / max(1, r["previstos_aceitos"])
        r["f1"] = 2 * r["precisao"] * r["revocacao"] / max(1e-12, r["precisao"] + r["revocacao"])
    return {"total": len(alvos), "acertos": int((previstos == alvos).sum()),
            "aceitos": int(aceitos.sum()), "aceitos_corretos": int((aceitos & (previstos == alvos)).sum()),
            "revocacao_macro": sum(r["revocacao"] for r in por_rota.values()) / len(ROTAS),
            "f1_macro": sum(r["f1"] for r in por_rota.values()) / len(ROTAS),
            "baseline_majoritario": {"rota": "conversa", "total": len(alvos),
                                      "acertos": int((alvos == 0).sum()), "revocacao_macro": 1 / len(ROTAS)},
            "matriz_confusao": confusao.tolist(), "ordem_rotas": list(ROTAS), "por_rota": por_rota,
            "limiar": limiar, "margem": margem}


def treinar_rota(p, treino, validacao, atos, semente, passos=300):
    """Head próprio equilibrado; encoder congelado, sem somar 21 classes."""
    import numpy as np
    x, y = _representacoes_rota(p, treino, atos)
    xv, yv = _representacoes_rota(p, validacao, atos)
    media, escala = x.mean(axis=0), np.maximum(x.std(axis=0), .05)
    z = (x - media) / escala
    contador = np.bincount(y, minlength=len(ROTAS))
    if not (contador > 0).all():
        return None
    pesos = len(y) / (len(ROTAS) * contador)
    pesos_casos = pesos[y]
    rng = np.random.default_rng(semente + 1)
    w = rng.normal(0, .02, (x.shape[1], len(ROTAS))).astype("float32")
    b = np.zeros(len(ROTAS), dtype="float32")
    mw, vw, mb, vb = np.zeros_like(w), np.zeros_like(w), np.zeros_like(b), np.zeros_like(b)
    alvos = np.full((len(y), len(ROTAS)), .02 / len(ROTAS), dtype="float32")
    alvos[np.arange(len(y)), y] += .98
    for passo in range(1, passos + 1):
        logits = z @ w + b
        ps = np.exp(logits - logits.max(axis=1, keepdims=True))
        ps /= ps.sum(axis=1, keepdims=True)
        delta = (ps - alvos) * (pesos_casos / pesos_casos.sum())[:, None]
        gw, gb = z.T @ delta + .01 * w, delta.sum(axis=0)
        mw, vw = .9 * mw + .1 * gw, .999 * vw + .001 * gw * gw
        mb, vb = .9 * mb + .1 * gb, .999 * vb + .001 * gb * gb
        w -= .03 * (mw / (1 - .9 ** passo)) / (np.sqrt(vw / (1 - .999 ** passo)) + 1e-8)
        b -= .03 * (mb / (1 - .9 ** passo)) / (np.sqrt(vb / (1 - .999 ** passo)) + 1e-8)
    p["L"] = (w / escala[:, None]).astype("float32")
    p["bl"] = (b - (media / escala) @ w).astype("float32")
    bruto = _probabilidades_rota(p, xv)
    calibracao = _calibrar_probabilidades(bruto, yv)
    temperatura = calibracao["temperatura"]
    return {"aprendizado": {"rotas": list(ROTAS), "passos": passos, "semente": semente + 1,
                            "pesos_classes": pesos.tolist(), "encoder_congelado": True,
                            "regularizacao_l2": .01, "suavizacao_alvos": .02,
                            "limiar_fixo": .8, "margem_fixa": .15,
                            "origem": "Inicialização aleatória própria sobre representação contextual treinada no projeto; nenhum peso externo."},
            "calibracao": calibracao,
            "treino": _avaliar_rota(_probabilidades_rota(p, x, temperatura), y),
            "validacao_sem_calibracao": _avaliar_rota(bruto, yv),
            "validacao": _avaliar_rota(_probabilidades_rota(p, xv, temperatura), yv)}


def treinar(caminho, destino, epocas=90, lote_tamanho=32, ocultos=40, embeddings=24,
            baldes=2048, semente=2718, peso_spans=.8, max_atual=96, max_historico=64,
            checkpoint_progresso=None, retomar=False, dropout=.25, equilibrar_atos=True,
            dropout_trechos=.35, suavizacao_atos=.1, paciencia=0, avaliar_cada=5):
    import numpy as np
    if (not 1 <= epocas <= 1000 or not 1 <= lote_tamanho <= 256 or
            not 8 <= ocultos <= 96 or not 8 <= embeddings <= 64 or not 128 <= baldes <= 8192 or
            not 0 <= peso_spans <= 3 or not 0 <= dropout < .75 or not 0 <= dropout_trechos < 1 or
            not 0 <= suavizacao_atos < .5 or not isinstance(paciencia, int) or paciencia < 0 or
            not isinstance(avaliar_cada, int) or avaliar_cada < 1):
        raise ValueError("Configuração de compreensão fora dos limites")
    inicio = time.monotonic()
    from arquivos_contextuais import ler_json
    dados = ler_json(caminho)
    treino, validacao = preparar_dados(dados, baldes, max_atual, max_historico)
    atos, papeis = dados["atos"], dados["papeis"]
    p = inicializar(atos, papeis, ocultos, embeddings, baldes, semente)
    contador = Counter(etiqueta for c in treino for i, etiqueta in enumerate(c["etiquetas"])
                       if c["entrada"]["offsets"][i] is not None)
    frequencia_o = max(1, contador[0])
    pesos_etiquetas = [min(4.0, math.sqrt(frequencia_o / max(1, contador[i])))
                      for i in range(1 + 2 * len(papeis))]
    contador_atos = Counter(c["ato_indice"] for c in treino)
    pesos_atos = [min(5.0, math.sqrt(len(treino) / (len(atos) * contador_atos[i])))
                 for i in range(len(atos))] if equilibrar_atos else None
    m, v = ({k: np.zeros_like(a) for k, a in p.items()} for _ in range(2))
    rng, passo, perdas, primeira_epoca = np.random.default_rng(semente), 0, [], 0
    melhores_pesos, melhor_medida, melhor_epoca, sem_melhora = None, -1.0, 0, 0
    desenvolvimento = []
    supervisao_sha = assinatura_supervisao(dados)
    configuracao = {"supervisao": supervisao_sha, "lote": lote_tamanho,
                   "ocultos": ocultos, "embeddings": embeddings, "baldes": baldes,
                   "semente": semente, "peso_spans": peso_spans,
                   "max_atual": max_atual, "max_historico": max_historico,
                   "dropout": dropout, "equilibrar_atos": equilibrar_atos,
                   "dropout_trechos": dropout_trechos,
                   "suavizacao_atos": suavizacao_atos,
                   "paciencia": paciencia, "avaliar_cada": avaliar_cada,
                   "assinatura_entrada": assinatura_entrada()}
    if retomar:
        if not checkpoint_progresso:
            raise ValueError("Retomada exige um checkpoint próprio de progresso")
        with np.load(checkpoint_progresso, allow_pickle=False) as salvo:
            estado = json.loads(str(salvo["estado"].item()))
            if estado.get("configuracao") != configuracao:
                raise ValueError("Checkpoint de progresso pertence a outro treino")
            for prefixo, colecao in (("p_", p), ("m_", m), ("v_", v)):
                for k, esperado in colecao.items():
                    obtido = salvo[prefixo + k]
                    if obtido.shape != esperado.shape or not np.isfinite(obtido).all():
                        raise ValueError("Checkpoint de progresso corrompido")
                    colecao[k] = obtido.copy()
            primeira_epoca, passo, perdas = estado["epocas"], estado["passo"], estado["perdas"]
            if not 0 <= primeira_epoca <= epocas or len(perdas) != primeira_epoca:
                raise ValueError("Épocas do checkpoint de progresso inválidas")
            rng.bit_generator.state = estado["rng"]
            desenvolvimento = estado.get("desenvolvimento", [])
            melhor_medida, melhor_epoca = estado.get("melhor_medida", -1.0), estado.get("melhor_epoca", 0)
            sem_melhora = estado.get("sem_melhora", 0)
            if melhor_epoca:
                melhores_pesos = {k: salvo["melhor_" + k].copy() for k in p}
    for epoca in range(primeira_epoca, epocas):
        ordem, epoca_perdas = rng.permutation(len(treino)), []
        for i in range(0, len(ordem), lote_tamanho):
            batch = [treino[j] for j in ordem[i:i + lote_tamanho]]
            mascara_e = (rng.random((len(batch), 1, embeddings)) >= dropout).astype("float32") / (1 - dropout)
            mascara_h = (rng.random((len(batch), 1, 2 * ocultos)) >= dropout).astype("float32") / (1 - dropout)
            dados_batch = lote(batch)
            mascara_l = np.where((dados_batch[5] > 0) &
                                 (rng.random(dados_batch[5].shape) < dropout_trechos), 0, 1).astype("float32")[:, :, None]
            perda, grad = perda_gradientes(p, dados_batch, peso_spans, pesos_etiquetas,
                                          mascara_e, mascara_h, pesos_atos, mascara_l, suavizacao_atos)
            epoca_perdas.append(perda)
            norma = math.sqrt(sum(float((g * g).sum()) for g in grad.values()))
            escala, passo = min(1.0, 5 / max(norma, 1e-12)), passo + 1
            for k in p:
                g = grad[k] * escala
                m[k] = .9 * m[k] + .1 * g
                v[k] = .999 * v[k] + .001 * g * g
                p[k] -= .003 * (m[k] / (1 - .9 ** passo)) / (np.sqrt(v[k] / (1 - .999 ** passo)) + 1e-8)
                if p[k].ndim == 2:
                    p[k] *= 1 - .003 * .0005
            p["E"][0] = 0
        media = sum(epoca_perdas) / len(epoca_perdas)
        perdas.append(media)
        if epoca == 0 or (epoca + 1) % 5 == 0:
            print("Época", epoca + 1, "perda treino", round(media, 5),
                  "segundos", round(time.monotonic() - inicio, 1), flush=True)
        if paciencia and ((epoca + 1) % avaliar_cada == 0 or epoca + 1 == epocas):
            medicao = avaliar(p, validacao, atos, papeis)
            macro = sum(a["acertos"] / a["total"] for a in medicao["por_ato"].values()) / len(atos)
            medida = (macro + medicao["f1_spans_emitidos"]) / 2
            desenvolvimento.append({"epoca": epoca + 1, "acuracia_macro_atos": macro,
                                    "f1_spans_emitidos": medicao["f1_spans_emitidos"],
                                    "medida_conjunta": medida})
            print("Desenvolvimento", epoca + 1, "macro atos", round(macro, 4),
                  "F1 trechos", round(medicao["f1_spans_emitidos"], 4), flush=True)
            if medida > melhor_medida + 1e-4:
                melhor_medida, melhor_epoca, sem_melhora = medida, epoca + 1, 0
                melhores_pesos = {k: a.copy() for k, a in p.items()}
            else:
                sem_melhora += 1
        if checkpoint_progresso and ((epoca + 1) % 5 == 0 or epoca + 1 == epocas):
            estado = {"configuracao": configuracao, "epocas": epoca + 1, "passo": passo,
                      "perdas": perdas, "rng": rng.bit_generator.state,
                      "desenvolvimento": desenvolvimento, "melhor_medida": melhor_medida,
                      "melhor_epoca": melhor_epoca, "sem_melhora": sem_melhora}
            arrays = {prefixo + k: a for prefixo, colecao in
                      (("p_", p), ("m_", m), ("v_", v)) for k, a in colecao.items()}
            if melhores_pesos is not None:
                arrays.update({"melhor_" + k: a for k, a in melhores_pesos.items()})
            temporario = Path(str(checkpoint_progresso) + ".tmp.npz")
            np.savez_compressed(str(temporario), estado=json.dumps(estado), **arrays)
            temporario.replace(checkpoint_progresso)
        if paciencia and sem_melhora >= paciencia:
            print("Parada por desenvolvimento; época escolhida", melhor_epoca, flush=True)
            break
    if melhores_pesos is not None:
        p = melhores_pesos
    rota = treinar_rota(p, treino, validacao, atos, semente)
    calibracao = calibrar_temperatura(p, validacao)
    checkpoint = {"versao": 1, "arquitetura": VERSAO, "assinatura_entrada": assinatura_entrada(),
                  "atos": atos, "papeis": papeis, "ocultos": ocultos, "embeddings": embeddings,
                  "baldes": baldes, "max_atual": max_atual, "max_historico": max_historico,
                  "limiar": .65, "margem_minima": .15, "limiar_span": .55,
                  "temperatura": calibracao["temperatura"], "calibracao": calibracao,
                  "limiar_rota": .8, "margem_rota": .15,
                  "temperatura_rota": rota["calibracao"]["temperatura"] if rota else 1.0,
                  "rota": rota,
                  "assinatura_treino": assinatura([c["exemplo"] for c in treino]),
                  "assinatura_supervisao": supervisao_sha,
                  "assinatura_curriculo": assinatura(dados), "pesos": {k: a.tolist() for k, a in p.items()},
                  "treino": {"epocas": len(perdas), "epocas_maximas": epocas,
                             "epoca_selecionada": melhor_epoca or len(perdas),
                             "paciencia": paciencia, "avaliar_cada": avaliar_cada,
                             "desenvolvimento": desenvolvimento,
                             "selecao": "Média da acurácia macro de atos e F1 de trechos emitidos no desenvolvimento" if paciencia else "Época final fixa",
                             "lote": lote_tamanho, "semente": semente,
                             "otimizador": "Adam", "taxa_aprendizado": .003,
                             "clip_gradiente": 5.0, "decaimento_matrizes": .0005,
                             "peso_spans": peso_spans, "pesos_etiquetas": pesos_etiquetas,
                             "dropout": dropout, "pesos_atos": pesos_atos,
                             "dropout_trechos": dropout_trechos,
                             "suavizacao_atos": suavizacao_atos,
                             "exemplos": len(treino), "parametros": sum(a.size for a in p.values()),
                             "familias": len({c["exemplo"]["familia"] for c in treino}),
                             "grupos": len({c["exemplo"]["grupo"] for c in treino}),
                             "perdas": perdas, "segundos": time.monotonic() - inicio,
                             "origem": "inicialização aleatória própria; nenhum peso externo"}}
    CompreensaoNeural(checkpoint)
    Path(destino).write_text(json.dumps(checkpoint, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return {"arquitetura": VERSAO, "parametros": checkpoint["treino"]["parametros"],
            "assinatura_treino": checkpoint["assinatura_treino"],
            "assinatura_supervisao": supervisao_sha,
            "assinatura_curriculo": checkpoint["assinatura_curriculo"],
            "calibracao": calibracao,
            "rota": rota,
            "treino": avaliar(p, treino, atos, papeis, temperatura=calibracao["temperatura"]),
            "validacao_sem_calibracao": avaliar(p, validacao, atos, papeis),
            "validacao": avaliar(p, validacao, atos, papeis, temperatura=calibracao["temperatura"]),
            "limite": "Desenvolvimento autoral com famílias e diálogos separados, usado para calibração e escolha de configuração. Não é teste cego. Mede atos e trechos literais, não inteligência geral nem veracidade. Probabilidades não garantem acerto fora do currículo."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", default="curriculo_compreensao.json")
    parser.add_argument("--saida", default="rede_compreensao.json")
    parser.add_argument("--relatorio", default="avaliacao_compreensao.json")
    parser.add_argument("--epocas", type=int, default=90)
    parser.add_argument("--lote", type=int, default=32)
    parser.add_argument("--ocultos", type=int, default=40)
    parser.add_argument("--embeddings", type=int, default=24)
    parser.add_argument("--baldes", type=int, default=2048)
    parser.add_argument("--semente", type=int, default=2718)
    parser.add_argument("--checkpoint-progresso", help="Estado próprio para retomar treino interrompido")
    parser.add_argument("--retomar", action="store_true")
    parser.add_argument("--dropout", type=float, default=.25)
    parser.add_argument("--sem-equilibrio-atos", action="store_true")
    parser.add_argument("--dropout-trechos", type=float, default=.35)
    parser.add_argument("--suavizacao-atos", type=float, default=.1)
    parser.add_argument("--paciencia", type=int, default=0, help="Avaliações sem melhora antes de parar; 0 fixa épocas")
    parser.add_argument("--avaliar-cada", type=int, default=5)
    args = parser.parse_args()
    resultado = treinar(args.dados, args.saida, args.epocas, args.lote, args.ocultos,
                        args.embeddings, args.baldes, args.semente,
                        checkpoint_progresso=args.checkpoint_progresso, retomar=args.retomar,
                        dropout=args.dropout, equilibrar_atos=not args.sem_equilibrio_atos,
                        dropout_trechos=args.dropout_trechos, suavizacao_atos=args.suavizacao_atos,
                        paciencia=args.paciencia, avaliar_cada=args.avaliar_cada)
    Path(args.relatorio).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {n: resultado[k][n] for n in
                         ("total", "acertos", "aceitos", "aceitos_corretos", "f1_spans")}
                      for k in ("treino", "validacao")}, ensure_ascii=False), flush=True)
