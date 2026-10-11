#!/usr/bin/env python3
"""Diagnóstico focal de recordar_objeto em V4/V5, sem treino e sem alterar pesos."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import auditar as au  # noqa:E402

ALVO_GATE = (False, True, False)
OPERACOES = (
    "recordar_pessoa", "recordar_objeto", "corrigir_pessoa",
    "guardar_hipotese", "mensagem_sem_horario", "pedir_detalhe",
)


def _menciona(texto, valor):
    return bool(valor) and au.norm(valor) in au.norm(texto)


def _top_tokens(t, logits, k=5):
    vals, ids = torch.topk(logits, k=min(k, logits.numel()))
    return [
        {
            "id": int(tok),
            "texto": t.decode([int(tok)]),
            "logit": float(val),
        }
        for val, tok in zip(vals.tolist(), ids.tolist())
    ]


@torch.no_grad()
def diagnosticar(nome, versao, pasta, exs, dispositivo="cpu"):
    m, t, _ = au.carregar_modelo(pasta, dispositivo)
    ponte, _ = au.carregar_ponte(pasta, dispositivo)
    casos = []

    for ex in exs:
        if ex["operacao"] != "recordar_objeto":
            continue
        z = au.preparar(t, ex, m.config.contexto)
        ids, terminou, hp = au.gerar(versao, m, t, z["fonte"], ponte)
        texto = t.decode(ids)
        alvo = z["resposta_ids"]
        prefixo = 0
        while prefixo < min(len(ids), len(alvo)) and ids[prefixo] == alvo[prefixo]:
            prefixo += 1

        x = torch.tensor([z["x"]], dtype=torch.long, device=dispositivo)
        pos = torch.tensor([z["pos"]], dtype=torch.long, device=dispositivo)
        log, gates, preds = au.forward_candidato(versao, m, ponte, x, pos)
        gate_probs = [float(v) for v in gates[0].tolist()]
        gate_bits = tuple(v >= .5 for v in gate_probs)

        ini, fim, tam = z["spans"]["objeto"]
        pred_obj = int(preds["objeto"][0])
        pred_pessoa = int(preds["pessoa"][0])
        pred_atividade = int(preds["atividade"][0])

        divergencia = None
        if prefixo < len(alvo):
            abs_pos = z["pos"] + prefixo
            esperado = int(alvo[prefixo])
            observado = int(ids[prefixo]) if prefixo < len(ids) else None
            divergencia = {
                "indice_resposta": prefixo,
                "esperado_id": esperado,
                "esperado_texto": t.decode([esperado]),
                "gerado_id": observado,
                "gerado_texto": t.decode([observado]) if observado is not None else None,
                "esperado_existe_na_fonte": esperado in z["fonte"],
                "top5_teacher_forced": _top_tokens(t, log[0, abs_pos], 5),
            }

        compat = []
        for op in OPERACOES:
            clone = dict(ex)
            clone["operacao"] = op
            slot_ok, op_ok = au.pontuar(clone, texto, terminou)
            if op_ok:
                compat.append(op)

        s = ex["slots"]
        casos.append({
            "id": ex["id"],
            "familia": ex["familia"],
            "turno": ex["turno"],
            "pergunta": ex["mensagem"],
            "esperado": ex["resposta"],
            "gerado": texto,
            "terminou": terminou,
            "prefixo_correto_tokens": prefixo,
            "objeto": s["objeto"],
            "pessoa": s["pessoa"],
            "atividade": s["atividade"],
            "menciona_objeto": _menciona(texto, s["objeto"]),
            "menciona_pessoa": _menciona(texto, s["pessoa"]),
            "menciona_atividade": _menciona(texto, s["atividade"]),
            "operacoes_compativeis_com_saida": compat,
            "gate_probs": {
                "pessoa": gate_probs[0],
                "objeto": gate_probs[1],
                "atividade": gate_probs[2],
            },
            "gate_bits": {
                "pessoa": gate_bits[0],
                "objeto": gate_bits[1],
                "atividade": gate_bits[2],
            },
            "gate_objeto_exato": gate_bits == ALVO_GATE,
            "pointer_objeto": {
                "pred": pred_obj,
                "inicio": ini,
                "fim_exclusivo": fim,
                "bpe_len": tam,
                "acertou_inicio": pred_obj == ini,
                "dentro_span": ini <= pred_obj < fim,
            },
            "pointer_pessoa_pred": pred_pessoa,
            "pointer_atividade_pred": pred_atividade,
            "pointer_objeto_primeiros4_geracao": hp["objeto"][:4],
            "divergencia": divergencia,
        })

    n = len(casos)
    resumo = {
        "nome": nome,
        "versao": versao,
        "n": n,
        "objeto_mencionado": sum(c["menciona_objeto"] for c in casos) / n,
        "pessoa_mencionada": sum(c["menciona_pessoa"] for c in casos) / n,
        "atividade_mencionada": sum(c["menciona_atividade"] for c in casos) / n,
        "gate_objeto_ligado": sum(c["gate_bits"]["objeto"] for c in casos) / n,
        "gate_objeto_exato": sum(c["gate_objeto_exato"] for c in casos) / n,
        "pointer_objeto_inicio": sum(c["pointer_objeto"]["acertou_inicio"] for c in casos) / n,
        "pointer_objeto_dentro_span": sum(c["pointer_objeto"]["dentro_span"] for c in casos) / n,
        "primeiro_token_correto": sum(c["prefixo_correto_tokens"] > 0 for c in casos) / n,
        "terminou": sum(c["terminou"] for c in casos) / n,
        "prefixo_medio_tokens": sum(c["prefixo_correto_tokens"] for c in casos) / n,
    }
    return resumo, casos


def markdown(resultado):
    linhas = [
        "# Diagnóstico focal — recordar_objeto",
        "",
        "Sem treino, sem mudança de pesos e sem autorização de promoção.",
        "",
        "| Métrica | V4 | V5 |",
        "|---|---:|---:|",
    ]
    chaves = [
        ("Objeto aparece na saída", "objeto_mencionado", True),
        ("Pessoa aparece na saída", "pessoa_mencionada", True),
        ("Atividade aparece na saída", "atividade_mencionada", True),
        ("Gate de objeto ligado", "gate_objeto_ligado", True),
        ("Padrão de gates exato (só objeto)", "gate_objeto_exato", True),
        ("Pointer no início do objeto", "pointer_objeto_inicio", True),
        ("Pointer dentro do span do objeto", "pointer_objeto_dentro_span", True),
        ("Primeiro token correto", "primeiro_token_correto", True),
        ("Geração terminou em <fim>", "terminou", True),
        ("Prefixo correto médio", "prefixo_medio_tokens", False),
    ]
    for rot, chave, pct in chaves:
        a = resultado["v4"]["resumo"][chave]
        b = resultado["v5"]["resumo"][chave]
        va = f"{100*a:.1f}%" if pct else f"{a:.2f}"
        vb = f"{100*b:.1f}%" if pct else f"{b:.2f}"
        linhas.append(f"| {rot} | {va} | {vb} |")

    for modelo in ("v4", "v5"):
        linhas += ["", f"## {modelo.upper()} — 20 casos", ""]
        linhas.append("| id | gate obj | ptr span | prefixo | menções | saída |")
        linhas.append("|---|---:|---:|---:|---|---|")
        for c in resultado[modelo]["casos"]:
            menc = "/".join(k for k, ok in (
                ("obj", c["menciona_objeto"]),
                ("pessoa", c["menciona_pessoa"]),
                ("ativ", c["menciona_atividade"]),
            ) if ok) or "—"
            txt = c["gerado"].replace("|", "\\|").replace("\n", " ")[:120]
            linhas.append(
                f"| {c['id']} | {'✓' if c['gate_bits']['objeto'] else '✗'} | "
                f"{'✓' if c['pointer_objeto']['dentro_span'] else '✗'} | "
                f"{c['prefixo_correto_tokens']} | {menc} | {txt} |"
            )
    return "\n".join(linhas) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v4", required=True)
    ap.add_argument("--v5", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--dispositivo", default="cpu")
    args = ap.parse_args()
    torch.set_num_threads(2)

    exs, man = au.abrir_holdout()
    r4, c4 = diagnosticar("V4", 4, args.v4, exs, args.dispositivo)
    r5, c5 = diagnosticar("V5", 5, args.v5, exs, args.dispositivo)
    resultado = {
        "holdout_sha256": man["holdout_sha256_canonico"],
        "sem_treino": True,
        "promocao_autorizada": False,
        "v4": {"resumo": r4, "casos": c4},
        "v5": {"resumo": r5, "casos": c5},
    }

    out = Path(args.saida)
    out.mkdir(parents=True, exist_ok=True)
    (out / "recordar_objeto.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "RECORDAR_OBJETO.md").write_text(markdown(resultado), encoding="utf-8")
    print(json.dumps({"v4": r4, "v5": r5}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
