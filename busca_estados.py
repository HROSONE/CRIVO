"""Síntese limitada, comparativa e reparo por contraexemplos de desenvolvimento."""
import copy
import re
import time
from interpretacao_estruturas import executar,analisar,javascript,validar_valor
from verificacao_codigo import iguais


def candidatos(tipo,campos=(),limite=1000):
    if tipo not in ('numero','array','string','objeto'):raise ValueError('Tipo de contrato desconhecido')
    if not 1<=limite<=2000:raise ValueError('Limite de candidatos inválido')
    if len(campos)>8 or any(not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',k) or k in ('__proto__','constructor','prototype') for k in campos):raise ValueError('Campos inválidos')
    atomos={'numero':['entrada','-2','-1','0','1','2','3','4','5'],
        'array':['entrada.length','entrada[0]','entrada[1]','0','1','2','3','4'],
        'string':['entrada.length','0','1','2','3'],
        'objeto':['entrada.'+k for k in campos]+['0','1','2','3']}[tipo]
    cs=['return '+a+';' for a in atomos]
    cs+=['return ('+a+' '+op+' '+b+');' for op in ('+','-','*','<','<=','>','>=','===','!==') for a in atomos for b in atomos]
    cs+=['if ('+a+' < '+k+') { return 0 - '+a+'; } else { return '+a+'; }' for a in atomos for k in ('0','1','2')]
    if tipo=='numero':
        cs+=['let total = 0; let i = 0; while (i < entrada) { total += '+x+'; i += 1; } return total;' for x in ('i','1','2')]
    elif tipo=='array':
        cs+=['let total = 0; let i = 0; while (i < entrada.length) { total += entrada[i]; i += 1; } return total;']
        for operacao in ('entrada[i]','entrada[i] + 1','entrada[i] * 2','entrada[i] * entrada[i]'):
            cs+=['let out = []; let i = 0; while (i < entrada.length) { out.push('+operacao+'); i += 1; } return out;']
        for comparacao in ('<','<=','>','>='):
            for k in ('0','1','2'):
                cs+=['let out = []; let i = 0; while (i < entrada.length) { if (entrada[i] '+comparacao+' '+k+') { out.push(entrada[i]); } i += 1; } return out;']
        cs+=['return entrada.slice('+k+');' for k in ('0','1','2','-1')]
    elif tipo=='string':
        cs+=['return entrada.'+metodo+'();' for metodo in ('trim','toLowerCase','toUpperCase')]
        cs+=['return entrada.slice('+k+');' for k in ('0','1','2','-1')]
    elif tipo=='objeto':
        cs+=['return entrada.'+a+' && entrada.'+b+';' for a in campos for b in campos]
        cs+=['return !entrada.'+a+';' for a in campos]
    # Estruturas entram antes das centenas de expressões; orçamento limitado não as oculta.
    cs.sort(key=lambda s:(0 if s.startswith('let ') or '.slice(' in s or '.trim(' in s or '.to' in s else 1,len(s)))
    return list(dict.fromkeys(cs))[:limite]


def validar_casos(casos):
    if not isinstance(casos,list) or not 1<=len(casos)<=24:raise ValueError('Exige 1..24 exemplos')
    for c in casos:
        if not isinstance(c,dict) or set(c)!={'entrada','saida'}:raise ValueError('Exemplo inválido')
        validar_valor(c['entrada']);validar_valor(c['saida'])


def acertou(codigo,c,previsor=None):
    try:
        r=executar(codigo,c['entrada'],previsor)
        # Este laboratório exige função sem modificar sua entrada.
        return iguais(r['resultado'],c['saida']) and iguais(r['estado']['entrada'],c['entrada'])
    except ValueError:return False


def variacoes(codigo):
    # Edita somente tokens; strings e nomes não são alterados por engano.
    from interpretacao_estruturas import ParserEstruturas
    tokens=ParserEstruturas(codigo).tokens;cs=[]
    for i,t in enumerate(tokens):
        novos=[str(x) for x in range(6)] if t.isdigit() else {'<':['<=','>','>='],'<=':['<','>='],'>':['>=','<'],'>=':['>','<='],'+':['-','*'],'-':['+'],'*':['+']}.get(t,[])
        for n in novos:
            ts=tokens.copy();ts[i]=n
            s=' '.join(ts)
            try:analisar(s);cs.append(s)
            except ValueError:pass
    return list(dict.fromkeys(cs))[:256]


def buscar(casos,tipo,previsor=None,campos=(),limite=1000,finalistas=64,anterior=None):
    validar_casos(casos)
    if not 1<=finalistas<=limite:raise ValueError('Orçamento de finalistas inválido')
    inicio=time.perf_counter();cs=(variacoes(anterior) if anterior else [])+candidatos(tipo,campos,limite)
    cs=list(dict.fromkeys(cs))[:limite]
    rank=[];avaliacoes_neurais=0
    for i,codigo in enumerate(cs):
        nota=0
        if previsor:
            for c in casos:nota+=acertou(codigo,c,previsor);avaliacoes_neurais+=1
        rank.append((-nota,len(codigo),i,codigo))
    ordem=sorted(rank) if previsor else [(0,0,i,c) for i,c in enumerate(cs)]
    verificadas=0
    for _,_,_,codigo in ordem[:finalistas if previsor else limite]:
        verificadas+=1
        if all(acertou(codigo,c) for c in casos):
            return dict(corpo=codigo,codigo=javascript(codigo),verificadas=verificadas,
                        candidatos=len(cs),avaliacoes_neurais=avaliacoes_neurais,segundos=time.perf_counter()-inicio,
                        atende_desenvolvimento=True,origem='guiada_rede' if previsor else 'simbolica')
    return dict(corpo=None,codigo=None,verificadas=verificadas,candidatos=len(cs),avaliacoes_neurais=avaliacoes_neurais,
                segundos=time.perf_counter()-inicio,atende_desenvolvimento=False,origem='busca_limitada')


def buscar_com_reparo(casos,tipo,contraexemplos=(),previsor=None,campos=(),max_reparos=2,limite=1000,finalistas=64):
    validar_casos(casos)
    if max_reparos not in (0,1,2):raise ValueError('Até dois reparos')
    if contraexemplos:validar_casos(list(contraexemplos))
    desenvolvimento=copy.deepcopy(casos);tentativas=[];atual=buscar(desenvolvimento,tipo,previsor,campos,limite,finalistas)
    tentativas.append(dict(busca=atual,contraexemplo=None))
    for _ in range(max_reparos):
        if atual['corpo'] is None:break
        falha=next((c for c in contraexemplos if not acertou(atual['corpo'],c)),None)
        if falha is None:break
        if len(desenvolvimento)>=24:break
        desenvolvimento.append(copy.deepcopy(falha))
        atual=buscar(desenvolvimento,tipo,previsor,campos,limite,finalistas,anterior=atual['corpo'])
        tentativas.append(dict(busca=atual,contraexemplo=copy.deepcopy(falha)))
    return dict(inicial=tentativas[0]['busca'],final=atual,tentativas=tentativas,
                casos_desenvolvimento=len(desenvolvimento),reparos=len(tentativas)-1,
                casos_reservados_consultados=False)
