"""Modelo operacional limitado de investigação de heap JavaScript em Node.

Não executa GC, mede processos, identifica objetos retidos ou prova vazamentos.
O modelo é uma simplificação editorial com fontes; tendências são entradas do
chamador. RSS, external e arrayBuffers exigem investigações distintas.
"""
from workspace_cognitivo import Hipotese, Pergunta, Investigador

FONTES = (
    'https://nodejs.org/api/process.html#processmemoryusage',
    'https://nodejs.org/en/learn/diagnostics/memory/using-gc-traces',
    'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Memory_management',
)


def criar_investigacao():
    return Investigador([
        Hipotese('retencao', 'Objetos retidos sem utilidade; requer caminhos de retenção e análise da intenção.',
                 (('pos_gc', ('cresce',)),)),
        Hipotese('cache', 'Cache sem limite contribuindo para o crescimento do heap.',
                 (('pos_gc', ('cresce',)), ('cache', ('cresce',)))),
        Hipotese('fila', 'Pedidos pendentes acumulados contribuindo para o crescimento do heap.',
                 (('pos_gc', ('cresce',)), ('fila', ('cresce',)))),
        Hipotese('transitorio', 'Oscilação transitória compatível com alocação e coleta.',
                 (('pos_gc', ('estavel',)),)),
    ], [
        Pergunta('runtime', 'Esse programa usa Node.js ou outro ambiente?', ('node', 'outro')),
        Pergunta('metrica', 'Você está medindo o heap do JavaScript ou a memória total do processo (RSS)?', ('heap', 'rss')),
        Pergunta('pos_gc', 'Sob carga comparável, o heap após ciclos de coleta continua crescendo ou volta a uma base estável?', ('cresce', 'estavel'), 2.),
        Pergunta('cache', 'A quantidade ou o tamanho dos itens no cache também cresce?', ('cresce', 'estavel')),
        Pergunta('fila', 'A quantidade de pedidos pendentes cresce porque entram mais pedidos do que o programa processa?', ('cresce', 'estavel')),
    ], dominio=(('runtime', 'node'), ('metrica', 'heap')))


def explicar(resultado):
    acao = resultado['acao']
    if acao in ('esclarecer', 'perguntar'):
        return resultado['pergunta']
    if acao == 'fora_de_escopo':
        return ('Este modelo cobre apenas heap JavaScript em Node. RSS pode incluir outras áreas de memória; '
                'seu crescimento não prova um vazamento no heap. Precisamos escolher métricas e um modelo adequados ao ambiente.')
    if acao == 'rever_modelo':
        return ('As observações não se encaixam nas hipóteses deste modelo. Precisamos verificar as medições, '
                'a comparabilidade da carga e considerar outras explicações.')
    return ('As observações disponíveis não distinguem mais as hipóteses deste modelo. '
            'Para investigar retenção, compare snapshots e caminhos de referência sob carga comparável. '
            'Compatibilidade não comprova um vazamento; cache e filas também podem coexistir.')
