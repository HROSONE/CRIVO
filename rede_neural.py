"""Rede neural original do Crivo: MLP com treinamento supervisionado, sem modelos externos.

Aprende a classificar intenções a partir de exemplos rotulados; não gera texto.
"""
import hashlib
import inspect
import json
import math
import random
import re
import unicodedata
from pathlib import Path


def assinatura_base(base):
    """Identifica as perguntas/rotulos exatos que produziram os pesos."""
    entradas = [(e["id"], e["perguntas"]) for e in base]
    payload = json.dumps(entradas, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def assinatura_regras(modo):
    """Detecta mudancas na normalizacao portuguesa que invalidam os pesos."""
    if modo not in ("portugues", "portugues_sem_filtro"):
        return None
    from crivo import SINONIMOS, radical
    payload = json.dumps(SINONIMOS, sort_keys=True,
                         ensure_ascii=False).encode("utf-8")
    payload += inspect.getsource(radical).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def caracteristicas(texto, dimensao=256, modo="caracteres"):
    """N-gramas de caracteres com hash determinístico (FNV-1a)."""
    s = "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                if unicodedata.category(c) != "Mn")
    s = " ".join(re.findall(r"[a-z0-9]+", s))
    vetor = [0.0] * dimensao
    if modo not in ("caracteres", "palavras", "misto", "portugues", "portugues_sem_filtro"):
        raise ValueError("Modo de caracteristicas invalido")
    palavras = s.split()
    if modo in ("portugues", "portugues_sem_filtro"):
        # Reutiliza apenas regras de portugues escritas para o proprio Crivo:
        # nao consulta respostas, rotulos de treinamento ou modelos externos.
        from crivo import SINONIMOS, radical
        ligacoes = {"a", "o", "as", "os", "um", "uma", "uns", "umas",
                    "de", "do", "da", "dos", "das", "em", "no", "na",
                    "nos", "nas", "ao", "aos", "e"}
        palavras = [SINONIMOS.get(radical(p), radical(p)) for p in palavras
                    if modo == "portugues_sem_filtro" or p not in ligacoes]
    for palavra in palavras:
        unidades = []
        if modo in ("palavras", "misto", "portugues", "portugues_sem_filtro"):
            unidades.append("w:" + palavra)
        if modo in ("caracteres", "misto", "portugues", "portugues_sem_filtro"):
            marcada = "^" + palavra + "$"
            for n in (2, 3, 4):
                unidades.extend(marcada[i:i+n] for i in range(len(marcada) - n + 1))
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
        self.assinatura_base = None
        self.assinatura_regras = None
        rng = random.Random(semente)
        self.w1 = [[rng.uniform(-0.08, 0.08) for _ in range(dimensao)]
                   for _ in range(ocultos)]
        self.b1 = [0.0] * ocultos
        self.w2 = [[rng.uniform(-0.08, 0.08) for _ in range(ocultos)]
                   for _ in rotulos]
        self.b2 = [0.0] * len(rotulos)

    def _forward(self, x):
        ativos = [(i, v) for i, v in enumerate(x) if v]
        h = [math.tanh(sum(linha[i]*v for i, v in ativos) + b)
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
                ativos = [(i, v) for i, v in enumerate(x) if v]
                for j, delta in enumerate(delta1):
                    for i, v in ativos:
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
        if self.assinatura_base is not None:
            conteudo["assinatura_base"] = self.assinatura_base
        if self.assinatura_regras is not None:
            conteudo["assinatura_regras"] = self.assinatura_regras
        Path(caminho).write_text(json.dumps(conteudo), encoding="utf-8")

    @classmethod
    def carregar(cls, caminho):
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
        rede = cls(dados["rotulos"], dados["dimensao"], dados["ocultos"],
                   modo=dados.get("modo", "caracteres"))
        for nome in ("w1", "b1", "w2", "b2"):
            setattr(rede, nome, dados[nome])
        rede.assinatura_base = dados.get("assinatura_base")
        rede.assinatura_regras = dados.get("assinatura_regras")
        return rede


def treinar_base(caminho="conhecimento.json", destino="rede_crivo.json",
                epocas=100, ocultos=24, dimensao=256, modo="caracteres",
                taxa=0.15, semente=42):
    """Treina todos os exemplos da base e salva um modelo pronto para carregar.

    Os benchmarks deixam perguntas fora do treino; este metodo de PRODUCAO
    usa todas as perguntas, apos a configuracao ser escolhida no benchmark.
    """
    if epocas < 1 or ocultos < 1 or dimensao < 1 or not 0 < taxa <= 1:
        raise ValueError("Hiperparametros de treinamento invalidos")
    base = json.loads(Path(caminho).read_text(encoding="utf-8"))
    rede = RedeCrivo([item["id"] for item in base], dimensao=dimensao,
                     ocultos=ocultos, modo=modo, semente=semente)
    rede.treinar([(q, item["id"]) for item in base for q in item["perguntas"]],
                 epocas=epocas, taxa=taxa, semente=semente)
    rede.assinatura_base = assinatura_base(base)
    rede.assinatura_regras = assinatura_regras(modo)
    rede.salvar(destino)
    return rede


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=str(Path(__file__).with_name("conhecimento.json")))
    parser.add_argument("--saida", default="rede_crivo.json")
    parser.add_argument("--epocas", type=int, default=100)
    parser.add_argument("--ocultos", type=int, default=24)
    parser.add_argument("--dimensao", type=int, default=256)
    parser.add_argument("--modo", choices=("caracteres", "palavras", "misto",
                        "portugues", "portugues_sem_filtro"), default="caracteres")
    parser.add_argument("--taxa", type=float, default=0.15)
    parser.add_argument("--semente", type=int, default=42)
    args = parser.parse_args()
    rede = treinar_base(args.base, args.saida, args.epocas, args.ocultos,
                        args.dimensao, args.modo, args.taxa, args.semente)
    print("Rede original treinada e salva em", args.saida,
          "| intenções:", len(rede.rotulos), "| modo:", rede.modo,
          "| dimensões:", rede.dimensao, "| neurônios ocultos:", rede.ocultos)
