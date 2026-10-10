"""Sequências autorais com trecho anterior, entidades separadas e sem alvos do teste."""
import copy
import hashlib
import json
import sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent.parent))
from linguagem_gerativa import tokenizar

CADEIA=[
    'A personagem parou para pensar. Observou o caminho com cuidado. Uma nova pista apareceu.',
    'Depois guardou a pista. Um pedido de ajuda chamou a atenção. A personagem procurou quem precisava de ajuda.',
    'Encontrou um objeto perdido. Antes de continuar, observou o objeto. Uma marca mostrou a direção.',
    'A personagem seguiu a direção da marca. Um som veio do outro lado. Decidiu procurar a origem do som.',
    'O som levou a uma passagem estreita. A personagem escolheu uma passagem segura. A travessia começou.',
    'Do outro lado havia uma pergunta. A personagem esperou com paciência. Uma resposta trouxe uma ideia.',
    'Com a nova ideia, a personagem procurou uma nova direção. O caminho estava aberto. A busca pôde continuar.',
    'A procura terminou com uma boa surpresa. A personagem agradeceu a ajuda. Depois guardou o objeto com cuidado.'
]

def prefixo(slots):
    return 'Ficção: @tema1 continuou a história'+(' com @detalhe' if slots.get('detalhe') else '')+(' em @tema2' if slots.get('tema2') else '')+'. '

def main():
    original=json.loads((H.parent/'dialogo_continuidade_20261010/corpus_gru.json').read_text())
    exemplos=copy.deepcopy(original['exemplos'])
    # Históricos de comando continuam neutros; a resposta anterior agora é supervisão.
    for e in exemplos:e['contexto'].update(mensagem='',historico=[])
    novos=[]
    for variante in range(8):
        for lugar in (False,True):
            for companhia in (False,True):
                for evento in (False,True):
                    for n in range(6):
                        val=n>=5
                        slots={'tema1':'uma irara aprendiz' if not val else 'um ouriço viajante'}
                        if lugar:slots['tema2']='um bosque distante' if not val else 'um castelo silencioso'
                        if companhia:slots['detalhe']='uma colega' if not val else 'um aliado'
                        if evento:slots['relato']='A personagem encontrou um objeto antigo' if not val else 'A personagem guardou uma pista'
                        anteriores=[e for e in exemplos if e['contexto']['acao']=='continuacao' and e['contexto'].get('variante')==variante and bool(e['contexto']['slots'].get('tema2'))==lugar and bool(e['contexto']['slots'].get('detalhe'))==companhia]
                        previo=anteriores[0]['resposta'] if anteriores else prefixo(slots)+'A personagem observou o caminho. Uma pista apareceu. A busca começou.'
                        for fase,corpo in enumerate(CADEIA,1):
                            # A variação de arco conserva o vocabulário autoral anterior.
                            texto=prefixo(slots)+('@relato. ' if evento else '')+corpo
                            if fase%2==0: texto=texto.replace('A personagem', 'Depois, a personagem',1)
                            contexto={'acao':'continuacao','slots':dict(slots),'estilo':'neutro','variante':variante,
                                      'mensagem':'','historico':[],'resposta_anterior':previo}
                            ident='sequencia-%d-%d-%d-%d-%d'%(variante,lugar,companhia,evento,n)
                            novos.append({'id':ident+'-'+str(fase),'dialogo':ident,'familia':'sequencia-autoral-'+str(variante),
                                          'split':'validacao' if val else 'treino','contexto':contexto,'resposta':texto,
                                          'origem':'Continuação escrita pelo projeto; não usa perguntas, entidades ou respostas das sondas.'})
                            previo=texto
    exemplos+=novos
    vocab=list(original['vocabulario'])
    vocab+=sorted({t for e in novos for t in tokenizar(e['resposta'])}-set(vocab))
    out={'versao':4,'origem':'Sequências autorais supervisionadas pela resposta anterior e evento explícito em slot.',
         'fontes_externas':False,'exemplos':exemplos,'vocabulario':vocab,
         'limite':'Oito estágios autorais compartilhados nas partições; exemplos sintéticos, não entendimento geral de textos.'}
    p=H/'corpus_gru.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    audit={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'novos':len(novos),'exemplos':len(exemplos),
           'treino':sum(e['split']=='treino' for e in exemplos),'validacao':sum(e['split']=='validacao' for e in exemplos),
           'tokens_novos':[t for t in vocab if t not in original['vocabulario']], 'vocabulario':len(vocab),
           'particao':'Diálogos inteiros e entidades separados; os estágios autorais são compartilhados, não generalização de enredo.'}
    (H/'auditoria_corpus.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(audit)

if __name__=='__main__':main()
