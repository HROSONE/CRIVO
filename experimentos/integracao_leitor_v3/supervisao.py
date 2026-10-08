"""Supervisão do calibrador: previsões internas, nunca o teste externo."""
import json
from pathlib import Path
import numpy as np
import politica_desenvolvimento as c
cs=json.loads((Path(__file__).resolve().parent/'tracos_desenvolvimento.json').read_text(encoding='utf-8'))


def examples(ids,pp,bb):
    xx=[]; yy=[]; rows=[]
    for k,p,z in zip(ids,pp,bb):
        case=cs[int(k)];p=np.asarray(p,dtype=float);z=np.asarray(z,dtype=float)
        act,i=c.tradicional(case,z)
        if act!='calar':continue
        j=c.rescatar(case,p,0.,0.)
        if j is None:continue
        lex=1/(1+np.exp(-z));second=max([0.]+[float(v) for h,v in enumerate(p) if h!=j]);x=case['x'][j]
        # Nenhuma identidade de assunto ou pergunta entra no calibrador.
        vals=[1.,p[j],p[j]-second,lex[j],lex[j]-max(lex),x[3],x[4],x[5],x[6],x[7],x[8],x[9],x[10],x[11],x[12],x[13],x[14],x[15],x[16],x[17],np.log1p(len(p))/3]
        xx.append(vals);yy.append(case['fato']==j);rows.append((int(k),j))
    return np.asarray(xx,dtype=float),np.asarray(yy,dtype=float),rows
