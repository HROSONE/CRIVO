"""Descobre e valida a base Transformer mais forte do CRIVO para conversa.

A base não é baixada da internet e nenhum provedor externo é usado. O runtime
só a ativa quando ``pesos.pt`` e ``tokenizer.json`` estão disponíveis localmente.
``CRIVO_TRANSFORMER_17M_DIR`` permite apontar explicitamente para a base.
"""
from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PESOS_SHA256 = "16102a72b21031b8bee2b4edfa633a359f7f08c5beab552b05f294e656b0cc67"
TOKENIZER_SHA256 = "6e3704ce921851122953b8ac20c05e3a131f9cf0fa3c76d6e2391c4ec3efc88f"


def _sha(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


@lru_cache(maxsize=8)
def _validar(pasta_texto: str, pesos_mtime: int, pesos_tamanho: int,
             tok_mtime: int, tok_tamanho: int) -> bool:
    pasta = Path(pasta_texto)
    pesos = pasta / "pesos.pt"
    tokenizer = pasta / "tokenizer.json"
    return (_sha(pesos) == PESOS_SHA256 and
            _sha(tokenizer) == TOKENIZER_SHA256)


def validar_base(pasta) -> bool:
    if not pasta:
        return False
    pasta = Path(pasta).expanduser().resolve()
    pesos, tokenizer = pasta / "pesos.pt", pasta / "tokenizer.json"
    if not pesos.is_file() or not tokenizer.is_file():
        return False
    ps, ts = pesos.stat(), tokenizer.stat()
    return _validar(str(pasta), ps.st_mtime_ns, ps.st_size,
                    ts.st_mtime_ns, ts.st_size)


def candidatos():
    explicito = os.environ.get("CRIVO_TRANSFORMER_17M_DIR", "").strip()
    if explicito:
        yield Path(explicito)
    # Destino recomendado para instalações locais/pacotes do CRIVO.
    yield RAIZ / "artefatos" / "transformer_leitor_17m" / "base"
    yield RAIZ / "artefatos" / "transformer-leitor" / "base"
    # Caminho usado pelo treino/exportação original em Colab + Drive montado.
    yield Path("/content/drive/MyDrive/CRIVO/transformer-leitor/base")
    # Conveniência para cópia local do diretório CRIVO no HOME.
    yield Path.home() / "CRIVO" / "transformer-leitor" / "base"


def localizar():
    """Retorna a base exata de 17,43M ou ``None`` sem quebrar o chat."""
    for pasta in candidatos():
        try:
            if validar_base(pasta):
                return str(Path(pasta).expanduser().resolve())
        except OSError:
            continue
    return None


def status():
    pasta = localizar()
    return {
        "preferido": "transformer_leitor_17m",
        "parametros": 17428224,
        "passo": 20000,
        "disponivel": bool(pasta),
        "pasta": pasta,
        "pesos_sha256": PESOS_SHA256 if pasta else None,
        "external_ai": False,
    }
