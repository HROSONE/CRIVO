#!/usr/bin/env python3
"""Holdout prospectivo V2: ligação de slots abertos no Transformer 17,43M.

Este arquivo é congelado antes do treinador V2. Não importa código de treino.
"""
from __future__ import annotations

OPERACOES=("recordar_pessoa","recordar_objeto","corrigir_pessoa","guardar_hipotese","mensagem_sem_horario","pedir_detalhe")
ROTULOS={
 "recordar_pessoa":("recordar","pessoa"),"recordar_objeto":("recordar","objeto"),
 "corrigir_pessoa":("atualizar","pessoa"),"guardar_hipotese":("epistemico","nenhum"),
 "mensagem_sem_horario":("compor","pessoa"),"pedir_detalhe":("esclarecer","objeto"),
}
FAMILIAS=(
 ("planetario","no planetário",("esfera armilar","projetor estelar","carta celeste","ocular","laser de apontamento"),("sessão de cúpula","navegação celeste","calibração de estrelas","simulação orbital","identificação de constelações")),
 ("aquario","no aquário",("refratômetro","sifão","termostato","rede de manejo","densímetro"),("aclimatação","análise salina","manutenção de tanque","alimentação de recife","inspeção de filtros")),
 ("hangar","no hangar",("torquímetro","calço de roda","rebiteira","manômetro","capa de pitot"),("inspeção de asa","checagem hidráulica","revisão de trem de pouso","teste de pressão","verificação de cabine")),
 ("grafica","na gráfica",("guilhotina","matriz","espátula","rolo entintador","conta-fios"),("prova de cor","imposição de páginas","corte de papel","registro de chapa","acabamento editorial")),
 ("torre","na torre meteorológica",("anemômetro","psicrômetro","pluviômetro","barógrafo","biruta"),("leitura do vento","registro de umidade","medição de chuva","análise de pressão","observação de rajadas")),
 ("pomar","no pomar",("tesoura de poda","enxadão","fita de enxertia","pulverizador","caixa de colheita"),("poda seletiva","enxertia","colheita de frutos","inspeção de pragas","irrigação localizada")),
)
NOMES=(("Taren-131","Selia-242"),("Moren-353","Liria-464"),("Pavel-575","Naira-686"),("Rovel-797","Talia-808"),("Ciren-919","Vania-121"),("Barel-232","Mirea-343"))
ORDENS=(
 OPERACOES,
 ("pedir_detalhe","mensagem_sem_horario","recordar_objeto","corrigir_pessoa","guardar_hipotese","recordar_pessoa"),
 ("guardar_hipotese","recordar_objeto","corrigir_pessoa","recordar_pessoa","mensagem_sem_horario","pedir_detalhe"),
 ("recordar_objeto","pedir_detalhe","mensagem_sem_horario","guardar_hipotese","recordar_pessoa","corrigir_pessoa"),
 ("mensagem_sem_horario","corrigir_pessoa","recordar_pessoa","pedir_detalhe","recordar_objeto","guardar_hipotese"),
)
FORMAS={
 "recordar_pessoa":("Recupere a pessoa válida desse contexto {lugar}.","Quem ficou como pessoa corrente {lugar}?","Sem repetir o resumo, diga a pessoa atual {lugar}.","Qual identidade humana está associada ao caso {lugar}?","Quem devo considerar como participante {lugar}?"),
 "recordar_objeto":("Recupere exatamente o objeto do contexto {lugar}.","Que item material ficou associado ao caso {lugar}?","Diga o objeto atual, não a pessoa, no cenário {lugar}.","Qual objeto específico está guardado no estado da conversa {lugar}?","Lembre o item mencionado no começo do caso {lugar}."),
 "corrigir_pessoa":("Corrija a pessoa {lugar}: sai {pessoa}, entra {nova}.","Atualize o participante {lugar} de {pessoa} para {nova}.","A identidade válida mudou {lugar}: substitua {pessoa} por {nova}.","Troque a pessoa do caso {lugar}; agora vale {nova}, não {pessoa}.","Registre a correção {lugar}: {nova} assume o lugar de {pessoa}."),
 "guardar_hipotese":("Estou apenas considerando {atividade} {lugar}. Isso já é fato confirmado?","Talvez aconteça {atividade} {lugar}; ainda não decidi. Está confirmado?","{atividade} {lugar} é só uma possibilidade por enquanto. Posso tratar como certo?","Cogitei {atividade} {lugar}, sem decisão final. Isso virou confirmação?","A ideia de {atividade} {lugar} continua provisória. Já posso chamá-la de fato?"),
 "mensagem_sem_horario":("Escreva para {pessoa} propondo {atividade} {lugar}, sem criar horário.","Monte um convite curto para {pessoa} sobre {atividade} {lugar}; deixe a hora em aberto.","Quero chamar {pessoa} para {atividade} {lugar}. Redija sem marcar quando.","Faça uma mensagem a {pessoa} combinando {atividade} {lugar}, mas não invente hora.","Prepare um convite simples para {pessoa} fazer {atividade} {lugar}, sem horário."),
 "pedir_detalhe":("Quero pedir algo a {pessoa} {lugar}, mas não informei qual item.","Há um pedido para {pessoa} {lugar}; falta dizer o objeto pedido.","Vou solicitar uma coisa a {pessoa} {lugar}, porém não especifiquei o quê.","O destinatário é {pessoa} {lugar}, mas ainda falta o item do pedido.","Preciso fazer um pedido a {pessoa} {lugar}; pergunte qual coisa está faltando."),
}

def resposta(op,pessoa,nova,objeto,atividade):
 if op=="recordar_pessoa": return f"A pessoa é {pessoa}."
 if op=="recordar_objeto": return f"O objeto é {objeto}."
 if op=="corrigir_pessoa": return f"Atualizado: a pessoa agora é {nova}."
 if op=="guardar_hipotese": return f"Não. {atividade} continua apenas como possibilidade."
 if op=="mensagem_sem_horario": return f"{pessoa}, quer combinar {atividade} comigo?"
 if op=="pedir_detalhe": return f"O que você quer pedir a {pessoa}?"
 raise KeyError(op)

def gerar():
 xs=[]
 for fi,(familia,lugar,objetos,atividades) in enumerate(FAMILIAS):
  base,nova=NOMES[fi]
  for v in range(5):
   pessoa=base; objeto=objetos[v]; atividade=atividades[v]
   hist=[{"papel":"usuario","texto":f"Estado inicial {lugar}: pessoa {pessoa}; objeto {objeto}; atividade {atividade}."},{"papel":"assistente","texto":"Certo, mantive esses três elementos no contexto."}]
   for turno,op in enumerate(ORDENS[v],1):
    msg=FORMAS[op][v].format(lugar=lugar,pessoa=pessoa,nova=nova,objeto=objeto,atividade=atividade)
    resp=resposta(op,pessoa,nova,objeto,atividade); acao,foco=ROTULOS[op]
    xs.append({"id":f"esc17m-v2-{familia}-{v}-{turno}","split":"prospectivo_v2","familia":familia,"variante":v,"turno":turno,"historico":[dict(z) for z in hist],"mensagem":msg,"resposta":resp,"operacao":op,"acao":acao,"foco":foco})
    hist.extend([{"papel":"usuario","texto":msg},{"papel":"assistente","texto":resp}])
    if op=="corrigir_pessoa": pessoa=nova
 assert len(xs)==180
 assert len({x["id"] for x in xs})==180
 assert len({x["mensagem"] for x in xs})==180
 assert {op:sum(x["operacao"]==op for x in xs) for op in OPERACOES}=={op:30 for op in OPERACOES}
 return xs

if __name__=="__main__":
 from collections import Counter
 xs=gerar(); print(len(xs),Counter(x["operacao"] for x in xs))
