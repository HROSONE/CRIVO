"""Treina a busca aprendida (busca_semantica.py): quanto vale cada evidência.

Uso:  python scripts/treinar_busca_semantica.py [--sem-teste]

Exemplos de treino, só das fichas permitidas: perguntas sintéticas tiradas de
cada fato (scripts/perguntas_sinteticas.py), com variação por sinônimo do
léxico, e "O que é X?" → primeiro fato. Para cada pergunta, a busca monta os
candidatos do acervo inteiro (as fichas com melhor BM25 e as citadas pelo
nome) e o modelo aprende, por softmax entre eles, a pôr o fato de origem em
primeiro; e, com o assunto dado, a escolher o fato dentro da ficha. O modelo
só vê evidências (TRACOS), nunca ids nem palavras: o que aprende vale para
qualquer ficha.

Fora do treino: as fichas do tutor (validação, para escolher a
regularização), dos testes congelados de leitura v1 e v2 (teste) e a
astronomia.

Medidas, contra a mesma busca só com BM25:
  dentro_ficha@1  o fato certo em 1º com o assunto dado;
  acervo@1, @5    o fato certo entre os k primeiros, assunto oculto.
O teste congelado é medido uma vez, no fim, e só em agregados. Aprovado só se
dentro_ficha@1 + acervo@5 melhorar na validação e nos dois testes congelados.
"""
import argparse
import json
import random
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

import numpy as np  # noqa: E402

from busca_semantica import CAMINHO_MODELO, TRACOS, BuscaSemantica  # noqa: E402

SEMENTE = 20261006
TESTES = ("avaliacoes/leitura_ficha_v1/teste.json", "avaliacoes/leitura_ficha_v2/teste.json")
L2 = (0.0, 0.001, 0.01, 0.1)


def _ler(caminho):
    return json.loads((RAIZ / caminho).read_text(encoding="utf-8"))


def assuntos_excluidos(compositor):
    fora = {c["assunto"] for c in _ler("dados/leitura_ficha_tutor.json")["casos"]}
    for teste in TESTES:
        fora |= {c["assunto"] for c in _ler(teste)["casos"]}
    fora |= {i for i, it in compositor.itens.items() if it.get("area") == "astronomia"}
    return fora


def _variar(pergunta, lexico, rng):
    ws = pergunta.rstrip("?").split()
    for i in rng.sample(range(len(ws)), len(ws)):
        sinonimos = sorted(lexico.sinonimos.get(ws[i].lower(), ()))
        if sinonimos:
            ws[i] = rng.choice(sinonimos)
            return " ".join(ws) + "?"
    return None


def exemplos_sinteticos(compositor, rng):
    """[(pergunta, assunto, índice do fato)] das fichas permitidas."""
    from perguntas_sinteticas import frases, perguntas_da_frase
    fora = assuntos_excluidos(compositor)
    saida = []
    for ident, it in sorted(compositor.itens.items()):
        if ident in fora:
            continue
        saida.append(("O que é " + it["nome"] + "?", ident, 0))
        pessoa = it.get("area") == "pessoas"
        for i, f in enumerate(it["fatos"]):
            texto = f["texto"] if isinstance(f, dict) else str(f)
            for frase in frases(texto) or [texto]:
                for q, _ in perguntas_da_frase(frase, it["nome"], pessoa):
                    if not re.search(re.escape(it["nome"].split()[0]), q, re.I):
                        q = q.rstrip("?") + " (" + it["nome"] + ")?"
                    saida.append((q, ident, i))
                    v = _variar(q, compositor.lexico, rng)
                    if v:
                        saida.append((v, ident, i))
    rng.shuffle(saida)
    return saida


def casos(caminho, compositor):
    return [(c["pergunta"], c["assunto"], c["fato"]) for c in _ler(caminho)["casos"]
            if c["fato"] is not None and c["assunto"] in compositor.itens]


def _matriz(cand):
    return np.asarray([[t[k] for k in TRACOS] for _, t in cand], dtype=np.float64), [j for j, _ in cand]


def grupos(busca, lista):
    """Para cada pergunta: traços dos candidatos do acervo e posição do certo
    (-1 se ficou fora), e o mesmo com só a ficha certa (assunto dado)."""
    pos = {(ident, i): j for j, (ident, i, _) in enumerate(busca.fatos)}
    saida = []
    for q, assunto, i in lista:
        alvo_j = pos[(assunto, i)]
        x, js = _matriz(busca.tracos(q))
        xf, jf = _matriz(busca.tracos(q, {assunto}))
        saida.append((x, js.index(alvo_j) if alvo_j in js else -1, xf, jf.index(alvo_j)))
    return saida


def medir(pesos, gs):
    r1 = r5 = dentro = 0
    for x, alvo, xf, alvo_f in gs:
        if alvo >= 0:
            z = x @ pesos
            # Empate conta contra: o certo precisa ficar estritamente acima.
            rank = int((z > z[alvo]).sum() + (z[:alvo] == z[alvo]).sum())
            r1 += rank < 1
            r5 += rank < 5
        dentro += int(np.argmax(xf @ pesos)) == alvo_f
    n = max(1, len(gs))
    return {"casos": len(gs), "dentro_ficha@1": round(dentro / n, 3), "acervo@1": round(r1 / n, 3),
            "acervo@5": round(r5 / n, 3)}


def nota(m):
    return m["dentro_ficha@1"] + m["acervo@5"]


def treinar(gs, l2, passos=300, lr=0.05):
    """Softmax entre candidatos (perda de lista), Adam, regularização L2."""
    usados = [(x, a) for x, a, _, _ in gs if a >= 0 and len(x) > 1]
    usados += [(xf, af) for _, _, xf, af in gs if len(xf) > 1]
    # Lote único: concatena as listas e soma por segmento.
    X = np.concatenate([x for x, _ in usados])
    seg = np.repeat(np.arange(len(usados)), [len(x) for x, _ in usados])
    inicio = np.cumsum([0] + [len(x) for x, _ in usados[:-1]])
    certos = inicio + np.asarray([a for _, a in usados])
    w = np.zeros(len(TRACOS))
    w[TRACOS.index("bm")] = 1.0
    m, v = np.zeros_like(w), np.zeros_like(w)
    perda = 0.0
    for t in range(1, passos + 1):
        z = X @ w
        zmax = np.full(len(usados), -np.inf)
        np.maximum.at(zmax, seg, z)
        e = np.exp(z - zmax[seg])
        soma = np.bincount(seg, weights=e)
        p = e / soma[seg]
        perda = float(-np.mean(np.log(p[certos] + 1e-12)))
        g = (X.T @ p - X[certos].sum(0)) / len(usados) + l2 * w
        m = 0.9 * m + 0.1 * g
        v = 0.999 * v + 0.001 * g * g
        w -= lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
    return w, perda


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--saida", default=str(CAMINHO_MODELO))
    ap.add_argument("--sem-teste", action="store_true",
                    help="ajuste: só a validação do tutor, sem tocar no teste congelado nem gravar")
    args = ap.parse_args()
    rng = random.Random(SEMENTE)
    random.seed(SEMENTE)  # perguntas_sinteticas sorteia "Quando…?"/"Em que ano…?" com o random global
    from crivo import Crivo
    comp = Crivo().compositor
    busca = BuscaSemantica(comp, caminho_modelo=RAIZ / "nao-existe.json")
    treino = grupos(busca, exemplos_sinteticos(comp, rng))
    validacao = grupos(busca, casos("dados/leitura_ficha_tutor.json", comp))
    print("perguntas de treino:", len(treino), "| com o certo entre os candidatos:",
          sum(a >= 0 for _, a, _, _ in treino), "| validação (tutor):", len(validacao), flush=True)
    base = np.zeros(len(TRACOS))
    base[TRACOS.index("bm")] = 1.0
    base_val = medir(base, validacao)
    print("só BM25: treino", medir(base, treino), "validação", base_val, flush=True)
    melhor = None
    for l2 in L2:
        w, perda = treinar(treino, l2)
        val = medir(w, validacao)
        print("L2 %-6s perda %.3f treino %s validação %s" % (l2, perda, medir(w, treino), val), flush=True)
        if melhor is None or nota(val) > nota(melhor[2]):
            melhor = (l2, w, val)
    l2, pesos, val = melhor
    print("pesos:", {t: round(float(p), 3) for t, p in zip(TRACOS, pesos)}, flush=True)
    if args.sem_teste:
        return
    # Teste congelado: uma vez, com a regularização escolhida pela validação.
    teste = {}
    for caminho in TESTES:
        gs = grupos(busca, casos(caminho, comp))
        teste[Path(caminho).parent.name] = {"aprendida": medir(pesos, gs), "so_bm25": medir(base, gs)}
    for nome, r in teste.items():
        print(nome, r, flush=True)
    aprovado = bool(nota(val) > nota(base_val)
                    and all(nota(r["aprendida"]) > nota(r["so_bm25"]) for r in teste.values()))
    print("aprovado:", aprovado, flush=True)
    meta = {
        "versao": 1, "tracos": list(TRACOS), "pesos": [round(float(p), 5) for p in pesos],
        "treino": {"perguntas": len(treino), "l2": l2, "semente": SEMENTE,
                   "dados": "perguntas sintéticas das fichas (sem tutor, testes v1/v2 e astronomia)"},
        "validacao_tutor": {"aprendida": val, "so_bm25": base_val},
        "teste_congelado": teste,
        "controle": {"aprovado": aprovado,
                     "criterio": "dentro_ficha@1 + acervo@5 maior que só BM25 na validação do tutor "
                                 "e nos testes congelados de leitura v1 e v2"},
    }
    Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.saida).write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
