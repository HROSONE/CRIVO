"""Reproduz a cabeça e o calibrador em CPU, sem promover pesos ao chat.

Usa estados finais cacheados dos pesos próprios e das perguntas públicas do
 tutor, identificados por hashes. Não lê testes congelados ou prospectivos.
"""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
sys.path[:0] = [str(RAIZ), str(RAIZ / "scripts"), str(PASTA)]
from apoio_treino import ajustar_cabeca, ajustar_calibrador, sigmoid
from supervisao import examples, cs
from treinar_leitura_ficha import treinar
import politica_desenvolvimento as politica


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    out = args.saida
    if out.exists() and any(out.iterdir()):
        raise SystemExit("Use uma pasta de saída vazia para preservar os resultados anteriores.")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)
    torch.manual_seed(20261008)
    base = RAIZ / "experimentos/pesos_base/leitor_transformer"
    manifest = json.loads((PASTA / "manifesto_cache.json").read_text(encoding="utf-8"))
    checks = [(base / "pesos_numpy.npz", manifest["base_sha256"]),
              (RAIZ / "dados/leitura_ficha_tutor.json", manifest["tutor_sha256"]),
              (PASTA / "cache_desenvolvimento.npz", manifest["cache_sha256"]),
              (PASTA / "tracos_desenvolvimento.json", manifest["tracos_sha256"])]
    checks += [(RAIZ / p, h) for p, h in manifest["fontes"].items()]
    if any(sha(p) != h for p, h in checks):
        raise SystemExit("Cache não corresponde às fontes, pesos, perguntas ou fatos declarados.")
    raw = json.loads((RAIZ / "dados/leitura_ficha_tutor.json").read_text(encoding="utf-8"))["casos"]
    from crivo import Crivo
    comp = Crivo(usar_geracao=False).compositor
    corpus = [dict(c, fatos=[f["texto"] for f in comp.itens[c["assunto"]]["fatos"]]) for c in raw]
    if hashlib.sha256(json.dumps(corpus, sort_keys=True).encode()).hexdigest() != manifest["fatos_sha256"]:
        raise SystemExit("Fichas mudaram; extraia e valide um novo cache antes de treinar.")
    raw_index = {c["pergunta"]: i for i, c in enumerate(raw)}
    with np.load(PASTA / "cache_desenvolvimento.npz", allow_pickle=False) as cache:
        hs = [torch.from_numpy(cache["x" + str(i)].copy()) for i in range(len(raw))]
    with np.load(base / "pesos_numpy.npz", allow_pickle=False) as pesos:
        w0 = pesos["cabeca.weight"][0].copy()
        b0 = float(pesos["cabeca.bias"][0])
    subjects = sorted({c["assunto"] for c in raw})
    random.Random(20261005).shuffle(subjects)
    fold = {s: i % 5 for i, s in enumerate(subjects)}
    records, baselines, selections, final_x, final_y = [], [], [], [], []
    for outer in range(5):
        internal_subjects = [s for s in subjects if fold[s] != outer]
        inner = {s: i % 4 for i, s in enumerate(internal_subjects)}
        ids, pp, bb = [], [], []
        for k in range(4):
            tr = [i for i, c in enumerate(raw) if fold[c["assunto"]] != outer and inner[c["assunto"]] != k]
            w, b = ajustar_cabeca(hs, raw, tr, w0, b0, .1)
            ctr = [i for i, c in enumerate(cs) if fold[c["assunto"]] != outer and inner[c["assunto"]] != k]
            cva = [i for i, c in enumerate(cs) if fold[c["assunto"]] != outer and inner[c["assunto"]] == k]
            weights = treinar([cs[i] for i in ctr])
            for i in cva:
                ids.append(i)
                pp.append(torch.sigmoid(hs[raw_index[cs[i]["pergunta"]]] @ w + b).numpy())
                bb.append(np.array(cs[i]["x"]) @ weights)
        x, y, rows = examples(ids, pp, bb)
        subs = sorted({cs[i]["assunto"] for i, j in rows})
        random.Random(20261008).shuffle(subs)
        subfold = {s: k % 4 for k, s in enumerate(subs)}
        choices = []
        for reg in [.01, .03, .1, .3, 1.]:
            probability = np.zeros(len(y))
            for k in range(4):
                train = np.array([subfold[cs[i]["assunto"]] != k for i, j in rows])
                valid = ~train
                if valid.any():
                    probability[valid] = sigmoid(x[valid] @ ajustar_calibrador(x[train], y[train], reg))
            for threshold in [.5, .55, .6, .65, .7, .75, .8, .85, .9, .95, .98]:
                accepted = probability >= threshold
                good = int(y[accepted].sum())
                bad = int(accepted.sum() - good)
                if good + bad >= 3 and good / (good + bad) >= .9:
                    choices.append((good, -bad, reg, threshold))
        _, _, reg, threshold = max(choices) if choices else (0, 0, .1, 1.1)
        calibrated = ajustar_calibrador(x, y, reg)
        tr = [i for i, c in enumerate(raw) if fold[c["assunto"]] != outer]
        w, b = ajustar_cabeca(hs, raw, tr, w0, b0, .1)
        ctr = [i for i, c in enumerate(cs) if fold[c["assunto"]] != outer]
        valid = [i for i, c in enumerate(cs) if fold[c["assunto"]] == outer]
        weights = treinar([cs[i] for i in ctr])
        vp = [torch.sigmoid(hs[raw_index[cs[i]["pergunta"]]] @ w + b).numpy() for i in valid]
        vb = [np.array(cs[i]["x"]) @ weights for i in valid]
        vx, vy, vrows = examples(valid, vp, vb)
        predictions = sigmoid(vx @ calibrated) if len(vy) else []
        accepted = {i: j for (i, j), p in zip(vrows, predictions) if p >= threshold}
        for i, probs, logits in zip(valid, vp, vb):
            case = cs[i]
            action, j = politica.tradicional(case, logits)
            rescue = i in accepted
            records.append((case, action, j, "aproximar" if rescue else action, accepted.get(i, j), rescue))
            baselines.append((case, action, j, action, j, False))
        selections.append(dict(bloco=outer, regularizacao=reg, limiar=threshold,
                               resgates_certos=int(sum(vy[h] for h, (i, j) in enumerate(vrows) if i in accepted)),
                               resgates_errados=int(sum(1 - vy[h] for h, (i, j) in enumerate(vrows) if i in accepted))))
        final_x.extend(x)
        final_y.extend(y)
        print(json.dumps(selections[-1], ensure_ascii=False), flush=True)
    reg = float(np.median([s["regularizacao"] for s in selections]))
    threshold = float(np.median([s["limiar"] for s in selections]))
    weights = ajustar_calibrador(np.array(final_x), np.array(final_y), reg)
    metadata = json.loads((PASTA / "candidato_campo/meta.json").read_text(encoding="utf-8"))
    metadata.update(pesos=weights.tolist(), regularizacao=reg, limiar=threshold)
    report = dict(baseline=politica.aggregate(baselines), candidato=politica.aggregate(records),
                  selecao=selections, aprovado=False)
    metadata["desenvolvimento"] = report
    metadata["controle"] = {"aprovado": False, "motivo": "Treino não aprova instalação. Requer controle do chat completo."}
    w, b = ajustar_cabeca(hs, raw, list(range(len(raw))), w0, b0, .1)
    np.savez_compressed(out / "cabeca_revisada.npz", **{"cabeca.weight": w.numpy()[None], "cabeca.bias": b.numpy()[None]})
    metadata["fontes"]["cabeca_sha256"] = sha(out / "cabeca_revisada.npz")
    (out / "meta.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "controle_desenvolvimento.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
