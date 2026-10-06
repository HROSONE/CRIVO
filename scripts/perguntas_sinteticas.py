"""Perguntas sintéticas a partir de um fato: (pergunta, trecho que responde).

Regras sobre a frase do fato: definição ("X é Y" → "O que é X?"), agente,
ano, quantidade, causa, lugar e exemplos. Usadas para treinar o leitor
Transformer (scripts/treinar_leitor_transformer.py); a resposta é sempre um
trecho exato da frase, então o rótulo "este fato responde" é seguro.

Veio do piloto do Leitor (branch leitor-piloto, scripts/gerar_leitor.py).
"""
import random
import re

COPULAS = r"(?:é|são|foi|foram|era|eram)"
NUMERO = r"\d[\d.,]*"


def frases(texto):
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9])", texto) if len(f.strip()) > 15]


def _sem_ponto(t):
    return t.rstrip(" .;:!?")


_MINUSCULAS = frozenset("o a os as um uma uns umas em no na nos nas este esta esse essa isso ele ela "
                        "eles elas seu sua seus suas cada todo toda muitos muitas alguns algumas".split())


def _minuscula_inicial(t):
    # Só artigos e palavras comuns viram minúscula; nomes próprios ficam.
    primeira = t.split(" ", 1)[0]
    return t[:1].lower() + t[1:] if primeira.lower() in _MINUSCULAS else t


_SUJEITO_RUIM = frozenset("como se quando mas isso isto ele ela eles elas também tambem assim só ja já ainda "
                          "mesmo porque nem quem onde que cada sua seu suas seus esse essa este esta".split())


def _sujeito_valido(sujeito):
    palavras = sujeito.split()
    return (len(palavras) <= 8 and palavras[0].lower() not in _SUJEITO_RUIM
            and not re.search(r"\b(?:não|nao)\b", sujeito) and "," not in sujeito)


def perguntas_da_frase(frase, nome=None, pessoa=False):
    """Lista de (pergunta, resposta) em que a resposta é trecho exato da frase."""
    saida = []
    f = _sem_ponto(frase)
    # Definição: “X é Y” → “O que é X?” / “Quem foi X?”
    m = re.match(r"^(.{2,60}?)\s+(" + COPULAS + r")\s+(.{8,})$", f)
    if m and not re.search(r"\d", m.group(1)) and _sujeito_valido(m.group(1)):
        sujeito, verbo, predicado = m.group(1), m.group(2), m.group(3)
        resposta = predicado.split(";")[0].strip(" ,")
        if pessoa or re.match(r"^[A-Z]", sujeito) and verbo in ("foi", "era") and re.match(r"(?:um|uma) ", predicado):
            saida.append(("Quem %s %s?" % (verbo, sujeito), resposta))
        elif re.match(r"^(?:O|A|Os|As) [a-zà-ú]", sujeito):
            # “O produto mais vendido é o pão de queijo” → “Qual é o produto mais vendido?”
            qual = "Quais" if sujeito.split()[0] in ("Os", "As") else "Qual"
            saida.append(("%s %s %s?" % (qual, verbo, _minuscula_inicial(sujeito)), resposta))
        else:
            saida.append(("O que %s %s?" % (verbo, _minuscula_inicial(sujeito)), resposta))
    # Agente: “Antônio Ferreira começou …” → “Quem começou …?”
    m = re.match(r"^((?:[A-ZÁÉÍÓÚ][\wÀ-ú]+)(?: (?:de |da |do |dos )?[A-ZÁÉÍÓÚ][\wÀ-ú]+)+),? ([a-zà-ú]+(?:ou|eu|iu|ava|ia|ram)) (.{6,})$", f)
    if m:
        saida.append(("Quem %s %s?" % (m.group(2), m.group(3)), m.group(1)))
    # Ano: “… em 1987 …” → “Quando …?”, “Em que ano …?”
    for m in re.finditer(r"\b(?:em|no ano de) (\d{4})\b", f):
        resto = (f[:m.start()] + f[m.end():]).strip(" ,")
        resto = re.sub(r"\s+,", ",", re.sub(r"\s{2,}", " ", resto))
        if len(resto) > 12:
            q = random.choice(("Quando %s?", "Em que ano %s?")) % _minuscula_inicial(resto)
            saida.append((q, m.group(0) if q.startswith("Quando") else m.group(1)))
    # Quantidade: “42 funcionários” → “Quantos funcionários …?”
    for m in re.finditer(r"\b(" + NUMERO + r")\s+([a-zà-ú]{3,}(?:\s+de\s+[a-zà-ú]{3,})?)", f):
        if re.fullmatch(r"\d{4}", m.group(1)) or m.group(2).split()[0] in ("que", "como", "para", "pelo", "pela"):
            continue
        unidade = m.group(2)
        antes = f[:m.start()].strip(" ,")
        if len(antes) > 8:
            fem = unidade.split()[0].endswith(("as", "a"))
            pal = "Quantas" if fem else "Quantos"
            saida.append(("%s %s %s?" % (pal, unidade, _minuscula_inicial(antes)), m.group(0)))
    # Causa: “… por causa de X” / “… porque X” → “Por que …?”
    m = re.search(r"^(.{10,}?)\s*,?\s+(por causa d[eoa]s? .{4,}|porque .{4,})$", f)
    if m:
        saida.append(("Por que %s?" % _minuscula_inicial(m.group(1).strip(" ,")), m.group(2)))
    # Lugar: “… em/no/na Lugar …” → “Onde …?”
    m = re.search(r"\b((?:em|no|na|nos|nas) (?:[A-ZÁÉÍÓÚÂÊÔ][\wÀ-ú-]+)(?: (?:(?:de|do|da|dos|das) )?[A-ZÁÉÍÓÚÂÊÔ][\wÀ-ú-]+)*)", f)
    if m and m.start() > 8:
        resto = (f[:m.start()] + f[m.end():]).strip(" ,")
        resto = re.sub(r"\s+,", ",", re.sub(r"\s{2,}", " ", resto))
        if len(resto) > 12 and not re.match(r"^(?:em|no|na) ", resto, re.I):
            saida.append(("Onde %s?" % _minuscula_inicial(resto), m.group(1)))
    # Exemplos: “como A, B e C” → “Quais são exemplos …?”
    m = re.search(r"\bcomo ([^,;.]+(?:, [^,;.]+)* e [^,;.]+)", f)
    if m and nome:
        saida.append(("Quais são exemplos citados sobre %s?" % nome, m.group(1)))
    return [(q, r) for q, r in saida if r and r in frase and len(r) < 160 and len(q.split()) <= 18]
