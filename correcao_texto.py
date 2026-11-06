"""Revisão conservadora de português, com original e alterações auditáveis.

Não é um corretor gramatical geral. Homógrafos e fronteiras de frases sem
evidência permanecem para revisão humana; nunca são completadas ideias.
"""
import gzip
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

GRAFIAS = {
    'nao': 'não', 'voce': 'você', 'voces': 'vocês', 'tambem': 'também',
    'ninguem': 'ninguém', 'alguem': 'alguém', 'entao': 'então',
    'porem': 'porém', 'parabens': 'parabéns', 'possivel': 'possível',
    'impossivel': 'impossível', 'facil': 'fácil', 'dificil': 'difícil',
    'concerteza': 'com certeza', 'derrepente': 'de repente',
    'porfavor': 'por favor', 'excessao': 'exceção', 'excessão': 'exceção',
    'exceçao': 'exceção', 'anciedade': 'ansiedade', 'ansiedaade': 'ansiedade',
    'precizo': 'preciso', 'nescessario': 'necessário',
    'nescessário': 'necessário', 'nescessidade': 'necessidade',
    'conciente': 'consciente', 'consciencia': 'consciência',
    'inportante': 'importante', 'inpossivel': 'impossível',
    'compreensao': 'compreensão', 'pontuacao': 'pontuação',
    'amanha': 'amanhã', 'noticias': 'notícias', 'relatorio': 'relatório',
    'virgula': 'vírgula', 'virgulas': 'vírgulas', 'comcerteza': 'com certeza',
    'ortografiaa': 'ortografia', 'atraz': 'atrás', 'atras': 'atrás',
    'atravez': 'através', 'atraves': 'através', 'sabado': 'sábado',
    # Erros clássicos de ouvido: estão nas legendas, então a busca por distância não os trocaria
    # (ou trocaria por vizinha errada, como "pobrema" → "pobreza").
    'pobrema': 'problema', 'pobremas': 'problemas', 'poblema': 'problema', 'poblemas': 'problemas',
    'probrema': 'problema', 'menas': 'menos', 'seje': 'seja', 'sejem': 'sejam', 'esteje': 'esteja',
    'estejem': 'estejam', 'mendingo': 'mendigo', 'previlegio': 'privilégio', 'previlégio': 'privilégio',
    'impecilho': 'empecilho', 'adevogado': 'advogado', 'asteristico': 'asterisco', 'asterístico': 'asterisco',
    'beneficiente': 'beneficente', 'cardaço': 'cadarço', 'frustado': 'frustrado', 'frustada': 'frustrada',
    'iorgute': 'iogurte', 'mortandela': 'mortadela', 'cabeleleiro': 'cabeleireiro',
    'bicabornato': 'bicarbonato', 'largatixa': 'lagartixa', 'largato': 'lagarto', 'mussarela': 'muçarela',
    'enchergar': 'enxergar', 'enchergo': 'enxergo', 'exitar': 'hesitar', 'concerteza,': 'com certeza,', 'ezemplo': 'exemplo',
    'excesão': 'exceção', 'excesao': 'exceção', 'paralizar': 'paralisar', 'analizar': 'analisar',
}

# Não modificar código, citações, endereços, números ou abreviaturas.
PROTEGIDOS = re.compile(
    r'```[\s\S]*?(?:```|\Z)|`[^`\n]+`|"[^"\n]*"|“[^”]*”|'
    r'https?://[^\s<>]+|www\.[^\s<>]+|'
    r'[\w.+-]+@[\w.-]+\.[\w-]+|(?<!\w)@[\w]+|'
    r'\b[\w-]+\.[\w.-]+\b|'
    r'\b(?:[A-ZÀ-Ý]\.){2,}|\b(?:Dr|Dra|Sr|Sra|Prof|Profa|etc)\.|'
    r'\d+(?:[.,:/-]\d+)*(?:[ \u00a0]\d{3})*(?:%|º|ª)?')


LEXICO = Path(__file__).resolve().parent / "artefatos" / "lexico_pt" / "palavras.json.gz"
VOCABULARIO = Path(__file__).resolve().parent / "artefatos" / "vetores_pt" / "vocabulario.json"
# Trocas comuns de quem escreve depressa ou de ouvido custam meia letra.
PARECIDAS = {frozenset(p) for p in ("lr", "sz", "sc", "gj", "ie", "ou", "ul", "xs", "mn", "bv")}
_lexico = None


def _sem_acento(palavra):
    return "".join(c for c in unicodedata.normalize("NFD", palavra) if unicodedata.category(c) != "Mn")


def _carregar_lexico():
    """(conhecidas sem acento, alvos {sem acento: (forma, frequência na fala, na Wikipédia)}) ou None."""
    global _lexico
    if _lexico is None:
        try:
            lex = json.loads(gzip.decompress(LEXICO.read_bytes()))
            wiki, fala = lex["palavras"], lex["legendas"]
            conhecidas = {_sem_acento(w) for w in list(wiki) + list(fala)}
            conhecidas.update(json.loads(VOCABULARIO.read_text(encoding="utf-8")))
        except (OSError, ValueError, KeyError):
            _lexico = False
            return None
        conhecidas.update(_sem_acento(w) for w in list(GRAFIAS) + list(GRAFIAS.values()))
        alvos = {}
        for w in set(wiki) | set(fala):
            # Da Wikipédia, duas ocorrências pelo menos: um erro de digitação de lá não vira alvo.
            if len(w) < 4 or "-" in w or (w not in fala and wiki[w] < 2):
                continue
            k, chave = _sem_acento(w), (fala.get(w, 0), wiki.get(w, 0))
            if k not in alvos or alvos[k][1:] < chave:
                alvos[k] = (w,) + chave
        _lexico = (conhecidas, alvos)
    return _lexico or None


def _distancia(a, b, teto):
    """Damerau-Levenshtein com meia letra para as trocas parecidas; para acima do teto."""
    ant2, ant = None, [float(j) for j in range(len(b) + 1)]
    for i in range(1, len(a) + 1):
        atual = [float(i)] + [0.0] * len(b)
        for j in range(1, len(b) + 1):
            troca = 0.0 if a[i - 1] == b[j - 1] else (0.5 if frozenset((a[i - 1], b[j - 1])) in PARECIDAS else 1.0)
            # Letra dobrada a mais ou a menos ("pesoas", "pessoas") custa meia letra.
            tira = 0.5 if i > 1 and a[i - 1] == a[i - 2] else 1.0
            poe = 0.5 if j > 1 and b[j - 1] == b[j - 2] else 1.0
            atual[j] = min(ant[j] + tira, atual[j - 1] + poe, ant[j - 1] + troca)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                atual[j] = min(atual[j], ant2[j - 2] + 1)
        if min(atual) > teto:
            return teto + 1
        ant2, ant = ant, atual
    return ant[-1]


# Flexões e derivações: "cronogramas", "simplificadas", "dedicarmos", "indisponibilidade" são
# palavras certas que a lista não traz; se a raiz com outra terminação é conhecida, a palavra fica.
TERMINACOES = sorted({
    "s", "es", "a", "o", "as", "os", "e", "ns", "is", "ais", "eis", "oes", "aes", "ao", "m", "r",
    "ar", "er", "ir", "or", "ou", "eu", "iu", "ei", "ai", "am", "em", "ava", "avam", "ia", "iam",
    "ado", "ada", "ados", "adas", "ido", "ida", "idos", "idas", "ando", "endo", "indo",
    "aram", "eram", "iram", "arem", "erem", "irem", "armos", "ermos", "irmos", "amos", "emos", "imos",
    "asse", "esse", "isse", "assem", "essem", "issem", "ara", "era", "ira", "arao", "erao", "irao",
    "aria", "eria", "iria", "ariam", "eriam", "iriam", "ei", "aremos", "eremos", "iremos",
    "dor", "dora", "dores", "doras", "mente", "cao", "coes", "vel", "veis", "dade", "dades",
    "ivo", "iva", "ivos", "ivas", "oso", "osa", "osos", "osas", "ante", "antes", "ente", "entes",
    "eza", "ismo", "ista", "istas", "inho", "inha", "inhos", "inhas", "ize", "iza", "izar"}, key=len, reverse=True)
VOGAIS_FINAIS = ("a", "o", "e", "ar", "er", "ir", "as", "os", "es")
PREFIXOS = ("des", "in", "im", "re", "dis", "sub", "super", "anti", "auto", "pre", "inter", "sobre")


def _parece_conhecida(k, conhecidas):
    for fim in TERMINACOES:
        raiz = k[:-len(fim)]
        if not k.endswith(fim) or len(raiz) < 4:
            continue
        if fim in ("s", "es", "mente") and raiz in conhecidas:
            return True
        if fim in ("a", "o", "e", "r", "m") and any(raiz + outro in conhecidas for outro in VOGAIS_FINAIS):
            return True
        # Troca de terminação só entre terminações de duas letras ou mais ("pesoas" não é "peso" + "as").
        if len(fim) >= 2 and any(len(outro) >= 2 and raiz + outro in conhecidas for outro in TERMINACOES):
            return True
    return any(k.startswith(p) and len(k) - len(p) >= 4 and (k[len(p):] in conhecidas or
               _parece_conhecida(k[len(p):], conhecidas)) for p in PREFIXOS)


def sugerir(palavra):
    """A palavra do dicionário mais próxima de uma palavra desconhecida, ou None.

    Só troca quando a palavra não existe em nenhuma das listas e há uma única mais próxima,
    a até meia letra por letra parecida, uma letra (até 9 letras) ou duas e meia (palavras longas)."""
    lex = _carregar_lexico()
    p = palavra.lower()
    if lex is None or not 5 <= len(p) <= 25 or re.search(r"(.)\1\1", p):
        return None
    conhecidas, alvos = lex
    k = _sem_acento(p)
    if k in conhecidas or _parece_conhecida(k, conhecidas):
        return None
    teto = 1.0 if len(k) <= 6 else (1.5 if len(k) <= 9 else 2.5)
    pares = {k[i:i + 2] for i in range(len(k) - 1)}
    achados = []
    for alvo, (forma, na_fala, na_wiki) in alvos.items():
        if abs(len(alvo) - len(k)) > teto or len(pares & {alvo[i:i + 2] for i in range(len(alvo) - 1)}) < len(pares) / 3:
            continue
        # Quem erra quase nunca erra a primeira letra.
        d = _distancia(k, alvo, teto) + (0 if alvo[0] == k[0] else 0.5)
        if d <= teto:
            achados.append((d, -na_fala, -na_wiki, forma))
    achados.sort()
    if not achados or len(achados) > 1 and achados[1][0] == achados[0][0]:
        return None
    return achados[0][-1]


def corrigir(original, _palavra=False):
    """Retorna uma proposta e um diff que reconstrói exatamente a proposta."""
    # Uma citação inteira ("Corrija esta palavra: \"Palarerepípedo\"") é o próprio texto a corrigir.
    citada = re.fullmatch(r'(\s*["“])([^"“”\n]+)(["”]\s*)', original)
    if citada:
        dentro = corrigir(citada.group(2), _palavra=bool(re.fullmatch(r"\s*[^\W\d_]+\s*", citada.group(2))))
        t = citada.group(1) + dentro['corrigido'] + citada.group(3)
        return _resultado(original, t, dentro['regras'], dentro['avisos'])
    prefixo = '\ue000'
    while prefixo in original:
        prefixo += '\ue000'
    fim = '\ue001'
    while fim in original:
        fim += '\ue001'
    guardados = []

    def guardar(m):
        guardados.append(m.group())
        return prefixo + str(len(guardados) - 1) + fim

    t = PROTEGIDOS.sub(guardar, original)
    notas = []
    regras = []

    def aplicar(padrao, substituto, regra, flags=0):
        nonlocal t
        novo = re.sub(padrao, substituto, t, flags=flags)
        if novo != t:
            regras.append(regra)
            t = novo

    def grafia(m):
        palavra = m.group()
        # Maiúsculas podem identificar pessoas, marcas e siglas.
        inicio = not t[:m.start()].strip() or bool(re.search(r'[.!?\n][ \t]*$', t[:m.start()]))
        if palavra != palavra.lower() and not (palavra.istitle() and inicio):
            return palavra
        nova = GRAFIAS.get(palavra.lower(), palavra)
        return nova[:1].upper() + nova[1:] if palavra.istitle() else nova

    aplicar(r'\b[^\W\d_]+\b', grafia, 'grafias explícitas')
    trocadas = []

    def dicionario(m):
        palavra = m.group()
        inicio = not t[:m.start()].strip() or bool(re.search(r'[.!?\n][ \t]*$', t[:m.start()]))
        # Maiúscula no meio da frase pode ser nome; no começo, só numa palavra sozinha.
        if palavra != palavra.lower() and not (palavra.istitle() and inicio and _palavra):
            return palavra
        nova = sugerir(palavra)
        if nova is None:
            return palavra
        nova = nova[:1].upper() + nova[1:] if palavra.istitle() else nova
        trocadas.append((palavra, nova))
        return nova

    aplicar(r'(?<![\w-])[^\W\d_]+(?![\w-])', dicionario, 'dicionário')
    # Apenas pares com sujeito e verbo adjacentes; não inferir sujeitos.
    for sujeito, errado, certo in (
            ('eu', 'vai', 'vou'), ('eu', 'fomos', 'fui'),
            ('nós', 'vai', 'vamos'), ('nós', 'foi', 'fomos'),
            ('eles', 'vai', 'vão'), ('elas', 'vai', 'vão'),
            ('eles', 'foi', 'foram'), ('elas', 'foi', 'foram'),
            ('vocês', 'vai', 'vão'), ('vocês', 'foi', 'foram')):
        aplicar(r'\b(' + sujeito + r')([ \t]+(?:(?:não|nunca)[ \t]+)?)(' + errado + r')\b',
                lambda m, c=certo: m[1] + m[2] + (c.upper() if m[3].isupper() else c),
                'concordância local', re.I)
    aplicar(r'[ \t]+([,;:!?])', r'\1', 'espaço antes de pontuação')
    aplicar(r'([,;:!?])(?=[^\W\d_])', r'\1 ', 'espaço após pontuação')
    aplicar(r'([.])(?=[a-zà-ÿ])', r'\1 ', 'espaço após ponto')
    aplicar(r'[ \t]{2,}', ' ', 'espaços repetidos')
    # Pontuação inserida somente em construções explícitas.
    aplicar(r'(^|\n)(oi|olá|ola)[ \t]+tudo bem\b(?![.!])[?]?',
            lambda m: m[1] + ('Olá' if m[2].lower() in ('olá', 'ola') else 'Oi') + ', tudo bem?',
            'saudação interrogativa', re.I)
    aplicar(r'(^|\n)(oi|olá|ola)[ \t]+(?=tudo bem[.!])',
            lambda m: m[1] + ('Olá' if m[2].lower() in ('olá', 'ola') else 'Oi') + ', ',
            'vírgula na saudação', re.I)
    aplicar(r'(?<=[^\W\d_])[ \t]+(mas|porém|entretanto)\b', r', \1',
            'vírgula antes de contraste explícito', re.I)
    # Não acrescentar uma vírgula depois de "mas": pode separar o sujeito.
    aplicar(r'(^|\n)(por favor|com certeza|de repente)[ \t]+', r'\1\2, ',
            'expressão introdutória', re.I)
    aplicar(r'(^|[.!?][ \t]+|\n)([a-zà-ÿ])',
            lambda m: m[1] + m[2].upper(), 'início de frase')
    # Uma pergunta explícita curta dispensa inferir onde começa outra frase.
    if re.fullmatch(r'(?:Como|Quando|Onde|Por que) (?:você|vocês|ele|ela|eles|elas) '
                    r'(?:chegou|chegaram|mora|moram|foi|foram)(?: aqui| hoje| ontem)?', t):
        t = t.rstrip() + '?'
        regras.append('pergunta explícita')
    elif t and re.search(r'[^\W\d_]$', t) and not _palavra:
        t = t.rstrip() + '.'
        regras.append('pontuação final proposta')
    for i, trecho in enumerate(guardados):
        t = t.replace(prefixo + str(i) + fim, trecho)

    if len(re.findall(r'\b\w+\b', original)) >= 12 and not re.search(r'[.!?\n]', original):
        notas.append('O original não delimita as frases. Revise a divisão e a pontuação: não inseri fronteiras sem evidência.')
    if re.search(r'\b(?:esta|este|e|tem|vem|nos|pais|por que|porque|a|ha)\b', original, re.I):
        notas.append('Palavras que dependem do contexto (como e/é, esta/está, a/há ou por que/porque) não foram trocadas automaticamente.')
    if guardados:
        notas.append('Números, endereços, código, abreviaturas e citações foram preservados literalmente quando encontrados.')
    if trocadas:
        notas.append('Palavras fora do dicionário trocadas pela mais próxima: ' + ', '.join(
            '%s → %s' % par for par in dict.fromkeys(trocadas)) + '. Confira se era essa a palavra.')
    notas.append('Revisão por regras limitadas: confira o resultado. Não avalio toda a gramática nem garanto equivalência de sentido.')
    return _resultado(original, t, list(dict.fromkeys(regras)), notas)


def _resultado(original, t, regras, notas):
    alteracoes = []
    # Limita custo em documentos repetitivos; offsets continuam exatos mesmo
    # quando o diff agrupa várias modificações num único trecho.
    for op, a, b, c, d in SequenceMatcher(None, original, t).get_opcodes():
        if op != 'equal':
            alteracoes.append({'inicio': a, 'fim': b, 'antes': original[a:b],
                              'depois': t[c:d]})
    return {'origem': 'conteudo_enviado', 'metodo': 'regras_conservadoras',
            'original': original, 'corrigido': t, 'alteracoes': alteracoes,
            'regras': regras, 'avisos': notas}


def apresentar(resultado, detalhes=False):
    if detalhes:
        itens = ['- %r → %r (posição %d)' % (a['antes'], a['depois'], a['inicio'])
                 for a in resultado['alteracoes']]
        return ('Alterações propostas:\n' + '\n'.join(itens) if itens else
                'Não houve alterações pelas regras disponíveis.')
    titulo = 'Proposta de texto corrigido:' if resultado['alteracoes'] else 'Texto revisado — sem alterações pelas regras disponíveis:'
    return titulo + '\n\n' + resultado['corrigido'] + '\n\nNotas de revisão:\n' + '\n'.join('- ' + n for n in resultado['avisos'])


# --- dúvida de grafia: "como se escreve X?", "tá certo X?", "qual o certo, A ou B?", "X tem acento?" ---

_P = r'["“\']?([^\W\d_]+)["”\']?'
_COMO_ESCREVE = re.compile(r"^(?:e )?como (?:e que |que )?(?:se |eu )?escreve(?:r|-se)? (?:a palavra |o nome )?" + _P + r"\s*\??$")
_TA_CERTO = re.compile(r"^(?:(?:ta|tá|esta|está|é|e) cert[oa] (?:escrever |a palavra |falar |dizer )?" + _P +
                       r"|(?:a palavra )?" + _P + r" (?:ta|tá|esta|está|é|e) (?:cert[oa]|escrit[oa] cert[oa]|corret[oa])"
                       r"|(?:se )?escreve " + _P + r" mesmo)\s*\??$")
_A_OU_B = re.compile(r"^(?:qual (?:e |é )?(?:o |a )?(?:cert[oa]|corret[oa]|forma (?:certa|correta)|jeito certo)"
                     r"|como (?:e |é )?(?:o )?certo|(?:o )?certo (?:e|é))[:,]?\s*" + _P + r" ou " + _P + r"\s*\??$"
                     r"|^" + _P + r" ou " + _P + r"[,]? (?:qual (?:e |é )?(?:o |a )?(?:cert[oa]|corret[oa])|o que (?:e|é) certo)\s*\??$")
_ACENTO = re.compile(r"^(?:a palavra )?" + _P + r" (?:tem|leva|vai com|e com|é com) acento\s*\??$")
# Pares em que as duas formas existem e o sentido escolhe.
_PARES = {
    frozenset(("mais", "mas")): "“Mais” é de quantidade (mais água); “mas” liga ideias opostas, como “porém”.",
    frozenset(("mal", "mau")): "“Mal” é o contrário de “bem”; “mau” é o contrário de “bom”.",
    frozenset(("onde", "aonde")): "“Onde” é lugar em que se está; “aonde” é lugar para onde se vai (aonde você vai?).",
    frozenset(("sessão", "seção")): "“Sessão” é um tempo de reunião ou de cinema; “seção” é uma parte ou divisão.",
    frozenset(("cessão", "sessão")): "“Cessão” é o ato de ceder; “sessão” é um tempo de reunião ou de cinema.",
    frozenset(("cessão", "seção")): "“Cessão” é o ato de ceder; “seção” é uma parte ou divisão.",
    frozenset(("concerto", "conserto")): "“Concerto” é apresentação musical; “conserto” é reparo.",
    frozenset(("senão", "se não")): "“Senão” é “caso contrário”; “se não” é condição com negação (se não chover).",
    frozenset(("esta", "está")): "“Esta” aponta algo (esta casa); “está” é do verbo estar (ela está aqui).",
    frozenset(("e", "é")): "“E” liga palavras; “é” é do verbo ser.",
    frozenset(("a", "há")): "“Há” indica tempo passado ou existência (há dois anos); “a” é artigo, preposição ou tempo futuro.",
}
_formas = None


def _formas_do_lexico():
    """{sem acento: {formas}} das listas, para saber se "esta" e "está" existem as duas."""
    global _formas
    if _formas is None:
        _formas = {}
        try:
            lex = json.loads(gzip.decompress(LEXICO.read_bytes()))
            for w, n in list(lex["legendas"].items()) + [(w, n) for w, n in lex["palavras"].items() if n >= 5]:
                _formas.setdefault(_sem_acento(w), set()).add(w)
        except (OSError, ValueError, KeyError):
            pass
    return _formas


def _grafia(palavra):
    """(forma certa, a palavra já estava certa) ou None quando as listas não dizem nada."""
    w = palavra.lower()
    if w in GRAFIAS:
        return GRAFIAS[w], False
    lex = _carregar_lexico()
    if lex is None:
        return None
    conhecidas, alvos = lex
    k = _sem_acento(w)
    formas = set(_formas_do_lexico().get(k, set())) | ({alvos[k][0]} if k in alvos else set())
    if w in formas:
        return w, True
    if formas:
        # Só a forma acentuada existe ("paralelepipedo" → "paralelepípedo"): a de maior frequência.
        melhor = alvos[k][0] if k in alvos else sorted(formas)[0]
        return melhor, False
    if k in conhecidas:
        return w, True
    nova = sugerir(w)
    return (nova, False) if nova else None


def duvida_grafia(texto):
    """Resposta a uma dúvida de grafia, ou None se a fala não é uma."""
    if not isinstance(texto, str) or len(texto) > 120:
        return None
    t = " ".join(texto.strip().lower().split()).rstrip(" ?!.") + "?"
    t = re.sub(r"^(?:(?:crivo|mano|cara|vei|véi|velho|po|pô|ei|e ai|oi|amigo)[,!]? |me (?:diz|fala),? |"
               r"uma duvida:? |uma dúvida:? )+", "", t)
    t = re.sub(r"\bq\b", "que", t)
    m = _A_OU_B.match(t)
    if m:
        a, b = [g for g in m.groups() if g]
        ga, gb = _grafia(a), _grafia(b)
        par = _PARES.get(frozenset((a, b)))
        if par:
            return par
        if ga and gb and ga[1] and gb[1]:
            if _distancia(_sem_acento(a), _sem_acento(b), 3) > 2:
                return None  # "qual o certo, ir ou ficar?" é escolha, não grafia
            return "As duas formas existem (“%s” e “%s”); a certa depende do sentido da frase." % (a, b)
        certas = [g[0] for g in (ga, gb) if g and g[1]]
        if len(certas) == 1:
            return "O certo é “%s”." % certas[0]
        if ga and gb and ga[0] == gb[0]:
            return "Nenhuma das duas: o certo é “%s”." % ga[0]
        return "Não achei essas formas nas minhas listas; não consigo dizer qual é a certa."
    for padrao, tipo in ((_COMO_ESCREVE, "como"), (_TA_CERTO, "certo"), (_ACENTO, "acento")):
        m = padrao.match(t)
        if not m:
            continue
        w = next(g for g in m.groups() if g)
        g = _grafia(w)
        if g is None:
            return "Não achei “%s” nas minhas listas; não consigo confirmar a grafia." % w
        forma, certa = g
        if tipo == "como":
            return "Escreve-se “%s”." % forma if certa else "Escreve-se “%s” (e não “%s”)." % (forma, w)
        if tipo == "certo":
            return "Sim, “%s” está certo." % forma if certa else "Não. O certo é “%s”." % forma
        acentuada = forma != _sem_acento(forma)
        outras = _formas_do_lexico().get(_sem_acento(forma), set())
        par = next((txt for chave, txt in _PARES.items() if len(chave) == 2 and chave <= outras), None)
        if par:
            return par
        return ("Sim: “%s”." % forma) if acentuada else ("Não: “%s”, sem acento." % forma)
    return None
