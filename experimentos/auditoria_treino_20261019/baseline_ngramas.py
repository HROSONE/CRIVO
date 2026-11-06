"""Linha de base sem rede profunda: centróide de n-gramas de caracteres e palavras, só a mensagem.

Uso: python3 baseline_ngramas.py experimentos/fase5_conversa_20261013/dados_fase5_v3.json.gz
Treina com as formas distintas do treino e mede no blind v3 (frases nunca vistas)."""
import gzip, json, re, sys, unicodedata, zlib
import numpy as np

D = 1 << 15


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " " + re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip() + " "


def vec(s):
    s = norm(s)
    v = np.zeros(D, np.float32)
    for n in (2, 3, 4):
        for i in range(len(s) - n + 1):
            v[zlib.crc32(s[i:i + n].encode()) % D] += 1
    for w in s.split():
        v[zlib.crc32(("w:" + w).encode()) % D] += 1
    return v / (np.linalg.norm(v) + 1e-9)


d = json.load(gzip.open(sys.argv[1]))
vistos = {}
for c in d["treino"]:
    vistos.setdefault((norm(c["mensagem"]), c["situacao"]), c)
sits = sorted({s for _, s in vistos})
idx = {s: i for i, s in enumerate(sits)}
C = np.zeros((len(sits), D), np.float32)
for c in vistos.values():
    C[idx[c["situacao"]]] += vec(c["mensagem"])
C /= np.linalg.norm(C, axis=1, keepdims=True) + 1e-9
T = np.stack([vec(c["mensagem"]) for c in d["blind_v3"]])
yt = np.array([idx[c["situacao"]] for c in d["blind_v3"]])
pr = T @ C.T
top5 = np.argsort(-pr, axis=1)[:, :5]
print(json.dumps({"formas_distintas_treino": len(vistos), "n_blind_v3": len(yt),
                  "centroide_top1": round(float((pr.argmax(1) == yt).mean()), 4),
                  "centroide_top5": round(float((top5 == yt[:, None]).any(1).mean()), 4)}))
