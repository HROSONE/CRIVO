#!/usr/bin/env python3
"""Holdout neutro para auditoria pareada V1/V4/V5. Não participa de treino."""
from __future__ import annotations

SEMENTE = 20261011182
OPERACOES = (
    "recordar_pessoa","recordar_objeto","corrigir_pessoa",
    "guardar_hipotese","mensagem_sem_horario","pedir_detalhe",
)
FAMILIAS = (
    ("laboratório de espectroscopia",
     ("Karel-3111","Karel-3127","Karel-3143","Karel-3159"),
     ("espectrômetro de massa","fonte de deutério","célula de quartzo","monocromador"),
     ("análise espectral","calibração de absorbância","varredura ultravioleta","medição de emissão")),
    ("observatório meteorológico alpino",
     ("Liren-3212","Liren-3228","Liren-3244","Liren-3260"),
     ("piranômetro","anemômetro sônico","ceilômetro","pluviômetro de pesagem"),
     ("medição de irradiância","perfil de vento","detecção de nuvens","registro de precipitação")),
    ("arquivo de cartografia histórica",
     ("Maren-3313","Maren-3329","Maren-3345","Maren-3361"),
     ("mesa de luz","lupa estereoscópica","scanner planetário","régua cartográfica"),
     ("comparação de mapas","inspeção de pigmentos","digitalização de atlas","medição de escala")),
    ("oficina de luteria experimental",
     ("Norel-3414","Norel-3430","Norel-3446","Norel-3462"),
     ("calibre de espessura","forma interna","raspador de aço","afinador estroboscópico"),
     ("medição de tampo","montagem de caixa","ajuste de curvatura","afinação de ressonância")),
    ("centro de entomologia agrícola",
     ("Pavel-3515","Pavel-3531","Pavel-3547","Pavel-3563"),
     ("armadilha luminosa","lupa binocular","câmara climática","aspirador entomológico"),
     ("triagem de insetos","identificação morfológica","ensaio de temperatura","coleta de espécimes")),
)
ORDENS = (
    ("recordar_pessoa","recordar_objeto","corrigir_pessoa","guardar_hipotese","mensagem_sem_horario","pedir_detalhe"),
    ("guardar_hipotese","pedir_detalhe","recordar_objeto","corrigir_pessoa","mensagem_sem_horario","recordar_pessoa"),
    ("mensagem_sem_horario","recordar_pessoa","guardar_hipotese","recordar_objeto","pedir_detalhe","corrigir_pessoa"),
    ("pedir_detalhe","corrigir_pessoa","mensagem_sem_horario","recordar_pessoa","recordar_objeto","guardar_hipotese"),
)
PERGUNTAS = {
    "recordar_pessoa":(
        "Quem continua registrado como participante neste caso de {familia}?",
        "Recupere o nome humano vigente nesta sequência de {familia}.",
        "Qual pessoa permanece associada ao estado atual de {familia}?",
        "Diga quem está valendo como participante neste caso de {familia}."),
    "recordar_objeto":(
        "Qual equipamento continua registrado neste caso de {familia}?",
        "Recupere o item material vigente nesta sequência de {familia}.",
        "Que objeto permanece associado ao estado atual de {familia}?",
        "Diga qual equipamento está valendo neste caso de {familia}."),
    "corrigir_pessoa":(
        "Corrija o participante: retire {pessoa} e use {nova}.",
        "Troque a referência humana de {pessoa} para {nova}.",
        "O nome correto agora é {nova}; substitua {pessoa}.",
        "Atualize o participante para {nova} no lugar de {pessoa}."),
    "guardar_hipotese":(
        "Estou apenas considerando {atividade}; isso já está confirmado?",
        "{atividade} ainda é uma possibilidade. Deve virar fato?",
        "Não decidi {atividade}. Isso continua provisório?",
        "Trate {atividade} só como ideia por enquanto. Já é confirmação?"),
    "mensagem_sem_horario":(
        "Escreva para {pessoa} sobre {atividade}, sem marcar horário.",
        "Convide {pessoa} para {atividade} sem escolher quando.",
        "Prepare uma mensagem a {pessoa} propondo {atividade}, sem hora.",
        "Redija um convite para {pessoa} fazer {atividade}, deixando o momento aberto."),
    "pedir_detalhe":(
        "Preciso pedir algo a {pessoa}, mas ainda não informei qual item.",
        "A solicitação é para {pessoa}; falta dizer o objeto.",
        "Quero pedir uma coisa a {pessoa}, porém o item não foi especificado.",
        "A pessoa é {pessoa}, mas ainda falta o conteúdo material do pedido."),
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
            nova=f'{pessoa.split("-")[0]}Z-{int(pessoa.split("-")[1])+91}'
            objeto=objetos[vi]
            atividade=atividades[vi]
            hist=[
                {"papel":"usuario","texto":f"Em {familia}, registre pessoa {pessoa}, objeto {objeto} e atividade {atividade}."},
                {"papel":"assistente","texto":f"Estado registrado: pessoa {pessoa}; objeto {objeto}; atividade {atividade}."},
            ]
            atual=pessoa
            ordem=ORDENS[(fi+vi)%len(ORDENS)]
            for turno,op in enumerate(ordem,1):
                pergunta=PERGUNTAS[op][(fi+vi+turno)%4].format(
                    pessoa=atual,nova=nova,atividade=atividade,objeto=objeto,familia=familia)
                resposta=RESPOSTAS[op].format(
                    pessoa=atual,nova=nova,atividade=atividade,objeto=objeto,familia=familia)
                if op=="corrigir_pessoa":
                    atual=nova
                ex={
                    "id":f"audit17m-{fi}-{vi}-{turno}",
                    "familia":familia,"turno":turno,"operacao":op,
                    "mensagem":pergunta,"resposta":resposta,
                    "historico":[dict(x) for x in hist],
                    "slots":{"pessoa":atual,"objeto":objeto,"atividade":atividade,"nova":nova},
                }
                saida.append(ex)
                hist.extend([{"papel":"usuario","texto":pergunta},{"papel":"assistente","texto":resposta}])
    assert len(saida)==120
    assert set(sum(x["operacao"]==op for x in saida) for op in OPERACOES)=={20}
    return saida
