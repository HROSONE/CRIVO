"""Confirmar semântica do interpretador próprio em runtimes JS/TS isolados."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from interpretacao_estados import executar,javascript
from scripts.treinar_efeitos import PROGRAMAS
from verificacao_codigo import verificar

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tsc',required=True);p.add_argument('--saida',required=True)
    a=p.parse_args();rs=[]
    for nome,corpo,entradas in PROGRAMAS:
        casos=[dict(entrada=[x],saida=executar(corpo,x)['resultado']) for x in entradas]
        for lang in ('javascript','typescript'):
            r=verificar(javascript(corpo,lang=='typescript'),lang,casos,tsc=a.tsc)
            rs.append(dict(id=nome,linguagem=lang,verificacao=r))
    out=Path(a.saida);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(referencias=True,resultados=rs),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(referencias=len(rs),casos_total=sum(x['verificacao']['casos_total'] for x in rs),casos_corretos=sum(x['verificacao']['casos_corretos'] for x in rs))))
    if not all(r['verificacao']['funcional'] for r in rs):raise SystemExit('Semântica divergiu do runtime ou isolamento indisponível')
