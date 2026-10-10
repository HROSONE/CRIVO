"""Juiz congelado antes de avaliar o candidato: continuidade, não cópia."""
import argparse,hashlib,json,sys,unicodedata
from pathlib import Path
H=Path(__file__).resolve().parent
def n(s):return ''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if not unicodedata.combining(c))
def pontuar(d):
 assert hashlib.sha256((H/'sondas.json').read_bytes()).hexdigest()==(H/'SHA256').read_text().split()[0]
 esperado=json.loads((H/'sondas.json').read_text())['sessoes'];assert [s['id'] for s in d['sessoes']]==[s['id'] for s in esperado];rows=[];refs=dom=contrad=0
 for e,s in zip(esperado,d['sessoes']):
  assert [r['usuario'] for r in s['resultados']]==e['turnos'];problemas=[];corpos=[]
  if s['id'].startswith('causal_'):
   for i,r in enumerate(s['resultados']):
    a=r['resposta'];g=a.get('dialogue_generation',{});t=a['response'];rota=(a.get('natural_routing') or {})
    if e['personagem'] not in t or e['lugar'] not in t:problemas.append([i,'referente ausente']);refs+=1
    if i<7 and not g.get('usada'):problemas.append([i,'história não entregue'])
    if i in e['continuacoes']:
     if not g.get('continuidade_causal') or g.get('classe_escrita')!=e['classe']:problemas.append([i,'estado não usado'])
     evento=e['evento'].split('. Continue')[0].strip('.! ')
     if evento in t:problemas.append([i,'declaração recopiada'])
     if not all(v in t for v in g.get('argumentos',{}).values()):problemas.append([i,'argumento alterado']);refs+=1
     if not g.get('guarda',{}).get('aceita'):problemas.append([i,'guarda recusou'])
     corpo=t.split('. ',1)[-1];corpos.append(corpo)
     if e['classe']=='recuperacao' and any(x in n(corpo) for x in ('objeto perdido','busca continuou','procurou')):problemas.append([i,'recuperação revertida']);contrad+=1
     if e['classe']=='perda' and any(x in n(corpo) for x in ('objeto recuperado','problema ficou resolvido')):problemas.append([i,'perda resolvida sem declaração']);contrad+=1
    if any(x in n(t) for x in ('repteis','anfibio','mancha de roupa','receita de')):problemas.append([i,'domínio trocado']);dom+=1
   if len(set(corpos))!=4:problemas.append([-1,'continuação repetida'])
  else:
   for i in ((0,2) if s['id']=='esclarecimento' else (3,)):
    a=s['resultados'][i]['resposta'];t=n(a['response']);rota=(a.get('natural_routing') or {})
    if rota.get('peca')!='esclarecimento' or rota.get('ato')!='continuidade_incerta' or '?' not in t:problemas.append([i,'não esclareceu contexto incerto'])
    if a.get('dialogue_generation',{}).get('usada'):problemas.append([i,'gerou sem contexto atual'])
   i=1 if s['id']=='esclarecimento' else 2;f=s['resultados'][i]['resposta']
   if f.get('id')!='conhecimento:mundo_potencial_eletrico' or f.get('mechanism')!='composicao_factual':problemas.append([i,'rota factual perdida'])
  rows.append(dict(id=s['id'],passou=not problemas,problemas=problemas,corpos_distintos=len(set(corpos))))
 return dict(sessoes=12,turnos=88,conversas_mantem_fio=sum(r['passou'] for r in rows[:10]),esclarecimentos=sum(r['passou'] for r in rows[10:]),referentes_ausentes=refs,trocas_dominio=dom,contradicoes_estado=contrad,resultados=rows,limite='Sondas autorais inéditas, classes conhecidas, revisão pelo agente e critério lexical limitado; não humanos, avaliação cega ou generalização de assunto.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--arquivo',required=True);p.add_argument('--saida',required=True);p.add_argument('--exigir-meta',action='store_true');a=p.parse_args();r=pontuar(json.loads(Path(a.arquivo).read_text()));Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items() if k!='resultados'})
 if a.exigir_meta:assert r['conversas_mantem_fio']>=6 and r['esclarecimentos']==2 and r['referentes_ausentes']==r['trocas_dominio']==r['contradicoes_estado']==0,r
