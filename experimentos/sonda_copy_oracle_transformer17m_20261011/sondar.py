#!/usr/bin/env python3
"""Sonda copy-oracle V4/V5: mede a interface recuperação -> emissão sem treinar pesos."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import torch

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
AUDITORIA = RAIZ / "experimentos" / "auditoria_transformer_17m_v4_v5_20261011"
sys.path[:0] = [str(AUDITORIA), str(RAIZ)]

spec = importlib.util.spec_from_file_location("audit17m", AUDITORIA / "auditar.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def mapa_slots_alvo(t, z):
    """Mapeia posições BPE da resposta-alvo ao slot que precisa ser emitido."""
    mapa = {}
    detalhes = {}
    alvo = z["resposta_ids"]
    for slot in audit.slots_relevantes(z["operacao"]):
        valor = z["ex"]["slots"][slot]
        candidatos = []
        for forma in (valor, " " + valor):
            seq = audit.cod(t, forma)
            p = audit.achar_subseq(alvo, seq)
            if p >= 0:
                candidatos.append((p, seq))
        if not candidatos:
            continue
        p, seq = max(candidatos, key=lambda x: (x[0], len(x[1])))
        detalhes[slot] = {"inicio_alvo": p, "tokens_alvo": seq}
        for j in range(len(seq)):
            mapa[p + j] = slot
    return mapa, detalhes


def token_copiavel(z, slot, token):
    ini, fim, _ = z["spans"][slot]
    return token in z["fonte"][ini:fim]


def prefixo_correto(saida, alvo):
    n = 0
    while n < min(len(saida), len(alvo)) and saida[n] == alvo[n]:
        n += 1
    return n


@torch.no_grad()
def teacher_forced(versao, m, ponte, t, zs):
    total = acertos = 0
    entidade_total = entidade_acertos = entidade_copiavel = 0
    nao_ent_total = nao_ent_acertos = 0
    oracle_gold_acertos = oracle_ptr_acertos = 0
    exata_base = exata_gold = exata_ptr = 0
    ptr_inicio = defaultdict(lambda: [0, 0])
    primeira_div_total = primeira_div_entidade = primeira_div_copiavel = 0
    primeira_div_ptr = 0

    for z in zs:
        x = torch.tensor([z["x"]], dtype=torch.long, device=m.embedding.weight.device)
        pos = torch.tensor([z["pos"]], dtype=torch.long, device=x.device)
        log, _, preds = audit.forward_candidato(versao, m, ponte, x, pos)
        mapa, _ = mapa_slots_alvo(t, z)
        alvo = z["resposta_ids"]
        base_seq, gold_seq, ptr_seq = [], [], []

        for slot in audit.slots_relevantes(z["operacao"]):
            if slot not in z["spans"]:
                continue
            ini, _, _ = z["spans"][slot]
            ptr_inicio[slot][1] += 1
            ptr_inicio[slot][0] += int(int(preds[slot][0]) == ini)

        primeira = None
        for k, gold in enumerate(alvo):
            pred = int(log[0, z["pos"] + k].argmax())
            total += 1
            acertos += int(pred == gold)
            base_seq.append(pred)
            gpred = pred
            ppred = pred
            slot = mapa.get(k)
            if slot is not None:
                entidade_total += 1
                entidade_acertos += int(pred == gold)
                copiavel = token_copiavel(z, slot, gold)
                entidade_copiavel += int(copiavel)
                if copiavel:
                    gpred = gold
                ini, _, _ = z["spans"][slot]
                if copiavel and int(preds[slot][0]) == ini:
                    ppred = gold
            else:
                nao_ent_total += 1
                nao_ent_acertos += int(pred == gold)
            gold_seq.append(gpred)
            ptr_seq.append(ppred)
            oracle_gold_acertos += int(gpred == gold)
            oracle_ptr_acertos += int(ppred == gold)
            if primeira is None and pred != gold:
                primeira = (k, slot, gold)

        exata_base += int(base_seq == alvo)
        exata_gold += int(gold_seq == alvo)
        exata_ptr += int(ptr_seq == alvo)
        if primeira is not None:
            primeira_div_total += 1
            _, slot, gold = primeira
            if slot is not None:
                primeira_div_entidade += 1
                copiavel = token_copiavel(z, slot, gold)
                primeira_div_copiavel += int(copiavel)
                ini, _, _ = z["spans"][slot]
                primeira_div_ptr += int(copiavel and int(preds[slot][0]) == ini)

    n = len(zs)
    return {
        "tokens": total,
        "token_acc_base": acertos / total,
        "token_acc_oracle_span_correto": oracle_gold_acertos / total,
        "token_acc_oracle_pointer_atual": oracle_ptr_acertos / total,
        "entity_token_acc_base": entidade_acertos / entidade_total,
        "non_entity_token_acc_base": nao_ent_acertos / nao_ent_total,
        "entity_token_copyable_from_correct_span": entidade_copiavel / entidade_total,
        "sequencia_exata_base": exata_base / n,
        "sequencia_exata_oracle_span_correto": exata_gold / n,
        "sequencia_exata_oracle_pointer_atual": exata_ptr / n,
        "primeira_divergencia_n": primeira_div_total,
        "primeira_divergencia_em_entidade": primeira_div_entidade / primeira_div_total,
        "primeira_divergencia_entidade_copiavel": primeira_div_copiavel / primeira_div_total,
        "primeira_divergencia_recuperavel_pointer_atual": primeira_div_ptr / primeira_div_total,
        "pointer_start_acc_relevante": {
            s: ok / tot for s, (ok, tot) in sorted(ptr_inicio.items()) if tot
        },
    }


@torch.no_grad()
def gerar_oracle(versao, m, ponte, t, z, modo):
    fim = t.token_to_id("<fim>")
    assist = t.token_to_id("<assistente>")
    proib = {t.token_to_id(x) for x in audit.ESPECIAIS[:-1]}
    alvo = z["resposta_ids"]
    mapa, _ = mapa_slots_alvo(t, z)
    ids = list(z["fonte"])
    saida = []
    terminou = False
    alinhado = True
    for k in range(48):
        janela = ids[-m.config.contexto:]
        x = torch.tensor([janela], dtype=torch.long, device=m.embedding.weight.device)
        p = audit.pos_assistente(janela, assist)
        pos = torch.tensor([p], dtype=torch.long, device=x.device)
        log, _, preds = audit.forward_candidato(versao, m, ponte, x, pos)
        logits = log[0, -1].clone()
        for tok in proib:
            logits[tok] = -float("inf")
        proximo = int(logits.argmax())

        if alinhado and k < len(alvo):
            slot = mapa.get(k)
            gold = alvo[k]
            if slot is not None and token_copiavel(z, slot, gold):
                if modo == "span_correto":
                    proximo = gold
                elif modo == "pointer_atual":
                    ini, _, _ = z["spans"][slot]
                    if int(preds[slot][0]) == ini:
                        proximo = gold

        if proximo == fim:
            terminou = True
            break
        saida.append(proximo)
        ids.append(proximo)
        if alinhado:
            alinhado = k < len(alvo) and proximo == alvo[k]
    return saida, terminou


def resumir_livre(versao, m, ponte, t, zs):
    modos = ("base", "pointer_atual", "span_correto")
    soma = {modo: defaultdict(float) for modo in modos}
    por_operacao = {modo: defaultdict(lambda: defaultdict(float)) for modo in modos}
    rescues = {"pointer_atual": 0, "span_correto": 0}

    for z in zs:
        alvo = z["resposta_ids"]
        resultados = {}
        base_ids, base_fim, _ = audit.gerar(versao, m, t, z["fonte"], ponte)
        resultados["base"] = (base_ids, base_fim)
        for modo in ("pointer_atual", "span_correto"):
            resultados[modo] = gerar_oracle(versao, m, ponte, t, z, modo)

        prefixo_base = prefixo_correto(base_ids, alvo)
        for modo, (ids, terminou) in resultados.items():
            texto = t.decode(ids)
            slot, operacao = audit.pontuar(z["ex"], texto, terminou)
            exata = audit.norm(texto) == audit.norm(z["resposta"])
            pref = prefixo_correto(ids, alvo)
            soma[modo]["n"] += 1
            soma[modo]["slot"] += slot
            soma[modo]["operacao"] += operacao
            soma[modo]["exata"] += exata
            soma[modo]["prefixo"] += pref
            po = por_operacao[modo][z["operacao"]]
            po["n"] += 1
            po["slot"] += slot
            po["operacao"] += operacao
            po["exata"] += exata
            if modo != "base" and pref > prefixo_base:
                rescues[modo] += 1

    saida = {}
    for modo in modos:
        n = soma[modo]["n"]
        saida[modo] = {
            "n": int(n),
            "slot": soma[modo]["slot"] / n,
            "operacao": soma[modo]["operacao"] / n,
            "exata": soma[modo]["exata"] / n,
            "prefixo_correto_medio_tokens": soma[modo]["prefixo"] / n,
            "por_operacao": {},
        }
        for op, d in sorted(por_operacao[modo].items()):
            nn = d["n"]
            saida[modo]["por_operacao"][op] = {
                "n": int(nn),
                "slot": d["slot"] / nn,
                "operacao": d["operacao"] / nn,
                "exata": d["exata"] / nn,
            }
    saida["casos_prefixo_estendido"] = {
        k: v / len(zs) for k, v in rescues.items()
    }
    return saida


def avaliar_modelo(nome, versao, pasta, exs, dispositivo):
    m, t, _ = audit.carregar_modelo(pasta, dispositivo)
    ponte, _ = audit.carregar_ponte(pasta, dispositivo)
    zs = [audit.preparar(t, ex, m.config.contexto) for ex in exs]
    return {
        "nome": nome,
        "versao": versao,
        "teacher_forced": teacher_forced(versao, m, ponte, t, zs),
        "geracao": resumir_livre(versao, m, ponte, t, zs),
    }


def markdown(r):
    l = [
        "# Sonda copy-oracle — Transformer 17,43M",
        "",
        "Sem treino, sem novos pesos e sem autorização de promoção. O oracle usa informação do alvo apenas para medir um limite superior causal da interface de cópia.",
        "",
    ]
    for chave in ("v4", "v5"):
        x = r[chave]
        tf = x["teacher_forced"]
        g = x["geracao"]
        l += [
            f"## {chave.upper()}",
            "",
            f"- entidade: LM acerta **{tf['entity_token_acc_base']:.2%}**; fora de entidade: **{tf['non_entity_token_acc_base']:.2%}**.",
            f"- tokens de entidade copiáveis do span correto: **{tf['entity_token_copyable_from_correct_span']:.2%}**.",
            f"- token acc teacher-forced: base **{tf['token_acc_base']:.2%}** → pointer atual **{tf['token_acc_oracle_pointer_atual']:.2%}** → span correto **{tf['token_acc_oracle_span_correto']:.2%}**.",
            f"- sequência teacher-forced inteira correta: base **{tf['sequencia_exata_base']:.2%}** → pointer atual **{tf['sequencia_exata_oracle_pointer_atual']:.2%}** → span correto **{tf['sequencia_exata_oracle_span_correto']:.2%}**.",
            f"- primeira divergência recuperável pelo pointer atual: **{tf['primeira_divergencia_recuperavel_pointer_atual']:.2%}**; por span correto: **{tf['primeira_divergencia_entidade_copiavel']:.2%}**.",
            "",
            "| geração greedy | operação | slot | exata | prefixo médio |",
            "|---|---:|---:|---:|---:|",
        ]
        for modo in ("base", "pointer_atual", "span_correto"):
            d = g[modo]
            l.append(f"| {modo} | {d['operacao']:.2%} | {d['slot']:.2%} | {d['exata']:.2%} | {d['prefixo_correto_medio_tokens']:.2f} |")
        l += [
            "",
            f"Casos cujo prefixo aumentou: pointer atual **{g['casos_prefixo_estendido']['pointer_atual']:.2%}**; span correto **{g['casos_prefixo_estendido']['span_correto']:.2%}**.",
            "",
        ]
    return "\n".join(l) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v4", required=True)
    ap.add_argument("--v5", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--dispositivo", default="cpu")
    a = ap.parse_args()
    torch.set_num_threads(2)
    exs, man = audit.abrir_holdout()
    r = {
        "holdout_sha256": man["holdout_sha256_canonico"],
        "sem_treino": True,
        "promocao_autorizada": False,
        "definicao": {
            "pointer_atual": "força um token de entidade somente quando o pointer atual aponta exatamente o início do span correto e o ID do token existe nesse span",
            "span_correto": "oracle superior: força token de entidade quando seu ID existe no span correto da fonte",
            "fora_de_entidade": "sempre usa o LM original",
        },
        "v4": avaliar_modelo("V4", 4, a.v4, exs, a.dispositivo),
        "v5": avaliar_modelo("V5", 5, a.v5, exs, a.dispositivo),
    }
    out = Path(a.saida)
    out.mkdir(parents=True, exist_ok=True)
    (out / "resultados.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "RELATORIO.md").write_text(markdown(r), encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
