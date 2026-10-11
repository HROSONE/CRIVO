"""Currículo V7: diversidade semântica ampla sem alterar arquitetura/objetivos da V4."""
from __future__ import annotations
from collections import Counter

SEMENTE = 20261011208
OPERACOES = (
    'recordar_pessoa','recordar_objeto','corrigir_pessoa',
    'guardar_hipotese','mensagem_sem_horario','pedir_detalhe',
)
ACOES = {
    'recordar_pessoa':'recordar','recordar_objeto':'recordar',
    'corrigir_pessoa':'atualizar','guardar_hipotese':'epistemico',
    'mensagem_sem_horario':'compor','pedir_detalhe':'esclarecer',
}
FOCOS = {
    'recordar_pessoa':'pessoa','recordar_objeto':'objeto',
    'corrigir_pessoa':'pessoa','guardar_hipotese':'nenhum',
    'mensagem_sem_horario':'pessoa','pedir_detalhe':'objeto',
}
CENARIOS = (
    'biblioteca técnica','almoxarifado industrial','estação agronômica','arquivo municipal',
    'oficina de instrumentação','laboratório de materiais','centro logístico','estúdio de ensaios',
    'sala de inventário','bancada de eletrônica','observatório didático','depósito de componentes',
    'centro de amostras','oficina de manutenção','sala de protótipos','arquivo de engenharia',
    'estação de campo','laboratório de metrologia','galpão de testes','centro de documentação',
    'sala de calibração','oficina de precisão','núcleo de catalogação','posto de inspeção',
)
PREF_PESSOA = ('Aren','Bela','Ciro','Dora','Elin','Faro','Gali','Hera','Iven','Jora','Keli','Luma','Maro','Nira','Oren','Pali','Quin','Ravi','Sela','Tori','Ulan','Vera','Wali','Xena','Yuri','Zali')
PREF_NOVA = ('Lio','Mavi','Nelo','Orin','Pavo','Quela','Reno','Sani','Tero','Ulia','Viro','Wena','Xaro','Yani','Zeno','Adri','Breno','Celi','Davi','Eli','Fina','Gino','Hali','Iara','Juno','Kira')
OBJ_BASE = ('sensor','medidor','calibrador','módulo','adaptador','registrador','indicador','amostrador','conector','suporte','cartucho','filtro','placa','painel','guia','cápsula','visor','recipiente','régua','sonda','ponteira','gabarito','separador','acoplador','carretel','disco','pino','anel','estojo','bloco','alicate','marcador')
OBJ_QUAL = ('óptico','térmico','digital','portátil','cerâmico','magnético','linear','selado','de referência','de bancada','graduado','compacto','isolado','mecânico','azul','âmbar')
ATIV_BASE = ('calibração','inspeção','catalogação','medição','triagem','revisão','montagem','limpeza','conferência','registro','ensaio','organização','comparação','levantamento','checagem','ajuste','classificação','marcação','preparação','alinhamento','inventário','teste','documentação','separação','verificação','amostragem','leitura','avaliação','contagem','mapeamento','observação','manutenção')
ATIV_QUAL = ('térmica','óptica','estrutural','manual','de campo','de bancada','de rotina','de precisão','comparativa','instrumental','de segurança','de qualidade','de material','de sensores','de componentes','de referência')
ABERTURAS = ('Neste caso','Por enquanto','No estado atual','Até aqui','Considerando o que registramos','Neste contexto','Agora','Com base no histórico')
PEDIDOS = ('me diga','recupere','lembre','identifique','informe','retome','aponte','indique')
PESSOA_NOMES = ('a pessoa vigente','o participante atual','a referência humana','quem está registrado','o nome em vigor','quem continua associado')
OBJETO_NOMES = ('o objeto vigente','o item material','o equipamento atual','a coisa registrada','o elemento físico associado','o item em vigor')
INCERTEZA = ('ainda é só uma possibilidade','continua provisório','não foi confirmado','é apenas uma hipótese','segue em consideração','ainda não virou fato')
SEM_HORA = ('sem marcar horário','sem escolher quando','deixando o momento em aberto','sem definir hora','sem inventar um horário','sem fixar o momento')
FALTA_ITEM = ('o item não foi informado','a coisa ainda não foi especificada','falta dizer o objeto','não sabemos o que será pedido','o conteúdo material ficou ausente','ainda não foi dito qual item')
RESPOSTAS_PESSOA = ('{pessoa} é a pessoa vigente.','A pessoa atual é {pessoa}.','{pessoa} continua como participante.','O participante registrado é {pessoa}.','A referência humana em vigor é {pessoa}.','Quem está valendo é {pessoa}.','{pessoa} permanece associado ao caso.','O nome vigente continua sendo {pessoa}.')
RESPOSTAS_OBJETO = ('{objeto} é o objeto vigente.','O objeto atual é {objeto}.','{objeto} continua como item registrado.','O item material em vigor é {objeto}.','O equipamento associado é {objeto}.','A coisa registrada continua sendo {objeto}.','{objeto} permanece como elemento físico do caso.','O item vigente continua sendo {objeto}.')
RESPOSTAS_CORRECAO = ('{nova} passa a ser a pessoa vigente.','A pessoa atual agora é {nova}.','{nova} substitui a referência anterior.','O participante em vigor passa a ser {nova}.','Registrei {nova} como pessoa atual.','Daqui em diante, a referência humana é {nova}.','{nova} fica como participante vigente.','A correção deixa {nova} como pessoa atual.')
RESPOSTAS_HIP = ('{atividade} continua como hipótese, não como confirmação.','{atividade} permanece uma possibilidade, não um fato.','{atividade} segue provisória; ainda não está confirmada.','{atividade} continua em consideração, sem confirmação.','Por enquanto, {atividade} é apenas uma hipótese.','{atividade} não deve ser tratada como decisão confirmada.','O status de {atividade} continua provisório.','{atividade} permanece incerta até haver confirmação.')
RESPOSTAS_MSG = ('{pessoa}, você gostaria de combinar {atividade} comigo?','{pessoa}, topa fazer {atividade} comigo?','{pessoa}, gostaria de fazer {atividade} comigo?','{pessoa}, vamos combinar {atividade}?','{pessoa}, você tem interesse em fazer {atividade} comigo?','{pessoa}, que tal fazermos {atividade}?','{pessoa}, podemos combinar {atividade}?','{pessoa}, você gostaria de participar de {atividade} comigo?')
RESPOSTAS_DET = ('Qual item você quer pedir a {pessoa}?','O que exatamente você quer pedir a {pessoa}?','Que item você pretende pedir a {pessoa}?','Falta dizer o item do pedido a {pessoa}; qual é?','Qual é a coisa que você quer solicitar a {pessoa}?','Você pode dizer qual objeto deseja pedir a {pessoa}?','Ainda falta o item: o que você quer pedir a {pessoa}?','Que objeto deve entrar no pedido para {pessoa}?')
ORDENS = (
    OPERACOES,
    ('corrigir_pessoa','recordar_objeto','guardar_hipotese','recordar_pessoa','pedir_detalhe','mensagem_sem_horario'),
    ('pedir_detalhe','mensagem_sem_horario','recordar_pessoa','guardar_hipotese','recordar_objeto','corrigir_pessoa'),
    ('recordar_objeto','corrigir_pessoa','mensagem_sem_horario','pedir_detalhe','guardar_hipotese','recordar_pessoa'),
    ('guardar_hipotese','recordar_pessoa','pedir_detalhe','recordar_objeto','corrigir_pessoa','mensagem_sem_horario'),
    ('mensagem_sem_horario','pedir_detalhe','corrigir_pessoa','guardar_hipotese','recordar_pessoa','recordar_objeto'),
    ('recordar_pessoa','mensagem_sem_horario','recordar_objeto','corrigir_pessoa','pedir_detalhe','guardar_hipotese'),
    ('pedir_detalhe','guardar_hipotese','mensagem_sem_horario','recordar_objeto','recordar_pessoa','corrigir_pessoa'),
)

def _slots(i):
    pessoa=f'{PREF_PESSOA[i%len(PREF_PESSOA)]}-{10000+i}'
    nova=f'{PREF_NOVA[(i*7)%len(PREF_NOVA)]}-{20000+i}'
    objeto=f'{OBJ_BASE[i%32]} {OBJ_QUAL[(i//32)%16]} série {30000+i}'
    atividade=f'{ATIV_BASE[(i*5)%32]} {ATIV_QUAL[(i//17)%16]} ciclo {40000+i}'
    return pessoa,nova,objeto,atividade

def _pergunta(op,i,turno,cenario,pessoa,nova,objeto,atividade):
    a=ABERTURAS[(i+turno)%len(ABERTURAS)]; p=PEDIDOS[(i*3+turno)%len(PEDIDOS)]
    if op=='recordar_pessoa':
        alvo=PESSOA_NOMES[(i+2*turno)%len(PESSOA_NOMES)]; formas=(f'{a}, {p} {alvo}.',f'{p.capitalize()} {alvo} {a.lower()}.',f'{a}, qual é {alvo}?',f'Quero retomar {cenario}: {p} {alvo}.')
    elif op=='recordar_objeto':
        alvo=OBJETO_NOMES[(i+2*turno)%len(OBJETO_NOMES)]; formas=(f'{a}, {p} {alvo}.',f'{p.capitalize()} {alvo} {a.lower()}.',f'{a}, qual é {alvo}?',f'Voltando a {cenario}, {p} {alvo}.')
    elif op=='corrigir_pessoa':
        formas=(f'Corrija apenas a pessoa: troque {pessoa} por {nova}.',f'{a}, {pessoa} deixa de valer; use {nova} como participante.',f'A referência humana mudou: não é mais {pessoa}, agora é {nova}.',f'Atualize o estado de {cenario}: substitua {pessoa} por {nova} e mantenha o restante.')
    elif op=='guardar_hipotese':
        inc=INCERTEZA[(i+turno)%len(INCERTEZA)]; formas=(f'Estou pensando em {atividade}; isso {inc}. Como tratar?',f'{atividade} {inc}. Posso considerar como fato?',f'{a}, a ideia de {atividade} {inc}; qual é o status?',f'No contexto de {cenario}, {atividade} {inc}. Isso já é decisão?')
    elif op=='mensagem_sem_horario':
        sh=SEM_HORA[(i+turno)%len(SEM_HORA)]; formas=(f'Escreva para {pessoa} propondo {atividade}, {sh}.',f'Convide {pessoa} para {atividade}, {sh}.',f'Faça uma mensagem natural a {pessoa} sobre {atividade}, {sh}.',f'Quero chamar {pessoa} para {atividade}; redija o convite {sh}.')
    else:
        falta=FALTA_ITEM[(i+turno)%len(FALTA_ITEM)]; formas=(f'Quero fazer um pedido a {pessoa}, mas {falta}.',f'O destinatário é {pessoa}; {falta}. O que você precisa saber?',f'Preciso solicitar algo a {pessoa}, porém {falta}.',f'Antes de preparar o pedido para {pessoa}, perceba que {falta}.')
    return formas[(i//8+turno)%len(formas)]

def _resposta(op,i,pessoa,nova,objeto,atividade):
    arr={'recordar_pessoa':RESPOSTAS_PESSOA,'recordar_objeto':RESPOSTAS_OBJETO,'corrigir_pessoa':RESPOSTAS_CORRECAO,'guardar_hipotese':RESPOSTAS_HIP,'mensagem_sem_horario':RESPOSTAS_MSG,'pedir_detalhe':RESPOSTAS_DET}[op]
    return arr[(i*5)%len(arr)].format(pessoa=pessoa,nova=nova,objeto=objeto,atividade=atividade)

def gerar_treino():
    saida=[]
    for i in range(4096):
        pessoa,nova,objeto,atividade=_slots(i); cenario=CENARIOS[(i*7)%len(CENARIOS)]; estilo=i%6
        if estilo==0:
            u=f'Em {cenario}, registre pessoa {pessoa}, objeto {objeto} e atividade {atividade}.'; a=f'Estado registrado: pessoa {pessoa}; objeto {objeto}; atividade {atividade}.'
        elif estilo==1:
            u=f'Contexto de {cenario}: {pessoa} participa; o item é {objeto}; estamos tratando de {atividade}.'; a=f'Entendi: participante {pessoa}, item {objeto}, atividade {atividade}.'
        elif estilo==2:
            u=f'Guarde este estado para {cenario}. Pessoa: {pessoa}. Equipamento: {objeto}. Trabalho: {atividade}.'; a=f'Vou considerar {pessoa} como pessoa, {objeto} como objeto e {atividade} como atividade.'
        elif estilo==3:
            u=f'Para o caso em {cenario}, associe {pessoa} a {objeto}; a atividade corrente é {atividade}.'; a=f'Associação mantida: {pessoa} / {objeto} / {atividade}.'
        elif estilo==4:
            u=f'Três dados de {cenario}: quem = {pessoa}; coisa = {objeto}; ação = {atividade}.'; a=f'Anotado. Pessoa {pessoa}, coisa {objeto}, ação {atividade}.'
        else:
            u=f'Estamos em {cenario}. O participante é {pessoa}, usamos {objeto} e a atividade é {atividade}.'; a=f'Certo, o estado atual liga {pessoa}, {objeto} e {atividade}.'
        hist=[{'papel':'usuario','texto':u},{'papel':'assistente','texto':a}]; atual=pessoa; ordem=ORDENS[i%len(ORDENS)]
        for turno,op in enumerate(ordem,1):
            q=_pergunta(op,i,turno,cenario,atual,nova,objeto,atividade); r=_resposta(op,i,atual,nova,objeto,atividade)
            if op=='corrigir_pessoa': atual=nova
            ex={'id':f'generalizacao-v7-train-{i}-{turno}','operacao':op,'acao':ACOES[op],'foco':FOCOS[op],'mensagem':q,'resposta':r,'historico':[dict(x) for x in hist],'slots':{'pessoa':atual,'objeto':objeto,'atividade':atividade,'nova':nova}}
            saida.append(ex); hist.extend([{'papel':'usuario','texto':q},{'papel':'assistente','texto':r}])
    assert len(saida)==24576
    por=Counter(x['operacao'] for x in saida); assert set(por.values())=={4096},por
    assert len({x['slots']['objeto'] for x in saida})==4096
    assert len({x['slots']['atividade'] for x in saida})==4096
    assert len({x['mensagem'] for x in saida})>=16000
    return saida

if __name__=='__main__':
    xs=gerar_treino(); print(len(xs),Counter(x['operacao'] for x in xs),len({x['mensagem'] for x in xs}))
