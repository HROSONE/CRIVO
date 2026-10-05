"""Intenção e contexto antes das respostas cadastradas.

Camada determinística, sem pesos treinados, que roda antes do recuperador:

* ``EstadoConversa`` guarda objetivos, preferências e restrições declarados
  pelo usuário e responde perguntas sobre eles ("O que eu quero fazer hoje?").
  Uma pergunta sobre o próprio usuário nunca cai numa ficha genérica.
* ``calcular`` resolve aritmética com números em português (30.000, 2,5, "vezes").
* ``inferir`` aplica modus ponens/tollens a premissas em linguagem comum
  ("Se chove, a rua fica molhada. Está chovendo. O que acontece com a rua?"),
  reutilizando a lógica proposicional de ``raciocinio_ativo``.
* ``reformular_finalidade`` reconhece a mesma intenção em formulações
  diferentes ("Pra que a célula precisa da mitocôndria?" = função da mitocôndria).
* ``InvestigacaoChat`` liga o investigador de memória do laboratório ao chat.
* ``ConsultaPratica`` relaciona perguntas práticas ao acervo de programação.

Nada aqui inventa fatos: cada resposta vem do que o usuário disse, de uma
conta verificável, de premissas explícitas ou de uma ficha com fonte.
"""
import ast
import operator
import re
import unicodedata


def dobrar(texto):
    """Minúsculas sem acento, preservando o comprimento (spans valem no original)."""
    saida = []
    for c in texto:
        base = unicodedata.normalize("NFD", c)[0].lower()
        saida.append(base[0] if base else c)
    return "".join(saida)


def _limpar_fim(texto):
    return texto.strip().rstrip(" .!?;,…").strip()


_EMOCAO = re.compile(r"\b(?:ansios\w*|trist\w*|cansad\w*|medo|preocupad\w*|estress\w*|angusti\w*|"
                     r"sozinh\w*|desanimad\w*|frustrad\w*|chorar|chorando|deprimid\w*|exaust\w*|arrasad\w*|mal|pessim\w*)\b")
_PEDIDO_AO_BOT = re.compile(r"(?:saber|entender|conversar|falar|perguntar|ouvir|ver|que voce|que vc|"
                            r"uma? |ajuda|aprender o que|descobrir o que)\b")


_PESSOA = {"minha": "sua", "minhas": "suas", "meu": "seu", "meus": "seus", "comigo": "com você",
           "eu": "você", "me": "se", "mim": "você"}


def segunda_pessoa(texto):
    """“organizar minha mudança” → “organizar sua mudança”, ao devolver ao usuário."""
    def troca(m):
        nova = _PESSOA[m.group(0).lower()]
        return nova.capitalize() if m.group(0)[0].isupper() else nova
    return re.sub(r"\b(?:minhas?|meus?|comigo|eu|mim)\b", troca, texto, flags=re.I)


class EstadoConversa:
    """Objetivos, preferências e restrições da conversa (até seis de cada)."""
    LIMITE = 6

    def __init__(self):
        self.objetivos = []
        self.preferencias = []
        self.restricoes = []

    # ------------------------------------------------------------ memória
    def exportar(self):
        return {"objetivos": list(self.objetivos[-self.LIMITE:]),
                "preferencias": list(self.preferencias[-self.LIMITE:]),
                "restricoes": list(self.restricoes[-self.LIMITE:])}

    def carregar(self, dados):
        for campo in ("objetivos", "preferencias", "restricoes"):
            for item in dados.get(campo, []):
                self._guardar(getattr(self, campo), item)

    def _guardar(self, lista, item):
        item = _limpar_fim(item)
        if not item or len(item) > 200:
            return False
        chave = dobrar(item)
        for i, antigo in enumerate(lista):
            if dobrar(antigo) == chave:
                lista.pop(i)
                break
        lista.append(item)
        del lista[:-self.LIMITE]
        return True

    # ---------------------------------------------------------- declarar
    def interpretar(self, texto):
        """Devolve (tipo, conteúdo, forte) para uma declaração, ou None.

        ``forte`` indica uma preferência ou restrição inequívoca, que merece
        confirmação explícita. Objetivos são sempre guardados em silêncio: o
        diálogo existente responde a eles e alimenta o planejador.
        """
        if not isinstance(texto, str) or "?" in texto or len(texto) > 300:
            return None
        bruto = _limpar_fim(texto)
        f = dobrar(bruto)
        f2 = re.sub(r"^(?:ok|certo|entao|bom|olha|ah|oi|ola)[,!]?\s+", "", f)
        desloc = len(f) - len(f2)
        f = f2

        def corte(m, grupo="x"):
            return _limpar_fim(bruto[desloc + m.start(grupo):desloc + m.end(grupo)])

        m = re.fullmatch(r"(?:por favor,?\s+)?(?:nao (?:use|usa|utilize|inclua|coloque|mencione|me de|me mande)|evite)\s+(?P<x>.+?)(?:,?\s*por favor)?(?:\s+nas? (?:respostas?|explicacoes?))?",
                         f)
        if m and not re.match(r"(?:sei|entendi|lembro|consigo|posso)\b", m.group("x")):
            x = corte(m)
            if len(x.split()) <= 12 and not re.match(r"(?:nada|isso|problema)\b", dobrar(x)):
                return ("restricao", x, True)
        m = re.fullmatch(r"(?:eu\s+)?prefiro\s+(?P<x>.+)", f)
        if m:
            return ("preferencia", corte(m), True)
        m = re.fullmatch(r"(?:eu\s+)?gosto\s+(?:mais\s+)?de\s+(?P<x>(?:explicac|respost|exemplo|texto|resumo|codigo)\w*.*)", f)
        if m:
            return ("preferencia", corte(m), True)
        m = re.fullmatch(r"(?:a partir de agora|daqui (?:pra|para) frente|de agora em diante|sempre),?\s+"
                         r"(?:me\s+)?(?:explique|responda|fale|escreva|use|de)\s+(?P<x>.+)", f)
        if m:
            return ("preferencia", corte(m), True)
        m = re.fullmatch(r"(?:eu\s+)?quero\s+(?:que (?:voce|vc)\s+(?:me\s+)?(?:explique|responda)\s+(?:com|de forma|em)\s+|"
                         r"(?=(?:respostas|explicacoes)\b))(?P<x>.+)", f)
        if m:
            return ("preferencia", corte(m), True)

        m = re.fullmatch(r"(?:hoje|agora|esta semana|essa semana|amanha)?,?\s*(?:o\s+)?(?:minha|meu)\s+"
                         r"(?:tarefa|meta|prioridade|missao|objetivo|plano|foco|trabalho)\s+"
                         r"(?:de hoje|hoje|do dia|da semana|agora|principal)?\s*(?:e|sera|vai ser)\s+(?P<x>.+)", f)
        if m:
            return ("objetivo", corte(m), not _EMOCAO.search(f))
        m = re.fullmatch(r"(?:hoje|agora)?,?\s*(?:eu\s+)?(?:estou|to|tou)\s+(?P<v>trabalhando|focad[oa])\s+"
                         r"(?P<x>(?:em|no|na|nos|nas|num|numa)\s+.+)", f)
        if m:
            verbo = "trabalhar " if m.group("v") == "trabalhando" else "focar "
            return ("objetivo", verbo + corte(m), not _EMOCAO.search(f))
        m = re.fullmatch(r"(?P<pre>(?:hoje|agora|esta semana|essa semana|amanha),?\s+)?(?:eu\s+)?"
                         r"(?:quero|preciso|tenho que|tenho de|vou|pretendo|planejo|gostaria de)\s+"
                         r"(?P<x>.+?)(?P<pos>,?\s+(?:hoje|agora|esta semana|essa semana|amanha))?", f)
        if m and not _PEDIDO_AO_BOT.match(m.group("x")):
            primeira = m.group("x").split()[0]
            if re.fullmatch(r"\w+(?:ar|er|ir|or)", primeira) and len(m.group("x").split()) >= 2:
                temporal = bool(m.group("pre") or m.group("pos"))
                return ("objetivo", corte(m), temporal and not _EMOCAO.search(f))
        return None

    def observar(self, texto):
        achado = self.interpretar(texto)
        if achado is None:
            return None
        tipo, conteudo, _ = achado
        lista = {"objetivo": self.objetivos, "preferencia": self.preferencias,
                 "restricao": self.restricoes}[tipo]
        return achado if self._guardar(lista, conteudo) else None

    @staticmethod
    def confirmar(tipo, conteudo):
        if tipo == "objetivo":
            return ("Anotado: você quer %s. Vou manter isso em mente durante a conversa. "
                    "Quer dividir em etapas ou começar por alguma parte específica?" % conteudo)
        if tipo == "preferencia":
            return "Combinado: você prefere %s. Vou levar isso em conta nas próximas respostas." % conteudo
        return "Entendido: vou evitar %s nas próximas respostas." % conteudo

    # ---------------------------------------------------------- recordar
    _OBJETIVO = re.compile(
        r"(?:e\s+)?(?:(?:voce\s+)?(?:lembra|sabe|lembra-se)\s+)?(?:(?:d?o\s+)?que|qual|quais)\s+(?:e\s+|era\s+|sao\s+)?"
        r"(?:(?:eu\s+)?(?:(?:te\s+)?disse que\s+)?(?:quero|queria|preciso|precisava|vou|ia|pretendo|pretendia|tenho que|tinha que|planejei)\s+fazer"
        r"|(?:a\s+|as\s+|o\s+|os\s+)?(?:minha|minhas|meu|meus)\s+(?:tarefa|tarefas|meta|metas|objetivo|objetivos|prioridade|prioridades|plano|planos|foco|missao))"
        r"(?:\s+(?:hoje|agora|de hoje|do dia|atual|principal))?"
        r"|(?:e\s+)?(?:no|em)\s+que\s+(?:eu\s+)?(?:estou|to|tou|estava)\s+trabalhando(?:\s+(?:hoje|agora))?")
    _PREFERENCIA = re.compile(
        r"(?:e\s+)?(?:(?:voce\s+)?(?:lembra|sabe)\s+)?(?:como|de que (?:jeito|forma|modo))\s+(?:(?:que\s+)?eu\s+)?"
        r"(?:prefiro|gosto|quero|pedi|disse que prefiro)(?:\s+(?:que voce (?:explique|responda)|de|das|dos|as|os|que))*"
        r"(?:\s+(?:as\s+|os\s+)?(?:explicacoes|respostas|textos|coisas))?"
        r"|(?:e\s+)?(?:qual|quais)\s+(?:e\s+|sao\s+)?(?:a\s+|as\s+)?(?:minha|minhas)\s+preferencias?")
    _RESTRICAO = re.compile(
        r"(?:e\s+)?(?:(?:voce\s+)?(?:lembra|sabe)\s+)?o\s+que\s+(?:eu\s+)?(?:te\s+)?(?:pedi|disse)\s+(?:para|pra)\s+(?:voce\s+)?(?:nao\s+\w+|evitar)")

    def responder(self, texto):
        """Responde perguntas sobre o próprio usuário; None se não for o caso."""
        if not isinstance(texto, str) or len(texto) > 200:
            return None
        f = _limpar_fim(dobrar(texto))
        if self._OBJETIVO.fullmatch(f):
            if not self.objetivos:
                return ("contexto:objetivo_desconhecido",
                        "Você ainda não me contou o que quer fazer. Se disser, por exemplo, "
                        "“hoje quero terminar o relatório”, eu guardo durante a conversa.")
            if len(self.objetivos) == 1:
                return "contexto:objetivo", "Você me disse que quer “%s”." % self.objetivos[0]
            itens = "; ".join("“%s”" % o for o in self.objetivos)
            return ("contexto:objetivo", "Você mencionou estes objetivos: %s. O mais recente foi “%s”."
                    % (itens, self.objetivos[-1]))
        if self._PREFERENCIA.fullmatch(f):
            if not self.preferencias:
                return ("contexto:preferencia_desconhecida",
                        "Você ainda não me disse como prefere as explicações. Pode dizer, por exemplo, "
                        "“prefiro explicações curtas com exemplos”.")
            texto_resp = "Você me disse que prefere %s." % "; ".join("“%s”" % p for p in self.preferencias)
            if self.restricoes:
                texto_resp += " E pediu para eu evitar %s." % "; ".join("“%s”" % r for r in self.restricoes)
            return "contexto:preferencia", texto_resp
        if self._RESTRICAO.fullmatch(f):
            if not self.restricoes:
                return ("contexto:restricao_desconhecida",
                        "Você ainda não me pediu para evitar nada nesta conversa.")
            return "contexto:restricao", "Você pediu para eu evitar %s." % "; ".join(
                "“%s”" % r for r in self.restricoes)
        return None

    # ----------------------------------------------------------- aplicar
    def prefere_curto(self):
        return any(re.search(r"\b(?:curt|breve|resumid|objetiv|diret|sucint)", dobrar(p))
                   for p in self.preferencias)

    _ENCURTAVEIS = ("conhecimento:", "escrita:", "composto:", "programacao:", "nocao:", "pratica:")

    def aplicar(self, ident, resposta, ids_editoriais=()):
        """Encurta respostas explicativas longas quando o usuário prefere assim."""
        if not self.prefere_curto() or not isinstance(resposta, str) or len(resposta) <= 260:
            return resposta
        if not (ident.startswith(self._ENCURTAVEIS) or ident in ids_editoriais):
            return resposta
        linhas = resposta.split("\n")
        fontes = [l for l in linhas if re.match(r"\s*(?:fontes?|referencias?)\s*:", dobrar(l))]
        corpo = next((l for l in linhas if l.strip() and l not in fontes), "")
        frases = re.split(r"(?<=[.!?])\s+", corpo.strip())
        curto = " ".join(frases[:2]).strip()
        if not curto or len(curto) >= len(resposta) - 40:
            return resposta
        saida = curto
        if fontes:
            saida += "\n" + fontes[0].strip()
        return saida + "\n(Resumi porque você prefere explicações curtas; peça a versão completa se quiser.)"


# ---------------------------------------------------------------- cálculo
_NUMEROS_ESCRITOS = {
    "zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5,
    "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12,
    "treze": 13, "catorze": 14, "quatorze": 14, "quinze": 15, "dezesseis": 16,
    "dezessete": 17, "dezoito": 18, "dezenove": 19, "vinte": 20, "trinta": 30,
    "quarenta": 40, "cinquenta": 50, "cem": 100, "mil": 1000,
}
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
_PEDIDO_CONTA = re.compile(
    r"(?:(?:e\s+)?quanto\s+(?:e|da|fica|vale|que e|seria)|calcule|calcula|calcular|resolva|resolve|"
    r"qual\s+(?:e\s+)?o\s+resultado\s+de|me\s+diz(?:er)?\s+quanto\s+(?:e|da)|faca\s+a\s+conta|"
    r"(?:voce\s+)?(?:sabe|consegue|pode)\s+(?:calcular|dizer quanto (?:e|da)))\s*:?\s+(?P<e>.+)")


def _expressao(texto):
    f = _limpar_fim(dobrar(texto)).rstrip("= ")
    m = _PEDIDO_CONTA.fullmatch(f)
    e = m.group("e") if m else f
    e = re.sub(r"^(?:a|o)\s+(?=raiz|\d)", "", e)
    if not m and not re.fullmatch(r"[\d\s.,+\-*/x×÷()%^−–—]+", e):
        return None
    e = e.replace("−", "-").replace("–", "-").replace("—", "-").replace("×", "*").replace("÷", "/")
    e = re.sub(r"\braiz quadrada de\s+(\d[\d.,]*)", r"(\1)**0.5", e)
    e = re.sub(r"(\d[\d.,]*)\s*%\s*de\s+", r"\1/100*", e)
    trocas = ((r"\bmultiplicado por\b", "*"), (r"\bvezes\b", "*"), (r"\bdividido por\b", "/"),
              (r"\bmais\b", "+"), (r"\bmenos\b", "-"), (r"\belevado (?:a|ao)\b", "**"),
              (r"\bao quadrado\b", "**2"), (r"\bao cubo\b", "**3"), (r"(?<=\d)\s*x\s*(?=\d)", "*"),
              (r"\^", "**"))
    for padrao, op in trocas:
        e = re.sub(padrao, " %s " % op, e)
    e = re.sub(r"\b(" + "|".join(_NUMEROS_ESCRITOS) + r")\b", lambda m: str(_NUMEROS_ESCRITOS[m.group(1)]), e)
    # Milhar com ponto (30.000) e decimal com vírgula (2,5), como no português.
    e = re.sub(r"\b\d{1,3}(?:\.\d{3})+(?![\d,])", lambda m: m.group(0).replace(".", ""), e)
    e = re.sub(r"(?<=\d),(?=\d)", ".", e)
    e = " ".join(e.split())
    if (not re.fullmatch(r"[\d\s.+\-*/()%]+", e) or not re.search(r"\d", e)
            or not re.search(r"\d\s*(?:\*\*|[+\-*/%])\s*[\d(]|\*\*\s*0\.5", e)):
        return None
    return e


def _avaliar(no):
    if isinstance(no, ast.Expression):
        return _avaliar(no.body)
    if isinstance(no, ast.Constant) and type(no.value) in (int, float):
        return no.value
    if isinstance(no, ast.UnaryOp) and isinstance(no.op, (ast.USub, ast.UAdd)):
        valor = _avaliar(no.operand)
        return -valor if isinstance(no.op, ast.USub) else valor
    if isinstance(no, ast.BinOp) and type(no.op) in _OPS:
        a, b = _avaliar(no.left), _avaliar(no.right)
        if isinstance(no.op, ast.Pow) and (abs(b) > 64 or abs(a) > 1e6):
            raise OverflowError
        resultado = _OPS[type(no.op)](a, b)
        if isinstance(resultado, complex) or abs(resultado) > 1e18:
            raise OverflowError
        return resultado
    raise ValueError("expressão não suportada")


def formatar_numero(valor):
    """Número no padrão brasileiro: 15.000 e 2,5."""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    sinal = "-" if valor < 0 else ""
    if isinstance(valor, int):
        return sinal + "{:,}".format(abs(valor)).replace(",", ".")
    inteiro, _, decimal = ("%.6f" % abs(valor)).rstrip("0").partition(".")
    if not decimal.strip("0"):
        return sinal + "{:,}".format(int(inteiro)).replace(",", ".")
    return sinal + "{:,}".format(int(inteiro)).replace(",", ".") + "," + decimal


def calcular(texto):
    """(id, resposta) para uma conta pedida, ou None se o texto não for conta."""
    if not isinstance(texto, str) or len(texto) > 200:
        return None
    e = _expressao(texto)
    if e is None:
        return None
    try:
        valor = _avaliar(ast.parse(e, mode="eval"))
    except ZeroDivisionError:
        return "calculo:indefinido", "Divisão por zero não tem resultado definido."
    except (SyntaxError, ValueError, OverflowError, TypeError, MemoryError, RecursionError):
        return None
    legivel = re.sub(r"\s*\*\*\s*", "^", e)
    legivel = re.sub(r"\s*([+\-*/%])\s*", r" \1 ", legivel).replace("*", "×")
    legivel = re.sub(r"\d+(?:\.\d+)?", lambda m: formatar_numero(float(m.group(0)) if "." in m.group(0)
                                                                 else int(m.group(0))), legivel)
    legivel = " ".join(legivel.split()).replace("( ", "(").replace(" )", ")")
    legivel = re.sub(r"([\d.,]+) / 100 × ", r"\1% de ", legivel)
    legivel = re.sub(r"(^|\()\s*- ", r"\1-", legivel)
    legivel = re.sub(r"\(([\d.,]+)\)\^0,5", r"√\1", legivel)
    return "calculo:aritmetica", "%s = %s" % (legivel, formatar_numero(valor))


# -------------------------------------------------------------- inferência
_VAZIAS = set("""o a os as um uma uns umas de do da dos das em no na nos nas e e é esta estao está
estão estava estavam fica ficam ficou ficar fico fiquei ficaram ficamos vai vao vão ser estar sempre entao então que com isso
ele ela eles elas la lá hoje agora tambem também muito ja já realmente mesmo pois logo assim
""".split())
_NEGACAO = re.compile(r"\b(?:nao|nunca|jamais)\b")
_REGRA = re.compile(r"(?:se|quando|sempre que|caso)\s+(?P<a>.+?)(?:,\s*(?:entao\s+)?|\s+entao\s+)(?P<c>.+)")
_PERGUNTA_ABERTA = re.compile(r"(?:o que|que)\s+(?:acontece|aconteceu|ocorre|vai acontecer|podemos concluir|"
                              r"(?:se\s+)?pode concluir|da para concluir|concluimos|eu concluo|se conclui|se segue)"
                              r"(?:\s+(?:com|sobre|a respeito d[oae]s?)\s+(?P<alvo>.+))?|"
                              r"(?:e\s+)?(?:entao|e dai|qual a conclusao|qual e a conclusao|o que se conclui)")


_SUFIXOS = ("ando", "endo", "indo", "aram", "eram", "iram", "avam", "ava", "ado", "ada", "ados", "adas",
            "ido", "ida", "idos", "idas", "ou", "ei", "eu", "iu", "ia", "am", "em", "ar", "er", "ir",
            "as", "es", "os", "a", "e", "o", "s")


def _raiz(palavra):
    """Radical rudimentar: “chovendo”, “chove” e “choveu” compartilham “chov”."""
    for sufixo in _SUFIXOS:
        if palavra.endswith(sufixo) and len(palavra) - len(sufixo) >= 3:
            palavra = palavra[:-len(sufixo)]
            break
    return palavra[:5]


def _chave(texto):
    f = dobrar(texto)
    palavras = [p for p in re.findall(r"[a-z0-9]+", f) if p not in _VAZIAS and p not in ("nao", "nunca", "jamais")]
    return frozenset(_raiz(p) for p in palavras)


def _semelhantes(a, b):
    if not a or not b:
        return False
    comum = len(a & b)
    return a == b or (comum and (a <= b or b <= a) and comum >= min(len(a), len(b))) or comum / len(a | b) >= 0.6


def _frase_literal(texto):
    texto = _limpar_fim(re.sub(r"^\s*(?:e|mas|logo|entao|então|agora|hoje)\s*,?\s+", "", texto, flags=re.I))
    return texto


class _Atomos:
    def __init__(self):
        self.chaves = []
        self.rotulos = []

    def literal(self, texto):
        from raciocinio_ativo import Literal
        rotulo = _frase_literal(texto)
        chave = _chave(rotulo)
        if not chave:
            raise ValueError("literal vazio")
        negativo = bool(_NEGACAO.search(dobrar(rotulo)))
        positivo = " ".join(re.sub(r"\b(?:não|nao)\s+", "", rotulo, flags=re.I).split())
        for i, existente in enumerate(self.chaves):
            if _semelhantes(chave, existente):
                return Literal("a%d" % i, negativo, self.rotulos[i])
        self.chaves.append(chave)
        self.rotulos.append(positivo)
        return Literal("a%d" % (len(self.chaves) - 1), negativo, positivo)


def _frases(texto):
    partes = re.split(r"(?<=[.;!?\n])\s*", texto)
    return [p.strip() for p in partes if p and p.strip(" .;!?\n")]


def _citar(textos):
    itens = ["“%s”" % (t[:1].lower() + t[1:]) for t in textos]
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def _texto_literal(lit):
    return ("não é verdade que " + lit.rotulo) if lit.negativo else lit.rotulo


class Inferencia:
    """Premissas da conversa em linguagem comum, válidas por até três turnos."""

    def __init__(self):
        self.premissas_texto = []
        self.turnos_sem_uso = 0

    def _ler(self, frases):
        regras, fatos, perguntas = [], [], []
        for frase in frases:
            f = _limpar_fim(dobrar(frase))
            f_sem_inicio = re.sub(r"^(?:e|mas|logo|entao|agora)\s*,?\s+", "", f)
            if frase.rstrip().endswith("?") or _PERGUNTA_ABERTA.fullmatch(f_sem_inicio):
                perguntas.append(frase)
                continue
            m = _REGRA.fullmatch(f_sem_inicio)
            desloc = len(f) - len(f_sem_inicio)
            bruto = _limpar_fim(frase)
            if m:
                regras.append((bruto[desloc + m.start("a"):desloc + m.end("a")],
                               bruto[desloc + m.start("c"):desloc + m.end("c")], bruto))
            else:
                fatos.append(bruto)
        return regras, fatos, perguntas

    def responder(self, texto):
        if not isinstance(texto, str) or len(texto) > 600:
            return None
        f = dobrar(texto)
        if re.match(r"\s*(?:considere|suponha|assuma|premissas?|hipotese)\b", f) or re.search(
                r"\b(?:todo|toda|todos|todas|nenhum|nenhuma|algum|alguma|alguns|algumas)\b", f):
            return None
        regras, fatos, perguntas = self._ler(_frases(texto))
        if not perguntas and (_EMOCAO.search(f) or any(not re.match(r"se\b", dobrar(r[2])) for r in regras)):
            # Sem pergunta, relatos com emoção ou narrativas com “quando”
            # (“Quando chove, fico triste.”) seguem para a conversa comum.
            return None
        if regras and not fatos and not perguntas:
            # Uma regra sozinha é guardada em silêncio para os próximos turnos.
            self.premissas_texto = (self.premissas_texto + [r[2] for r in regras])[-8:]
            self.turnos_sem_uso = 0
            return None
        if not regras:
            if not self.premissas_texto or not (perguntas or fatos):
                self.turnos_sem_uso += 1
                if self.turnos_sem_uso > 3:
                    self.premissas_texto = []
                return None
            r2, f2, _ = self._ler(_frases(". ".join(self.premissas_texto) + "."))
            # A fala nova precisa tratar do mesmo assunto das premissas guardadas.
            chaves = set().union(*(_chave(a) | _chave(c) for a, c, _ in r2))
            if not all(any(_semelhantes(_chave(x), _chave(y)) for a, c, _ in r2 for y in (a, c))
                       or (_chave(x) & chaves and x in perguntas) for x in fatos + perguntas):
                self.turnos_sem_uso += 1
                return None
            regras, fatos = r2, f2 + fatos
        if len(regras) > 6 or len(fatos) > 6 or len(perguntas) > 1:
            return None
        if not perguntas and not fatos:
            return None
        try:
            resultado = self._concluir(regras, fatos, perguntas)
        except Exception:
            return None
        if resultado is None:
            return None
        self.premissas_texto = [r[2] for r in regras] + list(fatos)
        self.turnos_sem_uso = 0
        return resultado

    def _concluir(self, regras, fatos, perguntas):
        from raciocinio_ativo import Premissa, SistemaPremissas
        atomos = _Atomos()
        premissas = []
        for a, c, bruto in regras:
            premissas.append(Premissa((atomos.literal(a),), atomos.literal(c), "e", bruto))
        literais_fatos = []
        for fato in fatos:
            lit = atomos.literal(fato)
            literais_fatos.append(lit)
            premissas.append(Premissa((), lit, "e", _limpar_fim(fato)))
        sistema = SistemaPremissas(premissas)
        textos_premissas = _citar([p.texto for p in premissas])
        aviso = "\nEssa conclusão vale sob as premissas que você deu; não verifica se elas são verdadeiras no mundo."
        if not sistema.mundos:
            return ("inferencia:conflito",
                    "As premissas %s se contradizem, então não autorizam conclusão nenhuma." % textos_premissas)
        pergunta = perguntas[0] if perguntas else None
        alvo_aberto = None
        if pergunta is not None:
            fp = _limpar_fim(re.sub(r"^(?:e|mas|logo|entao|agora)\s*,?\s+", "", dobrar(pergunta)))
            m = _PERGUNTA_ABERTA.fullmatch(fp)
            if m:
                alvo_aberto = _chave(m.group("alvo")) if m.groupdict().get("alvo") else frozenset()
        if pergunta is None or alvo_aberto is not None:
            dados = sistema.conclusoes()
            achados = []
            for c in dados.get("conclusoes", []):
                nome = c["alvo"]["nome"]
                indice = int(nome[1:])
                if alvo_aberto and not (atomos.chaves[indice] & alvo_aberto):
                    continue
                achados.append(c)
            if not achados and alvo_aberto:
                achados = list(dados.get("conclusoes", []))
            if not achados:
                if pergunta is None:
                    return None
                return ("inferencia:indeterminado",
                        "Com as premissas %s, não dá para concluir nada novo sobre isso. "
                        "Faltaria saber se as condições das regras acontecem." % textos_premissas + aviso)
            linhas = []
            for c in achados[:3]:
                provas = _citar([p["texto"] for p in c.get("provas", [])])
                linhas.append("%s, porque %s" % (c["alvo"]["texto"], provas))
            return ("inferencia:conclusao",
                    "Conclusão: " + "; ".join(linhas) + "." + self._nome_regra(achados[0], literais_fatos) + aviso)
        alvo = atomos.literal(pergunta)
        analise = sistema.analisar(alvo)
        provas = _citar([p["texto"] for p in analise.get("provas", [])] or ["as premissas"])
        if analise["status"] == "sustentado":
            return ("inferencia:sim", "Sim. Pelas premissas %s, segue que %s.%s" % (
                provas, _texto_literal(alvo), self._nome_regra(analise, literais_fatos)) + aviso)
        if analise["status"] == "refutado":
            return ("inferencia:nao", "Não. Pelas premissas %s, segue que %s.%s" % (
                provas, _texto_literal(alvo.oposto()), self._nome_regra(analise, literais_fatos)) + aviso)
        explicacao = self._falacia(regras, literais_fatos, alvo, atomos)
        return ("inferencia:indeterminado",
                "Não dá para concluir isso só com as premissas %s.%s" % (textos_premissas, explicacao) + aviso)

    @staticmethod
    def _nome_regra(analise, literais_fatos):
        if any(l.negativo for l in literais_fatos):
            return " (Isso é um modus tollens: negar a consequência nega a condição.)"
        return " (Isso é um modus ponens: a condição da regra aconteceu.)"

    @staticmethod
    def _falacia(regras, literais_fatos, alvo, atomos):
        for a, c, _ in regras:
            la, lc = atomos.literal(a), atomos.literal(c)
            for fato in literais_fatos:
                if fato == lc and alvo.nome == la.nome:
                    return (" Concluir “%s” a partir de “%s” seria afirmar o consequente: "
                            "“%s” pode ter outra causa." % (a, c, c))
                if fato.nome == la.nome and fato.negativo != la.negativo and alvo.nome == lc.nome:
                    return (" Negar a condição (“%s”) não basta para negar “%s”: seria negar o antecedente."
                            % (a, c))
        return " Faltam informações para decidir."


# --------------------------------------------------------- reformulação
_ART = r"(?:(?:o|a|os|as)\s+)?"
_QUALIFICADOR = r"(?P<q>\s+(?:para|pra|na|no|nas|nos|numa|num|em|de|do|da|dos|das|pela|pelo)\s+.+)?"
_FINALIDADE = (
    re.compile(r"(?:pra|para|por)\s+que\s+(?P<art>(?:o|a|os|as)\s+)?(?P<s>[a-z ]+?)\s+(?:precisa|precisam|necessita|"
               r"necessitam|depende|dependem|usa|usam|utiliza|utilizam)\s+(?:de\s+|do\s+|da\s+|dos\s+|das\s+)?(?P<x>[a-z ]+?)"),
    re.compile(r"por\s*que\s+(?P<x>(?:(?:o|a|os|as)\s+)?[a-z ]+?)\s+(?:e|sao|seria|seriam)\s+(?:tao\s+)?(?:importantes?|"
               r"necessari[oa]s?|essencia(?:l|is)|fundamenta(?:l|is)|vita(?:l|is)|indispensave(?:l|is))" + _QUALIFICADOR),
    re.compile(r"(?:qual|quais)\s+(?:e\s+|sao\s+)?(?:a\s+|o\s+)?(?:importancia|utilidade|papel|serventia)\s+"
               r"(?:de\s+|do\s+|da\s+|dos\s+|das\s+)(?P<x>[a-z]+(?:\s+[a-z]+)?)" + _QUALIFICADOR),
    re.compile(r"o\s+que\s+(?P<x>(?:o|a|os|as)\s+[a-z ]+?)\s+(?:faz|fazem)" + _QUALIFICADOR),
    re.compile(r"(?:pra|para)\s+que\s+(?:serve|servem)\s+(?P<x>[a-z ]+?)" + _QUALIFICADOR),
)
_EM = {"o ": "no ", "a ": "na ", "os ": "nos ", "as ": "nas "}


def reformular_finalidade(texto, reconhecer):
    """“Pra que a célula precisa da mitocôndria?” → “Para que serve a mitocôndria na célula?”.

    ``reconhecer(trecho)`` diz se o alvo é exatamente um conceito com ficha;
    sem ficha, nada é reformulado. Sujeito e qualificadores (“no Sol”, “de
    extraterrestres”) são mantidos para que o motor decida se há evidência:
    a paráfrase nunca apaga contexto.
    """
    if not isinstance(texto, str) or len(texto) > 200:
        return None
    bruto = _limpar_fim(texto)
    f = dobrar(bruto)
    f2 = re.sub(r"^(?:e\s+|mas\s+|me\s+(?:explica|diz|conta)\s*,?\s+|(?:voce\s+)?sabe\s+)", "", f)
    desloc = len(f) - len(f2)

    def trecho(m, grupo):
        return bruto[desloc + m.start(grupo):desloc + m.end(grupo)].strip()

    for padrao in _FINALIDADE:
        m = padrao.fullmatch(f2)
        if not m:
            continue
        alvo = trecho(m, "x")
        if not alvo or len(alvo.split()) > 4 or not reconhecer(alvo):
            continue
        contexto = ""
        if "s" in m.groupdict() and m.group("s"):
            artigo = m.group("art") or ""
            contexto = " " + _EM.get(artigo, "em ") + trecho(m, "s")
        elif m.groupdict().get("q"):
            contexto = " " + trecho(m, "q")
        return "Para que serve %s%s?" % (alvo, contexto)
    return None


# ---------------------------------------------------- investigação no chat
_MEMORIA_PROGRAMA = re.compile(
    r"\b(?:vazamento de memoria|memory leak|leak de memoria|out of memory|heap (?:cresce|crescendo|aumenta|estoura)|"
    r"(?:memoria|ram|heap|rss)\b.{0,40}\b(?:cresce\w*|aument\w*|sobe|subindo|consum\w*|estour\w*|vaza\w*|enche\w*)|"
    r"(?:consum\w*|cresce\w*|aument\w*|vaza\w*|gasta\w*|usa|usando|ocupa\w*|cada vez mais)\b.{0,40}\b(?:memoria|ram|heap))")
_CONTEXTO_PROGRAMA = re.compile(
    r"\b(?:programa|app|aplicac\w*|aplicativo|servidor|processo|node|nodejs|script|codigo|sistema|api|servico|"
    r"heap|rss|leak|vazamento|javascript|backend|container|worker|python|java|deploy)\b")


class InvestigacaoChat:
    """Conduz o investigador de heap do laboratório em turnos de conversa."""

    def __init__(self):
        self.investigador = None
        self.turno = 0

    @property
    def ativa(self):
        return self.investigador is not None

    def iniciar(self, texto):
        f = dobrar(texto)
        if not (_MEMORIA_PROGRAMA.search(f) and _CONTEXTO_PROGRAMA.search(f)):
            return None
        from investigacao_memoria import criar_investigacao
        self.investigador = criar_investigacao()
        self.turno = 0
        iniciais = {}
        if re.search(r"\b(?:node|nodejs|node\.js|express|nestjs)\b", f):
            iniciais["runtime"] = "node"
        elif re.search(r"\b(?:python|java|golang|rust|php|ruby|c#|dotnet|\.net|navegador|browser)\b", f):
            iniciais["runtime"] = "outro"
        if re.search(r"\bheap\b", f):
            iniciais["metrica"] = "heap"
        elif re.search(r"\b(?:rss|memoria total|gerenciador de tarefas|task manager)\b", f):
            iniciais["metrica"] = "rss"
        if iniciais:
            self.investigador.observar(iniciais, "turno:0")
        abertura = ("Vamos investigar sem chutar a causa. No modelo que tenho (heap JavaScript no Node), "
                    "as hipóteses são: objetos retidos sem utilidade, cache sem limite, fila de pedidos acumulada "
                    "ou apenas oscilação normal da coleta de lixo. Elas podem coexistir. ")
        return self._ciclo(abertura)

    _VALORES = {
        "runtime": ((r"\b(?:node|nodejs|node\.js|express|nestjs|javascript|js)\b", "node"),
                    (r"\b(?:python|java|golang|go|rust|php|ruby|c#|dotnet|\.net|navegador|browser|outro|outra|nao)\b", "outro"),
                    (r"\b(?:sim|isso|exato|uso|usa)\b", "node")),
        "metrica": ((r"\b(?:heap|heapused|heap used|heaptotal)\b", "heap"),
                    (r"\b(?:rss|total|processo|gerenciador|task manager|top|htop|docker stats|sistema)\b", "rss")),
    }
    _CRESCE = r"\b(?:cresce\w*|aument\w*|sobe|subindo|continua\w*|sim|piora\w*|acumula\w*|so cresce)\b"
    _ESTAVEL = (r"\b(?:estavel|estabiliza\w*|volta\w*|constante|para de crescer|nao cresce|nao aumenta|"
                r"nao|desce|cai|base)\b")

    def _ler(self, campo, f):
        if campo in self._VALORES:
            for padrao, valor in self._VALORES[campo]:
                if re.search(padrao, f):
                    return valor
            return None
        if re.search(r"\bnao (?:cresce|aumenta|sobe|acumula)\b|\b(?:estavel|estabiliza\w*|volta\w*|constante|para de crescer)\b", f):
            return "estavel"
        if re.search(self._CRESCE, f):
            return "cresce"
        if re.search(self._ESTAVEL, f):
            return "estavel"
        return None

    def continuar(self, texto):
        if not self.ativa or not isinstance(texto, str):
            return None
        f = _limpar_fim(dobrar(texto))
        ultimo = self.investigador.ultimo or {}
        campo = ultimo.get("campo")
        if re.fullmatch(r"(?:cancela\w*|para|parar|esquece|deixa pra la|mudar de assunto|chega)(?: .*)?", f):
            self.investigador = None
            return "investigacao:encerrada", "Tudo bem, encerrei a investigação de memória."
        if campo is None:
            self.investigador = None
            return None
        if re.search(r"\bnao sei\b|\bcomo (?:eu )?(?:sei|meco|medir|vejo|verifico)\b", f):
            return "investigacao:pergunta", self._como_medir(campo) + " Depois me diga o resultado: " + ultimo["pergunta"]
        valor = self._ler(campo, f)
        if valor is None:
            # Outra pergunta qualquer encerra a investigação e segue a conversa.
            if "?" in texto or len(f.split()) > 12:
                self.investigador = None
            return None
        self.turno += 1
        self.investigador.observar({campo: valor}, "turno:%d" % self.turno)
        return self._ciclo("")

    @staticmethod
    def _como_medir(campo):
        dicas = {
            "runtime": "Veja como o programa é iniciado: `node arquivo.js` ou `npm start` indicam Node.js.",
            "metrica": "No Node, `process.memoryUsage().heapUsed` mede o heap; `rss` é a memória total do processo.",
            "pos_gc": "Rode sob carga parecida e compare `heapUsed` depois de vários ciclos de coleta (por exemplo com `--trace-gc`).",
            "cache": "Registre periodicamente o tamanho do cache (quantidade de itens ou bytes).",
            "fila": "Registre periodicamente quantos pedidos estão pendentes e compare com a taxa de processamento.",
        }
        return dicas.get(campo, "Precisamos de uma medição para separar as hipóteses.")

    def _ciclo(self, abertura):
        from investigacao_memoria import FONTES, explicar
        resultado = self.investigador.investigar()
        acao = resultado["acao"]
        if acao in ("esclarecer", "perguntar"):
            return "investigacao:pergunta", abertura + resultado["pergunta"]
        self.investigador = None
        quadro = resultado["workspace"]["hipoteses"]
        compativeis = [h["descricao"] for h in quadro if h["estado"] == "compativel_no_modelo"]
        descartadas = [h["descricao"] for h in quadro if h["estado"] != "compativel_no_modelo"]
        partes = [abertura.strip()] if abertura.strip() else []
        if compativeis:
            partes.append("Compatíveis com o que você observou: " + " ".join("• " + c for c in compativeis))
        if descartadas:
            partes.append("Descartadas neste modelo: " + " ".join("• " + d for d in descartadas))
        partes.append(explicar(resultado))
        partes.append("Fontes: " + ", ".join(FONTES))
        return "investigacao:conclusao", "\n".join(partes)


# ------------------------------------------------------ consulta prática
_VAZIAS_PRATICA = set("""a o as os um uma de do da dos das em no na nos nas e que qual quais como para pra por
com sem se eu voce isso isto meu minha ele ela ser sao e esta estao posso pode devo fazer faz quando onde
tem ter uso usar usando realmente mesmo sim nao mais muito algum alguma ou porque entao ja nem certo certa
certos certas direito bem""".split())
_SINONIMOS_PRATICA = (
    (r"\bem tempo de execucao\b|\bem execucao\b|\btempo de execucao\b|\bruntime\b", " runtime "),
    (r"\bvalidar\b|\bvalida\b|\bvalidam\b|\bvalidacao\b|\bverifica\w*\b|\bchecar\b|\bcheca\b|\bgarant\w*\b", " valida "),
    (r"\bts\b", " typescript "), (r"\bjs\b", " javascript "),
)


def _termos(texto):
    f = " " + dobrar(texto) + " "
    for padrao, troca in _SINONIMOS_PRATICA:
        f = re.sub(padrao, troca, f)
    return {_raiz(p) for p in re.findall(r"[a-z0-9_$]+", f) if len(p) >= 3 and p not in _VAZIAS_PRATICA}


class ConsultaPratica:
    """Relaciona perguntas práticas ("interface valida JSON em execução?") às fichas."""
    _PROGRAMACAO = re.compile(r"\b(?:typescript|javascript|ts|js|node|interface|tipo|tipos|json|funcao|classe|"
                              r"objeto|array|promise|async|await|compilador|compilacao|runtime|codigo|api)\b")

    def __init__(self, catalogo):
        self.catalogo = catalogo
        self.indice = []
        if catalogo is None:
            return
        for u in catalogo.catalogo.get("unidades", []):
            nucleo = _termos(u.get("conceito", "") + " " + u.get("definicao", ""))
            corpo = _termos(" ".join(u.get(c, "") for c in ("mecanismo", "falhas_comuns", "criterio_de_escolha")))
            self.indice.append((u, nucleo, corpo))
        import math
        frequencia = {}
        for _, nucleo, corpo in self.indice:
            for termo in nucleo | corpo:
                frequencia[termo] = frequencia.get(termo, 0) + 1
        total = len(self.indice) or 1
        # Termos raros (json) distinguem mais que termos frequentes (api, tipo).
        self.peso = {t: math.log(1 + total / n) for t, n in frequencia.items()}

    def responder(self, texto):
        if not self.indice or not isinstance(texto, str) or len(texto) > 300:
            return None
        f = dobrar(texto)
        if not self._PROGRAMACAO.search(f) or re.search(r"\b(?:escreva|crie|implemente|gere|faca)\b", f):
            return None
        termos = _termos(texto)
        linguagem = "typescript" if termos & {"types"} else "javascript" if termos & {"javas"} else None
        termos -= {"types", "javas"}
        if len(termos) < 2:
            return None
        melhores = []
        for u, nucleo, corpo in self.indice:
            if linguagem and u.get("dominio") != linguagem:
                continue
            comum_nucleo = termos & nucleo
            comum = termos & (nucleo | corpo)
            if not comum_nucleo or len(comum) < 3 or len(comum) < 0.6 * len(termos):
                continue
            pontos = sum(self.peso.get(t, 0) for t in comum_nucleo) + sum(self.peso.get(t, 0) for t in comum)
            melhores.append((pontos, u))
        if not melhores:
            return None
        melhores.sort(key=lambda x: (-x[0], x[1]["id"]))
        if len(melhores) > 1 and melhores[1][0] >= 0.95 * melhores[0][0]:
            return None  # empate: melhor não responder do que escolher ao acaso
        u = melhores[0][1]
        abertura = self._sim_nao(f, u)
        refs = [self.catalogo.catalogo["fontes"][x]["url"] for x in u.get("fontes", [])
                if x in self.catalogo.catalogo.get("fontes", {})]
        resposta = (abertura + u["conceito"] + ": " + u["definicao"] + "\n\n" + u.get("mecanismo", "") +
                    "\n\nNa prática: " + u.get("criterio_de_escolha", "") +
                    "\nCuidados: " + u.get("falhas_comuns", "") +
                    "\nVerificação: " + u.get("verificacao", "") +
                    ("\nFontes: " + ", ".join(refs) if refs else "") +
                    "\nConsulta ao acervo autoral de programação; revisão editorial integral pendente.")
        return "pratica:" + u["id"], resposta

    @staticmethod
    def _sim_nao(f, unidade):
        if re.match(r"\s*(?:o que|como|qual|quais|quando|onde|por que|porque|quem|quanto|explique|me explica)\b", f):
            return ""
        definicao = " " + dobrar(unidade.get("definicao", "")) + " "
        for padrao, troca in _SINONIMOS_PRATICA:
            f = re.sub(padrao, troca, f)
        for verbo in re.findall(r"[a-z]{4,}", f):
            raiz = _raiz(verbo)
            if raiz in ("types", "javas", "inter", "objet"):
                continue
            if re.search(r"\bnao (?:\w+ )?" + re.escape(raiz), definicao):
                return "Não. "
        return ""
