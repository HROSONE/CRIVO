"""Preflight funcional antes de gastar GPU; candidatos nunca rodam sem runtime restrito."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from verificacao_codigo import verificar


def verificar_ambiente(tsc=None):
    resultados={}
    for linguagem, codigo in (
        ('javascript','function resolver(n) { return n * 2; }'),
        ('typescript','function resolver(n: number): number { return n * 2; }')):
        resultados[linguagem]=verificar(codigo,linguagem,[dict(entrada=[2],saida=4),dict(entrada=[-3],saida=-6)],tsc)
    return resultados


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tsc');a=p.parse_args()
    resultados=verificar_ambiente(a.tsc)
    print(json.dumps(resultados,ensure_ascii=False,indent=2))
    if not all(r['funcional'] for r in resultados.values()):
        sys.exit('Ambiente não passou no preflight JS/TS; corrija as dependências antes de treinar.')
