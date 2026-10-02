"""Pontuador neural de frases: o transformer causal do projeto
(artefatos/linguagem_profunda), executado em NumPy, diz qual de várias
formas de dizer a mesma coisa soa mais natural como resposta.

Ele não escreve conteúdo: só ordena candidatas que o gerador já montou e o
verificador já aprovou. Sem NumPy ou sem pesos, fica desligado e o gerador
usa a primeira candidata válida.

Pesos: scripts/exportar_pontuador.py converte pesos.pt → pesos_numpy.npz.
Tokenização: BPE em bytes (mesmo algoritmo do tokenizer.json, sem a
biblioteca tokenizers).
"""
import json
import math
import re
from functools import lru_cache
from pathlib import Path

_ARTEFATOS = Path(__file__).resolve().parent / "artefatos"
# Pontuador treinado para isso (notebooks/treinar_pontuador_colab.ipynb), se
# já foi aprovado e publicado; senão, o transformer de linguagem do projeto.
PASTA = (_ARTEFATOS / "pontuador_pt" if (_ARTEFATOS / "pontuador_pt" / "pesos_numpy.npz").exists()
         else _ARTEFATOS / "linguagem_profunda")

# Pré-tokenização do BPE em bytes (padrão GPT-2), com letras = [^\W\d_].
_PRE = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[^\W\d_]+| ?\d+| ?[^\s\w]+|\s+(?!\S)|\s+|_+""")


def _bytes_unicode():
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + \
        list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return dict(zip(bs, map(chr, cs)))


class BPE:
    def __init__(self, caminho):
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
        modelo = dados["model"]
        self.vocab = modelo["vocab"]
        self.ranks = {tuple(m) if isinstance(m, list) else tuple(m.split(" ")): i
                      for i, m in enumerate(modelo["merges"])}
        self.especiais = {t["content"]: t["id"] for t in dados.get("added_tokens", [])}
        self.bytes = _bytes_unicode()
        self._cache = {}

    def _palavra(self, simbolos):
        partes = list(simbolos)
        while len(partes) > 1:
            pares = [(self.ranks.get((a, b), math.inf), i) for i, (a, b) in enumerate(zip(partes, partes[1:]))]
            rank, i = min(pares)
            if rank == math.inf:
                break
            par = (partes[i], partes[i + 1])
            novas, j = [], 0
            while j < len(partes):
                if j < len(partes) - 1 and (partes[j], partes[j + 1]) == par:
                    novas.append(partes[j] + partes[j + 1])
                    j += 2
                else:
                    novas.append(partes[j])
                    j += 1
            partes = novas
        return partes

    def codificar(self, texto):
        ids = []
        for pedaco in _PRE.findall(texto):
            if pedaco not in self._cache:
                simbolos = "".join(self.bytes[b] for b in pedaco.encode("utf-8"))
                self._cache[pedaco] = [self.vocab[p] for p in self._palavra(simbolos) if p in self.vocab]
            ids.extend(self._cache[pedaco])
        return ids


def _erf(x, np):
    # Abramowitz & Stegun 7.1.26 (erro < 1,5e-7): GELU exata sem SciPy.
    s = np.sign(x)
    a = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * a)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t
               + 0.254829592) * t * np.exp(-a * a)
    return s * y


class Pontuador:
    def __init__(self, pasta=PASTA):
        self.disponivel = False
        self.motivo = ""
        try:
            import numpy as np
        except ImportError:
            self.motivo = "NumPy ausente"
            return
        pasta = Path(pasta)
        try:
            pesos = np.load(pasta / "pesos_numpy.npz")
            self.meta = json.loads(str(pesos["meta"]))
            self.bpe = BPE(pasta / "tokenizer.json")
        except (OSError, KeyError, ValueError) as exc:
            self.motivo = "pesos ausentes (%s)" % type(exc).__name__
            return
        self.np = np
        self.p = {k: pesos[k].astype(np.float32) for k in pesos.files if k != "meta"}
        self.camadas = self.meta["camadas"]
        self.cabecas = self.meta["cabecas"]
        self.contexto = self.meta["contexto"]
        self.disponivel = True

    def _norm(self, x, nome):
        np = self.np
        m = x.mean(-1, keepdims=True)
        v = ((x - m) ** 2).mean(-1, keepdims=True)
        return (x - m) / np.sqrt(v + 1e-5) * self.p[nome + ".weight"] + self.p[nome + ".bias"]

    def logits(self, ids):
        return self.logits_lote([ids])[0][:len(ids)]

    def logits_lote(self, lote):
        """Várias sequências de uma vez, completadas à direita: com atenção
        causal, o enchimento no fim não altera as posições anteriores."""
        np, p = self.np, self.p
        t = max(len(ids) for ids in lote)
        matriz = np.zeros((len(lote), t), dtype=np.int64)
        for i, ids in enumerate(lote):
            matriz[i, :len(ids)] = ids
        x = p["embedding.weight"][matriz] + p["posicao.weight"][:t]
        b_, h = len(lote), self.cabecas
        d = x.shape[-1] // h
        mascara = np.triu(np.full((t, t), -np.inf, dtype=np.float32), 1)
        for c in range(self.camadas):
            b = "blocos.%d." % c
            q, k, v = np.split(self._norm(x, b + "norm1") @ p[b + "qkv.weight"].T, 3, axis=-1)
            q, k, v = [a.reshape(b_, t, h, d).transpose(0, 2, 1, 3) for a in (q, k, v)]
            s = q @ k.transpose(0, 1, 3, 2) / math.sqrt(d) + mascara
            s = np.exp(s - s.max(-1, keepdims=True))
            s /= s.sum(-1, keepdims=True)
            a = (s @ v).transpose(0, 2, 1, 3).reshape(b_, t, h * d)
            x = x + a @ p[b + "projecao.weight"].T
            m = self._norm(x, b + "norm2") @ p[b + "mlp.0.weight"].T + p[b + "mlp.0.bias"]
            m = 0.5 * m * (1.0 + _erf(m / math.sqrt(2.0), np))
            x = x + m @ p[b + "mlp.2.weight"].T + p[b + "mlp.2.bias"]
        return self._norm(x, "norm") @ p["embedding.weight"].T

    def prefixo(self, mensagem):
        e = self.bpe.especiais
        return [e["<usuario>"]] + self.bpe.codificar(mensagem) + [e["<fim>"], e["<assistente>"]]

    def pontuar(self, mensagem, resposta):
        """Log-probabilidade média por token da resposta, dada a fala."""
        return self.pontuar_varias(mensagem, [resposta])[0]

    def pontuar_varias(self, mensagem, respostas):
        np = self.np
        pre = self.prefixo(mensagem)
        fim = self.bpe.especiais["<fim>"]
        seqs, alvos = [], []
        for r in respostas:
            alvo = self.bpe.codificar(r) + [fim]
            ids = (pre + alvo)[-self.contexto:]
            seqs.append(ids)
            alvos.append(min(len(alvo), len(ids) - 1))
        lg = self.logits_lote([ids[:-1] for ids in seqs])
        notas = []
        for i, (ids, n) in enumerate(zip(seqs, alvos)):
            t = len(ids) - 1
            x = lg[i, t - n:t]
            x = x - x.max(-1, keepdims=True)
            lp = x - np.log(np.exp(x).sum(-1, keepdims=True))
            notas.append(float(lp[np.arange(n), ids[-n:]].mean()))
        return notas


@lru_cache(maxsize=1)
def pontuador():
    return Pontuador()
