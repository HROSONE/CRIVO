"""Leitura dos artefatos autorais em JSON ou JSON comprimido sem perdas."""
import gzip
import json
from pathlib import Path


def localizar(caminho):
    caminho = Path(caminho)
    if not caminho.is_file() and caminho.suffix == ".json":
        comprimido = caminho.with_suffix(".json.gz")
        if comprimido.is_file():
            return comprimido
    return caminho


def ler_json(caminho):
    caminho = localizar(caminho)
    abrir = gzip.open if caminho.suffix == ".gz" else open
    with abrir(caminho, "rt", encoding="utf-8") as arquivo:
        return json.load(arquivo)
