"""Diagnóstico por contratos e reparos locais de AST no subconjunto JS próprio.

Uma correção que satisfaz exemplos é uma hipótese, não a intenção demonstrada.
Nenhuma referência ou caso reservado é aceito pela API de reparo.
"""
import copy
import json
import re
import time

from busca_estados import validar_casos
from interpretacao_estruturas import analisar, efeito_exato, executar
from execucao_rastreada import executar_rastreado
from verificacao_codigo import iguais

EXPRESSOES = {'num', 'literal', 'var', 'bin', 'un', 'array', 'objeto',
              'indice', 'propriedade', 'metodo'}
ARITMETICA = ('+', '-', '*')
COMPARACOES = ('<', '<=', '>', '>=', '===', '!==')
METODOS = ('trim', 'toLowerCase', 'toUpperCase', 'slice', 'includes', 'push')


def fonte_expr(e):
    tipo = e[0]
    if tipo == 'num':
        return str(e[1])
    if tipo == 'literal':
        return json.dumps(e[1], ensure_ascii=True)
    if tipo == 'var':
        return e[1]
    if tipo == 'bin':
        return '(' + fonte_expr(e[2]) + ' ' + e[1] + ' ' + fonte_expr(e[3]) + ')'
    if tipo == 'un':
        return '(!' + fonte_expr(e[2]) + ')'
    if tipo == 'array':
        return '[' + ', '.join(fonte_expr(x) for x in e[1]) + ']'
    if tipo == 'objeto':
        return '{' + ', '.join(k + ': ' + fonte_expr(v) for k, v in e[1]) + '}'
    if tipo == 'indice':
        return '(' + fonte_expr(e[1]) + ')[' + fonte_expr(e[2]) + ']'
    if tipo == 'propriedade':
        return '(' + fonte_expr(e[1]) + ').' + e[2]
    if tipo == 'metodo':
        return '(' + fonte_expr(e[1]) + ').' + e[2] + '(' + ', '.join(fonte_expr(x) for x in e[3]) + ')'
    raise ValueError('Expressão desconhecida')


def fonte_bloco(ss):
    return ' '.join(fonte_statement(s) for s in ss)


def fonte_statement(s):
    tipo = s[0]
    if tipo == 'declarar':
        return ('const ' if s[3] else 'let ') + s[1] + ' = ' + fonte_expr(s[2]) + ';'
    if tipo == 'atribuir_alvo':
        return fonte_expr(s[1]) + ' ' + s[3] + ' ' + fonte_expr(s[2]) + ';'
    if tipo == 'expressao':
        return fonte_expr(s[1]) + ';'
    if tipo == 'retornar':
        return 'return ' + fonte_expr(s[1]) + ';'
    if tipo in ('if', 'while'):
        out = tipo + ' (' + fonte_expr(s[1]) + ') { ' + fonte_bloco(s[2]) + ' }'
        if tipo == 'if' and s[3]:
            out += ' else { ' + fonte_bloco(s[3]) + ' }'
        return out
    raise ValueError('Statement desconhecido')


def percorrer(valor, caminho=()):
    # Percorre apenas posições tipadas da AST, nunca pares (chave, valor).
    yield caminho, valor
    if isinstance(valor, list):
        for i, filho in enumerate(valor):
            yield from percorrer(filho, caminho + (i,))
    elif isinstance(valor, tuple):
        tipo = valor[0]
        if tipo == 'objeto':
            for i, (_, filho) in enumerate(valor[1]):
                yield from percorrer(filho, caminho + (1, i, 1))
            return
        filhos = {'bin': (2, 3), 'un': (2,), 'array': (1,),
                  'indice': (1, 2), 'propriedade': (1,), 'metodo': (1, 3),
                  'declarar': (2,), 'atribuir_alvo': (1, 2),
                  'expressao': (1,), 'retornar': (1,),
                  'if': (1, 2, 3), 'while': (1, 2)}.get(tipo, ())
        for i in filhos:
            yield from percorrer(valor[i], caminho + (i,))


def substituir(valor, caminho, novo):
    if not caminho:
        return copy.deepcopy(novo)
    xs = list(valor)
    xs[caminho[0]] = substituir(xs[caminho[0]], caminho[1:], novo)
    return tuple(xs) if isinstance(valor, tuple) else xs


def fragmento(node):
    if isinstance(node, list):
        return fonte_bloco(node)
    return fonte_expr(node) if node[0] in EXPRESSOES else fonte_statement(node)


def gerar_edicoes(codigo, casos, limite=512):
    """Uma edição local, sem substituição por catálogo de programas completos."""
    validar_casos(casos)
    if type(limite) is not int or not 1 <= limite <= 1024:
        raise ValueError('Limite de edições deve estar em 1..1024')
    ast = analisar(codigo)
    nodes = list(percorrer(ast))
    nomes = sorted({n[1] for _, n in nodes if isinstance(n, tuple) and n[0] in ('var', 'declarar')})
    atomos = [('var', n) for n in nomes]
    entradas = [c['entrada'] for c in casos]
    if all(type(x) is list for x in entradas):
        atomos += [('indice', ('var', 'entrada'), ('var', n)) for n in nomes if n != 'entrada']
    if all(type(x) is dict for x in entradas):
        campos = sorted(set.intersection(*(set(x) for x in entradas)))[:16]
        for campo in campos:
            if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', campo):
                continue
            try:
                atomos.append(analisar('return entrada.' + campo + ';')[0][1])
            except ValueError:
                pass
    atomos += [n for _, n in nodes if isinstance(n, tuple) and n[0] in ('indice', 'propriedade')]
    atomos = list({fonte_expr(n): n for n in atomos}.values())[:64]
    edicoes = []
    vistos = {fonte_bloco(ast)}

    def adicionar(path, antes, depois, tipo, contexto):
        if len(edicoes) >= limite:
            return
        novo_ast = substituir(ast, path, depois)
        corpo = fonte_bloco(novo_ast)
        if corpo in vistos:
            return
        try:
            analisar(corpo)
        except ValueError:
            return
        vistos.add(corpo)
        edicoes.append(dict(corpo=corpo, caminho_ast=list(path), antes=fragmento(antes),
                            depois=fragmento(depois), tipo=tipo, contexto=contexto,
                            tamanho_delta=len(corpo) - len(codigo)))

    # Inserção/deleção vêm primeiro; a lista inteira é limitada e determinística.
    blocos = [((), ast)]
    for path, n in nodes:
        if not isinstance(n, tuple) or not n or n[0] not in ('if', 'while'):
            continue
        blocos.append((path + (2,), n[2]))
        if n[0] == 'if':
            blocos.append((path + (3,), n[3]))
        if n[0] == 'while':
            locais = sorted({v[1] for _, v in percorrer(n[1]) if isinstance(v, tuple) and v[0] == 'var' and v[1] != 'entrada'})
            for nome in locais:
                for op in ('+=', '-='):
                    novo = n[2] + [('atribuir_alvo', ('var', nome), ('num', 1), op)]
                    adicionar(path + (2,), n[2], novo, 'inserir_incremento', 'while')
    for path, bloco in blocos:
        for i, s in enumerate(bloco):
            if s[0] != 'retornar':
                adicionar(path, bloco, bloco[:i] + bloco[i+1:], 'remover_statement', s[0])
    for path, n in nodes:
        if not isinstance(n, tuple) or not n or n[0] not in EXPRESSOES | {'atribuir_alvo'}:
            continue
        tipo = n[0]
        if tipo == 'bin':
            ops = ARITMETICA if n[1] in ARITMETICA else COMPARACOES if n[1] in COMPARACOES else ('&&', '||')
            for op in ops:
                adicionar(path, n, ('bin', op, n[2], n[3]), 'operador', tipo)
        elif tipo == 'num':
            for valor in range(6):
                adicionar(path, n, ('num', valor), 'constante', tipo)
        elif tipo == 'metodo':
            for nome in METODOS:
                adicionar(path, n, ('metodo', n[1], nome, n[3]), 'metodo', tipo)
        elif tipo == 'atribuir_alvo':
            for op in ('=', '+=', '-='):
                adicionar(path, n, (tipo, n[1], n[2], op), 'atribuicao', tipo)
    # Troca de folha/subexpressão: nomes e campos vêm do código e dos exemplos.
    for path, n in nodes:
        if isinstance(n, tuple) and n and n[0] in ('var', 'indice', 'propriedade'):
            for atomo in atomos:
                adicionar(path, n, atomo, 'expressao', n[0])
    return edicoes


def avaliar(codigo, casos, previsor=None, max_passos=512, guardar_tracos=False):
    validar_casos(casos)
    resultados = []
    for c in casos:
        r = None
        try:
            r = executar_rastreado(codigo, c['entrada'], previsor, max_passos=max_passos)
            if 'erro' in r:
                raise ValueError(r['erro'])
            mutou = not iguais(r['estado']['entrada'], c['entrada'])
            item = dict(entrada=copy.deepcopy(c['entrada']), esperado=copy.deepcopy(c['saida']),
                        observado=r['resultado'], correto=iguais(r['resultado'], c['saida']) and not mutou,
                        entrada_modificada=mutou, passos=r['passos'])
            if guardar_tracos:
                item['tracos'] = r['tracos']
        except ValueError as exc:
            item = dict(entrada=copy.deepcopy(c['entrada']), esperado=copy.deepcopy(c['saida']),
                        correto=False, erro=str(exc))
        if guardar_tracos:
            tracos = r['tracos'] if r is not None else []
            item['tracos'] = tracos
            item['efeitos'] = [{k: v for k, v in t.items() if k not in ('tipo', 'origem')}
                               for t in tracos if t['tipo'] == 'efeito']
            if r is not None:
                item['estado_final'] = copy.deepcopy(r['estado'])
                item['passos'] = r['passos']
        resultados.append(item)
    return resultados


def diagnosticar(codigo, casos, ranking=None, limite=512, verificacoes=128):
    """Apenas exemplos de desenvolvimento. Devolve hipótese local verificável."""
    validar_casos(casos)
    if type(limite) is not int or not 1 <= limite <= 1024:
        raise ValueError('Limite de edições deve estar em 1..1024')
    if type(verificacoes) is not int or not 1 <= verificacoes <= limite:
        raise ValueError('Orçamento de verificações inválido')
    inicio = time.perf_counter()
    inicial = avaliar(codigo, casos, guardar_tracos=True)
    falhas = [i for i, r in enumerate(inicial) if not r['correto']]
    out = dict(inicial=inicial, primeiro_exemplo_falho=falhas[0] if falhas else None,
               casos_reservados_consultados=False, candidatos=0, verificadas=0,
               hipotese=None, corpo_corrigido=None, atende_desenvolvimento=not falhas,
               origem='ranking_proprio' if ranking is not None else 'ordem_estrutural')
    if falhas:
        cs = gerar_edicoes(codigo, casos, limite)
        out['candidatos'] = len(cs)
        if ranking is not None:
            cs = sorted(enumerate(cs), key=lambda p: (-ranking.nota(p[1], inicial), p[0]))
            cs = [c for _, c in cs]
        for c in cs[:verificacoes]:
            out['verificadas'] += 1
            r = avaliar(c['corpo'], casos)
            if all(x['correto'] for x in r):
                out.update(corpo_corrigido=c['corpo'], atende_desenvolvimento=True,
                           hipotese={k: v for k, v in c.items() if k != 'corpo'}, final=r)
                break
    out['segundos'] = time.perf_counter() - inicio
    out['explicacao'] = (
        'Programa atende aos exemplos fornecidos.' if not falhas else
        'Edição local satisfaz todos os exemplos de desenvolvimento. O trecho indicado é uma hipótese; outras correções podem satisfazer estes exemplos.'
        if out['corpo_corrigido'] else
        'Falha reproduzida; nenhuma edição dentro do orçamento satisfez todos os exemplos.')
    return out


def comparar_efeitos(codigo, entrada, previsor):
    """Distingue erro da rede de bug do programa: compara a MESMA fonte."""
    caso = [{'entrada': entrada, 'saida': None}]
    exato = avaliar(codigo, caso, guardar_tracos=True)[0]
    neural = avaliar(codigo, caso, previsor, guardar_tracos=True)[0]
    ea, eb = exato['efeitos'], neural['efeitos']
    diferenca = next((i for i in range(max(len(ea), len(eb)))
                      if i >= len(ea) or i >= len(eb) or not iguais(ea[i], eb[i])), None)
    return dict(primeiro_efeito_divergente=diferenca,
                efeito_exato=ea[diferenca] if diferenca is not None and diferenca < len(ea) else None,
                efeito_rede=eb[diferenca] if diferenca is not None and diferenca < len(eb) else None,
                erro_exato=exato.get('erro'), erro_rede=neural.get('erro'),
                interpretacao='Divergência do executor neural; não identifica por si só erro na intenção do programa.')
