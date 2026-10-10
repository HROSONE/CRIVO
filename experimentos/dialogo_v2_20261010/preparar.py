"""Diálogos autorais novos; argumentos e entidades separados por diálogo."""
import copy
import hashlib
import json
from pathlib import Path
import sys

H=Path(__file__).resolve().parent;ROOT=H.parent.parent
sys.path.insert(0,str(ROOT))
from linguagem_gerativa import ESPECIAIS,tokenizar

# Oito pequenos arcos escritos à mão. Não há alvo do conjunto congelado.
ARCOS=[
 ('Uma ponte estava quebrada. A personagem procurou madeira. Com paciência, montou uma passagem. A viagem pôde continuar.',
  'A passagem levou a uma trilha. A personagem conferiu o mapa. Depois escolheu um caminho seguro.',
  'O encontro trouxe ajuda. Juntos, consertaram a ponte. A viagem terminou com uma nova amizade.'),
 ('Um vento forte espalhou o mapa. A personagem recolheu os pedaços. Depois colocou tudo em ordem. O caminho ficou claro.',
  'A trilha parecia diferente. A personagem comparou os caminhos. Uma marca no chão mostrou a direção.',
  'O encontro resolveu a dúvida. Juntos, olharam o mapa. A viagem terminou com uma descoberta.'),
 ('Uma porta estava fechada. A personagem encontrou uma chave. Abriu a porta com cuidado. Do outro lado havia um caminho.',
  'O caminho levou a uma surpresa. A personagem escutou um som. Depois decidiu procurar sua origem.',
  'O encontro trouxe uma pergunta. Juntos, procuraram a resposta. A aventura terminou com uma porta aberta.'),
 ('Uma chuva começou durante a viagem. A personagem procurou abrigo. Esperou a chuva passar. Depois retomou o caminho.',
  'O caminho estava molhado. A personagem andou devagar. Depois encontrou uma passagem segura.',
  'O encontro trouxe companhia. Juntos, esperaram a chuva passar. A viagem terminou com uma conversa tranquila.'),
 ('Um bilhete caiu no caminho. A personagem leu o pedido. Decidiu procurar quem precisava de ajuda. A busca começou.',
  'Uma pista apareceu na trilha. A personagem seguiu a direção. Depois ouviu um pedido de ajuda.',
  'O encontro explicou o bilhete. Juntos, resolveram o pedido. A busca terminou com uma conversa.'),
 ('Um objeto apareceu na trilha. A personagem guardou o objeto. Procurou quem havia perdido aquilo. A procura trouxe uma pista.',
  'Uma marca apareceu no chão. A personagem seguiu a pista. Depois encontrou a origem do objeto.',
  'O encontro resolveu o mistério. Juntos, devolveram o objeto. A procura terminou com uma boa surpresa.'),
 ('Uma correnteza bloqueou o caminho. A personagem observou a água. Encontrou uma passagem. A travessia começou com cuidado.',
  'A passagem parecia estreita. A personagem avançou devagar. Depois alcançou o outro lado.',
  'O encontro trouxe uma ideia. Juntos, escolheram uma passagem segura. A travessia terminou com uma nova amizade.'),
 ('Um som chamou a atenção. A personagem parou para escutar. Procurou a origem do som. Depois encontrou uma pista.',
  'A pista levou a uma porta. A personagem procurou uma chave. Depois abriu a porta com cuidado.',
  'O encontro trouxe uma resposta. Juntos, descobriram a origem do som. A aventura terminou com uma boa surpresa.'),
]

def main():
    antigos=json.loads((H.parent/'dialogo_20261010/corpus_gru.json').read_text())['exemplos']
    raw_old=json.loads((H.parent/'dialogo_20261010/corpus.json').read_text())
    # O segundo checkpoint continua sendo um realizador de ficção: as demais
    # famílias ficam no corpus de diálogo, mas não são promovidas para esta rede.
    treino=[copy.deepcopy(e) for e in antigos if e['contexto']['acao'] in ('historia','continuacao','final')]
    novas=[]
    tr_personagens=['uma lontra inventora','um esquilo viajante','uma lebre curiosa','um castor aprendiz']
    va_personagens=['um quati desenhista','uma doninha exploradora']
    tr_lugares=['uma ilha pequena','um bosque silencioso','uma estação antiga','um vale distante']
    va_lugares=['uma praça vazia','uma torre esquecida']
    for variante,(inicio,meio,fim) in enumerate(ARCOS):
        for cenario in (False,True):
            for n in range(24):
                val=n>=20;split='validacao' if val else 'treino'
                personagem=(va_personagens if val else tr_personagens)[n% (2 if val else 4)]
                lugar=(va_lugares if val else tr_lugares)[(n//2)% (2 if val else 4)]
                slots={'tema1':personagem}
                if cenario:slots['tema2']=lugar
                abertura='Ficção: A história de @tema1 começou '+('em @tema2.' if cenario else 'com uma viagem.')
                continuacao='Ficção: @tema1 continuou a viagem'+(' em @tema2.' if cenario else '.')
                encerramento='Ficção: @tema1 encontrou '+('@detalhe em @tema2.' if cenario else '@tema2.')
                antes,ultima=fim.rsplit('. ',1)
                final_cinco=antes+'. A personagem agradeceu a ajuda. '+ultima
                textos=[abertura+' '+inicio,continuacao+' '+meio,encerramento+' '+final_cinco]
                mensagens=['Conte uma aventura com '+personagem+(' em '+lugar if cenario else '')+'.',
                            'Mostre a próxima parte da aventura.',
                            'Refaça o desfecho com um companheiro.']
                historico=[];ident='arco-%d-%d-%02d'%(variante,cenario,n)
                for t,acao in enumerate(('historia','continuacao','final')):
                    argumentos=dict(slots)
                    if acao=='final':argumentos['detalhe' if cenario else 'tema2']='um companheiro'
                    ctx={'acao':acao,'slots':argumentos,'estilo':'neutro','variante':variante,
                         'mensagem':mensagens[t],'historico':list(historico[-3:]),'resposta_anterior':''}
                    ex={'id':ident+'-'+str(t),'dialogo':ident,'familia':'arco-autoral-'+str(variante),
                        'split':split,'contexto':ctx,'resposta':textos[t],
                        'origem':'Enredo autoral novo; sem extração de alvos do teste.'}
                    novas.append(ex);historico.extend([mensagens[t],textos[t]])
    treino+=novas
    vocab=list(ESPECIAIS)+sorted({t for e in treino if e['split']=='treino' for t in tokenizar(e['resposta'])}-set(ESPECIAIS))
    assert len(vocab)<=209,('Não aumentar parâmetros',len(vocab))
    congelados=json.loads((H/'casos_congelados.json').read_text())['casos']
    entradas={c['entrada']['texto'] for c in congelados}
    assert not entradas & {e['contexto']['mensagem'] for e in novas}
    entidades_teste=['Pernélia','Dorlécio','Elvrino','mariposa jardineira','coruja engenheira','jardim suspenso','capivara astronauta','tatu violinista','ariranha cartógrafa']
    serialized=json.dumps(novas,ensure_ascii=False)
    assert not any(v in serialized for v in entidades_teste)
    corpus={'versao':2,'origem':'Demonstrações autorais, não sessões humanas. Oito arcos; reaproveita somente o treino próprio de ficção.',
        'fontes_externas':False,'dialogos_novos':384,'turnos_novos':2304,
        'turnos_corpus_total':raw_old['turnos_usuario_assistente']+2304,
        'exemplos':treino,'vocabulario':vocab,
        'limite':'48 novos padrões de narrativa, não 384 enredos humanos; estado de tarefa e argumentos vêm do roteador.'}
    p=H/'corpus_gru.json';p.write_text(json.dumps(corpus,ensure_ascii=False,indent=2)+'\n')
    audit={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'exemplos':len(treino),
        'treino':sum(e['split']=='treino' for e in treino),'validacao':sum(e['split']=='validacao' for e in treino),
        'padroes_ficcao_antes':len({e['resposta'] for e in antigos if e['contexto']['acao'] in ('historia','continuacao','final')}),
        'padroes_ficcao_depois':len({e['resposta'] for e in treino}),
        'vocabulario':len(vocab),'entidades_novas_separadas':True,'casos_avaliacao_no_treino':False,
        'particao':'Diálogo completo, personagens e cenários de validação diferentes do treino; oito arcos compartilhados.'}
    (H/'auditoria_corpus.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(audit)

if __name__=='__main__':main()
