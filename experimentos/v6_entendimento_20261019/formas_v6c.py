"""Falas do v6c: as do v6b (formas_v6b.py) sem os gatilhos que o diagnóstico do v6b achou (20/10/2026).

Autoria: assistente de programação (Claude), com autorização do criador. NÃO são falas humanas.

Diagnóstico (RESULTADO_V6B_RODADA1.md): frases que a v4 acertava e o v6b errou, comparadas com as falas de treino:
- "tô sangrando muito" (urgência) ← "tô muito apaixonada" (amor_bom);
- "isso não responde nada" (nao_era_isso) ← "não comi nada hoje" (fome);
- "é a ia do crivo?" (confirma_crivo) ← "hello crivo" (oi);
- "tô com dificuldade pra decidir" (conselho) ← "tô com dificuldade em química" (escola_dificil);
- "no que você é bom?" (o_que_faz) ← "você é vivo?" (consciencia).
A outra causa (situações sem casos novos perdendo peso) é corrigida no notebook, por substituição.
"""
from formas_v6b import FORMAS as _V6B, DEPOIS_DE_PERGUNTA  # noqa: F401

REMOVER = {
    "amor_bom": ["tô muito apaixonada"],
    "fome": ["não comi nada hoje"],
    "oi": ["hello crivo"],
    "escola_dificil": ["tô com dificuldade em química"],
    "consciencia": ["você é vivo?"],
}


def montar():
    out = {}
    for sit, falas in _V6B.items():
        tirar = set(REMOVER.get(sit, []))
        assert tirar <= set(falas), (sit, tirar - set(falas))
        out[sit] = [u for u in falas if u not in tirar]
    return out


FORMAS = montar()
