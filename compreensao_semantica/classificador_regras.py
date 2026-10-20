"""Classificador de base, só com regras. Ponto de comparação para o classificador treinado.

Classifica o tipo da pergunta (quem, o que, qual, quanto, ...) e o alvo (sobre o Crivo,
sobre a pessoa, sobre o mundo, prática, outro). Não inventa informação: só lê o texto.
"""
import re
import unicodedata

PREFIXOS = re.compile(r"^(?:e ai,? |e aí,? |e |mas |então |entao |tu sabe |você sabe |voce sabe |sabe |me fala |me diz |oi,? |ola,? |olá,? )+")
REGRAS_TIPO = [
    ("para_que", r"^(para|pra) que\b"),
    ("por_que", r"^(por que|porque|pq)\b"),
    ("onde", r"^(onde|aonde|em que lugar)\b"),
    ("quando", r"^quando\b"),
    ("quanto", r"^quant[oa]s?\b"),
    ("como", r"^como\b"),
    ("quem", r"^quem\b"),
    ("qual", r"^qua(l|is)\b"),
    ("o_que", r"^o que\b"),
    ("se", r"^(se|e se)\b"),
]
PEDIDO = re.compile(r"^(me (explica|conta|fala|diz|mostra)|escreve|faz|cria|lista|pode me |consegue me |poderia )", re.I)


def normalizar(texto):
    t = unicodedata.normalize("NFD", texto.casefold().strip())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def tipo(texto):
    n = PREFIXOS.sub("", normalizar(texto)).strip(" ?!.,")
    for rotulo, padrao in REGRAS_TIPO:
        if re.search(padrao, n):
            return rotulo
    if PEDIDO.search(n) or re.match(r"^pode me ajudar", n):
        return "pedido"
    return "nenhum"


def alvo(texto):
    n = normalizar(texto)
    if re.search(r"\b(voce|vc|tu|seu|sua|seus|suas)\b", n) and not re.search(r"\bmeu|\bminh", n):
        return "sobre_o_crivo"
    if re.search(r"\b(eu|meu|minha|meus|minhas|me)\b", n):
        return "sobre_o_usuario"
    if re.search(r"\b(codigo|receita|bolo|senha|python|linguagem|lista|poema|conta|calcul)", n) or re.search(r"quanto é|quanto e", n):
        return "sobre_pratica"
    if tipo(texto) in ("nenhum",) or re.search(r"\b(tem|tá|ta|hoje|dia)\b", n) and tipo(texto) == "nenhum":
        return "outro"
    return "sobre_o_mundo"
