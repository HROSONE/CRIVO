"""Dados do v7 (20/10/2026): volume. As falas de formas_v7 (v6c + grupos A–D, 108 situações) passam por três filtros:

1. conflito com o treino antigo (a mesma fala com outra situação): a fala SAI (no v6c, parava a geração);
2. parecença com os testes congelados (cosseno de n-gramas ≥ 0,7): sai;
3. detector de gatilhos (detector_gatilhos.py): sai toda fala mais parecida com o treino de OUTRA situação do que com o da
   própria (≥ 0,5), ou perto de saúde/urgência (≥ 0,4). Conferido antes nos culpados conhecidos do v6/v6b: pegou 10 de 17
   sem olhar os testes.

Sem equilíbrio: o notebook substitui casos da fase 5 da mesma situação (substituicao_v6c.py), e o peso de cada situação
fica igual ao da v4. Origem: falas escritas pelo assistente de programação (Claude), com autorização do criador; não são
humanas.

Uso: python gerar_v7.py [--resumo]   (escreve dados_v7.json.gz e manifesto_v7.json)
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
import formas_v7 as formas_v6b   # v7: mesmas regras do v6b/v6c, com volume
import detector_gatilhos

g1, revisao_v3, cenas_v4, ch = G.g1, G.revisao_v3, G.cenas_v4, G.ch
SEED = 20261020
# Casos por fala. As minhas são poucas e ganham grafias, molduras e históricos; as do professor já são muitas e variadas.
POR_FALA = {"assistente_v7": {"treino": 16, "dev": 2, "blind_v6": 3}, "professor_v7": {"treino": 4, "dev": 1, "blind_v6": 1}}
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
    ap.add_argument("--professor", help="jsonl.gz de professor_v7.py (opcional)")
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
    fontes = [(sit, u, "assistente_v7") for sit, falas in formas_v6b.FORMAS.items() for u in falas]
    PROF = []
    if a.professor:   # falas da pessoa escritas pelo professor (professor_v7.py), já conferidas por ele mesmo
        with gzip.open(a.professor, "rt", encoding="utf-8") as f:
            PROF = [json.loads(l) for l in f]
        fontes += [(x["situacao"], x["fala"], "professor_v7") for x in PROF]
    for sit, _, _ in fontes:
        assert (sit in S or sit in S4_ACEITAS) and sit not in G.FORA, sit
        assert not any("{" in r for r in respostas[sit]), sit
    # a mesma fala em duas situações: entre as minhas, para tudo; com o professor, sai a do professor (ambígua)
    sits_de = {}
    for sit, u, org in fontes:
        sits_de.setdefault(ch(u), {}).setdefault(sit, set()).add(org)
    for k, por in sits_de.items():
        minhas = [s_ for s_, o in por.items() if "assistente_v7" in o]
        assert len(minhas) <= 1, f"fala em duas situações: {k!r} {sorted(por)}"
    ambiguas = {k for k, por in sits_de.items() if len(por) > 1}
    rel["professor_ambigua_fora"] = sum(1 for sit, u, org in fontes if org == "professor_v7" and ch(u) in ambiguas)
    vistas, candidatas = set(), []
    for sit, u, org in fontes:
        k = ch(u)
        if org == "professor_v7" and k in ambiguas or k in vistas:
            continue
        vistas.add(k)
        if k in cong:
            rel["igual_a_teste_congelado_fora"] += 1
            continue
        candidatas.append((sit, u, org))
    V = np.stack([vetor(u) for _, u, _ in candidatas]) if candidatas else np.zeros((0, M.shape[1]), np.float32)
    maior = np.concatenate([(V[i:i + 512] @ M.T).max(1) for i in range(0, len(V), 512)]) if len(V) else np.zeros(0)
    nucleos, parecidas, origem_de = {}, [], {}
    for (sit, u, org), sim in zip(candidatas, maior):
        if sim >= LIMIAR_PARECIDA:
            parecidas.append([u, round(float(sim), 2)])
            continue
        nucleos.setdefault(sit, {"treino": [], "dev": [], "blind_v6": []})[G.parte(u)].append(u)
        origem_de[(sit, u)] = org
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
    tirar = {(sit, u) for u, sit, _ in conflitos}
    rel["conflito_com_treino_antigo_fora"] = len(tirar)
    # 3. detector de gatilhos, sobre todas as falas que sobraram (treino, dev e blind)
    candidatas = {sit: [u for u in sum(p.values(), []) if (sit, u) not in tirar] for sit, p in nucleos.items()}
    gatilhos = detector_gatilhos.detectar(candidatas)
    tirar |= {(g["situacao"], g["fala"]) for g in gatilhos}
    rel["gatilho_fora"] = len(gatilhos)
    for sit in nucleos:
        for parte_ in nucleos[sit]:
            nucleos[sit][parte_] = [u for u in nucleos[sit][parte_] if (sit, u) not in tirar]
    nucleos = {s: p for s, p in nucleos.items() if any(p.values())}
    treino_v3 = {ch(c["mensagem"]) for c in v3["treino"]}
    novas = {s: sum(ch(u) not in treino_v3 for u in p["treino"]) for s, p in nucleos.items()}
    rel["falas_de_treino_que_nao_estavam_no_treino_v3"] = sum(novas.values())

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
                org = origem_de[(sit, fala)]
                for _ in range(POR_FALA[org][split]):
                    dados[split].append(caso(sit, fala, split, org))

    rr.shuffle(dados["treino"])
    for split in dados:
        antes = len(dados[split])
        dados[split] = [c for c in dados[split] if ch(c["mensagem"]) not in cong]
        rel[f"ruido_igual_a_congelada_fora_{split}"] = antes - len(dados[split])
    novas_treino = {ch(c["fala_nucleo"]) for c in dados["treino"] if c["origem"] in ("assistente_v7", "professor_v7")}
    assert not novas_treino & {ch(c["fala_nucleo"]) for c in dados["blind_v6"] + dados["dev"]}

    nuc = {s: {k: len(v) for k, v in p.items()} for s, p in sorted(nucleos.items())}
    bruto = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
    arq = G.AQUI / "dados_v7.json.gz"
    with gzip.GzipFile(arq, "wb", mtime=0) as fz:
        fz.write(bruto)
    manifesto = {
        "protocolo": "v7_entendimento", "seed": SEED, "dados_sha256": hashlib.sha256(bruto).hexdigest(),
        "arquivo_gz_sha256": G.sha(arq), "tamanhos": {k: len(v) for k, v in dados.items()},
        "por_origem_treino": dict(Counter(c["origem"] for c in dados["treino"])),
        "falas_por_parte": {k: sum(n[k] for n in nuc.values()) for k in G.POR_FALA},
        "falas_por_origem": {o: {k: sum(1 for (s_, u), o_ in origem_de.items() if o_ == o and u in nucleos.get(s_, {}).get(k, []))
                                 for k in G.POR_FALA} for o in POR_FALA},
        "casos_por_origem": {k: dict(Counter(c["origem"] for c in v)) for k, v in dados.items()},
        "professor": {"arquivo_sha256": G.sha(a.professor) if a.professor else None, "falas_recebidas": len(PROF),
                      "modelos": dict(Counter(x.get("modelo") for x in PROF)),
                      "aviso": "falas da pessoa escritas por modelo de terceiros (professor, AGENTS.md); não são humanas"},
        "situacoes": len(nuc), "falas_por_situacao": nuc, "parecidas_com_teste_fora": parecidas,
        "origem": "falas da pessoa escritas pelo assistente de programação (Claude) com autorização do criador "
                  "(19 e 20/10/2026), não são humanas; correções guiadas pelos erros do v6 e do v6b nos blinds antigos; filtros de "
                  "conflito, parecença com testes e gatilhos; sem equilíbrio (o notebook substitui casos da fase 5 da mesma "
                  "situação); respostas das listas existentes",
        "formas_v6_sha256": G.sha(G.AQUI / "formas_v6.py"), "formas_v6b_sha256": G.sha(G.AQUI / "formas_v6b.py"),
        "formas_v6c_sha256": G.sha(G.AQUI / "formas_v6c.py"),
        **{f"{n}_sha256": G.sha(G.AQUI / f"{n}.py") for n in ("formas_v7", "formas_v7_a", "formas_v7_b", "formas_v7_c",
                                                              "formas_v7_d", "formas_v7_e", "detector_gatilhos", "substituicao_v6c")},
        "conflitos_fora": [list(x) for x in conflitos], "gatilhos_fora": gatilhos, "falas_novas_por_situacao": novas,
        "gerar_v6_sha256": G.sha(G.AQUI / "gerar_v6.py"), "gerar_v6b_sha256": G.sha(G.AQUI / "gerar_v6b.py"),
        "gerar_v6c_sha256": G.sha(G.AQUI / "gerar_v6c.py"),
        "gerar_v7_sha256": G.sha(G.AQUI / "gerar_v7.py"),
        "base_v3_gz_sha256": G.sha(G.EXP5 / "dados_fase5_v3.json.gz"), "relatorio": rel,
    }
    (G.AQUI / "manifesto_v7.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if a.resumo:
        print(json.dumps({k: v for k, v in manifesto.items() if k != "falas_por_situacao"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    principal()
