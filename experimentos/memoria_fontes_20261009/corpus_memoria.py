"""Dados autorais; banco factual supervisionado nunca entra na inferência."""
import argparse
from collections import defaultdict,Counter
from copy import deepcopy
import json
from pathlib import Path
import random
from apoio import ROOT,ASSOC,CONTEXT,INICIAL,sha,escrever
from preparo import codificar
from modelo import recuperar,esperado
from tokenizers import Tokenizer
import dados

def estados(rows):
    grupos=defaultdict(list)
    for e in rows:grupos[e['sessao']].append(e)
    for es in grupos.values():
        real=None
        for e in sorted(es,key=lambda e:e['etapa']):
            atual=e['argumentos']+[e['referente']]
            if not e['hipotese']:real=deepcopy(atual)
            e['bancos_gold']=[deepcopy(real),deepcopy(atual) if e['hipotese'] else [None]*4,deepcopy(atual)]
    return rows

def supervisionar(item):
    e=item['exemplo'];n=len(item['ids']);null=n-1
    banks=e.get('bancos_gold',[None,None,e['argumentos']+[e['referente']]])
    labels=[];valid=[]
    for spans in banks:
        for sp in spans if spans is not None else [None]*4:
            ys=[0.]*n
            if sp is None:ys[null]=1.
            else:
                inds=[i for i,o in enumerate(item['offsets']) if o and o[0]==sp['turno'] and o[2]>sp['inicio'] and o[1]<sp['fim']]
                if not inds:raise ValueError('Banco gold sem suporte literal.')
                for i in inds:ys[i]=1.
            labels.append(ys);valid.append(spans is not None)
    item['bancos_targets']=labels;item['bancos_validos']=valid
    return item

def main():
    p=argparse.ArgumentParser();p.add_argument('saida',type=Path);a=p.parse_args();a.saida.mkdir(exist_ok=False)
    tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));tok.encode_special_tokens=True
    # Só treino/dev. Não importa, lê ou escreve o painel futuro de outra autoria.
    f=dados.FORMAS['treino']
    f['hipotese'] += [
        'Não aconteceu: imagine {n} por {v} reais em uma alternativa. ',
        'Imagine uma alternativa ainda não ocorrida: {n} custaria {v} reais. ',
        'Não afirmo que seja real; suponha {n} por {v} reais. ',
        'É só possibilidade, não realidade: {n} ficaria em {v} reais. ']
    f['hip_posse'] += [
        'Imagine uma alternativa que não aconteceu: {n} {v}. ',
        'Não é um fato. Suponha, apenas para simular, que {n} {v}. ',
        'É uma possibilidade ainda não ocorrida: {n} {v}. ',
        'Não estou declarando a realidade: imagine que {n} {v}. ',
        'Se fosse assim, {n} {v}; isso ainda não aconteceu. ']
    f['correcao']+=['Não é uma hipótese: {n} na realidade custa {v} reais. ']
    f['corr_posse']+=['Não estou imaginando: o fato corrigido é que {n} {v}. ']
    f['pergunta']+=['Entre {a} e {b}, apresente a diferença.','Mostre os gastos de {a} e {b}.']
    d=dados.FORMAS['dev']
    d['hipotese']+=['Ainda não ocorreu; numa possibilidade imaginada, {n} valeria {v} reais. ']
    d['hip_posse']+=['Ocorre apenas na alternativa proposta, não nos fatos: {n} {v}. ',
                     'Para uma possibilidade que não se realizou, {n} {v}. ']
    d['pergunta']+=['Verifique os preços atuais de {a} e {b}.']
    stats={}
    for split,count in [('treino',800),('dev',80)]:
        rows=[];i=500000 if split=='treino' else 700000;n=0;rejected=0
        while n<count:
            es=estados(dados.construir(split,i));i+=1
            try:cs=[supervisionar(codificar(tok,e)) for e in es]
            except ValueError:rejected+=1;continue
            for c,e in zip(cs,es):
                assert esperado(e)['executavel']
                for sp,(x,y) in zip(e['argumentos']+[e['referente']],zip(c['pontos'][::2],c['pontos'][1::2])):
                    if sp:assert recuperar(c,x,y)['texto']==sp['texto']
            rows+=es;n+=1
        escrever(a.saida/(split+'.json'),rows)
        stats[split]={'sessoes':count,'prefixos':len(rows),'rejeitados_sem_truncar':rejected,'eventos':dict(Counter(e['evento'] for e in rows))}
    for nome,path,count in [('replay_associacao',ASSOC/'dados/treino.json',2000),('replay_contextual',CONTEXT/'dados/treino.json',1000)]:
        rows=estados(json.loads(path.read_text()))
        for e in rows:
            e['evento']=None # Não inventar evento para o corpus legado.
            e['bancos_gold']=[None,None,e['argumentos']+[e['referente']]]
        rows=random.Random(93719).sample(rows,count)
        escrever(a.saida/(nome+'.json'),rows)
    escrever(a.saida/'manifesto.json',{'dados_sha256':{f.stem:sha(f) for f in a.saida.glob('*.json')},
        'estatisticas':stats,'warm_start_sha256':sha(INICIAL),'gerador_sha256':sha(__file__),
        'limites':'Autoral sintético. Bancos por papel pressupõem mesma ordem das entidades nas consultas de cada sessão. Fontes reais/alternativas podem se sobrepor. Não gera conversa livre; sem fontes ou modelos externos.'})
    print(json.dumps(stats,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
