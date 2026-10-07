"""Lacunas de conhecimento: perguntas do dia a dia (avaliacoes/lacunas_v1).

Uso: python scripts/avaliar_lacunas.py [dev|teste] [--detalhes]

Cada caso traz palavras esperadas; a resposta conta como:
  certo    contém alguma palavra esperada;
  recusou  o CRIVO disse que não sabe ou não entendeu;
  errado   respondeu outra coisa (a falha mais grave: afirma sem saber).
O teste congelado é lido só em agregados (sem --detalhes).
"""
import json
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

RECUSAS = ("não entendi", "não sei", "não encontrei", "não tenho", "ainda não tenho", "não conheço",
           "não consegui", "prefiro não")


def _norm(t):
    t = unicodedata.normalize("NFKD", t.casefold())
    return "".join(c for c in t if not unicodedata.combining(c))


def classificar(rotulo, resposta, esperado):
    texto = _norm(resposta)
    if any(_norm(e) in texto for e in esperado):
        return "certo"
    if rotulo in ("fora", "nocao:nao_sei") or any(_norm(r) in texto for r in RECUSAS):
        return "recusou"
    return "errado"


def avaliar(conjunto="dev", detalhes=False, bot=None):
    casos = json.loads((RAIZ / "avaliacoes" / "lacunas_v1" / ("%s.json" % conjunto)).read_text(encoding="utf-8"))["casos"]
    if bot is None:
        from crivo import Crivo
        bot = Crivo()
    total, por_area, linhas = Counter(), defaultdict(Counter), []
    for c in casos:
        rotulo, resposta = bot.responder(c["pergunta"])
        estado = classificar(rotulo, resposta, c["esperado"])
        total[estado] += 1
        por_area[c["area"]][estado] += 1
        linhas.append((estado, rotulo, c["pergunta"], resposta[:160]))
    r = {"casos": len(casos), "certo": total["certo"], "recusou": total["recusou"], "errado": total["errado"]}
    if detalhes:
        r["por_area"] = {a: dict(v) for a, v in sorted(por_area.items())}
        r["linhas"] = linhas
    return r


if __name__ == "__main__":
    conjunto = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "dev"
    detalhes = "--detalhes" in sys.argv and conjunto != "teste"
    r = avaliar(conjunto, detalhes)
    for estado, rotulo, q, resp in r.pop("linhas", []):
        if estado != "certo":
            print("%-7s %-28s %s\n        %s" % (estado, rotulo, q, resp.replace("\n", " ")))
    print(json.dumps(r, ensure_ascii=False))
