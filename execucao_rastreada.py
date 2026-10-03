"""Executor V2 com preservação de traços em falhas de execução.

A semântica foi copiada da baseline congelada para não alterar experimentos
anteriores. Acrescenta só retornos de erro e registro de efeitos que falham.
As hipóteses de reparo identificam posições estáticas na AST separadamente.
"""
import copy
from interpretacao_estados import Retorno
from interpretacao_estruturas import analisar, validar_valor, efeito_exato, unidades, PROIBIDOS


def executar_rastreado(codigo,entrada,previsor=None,max_passos=512):
    validar_valor(entrada)
    if not 1<=max_passos<=2048:raise ValueError('Orçamento inválido')
    ast=analisar(codigo);estado={'entrada':copy.deepcopy(entrada)};constantes={'entrada'};tracos=[];passos=0
    def tick():
        nonlocal passos
        passos+=1
        if passos>max_passos:raise ValueError('Orçamento esgotado')
    def efeito(op,a,b=0):
        try:
            v=efeito_exato(op,a,b) if previsor is None else previsor(op,copy.deepcopy(a),copy.deepcopy(b))
        except ValueError as exc:
            tracos.append(dict(tipo='efeito',op=op,a=copy.deepcopy(a),b=copy.deepcopy(b),erro=str(exc),origem='exato' if previsor is None else 'rede'))
            raise
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
    except ValueError as exc:return dict(erro=str(exc),estado=estado,tracos=tracos,passos=passos)
    return dict(erro='Programa não retornou',estado=estado,tracos=tracos,passos=passos)

