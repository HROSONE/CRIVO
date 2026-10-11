"""Reaproveita a estrutura congelada, mas torna cada pergunta textual inédita.

Nao altera operacoes, contextos, preenchimentos, respostas ou criterios. Apenas
prefixa as formulacoes da prova para eliminar coincidencias literais com
holdouts anteriores antes de qualquer treinador existir.
"""
from __future__ import annotations

import preparar_holdout as base

for operacao, frases in list(base.MENSAGENS.items()):
    base.MENSAGENS[operacao] = [f"Nesta prova de contexto novo, {frase}" for frase in frases]

if __name__ == "__main__":
    base.main()
