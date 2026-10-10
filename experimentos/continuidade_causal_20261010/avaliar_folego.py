"""Dois encadeamentos prospectivos de dezoito turnos; janela HTTP real."""
import argparse,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def pontuar(d):
 p=H/'conversas_novas.json';assert hashlib.sha256(p.read_bytes()).hexdigest()==(H/'SHA256-novas').read_text().split()[0]
 ss=json.loads(p.read_text())['sessoes'];assert [s['id'] for s in d['sessoes']]==[s['id'] for s in ss];rows=[]
 for e,s in zip(ss,d['sessoes']):
  assert [r['usuario'] for r in s['resultados']]==e['turnos'];erros=[]
  primeiro=s['resultados'][0]['resposta'].get('dialogue_generation',{}).get('argumentos',{})
  for i,r in enumerate(s['resultados']):
   a=r['resposta'];g=a.get('dialogue_generation',{});t=a['response']
   if any(v not in t for v in primeiro.values()):erros.append([i,'abertura perdida'])
   if i<17 and (not g.get('usada') or not g.get('guarda',{}).get('aceita')):erros.append([i,'história recusada'])
   if i in (2,3,4,5,7,8,9,10,12,13,14,15):
    if not g.get('continuidade_causal'):erros.append([i,'estado não usado'])
    if any(v not in t for v in g.get('argumentos',{}).values()):erros.append([i,'referente ausente'])
   if i==17 and (a.get('natural_routing') or {}).get('ato')!='participantes_historia':erros.append([i,'participantes perdidos'])
  # Três acontecimentos distintos, sem reiniciar antes de quatro passos.
  for inicio in (2,7,12):
   bloco=s['resultados'][inicio:inicio+4]
   if [r['resposta'].get('dialogue_generation',{}).get('passo_causal') for r in bloco]!=list(range(4)):erros.append([inicio,'progressão incorreta'])
   if len({r['resposta']['response'].split('. ',1)[-1] for r in bloco})!=4:erros.append([inicio,'cena repetida'])
  rows.append(dict(id=s['id'],passou=not erros,problemas=erros))
 return dict(sessoes=2,turnos=36,aprovadas=sum(r['passou'] for r in rows),resultados=rows,limite='Três estados conhecidos encadeados, 18 mensagens. Sondas autorais pelo agente; não enredo livre longo, humanos ou memória ilimitada.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--arquivo',required=True);p.add_argument('--saida',required=True);p.add_argument('--exigir-meta',action='store_true');a=p.parse_args();r=pontuar(json.loads(Path(a.arquivo).read_text()));Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
 if a.exigir_meta:assert r['aprovadas']==2
