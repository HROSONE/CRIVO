"""Dados do treino v6 "entendimento": falas novas da pessoa (formas_v6.py) com as respostas de sempre.

Regras (auditoria de 19/10/2026, experimentos/auditoria_treino_20261019/RELATORIO.md):
- respostas só das listas que já existem (revisao_v3.respostas_para_treino): nenhuma fala ganha uma
  segunda resposta-alvo;
- uma fala não pode estar em duas situações, nem repetir uma fala dos testes congelados (blind v1, paráfrases,
  Grok, blind v3, dev/blind v4, frases reais do criador). Isso é conferido aqui e para a geração se falhar;
- a divisão treino/dev/blind_v6 é por FALA (núcleo), antes do ruído de digitação: o blind_v6 só tem falas
  que o treino nunca viu, em nenhuma grafia;
- ficam de fora: situações com encaixe ({motivo}), de saúde ou urgência (crise.py responde antes do modelo) e
  as que o IDENTIDADE.md cobre (extras_fase6b.FASE5_SUBSTITUIDAS).

Origem: falas escritas pelo assistente de programação (Claude), com autorização do criador. Não são humanas.

Uso: python gerar_v6.py [--resumo]   (escreve dados_v6.json.gz e manifesto_v6.json nesta pasta)
"""
import argparse
import gzip
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
EXP5 = RAIZ / "experimentos" / "fase5_conversa_20261013"
for p in (str(AQUI), str(EXP5), str(RAIZ / "experimentos" / "fase6b_conversa_humana"), str(RAIZ)):
    if p not in sys.path:
        sys.path.insert(0, p)

import gerar_fase5 as g1  # noqa: E402
import cenas_grok  # noqa: E402,F401
import revisao_v3  # noqa: E402
import formas_grok  # noqa: E402
import cenas_v4  # noqa: E402
import gerar_v4  # noqa: E402
import extras_fase6b  # noqa: E402
import formas_v6  # noqa: E402

SEED = 20261019
ch = formas_grok.chave
# Casos por fala em cada parte: no treino, a mesma fala aparece com grafias, molduras e históricos diferentes.
POR_FALA = {"treino": 16, "dev": 2, "blind_v6": 3}
FORA = {"ajuda_socorro", "ansioso_peito", "saude_urgente", "saude_geral"} | set(extras_fase6b.FASE5_SUBSTITUIDAS)
# Molduras neutras: não mudam o sentido. Não entram em falas muito curtas, em que mudariam (risada, "eita"...).
ABRE = ["", "", "", "", "crivo, ", "olha, ", "cara, ", "mano, ", "então, ", "ei, ", "pois é, ", "bom, "]
FECHA = ["", "", "", "", " viu", " cara", " crivo", " mano", "..."]
SEM_MOLDURA = {"sem_sentido", "risada", "expressao_curta", "teste"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parte(fala):
    h = int(hashlib.sha256(("v6:" + ch(fala)).encode()).hexdigest()[:8], 16) % 100
    return "blind_v6" if h < 20 else "dev" if h < 30 else "treino"


def congeladas():
    """Chaves de todas as falas de teste/dev já usadas como régua."""
    v1 = json.loads(gzip.open(EXP5 / "dados_fase5.json.gz").read().decode("utf-8"))
    v2 = json.loads(gzip.open(EXP5 / "dados_fase5_v2.json.gz").read().decode("utf-8"))
    v3 = json.loads(gzip.open(EXP5 / "dados_fase5_v3.json.gz").read().decode("utf-8"))
    cong = ({ch(c["mensagem"]) for c in v1["blind"]} | {ch(c["mensagem"]) for k in ("blind_parafrase", "blind_grok") for c in v2[k]}
            | {ch(c["mensagem"]) for c in v3["blind_v3"]} | {ch(c["mensagem"]) for c in v3["dev"]}
            | {ch(c["mensagem"]) for c in cenas_v4.CONVERSAS_REAIS})
    for cen in list(cenas_v4.S4.values()) + [{"u": u} for u in cenas_v4.FORMAS_EXTRA.values()]:
        cong |= {ch(u) for u in cen["u"] if gerar_v4.parte(u) != "treino"}
    return cong, v3


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumo", action="store_true")
    a = ap.parse_args()
    rr = random.Random(SEED)
    S = g1.cenas.S
    revisao_v3.acrescentar_respostas(S)
    respostas = revisao_v3.respostas_para_treino(S)
    cong, v3 = congeladas()
    treino_v3 = {ch(c["mensagem"]) for c in v3["treino"]}
    rel = Counter()

    # 1. conferências das falas
    dono = {}
    for sit, falas in formas_v6.FORMAS.items():
        assert sit in S, f"situação desconhecida: {sit}"
        assert sit not in FORA, f"situação fora do v6: {sit}"
        assert not any("{" in r for r in respostas[sit]), f"{sit} tem resposta com encaixe"
        for u in falas:
            k = ch(u)
            assert dono.get(k, sit) == sit, f"fala em duas situações: {u!r} ({dono[k]} e {sit})"
            dono[k] = sit
    nucleos = {}
    for sit, falas in formas_v6.FORMAS.items():
        vistas = set()
        for u in falas:
            k = ch(u)
            if k in vistas:
                rel["repetida_na_lista"] += 1
                continue
            vistas.add(k)
            if k in cong:
                rel["igual_a_teste_congelado_fora"] += 1
                continue
            if k in treino_v3:
                rel["ja_no_treino_v3"] += 1   # fica: não é nova, mas não conflita (mesma situação conferida abaixo)
            nucleos.setdefault(sit, {"treino": [], "dev": [], "blind_v6": []})[parte(u)].append(u)
    # mesma fala já no treino v3 com OUTRA situação = conflito
    sit_v3 = {}
    for c in v3["treino"]:
        sit_v3.setdefault(ch(c["mensagem"]), set()).add(c["situacao"][5:] if c["situacao"].startswith("cena:") else c["situacao"])
    conflitos = [(u, sit, sorted(sit_v3.get(ch(u), set()) - {sit})) for sit, partes in nucleos.items()
                 for u in sum(partes.values(), []) if sit_v3.get(ch(u), set()) - {sit}]
    assert not conflitos, "conflito com o treino v3 (fala, aqui, lá):\n" + "\n".join(map(str, conflitos))

    # 2. turnos anteriores: qualquer par do treino v3; depois de pergunta, só pares cuja resposta termina perguntando
    pares = [(c["mensagem"], c["resposta"]) for c in v3["treino"] if c["situacao"].startswith("cena:") and not c["historico"]]
    pares = sorted(set(pares))
    com_pergunta = [p for p in pares if p[1].rstrip().endswith("?")]
    como_esta = [p for p in pares if cenas_v4.casa_antes("reciproco", p[1])]
    rel["pares_turno_anterior"] = {"todos": len(pares), "com_pergunta": len(com_pergunta), "como_esta": len(como_esta)}

    def caso(sit, fala, split):
        u = fala
        if sit not in SEM_MOLDURA and rr.random() < 0.5:
            corpo = u.rstrip("?!.")
            u = rr.choice(ABRE) + corpo + rr.choice(FECHA) + u[len(corpo):]   # "seremos amigos, cara?" e não "amigos? cara"
        u = g1.ruido(u, rr)
        hist = []
        if sit == "estou_bem":
            hist = list(rr.choice(como_esta))
        elif sit in formas_v6.DEPOIS_DE_PERGUNTA:
            hist = list(rr.choice(com_pergunta))
        elif S[sit]["depois"]:
            hist = list(rr.choice(pares))
        elif rr.random() < 0.3:
            hist = list(rr.choice(pares))   # uma conversa antes, que não muda o sentido
        c = {"situacao": "cena:" + sit, "contexto": {}, "historico": hist, "mensagem": u,
             "resposta": rr.choice(respostas[sit]), "exigir": {"marcas": list(S[sit]["marcas"]), "nao_contem": []},
             "fala_nucleo": fala, "origem": "assistente_v6"}
        if split != "treino":
            c["frase_nova"] = True
        return c

    dados = {"treino": [], "dev": [], "blind_v6": []}
    for sit in sorted(nucleos):
        for split, falas in nucleos[sit].items():
            for fala in falas:
                for _ in range(POR_FALA[split]):
                    dados[split].append(caso(sit, fala, split))
    rr.shuffle(dados["treino"])
    # o ruído nunca pode recriar uma fala congelada
    for split in dados:
        antes = len(dados[split])
        dados[split] = [c for c in dados[split] if ch(c["mensagem"]) not in cong]
        rel[f"ruido_igual_a_congelada_fora_{split}"] = antes - len(dados[split])
    chaves_treino = {ch(c["fala_nucleo"]) for c in dados["treino"]}
    assert not chaves_treino & {ch(c["fala_nucleo"]) for c in dados["blind_v6"] + dados["dev"]}

    nuc = {s: {k: len(v) for k, v in p.items()} for s, p in sorted(nucleos.items())}
    bruto = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
    arq = AQUI / "dados_v6.json.gz"
    with gzip.GzipFile(arq, "wb", mtime=0) as fz:
        fz.write(bruto)
    manifesto = {
        "protocolo": "v6_entendimento", "seed": SEED, "dados_sha256": hashlib.sha256(bruto).hexdigest(),
        "arquivo_gz_sha256": sha(arq), "tamanhos": {k: len(v) for k, v in dados.items()},
        "falas_por_parte": {k: sum(n[k] for n in nuc.values()) for k in POR_FALA},
        "situacoes": len(nuc), "falas_por_situacao": nuc,
        "origem": "falas da pessoa escritas pelo assistente de programação (Claude) com autorização do criador "
                  "(19/10/2026); não são humanas; respostas das listas existentes da fase 5",
        "formas_v6_sha256": sha(AQUI / "formas_v6.py"), "gerar_v6_sha256": sha(AQUI / "gerar_v6.py"),
        "base_v3_gz_sha256": sha(EXP5 / "dados_fase5_v3.json.gz"), "relatorio": rel,
    }
    (AQUI / "manifesto_v6.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if a.resumo:
        print(json.dumps({k: v for k, v in manifesto.items() if k != "falas_por_situacao"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    principal()
