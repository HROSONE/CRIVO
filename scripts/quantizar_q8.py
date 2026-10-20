"""int8 por linha para os pesos NumPy do CRIVO (como a v3 D e a v4 F no site).

Cada matriz 2D vira `nome.q8` (int8) e `nome.escala` (float16, uma escala por linha, máximo
absoluto / 127). Vetores (normas e vieses) ficam em float16. O carregador (conversa_v3d) multiplica
de volta para float32. Para a v4 F: 774/800 respostas idênticas ao float16 e o mesmo sentido.

Uso: python scripts/quantizar_q8.py origem_float16.npz destino_int8.npz
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


def quantizar(origem, destino):
    origem, destino = Path(origem), Path(destino)
    p = np.load(origem)
    meta = json.loads(str(p["meta"]))
    sha_origem = hashlib.sha256(origem.read_bytes()).hexdigest()
    meta["quantizacao"] = "int8 por linha (escala float16), a partir de npz %s" % sha_origem
    saida = {"meta": np.array(json.dumps(meta))}
    for k in p.files:
        if k == "meta":
            continue
        w = p[k].astype(np.float32)
        if w.ndim == 2:
            e32 = np.abs(w).max(axis=1, keepdims=True) / 127.0   # arredonda pela escala exata; guarda em float16
            saida[k + ".q8"] = np.clip(np.rint(w / np.where(e32 == 0, 1.0, e32)), -127, 127).astype(np.int8)
            saida[k + ".escala"] = e32.astype(np.float16)
        else:
            saida[k] = w.astype(np.float16)
    np.savez_compressed(destino, **saida)
    return meta


def carregar(npz):
    """{nome: float32} de um npz int8 (ou float16)."""
    p = np.load(npz)
    out = {}
    for k in p.files:
        if k == "meta" or k.endswith(".escala"):
            continue
        if k.endswith(".q8"):
            base = k[:-3]
            out[base] = p[k].astype(np.float32) * p[base + ".escala"].astype(np.float32)
        else:
            out[k] = p[k].astype(np.float32)
    return out, json.loads(str(p["meta"]))


if __name__ == "__main__":
    m = quantizar(sys.argv[1], sys.argv[2])
    print("ok", sys.argv[2], m["quantizacao"])
