"""Léxico do português para a correção por dicionário (correcao_texto.py).

Duas fontes, sem nenhum modelo:
- as palavras escritas em minúsculas no começo dos 120 mil verbetes da Wikipédia que o projeto já
  guarda (artefatos/enciclopedia_pt); nomes próprios, que vêm em maiúscula, ficam fora;
- as 50 mil palavras mais frequentes de legendas em português do Brasil (dados/lexico_pt), a fala
  do dia a dia que a Wikipédia não tem ("abacaxi", "bagunça", "tô").
Uso: python scripts/construir_lexico.py
"""
import collections
import gzip
import hashlib
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "artefatos" / "enciclopedia_pt" / "enciclopedia_pt.json.gz"
LEGENDAS = RAIZ / "dados" / "lexico_pt" / "frequencia_legendas_pt_br_50k.txt"
DESTINO = RAIZ / "artefatos" / "lexico_pt" / "palavras.json.gz"
PALAVRA = re.compile(r"[a-záàâãéêíóôõúüç]+(?:-[a-záàâãéêíóôõúüç]+)*")


def principal():
    enc = json.loads(gzip.decompress(ORIGEM.read_bytes()))
    conta = collections.Counter(w for t in enc["leads"] for w in PALAVRA.findall(t) if len(w) <= 30)
    legendas = {}
    for linha in LEGENDAS.read_text(encoding="utf-8").splitlines():
        w, n = linha.rsplit(" ", 1)
        if PALAVRA.fullmatch(w):
            legendas[w] = int(n)
    dados = {"versao": 1,
             "fontes": {"wikipedia": {"fonte": enc["fonte"], "licenca": enc["licenca"],
                                      "sha256": hashlib.sha256(ORIGEM.read_bytes()).hexdigest()},
                        "legendas": {"fonte": "hermitdave/FrequencyWords, content/2018/pt_br/pt_br_50k.txt "
                                              "(OpenSubtitles 2018)", "licenca": "CC BY-SA 4.0",
                                     "sha256": hashlib.sha256(LEGENDAS.read_bytes()).hexdigest()}},
             "palavras": dict(sorted(conta.items(), key=lambda x: (-x[1], x[0]))),
             "legendas": legendas}
    bruto = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).encode()
    DESTINO.write_bytes(gzip.compress(bruto, 9, mtime=0))
    print(len(conta), "palavras;", DESTINO.stat().st_size, "bytes;",
          hashlib.sha256(DESTINO.read_bytes()).hexdigest())


if __name__ == "__main__":
    principal()
