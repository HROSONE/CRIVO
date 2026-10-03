"""Interpretador autoral de subconjunto JS numérico, sem eval ou APIs do host."""
import re

OPERACOES = ('+', '-', '<', '===')
TOKEN = re.compile(r'\s*(?:(\d+)|([A-Za-z_][A-Za-z_0-9]*)|(===|\+=|-=|[+<\-=;(){}]))')


class Parser:
    def __init__(self, codigo):
        if not isinstance(codigo,str) or len(codigo)>8000:raise ValueError('Código excede limite')
        self.tokens=[];pos=0
        while pos<len(codigo):
            if codigo[pos:].strip()=='':break
            m=TOKEN.match(codigo,pos)
            if not m:raise ValueError('Token fora do subconjunto na posição '+str(pos))
            self.tokens.append(next(x for x in m.groups() if x is not None));pos=m.end()
        if len(self.tokens)>512:raise ValueError('Muitos tokens')
        self.i=0
    def ver(self):return self.tokens[self.i] if self.i<len(self.tokens) else None
    def tomar(self,esperado=None):
        x=self.ver()
        if x is None or esperado is not None and x!=esperado:raise ValueError('Esperado '+str(esperado))
        self.i+=1;return x
    def nome(self):
        x=self.tomar()
        if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',x) or x in ('let','const','if','else','while','return','true','false'):
            raise ValueError('Nome inválido')
        return x
    def expr(self,minimo=0):
        x=self.tomar()
        if x=='(':esq=self.expr();self.tomar(')')
        elif x=='-':esq=('bin','-',('num',0),self.expr(3))
        elif x.isdigit():esq=('num',int(x))
        elif re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',x) and x not in ('let','const','if','else','while','return'):
            esq=('var',x)
        else:raise ValueError('Expressão inválida')
        prioridades={'===':1,'<':1,'+':2,'-':2}
        while self.ver() in prioridades and prioridades[self.ver()]>=minimo:
            op=self.tomar();esq=('bin',op,esq,self.expr(prioridades[op]+1))
        return esq
    def bloco(self):
        self.tomar('{');out=[]
        while self.ver()!='}':out.append(self.statement())
        self.tomar('}');return out
    def statement(self):
        x=self.tomar()
        if x in ('let','const'):
            nome=self.nome();self.tomar('=');e=self.expr();self.tomar(';');return ('declarar',nome,e,x=='const')
        if x=='return':
            e=self.expr();self.tomar(';');return ('retornar',e)
        if x in ('if','while'):
            self.tomar('(');e=self.expr();self.tomar(')');b=self.bloco()
            outro=[]
            if x=='if' and self.ver()=='else':self.tomar();outro=self.bloco()
            return (x,e,b,outro)
        self.i-=1;nome=self.nome();op=self.tomar()
        if op not in ('=','+=','-='):raise ValueError('Atribuição inválida')
        e=self.expr();self.tomar(';')
        if op!='=':e=('bin',op[0],('var',nome),e)
        return ('atribuir',nome,e)
    def parse(self):
        out=[]
        while self.ver() is not None:out.append(self.statement())
        return out


def analisar(codigo):
    try:return Parser(codigo).parse()
    except RecursionError:raise ValueError('Aninhamento excede limite')


def efeito_exato(op,a,b):
    if type(a) is not int or type(b) is not int:raise ValueError('Operadores exigem inteiros')
    if op=='+':r=a+b
    elif op=='-':r=a-b
    elif op=='<':return a<b
    elif op=='===':return a==b
    else:raise ValueError('Operação não suportada')
    if abs(r)>64:raise ValueError('Valor excede domínio seguro [-64,64]')
    return r


class Retorno(Exception):
    def __init__(self,valor):self.valor=valor


def executar(codigo,entrada,previsor=None,max_passos=128):
    if type(entrada) is not int or abs(entrada)>64:raise ValueError('Entrada deve ser inteiro em [-64,64]')
    if not 1<=max_passos<=512:raise ValueError('Limite de passos inválido')
    if not isinstance(codigo,str):raise ValueError('Código deve ser fonte textual restrita')
    ast=analisar(codigo)
    estado={'entrada':entrada};constantes={'entrada'};tracos=[];passos=0
    def tick():
        nonlocal passos
        passos+=1
        if passos>max_passos:raise ValueError('Orçamento de execução esgotado')
    def expr(e):
        tick()
        if e[0]=='num':
            if abs(e[1])>64:raise ValueError('Literal excede domínio')
            return e[1]
        if e[0]=='var':
            if e[1] not in estado:raise ValueError('Variável não declarada: '+e[1])
            return estado[e[1]]
        _,op,ea,eb=e;a=expr(ea);b=expr(eb)
        # No modo neural, o resultado vem exclusivamente da rede. Não consulta o oráculo.
        r=efeito_exato(op,a,b) if previsor is None else previsor(op,a,b)
        if type(r) is not (bool if op in ('<','===') else int):raise ValueError('Tipo de efeito inválido')
        if type(r) is int and abs(r)>64:raise ValueError('Efeito fora de domínio')
        tracos.append(dict(tipo='efeito',op=op,a=a,b=b,resultado=r,origem='exato' if previsor is None else 'rede'))
        return r
    def bloco(ss):
        for s in ss:
            tick();tipo=s[0]
            if tipo in ('declarar','atribuir'):
                nome=s[1]
                if tipo=='declarar' and (nome in estado or len(estado)>=8):raise ValueError('Declaração inválida')
                if tipo=='atribuir' and (nome not in estado or nome in constantes):raise ValueError('Atribuição inválida')
                antes=dict(estado);v=expr(s[2]);estado[nome]=v
                if tipo=='declarar' and s[3]:constantes.add(nome)
                tracos.append(dict(tipo='estado',antes=antes,depois=dict(estado),variavel=nome))
            elif tipo=='retornar':raise Retorno(expr(s[1]))
            elif tipo=='if':
                c=expr(s[1])
                if type(c) is not bool:raise ValueError('Condição deve ser booleana')
                bloco(s[2] if c else s[3])
            elif tipo=='while':
                while True:
                    tick();c=expr(s[1])
                    if type(c) is not bool:raise ValueError('Condição deve ser booleana')
                    if not c:break
                    bloco(s[2])
            else:raise ValueError('Statement inválido')
    try:bloco(ast)
    except Retorno as r:return dict(resultado=r.valor,estado=estado,tracos=tracos,passos=passos)
    raise ValueError('Programa não retornou')


def javascript(codigo,typescript=False):
    analisar(codigo)
    return 'function resolver(entrada'+(': number' if typescript else '')+') {\n'+codigo+'\n}'


def candidatos(limite=2000):
    """Gramática autoral limitada, não geração textual livre nem catálogo de respostas."""
    atoms=['entrada','-2','-1','0','1','2','3']
    base=['return '+x+';' for x in atoms]
    base += ['return ('+a+' '+op+' '+b+');' for op in ('+','-','<','===') for a in atoms for b in atoms]
    base += ['if (entrada < '+k+') { return '+a+'; } else { return '+b+'; }'
             for k in ('0','1','2') for a in ('entrada','0','1') for b in ('entrada','0','1')]
    base += ['let total = 0; let i = 0; while (i < entrada) { total += '+x+'; i += 1; } return total;'
             for x in ('i','1','2')]
    base += ['return (entrada '+op+' '+a+') '+op2+' '+b+';'
             for op in ('+','-') for op2 in ('+','-') for a in atoms for b in atoms]
    return list(dict.fromkeys(base))[:limite]


def sintetizar(casos,previsor=None,limite=500,finalistas=32):
    if not isinstance(casos,list) or not casos or len(casos)>16:raise ValueError('Contrato exige 1..16 exemplos de desenvolvimento')
    for c in casos:
        if not isinstance(c,dict) or set(c)!= {'entrada','saida'} or type(c['entrada']) is not int or abs(c['entrada'])>64 or type(c['saida']) not in (int,bool):
            raise ValueError('Exemplo fora do contrato numérico/booleano')
        if type(c['saida']) is int and abs(c['saida'])>64:raise ValueError('Saída fora de domínio')
    if not 1<=limite<=2000 or not 1<=finalistas<=limite:raise ValueError('Orçamento de busca inválido')
    rank=[]
    for i,codigo in enumerate(candidatos(limite)):
        acertos=0
        if previsor:
            for c in casos:
                try:
                    valor=executar(codigo,c['entrada'],previsor)['resultado']
                    acertos+=type(valor) is type(c['saida']) and valor==c['saida']
                except ValueError:pass
        rank.append((-acertos,len(codigo),i,codigo))
    ordem=sorted(rank) if previsor else [(0,0,i,c) for i,c in enumerate(candidatos(limite))]
    verificadas=0
    for _,_,_,codigo in ordem[:finalistas if previsor else limite]:
        verificadas+=1
        try:
            rs=[executar(codigo,c['entrada'])['resultado'] for c in casos]
            if all(type(v) is type(c['saida']) and v==c['saida'] for v,c in zip(rs,casos)):
                return dict(codigo=javascript(codigo),corpo=codigo,verificadas=verificadas,
                    origem='busca_simbolica_guiada_por_rede' if previsor else 'busca_simbolica',garantia='somente exemplos fornecidos')
        except ValueError:pass
    return dict(codigo=None,verificadas=verificadas,origem='busca_limitada',garantia='nenhuma solução neste orçamento')
