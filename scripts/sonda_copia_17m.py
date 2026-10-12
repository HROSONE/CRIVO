"""Sonda de cópia em contexto para qualquer Transformer 17M do CRIVO.

Mede o que o pré-treino continuado quer melhorar: repetição de 50 tokens
aleatórios (acerto top-1 na 2ª vez) e perda do nome inventado na 2ª menção.
Uso:
  python scripts/sonda_copia_17m.py --base PASTA        # pasta com pesos.pt + tokenizer.json
  python scripts/sonda_copia_17m.py --npz ARQUIVO.npz --tokenizer tokenizer.json
"""
import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))


def main():
    import numpy as np
    import torch
    import torch.nn.functional as F
    from tokenizers import Tokenizer
    import linguagem_profunda as lp
    from continuar_pretreino_17m import sonda_copia
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base")
    ap.add_argument("--npz")
    ap.add_argument("--tokenizer")
    ap.add_argument("--dispositivo", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    if args.base:
        modelo, tok, _ = lp.carregar(args.base, dispositivo=args.dispositivo)
    elif args.npz and args.tokenizer:
        z = np.load(args.npz, allow_pickle=True)
        modelo = lp.LinguagemProfunda(lp.Configuracao(vocabulario=8192, dimensao=384, camadas=8, cabecas=8,
                                                      contexto=256, dropout=0.1))
        modelo.load_state_dict({k: torch.tensor(z[k].astype(np.float32)) for k in modelo.state_dict()})
        modelo = modelo.to(args.dispositivo)
        tok = Tokenizer.from_file(args.tokenizer)
    else:
        raise SystemExit("use --base ou --npz com --tokenizer")
    print(json.dumps(sonda_copia(modelo.eval(), tok, args.dispositivo, np, torch, F), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
