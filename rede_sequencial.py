"""Rede autoral de projeção, com atributos ordenados e inferência Python puro.

Pesos aleatórios próprios, tanh e softmax treinados por gradiente. A ordem é
local (bigramas/trigramas e posição), não compreensão irrestrita. NumPy é
opcional somente para acelerar o treino; não carrega pesos/modelos externos.
"""
import hashlib
import difflib
import inspect
import json
import math
import random
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

VERSAO_ATRIBUTOS = "sequencia-local-v2"

# Léxico funcional autoral: flexões e equivalências de operações de linguagem.
# Não contém entidades, respostas ou perguntas do benchmark final.
FLEXOES = {
    "defina": "definicao", "definir": "definicao", "definir-me": "definicao",
    "significa": "significado", "significar": "significado",
    "compreender": "entender", "compreendo": "entender", "entendi": "entender",
    "conhecer": "saber", "esclarecer": "explicar", "esclareca": "explicar",
    "explica": "explicar", "explique": "explicar", "explicacao": "explicar",
    "falar": "fale", "fala": "fale", "conta": "conte", "contar": "conte",
    "age": "funciona", "agir": "funciona", "funcionamento": "funciona",
    "utilidade": "funcao", "diferencia": "diferenca", "diferenciar": "diferenca",
    "compare": "comparacao", "comparar": "comparacao", "iguais": "igual",
    "resuma": "resumo", "resumir": "resumo", "encurte": "curto", "encurtar": "curto",
    "topico": "topicos", "lista": "topicos", "listagem": "topicos",
    "fonte": "fontes", "referencia": "fontes", "referencias": "fontes", "origem": "fontes",
    "reformule": "reformular", "reescreva": "reformular", "reescrever": "reformular",
    "simplifique": "simples", "simplificar": "simples", "facil": "simples",
    "retome": "retomar", "voltar": "retomar", "volte": "retomar",
    "voltasse": "retomar", "voltamos": "retomar",
    "posso": "pode", "podemos": "pode", "podem": "pode", "podes": "pode",
    "poderia": "pode", "poderiamos": "pode",
    "conseguimos": "consegue", "conseguem": "consegue", "conseguiria": "consegue",
    "ainda": "ainda", "gente": "gente",
    "pedir": "pedido", "pedi": "pedido", "solicitei": "pedido", "solicitar": "pedido",
    "queria": "quero", "gostaria": "quero", "quer": "quero", "desejo": "quero",
    "este": "esse", "esta": "essa", "dessa": "essa", "desse": "esse",
    "organizada": "organizado", "organizadas": "organizado", "organizados": "organizado",
    "numa": "em", "num": "em", "anteriores": "anterior",
}


@lru_cache(maxsize=8192)
def _token_estrutura(t, estruturais):
    if t not in estruturais and len(t) >= 5:
        candidatos = difflib.get_close_matches(t, estruturais, n=2, cutoff=.86)
        if len(candidatos) == 1:
            t = candidatos[0]
    return FLEXOES.get(t, t) if t in estruturais else "<argumento>"


def token_estrutura(t, estruturais):
    return _token_estrutura(t, frozenset(estruturais))


def normalizar(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.casefold())
                   if unicodedata.category(c) != "Mn")


def palavras(texto):
    return [(normalizar(m.group()), m.start(), m.end())
            for m in re.finditer(r"[\w+#]+(?:[-_][\w+#]+)*", texto, re.UNICODE)]


@lru_cache(maxsize=8192)
def hash_atributo(s):
    h = 2166136261
    for c in s:
        h = ((h ^ ord(c)) * 16777619) & 0xffffffff
    return h


def _vetor(atributos, dimensao):
    if dimensao < 12:
        raise ValueError("Dimensão insuficiente")
    valores = {}
    bloco = dimensao // 3
    for nome, valor, grupo in atributos:
        i = grupo * bloco + hash_atributo(nome) % bloco
        valores.setdefault(i, []).append(valor)
    v = {i: math.fsum(vs) for i, vs in valores.items()}
    norma = math.sqrt(math.fsum(x*x for x in v.values())) or 1.0
    return {i: x / norma for i, x in v.items()}


def atributos_frase(texto, dimensao=768, ordem=True, estruturais=None):
    ts = [t for t, _, _ in palavras(texto)][:96]
    if estruturais is not None:
        ts = [token_estrutura(t, estruturais) for t in ts]
    atributos = []
    for t in ts:
        atributos.append(("w:" + t, 1.0, 0))
        for n in (2, 3, 4):
            marcada = "^" + t + "$"
            atributos.extend(("c:" + marcada[i:i+n], .35, 0)
                              for i in range(len(marcada) - n + 1))
    if ordem:
        for n in (2, 3):
            atributos.extend(("o%d:" % n + "|".join(ts[i:i+n]), .35, n - 1)
                              for i in range(len(ts) - n + 1))
        atributos += [("inicio:" + t, .2, 1) for t in ts[:3]]
        atributos += [("fim:" + t, .2, 2) for t in ts[-3:]]
    return _vetor(atributos, dimensao)


def atributos_token(ts, indice, dimensao=768):
    atual = ts[indice]
    atributos = []
    for deslocamento in range(-3, 4):
        k = indice + deslocamento
        t = ts[k] if 0 <= k < len(ts) else "<inicio>" if k < 0 else "<fim>"
        atributos.append(("janela:%d:" % deslocamento + t, 1.3 if deslocamento else .6, 1))
    for n in (2, 3, 4):
        marcada = "^" + atual + "$"
        atributos.extend(("letra:" + marcada[i:i+n], .25, 0)
                          for i in range(len(marcada) - n + 1))
    atributos += [("prefixo:" + t, .5, 2) for t in ts[:3]]
    atributos += [("sufixo:" + t, .5, 2) for t in ts[-3:]]
    atributos += [("pos:%d" % min(indice, 6), .6, 2),
                  ("resto:%d" % min(len(ts) - indice - 1, 6), .6, 2)]
    return _vetor(atributos, dimensao)


def softmax(logits, temperatura=1.0):
    if not math.isfinite(temperatura) or temperatura <= 0:
        raise ValueError("Temperatura inválida")
    pico = max(logits)
    valores = [math.exp((v-pico) / temperatura) for v in logits]
    total = sum(valores)
    return [v/total for v in valores]


class RedeSequencial:
    def __init__(self, rotulos, dimensao=768, ocultos=32, semente=42):
        if (not rotulos or len(rotulos) > 1024 or len(rotulos) != len(set(rotulos)) or
                not 12 <= dimensao <= 4096 or not 1 <= ocultos <= 128):
            raise ValueError("Rede inválida")
        self.rotulos, self.dimensao, self.ocultos = list(rotulos), dimensao, ocultos
        rng = random.Random(semente)
        self.w1 = [[rng.uniform(-.15, .15) for _ in range(dimensao)] for _ in range(ocultos)]
        self.b1 = [0.0] * ocultos
        self.w2 = [[rng.uniform(-.15, .15) for _ in range(ocultos)] for _ in rotulos]
        self.b2 = [0.0] * len(rotulos)
        self.temperatura = 1.0

    def projetar(self, x):
        return [math.tanh(sum(linha[i]*v for i, v in x.items()) + b)
                for linha, b in zip(self.w1, self.b1)]

    def logits(self, x):
        h = self.projetar(x)
        return [sum(w*v for w, v in zip(linha, h)) + b
                for linha, b in zip(self.w2, self.b2)]

    def prever(self, x):
        ps = softmax(self.logits(x), self.temperatura)
        indices = sorted(range(len(ps)), key=lambda k: ps[k], reverse=True)
        primeiro = indices[0]
        margem = ps[primeiro] - (ps[indices[1]] if len(indices) > 1 else 0)
        return self.rotulos[primeiro], ps[primeiro], margem

    def treinar(self, exemplos, epocas=60, taxa=.012, semente=42, acelerar=False):
        if not exemplos or epocas < 1 or not 0 < taxa <= 1:
            raise ValueError("Treino inválido")
        if acelerar:
            return self._treinar_numpy(exemplos, epocas, taxa, semente)
        dados = [(x, self.rotulos.index(r)) for x, r in exemplos]
        rng = random.Random(semente)
        for _ in range(epocas):
            rng.shuffle(dados)
            for x, y in dados:
                h = self.projetar(x)
                ps = softmax([sum(w*v for w, v in zip(linha, h)) + b
                              for linha, b in zip(self.w2, self.b2)])
                ps[y] -= 1
                dh = [(1-h[j]*h[j])*sum(ps[k]*self.w2[k][j]
                        for k in range(len(ps))) for j in range(self.ocultos)]
                for k, d in enumerate(ps):
                    for j, v in enumerate(h):
                        self.w2[k][j] -= taxa*d*v
                    self.b2[k] -= taxa*d
                for j, d in enumerate(dh):
                    for i, v in x.items():
                        self.w1[j][i] -= taxa*d*v
                    self.b1[j] -= taxa*d
        return self

    def _treinar_numpy(self, exemplos, epocas, taxa, semente):
        import numpy as np
        rng = np.random.default_rng(semente)
        x = np.zeros((len(exemplos), self.dimensao), dtype=np.float64)
        y = np.array([self.rotulos.index(r) for _, r in exemplos])
        for k, (linha, _) in enumerate(exemplos):
            for i, v in linha.items():
                x[k, i] = v
        pesos = [np.array(self.w1), np.array(self.b1), np.array(self.w2), np.array(self.b2)]
        m, v = [np.zeros_like(p) for p in pesos], [np.zeros_like(p) for p in pesos]
        frequencias = np.bincount(y, minlength=len(self.rotulos))
        classes = np.sqrt(len(y) / (len(self.rotulos)*np.maximum(frequencias, 1)))
        passo = 0
        for _ in range(epocas):
            indices = rng.permutation(len(y))
            for a in range(0, len(y), 128):
                ids = indices[a:a+128]
                xx, yy = x[ids], y[ids]
                h = np.tanh(xx @ pesos[0].T + pesos[1])
                logits = h @ pesos[2].T + pesos[3]
                z = np.exp(logits - logits.max(axis=1, keepdims=True))
                dz = z / z.sum(axis=1, keepdims=True)
                dz[np.arange(len(ids)), yy] -= 1
                dz *= classes[yy, None] / len(ids)
                dh = (dz @ pesos[2]) * (1 - h*h)
                grads = [dh.T @ xx + 1e-5*pesos[0], dh.sum(axis=0),
                         dz.T @ h + 1e-5*pesos[2], dz.sum(axis=0)]
                passo += 1
                for k, g in enumerate(grads):
                    m[k] = .9*m[k] + .1*g
                    v[k] = .999*v[k] + .001*g*g
                    pesos[k] -= taxa * (m[k]/(1-.9**passo)) / (np.sqrt(v[k]/(1-.999**passo))+1e-8)
        self.w1, self.b1, self.w2, self.b2 = [p.tolist() for p in pesos]
        return self

    def dados(self):
        return {k: getattr(self, k) for k in ("rotulos", "dimensao", "ocultos", "w1", "b1", "w2", "b2", "temperatura")}

    @classmethod
    def de_dados(cls, dados):
        r = cls(dados["rotulos"], dados["dimensao"], dados["ocultos"])
        for nome, forma in (("w1", (r.ocultos, r.dimensao)), ("w2", (len(r.rotulos), r.ocultos))):
            linhas = dados[nome]
            if len(linhas) != forma[0] or any(len(l) != forma[1] or
                    any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in l) for l in linhas):
                raise ValueError("Matriz neural inválida")
            setattr(r, nome, linhas)
        for nome, tamanho in (("b1", r.ocultos), ("b2", len(r.rotulos))):
            if len(dados[nome]) != tamanho or any(not math.isfinite(v) for v in dados[nome]):
                raise ValueError("Vetor neural inválido")
            setattr(r, nome, dados[nome])
        r.temperatura = dados.get("temperatura", 1.0)
        softmax([0, 1], r.temperatura)
        return r


def assinatura(dados):
    return hashlib.sha256(json.dumps(dados, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def assinatura_atributos():
    return assinatura({"versao": VERSAO_ATRIBUTOS, "flexoes": FLEXOES,
        "codigo": [inspect.getsource(f) for f in (normalizar, palavras, hash_atributo,
                   _token_estrutura, token_estrutura, _vetor, atributos_frase, atributos_token)]})
