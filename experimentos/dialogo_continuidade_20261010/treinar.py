"""Segundo treino próprio, isolado; nenhuma aprovação automática."""
import gzip
import hashlib
import json
import math
import sys
import time
from pathlib import Path
import numpy as np

H=Path(__file__).resolve().parent;ROOT=H.parent.parent
sys.path.insert(0,str(ROOT))
from linguagem_gerativa import assinatura_atributos
from treinar_geracao import inicializar,lote,perda_gradientes,regularizar_contexto,assinatura

def main(destino=None):
    corpus=H/'corpus_gru.json';d=json.loads(corpus.read_text());vocab=d['vocabulario'];idx={t:i for i,t in enumerate(vocab)}
    basepath=H/'checkpoint_base_128.json.gz'
    assert hashlib.sha256(basepath.read_bytes()).hexdigest()=='566cf4387d27b6e880cee2ad60c9668e8d7d8cbd40748272e84e753a60b0c646'
    base=json.loads(gzip.decompress(basepath.read_bytes()))
    tr=[e for e in d['exemplos'] if e['split']=='treino'];val=[e for e in d['exemplos'] if e['split']=='validacao']
    p=inicializar(vocab,base['ocultos'],base['embeddings'],20261012);oldidx={t:i for i,t in enumerate(base['vocabulario'])}
    for k in p:
        if k not in ('E','O','bo'):p[k]=np.asarray(base['pesos'][k],dtype='float32')
    for j,t in enumerate(vocab):
        if t in oldidx:
            i=oldidx[t];p['E'][j]=base['pesos']['E'][i];p['O'][:,j]=np.asarray(base['pesos']['O'],dtype='float32')[:,i];p['bo'][j]=base['pesos']['bo'][i]
    parametros=sum(a.size for a in p.values());assert parametros<=85581
    m,v=({k:np.zeros_like(a) for k,a in p.items()} for _ in range(2));rng=np.random.default_rng(20261012)
    passo=0;hist=[];melhor=float('inf');best=None;inicio=time.monotonic()
    def perda_val():
        perdas=[];tokens=[]
        for pos in range(0,len(val),48):
            f,x,y,mascara=lote(val[pos:pos+48],idx);loss,_=perda_gradientes(p,f,x,y,mascara)
            perdas.append(loss*mascara.sum());tokens.append(mascara.sum())
        return float(sum(perdas)/sum(tokens))
    inicial=perda_val();print('parâmetros',parametros,'val inicial',inicial,flush=True)
    for ep in range(1,25):
        ordem=rng.permutation(len(tr));losses=[]
        for pos in range(0,len(tr),48):
            f,x,y,mascara=lote([tr[i] for i in ordem[pos:pos+48]],idx);f=regularizar_contexto(f,rng,.4,.15)
            loss,grads=perda_gradientes(p,f,x,y,mascara);assert math.isfinite(loss)
            escala=min(1.,5/max(1e-9,math.sqrt(sum(float((g*g).sum()) for g in grads.values()))));passo+=1;losses.append(loss)
            for k in p:
                g=grads[k]*escala;m[k]=.9*m[k]+.1*g;v[k]=.999*v[k]+.001*g*g
                p[k]-=.0015*(m[k]/(1-.9**passo))/(np.sqrt(v[k]/(1-.999**passo))+1e-8)
        lv=perda_val();hist.append({'epoca':ep,'treino':sum(losses)/len(losses),'validacao':lv})
        if lv<melhor:melhor=lv;best={k:a.copy() for k,a in p.items()};selecionada=ep
        print('época',ep,'val',round(lv,4),'segundos',round(time.monotonic()-inicio,1),flush=True)
    config={'epocas':24,'epoca_selecionada':selecionada,'parametros':parametros,'semente':20261012,'lote':48,
        'taxa':.0015,'dropout_texto':.4,'mistura_texto':.15,'clip':5,'exemplos':len(tr),'validacao':len(val)}
    meta={'versao':1,'arquitetura':'GRU condicional autoregressiva própria','assinatura_atributos':assinatura_atributos(),
        'assinatura_treino':assinatura(tr),'vocabulario':vocab,'ocultos':base['ocultos'],'embeddings':base['embeddings'],
        'pesos':{k:np.round(a.astype('float64'),7).tolist() for k,a in best.items()},
        'controle':{'aprovado':False,'ativo_no_chat':False},'base_sha256':hashlib.sha256(basepath.read_bytes()).hexdigest(),
        'corpus_sha256':hashlib.sha256(corpus.read_bytes()).hexdigest(),'treino':config,
        'limite':'Continuações autorais com companhia e cenário preservados, sem compreensão geral de histórico. Não aprovado para produção.'}
    raw=json.dumps(meta,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    dest=Path(destino) if destino else H/'checkpoint_gru_dialogo.json.gz';dest.write_bytes(gzip.compress(raw,mtime=0))
    report={'config':config,'inicial_validacao':inicial,'historico':hist,'segundos':round(time.monotonic()-inicio,2),
        'checkpoint_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'aprovado':False}
    report_path=Path(str(dest)+'.treino.json') if destino else H/'treino.json'
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--destino');main(parser.parse_args().destino)
