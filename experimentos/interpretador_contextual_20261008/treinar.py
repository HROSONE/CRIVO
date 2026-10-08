"""Treinar somente treino/dev; nunca abre o arquivo teste.json."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys
import time
import torch
from corpus import OPERACOES, CLASSES, escrever
from modelo import Interprete, codificar, lote, proposta, conferir, executar, esperado, metricas


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@torch.no_grad()
def avaliar(modelo, itens, pad):
    modelo.eval(); rows=[]
    for i in range(0,len(itens),32):
        batch=itens[i:i+32]; x,l=lote(batch,pad); logits=modelo(x,l)
        for j,item in enumerate(batch):
            e=item['exemplo']; r={'sessao':e['sessao'],'familia':e['familia'],'etapa':e['etapa']}
            if modelo.braco == 'contextual':
                p=proposta(item,logits,j); c=conferir(e,p); out=executar(p); gold=esperado(e)
                r.update(c); r.update(proposta=p,execucao=out,
                    resultado_correto=out.get('resultado')==gold.get('resultado') and p['hipotese']==e['hipotese'])
            else:
                label=CLASSES[int(logits['operacao'][j].argmax())]
                r.update(classe_predita=label,classe_correta=label==e['classe'],contrato=label==e['classe'])
            rows.append(r)
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('braco',choices=['controle','contextual']);p.add_argument('saida',type=Path)
    p.add_argument('--raiz',type=Path,required=True);p.add_argument('--dados',type=Path,required=True)
    p.add_argument('--passos',type=int,default=600);args=p.parse_args()
    args.saida.mkdir(parents=True,exist_ok=False);torch.set_num_threads(1);torch.manual_seed(20261009)
    sys.path.insert(0,str(args.raiz));from linguagem_profunda import carregar
    base=args.raiz/'artefatos/linguagem_profunda';corpo,tok,_=carregar(base)
    pad=tok.token_to_id('<pad>');manifest=json.loads((args.dados/'manifesto.json').read_text())
    dados={}
    for s in ['treino','dev']:
        assert sha(args.dados/(s+'.json'))==manifest['sha256'][s]
        dados[s]=[codificar(tok,e) for e in json.loads((args.dados/(s+'.json')).read_text())]
    modelo=Interprete(corpo,args.braco)
    opt=torch.optim.AdamW(modelo.parameters(),lr=1e-4,weight_decay=.01)
    rng=random.Random(8419);hist=[];melhor=None;nota=-1.;inicio=time.monotonic();tokens=0;vistos=set()
    for passo in range(1,args.passos+1):
        modelo.train();inds=[rng.randrange(len(dados['treino'])) for _ in range(16)]
        batch=[dados['treino'][i] for i in inds];x,l=lote(batch,pad);logits=modelo(x,l)
        e=[i['exemplo'] for i in batch];classes=OPERACOES if args.braco=='contextual' else CLASSES
        y=torch.tensor([classes.index(c['operacao' if args.braco=='contextual' else 'classe']) for c in e])
        loss=torch.nn.functional.cross_entropy(logits['operacao'],y)
        if args.braco=='contextual':
            target=torch.tensor([i['pontos'] for i in batch])
            loss=loss + .2*torch.nn.functional.cross_entropy(logits['escopo'],torch.tensor([int(c['hipotese']) for c in e]))
            loss=loss + .8*torch.nn.functional.cross_entropy(logits['pontos'].reshape(-1,x.shape[1]),target.reshape(-1))
        opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(modelo.parameters(),1.);opt.step()
        tokens+=sum(len(i['ids']) for i in batch);vistos.update(inds)
        if passo%100==0:
            rows=avaliar(modelo,dados['dev'],pad);m=metricas(rows);score=m['acuracia_contrato']
            hist.append({'passo':passo,'perda':float(loss.detach()),'validacao':m,'segundos':round(time.monotonic()-inicio,2)})
            print(json.dumps(hist[-1],ensure_ascii=False),flush=True)
            if score>nota:
                nota=score;melhor=deepcopy(modelo.state_dict());escolhido=passo
                escrever(args.saida/'validacao_checkpoint.json',rows)
            escrever(args.saida/'progresso.json',{'historico':hist,'tokens_apresentados':tokens})
    modelo.load_state_dict(melhor)
    torch.save({'braco':args.braco,'config':vars(corpo.config),'modelo':modelo.state_dict(),
        'passo_escolhido':escolhido,'base_sha256':sha(base/'pesos.pt'),
        'tokenizer_sha256':sha(base/'tokenizer.json'),'pesos_externos':False},args.saida/'pesos.pt')
    rel={'braco':args.braco,'parametros':sum(p.numel() for p in modelo.parameters()),'passos':args.passos,
         'passo_escolhido':escolhido,'historico':hist,'tokens_apresentados':tokens,
         'entradas_distintas_apresentadas':len(vistos),'tokens_distintos_dessas_entradas':sum(len(dados['treino'][i]['ids']) for i in vistos),
         'supervisao_por_exemplo':10 if args.braco=='contextual' else 1,
         'tokens_supervisionados_causal_lm':0,'objetivo':'classificação e ponteiros, não redação causal',
         'segundos':round(time.monotonic()-inicio,2),'dados_sha256':manifest['sha256'],
         'base_sha256':sha(base/'pesos.pt'),'pesos_sha256':sha(args.saida/'pesos.pt'),
         'tokenizer_sha256':sha(base/'tokenizer.json'),'aprovado':False,
         'limite':'Controle mede classes; candidato mede argumentos, operação e escopo. Esses agregados não são diretamente comparáveis; comparar execução/sessões na avaliação pareada.',
         'teste_lido_no_treino':False}
    escrever(args.saida/'relatorio.json',rel)
    print(json.dumps({k:v for k,v in rel.items() if k!='historico'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
