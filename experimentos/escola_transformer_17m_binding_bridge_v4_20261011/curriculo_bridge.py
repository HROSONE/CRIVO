"""Currículo V4: estado aberto e operações de diálogo para a ponte de binding.

Gera 512 sessões × 6 operações = 3.072 exemplos. Pessoa, objeto e atividade
variam quase totalmente por sessão para forçar uso do histórico.
"""
from __future__ import annotations
from collections import Counter

SEMENTE = 20261011162
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
LUGARES = (
    'na biblioteca técnica','no almoxarifado','no laboratório seco','na sala de mapas',
    'no arquivo histórico','na bancada eletrônica','no observatório escolar','na oficina mecânica',
    'no centro de amostras','na sala de protótipos','no depósito central','no estúdio de testes',
    'no laboratório de materiais','na sala de inventário','no pátio de manutenção','na área de conferência',
)
PREF_PESSOA = (
    'Areno','Beli','Caio','Dorel','Elian','Fira','Galen','Helia',
    'Isen','Jora','Kalen','Mira','Noren','Olia','Peren','Rina',
    'Savio','Talia','Uren','Vania','Welen','Xira','Yalen','Zora',
    'Brina','Ciro','Dalia','Eron','Faren','Gilda','Haren','Iria',
)
PREF_NOVA = (
    'Lior','Mavi','Nilo','Oria','Pavel','Queli','Ravi','Sena',
    'Toren','Ulia','Vero','Wira','Xeno','Yara','Zeni','Adra',
    'Breno','Celi','Davi','Elia','Faro','Gina','Hugo','Iara',
    'Juno','Kira','Lena','Miro','Nara','Oren','Pia','Ruan',
)
OBJ_NOMES = (
    'medidor','estojo','sensor','calibrador','suporte','adaptador','amostrador','indicador',
    'módulo','visor','conector','recipiente','marcador','gabarito','registrador','acoplador',
    'carretel','medidor manual','bloco','separador','alicate','painel','cartucho','guia',
    'disco','pino','régua técnica','placa','anel','filtro','cápsula','ponteira',
)
OBJ_QUAL = (
    'âmbar','cerâmico','linear','óptico','térmico','magnético','azul','portátil',
    'de bancada','de referência','selado','graduado','isolado','compacto','mecânico','digital',
)
ATIV_NOMES = (
    'calibração','inspeção','catalogação','medição','triagem','revisão','montagem','limpeza',
    'conferência','registro','ensaio','organização','comparação','levantamento','checagem','ajuste',
    'classificação','marcação','preparação','alinhamento','inventário','teste','documentação','separação',
    'verificação','amostragem','leitura','avaliação','contagem','mapeamento','observação','manutenção',
)
ATIV_QUAL = (
    'térmica','óptica','estrutural','manual','de campo','de bancada','de rotina','de precisão',
    'comparativa','instrumental','de segurança','de qualidade','de material','de sensores','de componentes','de referência',
)
ORDENS = (
    OPERACOES,
    ('corrigir_pessoa','recordar_pessoa','recordar_objeto','guardar_hipotese','pedir_detalhe','mensagem_sem_horario'),
    ('recordar_objeto','guardar_hipotese','corrigir_pessoa','mensagem_sem_horario','recordar_pessoa','pedir_detalhe'),
    ('pedir_detalhe','recordar_pessoa','mensagem_sem_horario','corrigir_pessoa','recordar_objeto','guardar_hipotese'),
    ('mensagem_sem_horario','pedir_detalhe','recordar_objeto','guardar_hipotese','corrigir_pessoa','recordar_pessoa'),
    ('guardar_hipotese','recordar_objeto','pedir_detalhe','recordar_pessoa','mensagem_sem_horario','corrigir_pessoa'),
    ('recordar_pessoa','mensagem_sem_horario','guardar_hipotese','pedir_detalhe','recordar_objeto','corrigir_pessoa'),
    ('pedir_detalhe','corrigir_pessoa','guardar_hipotese','recordar_objeto','mensagem_sem_horario','recordar_pessoa'),
)
PERGUNTAS = {
 'recordar_pessoa':(
  'Quem é a pessoa vigente neste contexto?','Recupere a pessoa atual da conversa.',
  'Qual nome está valendo como participante?','Quem ficou registrado como pessoa?',
  'Lembre o participante atual.','Diga a referência humana vigente.',
  'Quem devo considerar como pessoa agora?','Qual pessoa está ativa neste caso?'),
 'recordar_objeto':(
  'Qual é o objeto vigente neste contexto?','Recupere o item material da conversa.',
  'Que objeto ficou registrado?','Qual coisa pertence ao estado atual?',
  'Lembre o item associado ao caso.','Diga o objeto atual.',
  'Que coisa material devo considerar agora?','Qual objeto está ativo neste contexto?'),
 'corrigir_pessoa':(
  'Troque a pessoa de {pessoa} para {nova}.','Atualize o participante: sai {pessoa}, entra {nova}.',
  'Agora a pessoa é {nova}, não {pessoa}.','Corrija a referência humana para {nova} no lugar de {pessoa}.',
  'Substitua {pessoa} por {nova} como pessoa atual.','A pessoa vigente mudou de {pessoa} para {nova}.',
  'Registre {nova} como nova pessoa e descarte {pessoa}.','Use {nova} daqui em diante em vez de {pessoa}.'),
 'guardar_hipotese':(
  'Talvez eu faça {atividade}. Isso já está confirmado?','Estou considerando {atividade}; posso tratar como fato?',
  '{atividade} ainda é só uma possibilidade. Já virou decisão?','Cogitei {atividade}, mas não decidi. Está confirmado?',
  'A ideia de {atividade} é provisória. Isso é certeza?','Ainda penso em {atividade}. Já devo considerar confirmado?',
  'Existe a possibilidade de {atividade}. É fato agora?','{atividade} está em avaliação. Posso marcar como confirmado?'),
 'mensagem_sem_horario':(
  'Escreva para {pessoa} chamando para {atividade}, sem horário.','Convide {pessoa} para {atividade} sem marcar hora.',
  'Faça uma mensagem a {pessoa} propondo {atividade}, sem dizer quando.','Redija um convite para {pessoa} fazer {atividade}; deixe a hora aberta.',
  'Quero chamar {pessoa} para {atividade}; escreva sem inventar horário.','Prepare um convite curto para {pessoa} sobre {atividade}, sem hora.',
  'Formule uma mensagem para {pessoa} combinando {atividade}, sem horário.','Mande um convite a {pessoa} para {atividade}, mas não escolha hora.'),
 'pedir_detalhe':(
  'Quero pedir algo a {pessoa}, mas não disse o item.','Há um pedido para {pessoa}; falta informar o objeto.',
  'Vou solicitar uma coisa a {pessoa}, só que não especifiquei qual.','O destinatário é {pessoa}, porém o item do pedido está ausente.',
  'Preciso pedir algo a {pessoa}; ainda falta dizer o quê.','Tenho um pedido para {pessoa}, mas a coisa não foi informada.',
  'Pretendo solicitar um item a {pessoa}; qual item ainda não foi dito.','Quero fazer um pedido a {pessoa}; o objeto não apareceu.'),
}
RESPOSTAS = {
 'recordar_pessoa':(
  '{pessoa} é a pessoa atual.','{pessoa} é a pessoa vigente.','{pessoa} é o participante registrado.','{pessoa} é a referência humana atual.'),
 'recordar_objeto':(
  '{objeto} é o objeto atual.','{objeto} é o objeto vigente.','{objeto} é o item registrado.','{objeto} é a coisa material atual.'),
 'corrigir_pessoa':(
  '{nova} é a pessoa atualizada.','{nova} passa a ser a pessoa vigente.','{nova} é a nova referência humana.','{nova} substitui a pessoa anterior.'),
 'guardar_hipotese':(
  '{atividade} continua como hipótese, não como confirmação.','{atividade} permanece uma possibilidade, não um fato confirmado.',
  '{atividade} segue provisória; ainda não está confirmada.','{atividade} continua em consideração, sem confirmação.'),
 'mensagem_sem_horario':(
  '{pessoa}, você quer combinar {atividade} comigo?','{pessoa}, topa fazer {atividade} comigo?',
  '{pessoa}, gostaria de combinar {atividade} comigo?','{pessoa}, vamos combinar {atividade}?'),
 'pedir_detalhe':(
  'Qual item você quer pedir a {pessoa}?','O que exatamente você quer pedir a {pessoa}?',
  'Que coisa você pretende pedir a {pessoa}?','Falta dizer o item do pedido a {pessoa}; qual é?'),
}

def _slots(i):
    pessoa=f'{PREF_PESSOA[i%32]}-{3000+i}'
    nova=f'{PREF_NOVA[(i*7)%32]}-{5000+i}'
    objeto=f'{OBJ_NOMES[i%32]} {OBJ_QUAL[(i//32)%16]}'
    atividade=f'{ATIV_NOMES[i%32]} {ATIV_QUAL[(i//32)%16]}'
    return pessoa,nova,objeto,atividade

def gerar_treino():
    saida=[]
    for i in range(512):
        pessoa,nova,objeto,atividade=_slots(i)
        lugar=LUGARES[i%len(LUGARES)]
        hist=[
          {'papel':'usuario','texto':f'Contexto {lugar}: pessoa {pessoa}; objeto {objeto}; atividade {atividade}.'},
          {'papel':'assistente','texto':f'Estado registrado: pessoa {pessoa}; objeto {objeto}; atividade {atividade}.'},
        ]
        atual=pessoa
        ordem=ORDENS[i%len(ORDENS)]
        for turno,op in enumerate(ordem,1):
            q=PERGUNTAS[op][(i+turno)%len(PERGUNTAS[op])].format(pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
            if op=='corrigir_pessoa':
                r=RESPOSTAS[op][(i+turno)%4].format(pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
                atual=nova
            else:
                r=RESPOSTAS[op][(i+turno)%4].format(pessoa=atual,nova=nova,objeto=objeto,atividade=atividade)
            ex={
              'id':f'bridge-v4-train-{i}-{turno}','operacao':op,'acao':ACOES[op],'foco':FOCOS[op],
              'mensagem':q,'resposta':r,'historico':[dict(x) for x in hist],
              'slots':{'pessoa':atual,'objeto':objeto,'atividade':atividade,'nova':nova},
            }
            saida.append(ex)
            hist.extend([{'papel':'usuario','texto':q},{'papel':'assistente','texto':r}])
    assert len(saida)==3072
    por=Counter(x['operacao'] for x in saida)
    assert set(por.values())=={512},por
    assert len({x['slots']['objeto'] for x in saida})==512
    assert len({x['slots']['atividade'] for x in saida})==512
    return saida

if __name__=='__main__':
    xs=gerar_treino(); print(len(xs),Counter(x['operacao'] for x in xs),
          len({x['slots']['objeto'] for x in xs}),len({x['slots']['atividade'] for x in xs}))
