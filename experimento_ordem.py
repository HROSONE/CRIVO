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


def caracteristicas_com_ordem(texto, dimensao=512, peso_ordem=0.15):
    """Adiciona bigramas consecutivos sem deixar o sinal de ordem dominar.

    O vetor de texto base ja tem norma 1. Na implementacao inicial,
    acrescentar cada bigrama com peso 1 colocava varios valores grandes
    sobre um vetor inteiro de norma 1, apagando praticamente o sinal
    lexical. Agora normalizamos ordem separadamente antes da mistura.
    A opcao peso_ordem=0 reproduz EXATAMENTE o vetor de referencia.
    """
    if dimensao <= 0 or not math.isfinite(peso_ordem) or peso_ordem < 0:
        raise ValueError("Dimensão e peso inválidos")
    base = caracteristicas(texto, dimensao, modo="portugues_sem_filtro")
    if peso_ordem == 0:
        return base
    ordem = [0.0] * dimensao
    palavras = _palavras(texto)
    for a, b in zip(palavras, palavras[1:]):
        h = 2166136261
        for c in "ordem:" + a + "|" + b:
            h = ((h ^ ord(c)) * 16777619) & 0xffffffff
        ordem[h % dimensao] += 1.0
    norma_ordem = math.sqrt(sum(v*v for v in ordem))
    if not norma_ordem:
        return base
    misturado = [v + peso_ordem * (b / norma_ordem)
                 for v, b in zip(base, ordem)]
    norma = math.sqrt(sum(v*v for v in misturado)) or 1.0
    return [v / norma for v in misturado]


def similaridade(a, b):
    return sum(x*y for x, y in zip(a, b))
