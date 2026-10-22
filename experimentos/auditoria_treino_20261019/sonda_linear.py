"""Uso: python3 sonda_linear.py 25  (formas por situação no treino da sonda)

Sonda linear: o estado final do 46M v4 (no chat) separa as situações da fase 5?
Treina regressão logística em formas do treino e testa no blind v3 (frases nunca vistas)."""
import sys, json, gzip, random, time
from collections import defaultdict
import numpy as np
REPO = "/home/user/CRIVO"
sys.path[:0] = [REPO, REPO + "/experimentos/fase6b_conversa_humana"]
import conversa_v3d as cv, gerar_fase6b
m = cv.Conversa46mNumpy(); Q = gerar_fase6b.resumo_identidade()
d = json.load(gzip.open(REPO + "/experimentos/fase5_conversa_20261013/dados_fase5_v3.json.gz"))
rng = random.Random(7)
por = defaultdict(list)
for c in d["treino"]: por[c["situacao"]].append(c)
treino = [c for s, L in por.items() for c in rng.sample(L, min(int(sys.argv[1]), len(L)))]
teste = d["blind_v3"]
def feat(c):
    ids = m.prompt_conversa({"quem": Q, **(c["contexto"] or {})}, c["historico"], c["mensagem"])
    h = m._passo(ids, 0, {})
    return h[-1]
t = time.time()
Xtr = np.stack([feat(c) for c in treino]); print("treino", len(treino), time.time() - t, flush=True)
Xte = np.stack([feat(c) for c in teste]); print("teste", len(teste), time.time() - t, flush=True)
sits = sorted(por); idx = {s: i for i, s in enumerate(sits)}
ytr = np.array([idx[c["situacao"]] for c in treino]); yte = np.array([idx.get(c["situacao"], -1) for c in teste])
mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
A, B = (Xtr - mu) / sd, (Xte - mu) / sd
W = np.zeros((A.shape[1], len(sits))); b = np.zeros(len(sits)); lr, lam = 0.5, 1e-3
Y = np.eye(len(sits))[ytr]
for it in range(600):
    z = A @ W + b; z -= z.max(1, keepdims=True); p = np.exp(z); p /= p.sum(1, keepdims=True)
    g = (p - Y) / len(A); W -= lr * (A.T @ g + lam * W); b -= lr * g.sum(0)
pr = B @ W + b
top1 = (pr.argmax(1) == yte).mean(); top5 = np.mean([yte[i] in np.argsort(-pr[i])[:5] for i in range(len(yte))])
print(json.dumps({"formas_por_situacao": int(sys.argv[1]), "n_treino": len(treino), "n_blind_v3": len(teste),
                  "situacoes": len(sits), "sem_rotulo_no_treino": int((yte < 0).sum()),
                  "treino_acc": float(((A @ W + b).argmax(1) == ytr).mean()),
                  "blind_v3_top1": round(float(top1), 4), "blind_v3_top5": round(float(top5), 4)}, ensure_ascii=False))
