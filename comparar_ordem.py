"""Compara representações em dobras idênticas, sem alterar o código de produção.

A mesma lista de treino/teste e a mesma semente são usadas nos dois modos.
As regras de normalização já foram desenvolvidas no corpus: não é teste externo.
"""
import argparse
import json
from pathlib import Path

import rede_neural
from experimento_ordem import caracteristicas_com_ordem


def comparar(base, epocas=30, ocultos=24, dimensao=512, semente=42, peso_ordem=0.15):
    rotulos = [e["id"] for e in base]
    n_dobras = max(len(e["perguntas"]) for e in base)
    original = rede_neural.caracteristicas
    resultados = []
    try:
        for dobra in range(n_dobras):
            treino, teste = [], []
            for entrada in base:
                perguntas = entrada["perguntas"]
                if len(perguntas) < 2:
                    continue
                treino.extend((p, entrada["id"]) for i, p in enumerate(perguntas)
                              if i != dobra)
                if dobra < len(perguntas):
                    teste.append((perguntas[dobra], entrada["id"]))
            linha = {"dobra": dobra + 1, "total": len(teste)}
            for nome in ("portugues_sem_filtro", "portugues_ordem"):
                if nome == "portugues_ordem":
                    def com_ordem(texto, dimensao=256, modo="caracteres"):
                        return caracteristicas_com_ordem(texto, dimensao, peso_ordem)
                    rede_neural.caracteristicas = com_ordem
                    modo = "portugues_sem_filtro"
                else:
                    rede_neural.caracteristicas = original
                    modo = "portugues_sem_filtro"
                rede = rede_neural.RedeCrivo(
                    rotulos, dimensao=dimensao, ocultos=ocultos,
                    semente=semente, modo=modo)
                rede.treinar(treino, epocas=epocas, semente=semente)
                linha[nome] = sum(rede.prever(p)[0] == esperado
                                  for p, esperado in teste)
            resultados.append(linha)
    finally:
        rede_neural.caracteristicas = original
    total = sum(r["total"] for r in resultados)
    return {
        "epocas": epocas, "ocultos": ocultos, "dimensao": dimensao,
        "peso_ordem": peso_ordem,
        "total": total,
        "acertos_sem_filtro": sum(r["portugues_sem_filtro"] for r in resultados),
        "acertos_com_ordem": sum(r["portugues_ordem"] for r in resultados),
        "dobras": resultados,
        "aviso": "A normalizacao foi desenvolvida no mesmo corpus; resultado nao e teste externo."
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base", default=str(Path(__file__).with_name("conhecimento.json")))
    p.add_argument("--epocas", type=int, default=30)
    p.add_argument("--ocultos", type=int, default=24)
    p.add_argument("--dimensao", type=int, default=512)
    p.add_argument("--peso-ordem", type=float, default=0.15)
    a = p.parse_args()
    dados = json.loads(Path(a.base).read_text(encoding="utf-8"))
    print(json.dumps(comparar(dados, a.epocas, a.ocultos, a.dimensao, peso_ordem=a.peso_ordem),
                     ensure_ascii=False, indent=2))
