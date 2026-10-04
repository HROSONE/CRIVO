"""Laboratório optativo: observações estruturadas de heap Node, sem medições automáticas."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from investigacao_memoria import criar_investigacao, explicar, FONTES


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime',choices=('node','outro'))
    p.add_argument('--metrica',choices=('heap','rss'))
    p.add_argument('--pos-gc',choices=('cresce','estavel'))
    p.add_argument('--cache',choices=('cresce','estavel'))
    p.add_argument('--fila',choices=('cresce','estavel'))
    a=p.parse_args();dados={k:v for k,v in vars(a).items() if v is not None}
    i=criar_investigacao();i.observar(dados,'observacoes_informadas_na_cli')
    r=i.investigar();r.update(resposta=explicar(r),fontes=list(FONTES))
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
