"""Converte artefatos/linguagem_profunda/pesos.pt (PyTorch) em
pesos_numpy.npz (float16) para o pontuador de frases rodar sem PyTorch.

Uso: python scripts/exportar_pontuador.py
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

PASTA = Path(__file__).resolve().parent.parent / "artefatos" / "linguagem_profunda"


def main():
    estado = torch.load(PASTA / "pesos.pt", map_location="cpu", weights_only=True)
    pesos = {k: v.numpy().astype(np.float16) for k, v in estado["modelo"].items()}
    meta = dict(estado["config"])
    meta.update(passo=estado["passo"],
                origem_sha256=hashlib.sha256((PASTA / "pesos.pt").read_bytes()).hexdigest(),
                tokenizer_sha256=estado["execucao"]["tokenizer_sha256"])
    np.savez_compressed(PASTA / "pesos_numpy.npz", meta=np.array(json.dumps(meta)), **pesos)
    print("ok", PASTA / "pesos_numpy.npz", sum(v.size for v in pesos.values()), "parâmetros")


if __name__ == "__main__":
    sys.exit(main())
