"""Corpus próprio de continuação com papéis constantes; nenhum alvo do teste."""
import copy
import hashlib
import json
from pathlib import Path
H=Path(__file__).resolve().parent

def main():
    anterior=json.loads((H.parent/'dialogo_v2_20261010/corpus_gru.json').read_text())
    exemplos=copy.deepcopy(anterior['exemplos'])
    # Canoniza companhia em @detalhe. @tema2 significa cenário em todos os atos.
    for e in exemplos:
        c=e['contexto']
        if c['acao']=='final' and 'detalhe' not in c['slots'] and 'tema2' in c['slots']:
            c['slots']['detalhe']=c['slots'].pop('tema2')
            e['resposta']=e['resposta'].replace('@tema2','@detalhe')
    arcos=[
        'Uma passagem apareceu. Juntos, consertaram a ponte. A viagem pôde continuar. A personagem agradeceu a ajuda.',
        'Um vento forte espalhou o mapa. Juntos, olharam o mapa. O caminho ficou claro. A viagem pôde continuar.',
        'Uma porta estava fechada. Juntos, procuraram uma chave. A personagem abriu a porta. Do outro lado havia um caminho.',
        'Uma chuva começou. Juntos, procuraram abrigo. Esperou a chuva passar. Depois retomou o caminho.',
        'Um bilhete apareceu. Juntos, resolveram o pedido. Depois procuraram quem precisava de ajuda. A busca começou.',
        'Um objeto apareceu. Juntos, procuraram quem havia perdido aquilo. Depois devolveram o objeto. A procura terminou com uma boa surpresa.',
        'Uma correnteza bloqueou o caminho. A personagem observou a água. Juntos, escolheram uma passagem segura. A travessia pôde continuar.',
        'Um som chamou a atenção. Juntos, procuraram a origem do som. Uma pista apareceu. A aventura pôde continuar.'
    ]
    novas=[]
    for variante,arco in enumerate(arcos):
        for cenario in (False,True):
            for n in range(24):
                val=n>=20
                # Nomes dos testes não entram nas demonstrações.
                pessoa=('uma irara aprendiz','um texugo curioso')[n%2] if not val else ('uma paca viajante','um furão curioso')[n%2]
                lugar=('um farol esquecido','uma floresta silenciosa')[n%2] if not val else ('uma casa antiga','um castelo vazio')[n%2]
                slots={'tema1':pessoa,'detalhe':'uma colega' if n%2 else 'um companheiro de viagem'}
                if cenario:slots['tema2']=lugar
                ident='companhia-%d-%d-%02d'%(variante,cenario,n)
                texto='Ficção: @tema1 continuou a viagem com @detalhe'+(' em @tema2.' if cenario else '.')+' '+arco
                ctx={'acao':'continuacao','slots':slots,'estilo':'neutro','variante':variante,
                     'mensagem':'Mostre a próxima parte com a companhia encontrada.',
                     'historico':['O encontro trouxe ajuda.'],'resposta_anterior':''}
                novas.append({'id':ident,'dialogo':ident,'familia':'companhia-autoral-'+str(variante),'split':'validacao' if val else 'treino','contexto':ctx,'resposta':texto,'origem':'Continuação escrita à mão, sem usar resposta alvo dos casos.'})
    exemplos+=novas
    import sys
    sys.path.insert(0,str(H.parent.parent))
    from linguagem_gerativa import tokenizar
    faltantes={t for e in novas for t in tokenizar(e['resposta'])}-set(anterior['vocabulario'])
    assert not faltantes, sorted(faltantes)
    out={'versao':3,'origem':'Corpus autoral focalizado em continuação com companhia; não conversas humanas.',
         'fontes_externas':False,'exemplos':exemplos,'vocabulario':anterior['vocabulario'],
         'limite':'Oito arcos compartilhados entre treino/validação; papéis e ato fornecidos pelo roteador, sem compreensão geral.'}
    p=H/'corpus_gru.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    audit={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'exemplos':len(exemplos),'novos':len(novas),
           'treino':sum(e['split']=='treino' for e in exemplos),'validacao':sum(e['split']=='validacao' for e in exemplos),
           'vocabulario':len(out['vocabulario']),'padroes_novos':len({e['resposta'] for e in novas}),
           'particao':'Diálogos completos e entidades novas separadas; oito arcos compartilhados.'}
    (H/'auditoria_corpus.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(audit)
if __name__=='__main__':main()
