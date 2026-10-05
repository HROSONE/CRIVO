"""Avalia a compreensão no teste congelado avaliacoes/entendimento_v1/teste.json.

Positivo correto: a resposta vem do id esperado (base editorial ou ficha).
Negativo correto: o CRIVO não responde com conteúdo de outro assunto
(admite que não sabe, pede esclarecimento ou conversa sem afirmar fatos).
"""
import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

RECUSAS = ("fora", "duvida", "social:nao_entendido", "conversa:esclarecer", "nocao:nao_sei")


def id_resposta(ident):
    return ident.split(":", 1)[1] if ident.startswith(("conhecimento:", "pratica:")) else ident


def avaliar(crivo_factory, teste=None):
    teste = teste or json.loads((RAIZ / "avaliacoes/entendimento_v1/teste.json").read_text(encoding="utf-8"))
    resultado = {"positivos": [], "negativos": []}
    for caso in teste["positivos"]:
        bot = crivo_factory()
        ident, resposta = bot.responder(caso["p"])
        temas = getattr(bot.contexto_textual, "temas", ()) or ()
        ok = id_resposta(ident) in caso["ids"] or any(t in caso["ids"] for t in temas)
        resultado["positivos"].append({"p": caso["p"], "id": ident, "ok": ok,
                                       "mecanismo": (bot.historico[-1].get("mecanismo") if bot.historico else None)})
    for p in teste["negativos"]:
        bot = crivo_factory()
        ident, resposta = bot.responder(p)
        ok = ident in RECUSAS or ident.startswith(("social:", "conversa:", "nocao:", "contexto:"))
        resultado["negativos"].append({"p": p, "id": ident, "ok": ok,
                                       "mecanismo": (bot.historico[-1].get("mecanismo") if bot.historico else None)})
    pos = resultado["positivos"]; neg = resultado["negativos"]
    resultado["resumo"] = {
        "positivos_corretos": sum(r["ok"] for r in pos), "positivos": len(pos),
        "negativos_corretos": sum(r["ok"] for r in neg), "negativos": len(neg),
        "respostas_neurais": sum(r["mecanismo"] == "compreensao_neural" for r in pos + neg),
    }
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida")
    parser.add_argument("--detalhes", action="store_true")
    args = parser.parse_args()
    from crivo import Crivo
    r = avaliar(Crivo)
    if args.detalhes:
        for chave in ("positivos", "negativos"):
            for item in r[chave]:
                print(("OK   " if item["ok"] else "FALHA"), chave[:3], item["id"][:34].ljust(34), item["p"])
    print(json.dumps(r["resumo"], ensure_ascii=False))
    if args.saida:
        Path(args.saida).write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
