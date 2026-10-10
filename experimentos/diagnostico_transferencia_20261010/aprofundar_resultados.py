"""Aprofunda resultados já produzidos; não executa o modelo nem altera pesos."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

DIR = Path(__file__).resolve().parent


def media(xs):
    return sum(xs) / len(xs) if xs else None


def corr(xs, ys):
    if len(xs) < 2:
        return None
    mx, my = media(xs), media(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    den = math.sqrt(sum(x*x for x in dx) * sum(y*y for y in dy))
    return sum(x*y for x, y in zip(dx, dy)) / den if den else 0.0


def primeiro_token(texto):
    import re
    partes = re.findall(r"\w+(?:[-’']\w+)*|[^\w\s]", texto, flags=re.UNICODE)
    return partes[0].casefold() if partes else "<vazio>"


def executar():
    dados = json.loads((DIR / "resultados.json").read_text(encoding="utf-8"))
    linhas = dados["detalhes"]

    alvo_primeiro = Counter(primeiro_token(x["alvo"]) for x in linhas)
    ger_primeiro = Counter(primeiro_token(x["gerada_full"]) for x in linhas)
    geradas = Counter(x["gerada_full"].strip().casefold() for x in linhas)
    erro_pos = Counter(str(x["primeiro_erro_indice"]) for x in linhas if x["primeiro_erro_indice"] is not None)

    episodios = defaultdict(list)
    for x in linhas:
        episodios[x["episodio"]].append(x)
    repeticoes = {
        "turnos_depois_do_primeiro": 0,
        "repete_resposta_gerada_anterior": 0,
        "repete_primeira_resposta_gerada": 0,
        "repete_alvo_anterior": 0,
    }
    por_familia = defaultdict(lambda: Counter())
    episodios_resumo = []
    for episodio, itens in sorted(episodios.items()):
        itens = sorted(itens, key=lambda x: int(x["turno"]))
        primeira = itens[0]["gerada_full"].strip().casefold()
        anteriores_geradas = set()
        anteriores_alvos = set()
        rep_g = rep_p = rep_a = 0
        for i, x in enumerate(itens):
            g = x["gerada_full"].strip().casefold()
            a = x["alvo"].strip().casefold()
            if i:
                repeticoes["turnos_depois_do_primeiro"] += 1
                por_familia[x["familia"]]["turnos_depois_do_primeiro"] += 1
                if g in anteriores_geradas:
                    repeticoes["repete_resposta_gerada_anterior"] += 1; rep_g += 1
                    por_familia[x["familia"]]["repete_resposta_gerada_anterior"] += 1
                if g == primeira:
                    repeticoes["repete_primeira_resposta_gerada"] += 1; rep_p += 1
                    por_familia[x["familia"]]["repete_primeira_resposta_gerada"] += 1
                if g in anteriores_alvos:
                    repeticoes["repete_alvo_anterior"] += 1; rep_a += 1
                    por_familia[x["familia"]]["repete_alvo_anterior"] += 1
            anteriores_geradas.add(g)
            anteriores_alvos.add(a)
        episodios_resumo.append({
            "episodio": episodio,
            "familia": itens[0]["familia"],
            "turnos": len(itens),
            "respostas_geradas_distintas": len(set(x["gerada_full"].strip().casefold() for x in itens)),
            "repeticoes_gerada_anterior": rep_g,
            "repeticoes_primeira_gerada": rep_p,
            "repeticoes_alvo_anterior": rep_a,
        })

    n_later = max(1, repeticoes["turnos_depois_do_primeiro"])
    repeticoes["fracao_repete_gerada_anterior"] = repeticoes["repete_resposta_gerada_anterior"] / n_later
    repeticoes["fracao_repete_primeira_gerada"] = repeticoes["repete_primeira_resposta_gerada"] / n_later
    repeticoes["fracao_repete_alvo_anterior"] = repeticoes["repete_alvo_anterior"] / n_later

    sims = [x["vizinho"]["similaridade_media"] for x in linhas]
    ces = [x["ce_full"] for x in linhas]
    corre = corr(sims, ces)
    altos = [x for x in linhas if x["vizinho"]["similaridade_media"] >= 0.50]
    baixos = [x for x in linhas if x["vizinho"]["similaridade_media"] < 0.50]

    aprofundado = {
        "nenhum_modelo_executado_nesta_etapa": True,
        "nenhum_treino": True,
        "aberturas": {
            "alvo_primeiro_token": alvo_primeiro,
            "gerado_primeiro_token": ger_primeiro,
            "primeiros_tokens_alvo_distintos": len(alvo_primeiro),
            "primeiros_tokens_gerados_distintos": len(ger_primeiro),
            "erro_posicao": erro_pos,
        },
        "repeticao": repeticoes,
        "por_familia_repeticao": {k: dict(v) for k, v in sorted(por_familia.items())},
        "episodios": episodios_resumo,
        "diversidade": {
            "respostas_geradas_distintas": len(geradas),
            "respostas_alvo_distintas": len(set(x["alvo"].strip().casefold() for x in linhas)),
            "top_respostas_geradas": geradas.most_common(10),
        },
        "proximidade_treino": {
            "correlacao_jaccard_ce": corre,
            "alta_similaridade_n": len(altos),
            "alta_similaridade_ce": media([x["ce_full"] for x in altos]),
            "alta_similaridade_exatas": sum(x["exata_full"] for x in altos),
            "baixa_similaridade_n": len(baixos),
            "baixa_similaridade_ce": media([x["ce_full"] for x in baixos]),
            "baixa_similaridade_exatas": sum(x["exata_full"] for x in baixos),
        },
    }
    (DIR / "aprofundamento.json").write_text(json.dumps(aprofundado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    linhas_md = [
        "# Aprofundamento: fixação da forma de resposta — 10/10/2026",
        "",
        "Esta etapa só lê `resultados.json`; não executa o modelo, não treina e não altera pesos.",
        "",
        "## Abertura da resposta",
        "",
        f"- Primeiros tokens distintos nos alvos: **{len(alvo_primeiro)}**.",
        f"- Primeiros tokens distintos nas gerações: **{len(ger_primeiro)}**.",
        f"- Erros já no token 0: **{erro_pos.get('0', 0)}/93** respostas não-exatas.",
        f"- Erros no token 1: **{erro_pos.get('1', 0)}/93**.",
        f"- Erros no token 2: **{erro_pos.get('2', 0)}/93**.",
        "",
        "Primeiros tokens mais comuns do alvo: " + ", ".join(f"`{k}`={v}" for k, v in alvo_primeiro.most_common(10)) + ".",
        "",
        "Primeiros tokens mais comuns gerados: " + ", ".join(f"`{k}`={v}" for k, v in ger_primeiro.most_common(10)) + ".",
        "",
        "## Fixação dentro das sessões",
        "",
        f"- Turnos após o primeiro: **{repeticoes['turnos_depois_do_primeiro']}**.",
        f"- Repete alguma resposta própria anterior: **{repeticoes['repete_resposta_gerada_anterior']}** ({100*repeticoes['fracao_repete_gerada_anterior']:.1f}%).",
        f"- Repete exatamente a primeira resposta gerada da sessão: **{repeticoes['repete_primeira_resposta_gerada']}** ({100*repeticoes['fracao_repete_primeira_gerada']:.1f}%).",
        f"- Repete literalmente um alvo correto de turno anterior: **{repeticoes['repete_alvo_anterior']}** ({100*repeticoes['fracao_repete_alvo_anterior']:.1f}%).",
        "",
        "## Diversidade global",
        "",
        f"- Respostas-alvo distintas: **{aprofundado['diversidade']['respostas_alvo_distintas']}**.",
        f"- Respostas geradas distintas: **{aprofundado['diversidade']['respostas_geradas_distintas']}**.",
        "",
        "Top respostas geradas:",
    ]
    for texto_, n in geradas.most_common(10):
        linhas_md.append(f"- **{n}×** `{texto_}`")
    linhas_md += [
        "",
        "## Proximidade lexical com o treino",
        "",
        f"- Correlação Jaccard de entrada × CE: **{corre:.3f}**.",
        f"- Similaridade ≥0,50: **{len(altos)}** casos, CE média **{media([x['ce_full'] for x in altos]):.3f}**, exatas **{sum(x['exata_full'] for x in altos)}**.",
        f"- Similaridade <0,50: **{len(baixos)}** casos, CE média **{media([x['ce_full'] for x in baixos]):.3f}**, exatas **{sum(x['exata_full'] for x in baixos)}**.",
        "",
        "A proximidade é lexical/estrutural simples e usa somente a entrada. Não mede equivalência semântica.",
    ]
    (DIR / "APROFUNDAMENTO.md").write_text("\n".join(linhas_md) + "\n", encoding="utf-8")
    print(json.dumps(aprofundado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
