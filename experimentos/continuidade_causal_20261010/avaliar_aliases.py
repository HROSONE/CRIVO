"""Operadores comuns também devem preservar acontecimento, não copiar relato."""
import argparse,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def pontuar(d):
 p=H/'sondas_aliases.json';assert hashlib.sha256(p.read_bytes()).hexdigest()==(H/'SHA256-aliases').read_text().split()[0];ss=json.loads(p.read_text())['sessoes'];assert [s['id'] for s in d['sessoes']]==[s['id'] for s in ss];rows=[]
 for e,s in zip(ss,d['sessoes']):
  assert [r['usuario'] for r in s['resultados']]==e['turnos'];erros=[];bloco=s['resultados'][2:6]
  for i,r in enumerate(s['resultados']):
   a=r['resposta'];g=a.get('dialogue_generation',{});t=a['response']
   if 'uma marta desenhista' not in t or 'uma oficina oliva' not in t:erros.append([i,'referente perdido'])
   if i<7 and not g.get('usada'):erros.append([i,'história ausente'])
   if i in (2,3,4,5):
    if not g.get('continuidade_causal') or g.get('classe_escrita')!=e['classe']:erros.append([i,'estado não usado'])
    if e['turnos'][1].split('. Continue')[0].strip('.! ') in t:erros.append([i,'relato recopiado'])
    if not all(v in t for v in g.get('argumentos',{}).values()):erros.append([i,'argumento alterado'])
    if e['classe']=='recuperacao' and 'objeto perdido' in t:erros.append([i,'recuperação revertida'])
  if [r['resposta'].get('dialogue_generation',{}).get('passo_causal') for r in bloco]!=list(range(4)):erros.append([-1,'progressão incorreta'])
  if len({r['resposta']['response'].split('. ',1)[-1] for r in bloco})!=4:erros.append([-1,'cena repetida'])
  rows.append(dict(id=s['id'],passou=not erros,problemas=erros))
 return dict(sessoes=3,turnos=24,aprovadas=sum(r['passou'] for r in rows),resultados=rows,limite='Aliases comuns em três classes conhecidas; exemplos autorais do agente, não avaliação humana ou generalização irrestrita.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--arquivo',required=True);p.add_argument('--saida',required=True);p.add_argument('--exigir-meta',action='store_true');a=p.parse_args();r=pontuar(json.loads(Path(a.arquivo).read_text()));Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
 if a.exigir_meta:assert r['aprovadas']==3
