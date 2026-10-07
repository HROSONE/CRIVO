"""Geração ancorada v2 dentro do CRIVO: com ("com") ou sem ("sem")."""
import json, os, sys, hashlib
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
sys.path.insert(0, os.path.join(os.getcwd(), "experimentos", "geracao_ancorada"))
modo = sys.argv[1]
import crivo
if modo == "com":
    _init = crivo.Crivo.__init__
    def init(self, *a, **k):
        _init(self, *a, **k); self.usar_geracao = True
    crivo.Crivo.__init__ = init
import avaliar_busca_sem_nome, avaliar_leitura_ficha, avaliar_bateria, avaliar_lacunas
import treinar_geracao_ancorada as tga
out = {}
comp = crivo.Crivo().compositor
ex = tga.carregar(os.path.join(os.getcwd(), "experimentos", "geracao_ancorada", "dados"), comp)
val = [e for e in ex if int(hashlib.sha256(e["id"].encode()).hexdigest()[:4], 16) % 20 == 0]
f1, usou, amostras = 0.0, 0, []
for e in val:
    b = crivo.Crivo(); i, r = b.responder(e["pergunta"])
    f1 += tga.f1(r, e["resposta"]); usou += i.startswith("geracao:")
    amostras.append({"p": e["pergunta"], "id": i, "r": r[:300]})
out["tutor_val"] = {"n": len(val), "f1": round(f1 / len(val), 3), "geracao": usou}
for c in ("dev", "teste"):
    out["sem_nome_" + c] = {k: v for k, v in avaliar_busca_sem_nome.avaliar(c).items() if k in ("certo", "errado", "recusou", "inventou", "calou_bem", "ficha_posterior")}
for c in avaliar_leitura_ficha.CONJUNTOS:
    out["leitura_" + c] = avaliar_leitura_ficha.avaliar(c)[0]
for c in ("dev", "retido"):
    out["bateria_" + c] = avaliar_bateria.avaliar(c)[0]
for c in ("dev", "teste"):
    r = avaliar_lacunas.avaliar(c, bot=crivo.Crivo())
    out["lacunas_" + c] = {k: r[k] for k in ("certo", "recusou", "errado") if k in r}
print(json.dumps(out, ensure_ascii=False, indent=0))
json.dump(amostras, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
