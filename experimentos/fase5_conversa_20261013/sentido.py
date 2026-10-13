"""Mede o SENTIDO das respostas do 17M, além da forma.

O "tudo ok" de formato_fase5 confere forma e verdade: não inventou nome nem número, terminou, tem
a marca exigida. Em situações sem marca ("ok", "risada"…), quase qualquer frase passa. Na v2,
"cara ok beleza… entendi" recebeu "Desculpa, eu me confundi" e contou como certo.

Aqui cada resposta de cena é comparada com as respostas escritas para cada situação (cenas.py e
as outras levas). As respostas de treino saem dessas listas fechadas, então dá para dizer:
- certo: a resposta é uma das respostas da situação pedida;
- confundiu: é uma resposta de outra situação, e não da pedida;
- livre: não é nenhuma resposta escrita (o modelo compôs algo novo). Não dá para julgar sem ler.

Uso: python sentido.py resultado_fase5_v2.json [--parcial pasta] [--saida resumo.json]
"""
import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parents[1]))

import gerar_fase5 as g1  # noqa: E402  (cenas, cenas_mais, cenas_combos)
import cenas_grok  # noqa: E402,F401
import revisao_v3  # noqa: E402

S = g1.cenas.S
# Respostas novas da revisão (revisao_v3.py) contam como respostas da situação.
revisao_v3.acrescentar_respostas(S)


def norm(t):
    t = unicodedata.normalize("NFC", t).strip().casefold()
    return re.sub(r"\s+", " ", t)


def molde(resposta):
    partes = re.split(r"(\{[a-z_]+\})", norm(resposta))
    rx = "".join("(.+?)" if re.fullmatch(r"\{[a-z_]+\}", p) else re.escape(p) for p in partes)
    return re.compile(r"(?:[^,]{1,30}, )?" + rx + r"$")


EXATAS = defaultdict(set)   # resposta normalizada → situações
MOLDES = []                 # (regex, situação) para respostas com encaixe
for nome, c in S.items():
    for r in c["c"]:
        if "{" in r:
            MOLDES.append((molde(r), nome))
        else:
            EXATAS[norm(r)].add(nome)


def situacoes_da_resposta(texto):
    t = norm(texto)
    achadas = set(EXATAS.get(t, ()))
    # Pode vir com o nome da pessoa na frente ("Ana, desculpa…").
    m = re.match(r"^[^,]{1,30}, (.+)$", t)
    if m:
        achadas |= EXATAS.get(m.group(1), set())
    if not achadas:
        achadas = {nome for rx, nome in MOLDES if rx.match(t)}
    return achadas


def julgar(linha):
    sit = linha["situacao"]
    if not sit.startswith("cena:"):
        return None
    nome = sit[5:]
    achadas = situacoes_da_resposta(linha["saida"])
    if nome in achadas:
        return "certo", achadas
    if achadas:
        return "confundiu", achadas
    return "livre", achadas


def analisar(linhas, rotulo):
    cont, por_sit, confusoes, exemplos = Counter(), defaultdict(Counter), Counter(), []
    forma_ok_sentido_errado = 0
    for l in linhas:
        j = julgar(l)
        if j is None:
            continue
        veredito, achadas = j
        cont[veredito] += 1
        por_sit[l["situacao"][5:]][veredito] += 1
        if veredito == "confundiu":
            confusoes[(l["situacao"][5:], "/".join(sorted(achadas))[:60])] += 1
            if l.get("tudo_ok"):
                forma_ok_sentido_errado += 1
            if len(exemplos) < 25:
                exemplos.append({"situacao": l["situacao"][5:], "mensagem": l["mensagem"], "saida": l["saida"],
                                 "respondeu_como": sorted(achadas)[:3], "tudo_ok_antigo": l.get("tudo_ok")})
    n = sum(cont.values())
    taxa = lambda k: round(cont[k] / n, 4) if n else None
    sit = {s: {"n": sum(c.values()), "certo": round(c["certo"] / sum(c.values()), 3),
               "confundiu": round(c["confundiu"] / sum(c.values()), 3)} for s, c in sorted(por_sit.items())}
    piores = sorted(((v["certo"], s, v["n"]) for s, v in sit.items() if v["n"] >= 10))[:12]
    return {"teste": rotulo, "n_cenas": n, "certo": taxa("certo"), "confundiu": taxa("confundiu"),
            "livre": taxa("livre"), "confundiu_com_tudo_ok_antigo": forma_ok_sentido_errado,
            "cada_situacao_n10_min": piores[0][0] if piores else None,
            "situacoes_n10_abaixo_60": sum(1 for c, _, _ in piores if c < 0.60) if piores else 0,
            "piores": [{"situacao": s, "certo": c, "n": nn} for c, s, nn in piores],
            "confusoes_mais_comuns": [{"pedida": a, "respondeu_como": b, "vezes": k}
                                      for (a, b), k in confusoes.most_common(15)],
            "exemplos": exemplos, "por_situacao": sit}


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("resultado")
    ap.add_argument("--parcial", help="pasta com ponto_de_partida*.json (opcional)")
    ap.add_argument("--saida")
    a = ap.parse_args()
    res = json.loads(Path(a.resultado).read_text(encoding="utf-8"))
    out = {"protocolo": "sentido_fase5_v2", "commit_resultado": res.get("commit"), "escolhida": res.get("escolhida"),
           "variantes": {}}
    for nome, v in res["variantes"].items():
        out["variantes"][nome] = {
            "gates": v["gates"], "gate_pass": v["gate_pass"], "melhor_passo": v["melhor_passo"],
            "tudo_ok_antigo": {"v1": v["blind_v1"]["tudo_ok"], "parafrases": v["parafrases"]["tudo_ok"],
                               "grok": v["grok"]["tudo_ok"]},
            "sentido": {k: analisar(v[campo], k) for k, campo in
                        (("v1", "linhas_v1"), ("parafrases", "linhas_parafrases"), ("grok", "linhas_grok"))}}
    if a.parcial:
        p = Path(a.parcial)
        for k, arq in (("parafrases", "ponto_de_partida.json"), ("grok", "ponto_de_partida_grok.json")):
            if (p / arq).is_file():
                out.setdefault("ponto_de_partida_fase5", {})[k] = analisar(json.loads((p / arq).read_text()), k)
    for nome, v in out["variantes"].items():
        falhou = [k for k, ok in v["gates"].items() if not ok]
        print(f"[{nome}] gates que falharam: {falhou}")
        for k, s in v["sentido"].items():
            print(f"[{nome}] {k:10s} tudo_ok antigo {v['tudo_ok_antigo'][k]:.3f} | sentido certo {s['certo']} | "
                  f"confundiu {s['confundiu']} | livre {s['livre']} | situações (n≥10) abaixo de 60%: "
                  f"{s['situacoes_n10_abaixo_60']} | pior {s['piores'][:3]}")
    for k, s in out.get("ponto_de_partida_fase5", {}).items():
        print(f"[fase 5, antes da v2] {k:10s} sentido certo {s['certo']} | confundiu {s['confundiu']} | livre {s['livre']}")
    if a.saida:
        Path(a.saida).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("salvo em", a.saida)


if __name__ == "__main__":
    principal()
