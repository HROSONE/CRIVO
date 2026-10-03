"""Mede se o CRIVO entende a pergunta sobre um conceito, seja qual for o jeito
de perguntar ("oq é X", "explica X pra mim", "tenho uma dúvida sobre X"...).

Caso de conceito: a resposta precisa trazer a definição cadastrada do conceito.
Controle: a resposta NÃO pode ser uma definição (relato, conversa, lógica).

Uso: python scripts/avaliar_interpretador.py [dev|retido|todos] [--detalhes]
(--detalhes só mostra o dev; o retido fica só no agregado.)
"""
import json
import sys
from collections import Counter
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA))

from linguagem_conversa import normalizar  # noqa: E402


def definicoes(bot):
    """nome normalizado do conceito -> trecho inicial da definição."""
    saida = {}
    for item in bot.compositor.itens.values():
        trecho = normalizar(item["fatos"][0]["texto"])[:40]
        for nome in [item["nome"]] + list(item.get("aliases", [])):
            saida.setdefault(normalizar(nome), trecho)
    return saida


def avaliar(conjunto):
    from crivo import Crivo
    dados = json.loads((PASTA / "avaliacoes" / "interpretador_v1" / (conjunto + ".json")).read_text(encoding="utf-8"))
    referencia = Crivo()
    defs = definicoes(referencia)
    ok, tipos, detalhes = 0, Counter(), []
    for caso in dados["casos"]:
        bot = Crivo()
        ident, resposta = bot.responder(caso["fala"])
        n = normalizar(resposta)
        if caso.get("nao_e_definicao"):
            tipo = "controle"
            passou = not ident.startswith("conhecimento:")
        else:
            tipo = "conceito"
            trecho = defs.get(normalizar(caso["conceito"]))
            passou = bool(trecho) and trecho in n
        ok += passou
        tipos[tipo + (":ok" if passou else ":falha")] += 1
        detalhes.append((caso, ident, resposta, passou))
    return {"conjunto": conjunto, "casos": len(dados["casos"]), "acertos": ok,
            "por_tipo": dict(sorted(tipos.items()))}, detalhes


def main():
    args = sys.argv[1:]
    alvo = next((a for a in args if a in ("dev", "retido", "todos")), "dev")
    for conjunto in (("dev", "retido") if alvo == "todos" else (alvo,)):
        resumo, detalhes = avaliar(conjunto)
        print(json.dumps(resumo, ensure_ascii=False))
        if "--detalhes" in args and conjunto == "dev":
            for caso, ident, resposta, passou in detalhes:
                if not passou:
                    print("  FALHA", caso["fala"], "->", ident, "|", resposta.replace("\n", " ")[:110])


if __name__ == "__main__":
    main()
