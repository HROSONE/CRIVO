"""Avaliação independente NumPy, sem selecionar ou ajustar pesos."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
PASTA=Path(__file__).resolve().parent
sys.path[:0]=[str(PASTA),str(PASTA.parents[1])]
from modular import ModeloNumpyModular,avaliar_modular,exemplos_modulares
from treinar_modular import avaliar_etapas


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pesos',type=Path,required=True)
    ap.add_argument('--casos',type=Path,required=True)
    ap.add_argument('--saida',type=Path,required=True)
    args=ap.parse_args()
    casos=json.loads(args.casos.read_text(encoding='utf-8'))
    m=ModeloNumpyModular(args.pesos)
    out=dict(teste_numpy=avaliar_modular(m,casos),
             etapas_teste=avaliar_etapas(m,exemplos_modulares(casos)),
             pesos_sha256=hashlib.sha256((args.pesos/'pesos_numpy.npz').read_bytes()).hexdigest(),
             casos_sha256_canonico=hashlib.sha256(json.dumps(casos,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
             decodificacao='greedy, 40 tokens, exige fim; sem máscaras lexicais ou penalidades de repetição')
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    args.saida.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print({k:v['total'] for k,v in out['teste_numpy'].items()},flush=True)


if __name__=='__main__':main()
