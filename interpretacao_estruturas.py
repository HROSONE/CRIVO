"""Subconjunto JS autoral com dados estruturados; APIs e chamadas livres proibidas."""
import copy
import json
import re
from interpretacao_estados import Parser, Retorno

TOKEN = re.compile(r'\s*("(?:[^"\\]|\\.)*"|\d+|[A-Za-z_][A-Za-z_0-9]*|===|!==|<=|>=|&&|\|\||\+=|-=|[+*<>=!;(){}\[\].,:-])')
PROIBIDOS = {'__proto__','constructor','prototype'}


def unidades(s):
    raw=s.encode('utf-16-le',errors='surrogatepass')
    return [chr(raw[i]+256*raw[i+1]) for i in range(0,len(raw),2)]


def validar_valor(v,profundidade=0):
    if profundidade>4:raise ValueError('Dados aninhados demais')
    if v is None or type(v) is bool:return
    if type(v) is int and abs(v)<=512:return
    if type(v) is str and len(unidades(v))<=64:return
    if type(v) is list and len(v)<=16:
        for x in v:validar_valor(x,profundidade+1)
        return
    if type(v) is dict and len(v)<=16:
        for k,x in v.items():
            if type(k) is not str or len(k)>32 or k in PROIBIDOS:raise ValueError('Chave inválida')
            validar_valor(x,profundidade+1)
        return
    raise ValueError('Valor fora do domínio limitado')


class ParserEstruturas(Parser):
    def __init__(self,codigo):
        if not isinstance(codigo,str) or len(codigo)>12000:raise ValueError('Fonte inválida ou grande demais')
        self.tokens=[];pos=0
        while pos<len(codigo):
            if codigo[pos:].strip()=='':break
            m=TOKEN.match(codigo,pos)
            if not m:raise ValueError('Token fora do subconjunto: '+str(pos))
            self.tokens.append(m.group(1));pos=m.end()
        if len(self.tokens)>768:raise ValueError('Muitos tokens')
        self.i=0
    def lista(self,fim):
        xs=[]
        if self.ver()!=fim:
            while True:
                xs.append(self.expr())
                if self.ver()!=',':break
                self.tomar(',')
        self.tomar(fim);return xs
    def expr(self,minimo=0):
        x=self.tomar()
        if x=='(':esq=self.expr();self.tomar(')')
        elif x=='-':esq=('bin','-',('num',0),self.expr(6))
        elif x=='!':esq=('un','!',self.expr(6))
        elif x.isdigit():esq=('num',int(x))
        elif x.startswith('"'):
            try:esq=('literal',json.loads(x))
            except ValueError:raise ValueError('String JSON inválida')
        elif x in ('true','false','null'):esq=('literal',{'true':True,'false':False,'null':None}[x])
        elif x=='[':esq=('array',self.lista(']'))
        elif x=='{':
            itens=[]
            if self.ver()!='}':
                while True:
                    k=self.tomar();k=json.loads(k) if k.startswith('"') else k
                    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',k) or k in PROIBIDOS:raise ValueError('Chave de objeto inválida')
                    self.tomar(':');itens.append((k,self.expr()))
                    if self.ver()!=',':break
                    self.tomar(',')
            self.tomar('}');esq=('objeto',itens)
        elif re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',x) and x not in ('let','const','if','else','while','return') and x not in PROIBIDOS:
            esq=('var',x)
        else:raise ValueError('Expressão inválida')
        while True:
            if self.ver()=='[':
                self.tomar();idx=self.expr();self.tomar(']');esq=('indice',esq,idx)
            elif self.ver()=='.':
                self.tomar();nome=self.nome()
                if nome in PROIBIDOS:raise ValueError('Propriedade proibida')
                if self.ver()=='(':
                    if nome not in ('push','slice','includes','trim','toLowerCase','toUpperCase'):raise ValueError('Método não autorizado')
                    self.tomar();esq=('metodo',esq,nome,self.lista(')'))
                else:esq=('propriedade',esq,nome)
            else:break
        prioridades={'||':1,'&&':2,'===':3,'!==':3,'<':4,'<=':4,'>':4,'>=':4,'+':5,'-':5,'*':6}
        while self.ver() in prioridades and prioridades[self.ver()]>=minimo:
            op=self.tomar();esq=('bin',op,esq,self.expr(prioridades[op]+1))
        return esq
    def statement(self):
        if self.ver() in ('let','const','return','if','while'):return super().statement()
        alvo=self.expr()
        if self.ver()==';':self.tomar();return ('expressao',alvo)
        op=self.tomar()
        if op not in ('=','+=','-=') or alvo[0] not in ('var','indice','propriedade'):raise ValueError('Atribuição inválida')
        v=self.expr();self.tomar(';')
        return ('atribuir_alvo',alvo,v,op)


def analisar(codigo):
    try:return ParserEstruturas(codigo).parse()
    except (RecursionError,OverflowError):raise ValueError('Fonte excede limites de aninhamento')


def efeito_exato(op,a,b=0):
    if op in ('&&','||','!'):
        if type(a) is not bool or op!='!' and type(b) is not bool:raise ValueError('Lógica exige booleanos')
        return not a if op=='!' else (a and b if op=='&&' else a or b)
    if op=='comprimento':
        if type(a) not in (list,str):raise ValueError('Comprimento exige array ou string')
        return len(unidades(a)) if type(a) is str else len(a)
    if op=='indice':
        if type(a) is not list or type(b) is not int or not 0<=b<len(a):raise ValueError('Índice inválido')
        return a[b]
    if op in ('===','!=='):
        from verificacao_codigo import iguais
        if type(a) in (dict,list) or type(b) in (dict,list):raise ValueError('Igualdade de estruturas fora do subconjunto')
        igual=iguais(a,b);return igual if op=='===' else not igual
    if type(a) is not int or type(b) is not int:raise ValueError('Aritmética/comparação exige inteiros')
    if op=='+':v=a+b
    elif op=='-':v=a-b
    elif op=='*':v=a*b
    elif op=='<':return a<b
    elif op=='<=':return a<=b
    elif op=='>':return a>b
    elif op=='>=':return a>=b
    else:raise ValueError('Operação desconhecida')
    validar_valor(v);return v


def executar(codigo,entrada,previsor=None,max_passos=512):
    validar_valor(entrada)
    if not 1<=max_passos<=2048:raise ValueError('Orçamento inválido')
    ast=analisar(codigo);estado={'entrada':copy.deepcopy(entrada)};constantes={'entrada'};tracos=[];passos=0
    def tick():
        nonlocal passos
        passos+=1
        if passos>max_passos:raise ValueError('Orçamento esgotado')
    def efeito(op,a,b=0):
        v=efeito_exato(op,a,b) if previsor is None else previsor(op,copy.deepcopy(a),copy.deepcopy(b))
        validar_valor(v)
        if op in ('+','-','*','comprimento') and type(v) is not int or op in ('<','<=','>','>=','===','!==','&&','||','!') and type(v) is not bool:
            raise ValueError('Tipo previsto incompatível')
        tracos.append(dict(tipo='efeito',op=op,a=copy.deepcopy(a),b=copy.deepcopy(b),resultado=copy.deepcopy(v),origem='exato' if previsor is None else 'rede'))
        return v
    def ler_indice(a,i):
        if type(a) is not list or type(i) is not int or not 0<=i<len(a):raise ValueError('Índice inválido')
        return efeito('indice',a,i)
    def expr(e):
        tick();tipo=e[0]
        if tipo in ('num','literal'):validar_valor(e[1]);return e[1]
        if tipo=='var':
            if e[1] not in estado:raise ValueError('Variável ausente')
            return estado[e[1]]
        if tipo=='array':
            v=[expr(x) for x in e[1]];validar_valor(v);return v
        if tipo=='objeto':
            v={k:expr(x) for k,x in e[1]};validar_valor(v);return v
        if tipo=='un':return efeito(e[1],expr(e[2]))
        if tipo=='bin':
            op=e[1];a=expr(e[2])
            if op in ('&&','||'):
                if type(a) is not bool:raise ValueError('Lógica exige booleanos')
                if op=='&&' and not a or op=='||' and a:return a
            return efeito(op,a,expr(e[3]))
        if tipo=='indice':return ler_indice(expr(e[1]),expr(e[2]))
        if tipo=='propriedade':
            a=expr(e[1]);k=e[2]
            if k=='length' and type(a) in (str,list):return efeito('comprimento',a)
            if type(a) is not dict or k not in a:raise ValueError('Propriedade ausente')
            return a[k]
        if tipo=='metodo':
            a=expr(e[1]);nome=e[2];args=[expr(x) for x in e[3]]
            antes=copy.deepcopy(estado)
            if nome=='push' and type(a) is list and len(args)==1:
                validar_valor(a+[args[0]]);a.append(args[0]);v=efeito('comprimento',a)
            elif nome=='slice' and type(a) in (list,str) and len(args) in (1,2) and all(type(x) is int for x in args):
                seq=unidades(a) if type(a) is str else a
                v=copy.deepcopy(seq[args[0]:args[1] if len(args)==2 else None]);v=''.join(v).encode('utf-16-le',errors='surrogatepass').decode('utf-16-le',errors='surrogatepass') if type(a) is str else v
            elif nome=='includes' and len(args)==1 and type(a) in (list,str):
                if type(a) is str:
                    if type(args[0]) is not str:raise ValueError('includes string exige string')
                    v=''.join(unidades(args[0])) in ''.join(unidades(a))
                else:
                    from verificacao_codigo import iguais
                    if any(type(x) in (dict,list) for x in a) or type(args[0]) in (dict,list):raise ValueError('includes estrutural não suportado')
                    v=any(iguais(x,args[0]) for x in a)
            elif nome in ('trim','toLowerCase','toUpperCase') and type(a) is str and not args:
                v=a.strip(' \t\r\n\v\f\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff') if nome=='trim' else a.lower() if nome=='toLowerCase' else a.upper()
            else:raise ValueError('Método ou argumentos inválidos')
            validar_valor(v)
            tracos.append(dict(tipo='metodo_manual',nome=nome,antes=antes,depois=copy.deepcopy(estado)))
            return v
        raise ValueError('Expressão desconhecida')
    def referencia(alvo):
        if alvo[0]=='var':
            nome=alvo[1]
            if nome not in estado or nome in constantes:raise ValueError('Variável ausente ou constante')
            return estado,nome
        a=expr(alvo[1])
        if alvo[0]=='indice':
            i=expr(alvo[2])
            if type(a) is not list or type(i) is not int or not 0<=i<len(a):raise ValueError('Índice inválido')
            return a,i
        k=alvo[2]
        if type(a) is not dict or k in PROIBIDOS:raise ValueError('Objeto inválido')
        return a,k
    def bloco(ss):
        for s in ss:
            tick();tipo=s[0]
            if tipo=='declarar':
                if s[1] in estado or len(estado)>=16:raise ValueError('Declaração inválida')
                antes=copy.deepcopy(estado);estado[s[1]]=expr(s[2])
                if s[3]:constantes.add(s[1])
                tracos.append(dict(tipo='estado',antes=antes,depois=copy.deepcopy(estado)))
            elif tipo=='atribuir_alvo':
                antes=copy.deepcopy(estado);a,k=referencia(s[1]);op=s[3]
                if op!='=' and isinstance(a,dict) and k not in a:raise ValueError('Propriedade ausente')
                antigo=a[k] if op!='=' else None
                v=expr(s[2]);v=efeito(op[0],antigo,v) if op!='=' else v
                validar_valor(v);a[k]=v
                for x in estado.values():validar_valor(x)
                tracos.append(dict(tipo='estado',antes=antes,depois=copy.deepcopy(estado)))
            elif tipo=='expressao':expr(s[1])
            elif tipo=='retornar':raise Retorno(copy.deepcopy(expr(s[1])))
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
            else:raise ValueError('Statement desconhecido')
    try:bloco(ast)
    except Retorno as r:return dict(resultado=r.valor,estado=estado,tracos=tracos,passos=passos)
    raise ValueError('Programa não retornou')


def javascript(codigo,typescript=False,tipo_entrada='number'):
    analisar(codigo)
    return 'function resolver(entrada'+(': '+tipo_entrada if typescript else '')+') {\n'+codigo+'\n}'
