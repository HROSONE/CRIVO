"""Escola Cognitiva: supervisao de ACAO e FOCO em subespacos fixos do estado.

ACAO recebe apenas as dimensoes 0:8, FOCO apenas 8:16 e 16:24 fica livre da
supervisao auxiliar. A geracao continua usando o estado completo. As cabecas
sao treino-only e o checkpoint final continua com 81.433 parametros.
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
OLD = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
FAT = RAIZ / "experimentos" / "corpus_fatorial_20261011"
AUX146 = RAIZ / "experimentos" / "ato_auxiliar_dialogo_20261011"
S148 = RAIZ / "experimentos" / "escola_cognitiva_20261011"
S149 = RAIZ / "experimentos" / "escola_contrastiva_20261011"
S150 = RAIZ / "experimentos" / "escola_consistencia_20261011"

sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AUX146))
sys.path.insert(0, str(S148))

from arquivos_contextuais import ler_json
import treinar_auxiliar as base_aux
import treinar_escola as escola148
from escola import PROFESSORES, validar_escola

ORIGINAL_GRAD_AUX = base_aux.gradiente_auxiliar
SUBESPACOS = {"acao": (0, 8), "foco": (8, 16), "livre": (16, 24)}


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


def criar_cabecas_subespaco(hidden: int, seed: int):
    if hidden != 24:
        raise ValueError("Esta ablacao foi congelada para estado de 24 dimensoes")
    cabecas = {}
    for i, (nome, professor) in enumerate(PROFESSORES.items()):
        inicio, fim = SUBESPACOS[nome]
        rng = np.random.default_rng(seed + 7919 + 104729 * i)
        w = np.zeros((hidden, len(professor.classes)), dtype=np.float32)
        w[inicio:fim] = rng.normal(0, 1 / math.sqrt(fim - inicio), (fim - inicio, len(professor.classes))).astype(np.float32)
        b = np.zeros(len(professor.classes), dtype=np.float32)
        cabecas[nome] = {
            "w": w, "b": b,
            "mw": np.zeros_like(w), "vw": np.zeros_like(w),
            "mb": np.zeros_like(b), "vb": np.zeros_like(b),
        }
    return cabecas


def gradiente_subespaco(p, batch, labels, waux, baux):
    """Usa o gradiente original, mas a cabeca tem suporte em apenas 8 dimensoes."""
    suporte = np.any(np.abs(waux) > 0, axis=1)
    if int(suporte.sum()) != 8:
        raise ValueError(f"Cabeca fora do subespaco congelado: {int(suporte.sum())} dimensoes ativas")
    perda, grad, gw, gb, corretos, total = ORIGINAL_GRAD_AUX(p, batch, labels, waux, baux)
    gw[~suporte] = 0.0
    if np.any(gw[~suporte] != 0):
        raise ValueError("Gradiente vazou para fora do subespaco")
    return perda, grad, gw, gb, corretos, total


def resumo(r):
    n = r["candidato"]
    p = r["criterio"]
    prof = r["treino"]["professores"]
    linhas = [
        "# Escola Cognitiva — subespacos internos",
        "",
        "ACAO usa somente dimensoes **0–7**, FOCO **8–15** e **16–23** fica livre da supervisao auxiliar. O decoder continua vendo as 24 dimensoes.",
        "",
        f"- Professor ACAO dev: **{100*prof['acao']['validacao_rotulada']['acuracia']:.1f}%**.",
        f"- Professor FOCO dev: **{100*prof['foco']['validacao_rotulada']['acuracia']:.1f}%**.",
        f"- old334: **{n['old334']['geracao']['iguais_ao_alvo']}/334**, CE **{n['old334']['perda']['entropia_cruzada']:.3f}**.",
        f"- known94: **{n['known94']['geracao']['iguais_ao_alvo']}/94**, CE **{n['known94']['perda']['entropia_cruzada']:.3f}**.",
        f"- fatorial96 operacoes: **{100*n['fatorial96']['operacoes']['taxa']:.1f}%**.",
        f"- holdouts conhecidos #146/#148/#149/#150: **{100*n['holdout146']['operacoes']['taxa']:.1f}% / {100*n['holdout148']['operacoes']['taxa']:.1f}% / {100*n['holdout149']['operacoes']['taxa']:.1f}% / {100*n['holdout150']['operacoes']['taxa']:.1f}%**.",
        f"- prova nova 180: CE **{n['novo180']['perda']['entropia_cruzada']:.3f}**, primeiro token **{100*n['novo180']['primeiro_token']['acuracia']:.1f}%**, operacoes **{100*n['novo180']['operacoes']['taxa']:.1f}%**.",
        "", "## Gate congelado", "",
    ]
    for k, v in p.items():
        if isinstance(v, bool):
            linhas.append(f"- {k}: **{'PASSOU' if v else 'FALHOU'}**.")
    linhas += ["", f"**Sucesso conjunto: {'SIM' if p['sucesso_conjunto'] else 'NAO'}.**", "", "Nenhuma promocao automatica; `ativo_no_chat=false`."]
    return "\n".join(linhas) + "\n"


def executar():
    validar_escola()
    protocolo = ler_json(DIR / "protocolo.json")
    pt = ler_json(DIR / "protocolo_treino.json")
    manifesto = ler_json(DIR / "manifesto_holdout.json")
    holdout = DIR / "holdout_subespacos.json"
    corpus = RAIZ / protocolo["fontes"]["corpus"]
    init = RAIZ / protocolo["fontes"]["inicializacao"]

    if sha256(DIR / "protocolo.json") != pt["protocolo_sha256"]:
        raise ValueError("Protocolo mudou apos congelamento")
    if not manifesto.get("aprovado") or sha256(holdout) != pt["holdout_sha256"]:
        raise ValueError("Holdout prospectivo nao esta congelado")
    if sha256(corpus) != pt["corpus_sha256"] or sha256(init) != pt["inicializacao_sha256"]:
        raise ValueError("Fontes de treino mudaram")

    destino = DIR / "checkpoint_subespacos.json.gz"
    if destino.exists():
        raise ValueError("Candidato unico ja existe")

    # Injeta a pedagogia da aula sem alterar a implementacao de producao.
    escola148.criar_cabecas = criar_cabecas_subespaco
    escola148.base_aux.gradiente_auxiliar = gradiente_subespaco
    compat = {"modelo_producao": {"parametros": 81433}}

    inicio = time.monotonic()
    cand, treino_info = escola148.treinar(corpus, init, compat, pt)
    cand.update(
        experimento="escola-subespacos-20261011",
        subespacos={k: list(v) for k, v in SUBESPACOS.items()},
        professores_descartados=True,
        aprovado=False,
        ativo_no_chat=False,
        sha256_holdout=pt["holdout_sha256"],
    )
    gravar_gz(destino, cand)

    if sha256(holdout) != pt["holdout_sha256"]:
        raise ValueError("Holdout mudou durante treino")

    old = ler_json(OLD / "corpus_sessoes.json.gz")["exemplos"]
    old334 = [e for e in old if e.get("split") == "validacao" and e.get("grupo") != "sessao_completa"]
    known94 = [e for e in old if e.get("split") == "validacao" and e.get("grupo") == "sessao_completa"]
    fat96 = ler_json(FAT / "avaliacao_final_fatorial.json")["exemplos"]
    h146 = ler_json(AUX146 / "holdout_novo.json")["exemplos"]
    h148 = ler_json(S148 / "holdout_escola.json")["exemplos"]
    h149 = ler_json(S149 / "holdout_contraste.json")["exemplos"]
    h150 = ler_json(S150 / "holdout_consistencia.json")["exemplos"]
    novo = ler_json(holdout)["exemplos"]
    if (len(old334), len(known94), len(fat96), len(h146), len(h148), len(h149), len(h150), len(novo)) != (334, 94, 96, 144, 144, 180, 180, 180):
        raise ValueError("Recortes de avaliacao mudaram")

    caminhos = {
        "controle_1x": OLD / "checkpoint_sessoes.json.gz",
        "fatorial": FAT / "checkpoint_fatorial.json.gz",
        "aux146": AUX146 / "checkpoint_auxiliar.json.gz",
        "escola148": S148 / "checkpoint_escola.json.gz",
        "contraste149": S149 / "checkpoint_contraste.json.gz",
        "consistencia150": S150 / "checkpoint_consistencia.json.gz",
    }
    modelos = {nome: ler_json(path) for nome, path in caminhos.items()}
    modelos["subespacos"] = cand

    blocos = {
        "old334": (old334, False), "known94": (known94, False),
        "fatorial96": (fat96, True), "holdout146": (h146, True),
        "holdout148": (h148, True), "holdout149": (h149, True),
        "holdout150": (h150, True), "novo180": (novo, True),
    }
    aval = {}
    for nome, dados in modelos.items():
        aval[nome] = {b: base_aux.avaliar_bloco(dados, exs, ops) for b, (exs, ops) in blocos.items()}

    n = aval["subespacos"]
    g = protocolo["portao"]
    baselines = [aval[k] for k in caminhos]
    best_ce = min(x["novo180"]["perda"]["entropia_cruzada"] for x in baselines)
    best_first = max(x["novo180"]["primeiro_token"]["acuracia"] for x in baselines)
    best_ops = max(x["novo180"]["operacoes"]["taxa"] for x in baselines)
    ce = n["novo180"]["perda"]["entropia_cruzada"]
    first = n["novo180"]["primeiro_token"]["acuracia"]
    ops = n["novo180"]["operacoes"]["taxa"]
    ganho_ce = (best_ce - ce) / max(best_ce, 1e-12)
    ganho_first = first - best_first
    ganho_ops = ops - best_ops
    min_op = min(v["taxa"] for v in n["novo180"]["operacoes"]["por_operacao"].values())
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
        "holdout149_operacoes": n["holdout149"]["operacoes"]["taxa"] >= g["holdout149_operacoes_min"],
        "holdout150_operacoes": n["holdout150"]["operacoes"]["taxa"] >= g["holdout150_operacoes_min"],
        "professor_acao_dev": pa >= g["professor_acao_dev_min"],
        "professor_foco_dev": pf >= g["professor_foco_dev_min"],
        "novo_ce": ganho_ce >= g["novo_ce_reducao_relativa_vs_melhor_baseline_min"],
        "novo_primeiro": ganho_first >= g["novo_primeiro_token_ganho_vs_melhor_baseline_min"],
        "novo_operacoes_ganho": ganho_ops >= g["novo_operacoes_ganho_vs_melhor_baseline_min"],
        "novo_operacoes_total": ops >= g["novo_operacoes_total_min"],
        "novo_operacao_individual": min_op >= g["novo_operacao_individual_min"],
        "ganho_ce_relativo": ganho_ce,
        "ganho_primeiro_pp": ganho_first,
        "ganho_operacoes_pp": ganho_ops,
        "min_operacao": min_op,
        "melhor_baseline_ce": best_ce,
        "melhor_baseline_primeiro": best_first,
        "melhor_baseline_operacoes": best_ops,
    }
    chaves = [k for k, v in criterio.items() if isinstance(v, bool)]
    criterio["sucesso_conjunto"] = all(criterio[k] for k in chaves)

    resultado = {
        "base_commit": pt["base_commit"],
        "integridade": {
            "um_unico_candidato": True,
            "prova_aberta_pos_selecao": True,
            "holdout_sha256": pt["holdout_sha256"],
            "parametros_serializados": cand["treino"]["parametros"],
            "vocabulario": len(cand["vocabulario"]),
            "cabecas_serializadas": False,
            "subespacos": {k: list(v) for k, v in SUBESPACOS.items()},
            "checkpoint_publico_alterado": False,
        },
        "treino": {**treino_info, "segundos_total_com_avaliacao": round(time.monotonic() - inicio, 2), "checkpoint_sha256": sha256(destino)},
        "controles": {k: aval[k] for k in caminhos},
        "candidato": n,
        "criterio": criterio,
        "aprovado_experimentalmente": bool(criterio["sucesso_conjunto"]),
        "ativo_no_chat": False,
        "limite": "Avaliacao prospectiva sintetica; nao equivale a avaliacao humana geral.",
    }
    gravar_json(DIR / "resultados.json", resultado)
    (DIR / "RELATORIO.md").write_text(resumo(resultado), encoding="utf-8")
    print(json.dumps({"criterio": criterio, "professores": treino_info["professores"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    executar()
