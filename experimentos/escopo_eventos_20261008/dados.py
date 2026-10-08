"""Sessões novas de eventos, com ordens diferentes e confirmação de hipóteses.

Não lê os testes antigos nem previsões. Textos autorais sintéticos, não uma
avaliação independente. Trajetórias compartilham regras entre partições.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
from base import ROOT,ASSOC,CONTEXT,escrever,sha
from corpus import Sessao
from modelo import esperado,recuperar
from normalizacao import codificar
from tokenizers import Tokenizer

EVENTOS=['declaracao','correcao','hipotese','retorno','consulta','confirmacao']
PLANOS={
 'treino': ['Azul','Verde','Sol','Lua','Brisa','Trilha','Mar','Rio','Cobre','Cinza','Ouro','Leste'],
 'dev':['Âmbar','Norte','Pedra','Violeta'],
 'teste':['Névoa','Cedro','Pérola','Horizonte','Granito','Avelã'],
}
PESSOAS={'treino':['Ana','Beto','Caio','Dora','Iara','Rui','Lia','Leo'],
         'dev':['Vera','Tito','Lena','Bruno'],'teste':['Helena','Artur','Inês','Otávio']}
OBJETOS={'treino':['chave','selo','cartão','senha','mapa','ticket','ficha','medalha'],
         'dev':['convite','pulseira','crachá','documento'],'teste':['passaporte','certificado','distintivo','credencial']}
# Frases conhecidas da investigação anterior podem voltar no TREINO, mas seus
# exemplos/testes completos não são lidos. Os bancos dev/teste abaixo são novos.
FORMAS={
 'treino': {
 'inicio':['O plano {n} custa {v} reais. ','{n} sai por {v} reais. ',
           'Por {n}, paga-se {v} reais. ','O custo de {n} é {v} reais. '],
 'correcao':['Eu me enganei sobre {n}: o valor certo é {v} reais. ',
             'Corrigindo {n}: o custo real é {v} reais. ',
             'Mude apenas a cobrança real de {n} para {v} reais. ',
             'Fora da hipótese, {n} agora custa {v} reais. ',
             'A correção é factual: {n} passou a {v} reais. ',
             'Acabei de conferir: {n} na verdade custa {v} reais. '],
 'hipotese':['Em outro cenário hipotético, {n} custaria {v} reais. ',
             'Faça de conta que {n} vale {v} reais; é só simulação. ',
             'Imagine {n} por {v} reais, sem alterar os fatos. ',
             'Suponha, em um novo cenário, {n} por {v} reais. ',
             'E se {n} passasse a {v} reais? É uma hipótese nova. '],
 'retorno':['Esqueça a simulação e use os preços reais corrigidos. ',
            'Encerre o cenário hipotético e calcule com os fatos. ',
            'A hipótese não ocorreu. Volte aos preços reais. ',
            'Retome o caso real; nada do cenário imaginado aconteceu. '],
 'consulta':['Mantenha o cenário atual. ','Continue a comparação atual. ','Sem alterar nenhum dado, '],
 'confirmacao':['A última hipótese aconteceu de verdade. Agora ela é fato. ',
                'Confirmo como reais os valores da última simulação. ',
                'O cenário que imaginei foi confirmado na realidade. '],
 'pergunta':['Compare {a} e {b}.','Qual custa menos: {a} ou {b}?',
             'Quanto separa os preços de {a} e {b}?'],
 'regra':['Para entrar são exigidos {v}. ','Os objetos requeridos para entrar são {v}. '],
 'posse':['{n} {v}. ','Sobre {n}: {v}. ','Inventário de {n}: {v}. '],
 'corr_posse':['Fora da hipótese, {n} agora {v}. ','Corrijo os fatos: {n} {v}. ',
               'Mude o registro real de {n}: {v}. ','Eu me enganei: na realidade {n} {v}. '],
 'hip_posse':['Em outro cenário hipotético, {n} {v}. ',
              'Faça de conta que {n} {v}; é uma nova simulação. ',
              'Imagine, sem mudar os fatos, que {n} {v}. '],
 'ret_posse':['Esqueça a simulação e use os objetos reais. ',
              'A hipótese não ocorreu. Retome o inventário factual. '],
 'perg_posse':['{n} cumpre os requisitos?','A regra permite que {n} entre?',
               'Com os itens atuais, {n} pode entrar?'],
 },
 'dev':{
 'inicio':['Contratar {n} custa {v} reais. ','A cobrança de {n} é {v} reais. '],
 'correcao':['O dado confirmado de {n} foi retificado para {v} reais. ',
             'A informação real anterior sobre {n} estava incorreta: custa {v} reais. '],
 'hipotese':['Vamos trabalhar com uma alternativa imaginária: {n} por {v} reais. ',
             'Em uma nova suposição, o custo de {n} seria {v} reais. '],
 'retorno':['Abandone a alternativa imaginária. Use o que foi confirmado como real. '],
 'consulta':['Sem novidade, continue usando o cenário que está ativo. '],
 'confirmacao':['A situação antes imaginária foi comprovada e passou a ser real. '],
 'pergunta':['Entre {a} e {b}, qual tem o menor gasto?', 'Compare os preços atuais de {a} e {b}.'],
 'regra':['No ingresso são requeridos {v}. '],
 'posse':['Quanto a {n}, {v}. '],
 'corr_posse':['Os dados confirmados de {n} foram retificados: {v}. '],
 'hip_posse':['Em uma nova situação imaginária, {n} {v}. '],
 'ret_posse':['Abandone a alternativa imaginária e use os objetos confirmados. '],
 'perg_posse':['Confira se {n} atende às condições de entrada.'],
 },
 'teste':{
 'inicio':['A despesa com {n} é de {v} reais. ','O plano {n} tem preço de {v} reais. '],
 'correcao':['A informação certa é esta: {n} custa {v} reais, de fato. ',
             'Houve um erro no dado real de {n}; o custo corrigido é {v} reais. ',
             'É uma atualização dos fatos, não uma suposição: {n} vale {v} reais. '],
 'hipotese':['Isto não aconteceu: num novo cenário fictício, {n} custa {v} reais. ',
             'Vamos testar outro cenário sem afirmar que ocorreu: {n} a {v} reais. ',
             'Considere como possibilidade imaginada, em vez de fato, {n} por {v} reais. '],
 'retorno':['Deixe de lado o que foi apenas imaginado. Compare os fatos confirmados. ',
            'Cancele o cenário fictício; a situação factual segue valendo. '],
 'consulta':['Sem modificar fatos ou possibilidades, retome o cálculo corrente. '],
 'confirmacao':['O que era apenas uma possibilidade realmente ocorreu; trate como fato confirmado. ',
                'A simulação anterior foi verificada: aqueles valores agora são reais. '],
 'pergunta':['Qual tem custo menor, {a} ou {b}, e quanto?',
             'Verifique a diferença entre {a} e {b} no cenário vigente.'],
 'regra':['Nesse acesso são exigidos {v}. '],
 'posse':['A informação sobre {n} é que {v}. '],
 'corr_posse':['Houve um erro nos fatos sobre {n}; o registro correto é que {v}. ',
               'Isto é factual, não simulado: {n} {v}. '],
 'hip_posse':['Isto não ocorreu: em outro cenário fictício, {n} {v}. ',
              'Considere como possibilidade imaginada, em vez de fato, que {n} {v}. '],
 'ret_posse':['Deixe de lado o inventário imaginado; considere os objetos confirmados. '],
 'perg_posse':['O caso vigente de {n} satisfaz os requisitos de acesso?'],
 },
}
TRAJETORIAS=[
 ['correcao','hipotese','retorno'],['hipotese','retorno','correcao'],
 ['hipotese','correcao','retorno'],['correcao','correcao','hipotese','retorno'],
 ['hipotese','consulta','retorno','correcao'],['correcao','hipotese','hipotese','retorno'],
 ['correcao','hipotese','confirmacao','retorno'],['hipotese','confirmacao','correcao','consulta'],
]

def partes(fmt,**campos):
    import re
    out=[];a=0
    for m in re.finditer(r'\{([a-z]+)\}',fmt):
        out.append(fmt[a:m.start()]);out.append((m[1],str(campos[m[1]])));a=m.end()
    out.append(fmt[a:]);return out

def construir(split,indice):
    rng=random.Random({'treino':31819,'dev':65357,'teste':94183}[split]+indice*104729)
    preco=indice%2==0;familia='precos' if preco else 'requisitos'
    s=Sessao(f'eventos-{split}-{indice}',familia,split);fs=FORMAS[split];pick=lambda k:rng.choice(fs[k])
    seq=TRAJETORIAS[(indice//2)%len(TRAJETORIAS)];out=[];ativo=False;virtual=None
    if preco:
        nomes=rng.sample(PLANOS[split],2);vs=rng.sample(range(10,190) if split!='teste' else range(351,550),9)
        intro=[]
        for i in rng.sample([0,1],2):
            intro+=partes(pick('inicio').replace('{n}',f'{{n{chr(97+i)}}}').replace('{v}',f'{{v{chr(97+i)}}}'),
                         **{f'n{chr(97+i)}':nomes[i],f'v{chr(97+i)}':vs[i]})
        intro+=['A entrega leva ',('distrator',str(vs[8])),' dias. ']
        q=lambda:pick('pergunta').format(a=nomes[0],b=nomes[1])
        a=s.fala(intro+[q()]);real=[a['va'],a['vb']];ref=None
        regra=None
    else:
        nomes=rng.sample(PESSOAS[split],2);x,y,z=rng.sample(OBJETOS[split],3)
        inventories=[f'tem {x} e {y}',f'tem {x} e não tem {y}',f'tem {x}',f'tem {x} e não tem {x}']
        shift=(indice//16)%4
        q=lambda:pick('perg_posse').format(n=nomes[0])
        a=s.fala(partes(pick('regra').replace('{v}','{r}'),r=' e '.join(rng.sample([x,y],2)))+
                 partes(pick('posse'),n=nomes[0],v=inventories[shift])+[q()])
        regra=a['r'];ref=a['n'];real=[regra,a['v']]
    def emitir(evento):
        valores=virtual if ativo else real
        e=s.exemplo('comparar_custos' if preco else 'verificar_requisitos',valores,ref,ativo)
        e['evento']=evento;e['trajetoria']='>'.join(seq);out.append(e)
    emitir('declaracao')
    for etapa,evento in enumerate(seq):
        if evento in ['correcao','hipotese']:
            if preco:
                idx=rng.randrange(2);r=s.fala(partes(pick(evento),n=nomes[idx],v=vs[etapa+2])+[q()])
                proximo=list(real);proximo[idx]=r['v']
            else:
                inv=inventories[(shift+etapa+1)%4]
                r=s.fala(partes(pick('corr_posse' if evento=='correcao' else 'hip_posse'),n=nomes[0],v=inv)+[q()])
                proximo=[regra,r['v']]
            if evento=='correcao':real=proximo;ativo=False;virtual=None
            else:virtual=proximo;ativo=True
        elif evento=='retorno':
            s.fala([pick('retorno' if preco else 'ret_posse'),q()]);ativo=False;virtual=None
        elif evento=='confirmacao':
            assert ativo and virtual is not None
            s.fala([pick('confirmacao'),q()]);real=list(virtual);virtual=None;ativo=False
        else:s.fala([pick('consulta'),q()])
        emitir(evento)
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('saida',type=Path);args=p.parse_args();args.saida.mkdir(parents=True,exist_ok=False)
    tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));tok.encode_special_tokens=True
    vistos=set();stats={};verificados=0
    for split,ns in [('treino',1000),('dev',80),('teste',120)]:
        rows=[];i=0;rejeitados=0;session_count=0;tokens=[]
        while session_count<ns:
            es=construir(split,i);i+=1
            keys=[json.dumps(e['turnos'],ensure_ascii=False) for e in es]
            try:cs=[codificar(tok,e) for e in es]
            except ValueError:rejeitados+=1;continue
            if any(k in vistos for k in keys):rejeitados+=1;continue
            for c,e in zip(cs,es):
                for sp,(a,b) in zip(e['argumentos']+[e['referente']],zip(c['pontos'][::2],c['pontos'][1::2])):
                    if sp:
                        r=recuperar(c,a,b);assert r and r['texto']==sp['texto'] and r['turno']==sp['turno']
                assert esperado(e)['executavel'];tokens.append(len(c['ids']));verificados+=1
            vistos.update(keys);rows+=es;session_count+=1
        escrever(args.saida/(split+'.json'),rows)
        stats[split]={'sessoes':ns,'exemplos':len(rows),'tokens':sum(tokens),'max_tokens':max(tokens),'rejeitados_sem_truncar':rejeitados,
            'eventos':dict(Counter(e['evento'] for e in rows)),'familias':dict(Counter(e['familia'] for e in rows))}
    # Replay anterior de TREINO apenas; só carrega labels antes vistos em treino.
    old=json.loads((CONTEXT/'dados/treino.json').read_text());replay=random.Random(71131).sample(old,1000)
    for e in replay:e['evento']=None
    escrever(args.saida/'replay.json',replay)
    escrever(args.saida/'manifesto.json',{'sha256':{s:sha(args.saida/(s+'.json')) for s in ['treino','dev','teste','replay']},
        'estatisticas':stats,'roundtrips_verificados':verificados,'codigo_gerador_sha256':sha(__file__),
        'origem':'Sintético autoral; nenhum controle antigo completo, conversa privada, modelo ou API externo lido.',
        'limites':'Bancos de frases e vocabulários separados, mesmas regras/trajetórias/autoria. Não independente, não conversa livre. Valores inteiros distintos, nomes de uma palavra. Cada novo cenário hipotético parte dos fatos reais; correção explícita encerra a hipótese; confirmação converte a última alternativa em fato.'})
    print(json.dumps(stats,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
