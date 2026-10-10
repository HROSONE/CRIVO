"""Greedy de sequências de validação, sem professor após o primeiro trecho."""
import argparse
import copy
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent.parent))
from linguagem_gerativa import GeradorGRU,renderizar,tokenizar

def avaliar(checkpoint,saida):
    data=json.loads(gzip.decompress(Path(checkpoint).read_bytes()));modelo=GeradorGRU(data)
    corpus=json.loads((H/'corpus_gru.json').read_text());grupos=defaultdict(list)
    for e in corpus['exemplos']:
        if e['split']=='validacao' and e['dialogo'].startswith('sequencia-'):grupos[e['dialogo']].append(e)
    rows=[]
    for nome,exemplos in sorted(grupos.items()):
        anterior=exemplos[0]['contexto']['resposta_anterior'];recentes=[]
        for e in exemplos:
            ctx=copy.deepcopy(e['contexto']);ctx['resposta_anterior']=anterior
            g=modelo.gerar(ctx,max_tokens=128);texto=renderizar(g,ctx['slots'])
            ideal=tokenizar(e['resposta']);cego=modelo.gerar(dict(ctx,resposta_anterior=''),max_tokens=128)
            rows.append({'dialogo':nome,'id':e['id'],'completa':g['completa'],'correta':g['tokens']==ideal,
                         'sem_anterior_correta':cego['tokens']==ideal,'repetida':texto in recentes,
                         'referentes_presentes':all(v in texto for v in ctx['slots'].values()),
                         'resposta':texto})
            recentes.append(texto);anterior=texto
    out={'checkpoint_sha256':hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest(),
         'controle':data['controle'],'sequencias':len(grupos),'total':len(rows),
         'corretas':sum(r['correta'] for r in rows),'sem_anterior_corretas':sum(r['sem_anterior_correta'] for r in rows),
         'repetidas':sum(r['repetida'] for r in rows),'referentes_ausentes':sum(not r['referentes_presentes'] for r in rows),
         'resultados':rows,'limite':'Oito estágios compartilhados no treino/validação. Esta ablação mede leitura de trecho dentro desses padrões, não generalização de enredo.'}
    Path(saida).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in out.items() if k!='resultados'},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--saida',required=True);a=p.parse_args();avaliar(a.checkpoint,a.saida)
