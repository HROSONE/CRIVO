"""Mede perguntas que supõem: a resposta à última fala de cada caso não pode
trazer a pergunta proibida e precisa perguntar algo; nos controles (relato de
algo que aconteceu) a pergunta específica continua.

Uso: python scripts/avaliar_suposicao.py [dev|retido|todos] [--detalhes]
(--detalhes só mostra o dev)
"""
import json
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA))


def avaliar(conjunto):
    from crivo import Crivo
    dados = json.loads((PASTA / "avaliacoes" / "suposicao_v1" / (conjunto + ".json")).read_text(encoding="utf-8"))
    ok, falhas, por_tipo = 0, [], {}
    for caso in dados["casos"]:
        bot = Crivo()
        bot.conversacao.sorteio.seed(20261003)
        resposta = ""
        for fala in caso["falas"]:
            _, resposta = bot.responder(fala)
        baixa = resposta.lower()
        passou = "?" in resposta and not any(p.lower() in baixa for p in caso.get("nao_contem", ())) \
            and all(p.lower() in baixa for p in caso.get("contem", ()))
        ok += passou
        t = por_tipo.setdefault(caso["tipo"], [0, 0])
        t[0] += passou
        t[1] += 1
        if not passou:
            falhas.append((caso["falas"], resposta))
    return {"conjunto": conjunto, "casos": len(dados["casos"]), "acertos": ok,
            "por_tipo": {k: "%d/%d" % tuple(v) for k, v in por_tipo.items()}}, falhas


def main():
    args = sys.argv[1:]
    alvo = next((a for a in args if a in ("dev", "retido", "todos")), "dev")
    for conjunto in (("dev", "retido") if alvo == "todos" else (alvo,)):
        resumo, falhas = avaliar(conjunto)
        print(json.dumps(resumo, ensure_ascii=False))
        if "--detalhes" in args and conjunto == "dev":
            for falas, resposta in falhas:
                print("  %s -> %s" % (" | ".join(falas), resposta[:200]))


if __name__ == "__main__":
    main()
