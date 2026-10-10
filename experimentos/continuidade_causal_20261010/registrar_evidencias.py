"""Preserva todos os checkpoints anteriores e dados históricos imutáveis."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=json.loads((H/'aprovacao.json').read_text());assert sha(ROOT/'rede_dialogo_conversa.json.gz')==a['checkpoint_producao_sha256']
 antigo=json.loads((H.parent/'diversidade_dialogo_20261010/manifesto.json').read_text());pres=dict(antigo['pesos_preservados_sha256']);pres['experimentos/continuidade_causal_20261010/checkpoint_base_134.json.gz']=antigo['checkpoint_producao_sha256']
 for f,h in pres.items():assert sha(ROOT/f)==h,f
 evidencias=dict(antigo['experimentos_preservados_sha256'])
 for p in sorted((H.parent/'diversidade_dialogo_20261010').rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:evidencias[str(p.relative_to(ROOT))]=sha(p)
 for f,h in evidencias.items():assert sha(ROOT/f)==h,f
 m=dict(base_commit='04f2be154850202c2831e426b23db0741d4dc74f',checkpoint_original_isolado_sha256=sha(H/'checkpoint_gru_dialogo.json.gz'),checkpoint_producao_sha256=sha(ROOT/'rede_dialogo_conversa.json.gz'),checkpoint_anterior_arquivado_sha256=sha(H/'checkpoint_base_134.json.gz'),parametros=85130,vocabulario=321,pesos_preservados_sha256=pres,experimentos_preservados_sha256=evidencias,arquivos_sha256={p.name:sha(p) for p in sorted(H.iterdir()) if p.is_file() and p.name!='manifesto.json'},runtime_sha256={f:sha(ROOT/f) for f in ('conversa_dialogo.py','compreensao_intencao.py','testes_continuidade_causal.py','testes_diversidade_dialogo.py','.github/workflows/escrita-acontecimentos.yml')},limite='Quatro passos e dez estados autorais; seleção estrutural, não planejamento livre nem avaliação humana/cega.')
 (H/'manifesto.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print('Pesos preservados',len(pres),'arquivos históricos',len(evidencias))
if __name__=='__main__':main()
