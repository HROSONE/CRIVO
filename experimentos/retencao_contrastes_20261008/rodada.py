"""Retenção do transformer próprio anterior e contrastes negados.

Não usa modelo externo. O teste prospectivo é registrado antes do treino.
"""
import argparse
from collections import defaultdict,Counter
from copy import deepcopy
import json
from pathlib import Path
import random
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'escopo_eventos_20261008'))
import torch
from tokenizers import Tokenizer
from base import ROOT,ASSOC,CONTEXT,INICIAL,sha,escrever
from rede_eventos import carregar,coletar,medidas,macro_eventos,macro_familias
from normalizacao import codificar
from modelo import lote,recuperar,esperado
from corpus import OPERACOES
import dados

def tokenizer():
    t=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));t.encode_special_tokens=True;return t

def preparar(lab):
    (lab/'dados').mkdir(exist_ok=False);t=tokenizer();stats={}
    fonte=ROOT/'experimentos/escopo_eventos_20261008/dados'
    prefixos={
        'treino':{'hipotese':['Não estou dizendo que aconteceu. ','Não é um fato real: é apenas uma possibilidade. ','Nada disso ocorreu de verdade. '],
                  'correcao':['Não estou propondo uma hipótese. ','Isto não é uma simulação. ']},
        'dev':{'hipotese':['Não afirmo que seja realidade. ','Não ocorreu realmente. '],
               'correcao':['Não se trata de uma suposição. ']},
    }
    rng=random.Random(99319)
    for split in ['treino','dev']:
        orig=json.loads((fonte/(split+'.json')).read_text());groups=defaultdict(list)
        for e in orig:groups[e['sessao']].append(e)
        novos=[];rejeitados=0
        for es in groups.values():
            pre={e['etapa']:rng.choice(prefixos[split][e['evento']]) for e in es if e['evento'] in prefixos[split]}
            copies=[]
            for e in es:
                c=deepcopy(e);c['sessao']+='-negacao'
                c['turnos']=[pre.get(i,'')+txt for i,txt in enumerate(c['turnos'])]
                # Question punctuation changes one character only, no offset shift.
                if rng.random()<.5:
                    c['turnos']=[txt[:-1]+'.' if txt.endswith('?') else txt for txt in c['turnos']]
                for s in c['argumentos']+[c['referente']]:
                    if s:s['inicio']+=len(pre.get(s['turno'],''));s['fim']+=len(pre.get(s['turno'],''))
                copies.append(c)
            try:encoded=[codificar(t,e) for e in copies]
            except ValueError:rejeitados+=1;continue
            for c,e in zip(encoded,copies):
                for sp,(a,b) in zip(e['argumentos']+[e['referente']],zip(c['pontos'][::2],c['pontos'][1::2])):
                    if sp:assert recuperar(c,a,b)['texto']==sp['texto']
            novos+=copies
        rows=orig+novos;escrever(lab/'dados'/(split+'.json'),rows)
        stats[split]={'prefixos':len(rows),'originais':len(orig),'aumentados':len(novos),'sessoes_rejeitadas_sem_truncar':rejeitados}
    dados.PLANOS['teste']=['Turquesa','Bambu','Quartzo','Areia']
    dados.PESSOAS['teste']=['Rosa','Sara','Gabi','Nilo']
    dados.OBJETOS['teste']=['lacre','adesivo','moeda','pin']
    dados.FORMAS['teste']={
        'inicio':['O plano {n} foi informado com custo de {v} reais. '],
        'correcao':['Corrijo o valor confirmado: {n} agora está em {v} reais. ',
                    'Não imagine nada aqui: {n} realmente custa {v} reais. '],
        'hipotese':['Sem dizer que aconteceu, imagine {n} pelo valor de {v} reais. ',
                    'Não ocorreu de verdade: numa alternativa, {n} custaria {v} reais. '],
        'retorno':['A alternativa foi abandonada. Volte ao último estado real confirmado. '],
        'consulta':['Continue com a situação que já está em uso. '],
        'confirmacao':['O que foi imaginado se concretizou; esses dados agora descrevem a realidade. '],
        'pergunta':['Compare as cobranças de {a} e {b}.','Entre {a} e {b}, apresente a diferença.'],
        'regra':['Para entrar, os itens requeridos são {v}. '],
        'posse':['O registro confirmado sobre {n} diz que {v}. '],
        'corr_posse':['Corrijo a informação verdadeira sobre {n}: {v}. '],
        'hip_posse':['Imagine uma alternativa que não aconteceu: {n} {v}. '],
        'ret_posse':['Sem manter o inventário imaginário, volte ao registro real confirmado. '],
        'perg_posse':['Confira a entrada de {n} com o estado vigente.'],
    }
    rows=[];i=300000;n=0;rejeitados=0
    while n<80:
        es=dados.construir('teste',i);i+=1
        try:cs=[codificar(t,e) for e in es]
        except ValueError:rejeitados+=1;continue
        for c,e in zip(cs,es):
            assert esperado(e)['executavel']
            for sp,(a,b) in zip(e['argumentos']+[e['referente']],zip(c['pontos'][::2],c['pontos'][1::2])):
                if sp:assert recuperar(c,a,b)['texto']==sp['texto']
        rows+=es;n+=1
    escrever(lab/'dados/teste.json',rows);stats['teste']={'sessoes':n,'prefixos':len(rows),'rejeitados_sem_truncar':rejeitados,'eventos':dict(Counter(e['evento'] for e in rows))}
    old=json.loads((ASSOC/'dados/treino.json').read_text())
    escrever(lab/'dados/replay_associacao.json',random.Random(52111).sample(old,2000))
    shutil_source=CONTEXT/'dados/treino.json'
    escrever(lab/'dados/replay_contextual.json',random.Random(79111).sample(json.loads(shutil_source.read_text()),1000))
    escrever(lab/'protocolo.json',{'codigo_sha256':sha(__file__),'inicial_sha256':sha(INICIAL),
        'dados_sha256':{p.stem:sha(p) for p in (lab/'dados').glob('*.json')},'estatisticas':stats,
        'passos':400,'seed':20261014,'lr':.00005,'lote':'8 críticos novos, 4 replay associação própria, 4 contextual próprio',
        'distilacao':'Somente professor congelado INICIAL; KL de operação, escopo e ponteiros, peso .25 para cada, apenas no replay',
        'perda_supervisionada':{'operacao':1.,'escopo':.2,'pontos':.8,'evento':0.},
        'selecao':'.5 macro eventos novo dev + .3 macro famílias dev associação antiga + .2 macro famílias dev contextual antigo',
        'criterios':'>=80% em cada evento crítico e família; +20pp sessões completas versus anterior com mesmo preparo; regressão máxima 5pp nos dois painéis conhecidos.',
        'limites':'Tentativa posterior aos testes anteriores, que passam a conhecidos. Corpus autoral sintético; regras compartilhadas; uma semente; não independente, não conversa livre. Este novo teste não é usado para selecionar ou mudar pesos.',
        'pesos_ativos_sha256':sha(ROOT/'artefatos/linguagem_profunda/pesos.pt')})
    print(json.dumps(stats,ensure_ascii=False),flush=True)

def treinar(lab):
    torch.set_num_threads(1);torch.manual_seed(20261014);p=json.loads((lab/'protocolo.json').read_text())
    assert sha(__file__)==p['codigo_sha256'];assert sha(INICIAL)==p['inicial_sha256']
    tok=tokenizer();pad=tok.token_to_id('<pad>');ds={}
    for s in ['treino','dev','replay_associacao','replay_contextual']:
        assert sha(lab/'dados'/(s+'.json'))==p['dados_sha256'][s]
        ds[s]=[codificar(tok,e) for e in json.loads((lab/'dados'/(s+'.json')).read_text())]
    assocdev=[codificar(tok,e) for e in json.loads((ASSOC/'dados/dev.json').read_text())]
    contdev=[codificar(tok,e) for e in json.loads((CONTEXT/'dados/dev.json').read_text())]
    m,metadata=carregar();teacher,_=carregar();teacher.eval()
    for par in teacher.parameters():par.requires_grad_(False)
    opt=torch.optim.AdamW(m.parameters(),lr=p['lr'],weight_decay=.01);rng=random.Random(64783)
    criticos=['correcao','hipotese','retorno','confirmacao']
    grupos={ev:[i for i,c in enumerate(ds['treino']) if c['exemplo']['evento']==ev] for ev in criticos}
    out=lab/'candidato';out.mkdir(exist_ok=False);hist=[];nota=-1.;best=None;escolhido=0;tokens=0;t0=time.monotonic();vistos=set()
    for passo in range(1,401):
        indices=[('treino',rng.choice(grupos[ev])) for ev in criticos for _ in range(2)]
        indices += [(s,rng.randrange(len(ds[s]))) for s in ['replay_associacao','replay_contextual'] for _ in range(4)]
        rng.shuffle(indices);vistos.update(indices);bs=[ds[s][i] for s,i in indices];es=[c['exemplo'] for c in bs]
        m.train();x,l=lote(bs,pad);ls=m(x,l)
        loss=torch.nn.functional.cross_entropy(ls['operacao'],torch.tensor([OPERACOES.index(e['operacao']) for e in es]))
        loss+=.2*torch.nn.functional.cross_entropy(ls['escopo'],torch.tensor([int(e['hipotese']) for e in es]))
        loss+=.8*torch.nn.functional.cross_entropy(ls['pontos'].reshape(-1,x.shape[1]),torch.tensor([c['pontos'] for c in bs]).reshape(-1))
        mask=torch.tensor([s!='treino' for s,i in indices])
        with torch.no_grad():ts=teacher(x[mask],l[mask])
        kl=0.
        for k in ['operacao','escopo','pontos']:
            v=ls[k][mask];tv=ts[k]
            if k=='pontos':v=v.reshape(-1,x.shape[1]);tv=tv.reshape(-1,x.shape[1])
            kl+=torch.nn.functional.kl_div(v.log_softmax(-1),tv.softmax(-1),reduction='batchmean')
        loss+=.25*kl
        opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1.);opt.step();tokens+=sum(len(c['ids']) for c in bs)
        if passo%100==0:
            _,lim=coletar(m,ds['dev'],pad);_,ad=coletar(m,assocdev,pad);_,cd=coletar(m,contdev,pad)
            score=.5*macro_eventos(lim)+.3*macro_familias(ad)+.2*macro_familias(cd)
            row={'passo':passo,'nota':score,'dev':medidas(lim),'dev_associacao':medidas(ad),'dev_contextual':medidas(cd),'perda':float(loss.detach()),'segundos':time.monotonic()-t0}
            hist.append(row);print(json.dumps({'passo':passo,'nota':score,'dev':sum(r['contrato'] for r in lim),'n':len(lim),'associacao':sum(r['contrato'] for r in ad),'segundos':round(row['segundos'],2)}),flush=True)
            if score>nota:nota=score;best=deepcopy(m.state_dict());escolhido=passo;escrever(out/'dev_escolhido.json',lim)
            torch.save({'modelo':m.state_dict(),'otimizador':opt.state_dict(),'rng_python':rng.getstate(),'rng_torch':torch.get_rng_state(),'melhor':best,'escolhido':escolhido,'passo':passo,'nota':nota,'historico':hist,'tokens':tokens,'vistos':list(vistos),'protocolo':p},out/'retomada.pt')
    m.load_state_dict(best)
    torch.save({**metadata,'modelo':m.state_dict(),'passo_retencao_escolhido':escolhido,'aprovado_para_chat':False},out/'pesos.pt')
    escrever(out/'relatorio.json',{'passos_completos':400,'passo_escolhido':escolhido,'historico':hist,'tokens_apresentados':tokens,'entradas_distintas':len(vistos),
        'pesos_sha256':sha(out/'pesos.pt'),'segundos':time.monotonic()-t0,'professor_proprio_sha256':sha(INICIAL),'pesos_externos':False,'teste_lido_no_treino':False,'aprovado_para_chat':False})

def avaliar(lab):
    torch.set_num_threads(1);torch.manual_seed(20261014);p=json.loads((lab/'protocolo.json').read_text())
    assert sha(__file__)==p['codigo_sha256'];assert sha(lab/'dados/teste.json')==p['dados_sha256']['teste']
    r=json.loads((lab/'candidato/relatorio.json').read_text());assert r['passos_completos']==400;assert sha(lab/'candidato/pesos.pt')==r['pesos_sha256']
    tok=tokenizer();out=lab/'avaliacao';out.mkdir(exist_ok=False);res={}
    for nome,cp in [('anterior',INICIAL),('retencao',lab/'candidato/pesos.pt')]:
        m,_=carregar(cp);res[nome]={}
        for painel,path in [('novo',lab/'dados/teste.json'),('associacao_conhecida',ASSOC/'dados/teste.json'),('contextual_conhecido',CONTEXT/'dados/teste.json')]:
            items=[codificar(tok,e) for e in json.loads(path.read_text())];raw,lim=coletar(m,items,tok.token_to_id('<pad>'))
            for tipo,rows in [('bruto',raw),('limitado',lim)]:
                escrever(out/f'{nome}_{painel}_{tipo}.json',rows);res[nome][painel+'_'+tipo]=medidas(rows)
            print(nome,painel,sum(r['contrato'] for r in lim),'/',len(lim),flush=True)
    a=res['anterior']['novo_limitado'];b=res['retencao']['novo_limitado']
    criticos=['correcao','hipotese','retorno','confirmacao'];aumento=b['sessoes_completas']/b['sessoes']-a['sessoes_completas']/a['sessoes']
    queda=max(res['anterior'][k+'_limitado']['acuracia_contrato']-res['retencao'][k+'_limitado']['acuracia_contrato'] for k in ['associacao_conhecida','contextual_conhecido'])
    criterios={'cada_evento_critico_80pct':all(b['por_evento'][e]['acuracia_contrato']>=.8 for e in criticos),
        'cada_familia_80pct':all(v['acuracia']>=.8 for v in b['por_familia'].values()),'aumento_sessoes_pp':100*aumento,'queda_maxima_regressoes_pp':100*queda}
    passou=criterios['cada_evento_critico_80pct'] and criterios['cada_familia_80pct'] and aumento>=.2 and queda<=.05
    escrever(out/'resumo.json',{'resultados':res,'criterios':criterios,'passou_criterio_sintetico':passou,'aprovado_para_chat':False,'limites':p['limites']})
    assert sha(ROOT/'artefatos/linguagem_profunda/pesos.pt')==p['pesos_ativos_sha256']

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('acao',choices=['preparar','treinar','avaliar']);p.add_argument('--laboratorio',type=Path,required=True);a=p.parse_args()
    {'preparar':preparar,'treinar':treinar,'avaliar':avaliar}[a.acao](a.laboratorio)
