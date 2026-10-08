"""Dois ajustes próprios: interpretação de operação e redação de conclusões.

Não abre controle.json. Seleciona checkpoint apenas por dev, conserva resultados
e pesos reprovados fora do runtime. Orçamento declarado: 600 passos por tarefa.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
import torch
from linguagem_profunda import carregar, codificar_texto
from treinar_interpretador import CLASSES, corpus


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def escrever(p,obj):
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


def entrada(tok,texto):
    return [tok.token_to_id('<usuario>')]+codificar_texto(tok,texto)+[tok.token_to_id('<fim>'),tok.token_to_id('<assistente>')]


def ocultos(modelo,x):
    h=modelo.embedding(x)+modelo.posicao(torch.arange(x.shape[1],device=x.device))
    for b in modelo.blocos:h=b(h)
    return modelo.norm(h)


def matriz(seqs,pad):
    x=torch.full((len(seqs),max(map(len,seqs))),pad,dtype=torch.long)
    for i,s in enumerate(seqs):x[i,:len(s)]=torch.tensor(s)
    return x


def dados_interpretacao():
    # Teste v1 já observado é diagnóstico; este teste v2 é novo e fixado
    # antes do ajuste, com famílias que não aparecem no treino/dev.
    dados={s:corpus(s,n) for s,n in [('treino',144),('dev',40)]}
    familias=[
        ['Como você vê a ideia de mudar de carreira?','Conte algo inventado sobre um barco.','O que a gravidade faz?','Senti saudade dos meus amigos.'],
        ['Em qual alternativa meu dinheiro rende mais pela despesa informada?','Há diferença financeira entre as duas escolhas?','Ordene as opções pelo preço final.','Se eu optar pela menor despesa, economizo quanto?'],
        ['Meu período livre é suficiente para o plano?','Quanto duram todas as etapas juntas?','Depois de fazer tudo isso ainda tenho minutos livres?','O tempo reservado comporta as durações?'],
        ['Que dia está livre para todo mundo?','Em quais dias as duas pessoas podem participar juntas?','A reunião cabe nas disponibilidades de cada participante?','Qual dia coincide para as pessoas?'],
        ['Dá para satisfazer as exigências com o que ele possui?','A regra do jogo permite isso com os objetos atuais?','Essas condições estão satisfeitas ou ainda falta algo?','O estado atual cumpre os requisitos mencionados?']]
    dados['teste']=[dict(texto=t,classe=CLASSES[c],familia=f) for c,ts in enumerate(familias) for f,t in enumerate(ts)]
    return dados


def treinar_interpretacao(args,modelo,tok,pasta):
    dados=dados_interpretacao()
    for s,cs in dados.items():escrever(pasta/(s+'.json'),cs)
    seqs={s:[entrada(tok,c['texto']) for c in cs] for s,cs in dados.items()}
    ys={s:torch.tensor([CLASSES.index(c['classe']) for c in cs]) for s,cs in dados.items()}
    head=torch.nn.Linear(modelo.config.dimensao,len(CLASSES))
    opt=torch.optim.AdamW([dict(params=modelo.parameters(),lr=3e-5),dict(params=head.parameters(),lr=5e-4)],weight_decay=.01)
    rng=random.Random(9471)
    pad=tok.token_to_id('<pad>')
    def logits(split,inds):
        ss=[seqs[split][i] for i in inds];x=matriz(ss,pad)
        h=ocultos(modelo,x)
        return head(h[torch.arange(len(ss)),torch.tensor([len(s)-1 for s in ss])])
    def avaliar(split):
        modelo.eval();head.eval();ps=[]
        with torch.no_grad():
            for start in range(0,len(seqs[split]),32):
                ps.extend(logits(split,list(range(start,min(start+32,len(seqs[split]))))).softmax(-1).numpy().tolist())
        return ps
    melhor=None;nota=-1;historico=[];inicio=time.monotonic()
    antes=avaliar('dev')
    for passo in range(1,args.passos+1):
        modelo.train();head.train()
        inds=[rng.randrange(len(seqs['treino'])) for _ in range(16)]
        opt.zero_grad();loss=torch.nn.functional.cross_entropy(logits('treino',inds),ys['treino'][inds]);loss.backward()
        torch.nn.utils.clip_grad_norm_(list(modelo.parameters())+list(head.parameters()),1.)
        opt.step()
        if passo%100==0:
            p=avaliar('dev');score=sum(int(np.argmax(prob))==int(y) for prob,y in zip(p,ys['dev']))/len(p)
            historico.append(dict(passo=passo,perda=float(loss),acuracia_dev=score))
            print('dev',historico[-1],round(time.monotonic()-inicio,1),flush=True)
            if score>nota:
                nota=score;melhor=deepcopy(modelo.state_dict());melhor_head=deepcopy(head.state_dict());escolhido=passo
    modelo.load_state_dict(melhor);head.load_state_dict(melhor_head)
    ps=avaliar('teste')
    casos=[dict(c,predita=CLASSES[int(np.argmax(prob))],confianca=max(prob),correto=CLASSES[int(np.argmax(prob))]==c['classe']) for c,prob in zip(dados['teste'],ps)]
    acc=sum(c['correto'] for c in casos)/len(casos);aceitos=[c for c in casos if c['confianca']>=.95]
    precisao=sum(c['correto'] for c in aceitos)/len(aceitos) if aceitos else 0
    # Amostra pequena não basta para promoção: candidato exige também painel
    # independente do projeto, ainda indisponível. Nunca alterar este gate.
    aprovado=False
    estado=dict(config=vars(modelo.config),modelo=modelo.state_dict(),cabeca=head.state_dict(),passo=escolhido,
                classes=CLASSES,execucao=dict(tokenizer_sha256=sha(ROOT/'artefatos/linguagem_profunda/tokenizer.json')))
    torch.save(estado,pasta/'pesos.pt')
    return dict(antes_dev=sum(int(np.argmax(p))==int(y) for p,y in zip(antes,ys['dev']))/len(antes),
                historico=historico,passo_escolhido_dev=escolhido,teste=dict(n=len(casos),acuracia=acc,
                aceitos=len(aceitos),precisao_aceitos=precisao),casos=casos,aprovado=aprovado,
                motivo_promocao='Sem validação independente de diálogo; cabeça ainda experimental.',
                parametros=sum(p.numel() for p in modelo.parameters())+sum(p.numel() for p in head.parameters()))


def dados_redacao(split,n):
    rng=random.Random({'treino':345,'dev':677,'teste':1323}[split]);cs=[]
    for i in range(n):
        a,b=rng.sample(range(1,100) if split!='teste' else range(100,200),2)
        if i%2:
            menor='A' if a<b else 'B';dif=abs(a-b)
            fonte=f'Conclusão verificada: opção A custa {a} reais; opção B custa {b} reais; menor custo: {menor}; diferença: {dif} reais.'
            texto=f'A opção {menor} custa menos. A diferença é de {dif} reais.'
            esperado=dict(tipo='custo',menor=menor,numero=dif)
        else:
            restante=a-b
            fonte=f'Conclusão verificada: tempo disponível {a} minutos; tempo das atividades {b} minutos; saldo {restante} minutos.'
            texto=(f'Sobram {restante} minutos.' if restante>=0 else f'Faltam {-restante} minutos para caber tudo.')
            esperado=dict(tipo='tempo',positivo=restante>=0,numero=abs(restante))
        prompt=fonte+' Redija somente a conclusão em uma frase, sem acrescentar informações.'
        cs.append(dict(texto=prompt,resposta=texto,esperado=esperado))
    return cs


def fidelidade(texto,c):
    e=c['esperado'];nums=re.findall(r'\d+',texto)
    if nums!=[str(e['numero'])]:return False
    if e['tipo']=='custo':
        return bool(re.search(r'\bopção '+e['menor']+r'\b',texto)) and 'custa menos' in texto and not re.search(r'\bopção '+('B' if e['menor']=='A' else 'A')+r'\b',texto)
    return ('Sobram' in texto if e['positivo'] else 'Faltam' in texto) and not ('Faltam' in texto if e['positivo'] else 'Sobram' in texto)


def treinar_redacao(args,modelo,tok,pasta):
    dados={s:dados_redacao(s,n) for s,n in [('treino',1200),('dev',80),('teste',48)]}
    for s,cs in dados.items():escrever(pasta/(s+'.json'),cs)
    pad=tok.token_to_id('<pad>');fim=tok.token_to_id('<fim>')
    exemplos=[]
    for c in dados['treino']:
        pre=entrada(tok,c['texto']);alvo=codificar_texto(tok,c['resposta'])+[fim]
        ids=pre+alvo
        if len(ids)>modelo.config.contexto:raise ValueError('Não truncar a conclusão.')
        exemplos.append((ids[:-1],[-100]*(len(pre)-1)+alvo))
    opt=torch.optim.AdamW(modelo.parameters(),lr=8e-5,weight_decay=.01)
    rng=random.Random(6821);hist=[];melhor=None;nota=float('inf');inicio=time.monotonic()
    def avaliar_geracao(split):
        modelo.eval();rs=[]
        for c in dados[split]:
            ids,completa=modelo.gerar(entrada(tok,c['texto']),fim,max_tokens=48,temperatura=0.,proibidos=[pad,tok.token_to_id('<usuario>'),tok.token_to_id('<assistente>'),tok.token_to_id('<documento>')])
            texto=tok.decode(ids,skip_special_tokens=True)
            rs.append(dict(c,proposta=texto,completa=completa,fiel=fidelidade(texto,c) and completa))
        return rs
    antes=avaliar_geracao('teste')
    for passo in range(1,args.passos+1):
        modelo.train();batch=[exemplos[rng.randrange(len(exemplos))] for _ in range(8)]
        x=matriz([c[0] for c in batch],pad);y=matriz([c[1] for c in batch],-100)
        opt.zero_grad();_,loss=modelo(x,y);loss.backward();torch.nn.utils.clip_grad_norm_(modelo.parameters(),1.);opt.step()
        if passo%100==0:
            modelo.eval()
            with torch.no_grad():
                perdas=[]
                for c in dados['dev']:
                    pre=entrada(tok,c['texto']);alvo=codificar_texto(tok,c['resposta'])+[fim]
                    ids=pre+alvo;y=[-100]*(len(pre)-1)+alvo
                    perdas.append(float(modelo(torch.tensor([ids[:-1]]),torch.tensor([y]))[1]))
            dev=sum(perdas)/len(perdas);hist.append(dict(passo=passo,perda_dev=dev))
            print('dev',hist[-1],round(time.monotonic()-inicio,1),flush=True)
            if dev<nota:nota=dev;melhor=deepcopy(modelo.state_dict());escolhido=passo
    modelo.load_state_dict(melhor);teste=avaliar_geracao('teste')
    acc=sum(c['fiel'] for c in teste)/len(teste)
    torch.save(dict(modelo=modelo.state_dict(),config=vars(modelo.config),passo=escolhido,
                   execucao=dict(tokenizer_sha256=sha(ROOT/'artefatos/linguagem_profunda/tokenizer.json'))),pasta/'pesos.pt')
    return dict(historico=hist,passo_escolhido_dev=escolhido,teste=dict(n=len(teste),fidelidade=acc),
                antes=dict(n=len(antes),fidelidade=sum(c['fiel'] for c in antes)/len(antes),casos=antes),
                casos=teste,aprovado=False,parametros=sum(p.numel() for p in modelo.parameters()),
                motivo_promocao='Teste numérico sintético é insuficiente para promover redação livre; candidato isolado.',
                limite_avaliador='Contrato de número, direção e opção; não julga toda a semântica de possíveis frases extras.')


def main():
    p=argparse.ArgumentParser();p.add_argument('tarefa',choices=['interpretacao','redacao']);p.add_argument('pasta',type=Path);p.add_argument('--passos',type=int,default=600);args=p.parse_args()
    args.pasta.mkdir(parents=True,exist_ok=False);torch.set_num_threads(1);torch.manual_seed(9103)
    modelo,tok,_=carregar(ROOT/'artefatos/linguagem_profunda')
    inicio=time.monotonic()
    r=(treinar_interpretacao if args.tarefa=='interpretacao' else treinar_redacao)(args,modelo,tok,args.pasta)
    r.update(tarefa=args.tarefa,orcamento_passos=args.passos,base_sha256=sha(ROOT/'artefatos/linguagem_profunda/pesos.pt'),
             pesos_sha256=sha(args.pasta/'pesos.pt'),pesos_externos=False,duracao_segundos=round(time.monotonic()-inicio,2),
             corpus_sha256={s:sha(args.pasta/(s+'.json')) for s in ['treino','dev','teste']})
    escrever(args.pasta/'relatorio.json',r)
    print(json.dumps({k:v for k,v in r.items() if k not in ('casos','antes')},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
