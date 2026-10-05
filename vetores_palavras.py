"""Similaridade entre palavras por vetores skip-gram treinados do zero.

Carregamento opcional: sem NumPy ou sem o arquivo de vetores, nenhuma
palavra é considerada equivalente a outra e o Crivo se comporta como antes.
Os vetores só aproximam UMA palavra de uma pergunta a uma palavra de um
fato já cadastrado; não criam fatos nem respostas.
"""
import json
import unicodedata
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "artefatos" / "vetores_pt"


def _normalizar(palavra):
    palavra = unicodedata.normalize("NFD", palavra.casefold())
    return "".join(c for c in palavra if unicodedata.category(c) != "Mn")


class VetoresPalavras:
    MINIMO_EQUIVALENTES = 0.45
    MARGEM_MINIMA = 0.35
    MARGEM_ANTONIMOS = 0.15

    def __init__(self, pasta=PASTA, exigir_controle=True):
        self.indice = {}
        self.vetores = None
        try:
            import numpy as np
            vocab = json.loads((Path(pasta) / "vocabulario.json").read_text(encoding="utf-8"))
            vetores = np.load(Path(pasta) / "vetores.npy").astype(np.float32)
        except (ImportError, OSError, ValueError):
            return
        if len(vocab) != len(vetores):
            return
        if not exigir_controle:
            self.indice = {p: i for i, p in enumerate(vocab)}
            self.vetores = vetores
            return
        # Controle de qualidade do treino: pares equivalentes precisam ficar
        # claramente mais próximos que pares aleatórios. Sem isso, desligado.
        try:
            controle = json.loads((Path(pasta) / "treino.json").read_text(encoding="utf-8"))["controle"]
            equivalentes, aleatorios = controle["pares_equivalentes"], controle["pares_aleatorios"]
            antonimos = controle["pares_antonimos"]
        except (OSError, ValueError, KeyError, TypeError):
            return
        # Vetores de contexto aproximam antônimos ("quente"/"frio"); aceitar
        # só se os equivalentes ficarem claramente acima dos antônimos.
        if (equivalentes is None or antonimos is None or controle.get("pares_avaliados", 0) < 8
                or equivalentes < self.MINIMO_EQUIVALENTES
                or equivalentes - aleatorios < self.MARGEM_MINIMA
                or equivalentes - antonimos < self.MARGEM_ANTONIMOS):
            return
        self.indice = {p: i for i, p in enumerate(vocab)}
        self.vetores = vetores

    @property
    def disponivel(self):
        return self.vetores is not None

    def similaridade(self, a, b):
        if self.vetores is None:
            return 0.0
        i, j = self.indice.get(_normalizar(a)), self.indice.get(_normalizar(b))
        if i is None or j is None:
            return 0.0
        return float(self.vetores[i] @ self.vetores[j])

    def mais_parecida(self, palavra, candidatas, limiar):
        """Melhor candidata com similaridade >= limiar, ou None."""
        melhor, nota = None, limiar
        for c in candidatas:
            s = self.similaridade(palavra, c)
            if s >= nota:
                melhor, nota = c, s
        return melhor
