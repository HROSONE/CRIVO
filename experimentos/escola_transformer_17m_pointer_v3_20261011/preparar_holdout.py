#!/usr/bin/env python3
"""Holdout prospectivo V3: binding/apontamento para o Transformer 17M.

Este arquivo não importa o treinador. Os 120 casos e sua ordem são
inteiramente determinados por constantes abaixo e pela semente fixa.
"""
from __future__ import annotations
import json, random

SEMENTE = 20261011151
OPERACOES = (
    'recordar_pessoa','recordar_objeto','corrigir_pessoa',
    'guardar_hipotese','mensagem_sem_horario','pedir_detalhe',
)
FAMILIAS = (
    ('planetário',
     ('Qira-811','Qira-824','Qira-837','Qira-850'),
     ('astrolábio de bancada','fotômetro portátil','espectroscópio manual','relógio sideral'),
     ('calibração celeste','revisão de efemérides','medição fotométrica','alinhamento de cúpula')),
    ('herbário',
     ('Vesna-913','Vesna-926','Vesna-939','Vesna-952'),
     ('prensa botânica','lupa entomológica','paquímetro foliar','frasco de exsicata'),
     ('catalogação botânica','triagem de sementes','medição foliar','montagem de exsicatas')),
    ('sala acústica',
     ('Tarek-1021','Tarek-1034','Tarek-1047','Tarek-1060'),
     ('decibelímetro','diapasão cromático','microfone de referência','gerador de ruído rosa'),
     ('calibração acústica','medição de reverberação','ensaio de isolamento','mapeamento de ruído')),
    ('estação de campo',
     ('Lume-1113','Lume-1126','Lume-1139','Lume-1152'),
     ('anemômetro sônico','pluviômetro basculante','sonda de umidade','termopar blindado'),
     ('levantamento microclimático','coleta meteorológica','checagem de sensores','registro de precipitação')),
    ('oficina óptica',
     ('Neris-1215','Neris-1228','Neris-1241','Neris-1254'),
     ('colimador laser','retículo de teste','lente acromática','banco óptico curto'),
     ('alinhamento óptico','ensaio de aberração','limpeza de lentes','medição de foco')),
)
ORDENS = (
    OPERACOES,
    ('recordar_objeto','pedir_detalhe','guardar_hipotese','corrigir_pessoa','recordar_pessoa','mensagem_sem_horario'),
    ('guardar_hipotese','recordar_pessoa','mensagem_sem_horario','recordar_objeto','corrigir_pessoa','pedir_detalhe'),
    ('pedir_detalhe','mensagem_sem_horario','recordar_objeto','corrigir_pessoa','guardar_hipotese','recordar_pessoa'),
)
PERGUNTAS = {
 'recordar_pessoa':(
  'Recupere apenas quem está valendo como pessoa neste caso do {familia}.',
  'Qual participante deve ser considerado agora no {familia}?',
  'Quem ficou como referência humana vigente no {familia}?',
  'Diga o nome atual ligado a esta situação do {familia}.'),
 'recordar_objeto':(
  'Qual instrumento pertence ao estado atual desta conversa sobre o {familia}?',
  'Recupere a coisa material registrada neste caso do {familia}.',
  'Que item está associado à situação do {familia} agora?',
  'Diga qual objeto precisa ser lembrado aqui no {familia}.'),
 'corrigir_pessoa':(
  'Atualização de participante: retire {pessoa} e passe a usar {nova}.',
  'Troque a pessoa vigente de {pessoa} para {nova}.',
  'A referência humana mudou: agora é {nova}, não {pessoa}.',
  'Corrija o estado: {nova} substitui {pessoa} como pessoa.'),
 'guardar_hipotese':(
  'Estou apenas cogitando {atividade}. Isso já virou confirmação?',
  '{atividade} é uma possibilidade por enquanto. Posso tratar como fato?',
  'Ainda não decidi sobre {atividade}; isso está confirmado?',
  'A ideia de {atividade} continua provisória. Já conta como decisão?'),
 'mensagem_sem_horario':(
  'Escreva para {pessoa} convidando para {atividade}, sem escolher horário.',
  'Formule um convite a {pessoa} para {atividade} e deixe a hora em aberto.',
  'Quero chamar {pessoa} para {atividade}; redija sem inventar quando.',
  'Prepare uma mensagem curta para {pessoa} sobre {atividade}, sem marcar hora.'),
 'pedir_detalhe':(
  'Vou pedir algo a {pessoa}, mas ainda não informei qual item.',
  'Existe um pedido para {pessoa}; falta dizer a coisa que será pedida.',
  'Quero solicitar alguma coisa a {pessoa}, só que o objeto não foi especificado.',
  'O destinatário é {pessoa}, porém falta indicar o item do pedido.'),
}
RESPOSTAS = {
 'recordar_pessoa':'{pessoa} é a pessoa vigente.',
 'recordar_objeto':'{objeto} é o objeto vigente.',
 'corrigir_pessoa':'{nova} passa a ser a pessoa vigente.',
 'guardar_hipotese':'{atividade} continua como hipótese, não como confirmação.',
 'mensagem_sem_horario':'{pessoa}, você gostaria de combinar {atividade} comigo?',
 'pedir_detalhe':'Qual item você quer pedir a {pessoa}?',
}


def gerar():
    rng=random.Random(SEMENTE)
    saida=[]
    for fi,(familia,pessoas,objetos,atividades) in enumerate(FAMILIAS):
        for vi in range(4):
            pessoa=pessoas[vi]; nova=f'{pessoa.split("-")[0]}X-{int(pessoa.split("-")[1])+71}'
            objeto=objetos[vi]; atividade=atividades[vi]
            hist=[
              {'papel':'usuario','texto':f'No {familia}, a pessoa é {pessoa}; o objeto é {objeto}; a atividade em pauta é {atividade}.'},
              {'papel':'assistente','texto':f'Registrei pessoa {pessoa}, objeto {objeto} e atividade {atividade}.'},
            ]
            atual=pessoa
            ordem=ORDENS[(fi+vi)%len(ORDENS)]
            for turno,op in enumerate(ordem,1):
                pergunta=PERGUNTAS[op][(fi*4+vi+turno)%4].format(pessoa=atual,nova=nova,atividade=atividade,objeto=objeto,familia=familia)
                resposta=RESPOSTAS[op].format(pessoa=atual,nova=nova,atividade=atividade,objeto=objeto,familia=familia)
                if op=='corrigir_pessoa':
                    atual=nova
                    resposta=RESPOSTAS[op].format(pessoa=pessoa,nova=nova,atividade=atividade,objeto=objeto)
                elif op in ('recordar_pessoa','mensagem_sem_horario','pedir_detalhe'):
                    resposta=RESPOSTAS[op].format(pessoa=atual,nova=nova,atividade=atividade,objeto=objeto,familia=familia)
                ex={
                  'id':f'esc17m-pointer-v3-{fi}-{vi}-{turno}',
                  'familia':familia,'turno':turno,'operacao':op,
                  'mensagem':pergunta,'resposta':resposta,
                  'historico':[dict(x) for x in hist],
                  'slots':{'pessoa':atual,'objeto':objeto,'atividade':atividade,'nova':nova},
                }
                saida.append(ex)
                hist.extend([{'papel':'usuario','texto':pergunta},{'papel':'assistente','texto':resposta}])
    assert len(saida)==120
    assert len({x['id'] for x in saida})==120
    por={op:sum(x['operacao']==op for x in saida) for op in OPERACOES}
    assert set(por.values())=={20},por
    return saida

if __name__=='__main__':
    print(json.dumps(gerar(),ensure_ascii=False,indent=2))
