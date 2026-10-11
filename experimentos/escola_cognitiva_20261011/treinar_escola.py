"""Primeiro treino da Escola Cognitiva: professores fatorados de ACAO e FOCO.

A única intervenção causal em relação ao PR #146 é a fatoração da supervisão.
O peso auxiliar total continua 0,25. As duas cabeças existem somente durante o
treino, não recebem tokens especiais e nunca são serializadas no checkpoint.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
DIR = Path(__file__).resolve().parent
FAT = RAIZ / "experimentos" / "corpus_fatorial_20261011"
OLD = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
AUX146 = RAIZ / "experimentos" / "ato_auxiliar_dialogo_20261011"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(DIR))
sys.path.insert(0, str(AUX146))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, formas, tokenizar
from treinar_dialogo_seq2seq import avaliar_perda, checkpoint, lote, perda_gradientes
import treinar_auxiliar as base_aux
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


def labels_professor(exemplos_raw, nome: str) -> list[int]:
    ids = PROFESSORES[nome].ids
    saida = []
    for ex in exemplos_raw:
        operacao = ex.get("operacao")
        if operacao not in MAPA_OPERACOES:
            saida.append(-1)
            continue
        rotulo = rotulos_da_operacao(operacao)[nome]
        saida.append(ids[rotulo])
    return saida


def avaliar_professor(p, exemplos_raw, indices, buckets, limite_fonte, limite_resposta, nome, w, b, lote_tamanho=64):
    ids = PROFESSORES[nome].ids
    rotulados = [e for e in exemplos_raw if e.get("operacao") in MAPA_OPERACOES]
    total = corretos = 0
    perda_soma = 0.0
    confusao = {rot: {r: 0 for r in PROFESSORES[nome].classes} for rot in PROFESSORES[nome].classes}
    for inicio in range(0, len(rotulados), lote_tamanho):
        es = rotulados[inicio:inicio + lote_tamanho]
        batch = lote([texto(e) for e in es], indices, buckets, limite_fonte, limite_resposta)
        inicial, *_ = base_aux.estado_inicial_com_cache(p, batch)
        logits = inicial @ w + b
        logits -= logits.max(axis=1, keepdims=True)
        probs = np.exp(logits)
        probs /= probs.sum(axis=1, keepdims=True)
        alvos_rot = [rotulos_da_operacao(e["operacao"])[nome] for e in es]
        y = np.asarray([ids[r] for r in alvos_rot], dtype=np.int64)
        pred = probs.argmax(axis=1)
        perda_soma += -float(np.log(np.maximum(probs[np.arange(len(y)), y], 1e-12)).sum())
        corretos += int((pred == y).sum())
        total += len(y)
        classes = PROFESSORES[nome].classes
        for alvo, pidx in zip(alvos_rot, pred.tolist()):
            confusao[alvo][classes[pidx]] += 1
    return {
        "exemplos": total,
        "corretos": corretos,
        "acuracia": corretos / max(1, total),
        "entropia_cruzada": perda_soma / max(1, total),
        "confusao": confusao,
    }


def criar_cabecas(hidden: int, seed: int):
    cabecas = {}
    for i, (nome, professor) in enumerate(PROFESSORES.items()):
        rng = np.random.default_rng(seed + 7919 + 104729 * i)
        w = rng.normal(0, 1 / math.sqrt(hidden), (hidden, len(professor.classes))).astype(np.float32)
        b = np.zeros(len(professor.classes), dtype=np.float32)
        cabecas[nome] = {
            "w": w,
            "b": b,
            "mw": np.zeros_like(w),
            "vw": np.zeros_like(w),
            "mb": np.zeros_like(b),
            "vb": np.zeros_like(b),
        }
    return cabecas


def treinar(corpus_path: Path, init_path: Path, protocolo, protocolo_treino):
    validar_escola()
    hcfg = protocolo_treino["hiperparametros"]
    bruto = ler_json(corpus_path)
    exemplos = bruto["exemplos"] if isinstance(bruto, dict) else bruto
    treino_raw = [e for e in exemplos if e.get("split") == "treino"]
    valid_raw = [e for e in exemplos if e.get("split") == "validacao"]
    treino = [texto(e) for e in treino_raw]
    validacao = [texto(e) for e in valid_raw]
    if (len(treino), len(validacao)) != (3699, 382):
        raise ValueError(f"Splits fatoriais inesperados: {(len(treino), len(validacao))}")
    if set(e.get("operacao") for e in treino_raw if e.get("operacao")) != set(MAPA_OPERACOES):
        raise ValueError("Operações rotuladas do treino mudaram")

    dados_ini = ler_json(init_path)
    modelo_ini = DialogoSeq2Seq(dados_ini)
    esperado = (hcfg["ocultos"], hcfg["embeddings"], hcfg["buckets"], hcfg["vocab_max"])
    real = (modelo_ini.ocultos, modelo_ini.embeddings, modelo_ini.buckets, len(modelo_ini.vocabulario))
    if real != esperado:
        raise ValueError(f"Inicialização incompatível: {real} != {esperado}")
    vocab = list(modelo_ini.vocabulario)
    indices = {t: i for i, t in enumerate(vocab)}
    p = {k: np.asarray(v, dtype=np.float32).copy() for k, v in dados_ini["pesos"].items()}
    if sum(v.size for v in p.values()) != protocolo["modelo_producao"]["parametros"]:
        raise ValueError("Contagem de parâmetros base mudou")

    seed = hcfg["semente"]
    rng = np.random.default_rng(seed)
    cabecas = criar_cabecas(hcfg["ocultos"], seed)
    momentos = {k: np.zeros_like(v) for k, v in p.items()}
    quadrados = {k: np.zeros_like(v) for k, v in p.items()}
    passo = 0
    inicio_treino = time.monotonic()
    entropias = []
    historico_professores = []
    validacoes = []
    melhor = None
    melhores_cabecas = None
    melhor_valor = float("inf")
    melhor_epoca = 0
    sem_melhoria = 0

    pesos = {nome: float(PROFESSORES[nome].peso) for nome in PROFESSORES}
    if abs(sum(pesos.values()) - 0.25) > 1e-12:
        raise ValueError("Peso auxiliar total deixou de ser 0,25")

    for epoca in range(hcfg["epocas"]):
        taxa_amostragem = min(
            hcfg["amostragem"],
            hcfg["amostragem"] * max(0, epoca - hcfg["aquecimento"] + 1) / 3,
        )
        ordem = rng.permutation(len(treino)).tolist()
        grupos = [ordem[j:j + hcfg["lote_tamanho"] * 8] for j in range(0, len(ordem), hcfg["lote_tamanho"] * 8)]
        batches = []
        for grupo in grupos:
            grupo.sort(key=lambda i: len(tokenizar(treino[i]["mensagem"])) + sum(len(tokenizar(x["texto"])) for x in treino[i].get("historico", [])))
            batches += [grupo[j:j + hcfg["lote_tamanho"]] for j in range(0, len(grupo), hcfg["lote_tamanho"])]
        rng.shuffle(batches)

        seq_total = 0.0
        tokens_total = 0
        prof_epoca = {nome: {"perda_soma": 0.0, "rotulados": 0, "corretos": 0} for nome in PROFESSORES}

        for pos in batches:
            textos = [treino[i] for i in pos]
            batch = lote(textos, indices, hcfg["buckets"], hcfg["limite_fonte"], hcfg["limite_resposta"])
            perda_seq, g = perda_gradientes(
                p, batch,
                dropout=hcfg["dropout"],
                dropout_tokens=hcfg["dropout_tokens"],
                amostragem=taxa_amostragem,
                rng=rng,
            )
            grads_cabecas = {}
            perdas_aux = []
            for nome, professor in PROFESSORES.items():
                labels = labels_professor([treino_raw[i] for i in pos], nome)
                cab = cabecas[nome]
                perda_aux, gaux, gw, gb, ac, nt = base_aux.gradiente_auxiliar(p, batch, labels, cab["w"], cab["b"])
                peso = pesos[nome]
                for k in g:
                    g[k] += peso * gaux[k]
                grads_cabecas[nome] = (peso * gw, peso * gb)
                prof_epoca[nome]["perda_soma"] += perda_aux * nt
                prof_epoca[nome]["rotulados"] += nt
                prof_epoca[nome]["corretos"] += ac
                perdas_aux.append(perda_aux)

            if not math.isfinite(perda_seq + sum(perdas_aux)) or any(not np.isfinite(x).all() for x in g.values()):
                raise ValueError("Gradiente da escola não finito")
            if any(not np.isfinite(gw).all() or not np.isfinite(gb).all() for gw, gb in grads_cabecas.values()):
                raise ValueError("Gradiente de professor não finito")

            n = int(batch["mascara"].sum())
            seq_total += perda_seq * n
            tokens_total += n
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
                gw = gw * escala
                gb = gb * escala
                cab["mw"] = .9 * cab["mw"] + .1 * gw
                cab["vw"] = .999 * cab["vw"] + .001 * gw * gw
                cab["mb"] = .9 * cab["mb"] + .1 * gb
                cab["vb"] = .999 * cab["vb"] + .001 * gb * gb
                cab["w"] -= hcfg["taxa"] * (cab["mw"] / (1 - .9 ** passo)) / (np.sqrt(cab["vw"] / (1 - .999 ** passo)) + 1e-8)
                cab["b"] -= hcfg["taxa"] * (cab["mb"] / (1 - .9 ** passo)) / (np.sqrt(cab["vb"] / (1 - .999 ** passo)) + 1e-8)

        media = seq_total / max(1, tokens_total)
        entropias.append(media)
        linha_prof = {"epoca": epoca + 1}
        for nome, m in prof_epoca.items():
            linha_prof[nome] = {
                "perda": m["perda_soma"] / max(1, m["rotulados"]),
                "acuracia": m["corretos"] / max(1, m["rotulados"]),
                "rotulados": m["rotulados"],
            }
        historico_professores.append(linha_prof)
        print("Época", epoca + 1, "CE geração", round(media, 4), "professores", {n: round(linha_prof[n]["acuracia"], 4) for n in PROFESSORES}, flush=True)

        if (epoca + 1) % hcfg["validar_cada"] == 0 or epoca + 1 == hcfg["epocas"]:
            med = avaliar_perda(p, validacao, indices, hcfg["buckets"], hcfg["limite_fonte"], hcfg["limite_resposta"], hcfg["lote_tamanho"])
            validacoes.append(dict(epoca=epoca + 1, **med))
            valor = med["entropia_cruzada"]
            print("Validação geração", epoca + 1, round(valor, 4), flush=True)
            if valor < melhor_valor - 1e-5:
                melhor_valor = valor
                melhor_epoca = epoca + 1
                sem_melhoria = 0
                melhor = {k: v.copy() for k, v in p.items()}
                melhores_cabecas = {nome: {"w": cab["w"].copy(), "b": cab["b"].copy()} for nome, cab in cabecas.items()}
            else:
                sem_melhoria += hcfg["validar_cada"]
            if sem_melhoria >= hcfg["paciencia"]:
                print("Parada por validação; melhor época", melhor_epoca, flush=True)
                break

    if melhor is None or melhores_cabecas is None:
        raise ValueError("Nenhuma época selecionada")
    p = melhor

    aval_prof = {}
    for nome in PROFESSORES:
        w = melhores_cabecas[nome]["w"]
        b = melhores_cabecas[nome]["b"]
        aval_prof[nome] = {
            "treino": avaliar_professor(p, treino_raw, indices, hcfg["buckets"], hcfg["limite_fonte"], hcfg["limite_resposta"], nome, w, b),
            "validacao_rotulada": avaliar_professor(p, valid_raw, indices, hcfg["buckets"], hcfg["limite_fonte"], hcfg["limite_resposta"], nome, w, b),
            "cabeca_parametros_treino": int(w.size + b.size),
            "serializada": False,
            "peso": pesos[nome],
            "classes": list(PROFESSORES[nome].classes),
        }

    meta = {
        "arquitetura": "BiGRU encoder + GRU decoder + atenção e pointer-generator; Escola Cognitiva descartada após treino",
        "treino": {
            "epocas_solicitadas": hcfg["epocas"],
            "epocas": len(entropias),
            "epoca_selecionada": melhor_epoca,
            "exemplos": len(treino),
            "parametros": sum(v.size for v in p.values()),
            "entropias": entropias,
            "validacoes": validacoes,
            "professores_por_epoca": historico_professores,
            "lambda_auxiliar_total": sum(pesos.values()),
            "segundos": round(time.monotonic() - inicio_treino, 2),
        },
        "escola_cognitiva": {
            "professores": aval_prof,
            "serializada": False,
            "tokens_especiais": False,
            "regra_runtime": False,
        },
        "limites": {"fonte_tokens": hcfg["limite_fonte"], "resposta_tokens": hcfg["limite_resposta"]},
        "aprovado": False,
        "ativo_no_chat": False,
    }
    dados = checkpoint(p, vocab, hcfg["ocultos"], hcfg["embeddings"], hcfg["buckets"], hcfg["limite_fonte"], **meta)
    if set(dados["pesos"]) != set(formas(vocab, hcfg["ocultos"], hcfg["embeddings"], hcfg["buckets"])):
        raise ValueError("Professor vazou para checkpoint")
    if sum(np.asarray(v).size for v in dados["pesos"].values()) != protocolo_treino["integridade"]["parametros_checkpoint"]:
        raise ValueError("Checkpoint serializado mudou de tamanho")
    if len(dados["vocabulario"]) != protocolo_treino["integridade"]["vocabulario_checkpoint"]:
        raise ValueError("Vocabulário serializado mudou")
    return dados, {
        "epoca_selecionada": melhor_epoca,
        "validacao_ce": melhor_valor,
        "professores": aval_prof,
        "segundos": round(time.monotonic() - inicio_treino, 2),
    }


def resumo(result):
    n = result["candidato"]
    p = result["criterio"]
    linhas = [
        "# Escola Cognitiva — primeira turma",
        "",
        "Professores treino-only: **AÇÃO** e **FOCO**, com 0,125 de peso cada. O checkpoint final continua com **81.433 parâmetros** e vocabulário **720**.",
        "",
        f"- Professor AÇÃO: treino **{100*result['treino']['professores']['acao']['treino']['acuracia']:.1f}%**, dev **{100*result['treino']['professores']['acao']['validacao_rotulada']['acuracia']:.1f}%**.",
        f"- Professor FOCO: treino **{100*result['treino']['professores']['foco']['treino']['acuracia']:.1f}%**, dev **{100*result['treino']['professores']['foco']['validacao_rotulada']['acuracia']:.1f}%**.",
        f"- old334: **{n['old334']['geracao']['iguais_ao_alvo']}/334**, CE **{n['old334']['perda']['entropia_cruzada']:.3f}**.",
        f"- known94: **{n['known94']['geracao']['iguais_ao_alvo']}/94**, CE **{n['known94']['perda']['entropia_cruzada']:.3f}**.",
        f"- fatorial96 operações: **{100*n['fatorial96']['operacoes']['taxa']:.1f}%**.",
        f"- holdout146 conhecido operações: **{100*n['holdout146']['operacoes']['taxa']:.1f}%**.",
        f"- prova nova 144: CE **{n['holdout_escola']['perda']['entropia_cruzada']:.3f}**, primeiro token **{100*n['holdout_escola']['primeiro_token']['acuracia']:.1f}%**, operações **{100*n['holdout_escola']['operacoes']['taxa']:.1f}%**.",
        "",
        "## Gate congelado",
        "",
    ]
    for k, v in p.items():
        if isinstance(v, bool):
            linhas.append(f"- {k}: **{'PASSOU' if v else 'FALHOU'}**.")
    linhas += ["", f"**Sucesso conjunto: {'SIM' if p['sucesso_conjunto'] else 'NÃO'}.**", "", "Nenhuma promoção automática; `ativo_no_chat=false`."]
    return "\n".join(linhas) + "\n"


def executar():
    validar_escola()
    protocolo = ler_json(DIR / "protocolo.json")
    pt = ler_json(DIR / "protocolo_treino.json")
    manifesto = ler_json(DIR / "manifesto_holdout.json")
    holdout_path = DIR / "holdout_escola.json"
    corpus_path = RAIZ / protocolo["treino_futuro"]["corpus"]
    init_path = RAIZ / protocolo["treino_futuro"]["inicializacao"]

    if sha256(DIR / "protocolo.json") != pt["protocolo_fundacao_sha256"]:
        raise ValueError("Protocolo de fundação mudou")
    if sha256(DIR / "escola.py") != pt["escola_sha256"]:
        raise ValueError("Definição da escola mudou")
    if not manifesto.get("aprovado") or sha256(holdout_path) != pt["holdout_sha256"] or manifesto["holdout_sha256"] != pt["holdout_sha256"]:
        raise ValueError("Prova prospectiva não está congelada")
    if sha256(corpus_path) != protocolo["treino_futuro"]["corpus_sha256"] or sha256(init_path) != protocolo["treino_futuro"]["inicializacao_sha256"]:
        raise ValueError("Fontes de treino mudaram")

    fat_protocol = ler_json(FAT / "protocolo.json")
    fat_results = ler_json(FAT / "resultados_treino.json")
    aux_results = ler_json(AUX146 / "resultados.json")
    ctrl_path = OLD / "checkpoint_sessoes.json.gz"
    fat_path = FAT / "checkpoint_fatorial.json.gz"
    aux_path = AUX146 / "checkpoint_auxiliar.json.gz"
    old_corpus = OLD / "corpus_sessoes.json.gz"
    if sha256(ctrl_path) != fat_protocol["controle"]["checkpoint_sha256"]:
        raise ValueError("Controle 1x mudou")
    if sha256(fat_path) != fat_results["treino"]["checkpoint_sha256"]:
        raise ValueError("Checkpoint fatorial mudou")
    if sha256(aux_path) != aux_results["checkpoint_sha256"]:
        raise ValueError("Checkpoint do PR146 mudou")

    destino = DIR / "checkpoint_escola.json.gz"
    if destino.exists():
        raise ValueError("Checkpoint da escola já existe; protocolo é de candidato único")

    inicio = time.monotonic()
    cand, treino_info = treinar(corpus_path, init_path, protocolo, pt)
    cand.update(
        experimento="escola-cognitiva-fatorada-20261011",
        sha256_holdout=pt["holdout_sha256"],
        aprovado=False,
        ativo_no_chat=False,
    )
    gravar_gz(destino, cand)

    # A prova nova só é aberta depois que a época já foi escolhida.
    if sha256(holdout_path) != pt["holdout_sha256"]:
        raise ValueError("Prova mudou durante treino")
    novo = ler_json(holdout_path)["exemplos"]
    old = ler_json(old_corpus)["exemplos"]
    old334 = [e for e in old if e.get("split") == "validacao" and e.get("grupo") != "sessao_completa"]
    known94 = [e for e in old if e.get("split") == "validacao" and e.get("grupo") == "sessao_completa"]
    fat96 = ler_json(FAT / "avaliacao_final_fatorial.json")["exemplos"]
    h146 = ler_json(AUX146 / "holdout_novo.json")["exemplos"]
    if (len(old334), len(known94), len(fat96), len(h146), len(novo)) != (334, 94, 96, 144, 144):
        raise ValueError("Recortes de avaliação mudaram")

    modelos = {
        "controle_1x": ler_json(ctrl_path),
        "fatorial": ler_json(fat_path),
        "aux146": ler_json(aux_path),
        "escola": cand,
    }
    aval = {}
    for nome, dados in modelos.items():
        aval[nome] = {
            "old334": base_aux.avaliar_bloco(dados, old334),
            "known94": base_aux.avaliar_bloco(dados, known94),
            "fatorial96": base_aux.avaliar_bloco(dados, fat96, True),
            "holdout146": base_aux.avaliar_bloco(dados, h146, True),
            "holdout_escola": base_aux.avaliar_bloco(dados, novo, True),
        }

    n = aval["escola"]
    g = pt["portao"]
    baselines = [aval["controle_1x"], aval["fatorial"], aval["aux146"]]
    best_ce = min(x["holdout_escola"]["perda"]["entropia_cruzada"] for x in baselines)
    best_first = max(x["holdout_escola"]["primeiro_token"]["acuracia"] for x in baselines)
    best_ops = max(x["holdout_escola"]["operacoes"]["taxa"] for x in baselines)
    cand_ce = n["holdout_escola"]["perda"]["entropia_cruzada"]
    cand_first = n["holdout_escola"]["primeiro_token"]["acuracia"]
    cand_ops = n["holdout_escola"]["operacoes"]["taxa"]
    ganho_ce = (best_ce - cand_ce) / max(best_ce, 1e-12)
    ganho_first = cand_first - best_first
    ganho_ops = cand_ops - best_ops
    min_op = min(v["taxa"] for v in n["holdout_escola"]["operacoes"]["por_operacao"].values())
    min_prof_dev = min(v["validacao_rotulada"]["acuracia"] for v in treino_info["professores"].values())

    criterio = {
        "old334_exatas": n["old334"]["geracao"]["iguais_ao_alvo"] >= g["old334_exatas_min"],
        "old334_ce": n["old334"]["perda"]["entropia_cruzada"] <= g["old334_ce_max"],
        "known94_exatas": n["known94"]["geracao"]["iguais_ao_alvo"] >= g["known94_exatas_min"],
        "known94_ce": n["known94"]["perda"]["entropia_cruzada"] <= g["known94_ce_max"],
        "fatorial96_operacoes": n["fatorial96"]["operacoes"]["taxa"] >= g["fatorial96_operacoes_min"],
        "holdout146_operacoes": n["holdout146"]["operacoes"]["taxa"] >= g["holdout146_operacoes_min"],
        "professores_dev": min_prof_dev >= g["professor_dev_acuracia_individual_min"],
        "novo_ce": ganho_ce >= g["novo_holdout_ce_melhora_relativa_vs_melhor_baseline_min"],
        "novo_primeiro": ganho_first >= g["novo_holdout_primeiro_ganho_vs_melhor_baseline_min"],
        "novo_operacoes_ganho": ganho_ops >= g["novo_holdout_operacoes_ganho_vs_melhor_baseline_min"],
        "novo_operacoes_total": cand_ops >= g["novo_holdout_operacoes_total_min"],
        "novo_operacao_individual": min_op >= g["novo_holdout_operacao_individual_min"],
        "ganho_ce_relativo": ganho_ce,
        "ganho_primeiro_pp": ganho_first,
        "ganho_operacoes_pp": ganho_ops,
        "min_operacao": min_op,
        "min_professor_dev": min_prof_dev,
    }
    chaves = [
        "old334_exatas", "old334_ce", "known94_exatas", "known94_ce",
        "fatorial96_operacoes", "holdout146_operacoes", "professores_dev",
        "novo_ce", "novo_primeiro", "novo_operacoes_ganho",
        "novo_operacoes_total", "novo_operacao_individual",
    ]
    criterio["sucesso_conjunto"] = all(criterio[k] for k in chaves)

    result = {
        "base_commit": pt["base_commit"],
        "integridade": {
            "um_unico_candidato": True,
            "prova_aberta_pos_selecao": True,
            "holdout_sha256": pt["holdout_sha256"],
            "parametros_serializados": cand["treino"]["parametros"],
            "vocabulario": len(cand["vocabulario"]),
            "cabecas_serializadas": False,
            "checkpoint_publico_alterado": False,
        },
        "treino": {
            **treino_info,
            "segundos_total_com_avaliacao": round(time.monotonic() - inicio, 2),
            "checkpoint_sha256": sha256(destino),
        },
        "controles": {
            "controle_1x": aval["controle_1x"],
            "fatorial": aval["fatorial"],
            "aux146": aval["aux146"],
        },
        "candidato": aval["escola"],
        "criterio": criterio,
        "aprovado_experimentalmente": bool(criterio["sucesso_conjunto"]),
        "ativo_no_chat": False,
        "limite": "Prova prospectiva autoral/sintética; não equivale a avaliação humana geral.",
    }
    gravar_json(DIR / "resultados.json", result)
    (DIR / "RELATORIO.md").write_text(resumo(result), encoding="utf-8")
    print(json.dumps({"criterio": criterio, "professores": treino_info["professores"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    executar()
