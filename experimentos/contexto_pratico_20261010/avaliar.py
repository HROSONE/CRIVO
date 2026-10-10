"""40 turnos realmente observados; regras mínimas congeladas + trace completo."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent.parent))
from composicao_textual import normalizar

def pontuar(d):
    for arquivo,sha in [('sondas.json','SHA256'),('criterios.json','SHA256-criterios')]:
        assert hashlib.sha256((H/arquivo).read_bytes()).hexdigest()==(H/sha).read_text().split()[0]
    regras=json.loads((H/'criterios.json').read_text());rows=[]
    for s in d['sessoes']:
        assert len(s['resultados'])==len(regras['sessoes'][s['id']])
        for i,(row,grupos) in enumerate(zip(s['resultados'],regras['sessoes'][s['id']])):
            r=row['resposta'];texto=normalizar(r['response']);rota=r.get('natural_routing') or {}
            faltam=[g for g in grupos if not any(normalizar(t) in texto for t in g)]
            desvios=[t for t in regras['proibidos'] if normalizar(t) in texto]
            peca=rota.get('peca') or r['id']
            correto=peca in regras['pecas']
            guarda=not rota or rota.get('guarda',{}).get('aceita',False)
            rows.append({'id':s['id']+'-'+str(i+1),'passou':correto and guarda and not faltam and not desvios,
                         'peca':peca,'faltam':faltam,'desvios':desvios,'guarda_aceita':guarda})
    assert len(rows)==40
    return {'turnos':40,'corretos':sum(r['passou'] for r in rows),'desvios':sum(bool(r['desvios']) for r in rows),
            'sessoes_minimas':sum(all(r['passou'] for r in rows if r['id'].startswith(s+'-')) for s in regras['sessoes']),
            'resultados':rows,'limite':regras['limite']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--arquivo',required=True);p.add_argument('--saida',required=True);p.add_argument('--exigir-meta',action='store_true');a=p.parse_args()
    r=pontuar(json.loads(Path(a.arquivo).read_text()));Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='resultados'},ensure_ascii=False))
    if a.exigir_meta:assert r['corretos']==40 and r['desvios']==0 and r['sessoes_minimas']==4
