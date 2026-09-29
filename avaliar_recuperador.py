"""Avalia o caminho de resposta real, sem treinar ou carregar pesos neurais."""
import argparse
import json
import tempfile
from pathlib import Path

from crivo import Crivo


def avaliar(base, classe=Crivo):
    if not base or any(len(e["perguntas"]) < 2 for e in base):
        raise ValueError("Cada entrada precisa de pelo menos duas perguntas")
    acertos = ranking_acertos = respondidas = total = 0
    erros = []
    with tempfile.TemporaryDirectory() as pasta:
        arquivo = Path(pasta) / "base.json"
        for dobra in range(max(len(e["perguntas"]) for e in base)):
            treino = [dict(e, perguntas=[q for i, q in enumerate(e["perguntas"])
                                        if i != dobra]) for e in base]
            arquivo.write_text(json.dumps(treino, ensure_ascii=False), encoding="utf-8")
            bot = classe(arquivo)
            for e in base:
                if dobra >= len(e["perguntas"]):
                    continue
                pergunta = e["perguntas"][dobra]
                bot.ultimo_assunto = None
                bot.ultimos = []
                bot.historico = []
                rank = bot._ranking(pergunta)
                obtido = bot.responder(pergunta)[0]
                total += 1
                acertos += obtido == e["id"]
                respondidas += obtido not in ("fora", "duvida", "vazio")
                ranking_acertos += bool(rank) and bot.base[rank[0][1]]["id"] == e["id"]
                if obtido != e["id"]:
                    erros.append({"pergunta": pergunta, "esperado": e["id"], "obtido": obtido})
    return {"total": total, "acertos": acertos, "ranking_acertos": ranking_acertos,
            "respondidas": respondidas, "erradas": respondidas - acertos,
            "abstencoes": total - respondidas, "acuracia": round(acertos / total, 4),
            "precisao_respondidas": round(acertos / max(1, respondidas), 4),
            "metodo": "Rotacao por indice, pergunta avaliada removida do indice; respostas mantidas.",
            "limite": "Avaliacao de desenvolvimento, nao teste cego nem comparavel diretamente a rede treinada so com perguntas.",
            "erros": erros}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=str(Path(__file__).with_name("conhecimento.json")))
    args = parser.parse_args()
    base = json.loads(Path(args.base).read_text(encoding="utf-8"))
    print(json.dumps(avaliar(base), ensure_ascii=False, indent=2))
