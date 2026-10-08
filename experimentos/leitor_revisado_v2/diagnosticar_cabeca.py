import os
"""Controle por assunto para adaptação apenas da cabeça do leitor próprio.

O tutor é agora supervisão: nunca anunciar sua pontuação de treino como teste.
Os cinco blocos externos recebem previsões de cabeças que não viram seu assunto.
Regularização escolhida em quatro blocos internos, também separados por assunto.
"""
import sys,json,hashlib,time,random
from pathlib import Path
import numpy as np
import torch
ROOT=Path(os.environ['CRIVO_REPO'])
OUT=Path(os.environ['CRIVO_SAIDA'])
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(Path(__file__).resolve().parent)]
from continuar_leitor import carregar,exportar
from scripts.treinar_leitor_transformer import lote_tensores

def metricas(pred,grupos):
    certos=0;pos=[];neg=[]
    for z,c in zip(pred,grupos):
        a=c['fato'];k=int(np.argmax(z));p=float(torch.sigmoid(torch.tensor(z[k])))
        if a is None:neg.append(p)
        else:pos.append(p);certos+=k==a
    auc=sum((a>b)+.5*(a==b) for a in pos for b in neg)/max(1,len(pos)*len(neg))
    return dict(acerto_fato=certos/max(1,len(pos)),auc_respondivel=auc,certos=certos,respondiveis=len(pos),sem_resposta=len(neg))

def treinar(xs,cs,indices,w0,b0,l2):
    # CE agrupada com opção fixa nenhuma + BCE; não mistura grupos de fichas.
    w=torch.tensor(w0,requires_grad=True);b=torch.tensor(b0,requires_grad=True)
    opt=torch.optim.LBFGS([w,b],lr=.5,max_iter=80,line_search_fn='strong_wolfe')
    x=torch.cat([xs[i] for i in indices]);ys=[];ranges=[];start=0
    for i in indices:
        n=len(xs[i]);a=cs[i]['fato'];y=torch.zeros(n)
        if a is not None:y[a]=1
        ys.append(y);ranges.append((start,start+n,n if a is None else a));start+=n
    y=torch.cat(ys);group_weights=torch.cat([torch.full((len(xs[i]),),1/len(xs[i])) for i in indices])
    init=torch.tensor(w0)
    def closure():
        opt.zero_grad();z=x@w+b
        rank=torch.stack([torch.nn.functional.cross_entropy(torch.cat((z[a:e],z.new_zeros(1)))[None],torch.tensor([target])) for a,e,target in ranges]).mean()
        binary=(torch.nn.functional.binary_cross_entropy_with_logits(z,y,reduction='none')*group_weights).sum()/len(indices)
        loss=rank+.5*binary+l2*((w-init).square().sum()+(b-b0).square())
        loss.backward();return loss
    opt.step(closure)
    return w.detach(),b.detach()

def main():
    torch.set_num_threads(2);torch.manual_seed(20261008)
    cases=json.loads((ROOT/'dados/leitura_ficha_tutor.json').read_text())['casos']
    from crivo import Crivo
    comp=Crivo().compositor
    cases=[c for c in cases if c['assunto'] in comp.itens]
    origem=ROOT/'experimentos/pesos_base/leitor_transformer'
    m,bpe,meta=carregar(origem,'cpu');m.eval()
    cache=OUT/'ocultos_tutor.npz'
    corpus=[dict(c,fatos=[f['texto'] for f in comp.itens[c['assunto']]['fatos']]) for c in cases]
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'linguagem_profunda.py',ROOT/'leitor_transformer.py',origem/'tokenizer.json']}
    signature=hashlib.sha256((origem/'pesos_numpy.npz').read_bytes()+json.dumps([corpus,sources,str(torch.__version__)],sort_keys=True).encode()).hexdigest()
    if cache.exists():
        z=np.load(cache,allow_pickle=False)
        if str(z['assinatura'])!=signature:raise ValueError('Cache incompatível')
        xs=[torch.from_numpy(z['x'+str(i)]) for i in range(len(cases))]
    else:
        xs=[]
        with torch.no_grad():
            for i,c in enumerate(cases):
                fatos=[f['texto'] for f in comp.itens[c['assunto']]['fatos']]
                ids,u=lote_tensores([(c['pergunta'],f) for f in fatos],bpe,256,'cpu')
                base=m.base;x=base.embedding(ids)+base.posicao(torch.arange(ids.shape[1]))
                for bloco in base.blocos:x=bloco(x)
                h=base.norm(x)[torch.arange(len(ids)),u].detach().cpu()
                xs.append(h)
                if i%25==0:print('extração',i,'/',len(cases),flush=True)
        np.savez_compressed(cache,assinatura=np.array(signature),**{'x'+str(i):x.numpy() for i,x in enumerate(xs)})
    w0=m.cabeca.weight.detach()[0].numpy().copy();b0=float(m.cabeca.bias.detach()[0])
    subjects=sorted({c['assunto'] for c in cases});random.Random(20261008).shuffle(subjects)
    fold={s:i%5 for i,s in enumerate(subjects)}
    pred0=[(x@torch.tensor(w0)+b0).numpy() for x in xs]
    print('baseline',metricas(pred0,cases),flush=True)
    # Grade estabelecida antes de observar quaisquer resultados externos.
    grade=[.03,.1,.3,1.,3.];pred=[None]*len(cases);selection=[]
    for outer in range(5):
        train=[i for i,c in enumerate(cases) if fold[c['assunto']]!=outer]
        test=[i for i,c in enumerate(cases) if fold[c['assunto']]==outer]
        inner_subjects=[s for s in subjects if fold[s]!=outer]
        inner={s:i%4 for i,s in enumerate(inner_subjects)}
        scores=[]
        for reg in grade:
            ip=[];ic=[]
            for k in range(4):
                tr=[i for i in train if inner[cases[i]['assunto']]!=k]
                va=[i for i in train if inner[cases[i]['assunto']]==k]
                w,b=treinar(xs,cases,tr,w0,b0,reg)
                ip.extend([(xs[i]@w+b).numpy() for i in va]);ic.extend([cases[i] for i in va])
            met=metricas(ip,ic);scores.append((met['acerto_fato']+met['auc_respondivel'],reg,met))
        _,reg,inner_met=max(scores,key=lambda r:(r[0],r[1]))
        w,b=treinar(xs,cases,train,w0,b0,reg)
        for i in test:pred[i]=(xs[i]@w+b).numpy()
        selection.append({'bloco':outer,'l2':reg,'validacao_interna':inner_met,'assuntos_externos':[s for s in subjects if fold[s]==outer]})
        print('bloco',outer,'l2',reg,'teste',metricas([pred[i] for i in test],[cases[i] for i in test]),flush=True)
    report={'protocolo':'5 blocos externos por assunto; seleção L2 em 4 blocos internos; somente cabeça linear adaptada; tutor agora supervisão; testes congelados não usados','baseline':metricas(pred0,cases),'validacao_externa':metricas(pred,cases),'selecao':selection,'origem_sha256':hashlib.sha256((origem/'pesos_numpy.npz').read_bytes()).hexdigest(),'corpus_sha256':hashlib.sha256(json.dumps(corpus,sort_keys=True).encode()).hexdigest(),'fontes':sources,'execucao':{'torch':str(torch.__version__),'numpy':str(np.__version__),'dispositivo':'cpu','semente':20261008},'aprovado':False}
    wins=losses=0
    for c,a,b in zip(cases,pred0,pred):
        if c['fato'] is None:continue
        old=int(a.argmax())==c['fato'];new=int(b.argmax())==c['fato']
        wins+=new and not old;losses+=old and not new
    report['pares_acerto']={'ganhos':wins,'perdas':losses}
    (OUT/'controle_cabeca.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (OUT/'predicoes_externas.json').write_text(json.dumps([{'assunto':c['assunto'],'alvo':c['fato'],'baseline':a.tolist(),'candidato':b.tolist()} for c,a,b in zip(cases,pred0,pred)]))
    print(json.dumps(report,ensure_ascii=False),flush=True)
    # A regularização final usa somente a seleção interna, nunca resultados externos.
    reg=float(np.median([r['l2'] for r in selection]));w,b=treinar(xs,cases,list(range(len(cases))),w0,b0,reg)
    with torch.no_grad():m.cabeca.weight.copy_(w[None]);m.cabeca.bias.copy_(b[None])
    exportar(m,origem,OUT/'candidato_cabeca',meta,0,report['validacao_externa'],report['baseline'])
    candidate_meta=json.loads((OUT/'candidato_cabeca/meta.json').read_text())
    candidate_meta.pop('ajuste_contrastivo',None)
    candidate_meta['adaptacao_cabeca']={'parametros_treinados':385,'l2':reg,'dados':'tutor como supervisão, validação cruzada aninhada por assunto; base totalmente congelada','controle':report}
    candidate_meta['controle']={'aprovado':False,'criterio':'Requer ganho end-to-end sem mais erros nos controles congelados.'}
    (OUT/'candidato_cabeca/meta.json').write_text(json.dumps(candidate_meta,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
