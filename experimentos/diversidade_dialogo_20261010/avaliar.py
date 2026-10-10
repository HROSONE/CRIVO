"""Distingue variação gerada de nomes/declarações apenas copiados dos slots."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent.parent;sys.path.insert(0,str(ROOT))
from conversa_dialogo import reacao_adequada
from linguagem_gerativa import tokenizar

def pontuar(d):
    assert hashlib.sha256((H/'sondas.json').read_bytes()).hexdigest()==(H/'SHA256').read_text().split()[0]
    sessoes=json.loads((H/'sondas.json').read_text())['sessoes'];rows=[]
    assert [s['id'] for s in d['sessoes']]==[s['id'] for s in sessoes]
    for esperado,s in zip(sessoes,d['sessoes']):
        assert [r['usuario'] for r in s['resultados']]==esperado['turnos']
        corpos=[];problemas=[]
        for i,r in enumerate(s['resultados']):
            resp=r['resposta'];g=resp['dialogue_generation'];corpo=resp['response'].split('. ',1)[-1]
            relato=g.get('argumentos',{}).get('relato')
            if relato:corpo=corpo.replace(relato+'. ', '',1)
            tokens=tokenizar(corpo)
            if not g.get('usada') or not g.get('guarda',{}).get('aceita'):problemas.append([i+1,'geração não entregue/guarda recusou'])
            if not all(v in resp['response'] for v in g.get('argumentos',{}).values()):problemas.append([i+1,'referente ausente'])
            if i in esperado['eventos']:
                if g.get('classe_escrita')!=esperado['classe'] or not reacao_adequada(tokens,esperado['classe']):problemas.append([i+1,'reação/classe incompatível'])
                if not tokens:problemas.append([i+1,'sem corpo']);continue
                corpos.append(' '.join(tokens))
        distintos=len(set(corpos));rows.append({'id':s['id'],'classe':esperado['classe'],'corpos_distintos':distintos,'acontecimentos':4,'corpos':corpos,'problemas':problemas,'passou':distintos>=3 and len(corpos)==4 and not problemas})
    return {'sessoes':len(rows),'sessoes_aprovadas':sum(r['passou'] for r in rows),'corpos_distintos_total':sum(r['corpos_distintos'] for r in rows),'turnos':48,'problemas_fidelidade':sum(len(r['problemas']) for r in rows),'resultados':rows,'limite':'Variantes nas classes conhecidas, cenas e alvos autorais compartilhados no treino. Métrica de forma + guardas/reação lexical e revisão do agente; não raciocínio ou generalização de assunto.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--arquivo',required=True);p.add_argument('--saida',required=True);p.add_argument('--exigir-meta',action='store_true');a=p.parse_args()
    r=pontuar(json.loads(Path(a.arquivo).read_text()));Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items() if k!='resultados'})
    if a.exigir_meta:assert r['sessoes_aprovadas']==8 and r['problemas_fidelidade']==0
