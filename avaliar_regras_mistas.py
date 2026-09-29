"""Avaliação pareada: sem grafo, grafo do PR #10 e grafo novo.

O conjunto é de desenvolvimento, não cego; a rotação retira cada pergunta
do índice e preserva as outras perguntas e respostas da mesma intenção.
O grafo original é reconstruído filtrando somente os dois tipos antigos
do arquivo relacoes.json atual, sem arquivos de redes neurais.
"""
import json
import shutil
from pathlib import Path

from avaliar_recuperador import avaliar
from coorte_geral import selecionar_coorte
from crivo import Crivo, PASTA


class CrivoComGrafo(Crivo):
    """Monta o grafo completo ao lado da base temporária em avaliação."""

    def __init__(self, caminho_base=None, agora=None):
        if caminho_base is not None:
            destino = Path(caminho_base).with_name("relacoes.json")
            shutil.copyfile(PASTA / "relacoes.json", destino)
        super().__init__(caminho_base=caminho_base, agora=agora)


class CrivoComGrafoAnterior(Crivo):
    """Reproduz o grafo de tipo_de/parte_de, sem as relações novas."""

    def __init__(self, caminho_base=None, agora=None):
        if caminho_base is not None:
            destino = Path(caminho_base).with_name("relacoes.json")
            dados = json.loads((PASTA / "relacoes.json").read_text(encoding="utf-8"))
            dados["entidades"] = {
                k: v for k, v in dados["entidades"].items()
                if v.get("tipo") != "caracteristica"
            }
            # Reconstruir o comportamento editorial do grafo da main
            # anterior, que ainda não continha ponteiros fonte_id.
            dados["fatos"] = [{k: v for k, v in f.items() if k != "fonte_id"}
                             for f in dados["fatos"]
                             if f["relacao"] in ("tipo_de", "parte_de")]
            destino.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        super().__init__(caminho_base=caminho_base, agora=agora)


def resumo(resultado):
    campos = ("total", "acertos", "erradas", "abstencoes", "ranking_acertos")
    return {k: resultado[k] for k in campos}


def diferencas(antes, depois):
    antigo = {x["pergunta"]: x for x in antes["erros"]}
    novo = {x["pergunta"]: x for x in depois["erros"]}
    return {
        "perdas": [x for p, x in novo.items() if p not in antigo],
        "ganhos": [x for p, x in antigo.items() if p not in novo],
        "trocas_de_erro": [{"pergunta": p,
                            "antes": antigo[p]["obtido"],
                            "depois": novo[p]["obtido"]}
                           for p in antigo.keys() & novo.keys()
                           if antigo[p]["obtido"] != novo[p]["obtido"]]
    }


def diagnosticar():
    base = json.loads((PASTA / "conhecimento.json").read_text(encoding="utf-8"))
    geral = selecionar_coorte(base)
    sem = avaliar(geral)
    antigo = avaliar(geral, CrivoComGrafoAnterior)
    novo = avaliar(geral, CrivoComGrafo)
    return {
        "sem_grafo": resumo(sem),
        "grafo_anterior": resumo(antigo),
        "grafo_novo": resumo(novo),
        "comparacao_com_sem_grafo": diferencas(sem, novo),
        "comparacao_com_grafo_anterior": diferencas(antigo, novo),
        "limite": "Taxonomia de intenções não é equivalente à verdade de uma resposta lógica. Comparar IDs de logica:* com IDs de assuntos exige cautela."
    }


if __name__ == "__main__":
    relatorio = diagnosticar()
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    sem = relatorio["sem_grafo"]
    antigo = relatorio["grafo_anterior"]
    novo = relatorio["grafo_novo"]
    assert (sem["total"], sem["acertos"], sem["erradas"],
            sem["abstencoes"]) == (278, 192, 44, 42), (
                "Benchmark histórico sem grafo divergiu")
    assert antigo["total"] == novo["total"] == 278
    if novo["acertos"] < antigo["acertos"] or novo["erradas"] > antigo["erradas"]:
        raise SystemExit("Regressão frente ao grafo anterior da main")
