"""Executar corpo JS restrito ou sintetizar função a partir de exemplos JSON."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from interpretacao_estados import executar,sintetizar
from rede_efeitos import RedeEfeitos

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--codigo');g.add_argument('--contrato',help='Arquivo JSON com lista de {entrada: inteiro, saida: inteiro ou booleano}')
    p.add_argument('--entrada',type=int,default=0);p.add_argument('--rede',help='Diretório com rede.npz e config.json; sem este argumento usa executor/busca exatos')
    a=p.parse_args();rede=RedeEfeitos.carregar(a.rede) if a.rede else None
    if a.codigo:r=executar(a.codigo,a.entrada,rede.prever if rede else None)
    else:
        arquivo=Path(a.contrato)
        if arquivo.stat().st_size>8192:raise ValueError('Contrato excede limite')
        r=sintetizar(json.loads(arquivo.read_text()),rede.prever if rede else None)
    print(json.dumps(r,ensure_ascii=False,indent=2))
