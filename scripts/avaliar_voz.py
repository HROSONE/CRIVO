"""Mede a voz no teste congelado avaliacoes/voz_v1/teste.json.

Para cada pergunta, compara a resposta do CRIVO com a do tutor:
  proximidade        chrF (n-gramas de 1 a 6 letras, beta 2), de 0 a 100;
  fidelidade         nenhuma palavra de conteúdo fora dos fatos dos assuntos,
                     da pergunta e do vocabulário de conversa (voz.DISCURSO);
  marcas_mecanicas   “Além disso,” e “estes são os fatos disponíveis”.

Uso: python scripts/avaliar_voz.py [--detalhes] [--sem-voz]
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

MARCAS = (r"\balém disso,", r"estes são os fatos disponíveis")


def _ngramas(texto, n):
    t = re.sub(r"\s+", " ", texto.strip())
    return Counter(t[i:i + n] for i in range(len(t) - n + 1))


def chrf(hipotese, referencia, ordem=6, beta=2.0):
    precisoes, revocacoes = [], []
    for n in range(1, ordem + 1):
        h, r = _ngramas(hipotese, n), _ngramas(referencia, n)
        comum = sum((h & r).values())
        if sum(h.values()):
            precisoes.append(comum / sum(h.values()))
        if sum(r.values()):
            revocacoes.append(comum / sum(r.values()))
    p = sum(precisoes) / len(precisoes) if precisoes else 0.0
    r = sum(revocacoes) / len(revocacoes) if revocacoes else 0.0
    if p + r == 0:
        return 0.0
    return 100 * (1 + beta ** 2) * p * r / (beta ** 2 * p + r)


def fontes_do_caso(bot, caso):
    from curriculo_mundo import texto_fato
    itens = bot.compositor.itens
    fontes = [caso["pergunta"]]
    for a in caso["assuntos"]:
        fontes += [texto_fato(f) for f in itens[a]["fatos"]] + [itens[a]["nome"]] + itens[a].get("aliases", [])
    return fontes


def avaliar(crivo_factory, teste=None):
    from voz import palavras_inventadas
    teste = teste or json.loads((RAIZ / "avaliacoes/voz_v1/teste.json").read_text(encoding="utf-8"))
    linhas = []
    for caso in teste["casos"]:
        bot = crivo_factory()
        _, resposta = bot.responder(caso["pergunta"])
        inventadas = palavras_inventadas(resposta, fontes_do_caso(bot, caso))
        marcas = sum(len(re.findall(m, resposta, re.I)) for m in MARCAS)
        linhas.append({"pergunta": caso["pergunta"], "resposta": resposta,
                       "chrf": round(chrf(resposta, caso["tutor"]), 2),
                       "inventadas": inventadas, "marcas": marcas})
    n = len(linhas)
    resumo = {
        "casos": n,
        "chrf_medio": round(sum(l["chrf"] for l in linhas) / n, 2),
        "fieis": sum(not l["inventadas"] for l in linhas),
        "marcas_mecanicas": sum(l["marcas"] for l in linhas),
    }
    return {"resumo": resumo, "casos": linhas}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detalhes", action="store_true")
    parser.add_argument("--sem-voz", action="store_true", help="mede o texto de antes da voz")
    args = parser.parse_args()
    from crivo import Crivo

    def fabrica():
        bot = Crivo()
        if args.sem_voz:
            bot.usar_voz = False
        return bot
    r = avaliar(fabrica)
    if args.detalhes:
        for l in r["casos"]:
            print("%6.1f %s %s" % (l["chrf"], "FIEL " if not l["inventadas"] else "INV%s" % l["inventadas"],
                                   l["pergunta"]))
            print("       " + l["resposta"].replace("\n", " / ")[:300])
    print(json.dumps(r["resumo"], ensure_ascii=False))


if __name__ == "__main__":
    main()
