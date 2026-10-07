"""Mede o codificador de sentido na busca: com ("com") ou sem ("sem")."""
import json, sys, os
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
modo = sys.argv[1]
import busca_semantica
if modo == "sem":
    busca_semantica.BuscaSemantica.proximidades = lambda self, p: None
import avaliar_busca_sem_nome, avaliar_leitura_ficha, avaliar_bateria, avaliar_lacunas
out = {}
for c in ("dev", "teste"):
    out["sem_nome_" + c] = avaliar_busca_sem_nome.avaliar(c)
for c in avaliar_leitura_ficha.CONJUNTOS:
    out["leitura_" + c] = avaliar_leitura_ficha.avaliar(c)[0]
for c in ("dev", "retido"):
    out["bateria_" + c] = avaliar_bateria.avaliar(c)[0]
for c in ("dev", "teste"):
    r = avaliar_lacunas.avaliar(c)
    out["lacunas_" + c] = {k: r[k] for k in ("certo", "recusou", "errado") if k in r}
print(json.dumps(out, ensure_ascii=False, indent=0))
