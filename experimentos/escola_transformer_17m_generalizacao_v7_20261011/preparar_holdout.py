"""Holdout prospectivo V7: generalização semântica, congelado antes do treino."""
from __future__ import annotations

SEMENTE = 20261011207
OPERACOES = (
    "recordar_pessoa","recordar_objeto","corrigir_pessoa",
    "guardar_hipotese","mensagem_sem_horario","pedir_detalhe",
)
FAMILIAS = (
    ("estação de arqueologia submarina",
     ("Terval-7101","Terval-7107","Terval-7113","Terval-7119"),
     ("sonar de varredura lateral","draga de sucção fina","câmera hiperbárica","magnetômetro marinho"),
     ("mapeamento do sítio","triagem de sedimentos","registro fotogramétrico","levantamento magnético")),
    ("laboratório de criogenia aplicada",
     ("Sorel-7202","Sorel-7208","Sorel-7214","Sorel-7220"),
     ("criostato de hélio","ponte térmica calibrada","sensor de fluxo quântico","câmara de vácuo pulsado"),
     ("ensaio supercondutor","calibração térmica","leitura de fluxo","ciclo de despressurização")),
    ("centro de restauração de manuscritos",
     ("Varen-7303","Varen-7309","Varen-7315","Varen-7321"),
     ("mesa de sucção capilar","espátula de bambu","lâmpada multiespectral","prensa de conservação"),
     ("limpeza de fibras","nivelamento de folhas","análise de pigmentos","estabilização do caderno")),
    ("plataforma de ecologia acústica",
     ("Neris-7404","Neris-7410","Neris-7416","Neris-7422"),
     ("gravador hidroacústico","calibrador acústico submersível","hidrofone vetorial","boia telemétrica"),
     ("amostragem de vocalizações","calibração de ganho","localização de fontes","telemetria de ruído")),
    ("oficina de microscopia eletrônica",
     ("Lumer-7505","Lumer-7511","Lumer-7517","Lumer-7523"),
     ("porta-amostra de cobre","canhão de emissão de campo","detector de elétrons retroespalhados","bomba turbomolecular"),
     ("metalização da amostra","ajuste do feixe","aquisição composicional","evacuação da coluna")),
)
# Estas formulações ficam exclusivamente na prova.
PERGUNTAS = {
 "recordar_pessoa": (
   "Sem repetir o restante do estado, identifique quem está valendo como participante em {familia}.",
   "Do que ficou estabelecido até aqui em {familia}, qual é a referência humana vigente?",
   "Se eu perguntar apenas pelo participante atual de {familia}, quem você recupera?",
   "Retome o contexto de {familia} e diga somente qual pessoa continua associada a ele.",
 ),
 "recordar_objeto": (
   "Sem listar o resto do estado, qual equipamento permanece associado a {familia}?",
   "Do contexto acumulado em {familia}, recupere o item físico que continua vigente.",
   "Se eu pedir apenas o objeto atual de {familia}, qual você deve recuperar?",
   "Retome {familia} e diga qual coisa material ainda pertence ao estado.",
 ),
 "corrigir_pessoa": (
   "Há uma retificação em {familia}: desconsidere {pessoa} e passe a considerar {nova}.",
   "Para o restante desta conversa sobre {familia}, a referência humana correta deixa de ser {pessoa} e passa a ser {nova}.",
   "Atualize somente o participante de {familia}: onde constava {pessoa}, agora vale {nova}.",
   "Corrija o estado de {familia}; mantenha o restante, mas troque {pessoa} por {nova}.",
 ),
 "guardar_hipotese": (
   "Em {familia}, estou apenas cogitando {atividade}. Isso deve ser tratado como certeza?",
   "Considere {atividade} uma possibilidade para {familia}, não uma decisão. Como fica o status?",
   "Ainda não confirmei {atividade} em {familia}; em que condição essa ideia deve permanecer?",
   "Sobre {familia}: {atividade} foi levantada só como hipótese. Isso já autoriza registrá-la como fato?",
 ),
 "mensagem_sem_horario": (
   "Redija para {pessoa} um convite natural sobre {atividade} em {familia}, mas deixe o momento totalmente em aberto.",
   "Quero propor {atividade} a {pessoa} no contexto de {familia}; escreva a mensagem sem escolher quando.",
   "Formule uma mensagem curta convidando {pessoa} para {atividade}, relacionada a {familia}, sem inventar horário.",
   "Convide {pessoa} para {atividade} em {familia}; a mensagem deve soar natural e não definir hora.",
 ),
 "pedir_detalhe": (
   "Em {familia}, sei que o pedido é para {pessoa}, mas não informei o que quero pedir. O que você deve fazer?",
   "Quero solicitar alguma coisa a {pessoa} sobre {familia}, porém o item ficou ausente. Responda adequadamente.",
   "Há destinatário — {pessoa} — mas falta o objeto da solicitação em {familia}. Como você prossegue?",
   "No caso de {familia}, pretendo pedir algo a {pessoa}; como ainda não disse o item, qual é a resposta correta?",
 ),
}
RESPOSTAS = {
 "recordar_pessoa": (
   "{pessoa} é a pessoa vigente.","A pessoa vigente é {pessoa}.",
   "{pessoa} continua como participante atual.","A referência humana atual é {pessoa}.",
 ),
 "recordar_objeto": (
   "{objeto} é o objeto vigente.","O objeto vigente é {objeto}.",
   "{objeto} continua como item atual.","A coisa material atual é {objeto}.",
 ),
 "corrigir_pessoa": (
   "{nova} passa a ser a pessoa vigente.","A pessoa vigente agora é {nova}.",
   "{nova} substitui a referência humana anterior.","O participante atual passa a ser {nova}.",
 ),
 "guardar_hipotese": (
   "{atividade} continua como hipótese, não como confirmação.",
   "{atividade} permanece uma possibilidade, não um fato confirmado.",
   "{atividade} segue provisória; ainda não está confirmada.",
   "{atividade} continua em consideração, sem confirmação.",
 ),
 "mensagem_sem_horario": (
   "{pessoa}, você gostaria de combinar {atividade} comigo?",
   "{pessoa}, topa fazer {atividade} comigo?",
   "{pessoa}, gostaria de fazer {atividade} comigo?",
   "{pessoa}, vamos combinar {atividade}?",
 ),
 "pedir_detalhe": (
   "Qual item você quer pedir a {pessoa}?",
   "O que exatamente você quer pedir a {pessoa}?",
   "Que item você pretende pedir a {pessoa}?",
   "Falta dizer o item do pedido a {pessoa}; qual é?",
 ),
}
ORDENS = (
 ("recordar_pessoa","guardar_hipotese","recordar_objeto","corrigir_pessoa","mensagem_sem_horario","pedir_detalhe"),
 ("pedir_detalhe","recordar_objeto","guardar_hipotese","recordar_pessoa","corrigir_pessoa","mensagem_sem_horario"),
 ("mensagem_sem_horario","corrigir_pessoa","recordar_pessoa","pedir_detalhe","recordar_objeto","guardar_hipotese"),
 ("guardar_hipotese","mensagem_sem_horario","pedir_detalhe","corrigir_pessoa","recordar_objeto","recordar_pessoa"),
)

def gerar():
    saida=[]
    sessao=0
    for fi,(familia,pessoas,objetos,atividades) in enumerate(FAMILIAS):
        for vi in range(4):
            variante=sessao % 4
            pessoa=pessoas[vi]; objeto=objetos[vi]; atividade=atividades[vi]
            nova=f"{pessoa.split('-')[0]}Q-{int(pessoa.split('-')[1])+137}"
            hist=[
              {"papel":"usuario","texto":f"Contexto inicial de {familia}: participante {pessoa}; equipamento {objeto}; atividade {atividade}."},
              {"papel":"assistente","texto":f"Entendido. Estado atual: pessoa {pessoa}; objeto {objeto}; atividade {atividade}."},
            ]
            atual=pessoa
            ordem=ORDENS[(fi+vi)%len(ORDENS)]
            for turno,op in enumerate(ordem,1):
                q=PERGUNTAS[op][variante].format(
                    familia=familia,pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
                r=RESPOSTAS[op][variante].format(
                    familia=familia,pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
                if op=="corrigir_pessoa":
                    atual=nova
                ex={"id":f"v7-hold-{fi}-{vi}-{turno}","familia":familia,"variante":variante,"operacao":op,
                    "mensagem":q,"resposta":r,"historico":[dict(x) for x in hist],
                    "slots":{"pessoa":atual,"objeto":objeto,"atividade":atividade,"nova":nova}}
                saida.append(ex)
                hist.extend([{"papel":"usuario","texto":q},{"papel":"assistente","texto":r}])
            sessao += 1
    assert len(saida)==120
    assert all(sum(x["operacao"]==op for x in saida)==20 for op in OPERACOES)
    for op in OPERACOES:
        xs=[x for x in saida if x["operacao"]==op]
        assert {sum(x["variante"]==v for x in xs) for v in range(4)}=={5}
        assert len({x["mensagem"] for x in xs})==20
    return saida
