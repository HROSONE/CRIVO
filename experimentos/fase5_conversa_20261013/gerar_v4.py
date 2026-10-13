"""Dados da fase 5 v4: o 17M lendo o que a pessoa quis dizer, inclusive pelo que veio antes.

Parte dos dados da v3 (dados_fase5_v3.json.gz, congelados) e acrescenta:

1. **Situações novas** (cenas_v4.py), que apareceram nas conversas reais do criador:
   "e você?" depois de "como você está?", "você é o crivo, né?", "sabe quem eu sou?" e
   "então você não sabe". As que dependem do turno anterior só aparecem depois de uma resposta do
   CRIVO que combina (cenas_v4.casa_antes). As falas são divididas por hash: 70% treino, 10% dev,
   20% blind_v4.
2. **Correções nos dados da v3:**
   - "preciso de ajuda agora/agr/urgente" sai da ajuda calma e vai para ajuda_socorro, igual a
     crise.py (o conflito custou 4 dos 7 erros de urgência da v3 D);
   - "tô bem, e você?" sai de estou_bem: vira reciproco quando o CRIVO tinha perguntado como a
     pessoa está, e sai do treino quando não tinha.
3. **Reforço das situações fracas:** as situações com sentido abaixo de 60% (n ≥ 10) no blind v3
   da D (resultado_v3_resumo.json) ganham uma cópia de cada caso de treino, com ruído de digitação novo.
4. **conversas_reais:** as frases que o criador digitou, com o que o CRIVO tinha mostrado antes.
   Ficam só no teste, e nenhuma fala de treino tem a mesma chave.

Uso: python gerar_v4.py [--resumo]
"""
import argparse
import gzip
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parents[1]))

import gerar_fase5 as g1  # noqa: E402
import cenas_grok  # noqa: E402,F401
import revisao_v3  # noqa: E402
import formas_grok  # noqa: E402
import cenas_v4  # noqa: E402

SEED = 20261016
CASOS = {"treino": 1400, "dev": 60, "blind_v4": 150}
AJUDA_URGENTE = re.compile(r"\bpreciso de ajuda (?:agora|agr|urgente|r[aá]pido|j[aá])\b", re.I)
DEVOLVE = re.compile(r"\be (?:voc[eê]|vc|tu|contigo|ctg|com voc[eê]|com vc)\s*\??\s*$", re.I)
ch = formas_grok.chave


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parte(fala):
    h = int(hashlib.sha256(("v4:" + ch(fala)).encode()).hexdigest()[:8], 16) % 100
    return "blind_v4" if h < 20 else "dev" if h < 30 else "treino"


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumo", action="store_true")
    a = ap.parse_args()
    rr = random.Random(SEED)
    S = g1.cenas.S
    revisao_v3.acrescentar_respostas(S)
    para_treino = revisao_v3.respostas_para_treino(S)
    v3 = json.loads(gzip.open(AQUI / "dados_fase5_v3.json.gz").read().decode("utf-8"))
    # Frase real que já era forma de treino na v3 fica (o teste a marca como vista); as novas saem.
    no_treino_v3 = {ch(c["mensagem"]) for c in v3["treino"]}
    reais = {ch(c["mensagem"]) for c in cenas_v4.CONVERSAS_REAIS} - no_treino_v3
    # Nenhuma forma nova pode repetir uma fala dos testes congelados (v1, v2, v3).
    v1 = json.loads(gzip.open(AQUI / "dados_fase5.json.gz").read().decode("utf-8"))
    v2 = json.loads(gzip.open(AQUI / "dados_fase5_v2.json.gz").read().decode("utf-8"))
    congeladas = ({ch(c["mensagem"]) for c in v3["blind_v3"]} | {ch(c["mensagem"]) for c in v1["blind"]}
                  | {ch(c["mensagem"]) for k in ("blind_parafrase", "blind_grok") for c in v2[k]})
    rel = Counter()

    # 2. correções nos dados da v3 (só treino e dev; o blind v3 é congelado)
    def corrigir(casos):
        out = []
        for c in casos:
            c = dict(c)
            if ch(c["mensagem"]) in reais:
                rel["fora_por_ser_conversa_real"] += 1
                continue
            sit = c["situacao"]
            if sit == "cena:ajuda" and AJUDA_URGENTE.search(c["mensagem"]):
                c.update(situacao="cena:ajuda_socorro", resposta=rr.choice(para_treino["ajuda_socorro"]),
                         exigir={"marcas": ["urgente"], "nao_contem": []})
                rel["ajuda_para_socorro"] += 1
            elif sit == "cena:estou_bem" and DEVOLVE.search(c["mensagem"]):
                ultima = c["historico"][-1] if c["historico"] else ""
                if not cenas_v4.casa_antes("reciproco", ultima):
                    rel["estou_bem_devolvendo_sem_pergunta_fora"] += 1
                    continue
                c.update(situacao="cena:reciproco", resposta=rr.choice(cenas_v4.S4["reciproco"]["c"]),
                         exigir={"marcas": [], "nao_contem": []})
                rel["estou_bem_para_reciproco"] += 1
            out.append(c)
        return out

    treino, dev = corrigir(v3["treino"]), corrigir(v3["dev"])

    # pares (fala, resposta) para montar o turno anterior das situações novas
    pares = [(c["mensagem"], c["resposta"]) for c in v3["treino"] if c["situacao"].startswith(("cena:", "nao_sei:"))
             and ch(c["mensagem"]) not in reais]
    nomes_meu = [c for c in v3["treino"] if c["situacao"] == "nome:meu"]

    # 1. situações novas
    novos = {k: [] for k in CASOS}
    extras = {n: {"u": u, "c": para_treino[n], "marcas": S[n]["marcas"], "depois": None, "antes": None}
              for n, u in cenas_v4.FORMAS_EXTRA.items()}
    for nome, cen in list(cenas_v4.S4.items()) + list(extras.items()):
        formas = {k: [] for k in CASOS}
        for u in cen["u"]:
            if ch(u) in reais or ch(u) in {ch(c["mensagem"]) for c in cenas_v4.CONVERSAS_REAIS}:
                rel["forma_igual_a_conversa_real_fora"] += 1
                continue
            if ch(u) in congeladas:
                rel["forma_igual_a_teste_congelado_fora"] += 1
                continue
            formas[parte(u)].append(u)
        rel[f"formas_{nome}"] = {k: len(v) for k, v in formas.items()}
        antes = [p for p in pares if cenas_v4.casa_antes(nome, p[1])] if cen["antes"] else pares
        rel[f"turnos_anteriores_{nome}"] = len(antes)
        for split, n in CASOS.items():
            if not formas[split]:
                continue
            for _ in range(n):
                hist, ctx, exigir = [], {}, {"marcas": list(cen["marcas"]), "nao_contem": []}
                for _ in range(rr.choice((0, 0, 1, 2))):
                    hist += list(rr.choice(pares))
                resp = rr.choice(cen["c"])
                if nome == "quem_sou_eu" and nomes_meu and rr.random() < 0.3:
                    m = rr.choice(nomes_meu)
                    nm = m["contexto"]["nomes"]["você"]
                    hist += [m["mensagem"], m["resposta"]]
                    ctx = {"nomes": {"você": nm}}
                    resp = rr.choice(cenas_v4.RESP_QUEM_SOU_COM_NOME).replace("{nome}", nm)
                    exigir["nomes"] = [nm]
                if cen["depois"] or cen["antes"]:
                    hist += list(rr.choice(antes))
                caso = {"situacao": "cena:" + nome, "contexto": ctx, "historico": hist,
                        "mensagem": g1.ruido(rr.choice(formas[split]), rr), "resposta": resp, "exigir": exigir}
                if split != "treino":
                    caso["frase_nova"] = True
                novos[split].append(caso)

    # 3. reforço das situações fracas na D
    resumo = json.loads((AQUI / "resultado_v3_resumo.json").read_text(encoding="utf-8"))
    piores = resumo["variantes"]["D"]["testes"]["v3"]["sentido_por_situacao"]
    fracas = sorted(s for s, x in piores.items() if x["n"] >= 10 and x["certo"] < 0.60)
    reforco = []
    for c in treino:
        if c["situacao"].startswith("cena:") and c["situacao"][5:] in fracas:
            reforco.append({**c, "mensagem": g1.ruido(c["mensagem"], rr)})
    rel["situacoes_reforcadas"] = fracas
    rel["casos_de_reforco"] = len(reforco)

    treino = treino + novos["treino"] + reforco
    rr.shuffle(treino)
    dev = dev + novos["dev"]
    reais_casos = []
    vistas = {ch(c["mensagem"]) for c in treino}
    for c in cenas_v4.CONVERSAS_REAIS:
        reais_casos.append({"situacao": "real:" + c["aceita"][0], "aceita": c["aceita"], "contexto": {},
                            "historico": c["historico"], "mensagem": c["mensagem"], "resposta": "",
                            "exigir": {}, "vista_no_treino": ch(c["mensagem"]) in vistas})
    assert not any(c["vista_no_treino"] for c in reais_casos if ch(c["mensagem"]) in reais)
    assert not ({ch(c["mensagem"]) for c in novos["treino"]} & congeladas)
    dados = {"treino": treino, "dev": dev, "blind_v4": novos["blind_v4"], "conversas_reais": reais_casos}
    bruto = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
    arq = AQUI / "dados_fase5_v4.json.gz"
    with gzip.GzipFile(arq, "wb", mtime=0) as f:
        f.write(bruto)
    manifesto = {
        "protocolo": "fase5_v4", "seed": SEED, "dados_sha256": hashlib.sha256(bruto).hexdigest(),
        "arquivo_gz_sha256": sha(arq), "tamanhos": {k: len(v) for k, v in dados.items()},
        "base_v3_gz_sha256": sha(AQUI / "dados_fase5_v3.json.gz"),
        "cenas_v4_sha256": sha(AQUI / "cenas_v4.py"), "gerar_v4_sha256": sha(AQUI / "gerar_v4.py"),
        "sentido_sha256": sha(AQUI / "sentido.py"), "formato_fase5_sha256": sha(AQUI / "formato_fase5.py"),
        "resumo_v3_sha256": sha(AQUI / "resultado_v3_resumo.json"), "relatorio": rel,
    }
    (AQUI / "manifesto_v4.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if a.resumo:
        print(json.dumps(manifesto, ensure_ascii=False, indent=1))
        print(Counter(c["situacao"] for c in novos["treino"]))


if __name__ == "__main__":
    principal()
