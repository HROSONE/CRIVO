"""Dois braços próprios com lotes idênticos. Nunca abre o teste final."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import random
import time
import torch
from base import ROOT, CONTEXT, INICIAL, escrever, sha
from rede_eventos import carregar,coletar,medidas,macro_eventos,macro_familias
from normalizacao import codificar
from modelo import lote
from corpus import OPERACOES
from dados import EVENTOS
from tokenizers import Tokenizer

def main():
    p=argparse.ArgumentParser();p.add_argument('--dados',type=Path,required=True)
    p.add_argument('--saida',type=Path,required=True);p.add_argument('--braco',choices=['controle','eventos'],required=True)
    p.add_argument('--retomar',action='store_true');a=p.parse_args()
    torch.set_num_threads(1);torch.manual_seed(20261012)
    m,metadata=carregar();base=ROOT/'artefatos/linguagem_profunda'
    tok=Tokenizer.from_file(str(base/'tokenizer.json'));tok.encode_special_tokens=True
    assert sha(base/'tokenizer.json')==metadata['tokenizer_sha256']
    manifesto=json.loads((a.dados/'manifesto.json').read_text());ds={}
    for s in ['treino','dev','replay']:
        assert sha(a.dados/(s+'.json'))==manifesto['sha256'][s]
        ds[s]=[codificar(tok,e) for e in json.loads((a.dados/(s+'.json')).read_text())]
    olddev=[codificar(tok,e) for e in json.loads((CONTEXT/'dados/dev.json').read_text())]
    pesos={'operacao':1.,'pontos':.8,'escopo':.2 if a.braco=='controle' else 1.,'evento':0. if a.braco=='controle' else .5}
    assinatura={'braco':a.braco,'dados':manifesto['sha256'],'inicial':sha(INICIAL),
        'codigo':{f.name:sha(f) for f in Path(__file__).parent.glob('*.py')},
        'passos':600,'lote':16,'lr':.0001,'seed':20261012,'pesos_perda':pesos,
        'selecao':'.70 média dos seis eventos do dev limitado + .30 média famílias dev contextual limitado',
        'amostragem':'2 exemplos por cada evento novo, mais 4 replay contextual; embaralhar; sem rótulos na entrada'}
    opt=torch.optim.AdamW(m.parameters(),lr=.0001,weight_decay=.01);rng=random.Random(85309)
    grupos={ev:[i for i,c in enumerate(ds['treino']) if c['exemplo']['evento']==ev] for ev in EVENTOS}
    hist=[];best=None;nota=-1.;escolhido=0;tokens=0;visto=set();inicio_passo=0;tempo_anterior=0.
    if a.retomar:
        r=torch.load(a.saida/'retomada.pt',map_location='cpu',weights_only=True);assert r['assinatura']==assinatura
        m.load_state_dict(r['modelo']);opt.load_state_dict(r['otimizador']);rng.setstate(r['rng_python']);torch.set_rng_state(r['rng_torch'])
        hist=r['historico'];best=r['melhor'];nota=r['nota'];escolhido=r['escolhido'];tokens=r['tokens'];visto=set(r['vistos'])
        inicio_passo=r['passo'];tempo_anterior=r['segundos']
    else:
        a.saida.mkdir(parents=True,exist_ok=False);escrever(a.saida/'assinatura.json',assinatura)
    t0=time.monotonic();pad=tok.token_to_id('<pad>')
    for passo in range(inicio_passo+1,601):
        m.train();indices=[('treino',rng.choice(grupos[ev])) for ev in EVENTOS for _ in range(2)]
        indices += [('replay',rng.randrange(len(ds['replay']))) for _ in range(4)]
        rng.shuffle(indices);visto.update(indices);bs=[ds[s][i] for s,i in indices]
        x,l=lote(bs,pad);ls=m(x,l);es=[c['exemplo'] for c in bs]
        loss=pesos['operacao']*torch.nn.functional.cross_entropy(ls['operacao'],torch.tensor([OPERACOES.index(e['operacao']) for e in es]))
        loss+=pesos['escopo']*torch.nn.functional.cross_entropy(ls['escopo'],torch.tensor([int(e['hipotese']) for e in es]))
        loss+=pesos['pontos']*torch.nn.functional.cross_entropy(ls['pontos'].reshape(-1,x.shape[1]),torch.tensor([c['pontos'] for c in bs]).reshape(-1))
        if pesos['evento']:
            targets=torch.tensor([EVENTOS.index(e['evento']) if e.get('evento') else -100 for e in es])
            loss+=pesos['evento']*torch.nn.functional.cross_entropy(ls['evento'],targets,ignore_index=-100)
        opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1.);opt.step();tokens+=sum(len(c['ids']) for c in bs)
        if passo%100==0:
            raw,lim=coletar(m,ds['dev'],pad);oldraw,oldlim=coletar(m,olddev,pad)
            score=.70*macro_eventos(lim)+.30*macro_familias(oldlim)
            row={'passo':passo,'perda':float(loss.detach()),'nota_selecao':score,'dev_bruto':medidas(raw),
                'dev_limitado':medidas(lim),'dev_anterior_limitado':medidas(oldlim),'segundos':round(tempo_anterior+time.monotonic()-t0,2)}
            hist.append(row)
            print(json.dumps({'passo':passo,'nota':score,'dev':len(lim),'contratos':sum(r['contrato'] for r in lim),
                'escopo':row['dev_limitado']['escopo_correto'],'segundos':row['segundos']}),flush=True)
            if score>nota:
                nota=score;best=deepcopy(m.state_dict());escolhido=passo;escrever(a.saida/'validacao_nova.json',lim)
            r={'assinatura':assinatura,'modelo':m.state_dict(),'otimizador':opt.state_dict(),'rng_python':rng.getstate(),'rng_torch':torch.get_rng_state(),
                'historico':hist,'melhor':best,'nota':nota,'escolhido':escolhido,'tokens':tokens,'vistos':list(visto),'passo':passo,'segundos':row['segundos']}
            tmp=a.saida/'retomada.tmp';torch.save(r,tmp);tmp.replace(a.saida/'retomada.pt');escrever(a.saida/'progresso.json',hist)
    m.load_state_dict(best)
    torch.save({**{k:v for k,v in metadata.items() if k!='modelo'},'modelo':m.state_dict(),'passo_escolhido':escolhido,
        'evento_classes':EVENTOS,'braco_eventos':a.braco,'aprovado_para_chat':False,'inicial_eventos_sha256':sha(INICIAL)},a.saida/'pesos.pt')
    escrever(a.saida/'relatorio.json',{'assinatura':assinatura,'historico':hist,'passos_completos':600,'passo_escolhido':escolhido,
        'tokens_apresentados':tokens,'entradas_distintas_apresentadas':len(visto),'segundos':round(tempo_anterior+time.monotonic()-t0,2),
        'parametros':sum(p.numel() for p in m.parameters()),'pesos_sha256':sha(a.saida/'pesos.pt'),
        'teste_lido_no_treino':False,'supervisao_causal_redacao':False,'pesos_externos':False,'aprovado_para_chat':False})
    print('Treino concluído; sem ativação automática.',flush=True)

if __name__=='__main__':main()
