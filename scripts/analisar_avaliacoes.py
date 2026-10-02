"""Lê o arquivo baixado no site ("Baixar avaliações") e resume a avaliação
humana: aprovação geral e por tipo de resposta, e as respostas reprovadas.

Uso: python scripts/analisar_avaliacoes.py crivo-avaliacoes.json [--reprovadas]
"""
import json
import sys
from collections import defaultdict


def tipo(ident):
    return (ident or "?").split(":")[0]


def resumir(dados):
    lista = dados.get("avaliacoes", []) if isinstance(dados, dict) else []
    por_tipo = defaultdict(lambda: [0, 0])
    for r in lista:
        t = tipo(r.get("id"))
        por_tipo[t][0 if r.get("nota") == 1 else 1] += 1
    total_bom = sum(b for b, _ in por_tipo.values())
    total = sum(b + r for b, r in por_tipo.values())
    return {
        "avaliacoes": total,
        "aprovacao": round(total_bom / total, 3) if total else None,
        "por_tipo": {t: {"boas": b, "ruins": r, "aprovacao": round(b / (b + r), 3)}
                     for t, (b, r) in sorted(por_tipo.items())},
    }, [r for r in lista if r.get("nota") == -1]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as f:
        resumo, ruins = resumir(json.load(f))
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    if "--reprovadas" in sys.argv:
        for r in ruins:
            print("\n[%s] %s\n  → %s" % (r.get("id"), r.get("pergunta"), (r.get("resposta") or "")[:200]))


if __name__ == "__main__":
    main()
