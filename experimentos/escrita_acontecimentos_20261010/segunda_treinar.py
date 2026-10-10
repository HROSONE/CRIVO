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
from treinar_geracao import inicializar,lote,perda_gradientes,assinatura

def main(destino=None, epocas=32):
    corpus=H/'corpus_gru.json';d=json.loads(corpus.read_text());vocab=d['vocabulario'];idx={t:i for i,t in enumerate(vocab)}
    basepath=H/'preliminar_checkpoint_gru_dialogo.json.gz'
    assert hashlib.sha256(basepath.read_bytes()).hexdigest()=='832473e4ec3fecab120e9e1625f135044a429fd20ff1798ab550740b6e62a8bc'
    base=json.loads(gzip.decompress(basepath.read_bytes()))
    tr=[e for e in d['exemplos'] if e['split']=='treino'];val=[e for e in d['exemplos'] if e['split']=='validacao']
    embedding=base['embeddings']
    while sum(a.size for a in inicializar(vocab,base['ocultos'],embedding,20261014).values())>85581:
        embedding-=1
    assert embedding>=1
    p=inicializar(vocab,base['ocultos'],embedding,20261014);oldidx={t:i for i,t in enumerate(base['vocabulario'])}
    for k in p:
        if k not in ('E','O','bo'):
            antigo=np.asarray(base['pesos'][k],dtype='float32')
            p[k]=np.concatenate((antigo[:embedding],antigo[base['embeddings']:]),axis=0) if k in ('Wz','Wr','Wn') else antigo
    p['F'][64:128]*=1
    for j,t in enumerate(vocab):
        if t in oldidx:
            i=oldidx[t];p['E'][j]=base['pesos']['E'][i][:embedding];p['O'][:,j]=np.asarray(base['pesos']['O'],dtype='float32')[:,i];p['bo'][j]=base['pesos']['bo'][i]
    parametros=sum(a.size for a in p.values());assert parametros<=85581
    m,v=({k:np.zeros_like(a) for k,a in p.items()} for _ in range(2));rng=np.random.default_rng(20261014)
    passo=0;hist=[];melhor=float('inf');best=None;inicio=time.monotonic()
    def perda_val():
        perdas=[];tokens=[]
        for pos in range(0,len(val),48):
            f,x,y,mascara=lote(val[pos:pos+48],idx);loss,_=perda_gradientes(p,f,x,y,mascara)
            perdas.append(loss*mascara.sum());tokens.append(mascara.sum())
        return float(sum(perdas)/sum(tokens))
    inicial=perda_val();print('parâmetros',parametros,'val inicial',inicial,flush=True)
    for ep in range(1,epocas+1):
        ordem=rng.permutation(len(tr));losses=[]
        for pos in range(0,len(tr),48):
            f,x,y,mascara=lote([tr[i] for i in ordem[pos:pos+48]],idx);# O trecho anterior determina o alvo: não pode ser misturado/apagado.
            loss,grads=perda_gradientes(p,f,x,y,mascara);assert math.isfinite(loss)
            escala=min(1.,5/max(1e-9,math.sqrt(sum(float((g*g).sum()) for g in grads.values()))));passo+=1;losses.append(loss)
            for k in p:
                g=grads[k]*escala;m[k]=.9*m[k]+.1*g;v[k]=.999*v[k]+.001*g*g
                p[k]-=.0015*(m[k]/(1-.9**passo))/(np.sqrt(v[k]/(1-.999**passo))+1e-8)
        lv=perda_val();hist.append({'epoca':ep,'treino':sum(losses)/len(losses),'validacao':lv})
        if lv<melhor:melhor=lv;best={k:a.copy() for k,a in p.items()};selecionada=ep
        print('época',ep,'val',round(lv,4),'segundos',round(time.monotonic()-inicio,1),flush=True)
    config={'epocas':epocas,'epoca_selecionada':selecionada,'parametros':parametros,'semente':20261014,'lote':48,
        'taxa':.0015,'dropout_texto':0,'mistura_texto':0,'embeddings':embedding,'escala_inicial_ato_semantico':1,'clip':5,'exemplos':len(tr),'validacao':len(val)}
    meta={'versao':1,'arquitetura':'GRU condicional autoregressiva própria','assinatura_atributos':assinatura_atributos(),
        'assinatura_treino':assinatura(tr),'vocabulario':vocab,'ocultos':base['ocultos'],'embeddings':embedding,
        'pesos':{k:np.round(a.astype('float64'),7).tolist() for k,a in best.items()},
        'controle':{'aprovado':False,'ativo_no_chat':False},'base_sha256':hashlib.sha256(basepath.read_bytes()).hexdigest(),
        'corpus_sha256':hashlib.sha256(corpus.read_bytes()).hexdigest(),'treino':config,
        'limite':'Acontecimentos autorais com reação e final condicionado; dez classes compartilhadas. Não comprova planejamento nem compreensão geral de histórico. Não aprovado para produção.'}
    raw=json.dumps(meta,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    dest=Path(destino) if destino else H/'checkpoint_gru_dialogo.json.gz';dest.write_bytes(gzip.compress(raw,mtime=0))
    report={'config':config,'inicial_validacao':inicial,'historico':hist,'segundos':round(time.monotonic()-inicio,2),
        'checkpoint_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'aprovado':False}
    report_path=Path(str(dest)+'.treino.json') if destino else H/'treino.json'
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--destino');parser.add_argument('--epocas',type=int,default=32);args=parser.parse_args();main(args.destino,args.epocas)
