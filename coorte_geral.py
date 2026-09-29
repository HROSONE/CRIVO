"""Coorte fixa de 278 perguntas gerais da base v0.4.

O arquivo coorte_geral_v04.json congela a população avaliada antes de
ampliar o currículo. Isso torna possível comparar números históricos sem
apagar novas perguntas. A coorte permanece desenvolvimento, não teste cego.
"""
import json
from pathlib import Path

from crivo import PASTA


def selecionar_coorte(entradas):
    especificacao = json.loads(
        (PASTA / "coorte_geral_v04.json").read_text(encoding="utf-8"))
    disponiveis = {e["id"]: e for e in entradas}
    coorte = []
    for registro in especificacao["entradas"]:
        ident = registro["id"]
        if ident not in disponiveis:
            raise ValueError("Assunto histórico ausente da base: " + ident)
        atual = disponiveis[ident]
        perguntas = registro["perguntas"]
        if not perguntas or not isinstance(perguntas, list):
            raise ValueError("Coorte histórica inválida")
        coorte.append(dict(atual, perguntas=list(perguntas)))
    total = sum(len(e["perguntas"]) for e in coorte)
    if total != 278:
        raise ValueError("A coorte geral histórica deve conservar 278 perguntas")
    return coorte


if __name__ == "__main__":
    atuais = json.loads((PASTA / "conhecimento.json").read_text(encoding="utf-8"))
    print("Coorte antiga:", len(selecionar_coorte(atuais)), "entradas / 278 perguntas")
