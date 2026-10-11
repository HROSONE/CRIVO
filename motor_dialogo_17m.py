"""Descobre e valida bases Transformer 17,43M autorais do CRIVO.

Nenhuma base e baixada da internet. A base legada continua sendo a unica
variante elegivel pelo opt-in historico. O checkpoint composicional de
2026-10-11 fica registrado por SHA, mas exige opt-in experimental adicional e
caminho explicito; sua mera presenca nunca promove nem ativa o modelo no chat.
"""
from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PESOS_SHA256 = "16102a72b21031b8bee2b4edfa633a359f7f08c5beab552b05f294e656b0cc67"
TOKENIZER_SHA256 = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"
PESOS_COMPOSICIONAL_SHA256 = "eed38d9b097ffb908874158c6309720db7c65b792de82c6aca7bf91f36d58ec7"
VARIANTE_COMPOSICIONAL = "composicional_20261011"

BASES = {
    "leitor": {
        "nome": "transformer_leitor_17m",
        "pesos_sha256": PESOS_SHA256,
        "tokenizer_sha256": TOKENIZER_SHA256,
        "passo": 20000,
        "experimental": False,
        "promovido": False,
    },
    VARIANTE_COMPOSICIONAL: {
        "nome": "transformer_composicional_17m_20261011",
        "pesos_sha256": PESOS_COMPOSICIONAL_SHA256,
        "tokenizer_sha256": TOKENIZER_SHA256,
        "passo": 5000,
        "experimental": True,
        "promovido": False,
    },
}


def _env_verdadeiro(nome: str) -> bool:
    return os.environ.get(nome, "").strip().lower() in ("1", "true", "yes", "on")


def variante_solicitada() -> str:
    valor = os.environ.get("CRIVO_TRANSFORMER_17M_VARIANT", "leitor").strip().lower()
    if valor in ("", "legacy", "legado", "leitor"):
        return "leitor"
    return valor


def especificacao(variante: str | None = None):
    variante = variante or variante_solicitada()
    spec = BASES.get(variante)
    if spec is None:
        return None
    if spec["experimental"] and not _env_verdadeiro(
            "CRIVO_ENABLE_EXPERIMENTAL_COMPOSITIONAL_17M"):
        return None
    return spec


def _sha(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


@lru_cache(maxsize=16)
def _validar(pasta_texto: str, pesos_mtime: int, pesos_tamanho: int,
             tok_mtime: int, tok_tamanho: int, pesos_sha: str,
             tokenizer_sha: str) -> bool:
    pasta = Path(pasta_texto)
    pesos = pasta / "pesos.pt"
    tokenizer = pasta / "tokenizer.json"
    return (_sha(pesos) == pesos_sha and _sha(tokenizer) == tokenizer_sha)


def validar_base(pasta, variante: str | None = None) -> bool:
    spec = especificacao(variante)
    if not pasta or spec is None:
        return False
    pasta = Path(pasta).expanduser().resolve()
    pesos, tokenizer = pasta / "pesos.pt", pasta / "tokenizer.json"
    if not pesos.is_file() or not tokenizer.is_file():
        return False
    ps, ts = pesos.stat(), tokenizer.stat()
    return _validar(str(pasta), ps.st_mtime_ns, ps.st_size,
                    ts.st_mtime_ns, ts.st_size,
                    spec["pesos_sha256"], spec["tokenizer_sha256"])


def candidatos(variante: str | None = None):
    variante = variante or variante_solicitada()
    explicito = os.environ.get("CRIVO_TRANSFORMER_17M_DIR", "").strip()
    if explicito:
        yield Path(explicito)
    # A variante experimental nunca e descoberta automaticamente. Para testa-la
    # e preciso fornecer CRIVO_TRANSFORMER_17M_DIR e os dois opt-ins.
    if variante == VARIANTE_COMPOSICIONAL:
        return
    yield RAIZ / "artefatos" / "transformer_leitor_17m" / "base"
    yield RAIZ / "artefatos" / "transformer-leitor" / "base"
    yield Path("/content/drive/MyDrive/CRIVO/transformer-leitor/base")
    yield Path.home() / "CRIVO" / "transformer-leitor" / "base"


def localizar():
    """Retorna somente uma base de hash exato autorizada pelos opt-ins."""
    variante = variante_solicitada()
    if especificacao(variante) is None:
        return None
    for pasta in candidatos(variante):
        try:
            if validar_base(pasta, variante):
                return str(Path(pasta).expanduser().resolve())
        except OSError:
            continue
    return None


def status():
    variante = variante_solicitada()
    spec_sem_trava = BASES.get(variante)
    spec = especificacao(variante)
    pasta = localizar() if spec is not None else None
    info = spec_sem_trava or BASES["leitor"]
    return {
        "preferido": info["nome"],
        "variante": variante,
        "parametros": 17428224,
        "passo": info["passo"],
        "experimental": bool(info["experimental"]),
        "promovido": bool(info["promovido"]),
        "opt_in_experimental_necessario": bool(info["experimental"]),
        "opt_in_experimental_ativo": bool(spec is not None) if info["experimental"] else None,
        "disponivel": bool(pasta),
        "pasta": pasta,
        "pesos_sha256": info["pesos_sha256"] if pasta else None,
        "tokenizer_sha256": info["tokenizer_sha256"] if pasta else None,
        "external_ai": False,
    }
