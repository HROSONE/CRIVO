"""SFT causal próprio de diálogo, separado do intérprete de argumentos.

Usa somente cenários autorais estáticos do projeto, sem expansão paramétrica,
e replay dos pares humanos públicos já existentes. Nunca lê teste no treino.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys
import time
import torch

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from linguagem_profunda import carregar,ESPECIAIS
from scripts.curriculo_dialogos_amplos import pares_conversa,particao_cenario

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def escrever(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def codificar(tok,e):
    seq=[]
    for t in e['historico']+[{'papel':'usuario','texto':e['mensagem']}]:
        seq+=[tok.token_to_id('<'+t['papel']+'>')]+tok.encode(t['texto'],add_special_tokens=False).ids+[tok.token_to_id('<fim>')]
    seq+=[tok.token_to_id('<assistente>')];inicio=len(seq)
    seq+=tok.encode(e['resposta'],add_special_tokens=False).ids+[tok.token_to_id('<fim>')]
    if len(seq)>256:raise ValueError('Par completo excede contexto; não truncar.')
    y=[-100]*len(seq[:-1])
    for i in range(inicio-1,len(y)):y[i]=seq[i+1]
    return {'x':seq[:-1],'y':y,'exemplo':e}

def lote(itens,pad):
    n=max(len(i['x']) for i in itens);x=torch.full((len(itens),n),pad,dtype=torch.long);y=torch.full_like(x,-100)
    for j,i in enumerate(itens):x[j,:len(i['x'])]=torch.tensor(i['x']);y[j,:len(i['y'])]=torch.tensor(i['y'])
    return x,y

def preparar(out):
    out.mkdir(parents=True,exist_ok=False);_,tok,_=carregar(ROOT/'artefatos/linguagem_profunda')
    dados={s:[] for s in ['treino','validacao','teste']};rejeitados=Counter()
    rows=json.loads((ROOT/'dados/dialogos_amplos_autorais.json').read_text())['conversas']
    for c in rows:
        split=particao_cenario('autoral:'+c['id']);es=list(pares_conversa('autoral:'+c['id'],c['familia'],c['turnos']))
        try:
            for e in es:codificar(tok,e)
        except ValueError:rejeitados[split]+=1;continue
        for e in es:e['origem']='sintetico_autoral_existente'
        dados[split]+=es
    humanos=json.loads((ROOT/'dados/dialogos_humanos.json').read_text())['exemplos'];human_reject=0
    for e in humanos:
        if e['split']!='treino':continue
        try:codificar(tok,e)
        except ValueError:human_reject+=1;continue
        dados['treino'].append({**e,'familia':'replay_humano','origem':'humano_publico_previamente_usado'})
    entradas={s:{json.dumps([e['historico'],e['mensagem']],ensure_ascii=False) for e in es} for s,es in dados.items()}
    for a,b in [('treino','validacao'),('treino','teste'),('validacao','teste')]:assert not entradas[a]&entradas[b]
    manifest={'fontes':{n:sha(ROOT/'dados'/n) for n in ['dialogos_amplos_autorais.json','dialogos_humanos.json']},
        'autorais_cenarios_rejeitados_por_contexto':dict(rejeitados),'humanos_treino_rejeitados_por_contexto':human_reject,
        'estatisticas':{},'tokenizer_sha256':sha(ROOT/'artefatos/linguagem_profunda/tokenizer.json'),'sha256':{},
        'limites':'Poucos cenários autorais existentes, sem expansão por números. Replay humano já conhecido pelo modelo não é novo dado. Partições autorais por cenário completo; origem anterior não certifica independência. Nenhum modelo/API externo ou conversa privada. Pares/sessões longos excluídos inteiros.'}
    for s,es in dados.items():
        escrever(out/(s+'.json'),es);cs=[codificar(tok,e) for e in es]
        manifest['sha256'][s]=sha(out/(s+'.json'))
        manifest['estatisticas'][s]={'pares':len(es),'cenarios':len({e['grupo'] for e in es}),
            'tokens_alvo':sum(sum(t!=-100 for t in c['y']) for c in cs),'tokens_entrada':sum(len(c['x']) for c in cs),
            'familias':dict(Counter(e['familia'] for e in es))}
    escrever(out/'manifesto.json',manifest);print(json.dumps(manifest['estatisticas'],ensure_ascii=False),flush=True)

@torch.no_grad()
def avaliar_perda(m,itens,pad):
    m.eval();soma=0.;nt=0
    for a in range(0,len(itens),8):
        x,y=lote(itens[a:a+8],pad);n=int((y!=-100).sum());soma+=float(m(x,y)[1])*n;nt+=n
    return soma/nt

def treinar(ex,retomar=False):
    torch.set_num_threads(1);torch.manual_seed(20261011);base=ROOT/'artefatos/linguagem_profunda';m,tok,meta=carregar(base)
    dados=ex/'dados';manifest=json.loads((dados/'manifesto.json').read_text());sets={}
    for s in ['treino','validacao']:
        assert sha(dados/(s+'.json'))==manifest['sha256'][s]
        sets[s]=[codificar(tok,e) for e in json.loads((dados/(s+'.json')).read_text())]
    humanos=[i for i,c in enumerate(sets['treino']) if c['exemplo']['familia']=='replay_humano']
    autorais=[i for i,c in enumerate(sets['treino']) if c['exemplo']['familia']!='replay_humano']
    assert humanos and autorais and sets['validacao']
    assinatura={'dados_manifesto_sha256':sha(dados/'manifesto.json'),'base_sha256':sha(base/'pesos.pt'),
        'codigo_sha256':sha(__file__),'passos':600,'lote':8,'autorais_por_lote':6,'replay_humano_por_lote':2,'seed':20261011,'lr':.0001,
        'selecao':'Menor entropia cruzada de todas as respostas da validação autoral com histórico de referência; não seleciona por teste ou sondas.'}
    out=ex/'candidato';opt=torch.optim.AdamW(m.parameters(),lr=.0001,weight_decay=.01);rng=random.Random(91731)
    hist=[];melhor=None;nota=float('inf');escolhido=0;passo_inicio=0;segundos_anteriores=0.;nt=0;vistos=set()
    if retomar:
        r=torch.load(out/'retomada.pt',map_location='cpu',weights_only=True);assert r['assinatura']==assinatura
        m.load_state_dict(r['modelo']);opt.load_state_dict(r['otimizador']);rng.setstate(r['rng_python']);torch.set_rng_state(r['rng_torch'])
        hist=r['historico'];melhor=r['melhor'];nota=r['nota'];escolhido=r['escolhido'];passo_inicio=r['passo'];segundos_anteriores=r['segundos'];nt=r['tokens'];vistos=set(r['vistos'])
    else:
        out.mkdir(exist_ok=False);escrever(out/'assinatura.json',assinatura)
    inicio=time.monotonic();pad=tok.token_to_id('<pad>')
    for passo in range(passo_inicio+1,601):
        m.train();inds=[rng.choice(autorais) for _ in range(6)]+[rng.choice(humanos) for _ in range(2)];rng.shuffle(inds);vistos.update(inds)
        x,y=lote([sets['treino'][i] for i in inds],pad);loss=m(x,y)[1]
        opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1.);opt.step();nt+=int((y!=-100).sum())
        if passo%100==0:
            ce=avaliar_perda(m,sets['validacao'],pad);segundos=segundos_anteriores+time.monotonic()-inicio
            row={'passo':passo,'perda_treino':float(loss.detach()),'ce_validacao':ce,'segundos':round(segundos,2)};hist.append(row);print(json.dumps(row),flush=True)
            if ce<nota:nota=ce;melhor=deepcopy(m.state_dict());escolhido=passo
            r={'assinatura':assinatura,'modelo':m.state_dict(),'otimizador':opt.state_dict(),'rng_python':rng.getstate(),'rng_torch':torch.get_rng_state(),
                'historico':hist,'melhor':melhor,'nota':nota,'escolhido':escolhido,'passo':passo,'segundos':segundos,'tokens':nt,'vistos':list(vistos)}
            tmp=out/'retomada.tmp';torch.save(r,tmp);tmp.replace(out/'retomada.pt');escrever(out/'progresso.json',hist)
    m.load_state_dict(melhor)
    estado={**meta,'modelo':m.state_dict(),'passo':escolhido,'experimental':True,'aprovado_para_chat':False,
        'ajuste_dialogo':assinatura}
    torch.save(estado,out/'pesos.pt');shutil.copyfile(base/'tokenizer.json',out/'tokenizer.json')
    escrever(out/'relatorio.json',{'passos_completos':600,'passo_escolhido':escolhido,'historico':hist,'assinatura':assinatura,
        'parametros':sum(p.numel() for p in m.parameters()),'tokens_alvo_apresentados':nt,'pares_distintos_apresentados':len(vistos),
        'segundos':round(segundos_anteriores+time.monotonic()-inicio,2),'pesos_sha256':sha(out/'pesos.pt'),'teste_lido_no_treino':False,
        'aprovado_para_chat':False,'limite':'Menor perda com histórico de referência não certifica conversa gerada com o próprio histórico. Pouco texto autoral disponível; não é treino amplo de linguagem nem IA geral.'})
    print('Treino causal concluído; ainda precisa avaliar respostas geradas.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('acao',choices=['preparar','treinar']);p.add_argument('pasta',type=Path);p.add_argument('--retomar',action='store_true');a=p.parse_args()
    if a.acao=='preparar':preparar(a.pasta)
    else:treinar(a.pasta,a.retomar)
