#!/usr/bin/env python3
"""Holdout prospectivo V6: 120 casos, 4 paráfrases balanceadas por operação."""
from __future__ import annotations
import json
SEMENTE=20261011196
OPERACOES=("recordar_pessoa","recordar_objeto","corrigir_pessoa","guardar_hipotese","mensagem_sem_horario","pedir_detalhe")
OP_INDEX={op:i for i,op in enumerate(OPERACOES)}
FAMILIAS=(
("laboratório de espectrometria de plasma",("Warel-4111","Warel-4127","Warel-4143","Warel-4159"),("nebulizador concêntrico","tocha de quartzo icp","amostrador de níquel","câmara ciclônica"),("ajuste de plasma","calibração multielementar","leitura de emissão","lavagem de linha")),
("observatório magnetométrico",("Xoren-4212","Xoren-4228","Xoren-4244","Xoren-4260"),("magnetômetro fluxgate","sensor de precessão de prótons","bobina de calibração","registrador geomagnético"),("medição de declinação","calibração de campo","registro de tempestade magnética","análise de variação secular")),
("centro de restauração cerâmica",("Yven-4313","Yven-4329","Yven-4345","Yven-4361"),("micromotor de precisão","espátula de teflon","lupa articulada","câmara de cura"),("limpeza de fragmentos","reintegração de lacunas","inspeção de esmalte","cura de adesivo")),
("oficina de drones de inspeção",("Zaren-4414","Zaren-4430","Zaren-4446","Zaren-4462"),("gimbal estabilizado","módulo rtk","controlador de voo","sensor óptico de fluxo"),("calibração de horizonte","planejamento de rota","teste de redundância","ajuste de posicionamento")),
("laboratório de oceanografia química",("Belon-4515","Belon-4531","Belon-4547","Belon-4563"),("titulador potenciométrico","amostrador rosette","sonda de oxigênio óptico","espectrofotômetro de bancada"),("medição de alcalinidade","coleta de profundidade","perfil de oxigênio","análise de nutrientes")),
)
ORDENS=(("recordar_pessoa","guardar_hipotese","recordar_objeto","corrigir_pessoa","pedir_detalhe","mensagem_sem_horario"),("pedir_detalhe","recordar_objeto","mensagem_sem_horario","guardar_hipotese","corrigir_pessoa","recordar_pessoa"),("mensagem_sem_horario","recordar_pessoa","corrigir_pessoa","pedir_detalhe","recordar_objeto","guardar_hipotese"),("guardar_hipotese","pedir_detalhe","recordar_pessoa","recordar_objeto","mensagem_sem_horario","corrigir_pessoa"))
Q={
"recordar_pessoa":("Qual nome humano deve ser recuperado no estado de {familia}?","Quem permanece como participante válido no histórico de {familia}?","Informe a pessoa que continua associada ao caso de {familia}.","Recupere quem está registrado como participante atual em {familia}."),
"recordar_objeto":("Qual item físico ficou vinculado ao estado atual de {familia}?","Recupere o equipamento que permanece válido no caso de {familia}.","Que peça material deve ser lembrada neste histórico de {familia}?","Informe o objeto que ainda pertence a esta situação de {familia}."),
"corrigir_pessoa":("Substitua {pessoa} por {nova} como participante válido.","Retifique o nome humano: agora vale {nova}, não {pessoa}.","Mude o participante registrado de {pessoa} para {nova}.","Considere {nova} como pessoa atual no lugar de {pessoa}."),
"guardar_hipotese":("{atividade} está apenas em consideração; isso conta como confirmação?","Ainda avalio {atividade}. Deve ser registrada como fato?","{atividade} segue como possibilidade; já é decisão?","Não confirme {atividade} ainda. Isso continua hipotético?"),
"mensagem_sem_horario":("Escreva a {pessoa} propondo {atividade}, sem definir horário.","Faça um convite para {pessoa} sobre {atividade} e deixe o momento em aberto.","Chame {pessoa} para {atividade} sem escolher quando.","Redija para {pessoa} uma proposta de {atividade}, sem marcar hora."),
"pedir_detalhe":("Vou solicitar algo a {pessoa}, mas não disse qual item; o que falta?","O pedido é para {pessoa}, porém o objeto não foi especificado. O que devo informar?","Quero pedir uma coisa a {pessoa}; qual detalhe material ainda falta?","Sei o destinatário {pessoa}, mas não o item do pedido. O que preciso dizer?"),}
R={"recordar_pessoa":"{pessoa} é a pessoa vigente.","recordar_objeto":"{objeto} é o objeto vigente.","corrigir_pessoa":"{nova} passa a ser a pessoa vigente.","guardar_hipotese":"{atividade} continua como hipótese, não como confirmação.","mensagem_sem_horario":"{pessoa}, você gostaria de combinar {atividade} comigo?","pedir_detalhe":"Qual item você quer pedir a {pessoa}?"}
def gerar():
 out=[]
 for fi,(fam,ps,os,ats) in enumerate(FAMILIAS):
  for vi in range(4):
   p=ps[vi]; nova=f'{p.split("-")[0]}R-{int(p.split("-")[1])+103}'; obj=os[vi]; at=ats[vi]
   hist=[{"papel":"usuario","texto":f"Em {fam}, registre pessoa {p}, objeto {obj} e atividade {at}."},{"papel":"assistente","texto":f"Estado registrado: pessoa {p}; objeto {obj}; atividade {at}."}]
   atual=p
   for turno,op in enumerate(ORDENS[(fi+vi)%4],1):
    qi=(vi+OP_INDEX[op])%4; q=Q[op][qi].format(familia=fam,pessoa=atual,nova=nova,objeto=obj,atividade=at)
    resp=R[op].format(pessoa=atual,nova=nova,objeto=obj,atividade=at)
    if op=="corrigir_pessoa": atual=nova
    ex={"id":f"v6hold-{fi}-{vi}-{turno}","familia":fam,"turno":turno,"operacao":op,"template":qi,"mensagem":q,"resposta":resp,"historico":[dict(x) for x in hist],"slots":{"pessoa":atual,"objeto":obj,"atividade":at,"nova":nova}}
    out.append(ex); hist.extend([{"papel":"usuario","texto":q},{"papel":"assistente","texto":resp}])
 assert len(out)==120 and len({x['mensagem'] for x in out})==120
 for op in OPERACOES:
  assert sum(x['operacao']==op for x in out)==20
  assert {i:sum(x['operacao']==op and x['template']==i for x in out) for i in range(4)}=={0:5,1:5,2:5,3:5}
 return out
if __name__=='__main__': print(json.dumps(gerar(),ensure_ascii=False,indent=2))
