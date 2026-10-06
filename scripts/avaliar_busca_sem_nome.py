"""Mede o CRIVO em perguntas que não citam o nome do assunto.

Uso: python scripts/avaliar_busca_sem_nome.py [dev|teste|todos] [--detalhes]

Conjuntos em avaliacoes/busca_sem_nome_v1: dev (pode ser olhado caso a caso)
e teste (congelado: só agregados, nunca --detalhes). Cada caso traz o fato
que responde (assunto e índice) ou nenhum, quando o acervo não tem a resposta.

Classificação da resposta do CRIVO:
  certo      mostrou o fato esperado (afirmando ou aproximando);
  errado     respondeu com outro conteúdo;
  recusou    admitiu não saber, embora o acervo tenha a resposta;
  inventou   respondeu a uma pergunta sem resposta no acervo (o erro grave);
  calou_bem  recusou uma pergunta sem resposta no acervo.
E da busca sozinha (assunto oculto): o fato esperado em 1º e entre os 5 primeiros.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))


def avaliar(conjunto, detalhes=False):
    from avaliar_bateria import recusou
    from crivo import Crivo
    from leitura_ficha import busca_aprendida
    casos = json.loads((RAIZ / "avaliacoes" / "busca_sem_nome_v1" / ("%s.json" % conjunto))
                       .read_text(encoding="utf-8"))["casos"]
    r = dict.fromkeys(("certo", "aproximou_certo", "errado", "recusou", "inventou", "calou_bem",
                       "busca_top1", "busca_top5"), 0)
    for caso in casos:
        bot = Crivo()
        ident, resposta = bot.responder(caso["pergunta"])
        negou = recusou(ident, resposta) and ident != "leitura:aproximacao"
        if caso["assunto"] is None:
            classe = "calou_bem" if negou else "inventou"
        else:
            alvo = (caso["assunto"], caso["fato"])
            fato = bot.compositor.itens[alvo[0]]["fatos"][alvo[1]]["texto"]
            ctx = bot.contexto_textual
            mostrou = (ctx is not None and alvo in tuple(ctx.exibidos)) or fato in resposta
            classe = "recusou" if negou else "certo" if mostrou else "errado"
            if classe == "certo" and ident == "leitura:aproximacao":
                r["aproximou_certo"] += 1
            achados = [(a, i) for _, a, i in busca_aprendida(bot.compositor).buscar(caso["pergunta"], k=5)]
            r["busca_top1"] += achados[:1] == [alvo]
            r["busca_top5"] += alvo in achados
        r[classe] += 1
        if detalhes:
            print("%-9s %-24s %s\n          %s" % (classe, ident, caso["pergunta"], resposta[:150].replace("\n", " ")))
    com = sum(1 for c in casos if c["assunto"])
    return dict({"conjunto": conjunto, "com_resposta": com, "sem_resposta": len(casos) - com}, **r)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    alvo = args[0] if args else "dev"
    detalhes = "--detalhes" in sys.argv
    for conjunto in (("dev", "teste") if alvo == "todos" else (alvo,)):
        if conjunto == "teste" and detalhes:
            raise SystemExit("O teste congelado só é medido em agregados.")
        print(json.dumps(avaliar(conjunto, detalhes), ensure_ascii=False))


if __name__ == "__main__":
    main()
