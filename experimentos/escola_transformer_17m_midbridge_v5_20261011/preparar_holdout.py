#!/usr/bin/env python3
"""Holdout prospectivo V5: binding injetado no meio do Transformer 17M."""
from __future__ import annotations
import json, random

SEMENTE = 20261011171
OPERACOES = (
    'recordar_pessoa','recordar_objeto','corrigir_pessoa',
    'guardar_hipotese','mensagem_sem_horario','pedir_detalhe',
)
FAMILIAS = (
    ('laboratório de acústica',
     ('Farel-1811','Farel-1827','Farel-1843','Farel-1859'),
     ('microfone de referência','analisador de espectro','calibrador acústico','painel absorvente'),
     ('medição de ruído','ensaio de resposta','calibração sonora','mapeamento acústico')),
    ('estação oceanográfica',
     ('Grena-1912','Grena-1928','Grena-1944','Grena-1960'),
     ('garrafa de niskin','sonda multiparâmetro','correntômetro','disco de secchi'),
     ('coleta de água','perfil de salinidade','medição de corrente','leitura de transparência')),
    ('oficina de conservação têxtil',
     ('Harel-2013','Harel-2029','Harel-2045','Harel-2061'),
     ('lupa conta-fios','suporte de trama','mesa de sucção','medidor de ph'),
     ('análise de fibras','estabilização de tecido','limpeza por sucção','medição de acidez')),
    ('núcleo de geodésia',
     ('Ivena-2114','Ivena-2130','Ivena-2146','Ivena-2162'),
     ('receptor gnss','nível digital','prisma topográfico','estação total'),
     ('levantamento geodésico','nivelamento de precisão','medição angular','ajuste de coordenadas')),
    ('viveiro botânico',
     ('Joren-2215','Joren-2231','Joren-2247','Joren-2263'),
     ('medidor de clorofila','bandeja de germinação','tensiômetro de solo','câmara de crescimento'),
     ('avaliação foliar','teste de germinação','monitoramento hídrico','controle de crescimento')),
)
ORDENS = (
    ('recordar_objeto','corrigir_pessoa','recordar_pessoa','guardar_hipotese','pedir_detalhe','mensagem_sem_horario'),
    ('guardar_hipotese','recordar_objeto','mensagem_sem_horario','corrigir_pessoa','recordar_pessoa','pedir_detalhe'),
    ('pedir_detalhe','recordar_pessoa','corrigir_pessoa','recordar_objeto','mensagem_sem_horario','guardar_hipotese'),
    ('mensagem_sem_horario','guardar_hipotese','recordar_pessoa','pedir_detalhe','corrigir_pessoa','recordar_objeto'),
)
PERGUNTAS = {
 'recordar_pessoa':(
  'Recupere quem permanece associado como participante nesta situação de {familia}.',
  'Qual nome humano está valendo neste ponto do caso de {familia}?',
  'Quem deve ser lembrado como participante atual em {familia}?',
  'Indique a pessoa que ficou vigente nesta sequência de {familia}.'),
 'recordar_objeto':(
  'Qual item físico continua ligado ao caso de {familia}?',
  'Traga de volta o equipamento registrado nesta sequência de {familia}.',
  'Que objeto material está valendo neste estado de {familia}?',
  'Qual foi a coisa registrada para este caso de {familia}?'),
 'corrigir_pessoa':(
  'Revise o participante: sai {pessoa} e entra {nova}.',
  'Faça a troca de referência humana de {pessoa} para {nova}.',
  'O participante correto agora é {nova}; substitua {pessoa}.',
  'Atualize o estado para considerar {nova} no lugar de {pessoa}.'),
 'guardar_hipotese':(
  'Estou somente avaliando {atividade}; isso já deve ser tratado como confirmado?',
  '{atividade} ainda é só uma possibilidade. Já posso registrar como decisão?',
  'Não fechei {atividade}. Isso conta como fato ou continua provisório?',
  'Considere {atividade} apenas como ideia por enquanto. Está confirmado?'),
 'mensagem_sem_horario':(
  'Escreva um convite a {pessoa} para {atividade}, sem definir quando.',
  'Redija para {pessoa} uma mensagem sobre {atividade} e não invente horário.',
  'Convide {pessoa} para {atividade}, deixando o momento em aberto.',
  'Prepare uma mensagem para {pessoa} propondo {atividade}, sem marcar hora.'),
 'pedir_detalhe':(
  'Preciso solicitar algo a {pessoa}, mas ainda não disse qual coisa.',
  'O pedido será para {pessoa}; falta informar o item solicitado.',
  'Quero fazer uma solicitação a {pessoa}, porém não especifiquei o objeto.',
  'A pessoa é {pessoa}, mas o conteúdo material do pedido ainda está ausente.'),
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
            pessoa=pessoas[vi]
            nova=f'{pessoa.split("-")[0]}Z-{int(pessoa.split("-")[1])+83}'
            objeto=objetos[vi]
            atividade=atividades[vi]
            hist=[
              {'papel':'usuario','texto':f'No contexto de {familia}, registre pessoa {pessoa}, objeto {objeto} e atividade {atividade}.'},
              {'papel':'assistente','texto':f'Estado inicial salvo: pessoa {pessoa}; objeto {objeto}; atividade {atividade}.'},
            ]
            atual=pessoa
            ordem=ORDENS[(fi*2+vi)%len(ORDENS)]
            for turno,op in enumerate(ordem,1):
                pergunta=PERGUNTAS[op][(fi+2*vi+turno)%4].format(
                    pessoa=atual,nova=nova,atividade=atividade,objeto=objeto,familia=familia)
                resposta=RESPOSTAS[op].format(
                    pessoa=atual,nova=nova,atividade=atividade,objeto=objeto,familia=familia)
                if op=='corrigir_pessoa':
                    resposta=RESPOSTAS[op].format(pessoa=atual,nova=nova,atividade=atividade,objeto=objeto)
                    atual=nova
                elif op in ('recordar_pessoa','mensagem_sem_horario','pedir_detalhe'):
                    resposta=RESPOSTAS[op].format(pessoa=atual,nova=nova,atividade=atividade,objeto=objeto,familia=familia)
                ex={
                  'id':f'esc17m-midbridge-v5-{fi}-{vi}-{turno}',
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
