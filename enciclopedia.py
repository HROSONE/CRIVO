"""Consulta à enciclopédia do CRIVO (o começo dos verbetes da Wikipédia em português).

Só entra quando o acervo não tem o assunto (identificador "fora"). Ela não é verdade conferida
pelo CRIVO: é o que a Wikipédia diz, e a resposta mostra a fonte. O verbete é achado pelo título
(sem acento, sem maiúscula; "Mercúrio" vale "Mercúrio (planeta)", o verbete mais longo). Não há
busca por semelhança: se o título não bate, ele não sabe.

Arquivo: artefatos/enciclopedia_pt/enciclopedia_pt.json.gz (scripts/construir_enciclopedia.py,
SHA conferido). Licença CC BY-SA: ver artefatos/enciclopedia_pt/NOTICE.
`CRIVO_DISABLE_ENCICLOPEDIA=1` desliga.
"""
import gzip
import hashlib
import json
import os
import re
from functools import lru_cache
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "artefatos" / "enciclopedia_pt"
ARQUIVO = PASTA / "enciclopedia_pt.json.gz"
SHA256 = "a86174a6cc48a1496ff5e77a3440edc5f187ce71d54a4343392363543ebea821"   # v2: 120 mil verbetes (notebooks/enciclopedia_wikipedia_colab.ipynb)
IDENT = "enciclopedia:wikipedia"

_ARTIGO = r"(?:(?:o|a|os|as|um|uma|uns|umas)\s+)?"
_PERGUNTAS = [
    re.compile(r"^(?:e\s+)?(?:o\s+)?(?:que|q)\s+(?:é|e|eh|são|sao|era|foi|significa|quer dizer)\s+" + _ARTIGO + r"(?P<x>.+)$"),
    re.compile(r"^(?:e\s+)?(?:quem|qm)\s+(?:é|e|eh|foi|era|são|foram)\s+" + _ARTIGO + r"(?P<x>.+)$"),
    re.compile(r"^(?:me\s+)?(?:fala|fale|conta|conte|explica|explique)(?:\s+(?:pra|para)\s+mim)?\s+(?:um\s+pouco\s+)?"
               r"(?:sobre|de|do|da|dos|das|o que é|o que e)\s+" + _ARTIGO + r"(?P<x>.+)$"),
    re.compile(r"^(?:o\s+)?(?:que|q)\s+(?:você|voce|vc)\s+sabe\s+(?:sobre|de|do|da|dos|das)\s+" + _ARTIGO + r"(?P<x>.+)$"),
    re.compile(r"^(?:você|voce|vc)\s+(?:sabe|conhece)\s+(?:o que é|o que e|quem (?:é|e|foi))\s+" + _ARTIGO + r"(?P<x>.+)$"),
    re.compile(r"^(?P<x>[^,]{2,60}),?\s+(?:o que é|o que e|quem é|quem e|quem foi)(?:\s+isso|\s+ele|\s+ela)?$"),
]


def desligada():
    return os.environ.get("CRIVO_DISABLE_ENCICLOPEDIA", "").strip().lower() in ("1", "true", "yes", "on", "sim")


def normalizar(t):
    import unicodedata
    t = unicodedata.normalize("NFD", t.casefold())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^\w\s-]", " ", t)
    return " ".join(t.split())


def assunto(fala):
    """O assunto de uma pergunta de enciclopédia ("o que é um ornitorrinco?" → "ornitorrinco"), ou None."""
    if not isinstance(fala, str):
        return None
    t = " ".join(fala.strip().split()).rstrip("?!. ").strip()
    if not t or len(t.split()) > 12:
        return None
    baixo = t[0].lower() + t[1:]
    for rx in _PERGUNTAS:
        m = rx.match(baixo)
        if m:
            x = m.group("x").strip(" ,;:")
            x = re.sub(r"\s+(?:mesmo|afinal|exatamente|aí|ai)$", "", x)
            if 1 <= len(x.split()) <= 6 and not re.search(r"\b(?:eu|você|voce|vc|isso|isto|aquilo|ele|ela|meu|minha)\b", x):
                return x
            return None
    return None


@lru_cache(maxsize=1)
def _dados():
    if desligada() or not ARQUIVO.is_file():
        return None
    bruto = ARQUIVO.read_bytes()
    if SHA256 is not None and hashlib.sha256(bruto).hexdigest() != SHA256:
        return None
    return json.loads(gzip.decompress(bruto))


def consultar(fala):
    """(título, frase) do verbete do assunto da fala, ou None."""
    x = assunto(fala)
    if x is None:
        return None
    enc = _dados()
    if enc is None:
        return None
    chave = normalizar(x)
    i = enc["chaves"].get(chave)
    if i is None and chave.endswith("s") and len(chave) > 4:
        i = enc["chaves"].get(chave[:-1])   # "ornitorrincos" → "ornitorrinco"
    if i is None:
        return None
    return enc["titulos"][i], enc["leads"][i]


def fonte(titulo):
    return "Fonte: Wikipédia, verbete «%s» (CC BY-SA)." % titulo


def status():
    enc = _dados()
    return {"ligada": enc is not None, "verbetes": enc["n"] if enc else 0, "sha256": SHA256,
            "fonte": "Wikipédia em português (wikimedia/wikipedia 20231101.pt)", "licenca": "CC BY-SA"}
