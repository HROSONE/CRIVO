"""Resolve referências exatas; nunca aproxima um número de versículo."""
import re
from composicao_textual import normalizar

LIVROS = ('Gênesis|Êxodo|Levítico|Números|Deuteronômio|Josué|Juízes|Rute|'
          '1 Samuel|2 Samuel|1 Reis|2 Reis|1 Crônicas|2 Crônicas|Esdras|Neemias|'
          'Ester|Jó|Salmos|Provérbios|Eclesiastes|Cântico de Salomão|Isaías|'
          'Jeremias|Lamentações|Ezequiel|Daniel|Oseias|Joel|Amós|Obadias|Jonas|'
          'Miqueias|Naum|Habacuque|Sofonias|Ageu|Zacarias|Malaquias|Mateus|Marcos|'
          'Lucas|João|Atos|Romanos|1 Coríntios|2 Coríntios|Gálatas|Efésios|'
          'Filipenses|Colossenses|1 Tessalonicenses|2 Tessalonicenses|1 Timóteo|'
          '2 Timóteo|Tito|Filêmon|Hebreus|Tiago|1 Pedro|2 Pedro|1 João|2 João|'
          '3 João|Judas|Apocalipse').split('|')
NOMES = {normalizar(n): normalizar(n) for n in LIVROS}
NOMES.update({'salmo': 'salmos', 'gn': 'genesis', 'ex': 'exodo', 'sl': 'salmos',
              'mt': 'mateus', 'mc': 'marcos', 'lc': 'lucas', 'jo': 'joao',
              '1co': '1 corintios', 'gl': 'galatas', 'ap': 'apocalipse'})
PADRAO = re.compile(r'(?<!\w)(' + '|'.join(re.escape(n) for n in sorted(NOMES, key=len, reverse=True)) +
                    r')\.?\s*(\d+)\s*:\s*(\d+)(?:\s*[-–]\s*(\d+))?((?:\s*[,;:]\s*\d+)*)')


def literal(texto):
    """Normalização com dois-pontos conservados, sem aproximação lexical."""
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold())
                   if unicodedata.category(c) != 'Mn')


def referencias(texto):
    # Listas e sequências compostas não podem ser reduzidas ao primeiro verso.
    return [(NOMES[m[1]], int(m[2]), int(m[3]), int(m[4] or m[3]), m[5].strip())
            for m in PADRAO.finditer(literal(texto))]


def responder(texto, compositor):
    if not isinstance(texto, str):
        return None
    refs = referencias(texto)
    if not refs:
        return None
    pedido = normalizar(texto).strip()
    pedido = re.sub(r'^(?:por favor |voce pode |pode )', '', pedido)
    if not (texto.strip().endswith('?') or
            re.match(r'^(?:o que|qual|quem|como|por que|explique|explica|interprete|comente|leia|mostre|resuma|compare|fale|me explique|me explica|me fale)\b', pedido) or
            PADRAO.fullmatch(literal(texto).strip())):
        return None  # Um relato pessoal que cita um versículo não é consulta.
    indice = {}
    for ident, item in compositor.itens.items():
        if item.get('area') != 'biblia':
            continue
        for alias in [item['nome']] + item.get('aliases', []):
            for ref in referencias(alias):
                indice.setdefault(ref, ident)
        for f in item['fatos']:
            rs = referencias(f.get('referencia_biblica', ''))
            # Uma referência com vários trechos não autoriza explicar cada
            # versículo separadamente. A cobertura é a síntese cadastrada.
            if len(rs) == 1 and not re.search(r',|\band\b', f.get('referencia_biblica', '')):
                indice.setdefault(rs[0], ident)
    if any(ref not in indice for ref in refs):
        return ('fora', 'Não tenho uma explicação cadastrada para essa referência exata. '
                'Não vou substituir por um versículo parecido. Consulte a Tradução do Novo Mundo: '
                'https://www.jw.org/pt/biblioteca/biblia/biblia-de-estudo/livros/', None)
    ids = tuple(dict.fromkeys(indice[ref] for ref in refs))
    if len(ids) != 1:
        return ('fora', 'Envie uma referência por vez para eu apresentar a síntese cadastrada de cada trecho.', None)
    return compositor._conceito(ids[0])
