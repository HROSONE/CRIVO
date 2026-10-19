"""Substituição do v6c: cada caso novo entra no lugar de casos antigos da fase 5 da MESMA situação (20/10/2026).

No v6 e no v6b os casos novos foram ACRESCENTADOS, e as situações que não ganharam nada perderam peso no treino
(urgência −16 pontos no v6b). Aqui o peso de cada situação, contando as repetições, fica igual ao da receita sem v6:

    casos_antigos(s) × rep_f5  ≈  (casos_antigos(s) − tirados(s)) × rep_f5 + novos(s) × rep_v6

Saem primeiro os casos antigos cuja fala mais se repete (a fase 5 repete cada fala ~5 vezes), para perder o mínimo de
variedade antiga. No máximo metade dos casos antigos de uma situação sai; se não couber, entram menos casos novos.
"""
import math
import random
from collections import Counter, defaultdict

LIMITE_TIRAR = 0.5


def substituir(fase5, novos, rep_f5, rep_v6, semente, chave):
    """fase5, novos: listas de casos com "situacao" e "mensagem". Devolve (fase5_que_fica, novos_que_entram, relatorio)."""
    rr = random.Random(semente)
    antigos_por, novos_por = defaultdict(list), defaultdict(list)
    for i, c in enumerate(fase5):
        antigos_por[c["situacao"]].append(i)
    for c in novos:
        novos_por[c["situacao"]].append(c)
    tirar, entram, rel = set(), [], {}
    for s in sorted(novos_por):
        antigos, lista = antigos_por.get(s, []), novos_por[s]
        cabe = int(len(antigos) * LIMITE_TIRAR)
        if not cabe:
            rel[s] = {"antigos": len(antigos), "novos_pedidos": len(lista), "novos": 0, "tirados": 0}
            continue
        n_novos = min(len(lista), (cabe * rep_f5) // rep_v6)
        escolhidos = rr.sample(lista, n_novos) if n_novos < len(lista) else list(lista)
        n_tirar = min(cabe, math.ceil(n_novos * rep_v6 / rep_f5))
        repet = Counter(chave(fase5[i]["mensagem"]) for i in antigos)
        ordem = sorted(antigos, key=lambda i: (-repet[chave(fase5[i]["mensagem"])], rr.random()))
        tirar.update(ordem[:n_tirar])
        entram += escolhidos
        rel[s] = {"antigos": len(antigos), "novos_pedidos": len(lista), "novos": n_novos, "tirados": n_tirar,
                  "peso_antes": len(antigos) * rep_f5, "peso_depois": (len(antigos) - n_tirar) * rep_f5 + n_novos * rep_v6}
    fica = [c for i, c in enumerate(fase5) if i not in tirar]
    return fica, entram, rel


def conferir(rel, rep_v6):
    """O peso de cada situação muda no máximo o arredondamento de um caso novo."""
    ruins = {s: r for s, r in rel.items() if "peso_antes" in r and abs(r["peso_depois"] - r["peso_antes"]) > rep_v6}
    assert not ruins, ruins
    return True
