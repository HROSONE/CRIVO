"""Revisão conservadora de português, com original e alterações auditáveis.

Não é um corretor gramatical geral. Homógrafos e fronteiras de frases sem
evidência permanecem para revisão humana; nunca são completadas ideias.
"""
import re
from difflib import SequenceMatcher

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
}

# Não modificar código, citações, endereços, números ou abreviaturas.
PROTEGIDOS = re.compile(
    r'```[\s\S]*?(?:```|\Z)|`[^`\n]+`|"[^"\n]*"|“[^”]*”|'
    r'https?://[^\s<>]+|www\.[^\s<>]+|'
    r'[\w.+-]+@[\w.-]+\.[\w-]+|(?<!\w)@[\w]+|'
    r'\b[\w-]+\.[\w.-]+\b|'
    r'\b(?:[A-ZÀ-Ý]\.){2,}|\b(?:Dr|Dra|Sr|Sra|Prof|Profa|etc)\.|'
    r'\d+(?:[.,:/-]\d+)*(?:[ \u00a0]\d{3})*(?:%|º|ª)?')


def corrigir(original):
    """Retorna uma proposta e um diff que reconstrói exatamente a proposta."""
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
    elif t and re.search(r'[^\W\d_]$', t):
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
    notas.append('Revisão por regras limitadas: confira o resultado. Não avalio toda a gramática nem garanto equivalência de sentido.')
    alteracoes = []
    # Limita custo em documentos repetitivos; offsets continuam exatos mesmo
    # quando o diff agrupa várias modificações num único trecho.
    for op, a, b, c, d in SequenceMatcher(None, original, t).get_opcodes():
        if op != 'equal':
            alteracoes.append({'inicio': a, 'fim': b, 'antes': original[a:b],
                              'depois': t[c:d]})
    return {'origem': 'conteudo_enviado', 'metodo': 'regras_conservadoras',
            'original': original, 'corrigido': t, 'alteracoes': alteracoes,
            'regras': list(dict.fromkeys(regras)), 'avisos': notas}


def apresentar(resultado, detalhes=False):
    if detalhes:
        itens = ['- %r → %r (posição %d)' % (a['antes'], a['depois'], a['inicio'])
                 for a in resultado['alteracoes']]
        return ('Alterações propostas:\n' + '\n'.join(itens) if itens else
                'Não houve alterações pelas regras disponíveis.')
    titulo = 'Proposta de texto corrigido:' if resultado['alteracoes'] else 'Texto revisado — sem alterações pelas regras disponíveis:'
    return titulo + '\n\n' + resultado['corrigido'] + '\n\nNotas de revisão:\n' + '\n'.join('- ' + n for n in resultado['avisos'])
