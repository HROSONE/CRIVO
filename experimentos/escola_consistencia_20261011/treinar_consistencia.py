"""Terceira aula da Escola Cognitiva: consistencia contrastiva no estado interno.

A classificacao auxiliar ocorre SOMENTE na linguagem real. A segunda vista nao
recebe rótulo classificatorio: ela serve apenas como positivo semantico. Um
negativo de classe diferente no mesmo lote deve ficar mais distante. As cabecas
e a perda contrastiva existem apenas no treino; o checkpoint final continua com
os mesmos 81.433 parametros.
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
SCHOOL148 = RAIZ / "experimentos" / "escola_cognitiva_20261011"
SCHOOL149 = RAIZ / "experimentos" / "escola_contrastiva_20261011"
for pth in (RAIZ, AUX146, SCHOOL148, SCHOOL149):
    sys.path.insert(0, str(pth))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq
from treinar_dialogo_seq2seq import lote
import treinar_auxiliar as base_aux
import treinar_contraste as multi
from escola import MAPA_OPERACOES, PROFESSORES, rotulos_da_operacao


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


def labels_professor(exemplos, nome):
    ids = PROFESSORES[nome].ids
    out = []
    for e in exemplos:
        op = e.get("operacao")
        out.append(ids[rotulos_da_operacao(op)[nome]] if op in MAPA_OPERACOES else -1)
    return out


def retroprop_estado(p, batch, dinicial, estado):
    """Retropropaga um gradiente arbitrario aplicado ao estado inicial da GRU."""
    inicial, fim, fwd, bwd, caches = estado
    grad = {k: np.zeros_like(v) for k, v in p.items()}
    di = dinicial * (1 - inicial * inicial)
    grad["I"] += fim.T @ di
    grad["bi"] += di.sum(axis=0)
    dfim = di @ p["I"].T
    h = p["I"].shape[1]
    dfwd = np.zeros_like(fwd)
    dbwd = np.zeros_like(bwd)
    dfwd[:, -1] += dfim[:, :h]
    dbwd[:, 0] += dfim[:, h:]
    demb = np.zeros((batch["fonte"].shape[0], batch["fonte"].shape[1], p["E"].shape[1]), dtype=p["E"].dtype)
    for nome, dsaida in (("EF", dfwd), ("EB", dbwd)):
        dh = np.zeros((batch["fonte"].shape[0], h), dtype=p["E"].dtype)
        for j, cache in reversed(caches[nome]):
            de, dh = base_aux._gru_grad(p, grad, dh + dsaida[:, j], cache, nome)
            demb[:, j] += de
    base_aux._grad_embeddings(grad, batch["fonte"], batch["chars_fonte"], batch["pesos_chars_fonte"], demb)
    return grad


def gradiente_triplet(p, batch_orig, batch_pos, labels, margem):
    """Triplet loss: original perto da vista equivalente e longe do negativo mais proximo."""
    est_o = base_aux.estado_inicial_com_cache(p, batch_orig)
    est_p = base_aux.estado_inicial_com_cache(p, batch_pos)
    ho, hp = est_o[0], est_p[0]
    labels = np.asarray(labels, dtype=np.int64)
    validos = np.flatnonzero(labels >= 0).tolist()
    do = np.zeros_like(ho)
    dp = np.zeros_like(hp)
    perdas = 0.0
    satisfeitos = 0
    total = len(validos)
    d = ho.shape[1]
    if not total:
        return 0.0, {k: np.zeros_like(v) for k, v in p.items()}, 0, 0

    for i in validos:
        candidatos = [j for j in validos if j != i and labels[j] != labels[i]]
        if not candidatos:
            continue
        # negativo mais dificil do lote, mas sempre de classe diferente
        j = min(candidatos, key=lambda x: float(np.mean((ho[i] - hp[x]) ** 2)))
        diff_pos = ho[i] - hp[i]
        diff_neg = ho[i] - hp[j]
        pos = float(np.mean(diff_pos * diff_pos))
        neg = float(np.mean(diff_neg * diff_neg))
        bruto = pos - neg + margem
        if bruto <= 0:
            satisfeitos += 1
            continue
        perdas += bruto
        escala = 2.0 / d / total
        do[i] += escala * (diff_pos - diff_neg)
        dp[i] += escala * (-diff_pos)
        dp[j] += escala * diff_neg

    go = retroprop_estado(p, batch_orig, do, est_o)
    gp = retroprop_estado(p, batch_pos, dp, est_p)
    grad = {k: go[k] + gp[k] for k in p}
    return perdas / max(1, total), grad, satisfeitos, total


class ProfessorConsistencia:
    """Substitui, em pares, a segunda CE auxiliar do PR149 por triplet loss."""
    def __init__(self, original, margem):
        self.original = original
        self.margem = float(margem)
        self.pendente = None
        self.chamadas = 0

    def __call__(self, p, batch, labels, waux, baux):
        par = self.chamadas % 2
        self.chamadas += 1
        if par == 0:
            resultado = self.original(p, batch, labels, waux, baux)
            self.pendente = (batch, list(labels))
            return resultado
        if self.pendente is None:
            raise ValueError("Vista positiva apareceu sem original")
        batch_orig, labels_orig = self.pendente
        self.pendente = None
        if list(labels) != labels_orig:
            raise ValueError("Rotulos mudaram entre original e positivo")
        perda, grad, ok, n = gradiente_triplet(p, batch_orig, batch, labels_orig, self.margem)
        return perda, grad, np.zeros_like(waux), np.zeros_like(baux), ok, n


def avaliar_triplet(dados, exemplos_raw, curriculo, corpus_treino, margem, lote_tamanho=64):
    modelo = DialogoSeq2Seq(dados)
    p = {k: np.asarray(v, dtype=np.float32) for k, v in dados["pesos"].items()}
    indices = {t: i for i, t in enumerate(modelo.vocabulario)}
    lex = multi.construir_lexicos(corpus_treino)
    saida = {}
    for nome in PROFESSORES:
        rot = [e for e in exemplos_raw if e.get("operacao") in MAPA_OPERACOES]
        total = satisfeitos = 0
        pos_soma = neg_soma = 0.0
        pares = 0
        for ini in range(0, len(rot), lote_tamanho):
            es = rot[ini:ini + lote_tamanho]
            orig = lote([texto(e) for e in es], indices, modelo.buckets, modelo.limite_fonte, 64)
            inv = lote([multi.vista_invariante(e, nome, curriculo, lex) for e in es], indices, modelo.buckets, modelo.limite_fonte, 64)
            ho = base_aux.estado_inicial_com_cache(p, orig)[0]
            hp = base_aux.estado_inicial_com_cache(p, inv)[0]
            labs = np.asarray(labels_professor(es, nome), dtype=np.int64)
            validos = np.flatnonzero(labs >= 0).tolist()
            for i in validos:
                candidatos = [j for j in validos if j != i and labs[j] != labs[i]]
                total += 1
                if not candidatos:
                    continue
                j = min(candidatos, key=lambda x: float(np.mean((ho[i] - hp[x]) ** 2)))
                pos = float(np.mean((ho[i] - hp[i]) ** 2))
                neg = float(np.mean((ho[i] - hp[j]) ** 2))
                pos_soma += pos; neg_soma += neg; pares += 1
                satisfeitos += int(pos + margem <= neg)
        saida[nome] = {
            "total": total,
            "pares_com_negativo": pares,
            "satisfeitos": satisfeitos,
            "taxa_satisfacao": satisfeitos / max(1, total),
            "distancia_positiva_media": pos_soma / max(1, pares),
            "distancia_negativa_media": neg_soma / max(1, pares),
            "margem_media": (neg_soma - pos_soma) / max(1, pares),
        }
    return saida


def resumo(r):
    n = r["candidato"]; p = r["criterio"]
    t = r["representacao_triplet_dev"]
    linhas = [
        "# Escola Cognitiva — consistencia representacional", "",
        "Classificacao somente na linguagem real; a segunda vista ensina proximidade semantica por triplet loss.", "",
        f"- Professor AÇÃO dev: **{100*r['treino']['professores']['acao']['validacao_rotulada']['acuracia']:.1f}%**.",
        f"- Professor FOCO dev: **{100*r['treino']['professores']['foco']['validacao_rotulada']['acuracia']:.1f}%**.",
        f"- Triplet AÇÃO dev: **{100*t['acao']['taxa_satisfacao']:.1f}%**; FOCO: **{100*t['foco']['taxa_satisfacao']:.1f}%**.",
        f"- old334: **{n['old334']['geracao']['iguais_ao_alvo']}/334**, CE **{n['old334']['perda']['entropia_cruzada']:.3f}**.",
        f"- known94: **{n['known94']['geracao']['iguais_ao_alvo']}/94**, CE **{n['known94']['perda']['entropia_cruzada']:.3f}**.",
        f"- fatorial96 operações: **{100*n['fatorial96']['operacoes']['taxa']:.1f}%**.",
        f"- holdout #146: **{100*n['holdout146']['operacoes']['taxa']:.1f}%**; #148: **{100*n['holdout148']['operacoes']['taxa']:.1f}%**; #149: **{100*n['holdout149']['operacoes']['taxa']:.1f}%**.",
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
    manifesto = ler_json(DIR / "manifesto_holdout.json")
    holdout_path = DIR / "holdout_consistencia.json"
    curriculo_path = RAIZ / pt["curriculo_reutilizado"]
    curriculo = ler_json(curriculo_path)
    if sha256(DIR / "protocolo.json") != pt["protocolo_sha256"]: raise ValueError("Protocolo mudou")
    if not manifesto.get("aprovado") or sha256(holdout_path) != pt["holdout_sha256"]: raise ValueError("Holdout nao congelado")
    if sha256(curriculo_path) != pt["curriculo_sha256"]: raise ValueError("Curriculo base mudou")

    corpus_path = FAT / "corpus_fatorial.json.gz"
    init_path = OLD / "inicializacao_sessoes.json.gz"
    destino = DIR / "checkpoint_consistencia.json.gz"
    if destino.exists(): raise ValueError("Candidato unico ja existe")

    original_grad = base_aux.gradiente_auxiliar
    patch = ProfessorConsistencia(original_grad, pt["pesos"]["margem_triplet_mse"])
    base_aux.gradiente_auxiliar = patch
    inicio = time.monotonic()
    try:
        cand, treino_info = multi.treinar(corpus_path, init_path, protocolo, pt, curriculo)
    finally:
        base_aux.gradiente_auxiliar = original_grad
    if patch.pendente is not None or patch.chamadas % 2:
        raise ValueError("Pareamento de vistas ficou incompleto")
    cand["experimento"] = "escola-consistencia-representacao-20261011"
    cand["sha256_holdout"] = pt["holdout_sha256"]
    cand["aprovado"] = False; cand["ativo_no_chat"] = False
    cand["escola_cognitiva"]["metodo"] = "classificacao_real_mais_triplet_consistencia"
    gravar_gz(destino, cand)
    if sha256(holdout_path) != pt["holdout_sha256"]: raise ValueError("Holdout mudou durante treino")

    bruto = ler_json(corpus_path)
    corpus = bruto["exemplos"] if isinstance(bruto, dict) else bruto
    treino_raw = [e for e in corpus if e.get("split") == "treino"]
    valid_raw = [e for e in corpus if e.get("split") == "validacao" and e.get("operacao") in MAPA_OPERACOES]
    triplet_dev = avaliar_triplet(cand, valid_raw, curriculo, treino_raw, pt["pesos"]["margem_triplet_mse"])

    old = ler_json(OLD / "corpus_sessoes.json.gz")["exemplos"]
    old334 = [e for e in old if e.get("split") == "validacao" and e.get("grupo") != "sessao_completa"]
    known94 = [e for e in old if e.get("split") == "validacao" and e.get("grupo") == "sessao_completa"]
    fat96 = ler_json(FAT / "avaliacao_final_fatorial.json")["exemplos"]
    h146 = ler_json(AUX146 / "holdout_novo.json")["exemplos"]
    h148 = ler_json(SCHOOL148 / "holdout_escola.json")["exemplos"]
    h149 = ler_json(SCHOOL149 / "holdout_contraste.json")["exemplos"]
    h180 = ler_json(holdout_path)["exemplos"]
    if tuple(map(len, (old334, known94, fat96, h146, h148, h149, h180))) != (334, 94, 96, 144, 144, 180, 180):
        raise ValueError("Recortes de avaliacao mudaram")

    caminhos = {
        "controle_1x": OLD / "checkpoint_sessoes.json.gz",
        "fatorial": FAT / "checkpoint_fatorial.json.gz",
        "aux146": AUX146 / "checkpoint_auxiliar.json.gz",
        "escola148": SCHOOL148 / "checkpoint_escola.json.gz",
        "escola149": SCHOOL149 / "checkpoint_contraste.json.gz",
    }
    modelos = {k: ler_json(v) for k, v in caminhos.items()}
    modelos["consistencia"] = cand
    blocos = {"old334": old334, "known94": known94, "fatorial96": fat96, "holdout146": h146, "holdout148": h148, "holdout149": h149, "holdout180": h180}
    aval = {}
    for nome, dados in modelos.items():
        aval[nome] = {}
        for bloco, exs in blocos.items():
            aval[nome][bloco] = base_aux.avaliar_bloco(dados, exs, bloco not in ("old334", "known94"))

    n = aval["consistencia"]
    baselines = [aval[k] for k in ("controle_1x", "fatorial", "aux146", "escola148", "escola149")]
    best_ce = min(x["holdout180"]["perda"]["entropia_cruzada"] for x in baselines)
    best_first = max(x["holdout180"]["primeiro_token"]["acuracia"] for x in baselines)
    best_ops = max(x["holdout180"]["operacoes"]["taxa"] for x in baselines)
    ce = n["holdout180"]["perda"]["entropia_cruzada"]
    first = n["holdout180"]["primeiro_token"]["acuracia"]
    ops = n["holdout180"]["operacoes"]["taxa"]
    ganho_ce = (best_ce - ce) / max(best_ce, 1e-12)
    ganho_first = first - best_first
    ganho_ops = ops - best_ops
    min_op = min(v["taxa"] for v in n["holdout180"]["operacoes"]["por_operacao"].values())
    pa = treino_info["professores"]["acao"]["validacao_rotulada"]["acuracia"]
    pf = treino_info["professores"]["foco"]["validacao_rotulada"]["acuracia"]
    trip_min = min(v["taxa_satisfacao"] for v in triplet_dev.values())
    g = pt["portao"]
    criterio = {
        "old334_exatas": n["old334"]["geracao"]["iguais_ao_alvo"] >= g["old334_exatas_min"],
        "old334_ce": n["old334"]["perda"]["entropia_cruzada"] <= g["old334_ce_max"],
        "known94_exatas": n["known94"]["geracao"]["iguais_ao_alvo"] >= g["known94_exatas_min"],
        "known94_ce": n["known94"]["perda"]["entropia_cruzada"] <= g["known94_ce_max"],
        "fatorial96_operacoes": n["fatorial96"]["operacoes"]["taxa"] >= g["fatorial96_operacoes_min"],
        "holdout146_operacoes": n["holdout146"]["operacoes"]["taxa"] >= g["holdout146_operacoes_min"],
        "holdout148_operacoes": n["holdout148"]["operacoes"]["taxa"] >= g["holdout148_operacoes_min"],
        "holdout149_operacoes": n["holdout149"]["operacoes"]["taxa"] >= g["holdout149_operacoes_min"],
        "professor_acao_dev": pa >= g["professor_acao_dev_min"],
        "professor_foco_dev": pf >= g["professor_foco_dev_min"],
        "triplet_dev": trip_min >= g["triplet_dev_satisfacao_min"],
        "novo_ce": ganho_ce >= g["novo_holdout_ce_melhora_relativa_vs_melhor_baseline_min"],
        "novo_primeiro": ganho_first >= g["novo_holdout_primeiro_ganho_vs_melhor_baseline_min"],
        "novo_operacoes_ganho": ganho_ops >= g["novo_holdout_operacoes_ganho_vs_melhor_baseline_min"],
        "novo_operacoes_total": ops >= g["novo_holdout_operacoes_total_min"],
        "novo_operacao_individual": min_op >= g["novo_holdout_operacao_individual_min"],
        "ganho_ce_relativo": ganho_ce,
        "ganho_primeiro_pp": ganho_first,
        "ganho_operacoes_pp": ganho_ops,
        "min_operacao": min_op,
        "triplet_dev_min": trip_min,
    }
    chaves = [k for k, v in criterio.items() if isinstance(v, bool)]
    criterio["sucesso_conjunto"] = all(criterio[k] for k in chaves)
    resultado = {
        "base_commit": pt["base_commit"],
        "integridade": {
            "um_unico_candidato": True,
            "holdout_aberto_pos_selecao": True,
            "holdout_sha256": pt["holdout_sha256"],
            "parametros_serializados": cand["treino"]["parametros"],
            "vocabulario": len(cand["vocabulario"]),
            "checkpoint_publico_alterado": False,
        },
        "treino": {**treino_info, "segundos_total_com_avaliacao": round(time.monotonic() - inicio, 2), "checkpoint_sha256": sha256(destino)},
        "representacao_triplet_dev": triplet_dev,
        "controles": {k: aval[k] for k in aval if k != "consistencia"},
        "candidato": n,
        "criterio": criterio,
        "aprovado_experimentalmente": bool(criterio["sucesso_conjunto"]),
        "ativo_no_chat": False,
    }
    gravar_json(DIR / "resultados.json", resultado)
    (DIR / "RELATORIO.md").write_text(resumo(resultado), encoding="utf-8")
    print(json.dumps({"criterio": criterio, "triplet_dev": triplet_dev, "professores": treino_info["professores"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    executar()
