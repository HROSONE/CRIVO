"""Gera e congela os dados da fase 5 v2: currículo de formas de fala, antes de qualquer treino.

Uso: python gerar_v2.py [--resumo]
Saída nesta pasta: dados_fase5_v2.json.gz e manifesto_v2.json.

A v1 (dados_fase5.json.gz) fica intacta: o treino da v2 mistura os casos da v1 (ensaio, para não
regredir) com este currículo, e o blind da v1 continua sendo o teste de não regressão.

Splits deste arquivo:
  treino            conversas da v1 em que ~60% das cenas são das situações de formas_v2.py, com
                    as formas de treino compostas e os contraexemplos;
  dev               o mesmo, em outras conversas (escolha do ponto do treino);
  blind_parafrase   conversas cujo ÚLTIMO turno usa uma forma reservada (parte de conteúdo que o
                    treino nunca viu); só esse turno entra na avaliação.
"""
import argparse
import gzip
import hashlib
import json
import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import gerar_fase5 as g1  # noqa: E402  (traz cenas, cenas_mais e cenas_combos)
import formas_v2  # noqa: E402

SEED = 20261014
CONVERSAS = {"treino": 52000, "dev": 700, "blind_parafrase": 3000}
PESO_V2 = 0.6


class ConversaV2(g1.Conversa):
    def cena(self, nome):
        c, rr = g1.cenas.S[nome], self.rr
        if c["depois"] == "resposta" and not self.hist:
            return False
        u = rr.choice(self.formas[nome])
        respostas = c["c"]
        if "{" not in u:
            # Fala sem encaixe: só respostas que não dependem de um motivo sorteado.
            respostas = [r for r in respostas if "{" not in r.replace("{ultima}", "")] or []
            if not respostas:
                return False
        slots = g1.slots_da_cena(rr)
        if self.hist:
            slots["ultima"] = self.hist[-1]
        u = g1.preencher(u, slots)
        resp = g1.preencher(rr.choice(respostas), slots)
        if "{" in resp or "{" in u:
            return False
        if "você" in self.nomes and rr.random() < 0.15 and resp[:2] not in ("Sou", "Eu"):
            resp = self.nomes["você"] + ", " + resp[0].lower() + resp[1:]
        ctx = {"cuidado": c["cuidado"]} if c["cuidado"] else {}
        exigir = {"marcas": c["marcas"], "nao_contem": c["nao_contem"]}
        self.turno(self.fala(u), resp, "cena:" + nome, ctx, exigir)
        if u in CONTRA_BLIND:
            self.casos[-1]["contraexemplo"] = True
        self.ultimo = ("cena", nome)
        return True


CONTRA_BLIND = {f for _, _, blind in formas_v2.CONTRAEXEMPLOS for f in blind}


def montar(rr, fatos, nomes, formas, v2_nomes, so_ultimo_v2=False):
    conv = ConversaV2(rr, "", fatos, nomes, formas)
    alvo = rr.choice([1, 2, 2, 3, 3, 4, 5, 6])
    tentativas = 0
    while len(conv.casos) < alvo and tentativas < 40:
        tentativas += 1
        ultimo = len(conv.casos) == alvo - 1
        if so_ultimo_v2:
            if ultimo:
                conv.cena(rr.choice(v2_nomes))
                continue
            tipo = rr.choices([p[0] for p in g1.PESOS], [p[1] for p in g1.PESOS])[0]
        else:
            tipo = "v2" if rr.random() < PESO_V2 else rr.choices([p[0] for p in g1.PESOS], [p[1] for p in g1.PESOS])[0]
        if tipo == "v2":
            conv.cena(rr.choice(v2_nomes))
        elif tipo == "cena":
            conv.cena(rr.choice(list(g1.cenas.S)))
        else:
            getattr(conv, tipo)()
    return conv.casos


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumo", action="store_true")
    a = ap.parse_args()
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(g1.TOKENIZER))
    rr = random.Random(SEED)
    from crivo import Crivo
    from curriculo_mundo import texto_fato
    itens = Crivo().compositor.itens
    fatos = {"treino": [], "dev": [], "blind": []}
    for chave, item in sorted(itens.items()):
        fs = [texto_fato(f) for f in item["fatos"] if f.get("natureza") != "religioso"]
        fs = [f for f in fs if 12 <= len(f) <= 260]
        if fs and 2 <= len(item["nome"]) <= 40:
            fatos[g1.parte("assunto:" + chave)].append((item["nome"], fs[:4]))
    nomes = g1.gerar_nomes(tok, rr)
    v2_nomes = sorted(n for n in formas_v2.FORMAS if n in g1.cenas.S)
    faltam = sorted(set(formas_v2.FORMAS) - set(g1.cenas.S))
    if faltam:
        raise SystemExit("formas_v2 cita situações que não existem: %s" % faltam)
    # Formas de treino: as da v1 (sem as duas reservadas) + as compostas de treino.
    formas_treino = {}
    for nome, c in g1.cenas.S.items():
        us = c["u"]
        corte = max(1, len(us) - 2) if len(us) >= 4 else len(us)
        formas_treino[nome] = us[:corte] + formas_v2.FORMAS.get(nome, {}).get("treino", [])
    formas_blind = dict(formas_treino)
    for nome in v2_nomes:
        formas_blind[nome] = formas_v2.FORMAS[nome]["blind"]
    dados, recusados = {}, {}
    for split, n in CONVERSAS.items():
        casos = []
        base = "blind" if split == "blind_parafrase" else ("dev" if split == "dev" else "treino")
        for _ in range(n):
            conv = montar(rr, fatos[base], nomes[base], formas_blind if split == "blind_parafrase" else formas_treino,
                          v2_nomes, so_ultimo_v2=split == "blind_parafrase")
            if split == "blind_parafrase":
                conv = conv[-1:] if conv and conv[-1]["situacao"][5:] in v2_nomes else []
            for caso in conv:
                ok, motivo = g1.conferir_alvo(caso)
                if not ok:
                    recusados.setdefault(caso["situacao"], 0)
                    recusados[caso["situacao"]] += 1
                    continue
                casos.append(caso)
        dados[split] = casos
    resumo = {"casos": {k: len(v) for k, v in dados.items()},
              "situacoes_v2": v2_nomes,
              "formas_v2": {"treino": sum(len(formas_v2.FORMAS[n]["treino"]) for n in v2_nomes),
                            "blind": sum(len(formas_v2.FORMAS[n]["blind"]) for n in v2_nomes)},
              "parte_v2_no_treino": round(sum(c["situacao"][5:] in v2_nomes for c in dados["treino"]) / max(1, len(dados["treino"])), 3),
              "falas_distintas_treino": len({c["mensagem"] for c in dados["treino"]}),
              "blind_contraexemplos": sum(bool(c.get("contraexemplo")) for c in dados["blind_parafrase"]),
              "blind_parafrase_por_situacao": {n: sum(c["situacao"] == "cena:" + n for c in dados["blind_parafrase"]) for n in v2_nomes},
              "alvos_recusados": recusados}
    # Nenhuma fala do blind de paráfrases pode aparecer no treino.
    vistas = {c["mensagem"].casefold() for c in dados["treino"]}
    vazadas = [c["mensagem"] for c in dados["blind_parafrase"] if c["mensagem"].casefold() in vistas]
    resumo["blind_parafrase_vazadas"] = len(vazadas)
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    if vazadas:
        print("VAZADAS (exemplos):", vazadas[:10])
    if a.resumo:
        return
    dados["blind_parafrase"] = [c for c in dados["blind_parafrase"] if c["mensagem"].casefold() not in vistas]
    bruto = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
    with gzip.GzipFile(AQUI / "dados_fase5_v2.json.gz", "wb", mtime=0) as f:
        f.write(bruto)
    sha = lambda p: hashlib.sha256((AQUI / p).read_bytes()).hexdigest()
    manifesto = {"seed": SEED, "dados_sha256": hashlib.sha256(bruto).hexdigest(),
                 "arquivo_gz_sha256": sha("dados_fase5_v2.json.gz"), "formato_fase5_sha256": sha("formato_fase5.py"),
                 "formas_v2_sha256": sha("formas_v2.py"), "v1_arquivo_gz_sha256": sha("dados_fase5.json.gz"),
                 **{k: v for k, v in resumo.items()}}
    manifesto["casos"]["blind_parafrase"] = len(dados["blind_parafrase"])
    (AQUI / "manifesto_v2.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    principal()
