"""Experimento isolado: acrescentar bigramas ordenados à representação portuguesa.

Não altera o comportamento do Crivo nem os pesos treinados. Sem dependências.
"""
import math
import re
import unicodedata

from rede_neural import caracteristicas


def _palavras(texto):
    from crivo import SINONIMOS, radical
    s = "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                if unicodedata.category(c) != "Mn")
    return [SINONIMOS.get(radical(p), radical(p))
            for p in re.findall(r"[a-z0-9]+", s)]


def caracteristicas_com_ordem(texto, dimensao=512, peso_ordem=1.0):
    """Mistura vetores portugueses com pares consecutivos de palavras.

    O hash tem prefixo próprio para não reutilizar n-gramas de caracteres.
    Mantém palavras funcionais: a ordem de sujeito e objeto importa.
    """
    if dimensao <= 0 or peso_ordem < 0:
        raise ValueError("Dimensão e peso inválidos")
    base = caracteristicas(texto, dimensao, modo="portugues_sem_filtro")
    palavras = _palavras(texto)
    for a, b in zip(palavras, palavras[1:]):
        h = 2166136261
        for c in "ordem:" + a + "|" + b:
            h = ((h ^ ord(c)) * 16777619) & 0xffffffff
        base[h % dimensao] += peso_ordem
    norma = math.sqrt(sum(v*v for v in base)) or 1.0
    return [v / norma for v in base]


def similaridade(a, b):
    return sum(x*y for x, y in zip(a, b))
