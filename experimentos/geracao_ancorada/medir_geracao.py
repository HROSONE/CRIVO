"""Mede a geração ancorada dentro do CRIVO nas perguntas de validação do tutor
(fichas fora do treino): com e sem geração, F1 contra a resposta do tutor."""
import hashlib, json
from pathlib import Path, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import treinar_geracao_ancorada as tga
from crivo import Crivo
comp = Crivo().compositor
ex = tga.carregar(str(Path(__file__).resolve().parent / "dados"), comp)
val = [e for e in ex if int(hashlib.sha256(e["id"].encode()).hexdigest()[:4], 16) % 20 == 0]
res = {"n": len(val), "usou": 0, "f1_sem": 0.0, "f1_com": 0.0, "f1_sem_onde_usou": 0.0, "f1_com_onde_usou": 0.0, "tempo": 0.0}
amostras = []
for e in val:
    a = Crivo(); _, r0 = a.responder(e["pergunta"])
    b = Crivo(); b.usar_geracao = True
    t = time.time(); _, r1 = b.responder(e["pergunta"]); res["tempo"] += time.time() - t
    f0, f1 = tga.f1(r0, e["resposta"]), tga.f1(r1, e["resposta"])
    res["f1_sem"] += f0; res["f1_com"] += f1
    if b.voz_do_turno == "geracao_ancorada":
        res["usou"] += 1; res["f1_sem_onde_usou"] += f0; res["f1_com_onde_usou"] += f1
        amostras.append({"p": e["pergunta"], "antes": r0, "depois": r1, "tutor": e["resposta"]})
n, u = res["n"], max(1, res["usou"])
for k in ("f1_sem", "f1_com", "tempo"): res[k] = round(res[k] / n, 3)
for k in ("f1_sem_onde_usou", "f1_com_onde_usou"): res[k] = round(res[k] / u, 3)
print(json.dumps(res, ensure_ascii=False))
json.dump(amostras, open("amostras_geracao.json", "w"), ensure_ascii=False, indent=1)
