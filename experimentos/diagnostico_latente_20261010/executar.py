"""Diagnóstico sem treino da representação usada para escolher o primeiro token."""
from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, ESPECIAIS, INICIO, fonte_dialogo, tokenizar


def media(xs):
    return sum(xs) / len(xs) if xs else None


def pct(x):
    return 100.0 * x


def primeiro_alvo(ex):
    ts = tokenizar(ex["resposta"])
    if not ts:
        raise ValueError("Resposta vazia")
    return ts[0]


def categoria_alvo(modelo, ex, alvo):
    fonte = set(fonte_dialogo(ex["mensagem"], ex.get("historico", []), modelo.limite_fonte))
    no_vocab = alvo in modelo.indices
    na_fonte = alvo in fonte
    if no_vocab and not na_fonte:
        return "geracao_lexical"
    if na_fonte:
        return "fonte_disponivel"
    return "impossivel"


def sondar(modelo, ex):
    import numpy as np
    alvo = primeiro_alvo(ex)
    estado = modelo.codificar(ex["mensagem"], ex.get("historico", []))
    dist, seguinte, aud = modelo.passo(ESPECIAIS[INICIO], estado)
    ordem = sorted(dist.items(), key=lambda kv: (-kv[1], kv[0]))
    pred, ptop = ordem[0]
    p_alvo = float(dist.get(alvo, 0.0))
    rank = next((i + 1 for i, (tok, _) in enumerate(ordem) if tok == alvo), len(ordem) + 1)
    vec = np.concatenate((np.asarray(seguinte["h"], dtype=float), np.asarray(seguinte["contexto"], dtype=float)))
    norma = float(np.linalg.norm(vec))
    if norma <= 1e-12:
        raise ValueError("Representacao latente nula")
    return {
        "id": ex.get("id"), "familia": ex.get("familia"), "grupo": ex.get("grupo"),
        "turno": ex.get("turno"), "mensagem": ex["mensagem"],
        "alvo_primeiro": alvo, "alvo_primeiro_cf": alvo.casefold(),
        "pred_primeiro": pred, "pred_primeiro_cf": pred.casefold(),
        "correto_primeiro": pred == alvo,
        "prob_alvo": p_alvo, "prob_top1": float(ptop), "margem_top1_menos_alvo": float(ptop - p_alvo),
        "rank_alvo": rank, "gate_gerar": float(aud["gerar"]),
        "categoria_alvo": categoria_alvo(modelo, ex, alvo),
        "vetor": vec, "vetor_norm": vec / norma,
    }


def resumo_sonda(linhas):
    ranks = [x["rank_alvo"] for x in linhas]
    return {
        "exemplos": len(linhas),
        "acertos_primeiro": sum(x["correto_primeiro"] for x in linhas),
        "acuracia_primeiro": sum(x["correto_primeiro"] for x in linhas) / len(linhas),
        "rank_mediano": statistics.median(ranks),
        "rank_medio": media(ranks),
        "alvo_top5": sum(x["rank_alvo"] <= 5 for x in linhas),
        "alvo_top10": sum(x["rank_alvo"] <= 10 for x in linhas),
        "prob_alvo_media": media([x["prob_alvo"] for x in linhas]),
        "margem_top1_menos_alvo_media": media([x["margem_top1_menos_alvo"] for x in linhas]),
        "gate_gerar_medio": media([x["gate_gerar"] for x in linhas]),
    }


def vizinhanca(dev, treino):
    import numpy as np
    matriz = np.stack([x["vetor_norm"] for x in treino])
    aberturas = [x["alvo_primeiro_cf"] for x in treino]
    saida = []
    for x in dev:
        sims = matriz @ x["vetor_norm"]
        top = np.argsort(-sims)[:5]
        alvo = x["alvo_primeiro_cf"]
        matches = [aberturas[i] == alvo for i in top]
        mesmos = np.flatnonzero(np.asarray([a == alvo for a in aberturas], dtype=bool))
        difs = np.flatnonzero(np.asarray([a != alvo for a in aberturas], dtype=bool))
        melhor_mesmo = float(sims[mesmos].max()) if len(mesmos) else None
        melhor_dif = float(sims[difs].max()) if len(difs) else None
        saida.append({
            "id": x["id"], "familia": x["familia"], "alvo": alvo,
            "pred": x["pred_primeiro_cf"], "correto_primeiro": x["correto_primeiro"],
            "top1_mesma_abertura": bool(matches[0]),
            "top5_tem_mesma_abertura": any(matches),
            "top5_aberturas": [aberturas[i] for i in top],
            "top5_similaridades": [float(sims[i]) for i in top],
            "top5_familias_treino": [treino[i]["familia"] for i in top],
            "melhor_cos_mesma_abertura": melhor_mesmo,
            "melhor_cos_abertura_diferente": melhor_dif,
            "margem_latente_mesma_menos_diferente": (melhor_mesmo - melhor_dif) if melhor_mesmo is not None and melhor_dif is not None else None,
        })
    return saida


def separacao_nova(nova):
    import numpy as np
    m = np.stack([x["vetor_norm"] for x in nova])
    sim = m @ m.T
    intra_fam, inter_fam, mesma_abertura, outra_abertura = [], [], [], []
    for i in range(len(nova)):
        for j in range(i + 1, len(nova)):
            v = float(sim[i, j])
            (intra_fam if nova[i]["familia"] == nova[j]["familia"] else inter_fam).append(v)
            (mesma_abertura if nova[i]["alvo_primeiro_cf"] == nova[j]["alvo_primeiro_cf"] else outra_abertura).append(v)
    return {
        "cos_intra_familia": media(intra_fam), "cos_inter_familia": media(inter_fam),
        "delta_intra_menos_inter": media(intra_fam) - media(inter_fam),
        "cos_mesma_abertura": media(mesma_abertura), "cos_abertura_diferente": media(outra_abertura),
        "delta_mesma_abertura": media(mesma_abertura) - media(outra_abertura),
        "pares_intra_familia": len(intra_fam), "pares_inter_familia": len(inter_fam),
    }


def gates_por_categoria(linhas):
    grupos = defaultdict(list)
    for x in linhas:
        grupos[x["categoria_alvo"]].append(x["gate_gerar"])
    return {k: {"n": len(v), "media": media(v), "mediana": statistics.median(v)} for k, v in sorted(grupos.items())}


def serializavel(x):
    return {k: v for k, v in x.items() if k not in ("vetor", "vetor_norm")}


def executar():
    p = ler_json(OUT / "protocolo.json")
    dados = ler_json(RAIZ / p["checkpoint"])
    corpus = ler_json(RAIZ / p["corpus"])
    modelo = DialogoSeq2Seq(dados)
    treino_raw = [e for e in corpus["exemplos"] if e.get("split") == "treino"]
    valid = [e for e in corpus["exemplos"] if e.get("split") == "validacao"]
    antiga_raw = [e for e in valid if e.get("grupo") != "sessao_completa"]
    nova_raw = [e for e in valid if e.get("grupo") == "sessao_completa"]
    if (len(treino_raw), len(antiga_raw), len(nova_raw)) != (p["recortes"]["treino"], p["recortes"]["dev_antiga"], p["recortes"]["dev_nova"]):
        raise ValueError("Recortes mudaram")

    print("Sondando treino", flush=True)
    treino = [sondar(modelo, e) for e in treino_raw]
    print("Sondando dev antiga", flush=True)
    antiga = [sondar(modelo, e) for e in antiga_raw]
    print("Sondando dev nova", flush=True)
    nova = [sondar(modelo, e) for e in nova_raw]

    viz_nova = vizinhanca(nova, treino)
    viz_antiga = vizinhanca(antiga, treino)
    sep = separacao_nova(nova)

    resumos = {"treino": resumo_sonda(treino), "dev_antiga": resumo_sonda(antiga), "dev_nova": resumo_sonda(nova)}
    gates = {"treino": gates_por_categoria(treino), "dev_antiga": gates_por_categoria(antiga), "dev_nova": gates_por_categoria(nova)}

    def resumo_viz(v):
        com = [x for x in v if x["top5_tem_mesma_abertura"]]
        return {
            "n": len(v),
            "top1_mesma_abertura": sum(x["top1_mesma_abertura"] for x in v),
            "top5_tem_mesma_abertura": len(com),
            "taxa_top5_mesma_abertura": len(com) / len(v),
            "erra_cabeca_com_vizinho_correto": sum((not x["correto_primeiro"]) for x in com),
            "taxa_erra_cabeca_dado_vizinho_correto": sum((not x["correto_primeiro"]) for x in com) / max(1, len(com)),
            "margem_latente_media": media([x["margem_latente_mesma_menos_diferente"] for x in v if x["margem_latente_mesma_menos_diferente"] is not None]),
        }

    rv_nova, rv_antiga = resumo_viz(viz_nova), resumo_viz(viz_antiga)
    gate_novo = gates["dev_nova"]
    glex = gate_novo.get("geracao_lexical", {}).get("media")
    gsrc = gate_novo.get("fonte_disponivel", {}).get("media")
    gap_acc = resumos["dev_antiga"]["acuracia_primeiro"] - resumos["dev_nova"]["acuracia_primeiro"]
    flags = {
        "gap_primeiro_token_novo": gap_acc >= 0.20,
        "gap_acuracia_antiga_menos_nova": gap_acc,
        "vizinhanca_nao_transfere_abertura": rv_nova["taxa_top5_mesma_abertura"] < 0.50,
        "cabeca_falha_mesmo_com_vizinho_correto": rv_nova["taxa_erra_cabeca_dado_vizinho_correto"] > 0.50,
        "gate_pouco_condicionado": (abs(glex - gsrc) < 0.10) if glex is not None and gsrc is not None else None,
        "delta_gate_lexical_menos_fonte": (glex - gsrc) if glex is not None and gsrc is not None else None,
        "familia_latente_separavel": sep["delta_intra_menos_inter"] >= 0.02,
    }

    resultado = {
        "base_commit": p["base_commit"], "nenhum_treino": True, "pesos_alterados": False,
        "holdout_final_lido": False, "resumos": resumos, "gates": gates,
        "vizinhanca": {"dev_nova": rv_nova, "dev_antiga": rv_antiga},
        "separacao_dev_nova": sep, "flags": flags,
        "detalhes_dev_nova": [dict(serializavel(x), vizinhanca=v) for x, v in zip(nova, viz_nova)],
        "limites": p["limites"],
    }
    (OUT / "resultados.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def rlinha(nome, r):
        return f"| {nome} | {r['exemplos']} | {r['acertos_primeiro']}/{r['exemplos']} | {pct(r['acuracia_primeiro']):.1f}% | {r['rank_mediano']:.1f} | {r['alvo_top5']} | {r['prob_alvo_media']:.4f} |"
    linhas = [
        "# Diagnóstico latente do primeiro token — 10/10/2026", "",
        "Sem treino. Sonda o checkpoint 1× no estado após o primeiro passo do decoder (`h` + contexto de atenção, 72 dimensões).", "",
        "| Recorte | N | Top1 alvo | Acurácia | Rank mediano | Alvo top5 | P(alvo) média |",
        "|---|---:|---:|---:|---:|---:|---:|",
        rlinha("treino", resumos["treino"]), rlinha("dev antiga", resumos["dev_antiga"]), rlinha("dev nova", resumos["dev_nova"]), "",
        "## Vizinhança latente", "",
        f"- Dev nova: top5 contém ao menos um exemplo de treino com a mesma abertura alvo em **{rv_nova['top5_tem_mesma_abertura']}/{rv_nova['n']}** ({pct(rv_nova['taxa_top5_mesma_abertura']):.1f}%).",
        f"- Dev antiga: mesma medida = **{rv_antiga['top5_tem_mesma_abertura']}/{rv_antiga['n']}** ({pct(rv_antiga['taxa_top5_mesma_abertura']):.1f}%).",
        f"- Quando a dev nova tem vizinho top5 com abertura correta, a cabeça ainda erra o primeiro token em **{rv_nova['erra_cabeca_com_vizinho_correto']}/{max(1, rv_nova['top5_tem_mesma_abertura'])}** ({pct(rv_nova['taxa_erra_cabeca_dado_vizinho_correto']):.1f}%).",
        f"- Margem cosseno média do melhor vizinho com mesma abertura menos melhor abertura diferente: **{rv_nova['margem_latente_media']:.4f}**.", "",
        "## Separação no desenvolvimento novo", "",
        f"- Cosseno intra-família: **{sep['cos_intra_familia']:.4f}**; inter-família: **{sep['cos_inter_familia']:.4f}**; Δ = **{sep['delta_intra_menos_inter']:.4f}**.",
        f"- Cosseno mesma abertura alvo: **{sep['cos_mesma_abertura']:.4f}**; abertura diferente: **{sep['cos_abertura_diferente']:.4f}**; Δ = **{sep['delta_mesma_abertura']:.4f}**.", "",
        "## Gate gerar × copiar no dev novo", "",
    ]
    for cat, g in gate_novo.items():
        linhas.append(f"- `{cat}`: n={g['n']}, gate gerar médio **{g['media']:.4f}**, mediana **{g['mediana']:.4f}**.")
    linhas += ["", "## Flags pré-congeladas", ""]
    for k, v in flags.items():
        if isinstance(v, bool) or v is None:
            linhas.append(f"- {k}: **{'sim' if v else 'não' if v is not None else 'indisponível'}**.")
        else:
            linhas.append(f"- {k}: **{v:.4f}**.")
    linhas += ["", "## Limites", "", *[f"- {x}" for x in p["limites"]], ""]
    (OUT / "RELATORIO.md").write_text("\n".join(linhas), encoding="utf-8")
    print(json.dumps({"resumos": resumos, "vizinhanca": resultado["vizinhanca"], "separacao": sep, "gates_novo": gate_novo, "flags": flags}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
