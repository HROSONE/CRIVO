import os
"""Experimento de adaptação das duas últimas camadas com perguntas revisadas.

Somente desenvolvimento por assunto; testes congelados ficam fora de todo treino.
Cache determinístico das seis camadas congeladas evita repetir seu cálculo.
"""
import sys,json,random,time,copy
from pathlib import Path
import numpy as np
import torch
ROOT=Path(os.environ['CRIVO_REPO']);OUT=Path(os.environ['CRIVO_SAIDA'])
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(OUT),str(Path(__file__).resolve().parent)]
from continuar_leitor import carregar,configurar_ajuste,perda_grupo,exportar
from scripts.treinar_leitor_transformer import lote_tensores
from diagnosticar_cabeca import metricas

def predizer(m,cache,indices):
    m.eval();out=[]
    with torch.no_grad():
        for i in indices:
            x,u=cache[i];h=x
            for block in m.base.blocos[-2:]:h=block(h)
            out.append(m.cabeca(m.base.norm(h)[torch.arange(len(h)),u]).squeeze(-1).numpy())
    return out

def treinar(m,cache,cases,train,dev,steps=200):
    configurar_ajuste(m,2)
    rng=random.Random(20261008);torch.manual_seed(20261008)
    opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=5e-5,weight_decay=.01)
    selected={k:v.detach().clone() for k,v in m.state_dict().items() if k.startswith(('base.blocos.6.','base.blocos.7.','base.norm.','cabeca.'))}
    baseline=metricas(predizer(m,cache,dev),[cases[i] for i in dev]) if dev else None
    best=(baseline['acerto_fato']+baseline['auc_respondivel']) if baseline else -1
    pos=[i for i in train if cases[i]['fato'] is not None];neg=[i for i in train if cases[i]['fato'] is None]
    chosen_step=0;history=[];start=time.monotonic()
    for step in range(1,steps+1):
        sample=[rng.choice(neg if rng.random()<.25 else pos) for _ in range(8)]
        total=sum(len(cache[i][0]) for i in sample);t=max(cache[i][0].shape[1] for i in sample)
        h=torch.zeros((total,t,m.base.config.dimensao));last=torch.empty(total,dtype=torch.long);ranges=[];offset=0
        for i in sample:
            x,u=cache[i];n=len(x);h[offset:offset+n,:x.shape[1]]=x;last[offset:offset+n]=u
            ranges.append((offset,offset+n,cases[i]['fato']));offset+=n
        m.train();opt.zero_grad(set_to_none=True)
        for block in m.base.blocos[-2:]:h=block(h)
        z=m.cabeca(m.base.norm(h)[torch.arange(total),last]).squeeze(-1)
        loss=torch.stack([perda_grupo(z[a:b],alvo) for a,b,alvo in ranges]).mean()
        if not torch.isfinite(loss):raise RuntimeError('Perda não finita')
        loss.backward();torch.nn.utils.clip_grad_norm_([p for p in m.parameters() if p.requires_grad],1.)
        opt.step()
        if step%25==0 or step==steps:
            met=metricas(predizer(m,cache,dev),[cases[i] for i in dev]) if dev else None
            print('passo',step,'perda',round(float(loss.detach()),4),'dev',met,'segundos',round(time.monotonic()-start,1),flush=True)
            if met:
                score=met['acerto_fato']+met['auc_respondivel']
                # Seleção por métrica conjunta de desenvolvimento; ganho de ranking
                # não autoriza regressão na separação de perguntas sem resposta.
                good=all(met[k]>=baseline[k] for k in ('acerto_fato','auc_respondivel'))
                if good and score>best:
                    best=score;chosen_step=step
                    selected={k:v.detach().clone() for k,v in m.state_dict().items() if k in selected}
                history.append({'passo':step,'metricas':met})
    if dev:m.load_state_dict(selected,strict=False)
    return chosen_step,history

def main():
    torch.set_num_threads(2);torch.manual_seed(20261008)
    from crivo import Crivo
    comp=Crivo().compositor
    cases=json.loads((ROOT/'dados/leitura_ficha_tutor.json').read_text())['casos']
    cases=[c for c in cases if c['assunto'] in comp.itens]
    origin=ROOT/'experimentos/pesos_base/leitor_transformer'
    base,bpe,meta=carregar(origin,'cpu');base.eval()
    path=OUT/'cache_seis_camadas.pt'
    if path.exists():cache=torch.load(path,weights_only=True)
    else:
        cache=[]
        with torch.no_grad():
            for i,c in enumerate(cases):
                facts=[f['texto'] for f in comp.itens[c['assunto']]['fatos']]
                ids,u=lote_tensores([(c['pergunta'],f) for f in facts],bpe,256,'cpu')
                h=base.base.embedding(ids)+base.base.posicao(torch.arange(ids.shape[1]))
                for block in base.base.blocos[:-2]:h=block(h)
                cache.append((h.detach(),u))
                if i%50==0:print('cache inferior',i,flush=True)
        torch.save(cache,path)
    subjects=sorted({c['assunto'] for c in cases});random.Random(20261008).shuffle(subjects)
    fold={s:i%5 for i,s in enumerate(subjects)}
    pred0=predizer(base,cache,list(range(len(cases))))
    predictions=[None]*len(cases);selections=[]
    for outer in range(5):
        allowed=[s for s in subjects if fold[s]!=outer]
        # Dev por assunto fixado antes do treino, cerca de 20% dos assuntos permitidos.
        dev_subjects=set(allowed[::5])
        train=[i for i,c in enumerate(cases) if fold[c['assunto']]!=outer and c['assunto'] not in dev_subjects]
        dev=[i for i,c in enumerate(cases) if c['assunto'] in dev_subjects]
        test=[i for i,c in enumerate(cases) if fold[c['assunto']]==outer]
        m=copy.deepcopy(base)
        print('BLOCO',outer,'treino',len(train),'dev',len(dev),'externo',len(test),flush=True)
        step,history=treinar(m,cache,cases,train,dev)
        scores=predizer(m,cache,test)
        for i,p in zip(test,scores):predictions[i]=p
        selections.append({'bloco':outer,'passo_escolhido':step,'historico_dev':history})
        print('resultado externo',outer,metricas(scores,[cases[i] for i in test]),flush=True)
        del m
    report={'protocolo':'Desenvolvimento em cinco blocos por assunto; parada escolhida em dev interno por assunto; dados humanos tutor usados como supervisão; congelados não usados','baseline':metricas(pred0,cases),'validacao_externa':metricas(predictions,cases),'selecao':selections,'aprovado':False}
    (OUT/'controle_duas_camadas.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (OUT/'predicoes_duas_camadas.json').write_text(json.dumps([{'assunto':c['assunto'],'alvo':c['fato'],'baseline':a.tolist(),'candidato':b.tolist()} for c,a,b in zip(cases,pred0,predictions)]))
    print(json.dumps(report,ensure_ascii=False),flush=True)
    horizon=int(np.median([s['passo_escolhido'] for s in selections]))
    if horizon:
        m=copy.deepcopy(base);treinar(m,cache,cases,list(range(len(cases))),[],horizon)
        exportar(m,origin,OUT/'candidato_duas_camadas',meta,horizon,report['validacao_externa'],report['baseline'])
        mp=OUT/'candidato_duas_camadas/meta.json';metadata=json.loads(mp.read_text())
        metadata['adaptacao_revisada']={'dados':'perguntas humanas tutor; supervisão com validação agrupada por assunto','controle':report,'horizonte_medido':horizon}
        mp.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
