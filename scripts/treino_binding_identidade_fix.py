#!/usr/bin/env python3
"""Hotfix do treino de binding de identidade.

O gerador original tinha no máximo 20*20*6 = 2400 nomes únicos, mas o treino
pedia 3000 entidades. Ao atingir 2400 ele entrava em loop infinito. Este wrapper
mantém todo o treino original e troca apenas o gerador por um espaço > 100 mil
combinações, validando unicidade antes de iniciar.
"""
from __future__ import annotations

import random

import scripts.treino_binding_identidade as treino


def make_entities_fixed(seed, n, prefix, mats):
    rng = random.Random(seed)
    a = ["na", "ze", "tor", "lum", "fi", "dra", "kel", "vo", "ri", "san",
         "bel", "tri", "mo", "pa", "xel", "gu", "pri", "do", "var", "chi"]
    b = ["lo", "ra", "mi", "to", "ve", "na", "po", "ri", "sa", "du",
         "xel", "go", "fi", "la", "ne", "bar", "ti", "cor", "zen", "mar"]
    c = ["n", "s", "r", "m", "l", "d"]
    d = ["ka", "zu", "pe", "no", "vi", "re", "ta", "mu", "si", "go"]

    capacidade = len(a) * len(b) * len(c) * len(d)
    if n > capacidade:
        raise ValueError(f"pedido de {n} nomes excede capacidade {capacidade}")

    # Embaralha o espaço cartesiano e pega n sem reposição: nunca entra em loop.
    combos = [(x, y, z, w) for x in a for y in b for z in c for w in d]
    rng.shuffle(combos)

    out = []
    for x, y, z, w in combos[:n]:
        name = prefix + x + y + w + z
        cat, funcs = rng.choice(treino.CATEGORIES)
        fn = rng.choice(funcs)
        m1, m2 = rng.sample(mats, 2)
        out.append(treino.Entity(name, cat, fn, m1, m2))

    if len(out) != n or len({e.name for e in out}) != n:
        raise AssertionError("gerador corrigido não produziu nomes únicos")
    return out


treino.make_entities = make_entities_fixed

if __name__ == "__main__":
    # Prova rápida antes de qualquer treino pesado.
    teste = make_entities_fixed(treino.SEED + 10, 3000, "t", treino.MATS)
    print(f"[HOTFIX] gerador OK: {len(teste)} nomes únicos", flush=True)
    treino.main()
