"""Reproduz a bateria v2, sem ensinar estados ao motor ou alterar os 25 originais."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('avaliacao_original', H.parent / 'roteamento_natural_20261009' / 'avaliar.py')
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)


def main():
 p=argparse.ArgumentParser()
 p.add_argument('--saida',required=True)
 p.add_argument('--exigir-meta',action='store_true')
 a=p.parse_args()
 f=H/'casos_congelados.json';sha=hashlib.sha256(f.read_bytes()).hexdigest()
 assert sha == (H/'SHA256').read_text().split()[0]
 dataset=json.loads(f.read_text())
 original=H.parent/'roteamento_natural_20261009'/'casos_congelados.json'
 assert hashlib.sha256(original.read_bytes()).hexdigest() == dataset['originais_sha256']
 assert dataset['casos'][:25] == json.loads(original.read_text())['casos']
 rows=[]
 out={'codigo':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'casos_sha256':sha,'metodo':'API padrão; replay de até dois turnos do usuário, sem memory injetada','resultados':rows}
 for c in dataset['casos']:
  assert len(c['entrada']['anteriores']) <= 2
  r=v1.responder_web({'message':c['entrada']['texto'],'history':c['entrada']['anteriores']})
  row=v1.pontuar(c,r);rows.append(row)
  out['resumo']=v1.resumo(rows)
  out['novos']=v1.resumo([x for x in rows if x['caso'].startswith('pos-')])
  Path(a.saida).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
  print(c['id'],'PASS' if row['peca_correta_com_evidencia'] else 'FAIL',row['peca_observada'],'faltam='+repr(row['faltam']),'desvios='+repr(row['desvios']),'refs='+repr(row['referentes_ausentes']),flush=True)
 print(json.dumps(out['resumo'],ensure_ascii=False),flush=True)
 if a.exigir_meta:
  assert out['resumo']['pecas_corretas_com_evidencia'] >= dataset['criterios']['peca_correta_minimo']
  assert out['novos']['pecas_corretas_com_evidencia'] == 10
  assert out['resumo']['desvios'] == 0
  assert out['resumo']['trocas_dominio'] == 0
  assert out['resumo']['casos_com_referentes_ausentes'] == 0


if __name__=='__main__':main()
