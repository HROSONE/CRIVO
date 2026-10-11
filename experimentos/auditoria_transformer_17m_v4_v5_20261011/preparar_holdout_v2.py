#!/usr/bin/env python3
"""Holdout diagnóstico V2: 120 casos, quatro paráfrases balanceadas por operação."""
from __future__ import annotations
import json

SEMENTE = 20261011191
OPERACOES = (
    "recordar_pessoa","recordar_objeto","corrigir_pessoa",
    "guardar_hipotese","mensagem_sem_horario","pedir_detalhe",
)
OP_INDEX = {op:i for i,op in enumerate(OPERACOES)}
FAMILIAS = (
    ("laboratório de acústica submarina",
     ("Ravel-3111","Ravel-3127","Ravel-3143","Ravel-3159"),
     ("hidrofone vetorial","calibrador acústico submersível","pré-amplificador estanque","gravador hidroacústico"),
     ("calibração de hidrofone","medição de ruído oceânico","teste de resposta acústica","análise de assinatura sonora")),
    ("centro de microscopia eletrônica",
     ("Sorel-3212","Sorel-3228","Sorel-3244","Sorel-3260"),
     ("porta-amostra de cobre","detector de elétrons secundários","canhão de emissão de campo","grade de difração eletrônica"),
     ("alinhamento do feixe","imagem de superfície","mapeamento elementar","difração de elétrons")),
    ("estação de geodesia de precisão",
     ("Taren-3313","Taren-3329","Taren-3345","Taren-3361"),
     ("receptor gnss geodésico","prisma de monitoramento","nível digital de precisão","antena choke ring"),
     ("rastreio de coordenadas","nivelamento geométrico","medição de deslocamento","ajuste de rede geodésica")),
    ("arquivo de conservação fotográfica",
     ("Ulen-3414","Ulen-3430","Ulen-3446","Ulen-3462"),
     ("densitômetro de transmissão","mesa de inspeção fria","lupa conta-fios","câmara de acondicionamento"),
     ("medição de densidade óptica","inspeção de negativos","avaliação de emulsão","controle de umidade")),
    ("laboratório de robótica agrícola",
     ("Viren-3515","Viren-3531","Viren-3547","Viren-3563"),
     ("sensor lidar agrícola","atuador linear selado","câmera multiespectral embarcada","encoder absoluto de roda"),
     ("mapeamento de fileiras","controle de direção","detecção de estresse vegetal","calibração de odometria")),
)
ORDENS = (
    ("recordar_pessoa","guardar_hipotese","recordar_objeto","corrigir_pessoa","pedir_detalhe","mensagem_sem_horario"),
    ("pedir_detalhe","recordar_objeto","mensagem_sem_horario","guardar_hipotese","corrigir_pessoa","recordar_pessoa"),
    ("mensagem_sem_horario","recordar_pessoa","corrigir_pessoa","pedir_detalhe","recordar_objeto","guardar_hipotese"),
    ("guardar_hipotese","pedir_detalhe","recordar_pessoa","recordar_objeto","mensagem_sem_horario","corrigir_pessoa"),
)
PERGUNTAS = {
 "recordar_pessoa":(
  "Quem segue como participante válido neste caso de {familia}?",
  "Recupere o nome humano vigente na situação de {familia}.",
  "Qual participante continua valendo neste histórico de {familia}?",
  "Diga quem ficou como pessoa atual neste caso de {familia}."),
 "recordar_objeto":(
  "Qual equipamento continua associado a este caso de {familia}?",
  "Recupere o item físico vigente no histórico de {familia}.",
  "Que objeto permanece registrado nesta situação de {familia}?",
  "Diga qual coisa material continua valendo em {familia}."),
 "corrigir_pessoa":(
  "Corrija o participante: troque {pessoa} por {nova}.",
  "A pessoa certa agora é {nova}, substituindo {pessoa}.",
  "Atualize a referência humana de {pessoa} para {nova}.",
  "Passe a considerar {nova} no lugar de {pessoa}."),
 "guardar_hipotese":(
  "Estou apenas considerando {atividade}. Isso já virou confirmação?",
  "{atividade} ainda é uma possibilidade; devo tratar como fato?",
  "Ainda não decidi sobre {atividade}. Está confirmado?",
  "Mantenha {atividade} só como hipótese por enquanto. Isso é definitivo?"),
 "mensagem_sem_horario":(
  "Convide {pessoa} para {atividade}, sem escolher horário.",
  "Escreva para {pessoa} propondo {atividade}, mas deixe a hora em aberto.",
  "Prepare um convite a {pessoa} para {atividade} sem marcar quando.",
  "Redija uma mensagem para {pessoa} sobre {atividade}, sem inventar hora."),
 "pedir_detalhe":(
  "Quero pedir alguma coisa a {pessoa}, mas o item não foi informado.",
  "Preciso fazer um pedido a {pessoa}; ainda falta dizer qual objeto.",
  "A solicitação será para {pessoa}, porém não especifiquei a coisa.",
  "Sei que o pedido é para {pessoa}, mas ainda não disse o item."),
}
RESPOSTAS = {
 "recordar_pessoa":"{pessoa} é a pessoa vigente.",
 "recordar_objeto":"{objeto} é o objeto vigente.",
 "corrigir_pessoa":"{nova} passa a ser a pessoa vigente.",
 "guardar_hipotese":"{atividade} continua como hipótese, não como confirmação.",
 "mensagem_sem_horario":"{pessoa}, você gostaria de combinar {atividade} comigo?",
 "pedir_detalhe":"Qual item você quer pedir a {pessoa}?",
}

def gerar():
    saida=[]
    for fi,(familia,pessoas,objetos,atividades) in enumerate(FAMILIAS):
        for vi in range(4):
            pessoa=pessoas[vi]
            nova=f'{pessoa.split("-")[0]}Q-{int(pessoa.split("-")[1])+101}'
            objeto=objetos[vi]
            atividade=atividades[vi]
            hist=[
                {"papel":"usuario","texto":f"Em {familia}, registre pessoa {pessoa}, objeto {objeto} e atividade {atividade}."},
                {"papel":"assistente","texto":f"Estado registrado: pessoa {pessoa}; objeto {objeto}; atividade {atividade}."},
            ]
            atual=pessoa
            ordem=ORDENS[(fi+vi)%len(ORDENS)]
            for turno,op in enumerate(ordem,1):
                qidx=(vi + OP_INDEX[op]) % 4
                pergunta=PERGUNTAS[op][qidx].format(
                    familia=familia,pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
                if op=="corrigir_pessoa":
                    resposta=RESPOSTAS[op].format(
                        pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
                    atual=nova
                else:
                    resposta=RESPOSTAS[op].format(
                        pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
                ex={
                    "id":f"audit17m-v2-{fi}-{vi}-{turno}",
                    "familia":familia,"turno":turno,"operacao":op,"template":qidx,
                    "mensagem":pergunta,"resposta":resposta,
                    "historico":[dict(x) for x in hist],
                    "slots":{"pessoa":atual,"objeto":objeto,"atividade":atividade,"nova":nova},
                }
                saida.append(ex)
                hist.extend([{"papel":"usuario","texto":pergunta},{"papel":"assistente","texto":resposta}])
    assert len(saida)==120
    assert len({x["id"] for x in saida})==120
    por={op:sum(x["operacao"]==op for x in saida) for op in OPERACOES}
    assert set(por.values())=={20},por
    for op in OPERACOES:
        dist={i:sum(x["operacao"]==op and x["template"]==i for x in saida) for i in range(4)}
        assert set(dist.values())=={5},(op,dist)
        assert len({x["mensagem"] for x in saida if x["operacao"]==op})==20,op
    assert len({x["mensagem"] for x in saida})==120
    return saida

if __name__=="__main__":
    print(json.dumps(gerar(),ensure_ascii=False,indent=2))
