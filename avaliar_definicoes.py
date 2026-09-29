"""Auditoria de intenções definicionais e coorte histórica congelada.

Separar duas populações:
* antiga: 278 perguntas de desenvolvimento fixadas antes da nova definição;
* atual: todas as perguntas gerais cadastradas, inclusive árvore.
Também avalia o grafo realmente carregado, não só o recuperador isolado.
"""
import json

from avaliar_recuperador import avaliar
from avaliar_regras_mistas import CrivoComGrafo
from coorte_geral import selecionar_coorte
from crivo import PASTA


def resumo(dados):
    return {k: dados[k] for k in
            ("total", "acertos", "erradas", "abstencoes", "ranking_acertos")}


def diagnosticar():
    atual = json.loads((PASTA / "conhecimento.json").read_text(encoding="utf-8"))
    historica = selecionar_coorte(atual)
    gerais = [e for e in atual if e["topico"] != "programacao"]
    resultados = {
        "coorte_historica_sem_grafo": resumo(avaliar(historica)),
        "coorte_historica_com_grafo": resumo(avaliar(historica, CrivoComGrafo)),
        "base_atual_sem_grafo": resumo(avaliar(gerais)),
        "base_atual_com_grafo": resumo(avaliar(gerais, CrivoComGrafo)),
        "limite": ("Avaliações de desenvolvimento: as perguntas são retiradas "
                   "do índice em cada dobra, mas as respostas e outras "
                   "paráfrases da intenção continuam disponíveis. "
                   "Mudanças no corpus alteram a população atual.")
    }
    return resultados


if __name__ == "__main__":
    relatorio = diagnosticar()
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    antigo = relatorio["coorte_historica_sem_grafo"]
    anterior_grafo = relatorio["coorte_historica_com_grafo"]
    atual = relatorio["base_atual_sem_grafo"]
    atual_grafo = relatorio["base_atual_com_grafo"]
    if (antigo["total"] != 278 or antigo["acertos"] < 192 or
            antigo["erradas"] > 44):
        raise SystemExit("Regressão da coorte histórica sem grafo")
    if (anterior_grafo["total"] != 278 or anterior_grafo["acertos"] < 192 or
            anterior_grafo["erradas"] > 44):
        raise SystemExit("Regressão da coorte histórica com grafo")
    if atual["total"] <= antigo["total"] or atual_grafo["total"] != atual["total"]:
        raise SystemExit("Base atual e coorte congelada inconsistentes")
    if atual_grafo["acertos"] < atual["acertos"]:
        raise SystemExit("Integração do grafo perdeu acertos contra o recuperador")
