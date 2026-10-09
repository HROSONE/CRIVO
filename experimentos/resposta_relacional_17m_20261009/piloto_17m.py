"""Triagem curta do mesmo currículo nos pesos maiores próprios já disponíveis.

Reutiliza o treinador congelado; muda inicialização/tokenizer e o orçamento.
Comparar somente os dois braços dentro deste modelo. Sem promoção automática.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / 'resposta_relacional_20261009'
sys.path.insert(0, str(SHARED))
import piloto
from curriculo import sha, salvar
from linguagem_profunda import carregar


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--braco', choices=['controle', 'relacional'], required=True)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--antigo', type=Path, default=Path('/workspace/experimentos/crivo-geracao-dialogo-20261008/dados'))
    a = p.parse_args()
    proto = json.loads((HERE / 'protocolo.json').read_text())
    assert sha(a.base / 'pesos.pt') == proto['base_sha256']
    assert sha(SHARED / 'piloto.py') == proto['treinador_compartilhado_sha256']
    assert sha(__file__) == proto['wrapper_sha256']
    assert sha(SHARED / 'sessoes.json') == proto['sessoes_sha256']
    a.tokens = 30000
    a.max_segundos = 900
    piloto.HERE = HERE
    piloto.treino(a)
