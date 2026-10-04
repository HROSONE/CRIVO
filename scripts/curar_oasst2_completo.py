"""Acrescenta mensagens humanas revisadas da exportação completa de OASST2.

IDs/árvores e textos comuns à exportação ready devem coincidir. Nunca concatenar
OASST1 para fingir novos exemplos: ele já está incluído em OASST2.
"""
import collections
import gzip
import json
from scripts.baixar_fontes_linguagem import FONTES
from scripts.curar_dialogos_humanos import ler_mensagens
from scripts.preparar_linguagem_profunda import selecionar_humanos_mensagens, sha

# Revisão pontual de conteúdo: rótulos positivos não garantem uma resposta boa.
# Recusar também descendentes que utilizem a resposta incorreta como histórico.
RECUSAS_CONTEUDO = {
    '2f5ba7af-f89c-4762-adde-37a444265c3a': 'Confunde espalhamento com reflexão/refração ao explicar o céu azul.',
    '16800832-37af-4057-b320-ef0901a1a156': 'Atribui satisfação e felicidade próprias ao assistente.',
    'a7646963-8232-4d7f-8883-d026d04bc4c7': 'Supõe telefone e rádio num cenário que proíbe toda tecnologia.',
    '0d461d19-3a3f-44d4-9d52-fd8fd360fa82': 'Confunde lambda Python e automações de outras plataformas com ESPHome.',
    '03d57bde-93d8-4df7-b8a1-b5cb3c5a2fea': 'Exemplo ESPHome usa variável pin_luz não definida e uma configuração inconsistente.',
    'b37fcfed-55e2-4bc7-b7df-81e4f394353c': 'Confunde Comuna de Paris com liderança da Revolução Francesa e Liga dos Comunistas.',
    '16223fdc-f98e-4b2d-b9b6-54a662bcd507': 'Responde identidades trigonométricas ao pedido de representação em produto.',
    '8fd3872f-a5b3-465f-a375-a533224730d9': 'Afirma aplicação apenas a valores pares e apresenta notação inconsistente.',
    'c98d5c1d-7a86-49d0-9eca-3041a13b6234': 'Confunde ROI com receita menos gasto e toma aumento de vendas como prova causal.',
    '66bc5657-24bc-4af8-b9ff-888623b4d77f': 'Confunde PageRank com conjunto amplo de critérios de ranking.',
    '12ea58ef-a9dd-4e09-9f9f-f7ff51637eac': 'Confunde single e double precision como formatos de números duplos.',
    'ea8bb156-e263-4be0-8027-b4b8842d5ec4': 'Exemplo binário truncado não demonstra o resultado IEEE 754 alegado.',
    'fbaf3ffb-69e9-4e7f-b315-481456087a8f': 'Atribui ao arredondamento da soma decimal exata o resultado da soma de operandos já aproximados.',
    'd71e6d84-5ea1-4630-9882-82f71087bb22': 'Receita não especifica quantidades e contém erros de escrita.',
    '329e6242-e891-420e-a288-3e3d3d9420ff': 'Receita inconsistente de banana com quiabo e escrita incoerente.',
    'debf1735-f8bb-49cf-a432-5fc1baee8d38': 'Texto não constitui receita executável de bolo.',
    '74ba5414-54fa-4349-8039-7d80dea691d9': 'Conserva receita sem quantidades e instruções incoerentes.',
    'b4e93c0d-0f69-490a-804d-2c7dfbe49a0d': 'Orçamento contradiz baixo custo e generaliza requisito de passaporte sem escopo.',
}


def selecionar_completo(ready, completo):
    fonte = FONTES['oasst2_completo']
    if sha(completo) != fonte['sha256']:
        raise ValueError('OASST2 completo difere da revisão pública fixada')
    base = ler_mensagens(ready)
    indice = {m['message_id']: m for m in base}
    with gzip.open(completo, 'rt', encoding='utf-8') as f:
        for linha in f:
            m = json.loads(linha)
            if m.get('lang') != 'pt-BR':
                continue
            ident = m['message_id']
            if ident in indice and indice[ident] != m:
                raise ValueError('Mensagem comum conflita entre ready e completo')
            indice[ident] = m
    base_ids = {m['message_id'] for m in base}
    mensagens = list(indice.values())
    exemplos, recusas = selecionar_humanos_mensagens(mensagens)
    limpos = []
    adicionais = collections.Counter()
    for e in exemplos:
        atual = indice[e['source_id']]
        cadeia = []
        while atual:
            cadeia.append(atual['message_id'])
            atual = indice.get(atual.get('parent_id'))
        if any(i in RECUSAS_CONTEUDO for i in cadeia):
            adicionais['erro_conteudo_revisado_v2'] += 1
            continue
        e['fonte_exportacao'] = 'ready' if e['source_id'] in base_ids else 'completa'
        limpos.append(e)
    recusas.update(adicionais)
    return limpos, dict(recusas)
