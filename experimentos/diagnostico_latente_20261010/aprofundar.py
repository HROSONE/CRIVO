"""Aprofunda o diagnóstico latente por componente e atenção; sem treino."""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, ESPECIAIS, INICIO, MENSAGEM, tokenizar


def media(xs): return sum(xs) / len(xs) if xs else None


def norma(v):
    import numpy as np
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v / max(n, 1e-12)


def extrair(modelo, ex):
    import numpy as np
    e0 = modelo.codificar(ex["mensagem"], ex.get("historico", []))
    dist, e1, aud = modelo.passo(ESPECIAIS[INICIO], e0)
    alvo = tokenizar(ex["resposta"])[0].casefold()
    marker = ESPECIAIS[MENSAGEM]
    idx = max(i for i, t in enumerate(e0["tokens"]) if t == marker)
    att = np.asarray(aud["atencao"], dtype=float)
    atual = float(att[idx:].sum())
    hist = float(att[:idx].sum())
    frac_tokens = (len(e0["tokens"]) - idx) / len(e0["tokens"])
    ent = -float(sum(a * math.log(max(a, 1e-15)) for a in att))
    ent_norm = ent / max(1e-12, math.log(max(2, len(att))))
    return {
        "id": ex.get("id"), "familia": ex.get("familia"), "turno": ex.get("turno"),
        "alvo": alvo, "pred": max(dist, key=dist.get).casefold(),
        "componentes": {
            "encoder_h": norma(e0["h"]),
            "decoder_h": norma(e1["h"]),
            "contexto_atencao": norma(e1["contexto"]),
            "combinado": norma(np.concatenate((e1["h"], e1["contexto"]))),
        },
        "atencao": {
            "tokens": len(e0["tokens"]), "tokens_atual": len(e0["tokens"]) - idx,
            "fracao_tokens_atual": frac_tokens, "massa_atual": atual, "massa_historico": hist,
            "razao_massa_por_token": atual / max(frac_tokens, 1e-12),
            "entropia_normalizada": ent_norm,
        },
    }


def vizinhanca(componente, treino, dev):
    import numpy as np
    mat = np.stack([x["componentes"][componente] for x in treino])
    ab = [x["alvo"] for x in treino]
    top1 = top5 = 0
    margens = []
    for x in dev:
        sims = mat @ x["componentes"][componente]
        inds = np.argsort(-sims)[:5]
        alvo = x["alvo"]
        top1 += ab[inds[0]] == alvo
        top5 += any(ab[i] == alvo for i in inds)
        mesmos = np.flatnonzero(np.asarray([a == alvo for a in ab], dtype=bool))
        outros = np.flatnonzero(np.asarray([a != alvo for a in ab], dtype=bool))
        if len(mesmos) and len(outros):
            margens.append(float(sims[mesmos].max() - sims[outros].max()))
    return {"n": len(dev), "top1": int(top1), "top5": int(top5), "taxa_top5": top5 / len(dev),
            "margem_mesma_abertura_media": media(margens)}


def separacao(componente, dev):
    import numpy as np
    mat = np.stack([x["componentes"][componente] for x in dev])
    sim = mat @ mat.T
    fam_in, fam_out, ab_in, ab_out = [], [], [], []
    for i in range(len(dev)):
        for j in range(i + 1, len(dev)):
            s = float(sim[i, j])
            (fam_in if dev[i]["familia"] == dev[j]["familia"] else fam_out).append(s)
            (ab_in if dev[i]["alvo"] == dev[j]["alvo"] else ab_out).append(s)
    return {"familia_delta": media(fam_in) - media(fam_out), "abertura_delta": media(ab_in) - media(ab_out),
            "familia_intra": media(fam_in), "familia_inter": media(fam_out),
            "abertura_mesma": media(ab_in), "abertura_diferente": media(ab_out)}


def resumo_atencao(xs):
    com_hist = [x for x in xs if x["atencao"]["massa_historico"] > 1e-12]
    base = com_hist if com_hist else xs
    return {"n": len(xs), "com_historico": len(com_hist),
            "massa_atual_media": media([x["atencao"]["massa_atual"] for x in base]),
            "fracao_tokens_atual_media": media([x["atencao"]["fracao_tokens_atual"] for x in base]),
            "razao_massa_por_token_media": media([x["atencao"]["razao_massa_por_token"] for x in base]),
            "entropia_normalizada_media": media([x["atencao"]["entropia_normalizada"] for x in base])}


def executar():
    protocolo = ler_json(OUT / "protocolo.json")
    modelo = DialogoSeq2Seq(ler_json(RAIZ / protocolo["checkpoint"]))
    corpus = ler_json(RAIZ / protocolo["corpus"])
    treino_raw = [e for e in corpus["exemplos"] if e.get("split") == "treino"]
    val = [e for e in corpus["exemplos"] if e.get("split") == "validacao"]
    antiga_raw = [e for e in val if e.get("grupo") != "sessao_completa"]
    nova_raw = [e for e in val if e.get("grupo") == "sessao_completa"]
    print("Extraindo componentes", flush=True)
    treino = [extrair(modelo, e) for e in treino_raw]
    antiga = [extrair(modelo, e) for e in antiga_raw]
    nova = [extrair(modelo, e) for e in nova_raw]
    componentes = ["encoder_h", "decoder_h", "contexto_atencao", "combinado"]
    comp = {}
    for nome in componentes:
        comp[nome] = {"viz_nova": vizinhanca(nome, treino, nova), "viz_antiga": vizinhanca(nome, treino, antiga),
                      "separacao_nova": separacao(nome, nova)}
    at = {"treino": resumo_atencao(treino), "dev_antiga": resumo_atencao(antiga), "dev_nova": resumo_atencao(nova)}
    saida = {"nenhum_treino": True, "pesos_alterados": False, "holdout_final_lido": False,
             "componentes": comp, "atencao": at,
             "limite": "Aprofundamento posterior ao diagnóstico principal; métricas descritivas, sem novas flags de aprovação."}
    (OUT / "aprofundamento.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    linhas = ["# Aprofundamento: onde o sinal de abertura se perde — 10/10/2026", "",
              "Sem treino. Compara quatro representações do mesmo checkpoint 1×.", "",
              "| Componente | Top5 abertura correta nova | Top5 antiga | Margem nova | Δ família nova | Δ abertura nova |",
              "|---|---:|---:|---:|---:|---:|"]
    for nome in componentes:
        r = comp[nome]
        linhas.append(f"| {nome} | {r['viz_nova']['top5']}/94 ({100*r['viz_nova']['taxa_top5']:.1f}%) | {r['viz_antiga']['top5']}/334 ({100*r['viz_antiga']['taxa_top5']:.1f}%) | {r['viz_nova']['margem_mesma_abertura_media']:.4f} | {r['separacao_nova']['familia_delta']:.4f} | {r['separacao_nova']['abertura_delta']:.4f} |")
    linhas += ["", "## Atenção no primeiro passo", "",
               "A razão `massa por token` compara a massa de atenção no pedido atual com a fração de tokens que ele ocupa; 1,0 seria proporcional ao tamanho.", "",
               "| Recorte | Casos com histórico | Massa atual | Fração tokens atual | Razão massa/token | Entropia normalizada |",
               "|---|---:|---:|---:|---:|---:|"]
    for nome, r in at.items():
        linhas.append(f"| {nome} | {r['com_historico']} | {r['massa_atual_media']:.4f} | {r['fracao_tokens_atual_media']:.4f} | {r['razao_massa_por_token_media']:.4f} | {r['entropia_normalizada_media']:.4f} |")
    linhas += ["", "Estas métricas não provam semântica geral; servem para localizar o gargalo antes de outra intervenção.", ""]
    (OUT / "APROFUNDAMENTO.md").write_text("\n".join(linhas), encoding="utf-8")
    print(json.dumps(saida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
