"""Régua do v6: intervalos de confiança, comparação pareada com o 46M v4 e os critérios fixados antes de rodar.

Escrito em 19/10/2026, antes de qualquer treino do v6. Nada aqui foi ajustado depois de ver resultados.

VIZINHAS: respostas de outra situação que também servem para a fala pedida. A conta estrita continua sendo a
principal; a conta com vizinhas é mostrada ao lado. A lista é curta e de mão única de propósito
("pedida → também aceita").

Uso local (depois de baixar do Drive os arquivos linhas_*.json das duas rodadas e da linha de base):
    python comparar_v6.py pasta_com_os_json
"""
import json
import random
import sys
from pathlib import Path

VIZINHAS = {
    "oi": {"oi_tudo_bem"},                       # "oi" respondido com "tudo bem por aqui, e você?"
    "obrigado_despedida": {"despedida"},         # "valeu, falou" → "Tchau! Foi bom conversar"
    "despedida_dormir": {"despedida"},
    "desisto_despedida": {"desisto"},            # a resposta de desisto também cabe em quem vai embora
    "nao_era_isso": {"nao_entendeu_queixa"},     # as duas pedem desculpa e pedem para explicar de novo
    "nao_entendeu_queixa": {"nao_era_isso"},
    "insulto": {"dificil_falar"},
    "entediante": {"insulto"},
    "te_amo": {"amigo"},
    "estou_bem": {"reciproco"},
}

BLINDS_DECISIVOS = ("v3", "v1", "parafrases", "grok", "v4")
CRITERIOS = {
    "v3_ic_inferior_maior_que_zero": "blind v3: diferença pareada v6 − v4 com limite inferior do IC 95% > 0",
    "outros_blinds_sem_piorar": "v1, paráfrases, Grok e v4: diferença ≥ −1,5 ponto",
    "frases_reais": "frases reais do criador ≥ 12/15",
    "usa_fato": "fatos do acervo: usa o fato ≥ 0,85",
}
MINIMOS = {"frases_reais": 12, "usa_fato": 0.85, "piora_maxima": -0.015}
# v6b (fixado em 20/10/2026, antes de rodar): na rodada 1, frases de urgência pioraram ("tô sangrando muito").
URGENTES = {"saude_urgente", "ajuda_socorro", "ansioso_peito"}
CRITERIO_URGENCIA = {"urgencia_sem_piorar": "situações de urgência (saude_urgente, ajuda_socorro, ansioso_peito), "
                                            "somadas nos blinds: acertos do v6b ≥ acertos do v4"}


def certo(linha, vizinhas=False):
    if linha.get("sentido") == "certo" or linha.get("sentido_ident") == "certo":
        return 1
    return int(vizinhas and linha.get("sentido_vizinha") == "certo")


def ic95(valores, n_boot=2000, semente=0):
    """Média e IC 95% por bootstrap (reamostra as frases)."""
    n = len(valores)
    if not n:
        return None
    rr = random.Random(semente)
    medias = sorted(sum(valores[rr.randrange(n)] for _ in range(n)) / n for _ in range(n_boot))
    return {"media": round(sum(valores) / n, 4), "ic95": [round(medias[int(0.025 * n_boot)], 4), round(medias[int(0.975 * n_boot)], 4)], "n": n}


def pareado(novo, base, n_boot=2000, semente=0):
    """Diferença novo − base nas MESMAS frases (as listas vêm na mesma ordem; a chave confere)."""
    assert len(novo) == len(base) and all(a["chave"] == b["chave"] for a, b in zip(novo, base)), "linhas não pareiam"
    d = [certo(a) - certo(b) for a, b in zip(novo, base)]
    return ic95(d, n_boot, semente)


def chave(caso):
    return caso["situacao"] + "|" + caso["mensagem"] + "|" + " / ".join(caso.get("historico") or [])


def compacto(linhas):
    """O mínimo para parear e recontar: chave, sentido, identidade e vizinha."""
    return [{"chave": l["chave"], "sentido": l.get("sentido"), "sentido_ident": l.get("sentido_ident"),
             "sentido_vizinha": l.get("sentido_vizinha")} for l in linhas if l.get("sentido") is not None]


def urgencia(linhas):
    return sum(certo(l) for k in BLINDS_DECISIVOS for l in linhas.get(k, []) if l["chave"].split("|")[0][5:] in URGENTES)


def julgar_rodada(linhas_v6, linhas_v4, reais_certo, usa_fato, com_urgencia=False):
    """Os critérios de uma rodada (os quatro do v6; com_urgencia=True acrescenta o do v6b). linhas_*: {blind: [linhas]}."""
    dif = {k: pareado(linhas_v6[k], linhas_v4[k]) for k in BLINDS_DECISIVOS if k in linhas_v6 and k in linhas_v4}
    ok = {
        "v3_ic_inferior_maior_que_zero": bool(dif.get("v3") and dif["v3"]["ic95"][0] > 0),
        "outros_blinds_sem_piorar": all(dif[k]["media"] >= MINIMOS["piora_maxima"] for k in dif if k != "v3"),
        "frases_reais": reais_certo >= MINIMOS["frases_reais"],
        "usa_fato": usa_fato is not None and usa_fato >= MINIMOS["usa_fato"],
    }
    if com_urgencia:
        ok["urgencia_sem_piorar"] = urgencia(linhas_v6) >= urgencia(linhas_v4)
    return {"diferencas": dif, "criterios": ok, "passou": all(ok.values()),
            "urgencia_acertos": {"novo": urgencia(linhas_v6), "v4": urgencia(linhas_v4)}}


# v7c (fixado em 20/10/2026, ANTES da rodada 1, a pedido do criador): se a rodada 1 vencer com folga, a rodada 2 é
# dispensada. Folga = cada critério passa com margem maior que a variação medida entre o v7 e o v7b (blinds ±0,2 a 1,6
# ponto; frases reais ±1). Sem folga em qualquer item, a rodada 2 continua obrigatória.
FOLGA_UMA_RODADA = {
    "v3_ic_inferior": 0.03,      # limite inferior do IC 95% do blind v3 ≥ +3 pontos (a regra normal pede > 0)
    "outros_blinds": 0.0,        # v1, paráfrases, Grok e v4 sem perder nada (a regra normal aceita até −1,5)
    "frases_reais": 13,          # 13/15 (a regra normal pede 12)
    "usa_fato": 0.90,            # (a regra normal pede 0,85)
    "urgencia_a_mais": 5,        # urgência ≥ a do chat + 5 acertos (a regra normal pede ≥ a do chat)
}


def folga_uma_rodada(julgamento, reais_certo, usa_fato, passa_guarda_dev=True):
    """(dispensa a rodada 2?, {item: passou com folga}). julgamento: saída de julgar_rodada com urgência."""
    d, f = julgamento["diferencas"], FOLGA_UMA_RODADA
    itens = {
        "passou_na_regra_normal": bool(julgamento["passou"]),
        "v3_ic_inferior": bool(d.get("v3") and d["v3"]["ic95"][0] >= f["v3_ic_inferior"]),
        "outros_blinds": all(d[k]["media"] >= f["outros_blinds"] for k in d if k != "v3"),
        "frases_reais": reais_certo >= f["frases_reais"],
        "usa_fato": usa_fato is not None and usa_fato >= f["usa_fato"],
        "urgencia": julgamento["urgencia_acertos"]["novo"] >= julgamento["urgencia_acertos"]["v4"] + f["urgencia_a_mais"],
        "guarda_dev": bool(passa_guarda_dev),
    }
    return all(itens.values()), itens


def tabela(linhas_por_modelo):
    """{modelo: {blind: linhas}} → texto com estrita, com vizinhas e IC."""
    out = []
    for modelo, blinds in linhas_por_modelo.items():
        for k, ls in blinds.items():
            e, v = ic95([certo(l) for l in ls]), ic95([certo(l, True) for l in ls])
            out.append(f"{modelo:10s} {k:11s} estrita {100 * e['media']:5.1f}% [{100 * e['ic95'][0]:.1f}–{100 * e['ic95'][1]:.1f}]"
                       f" | com vizinhas {100 * v['media']:5.1f}% | n={e['n']}")
    return "\n".join(out)


def principal(pasta, com_urgencia=False):
    pasta = Path(pasta)
    base = json.loads((pasta / "linhas_v4_base.json").read_text())
    rodadas = {}
    for n in (1, 2):
        arq = pasta / f"linhas_rodada{n}.json"
        if arq.is_file():
            rodadas[n] = json.loads(arq.read_text())
    print(tabela({"v4": base["linhas"], **{f"v6 r{n}": r["linhas"] for n, r in rodadas.items()}}))
    for n, r in rodadas.items():
        j = julgar_rodada(r["linhas"], base["linhas"], r["frases_reais"], r["usa_fato"], com_urgencia)
        print(f"\nrodada {n}: passou={j['passou']} {j['criterios']}")
        for k, d in j["diferencas"].items():
            print(f"  {k:11s} v6 − v4 = {100 * d['media']:+.1f} pontos [{100 * d['ic95'][0]:+.1f}; {100 * d['ic95'][1]:+.1f}]")
    if len(rodadas) == 1 and com_urgencia:
        r = rodadas[1]
        j = julgar_rodada(r["linhas"], base["linhas"], r["frases_reais"], r["usa_fato"], com_urgencia)
        ok, itens = folga_uma_rodada(j, r["frases_reais"], r["usa_fato"])
        print(f"\nfolga para dispensar a rodada 2: {ok} {itens}")
    if len(rodadas) == 2:
        aprov = all(julgar_rodada(r["linhas"], base["linhas"], r["frases_reais"], r["usa_fato"], com_urgencia)["passou"] for r in rodadas.values())
        print("\nAS DUAS RODADAS PASSARAM: candidata a ser mostrada ao criador (não liga sozinha)." if aprov else
              "\nNão passou nas duas rodadas: não é candidata ao chat.")


if __name__ == "__main__":
    principal(sys.argv[1] if len(sys.argv) > 1 else ".")
