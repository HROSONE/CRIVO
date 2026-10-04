"""Prioridade de avaliação reservada para escolher checkpoints, sem tocar no teste."""

def pontuacao_validacao(registro, fase, funcional=False, humanos=False):
    if humanos and (funcional or fase != 'dialogo'):
        raise ValueError('Seleção humana é exclusiva da validação de diálogo')
    medida = registro['avaliacao']['dialogo_humano' if humanos else fase]
    if humanos and (medida['particao'] != 'validacao' or medida['tokens_avaliados'] <= 0):
        raise ValueError('Seleção humana exige alvos da validação, nunca do teste')
    ce = medida['entropia_cruzada']
    if not funcional: return (-ce,)
    m = registro['funcional']['linguagens']
    # Primeiro código correto, depois sintaxe e término; CE apenas desempata.
    # Usar somente a primeira tentativa, sem soluções recuperadas ou teste final.
    return (sum(x['corretas'] for x in m.values()),
            sum(x.get('taxa_acerto_casos_por_tarefa',0.) for x in m.values()),
            sum(x['compilam'] for x in m.values()),
            sum(x['completas'] for x in m.values()), -ce)
