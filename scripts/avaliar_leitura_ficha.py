"""Mede o CRIVO inteiro em perguntas sobre fichas: a resposta está na ficha?

Para cada pergunta, roda um Crivo novo e classifica a resposta final:

  respondíveis (a ficha tem o fato):
    afirmou_certo     o fato certo, sem ressalva;
    aproximou_certo   "não tenho a resposta exata" + o fato certo;
    afirmou_errado    afirmou outro conteúdo (o erro grave);
    recusou           disse que não sabe (ou aproximou com outro fato).
  sem resposta na ficha:
    recusou           não afirmou nada (o certo);
    aproximou         disse que não tem a resposta exata e mostrou um fato;
    afirmou           afirmou um fato como se respondesse (o erro grave).

Uso: python scripts/avaliar_leitura_ficha.py [teste|teste_v2|tutor] [--sem-leitura] [--saida arquivo.json]
"""
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

CONJUNTOS = {"teste": RAIZ / "avaliacoes" / "leitura_ficha_v1" / "teste.json",
             "teste_v2": RAIZ / "avaliacoes" / "leitura_ficha_v2" / "teste.json",
             "tutor": RAIZ / "dados" / "leitura_ficha_tutor.json"}


def _n(t):
    from composicao_textual import normalizar
    return " ".join(normalizar(t).split())


def classificar(bot, caso, ident, resposta):
    from estado_interno import recusou
    r = _n(resposta)
    aproximou = ident == "leitura:aproximacao"
    if caso["fato"] is None:
        from avaliar_bateria import de_ficha_posterior
        if aproximou or recusou(ident, resposta):
            return "aproximou" if aproximou else "recusou"
        return "ficha_posterior" if de_ficha_posterior(bot) else "afirmou"
    alvo = _n(bot.compositor.itens[caso["assunto"]]["fatos"][caso["fato"]]["texto"])[:80]
    if alvo in r:
        return "aproximou_certo" if aproximou else "afirmou_certo"
    if aproximou or recusou(ident, resposta):
        return "recusou"
    return "afirmou_errado"


def avaliar(conjunto="teste", usar_leitura=True):
    from crivo import Crivo
    casos = json.loads(CONJUNTOS[conjunto].read_text(encoding="utf-8"))["casos"]
    resp, nulos, linhas = Counter(), Counter(), []
    for caso in casos:
        bot = Crivo()
        bot.usar_leitura_ficha = usar_leitura
        ident, resposta = bot.responder(caso["pergunta"])
        classe = classificar(bot, caso, ident, resposta)
        (nulos if caso["fato"] is None else resp)[classe] += 1
        linhas.append({"pergunta": caso["pergunta"], "classe": classe, "id": ident})
    return {"conjunto": conjunto, "leitura": usar_leitura, "casos": len(casos),
            "respondiveis": dict(resp), "sem_resposta": dict(nulos)}, linhas


def main():
    args = sys.argv[1:]
    conjunto = next((a for a in args if a in CONJUNTOS), "teste")
    resumo, linhas = avaliar(conjunto, usar_leitura="--sem-leitura" not in args)
    print(json.dumps(resumo, ensure_ascii=False))
    if "--saida" in args:
        Path(args[args.index("--saida") + 1]).write_text(
            json.dumps({"resumo": resumo, "linhas": linhas}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
