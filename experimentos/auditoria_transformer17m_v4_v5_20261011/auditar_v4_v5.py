#!/usr/bin/env python3
"""Auditoria pareada V1/V4/V5 sem treino, promoção ou alteração de pesos."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter
from pathlib import Path

import torch

AQUI = Path(__file__).resolve().parent
HOLDOUT_SHA = "ad6e539d5b2bee8bf5a7aeff077fa822c3f5d3f36aa9e39b9748f8877d1dd29a"
GERADOR_SHA = "ef0854b94009699852507f24624f002f2800ff20d26cab79c90b005cfb828e2a"
V1_SHA = "849bc4655820f8cd1f445539a1bd0f01959f03ce38145ece460c0fe27568c661"
V4_COMPOSTO = "c53981fda15f31fcc22b3355a8eb75551ce85907926960c1776774db0d9f2cda"
V5_COMPOSTO = "03a0bdc2241d01029df2ff34e2dc2aace1209bf90e6303ce50c9bb9b41758a89"


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_json(o):
    return hashlib.sha256(json.dumps(
        o, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def carregar_ponte(tb, pasta):
    ponte = tb.PonteBinding()
    estado = torch.load(Path(pasta) / "ponte_binding.pt", map_location="cpu", weights_only=True)
    ponte.load_state_dict(estado["estado"], strict=True)
    ponte.eval()
    return ponte


def subseq(seq, alvo):
    if not alvo:
        return -1
    for i in range(len(seq) - len(alvo) + 1):
        if seq[i:i + len(alvo)] == alvo:
            return i
    return -1


def span_slot(tb, tok, fonte, valor, inicio):
    candidatos = [tb.cod(tok, valor), tb.cod(tok, " " + valor)]
    for ids in candidatos:
        if ids and fonte[inicio:inicio + len(ids)] == ids:
            return ids
    for ids in candidatos:
        if ids and subseq(fonte, ids) >= 0:
            return ids
    return []


RELEVANTES = {
    "recordar_pessoa": ("pessoa",),
    "recordar_objeto": ("objeto",),
    "corrigir_pessoa": ("pessoa",),
    "guardar_hipotese": ("atividade",),
    "mensagem_sem_horario": ("pessoa", "atividade"),
    "pedir_detalhe": ("pessoa",),
}


def diagnostico_tokens(tb, modelo, ponte, tok, exs):
    fim = tok.token_to_id("<fim>")
    assist = tok.token_to_id("<assistente>")
    proib = [tok.token_to_id(x) for x in tb.ESPECIAIS[:-1]]
    total_resp = acerto_tf = total_slot = acerto_slot = 0
    diverg = Counter()
    spans = Counter()
    fonte_cobre = fonte_total = 0
    linhas = []
    for ex in exs:
        z = tb.preparar(tok, ex, modelo.config.contexto)
        x = torch.tensor([z["x"]], dtype=torch.long)
        pos = torch.tensor([z["pos"]], dtype=torch.long)
        _, log, _, _, _, _ = tb.forward_bridge(modelo, ponte, x, pos, False, None, None)
        alvo = tb.cod(tok, ex["resposta"]) + [fim]
        pred_tf = [int(log[0, z["pos"] + j].argmax()) for j in range(len(alvo))]
        total_resp += len(alvo)
        acerto_tf += sum(a == b for a, b in zip(alvo, pred_tf))

        slot_indices = set()
        slot_inicio = slot_fim = None
        for s in RELEVANTES[ex["operacao"]]:
            valor = ex["slots"][s]
            ids = span_slot(tb, tok, z["fonte"], valor, z["ptr"][s])
            spans[len(ids)] += 1
            alvo_sem_fim = alvo[:-1]
            candidatos = [tb.cod(tok, valor), tb.cod(tok, " " + valor)]
            achados = [(subseq(alvo_sem_fim, c), len(c)) for c in candidatos if c]
            achados = [q for q in achados if q[0] >= 0]
            if achados:
                p, n = min(achados, key=lambda q: q[0])
                slot_indices.update(range(p, p + n))
                slot_inicio = p if slot_inicio is None else min(slot_inicio, p)
                slot_fim = p + n if slot_fim is None else max(slot_fim, p + n)
                fonte_total += 1
                if any(subseq(z["fonte"], c) >= 0 for c in candidatos if c):
                    fonte_cobre += 1
        for j in slot_indices:
            if j < len(alvo):
                total_slot += 1
                acerto_slot += int(pred_tf[j] == alvo[j])

        ger, terminou = tb.gerar_bridge(modelo, ponte, z["fonte"], fim, assist, 48, proib)
        n = max(len(ger), len(alvo) - 1)
        d = None
        for j in range(n):
            g = ger[j] if j < len(ger) else None
            a = alvo[j] if j < len(alvo) - 1 else None
            if g != a:
                d = j
                break
        if d is None:
            diverg["sem_divergencia_antes_eos"] += 1
        elif slot_inicio is None or d < slot_inicio:
            diverg["antes_do_slot"] += 1
        elif d < slot_fim:
            diverg["dentro_do_slot"] += 1
        else:
            diverg["depois_do_slot"] += 1
        if len(linhas) < 20:
            linhas.append({
                "id": ex["id"], "operacao": ex["operacao"],
                "primeira_divergencia": d,
                "slot_inicio": slot_inicio, "slot_fim": slot_fim,
                "terminou": terminou, "alvo": ex["resposta"],
                "gerado": tok.decode(ger),
            })
    return {
        "teacher_forced_token_acc": acerto_tf / max(total_resp, 1),
        "teacher_forced_slot_token_acc": acerto_slot / max(total_slot, 1),
        "tokens_resposta": total_resp,
        "tokens_slot": total_slot,
        "cobertura_fonte_span_slot": fonte_cobre / max(fonte_total, 1),
        "comprimento_spans_slot": dict(sorted(spans.items())),
        "primeira_divergencia": dict(diverg),
        "amostra": linhas,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v1", required=True)
    ap.add_argument("--v4", required=True)
    ap.add_argument("--v5", required=True)
    ap.add_argument("--ref-v4", required=True)
    ap.add_argument("--ref-v5", required=True)
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()

    import holdout_neutro as hn
    if sha_bytes((AQUI / "holdout_neutro.py").read_bytes()) != GERADOR_SHA:
        raise SystemExit("gerador neutro mudou")
    exs = hn.gerar()
    pacote = {
        "versao": 1, "semente": hn.SEMENTE, "congelado_antes_da_auditoria": True,
        "auditoria": {
            "exemplos": len(exs), "familias": len(hn.FAMILIAS),
            "mensagens_exatas_repetidas": len(exs) - len({x["mensagem"] for x in exs}),
            "por_operacao": {op: sum(x["operacao"] == op for x in exs) for op in hn.OPERACOES},
        }, "exemplos": exs,
    }
    if sha_json(pacote) != HOLDOUT_SHA:
        raise SystemExit("holdout neutro mudou")

    ref4, ref5 = Path(a.ref_v4), Path(a.ref_v5)
    tb4 = load("auditoria_tb4", ref4 / "experimentos/escola_transformer_17m_binding_bridge_v4_20261011/treinar_bridge.py")
    v5 = load("auditoria_v5", ref5 / "experimentos/escola_transformer_17m_midbridge_v5_20261011/executar_midbridge_v5.py")
    tb5 = v5.tb

    treino = tb4.gerar_treino()
    texto = "\n".join(
        [x["mensagem"] for x in treino] +
        [h["texto"] for x in treino for h in x["historico"]]
    ).casefold()
    vazamento = [f[0] for f in hn.FAMILIAS if f[0].casefold() in texto]
    if vazamento:
        raise SystemExit("família neutra apareceu no treino: " + repr(vazamento))

    meta4 = json.loads((Path(a.v4) / "meta.json").read_text(encoding="utf-8"))
    meta5 = json.loads((Path(a.v5) / "meta.json").read_text(encoding="utf-8"))
    if meta4["checkpoint_composto_sha256"] != V4_COMPOSTO:
        raise SystemExit("checkpoint V4 diferente")
    if meta5["checkpoint_composto_sha256"] != V5_COMPOSTO:
        raise SystemExit("checkpoint V5 diferente")
    if tb4.sha(Path(a.v1) / "pesos.pt") != V1_SHA:
        raise SystemExit("checkpoint V1 diferente")

    base, t0, _ = tb4.carregar_checkpoint(a.v1, "cpu", True)
    m4, t4, _ = tb4.carregar_checkpoint(a.v4, "cpu", False)
    p4 = carregar_ponte(tb4, a.v4)
    m5, t5, _ = tb5.carregar_checkpoint(a.v5, "cpu", False)
    p5 = carregar_ponte(tb5, a.v5)

    diferentes = []
    for ex in exs:
        z4 = tb4.preparar(t4, ex, m4.config.contexto)
        z5 = tb5.preparar(t5, ex, m5.config.contexto)
        for k in ("x", "y", "pos", "ptr", "fonte", "primeiro"):
            if z4[k] != z5[k]:
                diferentes.append({"id": ex["id"], "campo": k})
                break
    if diferentes:
        raise SystemExit("pré-processamento V4/V5 divergiu: " + json.dumps(diferentes[:10]))

    b = tb4.avaliar_base(base, t0, exs, "cpu")
    r4 = tb4.avaliar_candidato(m4, p4, t4, exs, "cpu")
    r5 = tb5.avaliar_candidato(m5, p5, t5, exs, "cpu")
    d4 = diagnostico_tokens(tb4, m4, p4, t4, exs)
    d5 = diagnostico_tokens(tb5, m5, p5, t5, exs)

    resumo = {
        "tipo": "auditoria_pareada_sem_treino",
        "holdout_sha256": HOLDOUT_SHA,
        "preprocessamento_identico": True,
        "vazamento_familias_treino": False,
        "v1": b, "v4": r4, "v5": r5,
        "diagnostico_v4": d4, "diagnostico_v5": d5,
        "delta_v5_menos_v4": {
            "ce": r5["ce"] - r4["ce"],
            "operacao": r5["operacao"] - r4["operacao"],
            "slot": r5["slot"] - r4["slot"],
            "primeiro_token": r5["primeiro_token"] - r4["primeiro_token"],
            "teacher_forced_token_acc": d5["teacher_forced_token_acc"] - d4["teacher_forced_token_acc"],
            "teacher_forced_slot_token_acc": d5["teacher_forced_slot_token_acc"] - d4["teacher_forced_slot_token_acc"],
        },
        "promocao_autorizada": False,
    }
    out = Path(a.saida)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
