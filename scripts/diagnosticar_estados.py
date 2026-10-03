"""Diagnosticar uma função limitada usando somente exemplos de desenvolvimento."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from diagnostico_estados import diagnosticar, comparar_efeitos


def carregar_contrato(path):
    p = Path(path)
    if p.stat().st_size > 131072:
        raise ValueError('Contrato grande demais')
    c = json.loads(p.read_text())
    if not isinstance(c, dict) or set(c) != {'codigo', 'desenvolvimento'}:
        raise ValueError('Contrato aceita somente codigo e desenvolvimento; não envie referências ou reservados')
    return c


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contrato', required=True)
    p.add_argument('--rede-ranking')
    p.add_argument('--rede-efeitos')
    p.add_argument('--limite', type=int, default=512)
    p.add_argument('--verificacoes', type=int, default=128)
    a = p.parse_args()
    c = carregar_contrato(a.contrato)
    ranking = None
    if a.rede_ranking:
        from rede_reparos import RedeReparos
        ranking = RedeReparos.carregar(a.rede_ranking)
    r = diagnosticar(c['codigo'], c['desenvolvimento'], ranking, a.limite, a.verificacoes)
    if a.rede_efeitos:
        from rede_precisa import RedePrecisa
        rede = RedePrecisa.carregar(a.rede_efeitos)
        r['auditoria_efeitos'] = [comparar_efeitos(c['codigo'], ex['entrada'], rede.prever)
                                  for ex in c['desenvolvimento']]
    print(json.dumps(r, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
