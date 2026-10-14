"""Envelope da voz por quadro (30 fps), para a animação reagir à fala.

Uso: python scripts/energia_voz.py <wav da narração> public/voz/energia.json
"""
import json
import sys
import wave

import numpy as np

FPS = 30

entrada, saida = sys.argv[1], sys.argv[2]
with wave.open(entrada) as w:
    sr = w.getframerate()
    canais = w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, canais).mean(axis=1) / 32768

passo = sr // FPS
n = len(x) // passo
rms = np.sqrt((x[: n * passo].reshape(n, passo) ** 2).mean(axis=1))
db = 20 * np.log10(rms + 1e-9)
baixo, alto = np.percentile(db, 5), np.percentile(db, 98)
norm = np.clip((db - baixo) / (alto - baixo), 0, 1)
# ataque rápido, queda suave
suave = np.zeros(n)
for i, v in enumerate(norm):
    anterior = suave[i - 1] if i else 0
    suave[i] = v if v > anterior else anterior * 0.85 + v * 0.15
with open(saida, "w") as f:
    json.dump([round(float(v), 3) for v in suave], f)
print(n, "quadros")
