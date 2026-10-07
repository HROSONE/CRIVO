"""Gerador como resgate: quando o CRIVO recusa uma pergunta aberta que cita um
assunto com ficha, o Transformer tenta responder com os fatos da ficha."""
import hashlib, json
from pathlib import Path, re, sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import treinar_geracao_ancorada as tga
import os; sys.path.insert(0, os.getcwd())
from crivo import Crivo
from curriculo_mundo import texto_fato
from geracao_ancorada import geracao, norm, palavras_conteudo
g = geracao()
ABERTA = re.compile(r"(?:o que|que|qual|quais|quem|quando|onde|como|por ?que|quanto|quantos|quantas|para que|pra que)\b")
def recusa(bot, ident, r):
    return ident in ("fora", "social:nao_entendido", "conversa:esclarecer", "leitura:aproximacao", "duvida") or r.startswith("Reconheci o assunto")
def ordenar(fatos, pergunta):
    q = {w[:4] for w in palavras_conteudo(pergunta)}
    return sorted(fatos, key=lambda f: -len(q & {w[:4] for w in palavras_conteudo(f)}))
def tipo_ok(texto, pergunta):
    n = norm(pergunta)
    if re.search(r"\bquando\b|\bem que ano\b", n) and not re.search(r"\b1\d{3}\b|\b20\d\d\b|\bseculo\b", norm(texto)):
        return False
    if re.search(r"\bquant[oa]s?\b", n) and not re.search(r"\d", texto):
        return False
    return True
fonte = sys.argv[2]
if fonte == "val":
    comp = Crivo().compositor
    ex = tga.carregar(str(Path(__file__).resolve().parent / "dados"), comp)
    casos = [(e["pergunta"], e["resposta"]) for e in ex if int(hashlib.sha256(e["id"].encode()).hexdigest()[:4], 16) % 20 == 0]
else:
    d = json.load(open(fonte))
    casos = [(c.get("pergunta") or c.get("message") or c.get("texto"), json.dumps(c, ensure_ascii=False)[:200]) for c in (d if isinstance(d, list) else d.get("casos", d.get("itens", [])))]
tot = {"n": len(casos), "recusou": 0, "com_assunto": 0, "respondeu": 0}
for p, ref in casos:
    b = Crivo(); ident, r = b.responder(p)
    if not recusa(b, ident, r) or not ABERTA.match(norm(p).strip()):
        continue
    tot["recusou"] += 1
    a = b.compositor.assunto_mencionado(p)
    if not a:
        continue
    tot["com_assunto"] += 1
    fatos = ordenar([texto_fato(f) for f in b.compositor.itens[a]["fatos"]], p)[:6]
    out = g.gerar(p, fatos)
    if out and tipo_ok(out, p):
        tot["respondeu"] += 1
        print("P:", p, "\n  antes:", r[:120].replace("\n", " "), "\n  GERADO:", out, "\n  ref:", ref[:250], flush=True)
print(tot)
