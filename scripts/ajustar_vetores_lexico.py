"""Ajusta vetores de palavras com sinônimos e antônimos (counter-fitting).

Vetores aprendidos só pelo contexto aproximam antônimos ("quente"/"frio"),
porque eles aparecem nas mesmas frases. Seguindo Mrkšić et al. (2016),
"Counter-fitting Word Vectors to Linguistic Constraints":
  - antônimos são afastados  (perda max(0, δ − d(u, w)));
  - sinônimos são aproximados (perda max(0, d(u, w) − γ));
  - vizinhos originais conservam a distância (preservação do espaço).
d é a distância do cosseno. Pares "reservados" do léxico não entram no
ajuste e medem se ele generaliza.

Uso: python scripts/ajustar_vetores_lexico.py --entrada artefatos/vetores_pt \
        --lexico dados/lexico_sinonimos_antonimos_pt.json --saida artefatos/vetores_pt
"""
import argparse
import json
from pathlib import Path

import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lexico_pt import flexoes  # noqa: E402


def expandir(pares, indice):
    saida = set()
    for classe, a, b in pares:
        fa = [w for w in flexoes(classe, a) if w in indice]
        fb = [w for w in flexoes(classe, b) if w in indice]
        # Pareia forma com forma de mesma terminação quando possível
        # ("fortes"/"intensos"), e as formas-base entre si.
        if a in indice and b in indice:
            saida.add((indice[a], indice[b]))
        for x in fa:
            for y in fb:
                if x[-1] == y[-1] or (x.endswith("s") and y.endswith("s")):
                    saida.add((indice[x], indice[y]))
    return sorted(saida)


def media_cos(m, pares):
    return float(np.mean([m[i] @ m[j] for i, j in pares])) if pares else None


def ajustar(vetores, sinonimos, antonimos, epocas=20, taxa=0.1, delta=1.0, gama=0.0,
            limiar_vizinho=0.75, semente=7):
    m = vetores.astype(np.float64).copy()
    original = m.copy()
    palavras = sorted({i for p in sinonimos + antonimos for i in p})
    # Vizinhos originais das palavras do léxico, para preservar o espaço.
    vizinhos = []
    for i in palavras:
        sims = original @ original[i]
        for j in np.nonzero(sims >= limiar_vizinho)[0]:
            if j != i:
                vizinhos.append((i, int(j), 1.0 - float(sims[j])))
    rng = np.random.default_rng(semente)
    for _ in range(epocas):
        grad = np.zeros_like(m)
        for i, j in antonimos:
            d = 1.0 - m[i] @ m[j]
            if d < delta:          # empurra para longe: aumenta d
                grad[i] += m[j]
                grad[j] += m[i]
        for i, j in sinonimos:
            d = 1.0 - m[i] @ m[j]
            if d > gama:           # puxa para perto: diminui d
                grad[i] -= m[j]
                grad[j] -= m[i]
        for i, j, d0 in vizinhos:
            if 1.0 - m[i] @ m[j] > d0:
                grad[i] -= m[j]
                grad[j] -= m[i]
        m -= taxa * grad
        m /= np.linalg.norm(m, axis=1, keepdims=True) + 1e-9
        rng.random()  # reprodutibilidade explícita da sequência
    return m.astype(np.float32), len(vizinhos)


def controle(m, lexico, indice, rng):
    sin_r = expandir(lexico["reservados"]["sinonimos"], indice)
    ant_r = expandir(lexico["reservados"]["antonimos"], indice)
    sin_t = expandir(lexico["treino"]["sinonimos"], indice)
    ant_t = expandir(lexico["treino"]["antonimos"], indice)
    amostra = rng.integers(0, len(m), (2000, 2))
    aleatorio = float(np.mean(np.sum(m[amostra[:, 0]] * m[amostra[:, 1]], axis=1)))
    r = lambda x: None if x is None else round(x, 3)
    return {
        # Os campos usados pelo Crivo medem SOMENTE pares reservados.
        "pares_equivalentes": r(media_cos(m, sin_r)), "pares_antonimos": r(media_cos(m, ant_r)),
        "pares_aleatorios": round(aleatorio, 3), "pares_avaliados": len(sin_r),
        "antonimos_avaliados": len(ant_r),
        "treino_sinonimos": r(media_cos(m, sin_t)), "treino_antonimos": r(media_cos(m, ant_t)),
        "origem": "pares reservados do léxico (não usados no ajuste)",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entrada", required=True)
    p.add_argument("--lexico", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--epocas", type=int, default=20)
    p.add_argument("--taxa", type=float, default=0.1)
    a = p.parse_args()
    entrada, saida = Path(a.entrada), Path(a.saida)
    vocab = json.loads((entrada / "vocabulario.json").read_text(encoding="utf-8"))
    vetores = np.load(entrada / "vetores.npy").astype(np.float32)
    treino = json.loads((entrada / "treino.json").read_text(encoding="utf-8"))
    lexico = json.loads(Path(a.lexico).read_text(encoding="utf-8"))
    indice = {w: i for i, w in enumerate(vocab)}
    sinonimos = expandir(lexico["treino"]["sinonimos"], indice)
    antonimos = expandir(lexico["treino"]["antonimos"], indice)
    rng = np.random.default_rng(1)
    antes = controle(vetores.astype(np.float64), lexico, indice, rng)
    ajustados, n_viz = ajustar(vetores, sinonimos, antonimos, a.epocas, a.taxa)
    depois = controle(ajustados.astype(np.float64), lexico, indice, np.random.default_rng(1))
    saida.mkdir(parents=True, exist_ok=True)
    np.save(saida / "vetores.npy", ajustados.astype(np.float16))
    (saida / "vocabulario.json").write_text(json.dumps(vocab, ensure_ascii=False), encoding="utf-8")
    treino["controle_skipgram"] = treino.get("controle_skipgram", treino.get("controle"))
    treino["controle"] = depois
    treino["ajuste_lexico"] = {
        "metodo": "counter-fitting (Mrkšić et al., 2016), NumPy", "lexico": str(a.lexico),
        "pares_sinonimos_treino": len(sinonimos), "pares_antonimos_treino": len(antonimos),
        "vizinhos_preservados": n_viz, "epocas": a.epocas, "taxa": a.taxa,
        "reservados_antes": antes, "reservados_depois": depois,
    }
    (saida / "treino.json").write_text(json.dumps(treino, ensure_ascii=False, indent=1), encoding="utf-8")
    print("antes ", json.dumps(antes, ensure_ascii=False))
    print("depois", json.dumps(depois, ensure_ascii=False))


if __name__ == "__main__":
    main()
