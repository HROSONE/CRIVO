"""Sanidade das respostas de referência; indisponibilidade de isolamento é explícita."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verificacao_codigo import verificar,sandbox_disponivel

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tsc');p.add_argument('--saida',required=True);p.add_argument('--exigir-isolamento',action='store_true')
    a=p.parse_args();disponivel=sandbox_disponivel()
    tarefas=json.loads((ROOT/'dados/programacao/tarefas.json').read_text())['tarefas']
    resultados=[dict(id=t['id'],**verificar(t['resposta'],t['linguagem'],t['casos'],a.tsc)) for t in tarefas]
    Path(a.saida).write_text(json.dumps(dict(isolamento=disponivel,resultados=resultados),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(isolamento=disponivel,total=len(resultados),compilam=sum(r['compila'] for r in resultados),funcionais=sum(r['funcional'] for r in resultados))))
    if any(not r['compila'] or (disponivel and not r['funcional']) for r in resultados) or (a.exigir_isolamento and not disponivel):
        sys.exit(1)
