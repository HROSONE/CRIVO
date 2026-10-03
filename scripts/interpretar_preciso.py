"""Usar a rede própria com igualdade e índices aprimorados."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from interpretacao_estruturas import executar
from rede_precisa import RedePrecisa
from busca_estados import buscar_com_reparo

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--codigo');g.add_argument('--contrato',help='JSON com tipo, desenvolvimento, contraexemplos_desenvolvimento e campos opcionais')
    p.add_argument('--entrada-json',default='0');p.add_argument('--rede');p.add_argument('--reparos',type=int,default=2,choices=(0,1,2))
    a=p.parse_args();rede=RedePrecisa.carregar(a.rede) if a.rede else None
    if a.codigo:
        if len(a.entrada_json)>8192:raise ValueError('Entrada grande demais')
        r=executar(a.codigo,json.loads(a.entrada_json),rede.prever if rede else None)
    else:
        f=Path(a.contrato)
        if f.stat().st_size>32768:raise ValueError('Contrato grande demais')
        t=json.loads(f.read_text())
        if not isinstance(t,dict) or set(t)-{'tipo','desenvolvimento','contraexemplos_desenvolvimento','campos'}:raise ValueError('Forneça somente contrato e casos de desenvolvimento, sem reservados')
        r=buscar_com_reparo(t['desenvolvimento'],t['tipo'],t.get('contraexemplos_desenvolvimento',[]),rede.prever if rede else None,
                           campos=t.get('campos',[]),max_reparos=a.reparos)
    print(json.dumps(r,ensure_ascii=True,indent=2))
