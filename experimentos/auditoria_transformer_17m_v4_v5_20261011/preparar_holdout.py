#!/usr/bin/env python3
"""Holdout diagnóstico prospectivo: comparação pareada V1/V4/V5, sem treino."""
from __future__ import annotations
import json

SEMENTE = 20261011183
OPERACOES = (
    "recordar_pessoa","recordar_objeto","corrigir_pessoa",
    "guardar_hipotese","mensagem_sem_horario","pedir_detalhe",
)
FAMILIAS = (
    ("observatório meteorológico",
     ("Kirel-2311","Kirel-2327","Kirel-2343","Kirel-2359"),
     ("barômetro aneroide","psicrômetro ventilado","pluviômetro de báscula","anemômetro ultrassônico"),
     ("calibração de pressão","medição de umidade","teste de precipitação","análise de vento")),
    ("oficina de relojoaria",
     ("Lunor-2412","Lunor-2428","Lunor-2444","Lunor-2460"),
     ("cronocomparador","chave de fundo","lupa de bancada","desmagnetizador"),
     ("ajuste de marcha","abertura de caixa","inspeção de rubis","remoção de magnetismo")),
    ("acervo paleontológico",
     ("Miren-2513","Miren-2529","Miren-2545","Miren-2561"),
     ("paquímetro fossilífero","berço de espuma","agulha pneumática","lupa binocular"),
     ("medição de fóssil","acondicionamento de peça","preparação de matriz","análise de superfície")),
    ("laboratório de alimentos",
     ("Navel-2614","Navel-2630","Navel-2646","Navel-2662"),
     ("refratômetro digital","texturômetro","medidor de atividade de água","homogeneizador"),
     ("medição de sólidos","ensaio de textura","controle de estabilidade","preparo de amostra")),
    ("estúdio de iluminação",
     ("Orien-2715","Orien-2731","Orien-2747","Orien-2763"),
     ("fotômetro","fresnel led","cartão cinza","difusor parabólico"),
     ("medição de iluminância","ajuste de foco","balanço de exposição","controle de suavidade")),
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
            nova=f'{pessoa.split("-")[0]}Q-{int(pessoa.split("-")[1])+97}'
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
                    familia=familia,pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
                if op=="corrigir_pessoa":
                    resposta=RESPOSTAS[op].format(
                        pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
                    atual=nova
                else:
                    resposta=RESPOSTAS[op].format(
                        pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
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
    assert len({x["id"] for x in saida})==120
    por={op:sum(x["operacao"]==op for x in saida) for op in OPERACOES}
    assert set(por.values())=={20},por
    return saida

if __name__=="__main__":
    print(json.dumps(gerar(),ensure_ascii=False,indent=2))
