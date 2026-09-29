"""Rede neural original do Crivo: MLP com treinamento supervisionado, sem modelos externos.

Aprende a classificar intenções a partir de exemplos rotulados; não gera texto.
"""
import json
import math
import random
import re
import unicodedata
from pathlib import Path


def caracteristicas(texto, dimensao=256, modo="caracteres"):
    """N-gramas de caracteres com hash determinístico (FNV-1a)."""
    s = "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                if unicodedata.category(c) != "Mn")
    s = " ".join(re.findall(r"[a-z0-9]+", s))
    vetor = [0.0] * dimensao
    if modo not in ("caracteres", "palavras", "misto"):
        raise ValueError("Modo de caracteristicas invalido")
    for palavra in s.split():
        unidades = []
        if modo in ("palavras", "misto"):
            unidades.append("w:" + palavra)
        if modo in ("caracteres", "misto"):
            marcada = "^" + palavra + "$"
            for n in (2, 3, 4):
                unidades.extend("c:" + marcada[i:i+n] for i in range(len(marcada) - n + 1))
        for unidade in unidades:
            h = 2166136261
            for c in unidade:
                h = ((h ^ ord(c)) * 16777619) & 0xffffffff
            vetor[h % dimensao] += 1.0
    norma = math.sqrt(sum(v*v for v in vetor)) or 1.0
    return [v / norma for v in vetor]


class RedeCrivo:
    """Rede com camada oculta tanh e saída softmax, treinada por backpropagation."""

    def __init__(self, rotulos, dimensao=256, ocultos=24, semente=42, modo="caracteres"):
        if not rotulos or len(set(rotulos)) != len(rotulos):
            raise ValueError("Rotulos devem ser unicos e nao vazios")
        self.rotulos = list(rotulos)
        self.dimensao = dimensao
        self.ocultos = ocultos
        self.modo = modo
        rng = random.Random(semente)
        self.w1 = [[rng.uniform(-0.08, 0.08) for _ in range(dimensao)]
                   for _ in range(ocultos)]
        self.b1 = [0.0] * ocultos
        self.w2 = [[rng.uniform(-0.08, 0.08) for _ in range(ocultos)]
                   for _ in rotulos]
        self.b2 = [0.0] * len(rotulos)

    def _forward(self, x):
        h = [math.tanh(sum(w*v for w, v in zip(linha, x)) + b)
             for linha, b in zip(self.w1, self.b1)]
        logits = [sum(w*v for w, v in zip(linha, h)) + b
                  for linha, b in zip(self.w2, self.b2)]
        pico = max(logits)
        exps = [math.exp(v - pico) for v in logits]
        total = sum(exps)
        return h, [v / total for v in exps]

    def treinar(self, exemplos, epocas=100, taxa=0.15, semente=42):
        """Exemplos: pares (pergunta, id). Atualiza pesos por gradiente."""
        dados = [(caracteristicas(pergunta, self.dimensao, self.modo),
                  self.rotulos.index(rotulo)) for pergunta, rotulo in exemplos]
        if not dados:
            raise ValueError("Sem exemplos de treinamento")
        rng = random.Random(semente)
        for _ in range(epocas):
            rng.shuffle(dados)
            for x, alvo in dados:
                h, probabilidades = self._forward(x)
                delta2 = list(probabilidades)
                delta2[alvo] -= 1.0
                delta1 = [(1 - h[j]*h[j]) *
                          sum(delta2[k]*self.w2[k][j]
                              for k in range(len(self.rotulos)))
                          for j in range(self.ocultos)]
                for k, delta in enumerate(delta2):
                    for j in range(self.ocultos):
                        self.w2[k][j] -= taxa * delta * h[j]
                    self.b2[k] -= taxa * delta
                for j, delta in enumerate(delta1):
                    for i, v in enumerate(x):
                        if v:
                            self.w1[j][i] -= taxa * delta * v
                    self.b1[j] -= taxa * delta

    def prever(self, texto):
        _, probabilidades = self._forward(caracteristicas(texto, self.dimensao, self.modo))
        indice = max(range(len(probabilidades)), key=probabilidades.__getitem__)
        return self.rotulos[indice], probabilidades[indice]

    def salvar(self, caminho):
        conteudo = dict(rotulos=self.rotulos, dimensao=self.dimensao,
                        ocultos=self.ocultos, modo=self.modo, w1=self.w1, b1=self.b1,
                        w2=self.w2, b2=self.b2)
        Path(caminho).write_text(json.dumps(conteudo), encoding="utf-8")

    @classmethod
    def carregar(cls, caminho):
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
        rede = cls(dados["rotulos"], dados["dimensao"], dados["ocultos"],
                   modo=dados.get("modo", "caracteres"))
        for nome in ("w1", "b1", "w2", "b2"):
            setattr(rede, nome, dados[nome])
        return rede


def treinar_base(caminho="conhecimento.json", destino="rede_crivo.json", epocas=100):
    base = json.loads(Path(caminho).read_text(encoding="utf-8"))
    rede = RedeCrivo([item["id"] for item in base])
    rede.treinar([(q, item["id"]) for item in base for q in item["perguntas"]],
                 epocas=epocas)
    rede.salvar(destino)
    return rede


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=str(Path(__file__).with_name("conhecimento.json")))
    parser.add_argument("--saida", default="rede_crivo.json")
    parser.add_argument("--epocas", type=int, default=100)
    args = parser.parse_args()
    treinar_base(args.base, args.saida, args.epocas)
    print("Rede treinada e salva em", args.saida)
