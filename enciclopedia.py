"""Consulta à enciclopédia do CRIVO (o começo dos verbetes da Wikipédia em português).

Só entra quando o acervo não tem o assunto (identificador "fora"). Ela não é verdade conferida
pelo CRIVO: é o que a Wikipédia diz, e a resposta mostra a fonte. O verbete é achado pelo título
(sem acento, sem maiúscula; "Mercúrio" vale "Mercúrio (planeta)", o verbete mais longo). Não há
busca por semelhança: se o título não bate, ele não sabe.

Arquivo: artefatos/enciclopedia_pt/enciclopedia_pt.v3.gz (scripts/construir_enciclopedia.py, SHA
conferido): 300 mil verbetes, lidos como um bloco só e achados por busca binária na lista de chaves, sem
virar 300 mil objetos Python (cabe no celular). Licença CC BY-SA: ver artefatos/enciclopedia_pt/NOTICE.
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
ARQUIVO = PASTA / "enciclopedia_pt.v3.gz"
SHA256 = "f2803ea5efdcbbe4124bdbfb04a4e54b6afc7c6f96bb9078a2f78b5d0284dbca"   # v3: 300 mil verbetes da mesma Wikipédia (20231101.pt)
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


class _Enciclopedia:
    """O arquivo aberto como um bloco de bytes, com o começo de cada linha num vetor."""

    def __init__(self, bruto):
        self.bloco = gzip.decompress(bruto)
        try:
            import numpy as np
            fins = np.flatnonzero(np.frombuffer(self.bloco, dtype=np.uint8) == 10)
            self.inicios = np.concatenate([[0], fins + 1]).astype(np.int64)
            self.fins = np.concatenate([fins, [len(self.bloco)]]).astype(np.int64)
        except ImportError:   # sem NumPy (o site sempre tem; alguns testes do CI não): a biblioteca padrão
            from array import array
            fins = array("q", (m.start() for m in re.finditer(b"\n", self.bloco)))
            self.inicios = array("q", [0]) + array("q", (f + 1 for f in fins))
            self.fins = fins + array("q", [len(self.bloco)])
        cab = json.loads(self.linha(0))
        if cab.get("versao") != 3 or len(self.inicios) != 1 + cab["n"] + cab["chaves"]:
            raise ValueError("enciclopédia em formato desconhecido")
        self.n, self.nchaves = cab["n"], cab["chaves"]

    def linha(self, i):
        return self.bloco[int(self.inicios[i]):int(self.fins[i])].decode("utf-8")

    def _chave(self, j):
        b = self.bloco[int(self.inicios[1 + self.n + j]):int(self.fins[1 + self.n + j])]
        k, _, i = b.rpartition(b"\t")
        return k, int(i)

    def indice(self, chave):
        alvo, lo, hi = chave.encode("utf-8"), 0, self.nchaves
        while lo < hi:
            meio = (lo + hi) // 2
            if self._chave(meio)[0] < alvo:
                lo = meio + 1
            else:
                hi = meio
        if lo < self.nchaves:
            k, i = self._chave(lo)
            if k == alvo:
                return i
        return None

    def verbete(self, i):
        titulo, _, frase = self.linha(1 + i).partition("\t")
        return titulo, frase


@lru_cache(maxsize=1)
def _dados():
    if desligada() or not ARQUIVO.is_file():
        return None
    bruto = ARQUIVO.read_bytes()
    if SHA256 is not None and hashlib.sha256(bruto).hexdigest() != SHA256:
        return None
    return _Enciclopedia(bruto)


def consultar(fala):
    """(título, frase) do verbete do assunto da fala, ou None."""
    x = assunto(fala)
    if x is None:
        return None
    enc = _dados()
    if enc is None:
        return None
    chave = normalizar(x)
    i = enc.indice(chave)
    if i is None and chave.endswith("s") and len(chave) > 4:
        i = enc.indice(chave[:-1])   # "ornitorrincos" → "ornitorrinco"
    if i is None:
        return None
    return enc.verbete(i)


def fonte(titulo):
    return "Fonte: Wikipédia, verbete «%s» (CC BY-SA)." % titulo


def status():
    enc = _dados()
    return {"ligada": enc is not None, "verbetes": enc.n if enc else 0, "sha256": SHA256,
            "fonte": "Wikipédia em português (wikimedia/wikipedia 20231101.pt)", "licenca": "CC BY-SA"}
