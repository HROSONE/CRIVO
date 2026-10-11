#!/usr/bin/env python3
"""V5 causal: injeta a ponte V4 no meio do Transformer, após o bloco 3.

Tudo o mais é herdado da V4: checkpoint V1, currículo, ponte, perdas,
hiperparâmetros, congelamento, avaliador e gates. A única intervenção funcional
é dar aos blocos 4-7 acesso ao delta de binding antes do LM head.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import shutil
import sys
from pathlib import Path

import torch
from torch.nn import functional as F

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
V4 = RAIZ / "experimentos" / "escola_transformer_17m_binding_bridge_v4_20261011"
sys.path[:0] = [str(AQUI), str(V4), str(RAIZ)]

import treinar_bridge as tb  # noqa:E402

# O protocolo V5 é local; treino/currículo e utilitários seguem V4.
tb.AQUI = AQUI


def abrir_holdout_v5():
    """Abre somente o holdout V5 e revalida seu pré-compromisso canônico."""
    man = json.loads((AQUI / "manifesto_holdout.json").read_text(encoding="utf-8"))
    gerador = AQUI / "preparar_holdout.py"
    if tb.sha(gerador) != man["gerador_sha256"]:
        raise ValueError("gerador do holdout V5 mudou")

    spec = importlib.util.spec_from_file_location("holdout_v5_runtime", gerador)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    ex = h.gerar()
    por = {op: sum(z["operacao"] == op for z in ex) for op in h.OPERACOES}
    repetidas = len(ex) - len({z["mensagem"] for z in ex})
    pacote = {
        "versao": 5,
        "semente": h.SEMENTE,
        "congelado_antes_do_treino": True,
        "auditoria": {
            "aprovado": True,
            "exemplos": 120,
            "familias": len(h.FAMILIAS),
            "mensagens_exatas_repetidas": repetidas,
            "por_operacao": por,
        },
        "exemplos": ex,
    }
    if tb.sha_json(pacote) != man["holdout_sha256_canonico"]:
        raise ValueError("hash do holdout V5 mudou")
    if len(ex) != 120 or set(por.values()) != {20} or repetidas != 15:
        raise ValueError("estrutura do holdout V5 mudou")
    return ex, man


def residuais_inferiores(m, ids, treino_topo=False):
    """Executa embeddings + blocos 0-3; na fase conjunta essa base fica congelada."""
    t = ids.shape[1]
    if treino_topo:
        with torch.no_grad():
            x = m.embedding(ids) + m.posicao(torch.arange(t, device=ids.device))
            for bloco in m.blocos[:4]:
                x = bloco(x)
        return x
    x = m.embedding(ids) + m.posicao(torch.arange(t, device=ids.device))
    for bloco in m.blocos[:4]:
        x = bloco(x)
    return x


def residuais_superiores(m, x):
    """Deixa os blocos 4-7 consumirem o binding antes da normalização/LM head."""
    for bloco in m.blocos[4:]:
        x = bloco(x)
    return x


def forward_midbridge(m, ponte, ids, pos, treino_topo=False, alvos=None, gate_alvo=None):
    baixo = residuais_inferiores(m, ids, treino_topo)
    baixo2, perdas, acertos, gates, gate_loss = ponte.forward_residual(
        baixo, m, pos, alvos, gate_alvo
    )
    alto = residuais_superiores(m, baixo2)
    h = m.norm(alto)
    return h, F.linear(h, m.embedding.weight), perdas, acertos, gates, gate_loss


# Toda a V4 (loss, treino, geração e avaliação) passa a consumir este forward.
tb.forward_bridge = forward_midbridge


def salvar_v5(m, ponte, t, entrada, saida, treino, resultados):
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(entrada) / "tokenizer.json", saida / "tokenizer.json")
    origem = torch.load(Path(entrada) / "pesos.pt", map_location="cpu", weights_only=True)
    estado = {
        "versao": 1,
        "modelo": {k: v.detach().cpu() for k, v in m.state_dict().items()},
        "config": tb.CONFIG,
        "passo": int(origem.get("passo", 0)) + tb.PASSOS,
        "execucao": {
            "tokenizer_sha256": tb.TOK_SHA,
            "semente": tb.SEMENTE,
            "pesos_externos": False,
            "escola_cognitiva": {
                "versao": 5,
                "origem_sha256": tb.V1_SHA,
                "warmup_ponte": tb.WARMUP,
                "passos": tb.PASSOS,
                "ponte_binding": True,
                "ponto_injecao": "apos_bloco_3_antes_bloco_4",
                "ativo_no_chat": False,
            },
        },
    }
    torch.save(estado, saida / "pesos.pt")
    torch.save(
        {
            "versao": 1,
            "estado": {k: v.detach().cpu() for k, v in ponte.state_dict().items()},
            "dimensao": 384,
            "slots": tb.SLOTS,
            "parametros": sum(p.numel() for p in ponte.parameters()),
            "ponto_injecao": "apos_bloco_3_antes_bloco_4",
        },
        saida / "ponte_binding.pt",
    )
    hp = tb.sha(saida / "pesos.pt")
    hb = tb.sha(saida / "ponte_binding.pt")
    composto = hashlib.sha256((hp + ":" + hb).encode()).hexdigest()
    meta = {
        "versao": 5,
        "modelo": "transformer_crivo_17m_midbridge_v5",
        "checkpoint_composto_sha256": composto,
        "pesos_sha256": hp,
        "ponte_sha256": hb,
        "tokenizer_sha256": tb.TOK_SHA,
        "parametros_base": tb.PARAMETROS_BASE,
        "parametros_ponte": sum(p.numel() for p in ponte.parameters()),
        "parametros_inferencia": tb.PARAMETROS_BASE + sum(p.numel() for p in ponte.parameters()),
        "ponto_injecao": "apos_bloco_3_antes_bloco_4",
        "ativo_no_chat": False,
        "elegivel_promocao": bool(resultados["gates"]["todos"]),
        "treino": treino,
    }
    (saida / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (saida / "resultados.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return composto, hp, hb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--dispositivo", default="cpu")
    a = ap.parse_args()
    dev = a.dispositivo

    random.seed(tb.SEMENTE)
    torch.manual_seed(tb.SEMENTE)
    torch.set_num_threads(2)

    candidato, tok, _ = tb.carregar_checkpoint(a.entrada, dev, True)
    ponte, info = tb.treinar(candidato, tok, dev)

    # O holdout V5 só é aberto depois que os 1.000 passos terminaram.
    hold, man = abrir_holdout_v5()
    base, tokb, _ = tb.carregar_checkpoint(a.entrada, dev, True)
    entrada = tb.avaliar_base(base, tokb, hold, dev)
    cand = tb.avaliar_candidato(candidato, ponte, tok, hold, dev)

    # Ablação diagnóstica: mesmos pesos V5, mas sem consumir a ponte na inferência.
    # Não participa dos gates; apenas mede se o LM de fato usa o binding.
    ablation = tb.avaliar_base(candidato, tok, hold, dev)

    preservados = json.loads(
        (V4 / "preservacao_portugues.json").read_text(encoding="utf-8")
    )
    if not preservados.get("congelado_antes_do_treino"):
        raise ValueError("preservação não congelada")
    p0 = tb.preservacao(base, tokb, preservados["textos"], dev)
    p1 = tb.preservacao(candidato, tok, preservados["textos"], dev)

    protocolo = json.loads((AQUI / "protocolo.json").read_text(encoding="utf-8"))
    g = protocolo["avaliacao"]["promocao"]
    cada = min(v["operacao_taxa"] for v in cand["por_operacao"].values())
    gs = {
        "operacao": cand["operacao"] >= g["operacao_min"],
        "cada_operacao": cada >= g["cada_operacao_min"],
        "slot": cand["slot"] >= g["slot_min"],
        "primeiro_token": cand["primeiro_token"] >= g["primeiro_token_min"],
        "ce_relativa": cand["ce"] <= entrada["ce"] * g["ce_relativa_max"],
        "preservacao": p1 <= p0 * g["preservacao_ce_relativa_max"],
    }
    resultados = {
        "versao": 5,
        "holdout_sha256": man["holdout_sha256_canonico"],
        "mudanca_causal_unica": "binding apos bloco 3, antes dos blocos 4-7",
        "treino": info,
        "entrada_v1": entrada,
        "candidato": cand,
        "ablacao_sem_ponte": ablation,
        "efeito_ponte": {
            "operacao_delta": cand["operacao"] - ablation["operacao"],
            "slot_delta": cand["slot"] - ablation["slot"],
            "primeiro_token_delta": cand["primeiro_token"] - ablation["primeiro_token"],
            "ce_delta": cand["ce"] - ablation["ce"],
        },
        "preservacao": {
            "entrada_ce": p0,
            "candidato_ce": p1,
            "relativa": p1 / p0,
        },
        "gates": {**gs, "todos": all(gs.values()), "min_operacao": cada},
        "ativo_no_chat": False,
    }
    composto, hp, hb = salvar_v5(
        candidato, ponte, tok, a.entrada, a.saida, info, resultados
    )
    resultados["checkpoint_composto_sha256"] = composto
    resultados["pesos_sha256"] = hp
    resultados["ponte_sha256"] = hb
    Path(a.saida, "resultados.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "checkpoint_composto_sha256": composto,
                "entrada": {
                    "ce": entrada["ce"],
                    "operacao": entrada["operacao"],
                    "slot": entrada["slot"],
                    "primeiro": entrada["primeiro_token"],
                },
                "candidato": {
                    "ce": cand["ce"],
                    "operacao": cand["operacao"],
                    "slot": cand["slot"],
                    "primeiro": cand["primeiro_token"],
                    "por_operacao": {
                        k: v["operacao_taxa"] for k, v in cand["por_operacao"].items()
                    },
                    "pointer": cand["pointer"],
                    "gate": cand["gate"],
                },
                "ablacao_sem_ponte": {
                    "ce": ablation["ce"],
                    "operacao": ablation["operacao"],
                    "slot": ablation["slot"],
                    "primeiro": ablation["primeiro_token"],
                },
                "efeito_ponte": resultados["efeito_ponte"],
                "preservacao_relativa": p1 / p0,
                "gates": resultados["gates"],
                "ativo_no_chat": False,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
