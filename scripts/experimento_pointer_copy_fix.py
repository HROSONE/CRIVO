#!/usr/bin/env python3
"""Hotfix do Pointer-Copy Causal v1.

Garante que train/dev/blind sejam disjuntos por construcao, sem introduzir
prefixos especificos por split (o que criaria um atalho lexical). Mantem o
restante do experimento inalterado.
"""
from __future__ import annotations

import random

import scripts.experimento_pointer_copy as exp

_USED_NAMES: set[str] = set()


def make_entities_disjoint(tok, seed: int, n: int, mode: str):
    rng = random.Random(seed)
    families = [0, 1, 2] if mode == "train" else ([0, 1, 2, 3, 4] if mode == "blind" else [0, 1, 2, 3])
    local_seen: set[str] = set()
    out = []
    tries = 0
    max_tries = n * 2000

    while len(out) < n and tries < max_tries:
        tries += 1
        fam = rng.choice(families)
        name = exp.candidate_name(rng, fam)
        if name in local_seen or name in _USED_NAMES:
            continue

        ids = tok.encode(name, add_special_tokens=False).ids
        if not (1 <= len(ids) <= 4):
            continue

        local_seen.add(name)
        cat, funcs = rng.choice(exp.CATEGORIES)
        fn = rng.choice(funcs)
        m1, m2 = rng.sample(exp.MATERIALS, 2)
        lexical = "distant" if fam in (3, 4) else "close"
        out.append(exp.Entity(name, cat, fn, m1, m2, lexical, len(ids)))

    if len(out) != n:
        raise RuntimeError(
            f"nao consegui gerar {n} entidades disjuntas 1-4 tokens para {mode}; obtive {len(out)}"
        )

    _USED_NAMES.update(e.name for e in out)
    return out


exp.make_entities = make_entities_disjoint

if __name__ == "__main__":
    print("[HOTFIX SPLITS] train/dev/blind serao gerados sem nomes repetidos", flush=True)
    exp.main()
