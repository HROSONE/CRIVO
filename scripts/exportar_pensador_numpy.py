"""Exporta o pensador v2 (pensador.pt do treino) para NumPy float32, para o chat rodar sem PyTorch.

Uso: python scripts/exportar_pensador_numpy.py pensador.pt artefatos/pensador_v2_pt/pensador_numpy.npz
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch


def exportar(origem, destino):
    ck = torch.load(origem, map_location="cpu")
    meta = {"origem_sha256": hashlib.sha256(Path(origem).read_bytes()).hexdigest(), "passo": ck["passo"],
            "config": {k: ck["config"][k] for k in ("d", "camadas", "voltas")}, "cabecas": 4,
            "protocolo": "pensador_v2_20261014", "pesos_externos": False}
    arrays = {k: v.detach().float().numpy() for k, v in ck["estado"].items()}
    np.savez_compressed(destino, meta=np.array(json.dumps(meta)), **arrays)
    return meta


if __name__ == "__main__":
    print(exportar(sys.argv[1], sys.argv[2]))
