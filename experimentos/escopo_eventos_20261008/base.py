"""Acessa somente os módulos e pesos próprios já publicados do CRIVO."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
ASSOC=ROOT/'experimentos/associacao_fatos_20261008'
CONTEXT=ROOT/'experimentos/interpretador_contextual_20261008'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(CONTEXT));sys.path.insert(0,str(ASSOC))
INICIAL=ASSOC/'candidato_normalizado/pesos.pt'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def escrever(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
