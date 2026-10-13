"""Síntese de funções Python a partir de exemplos, com conferência em cada exemplo.

Caminho 3 da programação do CRIVO: em vez de uma rede escrevendo código livre (que nas rodadas
anteriores compilou mas acertou 0 de 16), o CRIVO procura, numa gramática pequena e conhecida, a
menor expressão que reproduz todos os exemplos. Cada candidato é avaliado por este próprio módulo,
sem executar código de fora; o texto Python é só a tradução da expressão encontrada, e os testes
conferem que a tradução dá o mesmo resultado que a avaliação.

Busca de baixo para cima, por tamanho, com equivalência observacional: duas expressões que dão os
mesmos valores nos exemplos contam como uma só. Quando há mais de uma função mínima que bate com os
exemplos e elas discordam em outras entradas, o motor não escolhe no chute: devolve a entrada que
separa as duas, para a pessoa dizer qual é a saída certa.

Sem modelo de terceiros, sem rede neural, sem execução de código enviado pela pessoa.
"""
import math
import random

VOGAIS = frozenset("aeiouáéíóúâêôãõàAEIOUÁÉÍÓÚÂÊÔÃÕÀ")
LIMITE_INT = 10 ** 18
LIMITE_SEQ = 200
ERRO = object()


class Falha(Exception):
    pass


# ------------------------------------------------------------------ tipos e valores
def tipo_de(v):
    if type(v) is bool:
        return "bool"
    if type(v) is int:
        return "int"
    if type(v) is float:
        return "float"
    if type(v) is str:
        return "str"
    if type(v) is list:
        if all(type(x) is int for x in v):
            return "li"
        if all(type(x) is str for x in v):
            return "ls"
    return None


def conferir(v):
    t = tipo_de(v)
    if t is None:
        raise Falha("valor fora dos tipos aceitos")
    if t == "int" and abs(v) > LIMITE_INT:
        raise Falha("número grande demais")
    if t == "float" and (v != v or abs(v) > LIMITE_INT):
        raise Falha("número inválido")
    if t in ("str", "li", "ls") and len(v) > LIMITE_SEQ:
        raise Falha("sequência grande demais")
    if t == "ls" and any(len(x) > LIMITE_SEQ for x in v):
        raise Falha("texto grande demais")
    return v


def chave(v):
    """Forma hashable e estrita: True ≠ 1 e 2 ≠ 2.0 (a média dá 2.0; a divisão inteira dá 2)."""
    if v is ERRO:
        return ("erro",)
    if type(v) is list:
        return ("lista",) + tuple(chave(x) for x in v)
    if type(v) is bool:
        return ("b", v)
    if type(v) is float:
        return ("f", round(v, 9))
    if type(v) is int:
        return ("n", v)
    return ("s", v)


def iguais(a, b):
    return a is not ERRO and b is not ERRO and chave(a) == chave(b)


# ------------------------------------------------------------------ operações
# nome: (tipos dos argumentos, tipo de saída, função, molde Python, é chamada/átomo)
def _div(a, b):
    if b == 0:
        raise Falha("divisão por zero")
    return a / b


def _floordiv(a, b):
    if b == 0:
        raise Falha("divisão por zero")
    return a // b


def _mod(a, b):
    if b == 0:
        raise Falha("divisão por zero")
    return a % b


def _mul(a, b):
    r = a * b
    if abs(r) > LIMITE_INT:
        raise Falha("grande demais")
    return r


def _fatorial(n):
    if n < 0 or n > 20:
        raise Falha("fatorial fora do limite")
    return math.factorial(n)


def _primo(n):
    return n >= 2 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def _indice(seq, i):
    if not -len(seq) <= i < len(seq):
        raise Falha("índice fora")
    return seq[i]


def _nao_vazia(f):
    def g(seq):
        if not seq:
            raise Falha("sequência vazia")
        return f(seq)
    return g


def _soma_digitos(n):
    return sum(int(c) for c in str(abs(n)))


def _repete(s, n):
    if n < 0 or n * len(s) > LIMITE_SEQ:
        raise Falha("repetição grande")
    return s * n


OPS = {
    # números
    "soma": (("int", "int"), "int", lambda a, b: a + b, "{0} + {1}", False),
    "sub": (("int", "int"), "int", lambda a, b: a - b, "{0} - {1}", False),
    "mul": (("int", "int"), "int", _mul, "{0} * {1}", False),
    "divint": (("int", "int"), "int", _floordiv, "{0} // {1}", False),
    "resto": (("int", "int"), "int", _mod, "{0} % {1}", False),
    "div": (("int", "int"), "float", _div, "{0} / {1}", False),
    "igual_n": (("int", "int"), "bool", lambda a, b: a == b, "{0} == {1}", False),
    "menor_n": (("int", "int"), "bool", lambda a, b: a < b, "{0} < {1}", False),
    "maior_n": (("int", "int"), "bool", lambda a, b: a > b, "{0} > {1}", False),
    "menorigual_n": (("int", "int"), "bool", lambda a, b: a <= b, "{0} <= {1}", False),
    "maiorigual_n": (("int", "int"), "bool", lambda a, b: a >= b, "{0} >= {1}", False),
    "neg": (("int",), "int", lambda a: -a, "-{0}", False),
    "abs": (("int",), "int", abs, "abs({0})", True),
    "fatorial": (("int",), "int", _fatorial, "math.factorial({0})", True),
    "primo": (("int",), "bool", _primo, "eh_primo({0})", True),
    "par": (("int",), "bool", lambda a: a % 2 == 0, "{0} % 2 == 0", False),
    "impar": (("int",), "bool", lambda a: a % 2 == 1, "{0} % 2 == 1", False),
    "soma_digitos": (("int",), "int", _soma_digitos, "sum(int(c) for c in str(abs({0})))", True),
    "texto_n": (("int",), "str", str, "str({0})", True),
    # lógica
    "nao": (("bool",), "bool", lambda a: not a, "not {0}", False),
    "e": (("bool", "bool"), "bool", lambda a, b: a and b, "{0} and {1}", False),
    "ou": (("bool", "bool"), "bool", lambda a, b: a or b, "{0} or {1}", False),
    # textos
    "maiusc": (("str",), "str", str.upper, "{0}.upper()", True),
    "minusc": (("str",), "str", str.lower, "{0}.lower()", True),
    "inverte_s": (("str",), "str", lambda s: s[::-1], "{0}[::-1]", True),
    "apara": (("str",), "str", str.strip, "{0}.strip()", True),
    "tira_espacos": (("str",), "str", lambda s: s.replace(" ", ""), '{0}.replace(" ", "")', True),
    "tira_vogais": (("str",), "str", lambda s: "".join(c for c in s if c not in VOGAIS),
                    '"".join(c for c in {0} if c not in VOGAIS)', True),
    "tam_s": (("str",), "int", len, "len({0})", True),
    "conta_vogais": (("str",), "int", lambda s: sum(c in VOGAIS for c in s), "sum(c in VOGAIS for c in {0})", True),
    "palavras": (("str",), "ls", str.split, "{0}.split()", True),
    "letras": (("str",), "ls", list, "list({0})", True),
    "primeira_s": (("str",), "str", _nao_vazia(lambda s: s[0]), "{0}[0]", True),
    "ultima_s": (("str",), "str", _nao_vazia(lambda s: s[-1]), "{0}[-1]", True),
    "so_digitos": (("str",), "bool", str.isdigit, "{0}.isdigit()", True),
    "igual_s": (("str", "str"), "bool", lambda a, b: a == b, "{0} == {1}", False),
    "junta_s": (("str", "str"), "str", lambda a, b: conferir(a + b), "{0} + {1}", False),
    "comeca": (("str", "str"), "bool", str.startswith, "{0}.startswith({1})", True),
    "termina": (("str", "str"), "bool", str.endswith, "{0}.endswith({1})", True),
    "conta_s": (("str", "str"), "int", lambda a, b: a.count(b) if b else _erro(), "{0}.count({1})", True),
    "contem_s": (("str", "str"), "bool", lambda a, b: b in a, "{1} in {0}", False),
    "repete_s": (("str", "int"), "str", _repete, "{0} * {1}", False),
    "indice_s": (("str", "int"), "str", _indice, "{0}[{1}]", True),
    # listas de números
    "soma_l": (("li",), "int", sum, "sum({0})", True),
    "tam_li": (("li",), "int", len, "len({0})", True),
    "max_l": (("li",), "int", _nao_vazia(max), "max({0})", True),
    "min_l": (("li",), "int", _nao_vazia(min), "min({0})", True),
    "produto": (("li",), "int", lambda l: conferir(math.prod(l)), "math.prod({0})", True),
    "ordena_l": (("li",), "li", sorted, "sorted({0})", True),
    "ordena_desc_l": (("li",), "li", lambda l: sorted(l, reverse=True), "sorted({0}, reverse=True)", True),
    "inverte_li": (("li",), "li", lambda l: l[::-1], "{0}[::-1]", True),
    "sem_repetir_li": (("li",), "li", lambda l: list(dict.fromkeys(l)), "list(dict.fromkeys({0}))", True),
    "indice_li": (("li", "int"), "int", _indice, "{0}[{1}]", True),
    "conta_li": (("li", "int"), "int", lambda l, x: l.count(x), "{0}.count({1})", True),
    "contem_li": (("li", "int"), "bool", lambda l, x: x in l, "{1} in {0}", False),
    # listas de textos
    "tam_ls": (("ls",), "int", len, "len({0})", True),
    "junta_espaco": (("ls",), "str", lambda l: conferir(" ".join(l)), '" ".join({0})', True),
    "junta_nada": (("ls",), "str", lambda l: conferir("".join(l)), '"".join({0})', True),
    "ordena_ls": (("ls",), "ls", sorted, "sorted({0})", True),
    "inverte_ls": (("ls",), "ls", lambda l: l[::-1], "{0}[::-1]", True),
    "indice_ls": (("ls", "int"), "str", _indice, "{0}[{1}]", True),
}
AUXILIARES = {
    "eh_primo": "def eh_primo(n):\n    return n >= 2 and all(n % d for d in range(2, int(n ** 0.5) + 1))\n",
    "VOGAIS": 'VOGAIS = set("aeiouáéíóúâêôãõàAEIOUÁÉÍÓÚÂÊÔÃÕÀ")\n',
    "math.": "import math\n",
}
# Funções de um elemento usadas em map/filter e nas somas/contagens com condição.
HOF = {
    # nome: (tipo da lista, tipo da saída do corpo, tipo de saída, molde)
    "mapa": None,  # tratado à parte: a saída depende do corpo
    "filtra": None,
}


def _erro():
    raise Falha("valor inválido")


# ------------------------------------------------------------------ expressões
class Expr:
    __slots__ = ("op", "filhos", "tipo", "tam", "valor", "corpo")

    def __init__(self, op, filhos, tipo, tam, valor=None, corpo=None):
        self.op, self.filhos, self.tipo, self.tam, self.valor, self.corpo = op, filhos, tipo, tam, valor, corpo


def avaliar(ex, env):
    op = ex.op
    if op == "var":
        return env[ex.valor]
    if op == "const":
        return ex.valor
    if op in ("mapa", "filtra", "soma_se", "conta_se", "soma_mapa"):
        seq = avaliar(ex.filhos[0], env)
        nome = ex.corpo[0]
        f = lambda x: avaliar(ex.corpo[1], {**env, nome: x})
        if op == "mapa":
            return conferir([f(x) for x in seq])
        if op == "filtra":
            return [x for x in seq if f(x) is True]
        if op == "soma_mapa":
            return conferir(sum(f(x) for x in seq))
        if op == "conta_se":
            return sum(1 for x in seq if f(x) is True)
        return sum(x for x in seq if f(x) is True)
    args, _, fn, _, _ = OPS[op]
    vals = [avaliar(f, env) for f in ex.filhos]
    v = fn(*vals)
    conferir(v)
    return v


def texto_python(ex):
    op = ex.op
    if op == "var":
        return ex.valor
    if op == "const":
        return repr(ex.valor) if not isinstance(ex.valor, str) else '"%s"' % ex.valor.replace("\\", "\\\\").replace('"', '\\"')
    if op in ("mapa", "filtra", "soma_se", "conta_se", "soma_mapa"):
        seq, (nome, corpo) = texto_python(ex.filhos[0]), ex.corpo
        c = texto_python(corpo)
        return {"mapa": "[%s for %s in %s]" % (c, nome, seq),
                "filtra": "[%s for %s in %s if %s]" % (nome, nome, seq, c),
                "soma_mapa": "sum(%s for %s in %s)" % (c, nome, seq),
                "conta_se": "sum(1 for %s in %s if %s)" % (nome, seq, c),
                "soma_se": "sum(%s for %s in %s if %s)" % (nome, nome, seq, c)}[op]
    molde, atomo = OPS[op][3], OPS[op][4]
    partes = []
    for i, f in enumerate(ex.filhos):
        t = texto_python(f)
        filho_simples = (f.op in ("var", "mapa", "filtra", "soma_mapa", "conta_se", "soma_se") or
                         f.op == "const" and not (type(f.valor) is int and f.valor < 0) or
                         f.op in OPS and OPS[f.op][4] and not OPS[f.op][3].startswith(('"', "-")))
        marca = "{%d}" % i
        depois = molde[molde.index(marca) + len(marca):][:1]
        # Operador (a + b) e receptor de método/índice ((a + b).upper()) pedem parênteses.
        if not filho_simples and (not atomo or depois in (".", "[")):
            t = "(" + t + ")"
        partes.append(t)
    return molde.format(*partes)


def programa_python(ex, nome="resolver"):
    corpo = texto_python(ex)
    cabecalho = ""
    for chave_aux, fonte in AUXILIARES.items():
        if chave_aux in corpo:
            cabecalho += fonte
    if cabecalho:
        cabecalho += "\n\n"
    return "%sdef %s(entrada):\n    return %s\n" % (cabecalho, nome, corpo)


# ------------------------------------------------------------------ busca
BASE_INTS = (0, 1, 2, 3, 10)


def _constantes(entradas):
    """Constantes de base custam 1; as tiradas dos exemplos custam 2 (Occam: menos chute)."""
    ints, chars = set(BASE_INTS), {"", " "}
    for v in entradas:
        itens = v if isinstance(v, list) else [v]
        for x in itens:
            if type(x) is int and abs(x) <= 1000:
                ints.add(x)
            if type(x) is str:
                chars.update(x)
    ints = sorted(ints, key=lambda n: (n not in BASE_INTS, abs(n), n))[:12]
    return ints, sorted(chars, key=lambda c: (c not in ("", " "), c))[:30]


class Banco:
    """Expressões por tamanho, uma por (tipo, valores nos pontos de avaliação)."""

    def __init__(self, pontos, var, tipo_var, consts, limite_itens, n_exemplos=None):
        self.pontos, self.var, self.tipo_var = pontos, var, tipo_var
        # Nos exemplos a expressão não pode falhar; nas sondas, falhar é só mais um valor.
        self.n_exemplos = len(pontos) if n_exemplos is None else n_exemplos
        self.por_tam = {}
        self.vistos = set()
        self.itens = 0
        self.limite_itens = limite_itens
        ints, chars = consts
        self.add(Expr("var", (), tipo_var, 1, var), 1)
        for n in ints:
            t = 1 if n in BASE_INTS else 2
            self.add(Expr("const", (), "int", t, n), t)
        for c in chars:
            t = 1 if c in ("", " ") else 2
            self.add(Expr("const", (), "str", t, c), t)

    def valores(self, ex):
        out = []
        for i, p in enumerate(self.pontos):
            try:
                out.append(avaliar(ex, {self.var: p}))
            except (Falha, TypeError, ValueError, IndexError, ZeroDivisionError, OverflowError, RecursionError):
                if i < self.n_exemplos:
                    return None
                out.append(ERRO)
        return out

    def add(self, ex, tam):
        vals = self.valores(ex)
        if vals is None:
            return None
        k = (ex.tipo, tuple(chave(v) for v in vals))
        if k in self.vistos:
            return None
        self.vistos.add(k)
        self.por_tam.setdefault(tam, []).append((ex, vals))
        self.itens += 1
        return vals

    def de_tipo(self, tam, tipo):
        return [e for e, _ in self.por_tam.get(tam, ()) if e.tipo == tipo]


def _particoes(total, n):
    if n == 1:
        yield (total,)
        return
    for i in range(1, total - n + 2):
        for resto in _particoes(total - i, n - 1):
            yield (i,) + resto


def _crescer(banco, tam, extras=()):
    """Gera as expressões de tamanho `tam` a partir das menores."""
    for op, (args, saida, _, _, _) in OPS.items():
        if len(args) == 1:
            for e in banco.de_tipo(tam - 1, args[0]):
                yield Expr(op, (e,), saida, tam)
        else:
            for t1, t2 in _particoes(tam - 1, 2):
                for a in banco.de_tipo(t1, args[0]):
                    for b in banco.de_tipo(t2, args[1]):
                        yield Expr(op, (a, b), saida, tam)
    for gerar in extras:
        yield from gerar(banco, tam)


def _corpos(elementos, tipo_el, consts, tam_max=4, limite=4000):
    """Funções de um elemento (para map/filter), por equivalência nos elementos vistos."""
    if not elementos:
        return []
    b = Banco(elementos, "x_el", tipo_el, consts, limite)
    for tam in range(2, tam_max + 1):
        for ex in _crescer(b, tam):
            b.add(ex, tam)
            if b.itens > limite:
                break
    saida = []
    for tam in sorted(b.por_tam):
        for ex, _ in b.por_tam[tam]:
            if ex.op != "const" and _usa_var(ex, "x_el"):
                saida.append((tam, ex))
    return saida


def _usa_var(ex, nome):
    if ex.op == "var":
        return ex.valor == nome
    return any(_usa_var(f, nome) for f in ex.filhos) or bool(ex.corpo and _usa_var(ex.corpo[1], nome))


def _renomear(ex, nome):
    if ex.op == "var":
        return Expr("var", (), ex.tipo, 1, nome)
    return Expr(ex.op, tuple(_renomear(f, nome) for f in ex.filhos), ex.tipo, ex.tam, ex.valor, ex.corpo)


def sintetizar(exemplos, tam_max=8, limite_itens=60000, sondas=None, folga=1):
    """→ dict(programa, expressao, ambigua, pergunta, verificadas).

    exemplos: lista de {"entrada": v, "saida": v}, todas as entradas do mesmo tipo.
    Devolve programa=None se nada na gramática bate com todos os exemplos.
    """
    if not exemplos:
        raise Falha("sem exemplos")
    entradas = [conferir(e["entrada"]) for e in exemplos]
    saidas = [conferir(e["saida"]) for e in exemplos]
    tipos = {tipo_de(v) for v in entradas if v != []}
    if not tipos and entradas:
        tipos = {"li"}
    if len(tipos) != 1:
        raise Falha("as entradas precisam ser todas do mesmo tipo")
    tipo_var = tipos.pop()
    if tipo_var in ("bool", "float"):
        raise Falha("entrada precisa ser número inteiro, texto ou lista")
    sondas = sondas if sondas is not None else gerar_sondas(entradas, tipo_var)
    pontos = entradas + sondas
    consts = _constantes(entradas)
    banco = Banco(pontos, "entrada", tipo_var, consts, limite_itens, n_exemplos=len(entradas))
    n = len(entradas)
    alvo = tuple(chave(v) for v in saidas)

    # funções de um elemento para listas do problema
    extras = []
    if tipo_var in ("li", "ls", "str"):
        elementos = []
        for p in pontos:
            seqs = [p] if tipo_var != "str" else [p.split(), list(p)]
            for s in seqs:
                for x in s:
                    if x not in elementos:
                        elementos.append(x)
        el_int = [x for x in elementos if type(x) is int][:40]
        el_str = [x for x in elementos if type(x) is str][:40]
        corpos = {"int": _corpos(el_int, "int", consts) if el_int else [],
                  "str": _corpos(el_str, "str", consts) if el_str else []}

        def gerar_hof(b, tam):
            for tl in range(1, tam - 2):
                for tipo_l, tipo_el in (("li", "int"), ("ls", "str")):
                    for seq in b.de_tipo(tl, tipo_l):
                        for tc, corpo in corpos[tipo_el]:
                            if 1 + tl + tc != tam:
                                continue
                            c = _renomear(corpo, "x")
                            tc_saida = corpo.tipo
                            if tc_saida == "bool":
                                yield Expr("filtra", (seq,), tipo_l, tam, corpo=("x", c))
                                yield Expr("conta_se", (seq,), "int", tam, corpo=("x", c))
                                if tipo_el == "int":
                                    yield Expr("soma_se", (seq,), "int", tam, corpo=("x", c))
                            elif tc_saida in ("int", "str"):
                                saida_l = "li" if tc_saida == "int" else "ls"
                                yield Expr("mapa", (seq,), saida_l, tam, corpo=("x", c))
                                if tc_saida == "int":
                                    yield Expr("soma_mapa", (seq,), "int", tam, corpo=("x", c))
        extras.append(gerar_hof)

    solucoes, verificadas, tam_achado = [], 0, None

    def confere(ex, vals):
        return tuple(chave(v) for v in vals[:n]) == alvo

    for tam in sorted(banco.por_tam):
        for ex, vals in banco.por_tam[tam]:
            verificadas += 1
            if confere(ex, vals):
                solucoes.append((tam, ex, vals))
                tam_achado = tam if tam_achado is None else tam_achado
    completa = False  # terminou de olhar todas as alternativas até tam_achado + folga?
    for tam in range(2, tam_max + 1):
        if tam_achado is not None and tam > tam_achado + folga:
            completa = True
            break
        if banco.itens > limite_itens:
            break
        for ex in _crescer(banco, tam, extras):
            vals = banco.add(ex, tam)
            if vals is None:
                continue
            verificadas += 1
            if confere(ex, vals):
                solucoes.append((tam, ex, vals))
                if tam_achado is None:
                    tam_achado = tam
            if banco.itens > limite_itens:
                break
    if not solucoes:
        return dict(programa=None, expressao=None, ambigua=False, pergunta=None, verificadas=verificadas,
                    tamanho=None, completa=False)
    solucoes.sort(key=lambda s: s[0])
    melhor = solucoes[0]
    # Ambiguidade: outra solução de tamanho até `folga` acima discorda numa sonda?
    # A pergunta que vale é a que mais divide as funções ainda possíveis (as mais simples pesam
    # mais): qualquer resposta elimina muitas de uma vez. Empate: a entrada mais fácil de responder.
    pergunta = None
    pesos = [2.0 ** -(t - melhor[0]) for t, _, _ in solucoes]
    melhor_nota = None
    for i in range(n, len(pontos)):
        if melhor[2][i] is ERRO:
            continue
        grupos = {}
        for w, (_, _, vals) in zip(pesos, solucoes):
            if vals[i] is not ERRO:
                grupos[chave(vals[i])] = grupos.get(chave(vals[i]), 0.0) + w
        if len(grupos) < 2:
            continue
        nota = (max(grupos.values()) / sum(grupos.values()), _peso(pontos[i]))
        if melhor_nota is None or nota < melhor_nota:
            melhor_nota = nota
            outra = next(s_ for s_ in solucoes[1:] if s_[2][i] is not ERRO and not iguais(s_[2][i], melhor[2][i]))
            pergunta = dict(entrada=pontos[i], opcoes=[melhor[2][i], outra[2][i]],
                            alternativa=programa_python(outra[1]))
    # Sem ter olhado todas as alternativas do mesmo tamanho (orçamento acabou), não dá para dizer
    # que não há outra função: a resposta fica ambígua mesmo sem pergunta pronta.
    return dict(programa=programa_python(melhor[1]), expressao=melhor[1],
                ambigua=pergunta is not None or not completa, pergunta=pergunta, verificadas=verificadas,
                tamanho=melhor[0], completa=completa)


def _peso(v):
    """Quão simples é uma entrada para a pessoa responder de cabeça."""
    if type(v) is int:
        return abs(v)
    if type(v) is str:
        return len(v) * 2
    return sum(_peso(x) + 1 for x in v)


def gerar_sondas(entradas, tipo, n=14, semente=7):
    """Entradas extras, só para descobrir se duas funções que batem nos exemplos discordam."""
    rr = random.Random(semente)
    vistas, saida = {chave(e) for e in entradas}, []

    def add(v):
        try:
            conferir(v)
        except Falha:
            return
        if tipo_de(v) == tipo and chave(v) not in vistas:
            vistas.add(chave(v))
            saida.append(v)

    if tipo == "int":
        for v in [-7, -1, 1, 2, 5, 6, 9, 11, 12, 15, 21, 100, 101] + [e + d for e in entradas for d in (-1, 1)]:
            add(v)
    elif tipo == "str":
        letras = sorted({c for e in entradas for c in e}) or list("abc")
        for e in entradas:
            add(e[::-1]); add(e.upper()); add(e + e[:1]); add(e[1:]); add(" " + e); add(e.capitalize())
        for v in ["ana", "Ana", "aba", "ab", "Teste de frase", "xyz", "o", "12", "a b", "abc abc"]:
            add(v)
        for _ in range(4):
            add("".join(rr.choice(letras) for _ in range(rr.randint(1, 6))))
    elif tipo == "li":
        for v in [[0], [1, 2], [2, 1], [5, 5], [3, -1, 4], [10, 20, 30, 40], [-2, -4], [7, 1, 7, 3], [11, 12, 9],
                  [1, 2, 3, 4, 5, 6], [0, 0, 1]]:
            add(v)
        for e in entradas:
            add(e[::-1]); add(sorted(e)); add(e + [e[0]] if e else [4]); add([x + 1 for x in e])
    elif tipo == "ls":
        for v in [["a"], ["b", "a"], ["casa", "oi"], ["x", "y", "z"], ["Bom", "dia"], ["aa", "a", "aaa"], ["um", "um"]]:
            add(v)
        for e in entradas:
            add(e[::-1]); add(sorted(e)); add([x.upper() for x in e])
    rr.shuffle(saida)
    return saida[:n]
