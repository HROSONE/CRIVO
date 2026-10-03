"""Carregar somente o pequeno modelo próprio publicado com procedência fixa."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

PASTA = Path(__file__).resolve().parent/'artefatos/efeitos_programacao'


@lru_cache(maxsize=4)
def carregar_modelo(pasta=str(PASTA)):
    # Cache de pesos fixos do projeto, nunca de conversas ou código do usuário.
    p = Path(pasta)
    try:
        origem = json.loads((p/'proveniencia.json').read_text())
        if origem.get('pesos_externos') is not False or origem.get('parametros') != 1679:
            raise ValueError('Procedência incompatível')
        sha = hashlib.sha256((p/'rede.npz').read_bytes()).hexdigest()
        if sha != origem['pesos_sha256']:
            raise ValueError('Pesos não correspondem à procedência')
        from rede_precisa import RedePrecisa
        return RedePrecisa.carregar(p), origem
    except (ImportError, OSError, ValueError, KeyError):
        return None, None


def status_modelo(pasta=str(PASTA)):
    rede, origem = carregar_modelo(str(pasta))
    return dict(active=rede is not None, parameters=1679 if rede is not None else 0,
                external_weights=False, sha256=origem['pesos_sha256'] if origem else None)


def conferir_efeitos(analises, pasta=str(PASTA)):
    rede, origem = carregar_modelo(str(pasta))
    r = dict(ativo=rede is not None, parametros=1679 if rede is not None else 0,
             comparados=0, concordantes=0, fora_dominio=0, primeira_divergencia=None)
    if rede is None:
        return r
    r['pesos_sha256'] = origem['pesos_sha256']
    # Até 128 efeitos efetivamente executados. Sem consulta a exemplos reservados.
    for analise in analises:
        for efeito in analise.get('tracos', []):
            if efeito['tipo'] != 'efeito' or 'resultado' not in efeito:
                continue
            if r['comparados'] + r['fora_dominio'] >= 128:
                return r
            try:
                previsto = rede.prever(efeito['op'], efeito['a'], efeito.get('b', 0))
            except ValueError:
                r['fora_dominio'] += 1
                continue
            from verificacao_codigo import iguais
            certo = iguais(previsto, efeito['resultado'])
            r['comparados'] += 1
            r['concordantes'] += certo
            if not certo and r['primeira_divergencia'] is None:
                r['primeira_divergencia'] = dict(op=efeito['op'], previsto=previsto, exato=efeito['resultado'])
    return r
