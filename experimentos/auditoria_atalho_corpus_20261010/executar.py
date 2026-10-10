"""Auditoria puramente estatística do corpus de sessões; não lê pesos."""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
from arquivos_contextuais import ler_json
from dialogo_seq2seq import tokenizar


def entropia(contagem):
    total = sum(contagem.values())
    if not total:
        return 0.0
    return -sum((n/total)*math.log2(n/total) for n in contagem.values() if n)


def entropia_condicional(xs, chave_x, chave_y):
    grupos = defaultdict(Counter)
    for e in xs:
        grupos[chave_x(e)][chave_y(e)] += 1
    total = len(xs)
    return sum((sum(c.values())/total)*entropia(c) for c in grupos.values())


def nmi(xs, chave_x, chave_y):
    hy = entropia(Counter(chave_y(e) for e in xs))
    hcond = entropia_condicional(xs, chave_x, chave_y)
    mi = hy - hcond
    return {"h_y": hy, "h_y_dado_x": hcond, "mi": mi, "nmi": mi/hy if hy else 0.0}


def tokens_resposta(e):
    return [t.casefold() for t in tokenizar(e["resposta"])]


def abertura(e):
    ts = tokens_resposta(e)
    return ts[0] if ts else "<vazio>"


def prefixo2(e):
    ts = tokens_resposta(e)
    return " ".join(ts[:2]) if ts else "<vazio>"


def pureza(xs, chave_grupo, chave_alvo):
    grupos = defaultdict(Counter)
    for e in xs:
        grupos[chave_grupo(e)][chave_alvo(e)] += 1
    total = len(xs)
    correto = sum(max(c.values()) for c in grupos.values())
    return {"grupos": len(grupos), "pureza_ponderada": correto/total, "acertos_majoritario": correto, "total": total,
            "pureza_mediana_grupo": sorted(max(c.values())/sum(c.values()) for c in grupos.values())[len(grupos)//2] if grupos else 0.0}


def palavras_mensagem(e):
    return {t.casefold() for t in tokenizar(e["mensagem"]) if any(ch.isalnum() for ch in t)}


def jaccard(a, b):
    u = a | b
    return len(a & b)/len(u) if u else 1.0


def executar():
    p = ler_json(OUT / "protocolo.json")
    corpus = ler_json(RAIZ / p["corpus"])
    treino = [e for e in corpus["exemplos"] if e.get("split") == "treino"]
    dev = [e for e in corpus["exemplos"] if e.get("split") == "validacao" and e.get("grupo") == "sessao_completa"]
    sessoes = [e for e in treino if e.get("grupo") == "sessao_completa"]
    replay = [e for e in treino if e.get("grupo") == "replay_legado"]
    apoio = [e for e in treino if e.get("grupo") == "apoio_lexical"]
    obtido = {"treino_total": len(treino), "treino_sessoes": len(sessoes), "replay_legado": len(replay),
              "apoio_lexical": len(apoio), "dev_sessoes": len(dev)}
    if obtido != p["recortes_esperados"]:
        raise ValueError(f"Recortes mudaram: {obtido}")

    fam = lambda e: e.get("familia", "<sem_familia>")
    turno = lambda e: int(e.get("turno") or 0)
    fam_turno = lambda e: f"{fam(e)}::{turno(e)}"

    info = {
        "abertura": {
            "familia": nmi(sessoes, fam, abertura),
            "turno": nmi(sessoes, turno, abertura),
            "familia_turno": nmi(sessoes, fam_turno, abertura),
        },
        "prefixo2": {
            "familia": nmi(sessoes, fam, prefixo2),
            "turno": nmi(sessoes, turno, prefixo2),
            "familia_turno": nmi(sessoes, fam_turno, prefixo2),
        },
    }
    pur = {
        "abertura_por_familia": pureza(sessoes, fam, abertura),
        "abertura_por_familia_turno": pureza(sessoes, fam_turno, abertura),
        "prefixo2_por_familia": pureza(sessoes, fam, prefixo2),
        "prefixo2_por_familia_turno": pureza(sessoes, fam_turno, prefixo2),
    }

    fam_por_ab = defaultdict(set); fam_por_p2 = defaultdict(set); fam_turno_por_ab = defaultdict(set)
    for e in sessoes:
        fam_por_ab[abertura(e)].add(fam(e))
        fam_por_p2[prefixo2(e)].add(fam(e))
        fam_turno_por_ab[(turno(e), abertura(e))].add(fam(e))
    suporte_p2 = [len(fam_por_p2[prefixo2(e)]) for e in sessoes]
    pouco_cruzados = sum(n <= 2 for n in suporte_p2)

    suporte_dev = []
    for e in dev:
        ab = abertura(e); tu = turno(e)
        suporte_dev.append({
            "id": e.get("id"), "familia": fam(e), "turno": tu, "abertura": ab, "prefixo2": prefixo2(e),
            "familias_abertura_qualquer_turno": len(fam_por_ab.get(ab, set())),
            "familias_abertura_mesmo_turno": len(fam_turno_por_ab.get((tu, ab), set())),
            "familias_prefixo2": len(fam_por_p2.get(prefixo2(e), set())),
        })
    baixo_mesmo_turno = sum(e["familias_abertura_mesmo_turno"] < 3 for e in suporte_dev)
    sem_abertura = sum(e["familias_abertura_qualquer_turno"] == 0 for e in suporte_dev)
    sem_prefixo = sum(e["familias_prefixo2"] == 0 for e in suporte_dev)

    # Baseline puramente superficial: vizinhos pela mensagem atual, sem histórico e sem resposta na busca.
    conjuntos_treino = [palavras_mensagem(e) for e in sessoes]
    ab_treino = [abertura(e) for e in sessoes]
    vizinhos = []
    for e in dev:
        q = palavras_mensagem(e)
        sims = [(jaccard(q, s), i) for i, s in enumerate(conjuntos_treino)]
        sims.sort(key=lambda x: (-x[0], x[1]))
        top = sims[:5]; alvo = abertura(e)
        vizinhos.append({"id": e.get("id"), "alvo": alvo, "top1_mesma_abertura": ab_treino[top[0][1]] == alvo,
                         "top5_tem_mesma_abertura": any(ab_treino[i] == alvo for _, i in top),
                         "similaridade_top1": top[0][0], "aberturas_top5": [ab_treino[i] for _, i in top]})
    top5_j = sum(v["top5_tem_mesma_abertura"] for v in vizinhos)
    top1_j = sum(v["top1_mesma_abertura"] for v in vizinhos)

    flags = {
        "atalho_familia_turno_forte": info["prefixo2"]["familia_turno"]["nmi"] >= 0.65,
        "prefixos_pouco_cruzados": pouco_cruzados/len(sessoes) >= 0.40,
        "suporte_cross_family_novo_baixo": baixo_mesmo_turno/len(dev) >= 0.50,
        "texto_superficial_nao_resolve": top5_j/len(dev) < 0.50,
    }
    resultado = {
        "nenhum_treino": True, "nenhum_peso_lido": True, "holdout_final_lido": False,
        "recortes": obtido, "informacao_mutua": info, "pureza": pur,
        "cruzamento": {
            "familias_treino": len({fam(e) for e in sessoes}),
            "aberturas_distintas": len(fam_por_ab), "prefixos2_distintos": len(fam_por_p2),
            "exemplos_prefixo2_em_ate_2_familias": pouco_cruzados,
            "fracao_prefixo2_em_ate_2_familias": pouco_cruzados/len(sessoes),
            "dev_suporte_mesmo_turno_menor_3": baixo_mesmo_turno,
            "fracao_dev_suporte_mesmo_turno_menor_3": baixo_mesmo_turno/len(dev),
            "dev_abertura_sem_suporte": sem_abertura, "dev_prefixo2_sem_suporte": sem_prefixo,
        },
        "jaccard_mensagem": {"top1_mesma_abertura": top1_j, "top5_tem_mesma_abertura": top5_j,
                             "taxa_top5": top5_j/len(dev)},
        "flags": flags, "suporte_dev": suporte_dev, "vizinhos_jaccard": vizinhos,
    }
    (OUT / "resultados.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    linhas = ["# Auditoria de atalhos no corpus — 10/10/2026", "",
              "Sem treino e sem leitura de pesos. Analisa apenas a composição do corpus de sessões.", "",
              "## Informação que a identidade da família fornece sobre a saída", "",
              "| Alvo | Condição | H(Y) | H(Y|X) | NMI |",
              "|---|---|---:|---:|---:|"]
    for alvo in ("abertura", "prefixo2"):
        for cond in ("familia", "turno", "familia_turno"):
            r = info[alvo][cond]
            linhas.append(f"| {alvo} | {cond} | {r['h_y']:.3f} | {r['h_y_dado_x']:.3f} | **{r['nmi']:.3f}** |")
    linhas += ["", "## Pureza majoritária", ""]
    for k, r in pur.items():
        linhas.append(f"- `{k}`: **{100*r['pureza_ponderada']:.1f}%** ({r['grupos']} grupos).")
    c = resultado["cruzamento"]
    linhas += ["", "## Cruzamento entre famílias", "",
              f"- Famílias de sessão no treino: **{c['familias_treino']}**.",
              f"- **{c['exemplos_prefixo2_em_ate_2_familias']}/{len(sessoes)} ({100*c['fracao_prefixo2_em_ate_2_familias']:.1f}%)** exemplos usam prefixo de 2 tokens presente em no máximo duas famílias.",
              f"- No desenvolvimento novo, **{c['dev_suporte_mesmo_turno_menor_3']}/94 ({100*c['fracao_dev_suporte_mesmo_turno_menor_3']:.1f}%)** têm abertura alvo suportada por menos de 3 famílias de treino no mesmo turno.",
              f"- Aberturas totalmente sem suporte no treino: **{c['dev_abertura_sem_suporte']}/94**; prefixos de 2 tokens totalmente sem suporte: **{c['dev_prefixo2_sem_suporte']}/94**.", "",
              "## Baseline superficial da mensagem atual", "",
              f"- Jaccard top1 com mesma abertura: **{top1_j}/94**.",
              f"- Algum dos top5 Jaccard com mesma abertura: **{top5_j}/94 ({100*top5_j/94:.1f}%)**.", "",
              "## Flags pré-congeladas", ""]
    for k, v in flags.items(): linhas.append(f"- {k}: **{'sim' if v else 'não'}**.")
    linhas += ["", "A auditoria mede correlação estrutural do corpus; não prova que a rede use causalmente cada atalho.", ""]
    (OUT / "RELATORIO.md").write_text("\n".join(linhas), encoding="utf-8")
    print(json.dumps({"informacao_mutua": info, "pureza": pur, "cruzamento": c, "jaccard": resultado["jaccard_mensagem"], "flags": flags}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
