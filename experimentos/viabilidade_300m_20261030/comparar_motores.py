"""Motor em C antes × depois, alternados no mesmo processo (a CPU é disputada; vale o melhor de várias vezes).
Uso: python comparar.py <repo> <pasta> <lib_antes> <lib_depois> <46m|300m> <threads> <repeticoes>"""
import os, sys, time, json
import numpy as np
REPO, OUT, ANTES, DEPOIS, QUAL, TH, REP = sys.argv[1:8]
sys.path.insert(0, REPO); os.chdir(REPO)
import motor_nativo
npz = "artefatos/conversa46m_v7c_pt/pesos_numpy.npz" if QUAL == "46m" else os.path.join(OUT, "sintetico_300m.npz")
arq = os.path.join(OUT, f"motor_{QUAL}.bin")
if not os.path.exists(arq):
    motor_nativo.exportar(npz, arq)
motores = {"antes": motor_nativo.MotorNativo(ANTES, arq, threads=int(TH)),
           "depois": motor_nativo.MotorNativo(DEPOIS, arq, threads=int(TH))}
ids = [int(x) for x in np.random.default_rng(1).integers(10, 8000, size=400)]
melhor = {k: {"prompt150": 9e9, "prompt400": 9e9, "token": 9e9} for k in motores}
dif = 0.0
for r in range(int(REP)):
    for nome, m in motores.items():
        t0 = time.perf_counter(); a = m.avancar(ids[:150], 0); t1 = time.perf_counter()
        melhor[nome]["prompt150"] = min(melhor[nome]["prompt150"], t1 - t0)
        t0 = time.perf_counter(); a = m.avancar(ids, 0); t1 = time.perf_counter()
        melhor[nome]["prompt400"] = min(melhor[nome]["prompt400"], t1 - t0)
        t0 = time.perf_counter()
        for i in range(20):
            a = m.avancar([int(a.argmax()) % 8000 + 10], 400 + i)
        melhor[nome]["token"] = min(melhor[nome]["token"], (time.perf_counter() - t0) / 20)
# mesmas contas? (logits do prompt de 400 nos dois motores)
la = motores["antes"].avancar(ids, 0).copy(); lb = motores["depois"].avancar(ids, 0).copy()
print(json.dumps({"modelo": QUAL, "threads": int(TH),
                  **{k: {x: round(v, 3) for x, v in d.items()} for k, d in melhor.items()},
                  "dif_max_logits": float(abs(la - lb).max()), "mesmo_argmax": int(la.argmax()) == int(lb.argmax())}))
