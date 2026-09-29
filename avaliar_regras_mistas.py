"""Compara a recuperação histórica com e sem o grafo opcional.

O avaliador rotaciona cada pergunta geral para fora do índice. Por padrão,
essa rotação constrói base temporária sem relacoes.json; esta sonda copia
explicitamente o grafo junto da base temporária para observar o efeito
REAL da integração na produção, sem mudar o avaliador histórico.
Não é teste cego: todos os exemplos são de desenvolvimento.
"""
import json
import shutil
from pathlib import Path

from avaliar_recuperador import avaliar
from crivo import Crivo, PASTA


class CrivoComGrafo(Crivo):
    """Replica relacoes.json para a base temporária usada pelo avaliador."""

    def __init__(self, caminho_base=None, agora=None):
        if caminho_base is not None:
            pasta = Path(caminho_base).parent
            shutil.copyfile(PASTA / "relacoes.json", pasta / "relacoes.json")
        super().__init__(caminho_base=caminho_base, agora=agora)


def diagnosticar():
    base = json.loads((PASTA / "conhecimento.json").read_text(encoding="utf-8"))
    geral = [e for e in base if e["topico"] != "programacao"]
    anterior = avaliar(geral)
    com_grafo = avaliar(geral, CrivoComGrafo)
    campos = ("total", "acertos", "erradas", "abstencoes", "ranking_acertos")
    return {
        "sem_grafo": {k: anterior[k] for k in campos},
        "com_grafo": {k: com_grafo[k] for k in campos},
        "alteracoes": {
            "acertos": com_grafo["acertos"] - anterior["acertos"],
            "erradas": com_grafo["erradas"] - anterior["erradas"],
            "abstencoes": com_grafo["abstencoes"] - anterior["abstencoes"],
        },
        "limite": "Benchmark de desenvolvimento com pergunta removida; a inclusão do grafo pode alterar o ID de respostas semanticamente válidas."
    }


if __name__ == "__main__":
    relatorio = diagnosticar()
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    anterior = relatorio["sem_grafo"]
    novo = relatorio["com_grafo"]
    assert (anterior["total"], anterior["acertos"], anterior["erradas"],
            anterior["abstencoes"]) == (278, 192, 44, 42), (
                "Benchmark histórico sem grafo divergiu")
    assert novo["total"] == 278, "Número de casos alterado"
    if novo["acertos"] < anterior["acertos"] or novo["erradas"] > anterior["erradas"]:
        raise SystemExit("Regressão no desempenho histórico com grafo carregado")
