"""Ablação curta: mesmo corpus e pesos, matriz compartilhada fixa ou ajustável."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / 'resposta_relacional_20261009'
sys.path.insert(0, str(SHARED))
import piloto_duravel as piloto
from curriculo import sha


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('condicao', choices=['ajustavel', 'congelado'])
    a = p.parse_args()
    proto = json.loads((HERE / 'protocolo.json').read_text())
    assert sha(__file__) == proto['codigo_wrapper_sha256']
    assert sha(SHARED / 'piloto_duravel.py') == proto['treinador_sha256']
    carregar_original = piloto.carregar
    def carregar_base(*args, **kwargs):
        m, tok, meta = carregar_original(*args, **kwargs)
        if a.condicao == 'congelado':
            m.embedding.weight.requires_grad_(False)
        assert sha(Path(args[0]) / 'pesos.pt') == proto['base_sha256']
        return m, tok, meta
    piloto.carregar = carregar_base
    piloto.HERE = HERE / a.condicao
    a.braco = 'relacional'
    a.base = SHARED.parents[1] / 'artefatos/linguagem_profunda'
    a.antigo = Path('/workspace/experimentos/crivo-geracao-dialogo-20261008/dados')
    a.tokens = 30000
    a.max_segundos = 600
    piloto.treino(a)
