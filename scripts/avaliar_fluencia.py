"""Mede o pontuador neural de frases: em cada par (fala, natural,
estranha), ele deve dar nota maior à natural.

Uso: python scripts/avaliar_fluencia.py [dev|retido|todos] [--pasta DIR] [--detalhes]
(--detalhes só mostra pares do dev; o retido fica só no agregado.)
"""
import json
import sys
from collections import Counter
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA))


def avaliar(conjunto, pasta=None):
    from pontuador_frases import Pontuador, pontuador
    p = Pontuador(pasta) if pasta else pontuador()
    if not p.disponivel:
        return {"conjunto": conjunto, "disponivel": False, "motivo": p.motivo}, []
    dados = json.loads((PASTA / "avaliacoes" / "fluencia_v1" / (conjunto + ".json")).read_text(encoding="utf-8"))
    ok, por_tipo, erros = 0, Counter(), []
    for par in dados["pares"]:
        a = p.pontuar(par["fala"], par["natural"])
        b = p.pontuar(par["fala"], par["estranha"])
        por_tipo[par["tipo"] + (":ok" if a > b else ":erro")] += 1
        ok += a > b
        if a <= b:
            erros.append(par)
    return {"conjunto": conjunto, "pares": len(dados["pares"]), "acertos": ok,
            "por_tipo": dict(sorted(por_tipo.items()))}, erros


def main():
    args = sys.argv[1:]
    alvo = next((a for a in args if a in ("dev", "retido", "todos")), "dev")
    for conjunto in (("dev", "retido") if alvo == "todos" else (alvo,)):
        pasta = next((a.split("=", 1)[1] for a in args if a.startswith("--pasta=")), None)
        if "--pasta" in args:
            pasta = args[args.index("--pasta") + 1]
        resumo, erros = avaliar(conjunto, pasta)
        if pasta:
            resumo["pasta"] = pasta
        print(json.dumps(resumo, ensure_ascii=False))
        if "--detalhes" in args and conjunto == "dev":
            for e in erros:
                print("  [%s] %s | %s" % (e["tipo"], e["natural"], e["estranha"]))


if __name__ == "__main__":
    main()
