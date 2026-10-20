"""Falas do v7 (20/10/2026): as do v6c mais os grupos A–E, para as 108 situações elegíveis.

Autoria: assistente de programação (Claude), com autorização do criador. NÃO são falas humanas.
O que entra no treino é decidido por gerar_v7.py, depois de três filtros: conflito com o treino antigo, parecença com os
testes congelados (cosseno ≥ 0,7) e o detector de gatilhos (detector_gatilhos.py).
"""
from formas_v6c import FORMAS as _V6C, DEPOIS_DE_PERGUNTA  # noqa: F401
import formas_v7_a, formas_v7_b, formas_v7_c, formas_v7_d, formas_v7_e


def montar():
    out = {s: list(v) for s, v in _V6C.items()}
    for mod in (formas_v7_a, formas_v7_b, formas_v7_c, formas_v7_d, formas_v7_e):
        for s, falas in mod.F.items():
            out.setdefault(s, [])
            out[s] += [u for u in falas if u not in out[s]]
    return out


FORMAS = montar()
