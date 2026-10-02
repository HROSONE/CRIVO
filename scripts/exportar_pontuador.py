"""Converte os pesos de um transformer do projeto (pesos.pt, PyTorch) em
pesos_numpy.npz (float16) para o pontuador de frases rodar sem PyTorch, e
confere a paridade NumPy × PyTorch numa frase de exemplo.

Uso:
  python scripts/exportar_pontuador.py                       # modelo atual
  python scripts/exportar_pontuador.py --origem trabalho/dialogo --destino artefatos/pontuador_pt
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import torch

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
PADRAO = RAIZ / "artefatos" / "linguagem_profunda"


def exportar(origem, destino):
    origem, destino = Path(origem), Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    if origem.resolve() != destino.resolve():
        for nome in ("tokenizer.json", "relatorio.json"):
            if (origem / nome).exists():
                shutil.copyfile(origem / nome, destino / nome)
    estado = torch.load(origem / "pesos.pt", map_location="cpu", weights_only=True)
    pesos = {k: v.float().numpy().astype(np.float16) for k, v in estado["modelo"].items()}
    meta = dict(estado["config"])
    meta.update(passo=estado["passo"],
                origem_sha256=hashlib.sha256((origem / "pesos.pt").read_bytes()).hexdigest(),
                tokenizer_sha256=estado["execucao"]["tokenizer_sha256"])
    np.savez_compressed(destino / "pesos_numpy.npz", meta=np.array(json.dumps(meta)), **pesos)
    return estado, sum(v.size for v in pesos.values())


def paridade(origem, destino):
    """Maior diferença de logit entre PyTorch e NumPy numa resposta de exemplo."""
    from linguagem_profunda import carregar
    from pontuador_frases import Pontuador
    modelo, _, _ = carregar(origem)
    p = Pontuador(destino)
    ids = p.prefixo("hoje perdi o ônibus") + p.bpe.codificar("Poxa, que chato. Você chegou atrasado?")
    with torch.no_grad():
        ref = modelo(torch.tensor([ids]))[0][0].numpy()
    return float(abs(ref - p.logits(ids)).max())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--origem", default=str(PADRAO))
    ap.add_argument("--destino", default=None)
    args = ap.parse_args()
    destino = args.destino or args.origem
    _, n = exportar(args.origem, destino)
    dif = paridade(args.origem, destino)
    print("ok", Path(destino) / "pesos_numpy.npz", n, "parâmetros; diferença máxima de logit", round(dif, 4))
    if dif > 0.1:
        sys.exit("paridade NumPy × PyTorch acima do tolerado")


if __name__ == "__main__":
    main()
