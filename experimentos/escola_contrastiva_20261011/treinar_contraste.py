"""Segunda aula da Escola Cognitiva: ensino multivista invariavel.

A geracao usa exatamente o mesmo corpus e hiperparametros do PR #148.
A unica mudanca e pedagogica: cada professor divide o mesmo peso entre a
entrada original e uma segunda vista que remove atalhos lexicais.
As cabecas continuam treino-only e nunca entram no checkpoint final.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
DIR = Path(__file__).resolve().parent
FAT = RAIZ / "experimentos" / "corpus_fatorial_20261011"
OLD = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
AUX146 = RAIZ / "experimentos" / "ato_auxiliar_dialogo_20261011"
SCHOOL148 = RAIZ / "experimentos" / "escola_cognitiva_20261011"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AUX146))
sys.path.insert(0, str(SCHOOL148))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, formas, tokenizar
from treinar_dialogo_seq2seq import avaliar_perda, checkpoint, lote, perda_gradientes
import treinar_auxiliar as base_aux
import treinar_escola as escola148
from escola import MAPA_OPERACOES, PROFESSORES, rotulos_da_operacao, validar_escola


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar_json(path: Path, dados) -> None:
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def gravar_gz(path: Path, dados) -> None:
    bruto = (json.dumps(dados, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    path.write_bytes(gzip.compress(bruto, mtime=0))


def texto(ex):
    return {"mensagem": ex["mensagem"], "historico": ex.get("historico", []), "resposta": ex["resposta"]}


def substituir(texto_in: str, valores, repl: str) -> str:
    s = str(texto_in)
    for valor in sorted({str(v) for v in valores if v}, key=len, reverse=True):
        s = re.sub(rf"(?<!\w){re.escape(valor)}(?!\w)", repl, s, flags=re.IGNORECASE)
    return s


def construir_lexicos(exemplos):
    nomes = set()
    objetos = set()
    atividades = set()
    for e in exemplos:
        for k in ("nome_antes", "esperado_nome"):
            if e.get(k): nomes.add(str(e[k]))
        if e.get("objeto"): objetos.add(str(e["objeto"]))
        if e.get("atividade"): atividades.add(str(e["atividade"]))
    return {
        "nomes": nomes,
        "objetos": objetos,
        "atividades": atividades,
        "ambiguos": objetos & atividades,
    }


def anonimizar_acao(s: str, lex) -> str:
    todos = lex["nomes"] | lex["objetos"] | lex["atividades"]
    return substituir(s, todos, "coisa")


def anonimizar_foco(s: str, lex) -> str:
    s = substituir(s, lex["nomes"], "pessoa")
    s = substituir(s, lex["ambiguos"], "coisa")
    s = substituir(s, lex["objetos"] - lex["ambiguos"], "objeto")
    s = substituir(s, lex["atividades"] - lex["ambiguos"], "atividade")
    return s


def indice_estilo(ex_id: str, n: int) -> int:
    return int(hashlib.sha256(str(ex_id).encode()).hexdigest()[:8], 16) % n


def vista_invariante(ex, professor: str, curriculo, lex):
    base = texto(ex)
    op = ex.get("operacao")
    if op not in MAPA_OPERACOES:
        return base
    if professor == "acao":
        acao = rotulos_da_operacao(op)["acao"]
        frases = curriculo["vistas"]["acao"]["parafrases"][acao]
        msg = frases[indice_estilo(ex.get("id", ""), len(frases))]
        hist = [{"papel": h["papel"], "texto": anonimizar_acao(h["texto"], lex)} for h in ex.get("historico", [])]
        return {"mensagem": msg, "historico": hist, "resposta": ex["resposta"]}
    if professor == "foco":
        msg = anonimizar_foco(ex["mensagem"], lex)
        hist = [{"papel": h["papel"], "texto": anonimizar_foco(h["texto"], lex)} for h in ex.get("historico", [])]
        return {"mensagem": msg, "historico": hist, "resposta": ex["resposta"]}
    raise ValueError(professor)


def labels_professor(exemplos_raw, nome: str):
    ids = PROFESSORES[nome].ids
    out = []
    for e in exemplos_raw:
        op = e.get("operacao")
        if op not in MAPA_OPERACOES:
            out.append(-1)
        else:
            out.append(ids[rotulos_da_operacao(op)[nome]])
    return out


def treinar(corpus_path: Path, init_path: Path, protocolo, pt, curriculo):
    validar_escola()
    hcfg = pt["hiperparametros"]
    bruto = ler_json(corpus_path)
    exemplos = bruto["exemplos"] if isinstance(bruto, dict) else bruto
    treino_raw = [e for e in exemplos if e.get("split") == "treino"]
    valid_raw = [e for e in exemplos if e.get("split") == "validacao"]
    treino = [texto(e) for e in treino_raw]
    validacao = [texto(e) for e in valid_raw]
    if (len(treino), len(validacao)) != (3699, 382):
        raise ValueError(f"Splits inesperados: {(len(treino), len(validacao))}")
    if set(e.get("operacao") for e in treino_raw if e.get("operacao")) != set(MAPA_OPERACOES):
        raise ValueError("Operacoes rotuladas mudaram")

    lex = construir_lexicos(treino_raw)
    dados_ini = ler_json(init_path)
    modelo_ini = DialogoSeq2Seq(dados_ini)
    real = (modelo_ini.ocultos, modelo_ini.embeddings, modelo_ini.buckets, len(modelo_ini.vocabulario))
    esperado = (hcfg["ocultos"], hcfg["embeddings"], hcfg["buckets"], hcfg["vocab_max"])
    if real != esperado:
        raise ValueError(f"Inicializacao incompativel: {real} != {esperado}")
    vocab = list(modelo_ini.vocabulario)
    indices = {t: i for i, t in enumerate(vocab)}
    p = {k: np.asarray(v, dtype=np.float32).copy() for k, v in dados_ini["pesos"].items()}
    if sum(v.size for v in p.values()) != protocolo["modelo_producao"]["parametros"]:
        raise ValueError("Parametros base mudaram")

    seed = hcfg["semente"]
    rng = np.random.default_rng(seed)
    cabecas = escola148.criar_cabecas(hcfg["ocultos"], seed)
    momentos = {k: np.zeros_like(v) for k, v in p.items()}
    quadrados = {k: np.zeros_like(v) for k, v in p.items()}
    passo = 0
    inicio_treino = time.monotonic()
    entropias = []
    validacoes = []
    hist_prof = []
    melhor = None
    melhores_cabecas = None
    melhor_valor = float("inf")
    melhor_epoca = 0
    sem_melhoria = 0

    pesos_vistas = {
        nome: (
            float(curriculo["vistas"][nome]["original_peso"]),
            float(curriculo["vistas"][nome]["invariante_peso"]),
        ) for nome in PROFESSORES
    }
    if abs(sum(sum(v) for v in pesos_vistas.values()) - 0.25) > 1e-12:
        raise ValueError("Lambda auxiliar total mudou")

    for epoca in range(hcfg["epocas"]):
        taxa_amostragem = min(hcfg["amostragem"], hcfg["amostragem"] * max(0, epoca - hcfg["aquecimento"] + 1) / 3)
        ordem = rng.permutation(len(treino)).tolist()
        grupos = [ordem[j:j + hcfg["lote_tamanho"] * 8] for j in range(0, len(ordem), hcfg["lote_tamanho"] * 8)]
        batches = []
        for grupo in grupos:
            grupo.sort(key=lambda i: len(tokenizar(treino[i]["mensagem"])) + sum(len(tokenizar(x["texto"])) for x in treino[i].get("historico", [])))
            batches += [grupo[j:j + hcfg["lote_tamanho"]] for j in range(0, len(grupo), hcfg["lote_tamanho"])]
        rng.shuffle(batches)

        seq_total = 0.0
        tokens_total = 0
        prof_ep = {nome: {"orig_loss": 0.0, "inv_loss": 0.0, "orig_ok": 0, "inv_ok": 0, "n": 0} for nome in PROFESSORES}

        for pos in batches:
            raws = [treino_raw[i] for i in pos]
            textos = [treino[i] for i in pos]
            batch = lote(textos, indices, hcfg["buckets"], hcfg["limite_fonte"], hcfg["limite_resposta"])
            perda_seq, g = perda_gradientes(
                p, batch,
                dropout=hcfg["dropout"], dropout_tokens=hcfg["dropout_tokens"],
                amostragem=taxa_amostragem, rng=rng,
            )
            grads_cabecas = {}
            perdas_aux = []
            for nome in PROFESSORES:
                labels = labels_professor(raws, nome)
                cab = cabecas[nome]
                w_orig, w_inv = pesos_vistas[nome]
                po, go, gwo, gbo, aco, nto = base_aux.gradiente_auxiliar(p, batch, labels, cab["w"], cab["b"])
                inv_textos = [vista_invariante(e, nome, curriculo, lex) for e in raws]
                batch_inv = lote(inv_textos, indices, hcfg["buckets"], hcfg["limite_fonte"], hcfg["limite_resposta"])
                pi, gi, gwi, gbi, aci, nti = base_aux.gradiente_auxiliar(p, batch_inv, labels, cab["w"], cab["b"])
                if nto != nti:
                    raise ValueError("Vistas perderam rotulos")
                for k in g:
                    g[k] += w_orig * go[k] + w_inv * gi[k]
                grads_cabecas[nome] = (w_orig * gwo + w_inv * gwi, w_orig * gbo + w_inv * gbi)
                m = prof_ep[nome]
                m["orig_loss"] += po * nto; m["inv_loss"] += pi * nti
                m["orig_ok"] += aco; m["inv_ok"] += aci; m["n"] += nto
                perdas_aux += [po, pi]

            if not math.isfinite(perda_seq + sum(perdas_aux)) or any(not np.isfinite(x).all() for x in g.values()):
                raise ValueError("Gradiente nao finito")
            if any(not np.isfinite(gw).all() or not np.isfinite(gb).all() for gw, gb in grads_cabecas.values()):
                raise ValueError("Gradiente de cabeca nao finito")

            n = int(batch["mascara"].sum())
            seq_total += perda_seq * n; tokens_total += n
            norma2 = sum(float((x * x).sum()) for x in g.values())
            for gw, gb in grads_cabecas.values():
                norma2 += float((gw * gw).sum()) + float((gb * gb).sum())
            escala = min(1.0, 5 / max(math.sqrt(norma2), 1e-12))
            passo += 1
            for k in p:
                dg = g[k] * escala
                momentos[k] = .9 * momentos[k] + .1 * dg
                quadrados[k] = .999 * quadrados[k] + .001 * dg * dg
                p[k] -= hcfg["taxa"] * (momentos[k] / (1 - .9 ** passo)) / (np.sqrt(quadrados[k] / (1 - .999 ** passo)) + 1e-8)
                if p[k].ndim == 2:
                    p[k] *= 1 - hcfg["taxa"] * hcfg.get("decaimento", .00001)
            for nome, (gw, gb) in grads_cabecas.items():
                cab = cabecas[nome]
                gw *= escala; gb *= escala
                cab["mw"] = .9 * cab["mw"] + .1 * gw; cab["vw"] = .999 * cab["vw"] + .001 * gw * gw
                cab["mb"] = .9 * cab["mb"] + .1 * gb; cab["vb"] = .999 * cab["vb"] + .001 * gb * gb
                cab["w"] -= hcfg["taxa"] * (cab["mw"] / (1 - .9 ** passo)) / (np.sqrt(cab["vw"] / (1 - .999 ** passo)) + 1e-8)
                cab["b"] -= hcfg["taxa"] * (cab["mb"] / (1 - .9 ** passo)) / (np.sqrt(cab["vb"] / (1 - .999 ** passo)) + 1e-8)

        media = seq_total / max(1, tokens_total)
        entropias.append(media)
        linha = {"epoca": epoca + 1}
        for nome, m in prof_ep.items():
            linha[nome] = {
                "original_perda": m["orig_loss"] / max(1, m["n"]),
                "invariante_perda": m["inv_loss"] / max(1, m["n"]),
                "original_acuracia": m["orig_ok"] / max(1, m["n"]),
                "invariante_acuracia": m["inv_ok"] / max(1, m["n"]),
                "rotulados": m["n"],
            }
        hist_prof.append(linha)
        print("Epoca", epoca + 1, "CE", round(media, 4), "prof", {n: (round(linha[n]["original_acuracia"], 3), round(linha[n]["invariante_acuracia"], 3)) for n in PROFESSORES}, flush=True)

        if (epoca + 1) % hcfg["validar_cada"] == 0 or epoca + 1 == hcfg["epocas"]:
            med = avaliar_perda(p, validacao, indices, hcfg["buckets"], hcfg["limite_fonte"], hcfg["limite_resposta"], hcfg["lote_tamanho"])
            validacoes.append(dict(epoca=epoca + 1, **med))
            valor = med["entropia_cruzada"]
            print("Validacao geracao", epoca + 1, round(valor, 4), flush=True)
            if valor < melhor_valor - 1e-5:
                melhor_valor = valor; melhor_epoca = epoca + 1; sem_melhoria = 0
                melhor = {k: v.copy() for k, v in p.items()}
                melhores_cabecas = {nome: {"w": c["w"].copy(), "b": c["b"].copy()} for nome, c in cabecas.items()}
            else:
                sem_melhoria += hcfg["validar_cada"]
            if sem_melhoria >= hcfg["paciencia"]:
                print("Parada; melhor epoca", melhor_epoca, flush=True)
                break

    if melhor is None or melhores_cabecas is None:
        raise ValueError("Nenhuma epoca selecionada")
    p = melhor
    aval_prof = {}
    for nome in PROFESSORES:
        w = melhores_cabecas[nome]["w"]; b = melhores_cabecas[nome]["b"]
        aval_prof[nome] = {
            "treino": escola148.avaliar_professor(p, treino_raw, indices, hcfg["buckets"], hcfg["limite_fonte"], hcfg["limite_resposta"], nome, w, b),
            "validacao_rotulada": escola148.avaliar_professor(p, valid_raw, indices, hcfg["buckets"], hcfg["limite_fonte"], hcfg["limite_resposta"], nome, w, b),
            "cabeca_parametros_treino": int(w.size + b.size), "serializada": False,
        }

    meta = {
        "arquitetura": "BiGRU encoder + GRU decoder + atencao e pointer-generator; Escola Cognitiva descartada apos treino",
        "treino": {
            "epocas_solicitadas": hcfg["epocas"], "epocas": len(entropias), "epoca_selecionada": melhor_epoca,
            "exemplos": len(treino), "parametros": sum(v.size for v in p.values()), "entropias": entropias,
            "validacoes": validacoes, "professores_por_epoca": hist_prof, "lambda_auxiliar_total": 0.25,
            "segundos": round(time.monotonic() - inicio_treino, 2),
        },
        "escola_cognitiva": {"metodo": "multivista_invariante", "professores": aval_prof, "serializada": False, "regra_runtime": False},
        "limites": {"fonte_tokens": hcfg["limite_fonte"], "resposta_tokens": hcfg["limite_resposta"]},
        "aprovado": False, "ativo_no_chat": False,
    }
    dados = checkpoint(p, vocab, hcfg["ocultos"], hcfg["embeddings"], hcfg["buckets"], hcfg["limite_fonte"], **meta)
    if set(dados["pesos"]) != set(formas(vocab, hcfg["ocultos"], hcfg["embeddings"], hcfg["buckets"])):
        raise ValueError("Professor vazou no checkpoint")
    if sum(np.asarray(v).size for v in dados["pesos"].values()) != pt["integridade"]["parametros_checkpoint"]:
        raise ValueError("Checkpoint mudou de tamanho")
    if len(dados["vocabulario"]) != pt["integridade"]["vocabulario_checkpoint"]:
        raise ValueError("Vocabulario mudou")
    return dados, {"epoca_selecionada": melhor_epoca, "validacao_ce": melhor_valor, "professores": aval_prof, "segundos": round(time.monotonic() - inicio_treino, 2)}


def resumo(r):
    n = r["candidato"]; p = r["criterio"]
    linhas = [
        "# Escola Cognitiva — aula contrastiva multivista", "",
        "Mesma GRU, mesmos 81.433 parametros, mesmos 3.699 exemplos de geracao e lambda auxiliar total 0,25.", "",
        f"- Professor AÇÃO dev: **{100*r['treino']['professores']['acao']['validacao_rotulada']['acuracia']:.1f}%**.",
        f"- Professor FOCO dev: **{100*r['treino']['professores']['foco']['validacao_rotulada']['acuracia']:.1f}%**.",
        f"- old334: **{n['old334']['geracao']['iguais_ao_alvo']}/334**, CE **{n['old334']['perda']['entropia_cruzada']:.3f}**.",
        f"- known94: **{n['known94']['geracao']['iguais_ao_alvo']}/94**, CE **{n['known94']['perda']['entropia_cruzada']:.3f}**.",
        f"- fatorial96 operações: **{100*n['fatorial96']['operacoes']['taxa']:.1f}%**.",
        f"- holdout #146: **{100*n['holdout146']['operacoes']['taxa']:.1f}%**.",
        f"- holdout #148: **{100*n['holdout148']['operacoes']['taxa']:.1f}%**.",
        f"- prova nova 180: CE **{n['holdout180']['perda']['entropia_cruzada']:.3f}**, primeiro token **{100*n['holdout180']['primeiro_token']['acuracia']:.1f}%**, operações **{100*n['holdout180']['operacoes']['taxa']:.1f}%**.",
        "", "## Gate congelado", "",
    ]
    for k, v in p.items():
        if isinstance(v, bool): linhas.append(f"- {k}: **{'PASSOU' if v else 'FALHOU'}**.")
    linhas += ["", f"**Sucesso conjunto: {'SIM' if p['sucesso_conjunto'] else 'NÃO'}.**", "", "Nenhuma promoção automática; `ativo_no_chat=false`."]
    return "\n".join(linhas) + "\n"


def executar():
    protocolo = ler_json(DIR / "protocolo.json")
    pt = ler_json(DIR / "protocolo_treino.json")
    curriculo = ler_json(DIR / "curriculo.json")
    manifesto = ler_json(DIR / "manifesto_holdout.json")
    holdout_path = DIR / "holdout_contraste.json"
    if sha256(DIR / "protocolo.json") != pt["protocolo_sha256"]: raise ValueError("Protocolo mudou")
    if sha256(DIR / "curriculo.json") != pt["curriculo_sha256"]: raise ValueError("Curriculo mudou")
    if sha256(SCHOOL148 / "escola.py") != pt["escola_base_sha256"]: raise ValueError("Escola base mudou")
    if not manifesto.get("aprovado") or sha256(holdout_path) != pt["holdout_sha256"]: raise ValueError("Holdout nao congelado")
    corpus_path = RAIZ / protocolo["fontes"]["corpus"]
    init_path = RAIZ / protocolo["fontes"]["inicializacao"]
    if sha256(corpus_path) != protocolo["fontes"]["corpus_sha256"] or sha256(init_path) != protocolo["fontes"]["inicializacao_sha256"]:
        raise ValueError("Fontes de treino mudaram")

    fat_protocol = ler_json(FAT / "protocolo.json"); fat_results = ler_json(FAT / "resultados_treino.json")
    aux_results = ler_json(AUX146 / "resultados.json"); school_results = ler_json(SCHOOL148 / "resultados.json")
    ctrl_path = OLD / "checkpoint_sessoes.json.gz"; fat_path = FAT / "checkpoint_fatorial.json.gz"
    aux_path = AUX146 / "checkpoint_auxiliar.json.gz"; school_path = SCHOOL148 / "checkpoint_escola.json.gz"
    if sha256(ctrl_path) != fat_protocol["controle"]["checkpoint_sha256"]: raise ValueError("Controle mudou")
    if sha256(fat_path) != fat_results["treino"]["checkpoint_sha256"]: raise ValueError("Fatorial mudou")
    if sha256(aux_path) != aux_results["treino"]["checkpoint_sha256"] and sha256(aux_path) != aux_results.get("checkpoint_sha256", ""):
        raise ValueError("PR146 mudou")
    if sha256(school_path) != school_results["treino"]["checkpoint_sha256"]: raise ValueError("PR148 mudou")

    destino = DIR / "checkpoint_contraste.json.gz"
    if destino.exists(): raise ValueError("Candidato unico ja existe")
    inicio = time.monotonic()
    cand, treino_info = treinar(corpus_path, init_path, protocolo, pt, curriculo)
    cand.update(experimento="escola-contrastiva-20261011", sha256_holdout=pt["holdout_sha256"], aprovado=False, ativo_no_chat=False)
    gravar_gz(destino, cand)
    if sha256(holdout_path) != pt["holdout_sha256"]: raise ValueError("Holdout mudou durante treino")

    old = ler_json(OLD / "corpus_sessoes.json.gz")["exemplos"]
    old334 = [e for e in old if e.get("split") == "validacao" and e.get("grupo") != "sessao_completa"]
    known94 = [e for e in old if e.get("split") == "validacao" and e.get("grupo") == "sessao_completa"]
    fat96 = ler_json(FAT / "avaliacao_final_fatorial.json")["exemplos"]
    h146 = ler_json(AUX146 / "holdout_novo.json")["exemplos"]
    h148 = ler_json(SCHOOL148 / "holdout_escola.json")["exemplos"]
    h180 = ler_json(holdout_path)["exemplos"]
    if (len(old334), len(known94), len(fat96), len(h146), len(h148), len(h180)) != (334, 94, 96, 144, 144, 180):
        raise ValueError("Recortes mudaram")

    modelos = {"controle_1x": ler_json(ctrl_path), "fatorial": ler_json(fat_path), "aux146": ler_json(aux_path), "escola148": ler_json(school_path), "contraste": cand}
    aval = {}
    for nome, dados in modelos.items():
        aval[nome] = {
            "old334": base_aux.avaliar_bloco(dados, old334),
            "known94": base_aux.avaliar_bloco(dados, known94),
            "fatorial96": base_aux.avaliar_bloco(dados, fat96, True),
            "holdout146": base_aux.avaliar_bloco(dados, h146, True),
            "holdout148": base_aux.avaliar_bloco(dados, h148, True),
            "holdout180": base_aux.avaliar_bloco(dados, h180, True),
        }
    n = aval["contraste"]; g = protocolo["portao"]
    baselines = [aval[k] for k in ("controle_1x", "fatorial", "aux146", "escola148")]
    best_ce = min(x["holdout180"]["perda"]["entropia_cruzada"] for x in baselines)
    best_first = max(x["holdout180"]["primeiro_token"]["acuracia"] for x in baselines)
    best_ops = max(x["holdout180"]["operacoes"]["taxa"] for x in baselines)
    ce = n["holdout180"]["perda"]["entropia_cruzada"]
    first = n["holdout180"]["primeiro_token"]["acuracia"]
    ops = n["holdout180"]["operacoes"]["taxa"]
    ganho_ce = (best_ce - ce) / max(best_ce, 1e-12); ganho_first = first - best_first; ganho_ops = ops - best_ops
    min_op = min(v["taxa"] for v in n["holdout180"]["operacoes"]["por_operacao"].values())
    pa = treino_info["professores"]["acao"]["validacao_rotulada"]["acuracia"]
    pf = treino_info["professores"]["foco"]["validacao_rotulada"]["acuracia"]
    criterio = {
        "old334_exatas": n["old334"]["geracao"]["iguais_ao_alvo"] >= g["old334_exatas_min"],
        "old334_ce": n["old334"]["perda"]["entropia_cruzada"] <= g["old334_ce_max"],
        "known94_exatas": n["known94"]["geracao"]["iguais_ao_alvo"] >= g["known94_exatas_min"],
        "known94_ce": n["known94"]["perda"]["entropia_cruzada"] <= g["known94_ce_max"],
        "fatorial96_operacoes": n["fatorial96"]["operacoes"]["taxa"] >= g["fatorial96_operacoes_min"],
        "holdout146_operacoes": n["holdout146"]["operacoes"]["taxa"] >= g["holdout146_operacoes_min"],
        "holdout148_operacoes": n["holdout148"]["operacoes"]["taxa"] >= g["holdout148_operacoes_min"],
        "professor_acao_dev": pa >= g["professor_acao_dev_min"],
        "professor_foco_dev": pf >= g["professor_foco_dev_min"],
        "novo_ce": ganho_ce >= g["novo_holdout_ce_melhora_relativa_vs_melhor_baseline_min"],
        "novo_primeiro": ganho_first >= g["novo_holdout_primeiro_ganho_vs_melhor_baseline_min"],
        "novo_operacoes_ganho": ganho_ops >= g["novo_holdout_operacoes_ganho_vs_melhor_baseline_min"],
        "novo_operacoes_total": ops >= g["novo_holdout_operacoes_total_min"],
        "novo_operacao_individual": min_op >= g["novo_holdout_operacao_individual_min"],
        "ganho_ce_relativo": ganho_ce, "ganho_primeiro_pp": ganho_first, "ganho_operacoes_pp": ganho_ops,
        "min_operacao": min_op, "professor_acao_dev_valor": pa, "professor_foco_dev_valor": pf,
    }
    chaves = [k for k, v in criterio.items() if isinstance(v, bool)]
    criterio["sucesso_conjunto"] = all(criterio[k] for k in chaves)
    result = {
        "base_commit": pt["base_commit"],
        "integridade": {"um_unico_candidato": True, "prova_aberta_pos_selecao": True, "holdout_sha256": pt["holdout_sha256"], "parametros_serializados": cand["treino"]["parametros"], "vocabulario": len(cand["vocabulario"]), "checkpoint_publico_alterado": False},
        "treino": {**treino_info, "segundos_total_com_avaliacao": round(time.monotonic() - inicio, 2), "checkpoint_sha256": sha256(destino)},
        "controles": {k: aval[k] for k in ("controle_1x", "fatorial", "aux146", "escola148")},
        "candidato": n, "criterio": criterio, "aprovado_experimentalmente": bool(criterio["sucesso_conjunto"]), "ativo_no_chat": False,
        "limite": "Prova prospectiva sintetica/autoral; nao equivale a avaliacao humana geral."
    }
    gravar_json(DIR / "resultados.json", result)
    (DIR / "RELATORIO.md").write_text(resumo(result), encoding="utf-8")
    print(json.dumps({"criterio": criterio, "professores": treino_info["professores"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    executar()
