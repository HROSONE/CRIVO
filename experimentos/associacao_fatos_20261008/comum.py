"""Reutiliza a arquitetura e os decodificadores próprios congelados da rodada 1."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
ANTERIOR = ROOT / 'experimentos/interpretador_contextual_20261008'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ANTERIOR))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def escrever(p, value):
    Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
