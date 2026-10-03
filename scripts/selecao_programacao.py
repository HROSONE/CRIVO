"""Prioridade de avaliação reservada para escolher checkpoints, sem tocar no teste."""

def pontuacao_validacao(registro, fase, funcional=False):
    ce = registro['avaliacao'][fase]['entropia_cruzada']
    if not funcional: return (-ce,)
    m = registro['funcional']['linguagens']
    # Primeiro código correto, depois sintaxe e término; CE apenas desempata.
    # Usar somente a primeira tentativa, sem soluções recuperadas ou teste final.
    return (sum(x['corretas'] for x in m.values()),
            sum(x['compilam'] for x in m.values()),
            sum(x['completas'] for x in m.values()), -ce)
