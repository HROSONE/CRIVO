"""Adapta cabeças próprias; corpo/professor congelados. Teste fechado não lido."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import random
import time
import torch
from apoio import ROOT,ASSOC,CONTEXT,INICIAL,sha,escrever
from preparo import codificar
from rede import carregar
from corpus_memoria import supervisionar
from rede_eventos import coletar,medidas,macro_familias
from modelo import lote
from dados import EVENTOS
from tokenizers import Tokenizer

def macro_criticos(rows):
    return sum(sum(r['contrato'] for r in rows if r['evento']==ev and r['familia']==fam)/sum(r['evento']==ev and r['familia']==fam for r in rows)
               for ev in ['correcao','hipotese','retorno','confirmacao'] for fam in ['precos','requisitos'])/8

def loss_bancos(logits,bs,l):
    ys=torch.zeros_like(logits).view(len(bs),12,-1);valid=torch.tensor([c['bancos_validos'] for c in bs])
    for j,c in enumerate(bs):ys[j,:,:len(c['ids'])]=torch.tensor(c['bancos_targets'])
    v=logits.view(len(bs),12,-1);mask=torch.arange(v.shape[-1])[None,None,:]<l[:,None,None]
    pos=(ys>0)&mask;neg=(ys==0)&mask
    lp=(torch.nn.functional.softplus(-v)*pos).sum(-1)/pos.sum(-1).clamp_min(1)
    ln=(torch.nn.functional.softplus(v)*neg).sum(-1)/neg.sum(-1).clamp_min(1)
    return ((lp+ln)*.5)[valid].mean()

def main():
    p=argparse.ArgumentParser();p.add_argument('--laboratorio',type=Path,required=True)
    p.add_argument('--braco',choices=['controle','fontes'],required=True);p.add_argument('--retomar',action='store_true');a=p.parse_args()
    lab=a.laboratorio;proto=json.loads((lab/'protocolo.json').read_text());torch.set_num_threads(1);torch.manual_seed(proto['seed'])
    for n,h in proto['codigo'].items():assert sha(Path(__file__).parent/n)==h
    assert sha(INICIAL)==proto['inicial_sha256'];path=lab/proto['dados_dir'];ds={}
    tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));tok.encode_special_tokens=True;pad=tok.token_to_id('<pad>')
    for s in ['treino','dev','replay_associacao','replay_contextual']:
        assert sha(path/(s+'.json'))==proto['dados_sha256'][s]
        ds[s]=[supervisionar(codificar(tok,e)) for e in json.loads((path/(s+'.json')).read_text())]
    ad=[codificar(tok,e) for e in json.loads((ASSOC/'dados/dev.json').read_text())]
    cd=[codificar(tok,e) for e in json.loads((CONTEXT/'dados/dev.json').read_text())]
    m,metadata=carregar(tok);opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=proto['lr'],weight_decay=.01)
    groups={(ev,f):[i for i,c in enumerate(ds['treino']) if c['exemplo']['evento']==ev and c['exemplo']['familia']==f]
            for ev in EVENTOS for f in ['precos','requisitos']}
    rng=random.Random(152671);out=lab/a.braco;hist=[];best=None;nota=-1.;chosen=0;tokens=0;seen=set();step0=0;tempo0=0.
    assinatura={'protocolo_sha256':sha(lab/'protocolo.json'),'braco':a.braco,'auxiliar':0. if a.braco=='controle' else .3}
    if a.retomar:
        r=torch.load(out/'retomada.pt',map_location='cpu',weights_only=True);assert r['assinatura']==assinatura
        m.load_state_dict(r['modelo']);opt.load_state_dict(r['otimizador']);rng.setstate(r['rng_python']);torch.set_rng_state(r['rng_torch'])
        hist=r['historico'];best=r['melhor'];nota=r['nota'];chosen=r['escolhido'];tokens=r['tokens'];seen=set(r['vistos']);step0=r['passo'];tempo0=r['segundos']
    else:out.mkdir(exist_ok=False);escrever(out/'assinatura.json',assinatura)
    t0=time.monotonic()
    for step in range(step0+1,proto['passos']+1):
        inds=[('treino',rng.choice(groups[(ev,f)])) for ev in EVENTOS for f in ['precos','requisitos']]
        inds += [(s,rng.randrange(len(ds[s]))) for s in ['replay_associacao','replay_contextual'] for _ in range(4)]
        rng.shuffle(inds);seen.update(inds);bs=[ds[s][i] for s,i in inds];es=[c['exemplo'] for c in bs]
        m.train();x,l=lote(bs,pad);ls=m(x,l)
        loss=.8*torch.nn.functional.cross_entropy(ls['pontos'].reshape(-1,x.shape[1]),torch.tensor([c['pontos'] for c in bs]).reshape(-1))
        loss+=.5*torch.nn.functional.cross_entropy(ls['escopo'],torch.tensor([int(e['hipotese']) for e in es]),weight=torch.tensor([1.,2.]))
        ev=torch.tensor([EVENTOS.index(e['evento']) if e.get('evento') else -100 for e in es])
        loss+=.2*torch.nn.functional.cross_entropy(ls['evento'],ev,ignore_index=-100)
        bancos=loss_bancos(ls['validade'],bs,l)
        if assinatura['auxiliar']:loss+=assinatura['auxiliar']*bancos
        replay=torch.tensor([s!='treino' for s,i in inds]);kl=0.
        for k in ['escopo','pontos']:
            v=ls[k][replay];teacher=ls['original'][k][replay]
            if k=='pontos':v=v.reshape(-1,x.shape[1]);teacher=teacher.reshape(-1,x.shape[1])
            kl+=torch.nn.functional.kl_div(v.log_softmax(-1),teacher.softmax(-1),reduction='batchmean')
        loss+=.25*kl
        opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_([p for p in m.parameters() if p.requires_grad],1.);opt.step()
        tokens+=sum(len(c['ids']) for c in bs)
        if step%100==0:
            _,dv=coletar(m,ds['dev'],pad);_,av=coletar(m,ad,pad);_,cv=coletar(m,cd,pad)
            score=.6*macro_criticos(dv)+.25*macro_familias(av)+.15*macro_familias(cv)
            row={'passo':step,'nota':score,'dev':medidas(dv),'dev_associacao':medidas(av),'dev_contextual':medidas(cv),
                 'perda':float(loss.detach()),'perda_bancos':float(bancos.detach()),'segundos':tempo0+time.monotonic()-t0}
            hist.append(row)
            if score>nota:nota=score;best=deepcopy(m.state_dict());chosen=step;escrever(out/'dev_escolhido.json',dv)
            print(json.dumps({'passo':step,'nota':score,'dev':sum(r['contrato'] for r in dv),'n':len(dv),
                'associacao':sum(r['contrato'] for r in av),'contextual':sum(r['contrato'] for r in cv),'segundos':round(row['segundos'],2)}),flush=True)
            r={'assinatura':assinatura,'modelo':m.state_dict(),'otimizador':opt.state_dict(),'rng_python':rng.getstate(),'rng_torch':torch.get_rng_state(),
                'melhor':best,'nota':nota,'escolhido':chosen,'historico':hist,'tokens':tokens,'vistos':list(seen),'passo':step,'segundos':row['segundos']}
            tmp=out/'retomada.tmp';torch.save(r,tmp);tmp.replace(out/'retomada.pt');escrever(out/'progresso.json',hist)
    m.load_state_dict(best)
    # Backbone e cabeças herdadas precisam permanecer bit a bit iguais.
    for k,v in metadata['modelo'].items():assert torch.equal(m.state_dict()[k],v)
    torch.save({**metadata,'modelo':m.state_dict(),'cabecas_memoria':True,'passo_escolhido':chosen,'aprovado_para_chat':False},out/'pesos.pt')
    escrever(out/'relatorio.json',{'assinatura':assinatura,'passos_completos':proto['passos'],'passo_escolhido':chosen,'historico':hist,
        'tokens_apresentados':tokens,'entradas_distintas':len(seen),'segundos':tempo0+time.monotonic()-t0,
        'parametros':sum(p.numel() for p in m.parameters()),'parametros_treinaveis':sum(p.numel() for p in m.parameters() if p.requires_grad),
        'corpo_e_cabecas_antigas_preservadas':True,'pesos_sha256':sha(out/'pesos.pt'),'teste_lido_no_treino':False,
        'pesos_externos':False,'supervisao_redacao_livre':False,'aprovado_para_chat':False})
    print('Concluído; sem ativação automática.',flush=True)

if __name__=='__main__':main()
