"""Vetores de palavras em português treinados do zero (skip-gram com
amostragem negativa), em NumPy, sobre artigos públicos da Wikipédia já
usados pelo pré-treino do projeto (SHA verificado em baixar_fontes_linguagem).

O resultado serve só para reconhecer paráfrases de UMA palavra na busca
factual ("ventos fortes" ~ "ventos intensos"). Não gera texto nem fatos.

Uso:
  python scripts/treinar_vetores_palavras.py --wikipedia wikipedia.pt.parquet \
      --saida artefatos/vetores_pt --documentos 20000 --vocabulario 40000 --dim 64
"""
import argparse
import json
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.casefold())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def frases(textos):
    for texto in textos:
        for linha in re.split(r"[.!?\n]+", normalizar(texto)):
            palavras = re.findall(r"[a-z]+", linha)
            if len(palavras) >= 3:
                yield palavras


def ler_wikipedia(caminho, documentos):
    import pyarrow.parquet as pq
    tabela = pq.read_table(caminho, columns=["text"])
    return [t for t in tabela.column("text").to_pylist()[:documentos] if t]


def treinar(sentencas, vocabulario, dim, janela, negativos, epocas, taxa, semente, limite_segundos):
    rng = np.random.default_rng(semente)
    contagem = Counter(p for s in sentencas for p in s)
    vocab = [p for p, c in contagem.most_common(vocabulario) if c >= 5]
    indice = {p: i for i, p in enumerate(vocab)}
    freq = np.array([contagem[p] for p in vocab], dtype=np.float64)
    total = freq.sum()
    # Subamostragem de palavras muito frequentes (Mikolov et al., 2013).
    manter = np.minimum(1.0, np.sqrt(1e-4 * total / freq) + 1e-4 * total / freq)
    ruido = freq ** 0.75
    ruido /= ruido.sum()
    tabela_ruido = rng.choice(len(vocab), size=10_000_000, p=ruido).astype(np.int32)
    entrada = ((rng.random((len(vocab), dim)) - 0.5) / dim).astype(np.float32)
    saida = np.zeros((len(vocab), dim), dtype=np.float32)
    ids = [np.array([indice[p] for p in s if p in indice], dtype=np.int32) for s in sentencas]
    inicio = time.time()
    pares_vistos = 0
    taxa_inicial = taxa
    passos_totais = max(1, epocas * len(ids))
    for epoca in range(epocas):
        rng.shuffle(ids)
        for n, frase in enumerate(ids):
            # Decaimento linear da taxa, como no word2vec original.
            taxa = max(taxa_inicial * 1e-4, taxa_inicial * (1 - (epoca * len(ids) + n) / passos_totais))
            if len(frase) < 2:
                continue
            frase = frase[rng.random(len(frase)) < manter[frase]]
            if len(frase) < 2:
                continue
            centros, contextos = [], []
            for k, c in enumerate(frase):
                r = rng.integers(1, janela + 1)
                for j in range(max(0, k - r), min(len(frase), k + r + 1)):
                    if j != k:
                        centros.append(c)
                        contextos.append(frase[j])
            centros = np.array(centros, dtype=np.int32)
            contextos = np.array(contextos, dtype=np.int32)
            amostras = tabela_ruido[rng.integers(0, len(tabela_ruido), (len(centros), negativos))]
            alvos = np.concatenate([contextos[:, None], amostras], axis=1)
            rotulos = np.zeros(alvos.shape, dtype=np.float32)
            rotulos[:, 0] = 1.0
            vc = entrada[centros]
            vo = saida[alvos]
            pontuacao = np.einsum("bd,bkd->bk", vc, vo)
            erro = (1.0 / (1.0 + np.exp(-np.clip(pontuacao, -10, 10))) - rotulos) * taxa
            grad_c = np.einsum("bk,bkd->bd", erro, vo)
            grad_o = erro[:, :, None] * vc[:, None, :]
            np.add.at(saida, alvos, -grad_o)
            np.add.at(entrada, centros, -grad_c)
            pares_vistos += len(centros)
            if n % 20000 == 0:
                print("epoca {} frase {}/{} pares {} {:.0f}s".format(
                    epoca + 1, n, len(ids), pares_vistos, time.time() - inicio), flush=True)
            if time.time() - inicio > limite_segundos:
                print("limite de tempo atingido; salvando o estado atual", flush=True)
                return vocab, entrada
    return vocab, entrada


def vizinhos(vocab, vetores, palavra, k=8):
    indice = {p: i for i, p in enumerate(vocab)}
    if palavra not in indice:
        return []
    normas = vetores / (np.linalg.norm(vetores, axis=1, keepdims=True) + 1e-9)
    sim = normas @ normas[indice[palavra]]
    return [(vocab[i], round(float(sim[i]), 3)) for i in np.argsort(-sim)[1:k + 1]]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--wikipedia", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--documentos", type=int, default=20000)
    p.add_argument("--vocabulario", type=int, default=40000)
    p.add_argument("--dim", type=int, default=64)
    p.add_argument("--janela", type=int, default=5)
    p.add_argument("--negativos", type=int, default=5)
    p.add_argument("--epocas", type=int, default=2)
    p.add_argument("--taxa", type=float, default=0.025)
    p.add_argument("--semente", type=int, default=20261002)
    p.add_argument("--limite-minutos", type=float, default=150)
    a = p.parse_args()
    textos = ler_wikipedia(a.wikipedia, a.documentos)
    sentencas = list(frases(textos))
    print(len(textos), "documentos,", len(sentencas), "frases", flush=True)
    vocab, vetores = treinar(sentencas, a.vocabulario, a.dim, a.janela, a.negativos,
                             a.epocas, a.taxa, a.semente, a.limite_minutos * 60)
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    # Centralizar remove a direção comum a todas as palavras (anisotropia),
    # que inflava similaridades entre palavras sem relação.
    centrados = vetores - vetores.mean(axis=0, keepdims=True)
    normas = centrados / (np.linalg.norm(centrados, axis=1, keepdims=True) + 1e-9)
    np.save(saida / "vetores.npy", normas.astype(np.float16))
    sondas = ["forte", "fortes", "intensos", "chove", "chuva", "morre", "planeta", "estrela",
              "lua", "quente", "gigante", "ano", "jatos", "suga"]
    relatorio = {p: vizinhos(vocab, normas, p) for p in sondas}
    # Pares de controle: equivalentes devem ficar mais próximos que pares aleatórios.
    indice = {p: i for i, p in enumerate(vocab)}
    pares = [("forte", "intenso"), ("fortes", "intensos"), ("grande", "enorme"), ("rapido", "veloz"),
             ("comecar", "iniciar"), ("morrer", "falecer"), ("chuva", "chuvas"), ("terminar", "acabar"),
             ("pequeno", "minusculo"), ("quente", "calor"), ("mostrar", "exibir"), ("antigo", "velho")]
    sims = [float(normas[indice[a]] @ normas[indice[b]]) for a, b in pares if a in indice and b in indice]
    rng_controle = np.random.default_rng(1)
    amostra = rng_controle.integers(0, len(vocab), (2000, 2))
    base = float(np.mean(np.sum(normas[amostra[:, 0]] * normas[amostra[:, 1]], axis=1)))
    controle = {"pares_equivalentes": round(float(np.mean(sims)), 3) if sims else None,
                "pares_avaliados": len(sims), "pares_aleatorios": round(base, 3)}
    (saida / "vocabulario.json").write_text(json.dumps(vocab, ensure_ascii=False), encoding="utf-8")
    (saida / "treino.json").write_text(json.dumps({
        "metodo": "skip-gram com amostragem negativa, NumPy, do zero",
        "fonte": "wikimedia/wikipedia 20231101.pt (ver dados/origem_wikipedia_20261001.json)",
        "licenca_fonte": "CC-BY-SA-3.0/GFDL", "documentos": len(textos), "frases": len(sentencas),
        "vocabulario": len(vocab), "dim": a.dim, "janela": a.janela, "negativos": a.negativos,
        "epocas": a.epocas, "semente": a.semente, "controle": controle, "vizinhos": relatorio}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("controle", controle, flush=True)
    for p_, v in relatorio.items():
        print(p_, v, flush=True)


if __name__ == "__main__":
    main()
