"""Política de desenvolvimento usada nos diagnósticos; não instala pesos."""
import sys,json,random,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from leitura_ficha import TRACOS,ABSOLUTOS,pergunta_direta
from composicao_textual import normalizar


def tradicional(c,z):
    p=1/(1+np.exp(-z));i=int(np.argmax(p));t=dict(zip(TRACOS,c['x'][i]))
    from leitura_ficha import pode_aproximar
    t['pergunta_direta']=pergunta_direta(c['pergunta'])
    if p[i]>=.5 and t['todas'] and not t['tipo_sem_par']:return 'afirmar',i
    if p[i]>=.55 and pode_aproximar(t,True):return 'aproximar',i
    return 'calar',i

def rescatar(c,p,limiar,margem):
    q=normalizar(c['pergunta'])
    if not pergunta_direta(c['pergunta']) or re.search(r'\b(?:nao|nem|nunca|jamais)\b',q):return None
    if any(ABSOLUTOS.match(w) for w in re.findall(r'[a-z]+',q)):return None
    i=int(np.argmax(p));t=dict(zip(TRACOS,c['x'][i]))
    if t['tipo_sem_par']:return None
    second=max([0.]+[float(v) for j,v in enumerate(p) if i!=j])
    if p[i]<limiar or p[i]-second<margem:return None
    return i

def aggregate(records):
    counts={'afirmados_certos':0,'afirmados_errados':0,'aproximados_certos':0,'aproximados_errados':0,'aproximados_nulos':0,'resgates_certos':0,'resgates_errados':0,'resgates_nulos':0,'recusados':0}
    for r in records:
        c,base,i,action,chosen,is_rescue=r;alvo=c['fato']
        if action=='afirmar':counts['afirmados_certos' if alvo==chosen else 'afirmados_errados']+=1
        elif action=='aproximar':
            kind='certos' if alvo==chosen else 'nulos' if alvo is None else 'errados'
            counts['aproximados_'+kind]+=1
            if is_rescue:counts['resgates_'+kind]+=1
        else:counts['recusados']+=1
    counts['certos_entregues']=counts['afirmados_certos']+counts['aproximados_certos']
    return counts

def run(cs,indices,preds,base,limiar,margem):
    records=[]
    for k,p,z in zip(indices,preds,base):
        c=cs[k];action,i=tradicional(c,z);rescue=rescatar(c,p,limiar,margem) if action=='calar' else None
        records.append((c,action,i,'aproximar' if rescue is not None else action,rescue if rescue is not None else i,rescue is not None))
    return records
