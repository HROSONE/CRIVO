"""Continua somente pesos próprios; treino nunca abre teste.json.

Checkpoints de retomada conservam Adam, RNG, pesos correntes e melhor estado.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import random
import time
import torch
from comum import ROOT, ANTERIOR, escrever, sha
from modelo import Interprete, codificar, lote, proposta, conferir, executar, esperado, metricas
from corpus import OPERACOES
from decodificar import proposta_limitada
from linguagem_profunda import Configuracao, LinguagemProfunda
from tokenizers import Tokenizer

def carregar(p):
    state=torch.load(p,map_location='cpu',weights_only=True)
    m=Interprete(LinguagemProfunda(Configuracao(**state['config'])),'contextual')
    m.load_state_dict(state['modelo']);return m,state

@torch.no_grad()
def coletar(m,itens,pad):
    m.eval();raw=[];limited=[]
    for i in range(0,len(itens),16):
        bs=itens[i:i+16];x,l=lote(bs,pad);ls=m(x,l)
        for j,item in enumerate(bs):
            e=item['exemplo']
            for destino,decoder in [(raw,proposta),(limited,proposta_limitada)]:
                pr=decoder(item,ls,j);out=executar(pr);gold=esperado(e)
                destino.append({'sessao':e['sessao'],'familia':e['familia'],'etapa':e['etapa'],
                    **conferir(e,pr),'proposta':pr,'execucao':out,
                    'resultado_correto':out.get('resultado')==gold.get('resultado') and pr['hipotese']==e['hipotese']})
    return raw,limited

def media_familias(rows):
    fs=metricas(rows)['por_familia'];return sum(v['acuracia'] for v in fs.values())/len(fs)

def main():
    p=argparse.ArgumentParser();p.add_argument('--dados',type=Path,required=True);p.add_argument('--saida',type=Path,required=True)
    p.add_argument('--retomar',action='store_true');args=p.parse_args()
    torch.set_num_threads(1);torch.manual_seed(20261010)
    initial=ANTERIOR/'pesos_contextual/pesos.pt';m,metadata=carregar(initial)
    base=ROOT/'artefatos/linguagem_profunda';tok=Tokenizer.from_file(str(base/'tokenizer.json'));tok.encode_special_tokens=True
    assert sha(base/'tokenizer.json')==metadata['tokenizer_sha256']
    manifest=json.loads((args.dados/'manifesto.json').read_text());dados={}
    for s in ['treino','dev','replay']:
        assert sha(args.dados/(s+'.json'))==manifest['sha256'][s]
        dados[s]=[codificar(tok,e) for e in json.loads((args.dados/(s+'.json')).read_text())]
    olddev=[codificar(tok,e) for e in json.loads((ANTERIOR/'dados/dev.json').read_text())]
    assinatura={'dados':manifest['sha256'],'inicial':sha(initial),
        'codigo':{n:sha(Path(__file__).parent/n) for n in ['ajustar.py','decodificar.py','comum.py']},
        'passos':600,'lote':16,'lr':.0001,'seed':20261010,'selecionar':'.70 média famílias novo dev limitado + .30 média famílias dev anterior limitado'}
    opt=torch.optim.AdamW(m.parameters(),lr=.0001,weight_decay=.01)
    rng=random.Random(52133);hist=[];melhor=None;nota=-1.;escolhido=0;tokens=0;passo_inicio=0;segundos_anteriores=0.
    if args.retomar:
        r=torch.load(args.saida/'retomada.pt',map_location='cpu',weights_only=True)
        assert r['assinatura']==assinatura
        m.load_state_dict(r['modelo']);opt.load_state_dict(r['otimizador']);rng.setstate(r['rng_python']);torch.set_rng_state(r['rng_torch'])
        hist=r['historico'];melhor=r['melhor'];nota=r['nota'];escolhido=r['escolhido'];tokens=r['tokens'];passo_inicio=r['passo'];segundos_anteriores=r['segundos']
    else:
        args.saida.mkdir(parents=True,exist_ok=False)
        escrever(args.saida/'assinatura.json',assinatura)
    inicio=time.monotonic();pad=tok.token_to_id('<pad>');visto=set(r['vistos']) if args.retomar else set()
    for passo in range(passo_inicio+1,601):
        m.train();bs=[]
        # 12 novos exemplos + 4 anteriores por lote, sem rótulo na entrada.
        for s,n in [('treino',12),('replay',4)]:
            inds=[rng.randrange(len(dados[s])) for _ in range(n)]
            visto.update((s,i) for i in inds);bs.extend(dados[s][i] for i in inds)
        rng.shuffle(bs);x,l=lote(bs,pad);ls=m(x,l);es=[i['exemplo'] for i in bs]
        op=torch.tensor([OPERACOES.index(e['operacao']) for e in es]);spans=torch.tensor([i['pontos'] for i in bs])
        loss=torch.nn.functional.cross_entropy(ls['operacao'],op)
        loss+=.2*torch.nn.functional.cross_entropy(ls['escopo'],torch.tensor([int(e['hipotese']) for e in es]))
        loss+=.8*torch.nn.functional.cross_entropy(ls['pontos'].reshape(-1,x.shape[1]),spans.reshape(-1))
        opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1.);opt.step();tokens+=sum(len(i['ids']) for i in bs)
        if passo%100==0:
            raw,lim=coletar(m,dados['dev'],pad);oldraw,oldlim=coletar(m,olddev,pad)
            score=.70*media_familias(lim)+.30*media_familias(oldlim)
            row={'passo':passo,'perda':float(loss.detach()),'nota_selecao':score,
                 'dev_bruto':metricas(raw),'dev_limitado':metricas(lim),'dev_anterior_bruto':metricas(oldraw),'dev_anterior_limitado':metricas(oldlim),
                 'segundos':round(segundos_anteriores+time.monotonic()-inicio,2)}
            hist.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
            if score>nota:
                nota=score;melhor=deepcopy(m.state_dict());escolhido=passo
                escrever(args.saida/'validacao_nova.json',lim);escrever(args.saida/'validacao_anterior.json',oldlim)
            r={'assinatura':assinatura,'modelo':m.state_dict(),'otimizador':opt.state_dict(),'rng_python':rng.getstate(),'rng_torch':torch.get_rng_state(),
               'historico':hist,'melhor':melhor,'nota':nota,'escolhido':escolhido,'tokens':tokens,'passo':passo,'segundos':row['segundos'],'vistos':list(visto)}
            tmp=args.saida/'retomada.tmp';torch.save(r,tmp);tmp.replace(args.saida/'retomada.pt')
            escrever(args.saida/'progresso.json',hist)
    m.load_state_dict(melhor)
    torch.save({**{k:v for k,v in metadata.items() if k!='modelo'},'modelo':m.state_dict(),'passo_escolhido':escolhido,
                'inicial_contextual_sha256':sha(initial),'aprovado_para_chat':False},args.saida/'pesos.pt')
    escrever(args.saida/'relatorio.json',{'assinatura':assinatura,'historico':hist,'passos_completos':600,'passo_escolhido':escolhido,
        'tokens_apresentados':tokens,'entradas_distintas_apresentadas':len(visto),'contagem_vistos_inclui_antes_de_retomada':True,
        'segundos':round(segundos_anteriores+time.monotonic()-inicio,2),'parametros':sum(p.numel() for p in m.parameters()),
        'pesos_sha256':sha(args.saida/'pesos.pt'),'teste_lido_no_treino':False,'aprovado_para_chat':False,'supervisao_causal_redacao':False})
    print('Treino concluído; candidato não aprovado automaticamente.',flush=True)

if __name__=='__main__': main()
