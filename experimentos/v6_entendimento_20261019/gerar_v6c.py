"""Dados do v6c (20/10/2026): as falas de formas_v6c (as do v6b sem os gatilhos que o diagnóstico do v6b achou),
com as mesmas regras do gerar_v6b.py (conflitos, filtro de parecença com os testes, respostas das listas existentes,
situações da v4), mas SEM equilíbrio.

Por que sem equilíbrio: no v6b, acrescentar casos tirou peso das situações que não ganharam nada (urgência −16 pontos,
situações da v4 −6). No v6c, o notebook faz SUBSTITUIÇÃO: cada caso novo entra no lugar de um caso antigo da fase 5 da
mesma situação, e o peso de cada situação no treino fica igual ao da v4. Isso só pode ser feito no notebook, porque os
dados da fase 5 v4 são gerados lá.

Origem: falas escritas pelo assistente de programação (Claude) com autorização do criador. Não são humanas.

Uso: python gerar_v6c.py [--resumo]   (escreve dados_v6c.json.gz e manifesto_v6c.json)
"""
import argparse
import gzip
import hashlib
import json
import random
import re
import unicodedata
import zlib
from collections import Counter

import numpy as np

import gerar_v6 as G   # caminhos, módulos da fase 5, congeladas() e parte()
import formas_v6c as formas_v6b   # v6c: mesmas regras, falas sem os gatilhos do diagnóstico do v6b

g1, revisao_v3, cenas_v4, ch = G.g1, G.revisao_v3, G.cenas_v4, G.ch
SEED = 20261020
LIMIAR_PARECIDA = 0.70
S4_ACEITAS = {"reciproco", "quem_sou_eu"}
D = 4096


def _norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " " + re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip() + " "


def vetor(s):
    s = _norm(s)
    v = np.zeros(D, np.float32)
    for n in (3, 4):
        for i in range(len(s) - n + 1):
            v[zlib.crc32(s[i:i + n].encode()) % D] += 1
    for w in s.split():
        v[zlib.crc32(("w:" + w).encode()) % D] += 2
    return v / (np.linalg.norm(v) + 1e-9)


def frases_de_teste():
    v1 = json.loads(gzip.open(G.EXP5 / "dados_fase5.json.gz").read().decode("utf-8"))
    v2 = json.loads(gzip.open(G.EXP5 / "dados_fase5_v2.json.gz").read().decode("utf-8"))
    v3 = json.loads(gzip.open(G.EXP5 / "dados_fase5_v3.json.gz").read().decode("utf-8"))
    t = ([c["mensagem"] for c in v1["blind"]] + [c["mensagem"] for k in ("blind_parafrase", "blind_grok") for c in v2[k]]
         + [c["mensagem"] for c in v3["blind_v3"]] + [c["mensagem"] for c in v3["dev"]]
         + [c["mensagem"] for c in cenas_v4.CONVERSAS_REAIS])
    for cen in list(cenas_v4.S4.values()) + [{"u": u} for u in cenas_v4.FORMAS_EXTRA.values()]:
        t += [u for u in cen["u"] if G.gerar_v4.parte(u) != "treino"]
    return sorted({_norm(x) for x in t})


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumo", action="store_true")
    a = ap.parse_args()
    rr = random.Random(SEED)
    S = g1.cenas.S
    revisao_v3.acrescentar_respostas(S)
    respostas = revisao_v3.respostas_para_treino(S)
    for n in S4_ACEITAS:
        respostas[n] = list(cenas_v4.S4[n]["c"])
    marcas = {n: S[n]["marcas"] for n in S} | {n: cenas_v4.S4[n]["marcas"] for n in S4_ACEITAS}
    cong, v3 = G.congeladas()
    rel = Counter()

    # 1. conferências (as mesmas do v6) e filtro de parecença
    teste = frases_de_teste()
    M = np.stack([vetor(x) for x in teste])
    dono, nucleos, parecidas = {}, {}, []
    for sit, falas in formas_v6b.FORMAS.items():
        assert (sit in S or sit in S4_ACEITAS) and sit not in G.FORA, sit
        assert not any("{" in r for r in respostas[sit]), sit
        vistas = set()
        for u in falas:
            k = ch(u)
            assert dono.get(k, sit) == sit, f"fala em duas situações: {u!r} ({dono[k]} e {sit})"
            dono[k] = sit
            if k in vistas:
                continue
            vistas.add(k)
            if k in cong:
                rel["igual_a_teste_congelado_fora"] += 1
                continue
            sim = float((M @ vetor(u)).max())
            if sim >= LIMIAR_PARECIDA:
                parecidas.append([u, round(sim, 2)])
                continue
            nucleos.setdefault(sit, {"treino": [], "dev": [], "blind_v6": []})[G.parte(u)].append(u)
    rel["parecida_com_teste_fora"] = len(parecidas)
    sit_v3 = {}
    for c in v3["treino"]:
        sit_v3.setdefault(ch(c["mensagem"]), set()).add(c["situacao"][5:] if c["situacao"].startswith("cena:") else c["situacao"])
    for n in S4_ACEITAS:   # formas da v4 que treinam: mesma regra de conflito
        for u in cenas_v4.S4[n]["u"]:
            if G.gerar_v4.parte(u) == "treino":
                sit_v3.setdefault(ch(u), set()).add(n)
    conflitos = [(u, sit, sorted(sit_v3.get(ch(u), set()) - {sit})) for sit, p in nucleos.items()
                 for u in sum(p.values(), []) if sit_v3.get(ch(u), set()) - {sit}]
    assert not conflitos, "conflito com o treino anterior:\n" + "\n".join(map(str, conflitos))

    # 2. turnos anteriores
    pares = sorted({(c["mensagem"], c["resposta"]) for c in v3["treino"] if c["situacao"].startswith("cena:") and not c["historico"]})
    com_pergunta = [p for p in pares if p[1].rstrip().endswith("?")]
    como_esta = [p for p in pares if cenas_v4.casa_antes("reciproco", p[1])]

    def caso(sit, fala, split, origem):
        u = fala
        if sit not in G.SEM_MOLDURA and rr.random() < 0.5:
            corpo = u.rstrip("?!.")
            u = rr.choice(G.ABRE) + corpo + rr.choice(G.FECHA) + u[len(corpo):]
        u = g1.ruido(u, rr)
        if sit in ("estou_bem", "reciproco"):
            hist = list(rr.choice(como_esta))
        elif sit in formas_v6b.DEPOIS_DE_PERGUNTA:
            hist = list(rr.choice(com_pergunta))
        elif sit in S and S[sit]["depois"]:
            hist = list(rr.choice(pares))
        else:
            hist = list(rr.choice(pares)) if rr.random() < 0.3 else []
        c = {"situacao": "cena:" + sit, "contexto": {}, "historico": hist, "mensagem": u, "resposta": rr.choice(respostas[sit]),
             "exigir": {"marcas": list(marcas[sit]), "nao_contem": []}, "fala_nucleo": fala, "origem": origem}
        if split != "treino":
            c["frase_nova"] = True
        return c

    dados = {"treino": [], "dev": [], "blind_v6": []}
    for sit in sorted(nucleos):
        for split, falas in nucleos[sit].items():
            for fala in falas:
                for _ in range(G.POR_FALA[split]):
                    dados[split].append(caso(sit, fala, split, "assistente_v6c"))

    rr.shuffle(dados["treino"])
    for split in dados:
        antes = len(dados[split])
        dados[split] = [c for c in dados[split] if ch(c["mensagem"]) not in cong]
        rel[f"ruido_igual_a_congelada_fora_{split}"] = antes - len(dados[split])
    novas_treino = {ch(c["fala_nucleo"]) for c in dados["treino"] if c["origem"] == "assistente_v6c"}
    assert not novas_treino & {ch(c["fala_nucleo"]) for c in dados["blind_v6"] + dados["dev"]}

    nuc = {s: {k: len(v) for k, v in p.items()} for s, p in sorted(nucleos.items())}
    bruto = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
    arq = G.AQUI / "dados_v6c.json.gz"
    with gzip.GzipFile(arq, "wb", mtime=0) as fz:
        fz.write(bruto)
    manifesto = {
        "protocolo": "v6c_entendimento", "seed": SEED, "dados_sha256": hashlib.sha256(bruto).hexdigest(),
        "arquivo_gz_sha256": G.sha(arq), "tamanhos": {k: len(v) for k, v in dados.items()},
        "por_origem_treino": dict(Counter(c["origem"] for c in dados["treino"])),
        "falas_por_parte": {k: sum(n[k] for n in nuc.values()) for k in G.POR_FALA},
        "situacoes": len(nuc), "falas_por_situacao": nuc, "parecidas_com_teste_fora": parecidas,
        "origem": "falas da pessoa escritas pelo assistente de programação (Claude) com autorização do criador "
                  "(19 e 20/10/2026), não são humanas; correções guiadas pelos erros do v6 e do v6b nos blinds antigos; "
                  "sem equilíbrio (o notebook substitui casos da fase 5 da mesma situação); respostas das listas existentes",
        "formas_v6_sha256": G.sha(G.AQUI / "formas_v6.py"), "formas_v6b_sha256": G.sha(G.AQUI / "formas_v6b.py"),
        "formas_v6c_sha256": G.sha(G.AQUI / "formas_v6c.py"),
        "gerar_v6_sha256": G.sha(G.AQUI / "gerar_v6.py"), "gerar_v6b_sha256": G.sha(G.AQUI / "gerar_v6b.py"),
        "gerar_v6c_sha256": G.sha(G.AQUI / "gerar_v6c.py"),
        "base_v3_gz_sha256": G.sha(G.EXP5 / "dados_fase5_v3.json.gz"), "relatorio": rel,
    }
    (G.AQUI / "manifesto_v6c.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if a.resumo:
        print(json.dumps({k: v for k, v in manifesto.items() if k != "falas_por_situacao"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    principal()
