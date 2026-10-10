"""Juiz congelado antes da implementação; preservação de objeto e estado."""
import argparse,hashlib,json,unicodedata
from pathlib import Path
H=Path(__file__).resolve().parent
CHECKPOINT='28d05179e4dda05473a5bdb0a3963d8e032b3d3e9c5d6d60a77404310545d4e8'
def n(t):return ''.join(c for c in unicodedata.normalize('NFD',t.casefold()) if not unicodedata.combining(c))
def pontuar(d):
 assert hashlib.sha256((H/'casos.json').read_bytes()).hexdigest()==(H/'SHA256').read_text().split()[0]
 cases=json.loads((H/'casos.json').read_text())['sessoes'];assert [s['id'] for s in d['sessoes']]==[s['id'] for s in cases]
 res=[];refs=dom=estado=0
 for e,s in zip(cases,d['sessoes']):
  assert [r['usuario'] for r in s['resultados']]==e['turnos'];erros=[]
  for i in e.get('verificar',[e.get('esclarecer')]):
   r=s['resultados'][i]['resposta'];t=n(r['response']);g=r.get('dialogue_generation',{});rota=r.get('natural_routing') or {}
   if e['id']=='negacao':
    esclarece=rota.get('peca')=='esclarecimento' and '?' in t and not g.get('usada')
    continua=g.get('usada') and g.get('classe_escrita')=='perda' and 'carteira jade' in t and 'objeto recuperado' not in t
    if not (esclarece or continua):erros.append([i,'negação virou recuperação']);estado+=1
    continue
   if 'verificar' not in e:
    if rota.get('peca')!='esclarecimento' or g.get('usada') or '?' not in t:erros.append([i,'gerou referência sem resolver ambiguidade']);estado+=1
    continue
   if not g.get('usada') or g.get('checkpoint_sha256')!=CHECKPOINT or g.get('experimental') or not g.get('guarda',{}).get('aceita'):erros.append([i,'história própria aprovada não entregue'])
   if g.get('classe_escrita')!=e['classe']:erros.append([i,'estado incorreto']);estado+=1
   for v in (e['personagem'],e['lugar'],e['objeto_novo']):
    if n(v) not in t:erros.append([i,'referente ausente: '+v]);refs+=1
   if e['objeto_anterior']!=e['objeto_novo'] and n(e['objeto_anterior']) in t:erros.append([i,'correção não aplicada']);refs+=1
   if i in (3,4) and not g.get('continuidade_causal'):erros.append([i,'continuação não usou o acontecimento'])
   if e['classe']=='recuperacao' and 'objeto perdido' in t:erros.append([i,'recuperação revertida']);estado+=1
   if any(v in t for v in ('receita de','repteis','mancha de roupa')):erros.append([i,'domínio trocado']);dom+=1
  res.append(dict(id=e['id'],passou=not erros,problemas=erros))
 return dict(sessoes=len(cases),turnos=sum(len(s['resultados']) for s in d['sessoes']),referencias_corretas=sum(r['passou'] for r in res[:6]),fronteiras_corretas=sum(r['passou'] for r in res[6:]),referentes_ausentes_ou_antigos=refs,trocas_dominio=dom,estados_incorretos=estado,resultados=res,limite='Onze sondas autorais, classes conhecidas e critérios lexicais explícitos. Não avaliação humana, entendimento geral de pronomes ou correção livre.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--arquivo',required=True);p.add_argument('--saida',required=True);p.add_argument('--exigir-meta',action='store_true');a=p.parse_args();r=pontuar(json.loads(Path(a.arquivo).read_text()));Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items() if k!='resultados'})
 if a.exigir_meta:assert r['referencias_corretas']==6 and r['fronteiras_corretas']==5 and not r['referentes_ausentes_ou_antigos'] and not r['trocas_dominio'] and not r['estados_incorretos'],r
