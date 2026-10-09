from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
EVENTOS_DIR=ROOT/'experimentos/escopo_eventos_20261008'
sys.path.insert(0,str(EVENTOS_DIR))
from base import ASSOC,CONTEXT,sha,escrever
INICIAL=ROOT/'experimentos/retencao_contrastes_20261008/candidato/pesos.pt'
