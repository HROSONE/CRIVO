"""Definições treino-only da Escola Cognitiva do CRIVO.

A escola não participa da inferência. Ela descreve professores auxiliares que
supervisionam dimensões internas durante o treino e são descartados antes do
checkpoint final.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Professor:
    nome: str
    classes: tuple[str, ...]
    peso: float

    @property
    def ids(self) -> dict[str, int]:
        return {rotulo: i for i, rotulo in enumerate(self.classes)}


PROFESSORES = {
    "acao": Professor(
        nome="acao",
        classes=("recordar", "corrigir", "avaliar", "escrever", "perguntar"),
        peso=0.125,
    ),
    "foco": Professor(
        nome="foco",
        classes=("pessoa", "objeto", "estado", "atividade", "detalhe"),
        peso=0.125,
    ),
}

# A operação observável continua sendo a mesma do corpus. O que muda é que a
# supervisão deixa de tratá-la como uma classe monolítica e a decompõe em duas
# dimensões reutilizáveis.
MAPA_OPERACOES = {
    "recordar_pessoa": {"acao": "recordar", "foco": "pessoa"},
    "recordar_objeto": {"acao": "recordar", "foco": "objeto"},
    "corrigir_pessoa": {"acao": "corrigir", "foco": "pessoa"},
    "guardar_hipotese": {"acao": "avaliar", "foco": "estado"},
    "mensagem_sem_horario": {"acao": "escrever", "foco": "atividade"},
    "pedir_detalhe": {"acao": "perguntar", "foco": "detalhe"},
}


def rotulos_da_operacao(operacao: str) -> dict[str, str]:
    try:
        return dict(MAPA_OPERACOES[operacao])
    except KeyError as exc:
        raise ValueError(f"Operação sem professores definidos: {operacao}") from exc


def ids_da_operacao(operacao: str) -> dict[str, int]:
    rotulos = rotulos_da_operacao(operacao)
    return {nome: PROFESSORES[nome].ids[rotulo] for nome, rotulo in rotulos.items()}


def validar_escola() -> None:
    if abs(sum(p.peso for p in PROFESSORES.values()) - 0.25) > 1e-12:
        raise ValueError("Peso auxiliar total deve permanecer 0,25 nesta ablação")
    for operacao, rotulos in MAPA_OPERACOES.items():
        if set(rotulos) != set(PROFESSORES):
            raise ValueError(f"Dimensões incompletas em {operacao}")
        for nome, rotulo in rotulos.items():
            if rotulo not in PROFESSORES[nome].ids:
                raise ValueError(f"Rótulo inválido {nome}={rotulo} em {operacao}")


validar_escola()
