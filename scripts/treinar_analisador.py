"""Treina do zero, em NumPy, o etiquetador e o parser do analisador_frases.

Dados: UD Portuguese-Bosque (CC BY-SA 4.0), versão fixada por commit e
conferida por SHA-256 (dados/origem_ud_bosque.json). O conjunto de teste
oficial só é usado na avaliação final; a escolha da melhor época usa o
conjunto de validação (dev).

Uso:
  python scripts/treinar_analisador.py --dados PASTA_COM_CONLLU --saida artefatos/analisador_pt
"""
import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import analisador_frases as af  # noqa: E402

ORIGEM = Path(__file__).resolve().parent.parent / "dados" / "origem_ud_bosque.json"


# ---------------------------------------------------------------------------
# Dados

def ler_conllu(caminho):
    frases, contracoes, inteiras = [], defaultdict(Counter), Counter()
    atual, mwt = [], {}
    for linha in open(caminho, encoding="utf-8"):
        linha = linha.rstrip("\n")
        if not linha:
            if atual:
                frases.append(atual)
            atual, mwt = [], {}
            continue
        if linha.startswith("#"):
            continue
        c = linha.split("\t")
        if "-" in c[0]:
            ini, fim = map(int, c[0].split("-"))
            mwt[ini] = (fim, c[1].lower())
            continue
        if "." in c[0]:
            continue
        idx = int(c[0])
        atual.append({"forma": c[1], "lema": c[2], "classe": c[3], "pai": int(c[6]), "ligacao": c[7]})
        if idx in mwt:
            mwt[idx] = mwt[idx] + (idx,)
        dentro = any(i <= idx <= f for i, (f, *_r) in mwt.items())
        if not dentro:
            inteiras[c[1].lower()] += 1
    if atual:
        frases.append(atual)
    # Contrações: reler para pegar as partes de cada forma composta.
    partes_atual, alvo = [], None
    for linha in open(caminho, encoding="utf-8"):
        c = linha.rstrip("\n").split("\t")
        if len(c) < 2:
            continue
        if "-" in c[0]:
            ini, fim = map(int, c[0].split("-"))
            alvo, partes_atual, faltam = c[1].lower(), [], fim - ini + 1
            continue
        if alvo is not None and c[0].isdigit():
            partes_atual.append(c[1].lower())
            faltam -= 1
            if faltam == 0:
                contracoes[alvo][tuple(partes_atual)] += 1
                alvo = None
    return frases, contracoes, inteiras


def tabela_contracoes(contracoes, inteiras):
    tabela = {}
    for forma, partes in contracoes.items():
        if "-" in forma:
            continue  # clíticos ficam com a regra do hífen
        separada = sum(partes.values())
        if separada >= 2 and separada > inteiras.get(forma, 0):
            tabela[forma] = list(partes.most_common(1)[0][0])
    return tabela


def conferir_origem(pasta):
    origem = json.loads(ORIGEM.read_text(encoding="utf-8"))
    for nome, sha in origem["sha256"].items():
        h = hashlib.sha256((Path(pasta) / nome).read_bytes()).hexdigest()
        if h != sha:
            raise SystemExit("SHA-256 diferente em %s: %s" % (nome, h))
    return origem


# ---------------------------------------------------------------------------
# Rede: embeddings → camada oculta ReLU → cabeças softmax (Adam, dropout)

class Rede:
    def __init__(self, tabelas, n_entrada, oculta, cabecas, rng):
        self.p = dict(tabelas)
        self.p["W1"] = (rng.standard_normal((n_entrada, oculta)) * np.sqrt(2.0 / n_entrada)).astype(np.float32)
        self.p["b1"] = np.zeros(oculta, np.float32)
        for nome, n in cabecas.items():
            self.p["W_" + nome] = (rng.standard_normal((oculta, n)) * np.sqrt(1.0 / oculta)).astype(np.float32)
            self.p["b_" + nome] = np.zeros(n, np.float32)
        self.cabecas = list(cabecas)
        self.m = {k: np.zeros_like(v) for k, v in self.p.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.p.items()}
        self.t = 0

    def entrada(self, grupos):
        """grupos: lista de (tabela, ids[lote, k])."""
        return np.concatenate([self.p[t][ids].reshape(len(ids), -1) for t, ids in grupos], axis=1)

    def passo(self, grupos, alvos, rng, taxa=1e-3, queda=0.3):
        x = self.entrada(grupos)
        z = x @ self.p["W1"] + self.p["b1"]
        h = np.maximum(0, z)
        mascara = (rng.random(h.shape) > queda).astype(np.float32) / (1 - queda)
        hd = h * mascara
        grads = {k: None for k in self.p}
        dh = np.zeros_like(h)
        perda = 0.0
        n = len(x)
        for nome, y in zip(self.cabecas, alvos):
            if y is None:
                continue
            log = hd @ self.p["W_" + nome] + self.p["b_" + nome]
            log -= log.max(1, keepdims=True)
            pr = np.exp(log)
            pr /= pr.sum(1, keepdims=True)
            perda += -np.log(pr[np.arange(n), y] + 1e-9).mean()
            pr[np.arange(n), y] -= 1
            pr /= n
            grads["W_" + nome] = hd.T @ pr
            grads["b_" + nome] = pr.sum(0)
            dh += pr @ self.p["W_" + nome].T
        dz = dh * mascara * (z > 0)
        grads["W1"] = x.T @ dz
        grads["b1"] = dz.sum(0)
        dx = dz @ self.p["W1"].T
        col = 0
        for tabela, ids in grupos:
            largura = ids.shape[1] * self.p[tabela].shape[1]
            g = dx[:, col:col + largura].reshape(-1, self.p[tabela].shape[1])
            if grads[tabela] is None:
                grads[tabela] = np.zeros_like(self.p[tabela])
            np.add.at(grads[tabela], ids.reshape(-1), g)
            col += largura
        self.t += 1
        b1, b2 = 0.9, 0.999
        for k, g in grads.items():
            if g is None:
                continue
            self.m[k] = b1 * self.m[k] + (1 - b1) * g
            self.v[k] = b2 * self.v[k] + (1 - b2) * g * g
            mh = self.m[k] / (1 - b1 ** self.t)
            vh = self.v[k] / (1 - b2 ** self.t)
            self.p[k] -= (taxa * mh / (np.sqrt(vh) + 1e-8)).astype(np.float32)
        return perda


def tabela_palavras(vocab_treino, vetores, dim, rng):
    """Palavras do treino + palavras dos vetores, na mesma ordem que
    af.estender usa na execução. Linhas iniciam no vetor do projeto."""
    palavras, matriz = vetores
    indice = {w: i for i, w in enumerate(palavras)}
    linhas = []
    for w in vocab_treino:
        k = indice.get(w, indice.get(af.sem_acento(w)))
        linhas.append(matriz[k] if (matriz is not None and k is not None and w not in (af.NULO, af.UNK, af.RAIZ))
                      else rng.standard_normal(dim) * 0.1)
    tabela = np.array(linhas, np.float32)
    vocab, tabela = af.estender(vocab_treino, tabela, vetores, np)
    return vocab, tabela


# ---------------------------------------------------------------------------
# Etiquetador

def treinar_etiquetador(treino, dev, vetores, rng, epocas, contr):
    freq = Counter(af.forma_chave(p["forma"]) for f in treino for p in f)
    vocab_treino = [af.NULO, af.UNK] + sorted(freq)
    sufixos = [af.NULO, af.UNK] + sorted({af.sufixo(p["forma"]) for f in treino for p in f})
    formatos = [af.NULO, af.UNK, "num", "pont", "maius", "inicial", "minus"]
    classes = sorted({p["classe"] for f in treino for p in f})
    regras = Counter(af.regra_lema(p["forma"], p["lema"]) for f in treino for p in f)
    regras_lista = [af.UNK] + [r for r, c in regras.most_common() if c >= 2][:800]
    dim = vetores[1].shape[1] if vetores[1] is not None else 64
    vocab, tab_pal = tabela_palavras(vocab_treino, vetores, dim, rng)
    suf_id = {w: i for i, w in enumerate(sufixos)}
    fmt_id = {w: i for i, w in enumerate(formatos)}
    cls_id = {w: i for i, w in enumerate(classes)}
    reg_id = {w: i for i, w in enumerate(regras_lista)}

    def exemplos(frases, abandono=0.0):
        X, Yc, Yl = [], [], []
        for f in frases:
            formas = [p["forma"] for p in f]
            ids = af.ids_etiquetador(formas, vocab, suf_id, fmt_id)
            for linha, p in zip(ids, f):
                if abandono:
                    for k in (0, 3, 6, 9, 12):
                        w = linha[k]
                        if w > 1 and rng.random() < abandono / (abandono + freq.get(vocab_treino[w], 0)
                                                                 if w < len(vocab_treino) else 1):
                            linha[k] = 1
                X.append(linha)
                Yc.append(cls_id[p["classe"]])
                Yl.append(reg_id.get(af.regra_lema(p["forma"], p["lema"]), 0))
        return np.array(X), np.array(Yc), np.array(Yl)

    rede = Rede({"et_pal": tab_pal,
                 "et_suf": (rng.standard_normal((len(sufixos), 32)) * 0.1).astype(np.float32),
                 "et_fmt": (rng.standard_normal((len(formatos), 8)) * 0.1).astype(np.float32)},
                5 * (dim + 32 + 8), 300, {"c": len(classes), "l": len(regras_lista)}, rng)

    def grupos(X):
        return [("et_pal", X[:, 0::3]), ("et_suf", X[:, 1::3]), ("et_fmt", X[:, 2::3])]

    Xd, Ycd, Yld = exemplos(dev)
    melhor, melhor_p = -1, None
    for epoca in range(epocas):
        X, Yc, Yl = exemplos(treino, abandono=0.25)
        ordem = rng.permutation(len(X))
        inicio = time.time()
        perdas = []
        for k in range(0, len(X), 256):
            b = ordem[k:k + 256]
            perdas.append(rede.passo(grupos(X[b]), [Yc[b], Yl[b]], rng, taxa=1e-3))
        acc = avaliar_et(rede, grupos(Xd), Ycd, Yld)
        print("etiquetador época %d perda %.3f dev classe %.4f lema-regra %.4f (%.0fs)"
              % (epoca + 1, np.mean(perdas), acc[0], acc[1], time.time() - inicio), flush=True)
        if acc[0] > melhor:
            melhor, melhor_p = acc[0], {k: v.copy() for k, v in rede.p.items()}
    meta = {"vocab_etiquetador": vocab_treino, "sufixos": sufixos, "formatos": formatos,
            "classes": classes, "regras_lema": regras_lista}
    pesos = {"et_pal": melhor_p["et_pal"][:len(vocab_treino)], "et_suf": melhor_p["et_suf"],
             "et_fmt": melhor_p["et_fmt"], "et_W1": melhor_p["W1"], "et_b1": melhor_p["b1"],
             "et_Wc": melhor_p["W_c"], "et_bc": melhor_p["b_c"], "et_Wl": melhor_p["W_l"],
             "et_bl": melhor_p["b_l"]}
    return meta, pesos


def avaliar_et(rede, grupos, Yc, Yl):
    x = rede.entrada(grupos)
    h = np.maximum(0, x @ rede.p["W1"] + rede.p["b1"])
    pc = (h @ rede.p["W_c"] + rede.p["b_c"]).argmax(1)
    pl = (h @ rede.p["W_l"] + rede.p["b_l"]).argmax(1)
    return (pc == Yc).mean(), (pl == Yl).mean()


def lemas_fixos(treino):
    """Formas frequentes com lema estável por classe (verbos irregulares,
    pronomes): "é"/AUX → "ser", "foi"/AUX → "ser"."""
    cont = defaultdict(Counter)
    for f in treino:
        for p in f:
            cont[p["forma"].lower() + "\t" + p["classe"]][p["lema"]] += 1
    fixos = {}
    for chave, lemas in cont.items():
        lema, n = lemas.most_common(1)[0]
        total = sum(lemas.values())
        if total >= 3 and n / total >= 0.9 and lema != chave.split("\t")[0]:
            fixos[chave] = lema
    return fixos


# ---------------------------------------------------------------------------
# Parser

def oraculo(frase, n_lig_id):
    """Sequência de (características, ação) do arc-standard; None se não
    projetiva (o oráculo não reconstrói a árvore)."""
    n = len(frase)
    pai = [None] + [p["pai"] for p in frase]
    lig = [None] + [n_lig_id[p["ligacao"]] for p in frase]
    faltam = Counter(pai[1:])
    conf = af.Configuracao(n)
    passos = []
    while not conf.terminou():
        acao = None
        if len(conf.pilha) >= 2:
            s0, s1 = conf.pilha[-1], conf.pilha[-2]
            if s1 != 0 and pai[s1] == s0:
                acao = (1, lig[s1])
            elif pai[s0] == s1 and faltam[s0] == 0 and (s1 != 0 or not conf.buffer):
                acao = (2, lig[s0])
        if acao is None:
            if not conf.buffer:
                return None
            acao = (0, 0)
        passos.append((conf, acao))
        estado = (list(conf.pilha), list(conf.buffer), [list(x) for x in conf.filhos_esq],
                  [list(x) for x in conf.filhos_dir], list(conf.lig))
        passos[-1] = (estado, acao)
        if acao[0] == 1:
            faltam[conf.pilha[-1]] -= 1
        elif acao[0] == 2:
            faltam[conf.pilha[-2]] -= 1
        conf.aplicar(acao[0], acao[1])
    if conf.pai[1:] != pai[1:]:
        return None
    return passos


def treinar_parser(treino, dev, vetores, rng, epocas, classes, etiquetar_dev):
    freq = Counter(af.forma_chave(p["forma"]) for f in treino for p in f)
    vocab_treino = [af.NULO, af.UNK, af.RAIZ] + sorted(freq)
    ligacoes = sorted({p["ligacao"] for f in treino for p in f})
    lig_id = {w: i + 3 for i, w in enumerate(ligacoes)}
    cls_id = {w: i + 3 for i, w in enumerate(classes)}
    nl = len(ligacoes)
    dim = vetores[1].shape[1] if vetores[1] is not None else 64
    vocab, tab_pal = tabela_palavras(vocab_treino, vetores, dim, rng)

    W, C, L, Y = [], [], [], []
    nao_proj = 0
    for f in treino:
        passos = oraculo(f, lig_id)
        if passos is None:
            nao_proj += 1
            continue
        pal = [2] + [vocab.get(af.forma_chave(p["forma"]), 1) for p in f]
        cls = [2] + [cls_id[p["classe"]] if rng.random() > 0.05 else int(rng.integers(3, 3 + len(classes)))
                     for p in f]
        for (pilha, buffer, fe, fd, lg), (acao, rotulo) in passos:
            w, c, l = af.ids_parser(pilha, buffer, fe, fd, lg, pal, cls)
            W.append(w)
            C.append(c)
            L.append(l)
            Y.append(0 if acao == 0 else (rotulo - 3 + 1 if acao == 1 else rotulo - 3 + 1 + nl))
    W, C, L, Y = map(np.array, (W, C, L, Y))
    print("parser: %d exemplos, %d frases não projetivas fora do treino" % (len(Y), nao_proj), flush=True)
    freq_id = np.zeros(len(vocab), np.float32)
    for w, c in freq.items():
        freq_id[vocab[w]] = c

    rede = Rede({"pa_pal": tab_pal,
                 "pa_cls": (rng.standard_normal((len(classes) + 3, 32)) * 0.1).astype(np.float32),
                 "pa_lig": (rng.standard_normal((nl + 3, 32)) * 0.1).astype(np.float32)},
                18 * dim + 18 * 32 + 12 * 32, 400, {"t": 1 + 2 * nl}, rng)
    meta = {"vocab_parser": vocab_treino, "ligacoes": ligacoes}
    melhor, melhor_p = -1, None
    for epoca in range(epocas):
        ordem = rng.permutation(len(Y))
        inicio = time.time()
        perdas = []
        for k in range(0, len(Y), 512):
            b = ordem[k:k + 512]
            Wb = W[b].copy()
            # Abandono de palavra: raras viram <unk> às vezes.
            f = freq_id[Wb]
            troca = (Wb > 2) & (rng.random(Wb.shape) < 0.25 / (0.25 + f))
            Wb[troca] = 1
            perdas.append(rede.passo([("pa_pal", Wb), ("pa_cls", C[b]), ("pa_lig", L[b])], [Y[b]], rng))
        pesos = pesos_parser(rede.p, len(vocab_treino))
        uas, las = avaliar_parser(dev, pesos, meta, classes, etiquetar_dev)
        print("parser época %d perda %.3f dev UAS %.4f LAS %.4f (%.0fs)"
              % (epoca + 1, np.mean(perdas), uas, las, time.time() - inicio), flush=True)
        if las > melhor:
            melhor, melhor_p = las, pesos
    return meta, melhor_p


def pesos_parser(p, n_treino):
    return {"pa_pal": p["pa_pal"][:n_treino].copy(), "pa_cls": p["pa_cls"].copy(),
            "pa_lig": p["pa_lig"].copy(), "pa_W1": p["W1"].copy(), "pa_b1": p["b1"].copy(),
            "pa_W2": p["W_t"].copy(), "pa_b2": p["b_t"].copy()}


def avaliar_parser(frases, pesos, meta, classes, etiquetas):
    """UAS/LAS com classes previstas pelo etiquetador (como na execução)."""
    a = af.AnalisadorFrases.__new__(af.AnalisadorFrases)
    a.np = np
    a.p = dict(pesos)
    a.vocab_pa, a.p["pa_pal"] = af.estender(meta["vocab_parser"], pesos["pa_pal"],
                                            af.carregar_vetores(np), np)
    a.cls_id = {w: i for i, w in enumerate(classes)}
    a.ligacoes = meta["ligacoes"]
    certos_u = certos_l = total = 0
    for f, cls in zip(frases, etiquetas):
        pais, ligs = a.ligar([p["forma"] for p in f], cls)
        for p, pai, lig in zip(f, pais, ligs):
            total += 1
            if pai == p["pai"]:
                certos_u += 1
                certos_l += lig == p["ligacao"]
    return certos_u / total, certos_l / total


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--epocas-etiquetador", type=int, default=8)
    ap.add_argument("--epocas-parser", type=int, default=10)
    ap.add_argument("--semente", type=int, default=20261002)
    a = ap.parse_args()
    origem = conferir_origem(a.dados)
    rng = np.random.default_rng(a.semente)
    random.seed(a.semente)
    pasta = Path(a.dados)
    treino, contr, inteiras = ler_conllu(pasta / "pt_bosque-ud-train.conllu")
    dev, _, _ = ler_conllu(pasta / "pt_bosque-ud-dev.conllu")
    teste, _, _ = ler_conllu(pasta / "pt_bosque-ud-test.conllu")
    contracoes = tabela_contracoes(contr, inteiras)
    vetores = af.carregar_vetores(np)
    print("treino %d, dev %d, teste %d frases; %d contrações; vetores %s"
          % (len(treino), len(dev), len(teste), len(contracoes),
             None if vetores[1] is None else vetores[1].shape), flush=True)

    meta_et, pesos_et = treinar_etiquetador(treino, dev, vetores, rng, a.epocas_etiquetador, contracoes)
    meta = dict(meta_et, contracoes=contracoes, lemas_fixos=lemas_fixos(treino))
    # Analisador provisório só com o etiquetador, para dar ao parser as
    # classes previstas do dev (a mesma condição da execução).
    prov = af.AnalisadorFrases.__new__(af.AnalisadorFrases)
    prov.np, prov.p, prov.meta = np, dict(pesos_et), meta
    prov.vocab_et, prov.p["et_pal"] = af.estender(meta["vocab_etiquetador"], pesos_et["et_pal"], vetores, np)
    prov.sufixos = {w: i for i, w in enumerate(meta["sufixos"])}
    prov.formatos = {w: i for i, w in enumerate(meta["formatos"])}
    prov.classes, prov.regras, prov.lemas_fixos = meta["classes"], meta["regras_lema"], meta["lemas_fixos"]

    def etiquetas(frases):
        return [[c for c, _ in prov.etiquetar([p["forma"] for p in f])] for f in frases]

    meta_pa, pesos_pa = treinar_parser(treino, dev, vetores, rng, a.epocas_parser, meta["classes"],
                                       etiquetas(dev))
    meta.update(meta_pa)

    # Avaliação final no teste oficial (tokenização de referência).
    et_teste = [prov.etiquetar([p["forma"] for p in f]) for f in teste]
    total = sum(len(f) for f in teste)
    upos = sum(c == p["classe"] for f, e in zip(teste, et_teste) for p, (c, _) in zip(f, e)) / total
    lema = sum(l.lower() == p["lema"].lower() for f, e in zip(teste, et_teste)
               for p, (_, l) in zip(f, e)) / total
    uas, las = avaliar_parser(teste, pesos_pa, meta, meta["classes"], [[c for c, _ in e] for e in et_teste])
    uas_d, las_d = avaliar_parser(dev, pesos_pa, meta, meta["classes"], etiquetas(dev))
    meta["avaliacao"] = {
        "teste": {"upos": round(upos, 4), "lema": round(lema, 4), "uas": round(uas, 4), "las": round(las, 4),
                  "palavras": total, "frases": len(teste)},
        "dev": {"uas": round(uas_d, 4), "las": round(las_d, 4)},
        "observacao": "Tokenização de referência do treebank; pontuação incluída. Classes previstas "
                      "pelo etiquetador alimentam o parser, como na execução.",
    }
    meta["minimo"] = af.MINIMO
    meta["origem"] = origem
    meta["treino"] = {"semente": a.semente, "epocas_etiquetador": a.epocas_etiquetador,
                      "epocas_parser": a.epocas_parser, "metodo": "MLP de janela + arc-standard "
                      "(Chen & Manning, 2014), NumPy, do zero; palavras iniciadas nos vetores do projeto"}
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    pesos = dict(pesos_et, **pesos_pa)
    np.savez_compressed(saida / "modelo.npz", **{k: v.astype(np.float16) for k, v in pesos.items()})
    (saida / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(meta["avaliacao"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
