"""Teste do teto antes da primeira avaliação, com modelo próprio minúsculo.

Fixture aleatória de 16 dimensões; não é treino de capacidade do Crivo.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

import torch
import piloto_duravel as piloto
from curriculo import ROOT, sha
from linguagem_profunda import LinguagemProfunda, Configuracao


if __name__ == '__main__':
    torch.set_num_threads(1)
    source = Path(__file__).parent
    with tempfile.TemporaryDirectory(prefix='crivo-persistencia-') as pasta:
        p = Path(pasta)
        base = p / 'base'
        base.mkdir()
        shutil.copyfile(ROOT / 'artefatos/linguagem_profunda/tokenizer.json', base / 'tokenizer.json')
        cfg = Configuracao(vocabulario=4096, dimensao=16, camadas=1, cabecas=2, contexto=256)
        torch.manual_seed(17)
        m = LinguagemProfunda(cfg)
        original = {k: v.clone() for k, v in m.state_dict().items()}
        torch.save({'versao': 1, 'modelo': original, 'config': asdict(cfg), 'passo': 0,
                    'execucao': {'tokenizer_sha256': sha(base / 'tokenizer.json')}}, base / 'pesos.pt')
        ex = p / 'experimento'
        ex.mkdir()
        (ex / 'dados').symlink_to(source / 'dados', target_is_directory=True)
        piloto.HERE = ex
        args = argparse.Namespace(base=base, antigo=Path('/workspace/experimentos/crivo-geracao-dialogo-20261008/dados'),
                                  braco='relacional', tokens=1000, max_segundos=1)
        clock_real = piloto.time.monotonic
        chamadas = [0]
        def clock():
            frame = sys._getframe(1)
            if frame.f_code.co_name == 'treino' and frame.f_code.co_filename == piloto.__file__:
                chamadas[0] += 1
                return 0. if chamadas[0] == 1 else .01 if chamadas[0] == 2 else 2.
            return clock_real()
        with patch.object(piloto.time, 'monotonic', clock):
            piloto.treino(args)
        out = ex / 'relacional'
        state = torch.load(out / 'passo_atual.pt', weights_only=True)
        report = json.loads((out / 'relatorio.json').read_text())
        assert state['passo'] == 1 and 0 < state['tokens_alvo'] < 1000
        assert any(not torch.equal(v, original[k]) for k, v in state['modelo'].items())
        assert state['otimizador']['state'] and state['rng_torch'].numel()
        assert report['historico'][-1]['passo'] == 1
        assert report['historico'][-1]['parada_pelo_teto']
        assert report['ultimo_estado_persistido'] and not report['orcamento_completo']
        assert report['modelo_base_preservado'] and not report['aprovado_para_chat']
        print('PASS: teto antes da avaliação preserva atualização, Adam e RNG; fim parcial avaliado; base intacta.')
