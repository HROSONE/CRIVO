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
        self._puro = None
        if not exigir_controle:
            # Traço fraco da leitura da ficha: precisa dar o mesmo resultado
            # com ou sem NumPy (o CI de testes roda em Python puro).
            self._carregar_sem_controle(Path(pasta))
            return
        try:
            import numpy as np
            vocab = json.loads((Path(pasta) / "vocabulario.json").read_text(encoding="utf-8"))
            vetores = np.load(Path(pasta) / "vetores.npy").astype(np.float32)
        except (ImportError, OSError, ValueError):
            return
        if len(vocab) != len(vetores):
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

    def _carregar_sem_controle(self, pasta):
        """Vetores em precisão dupla, por NumPy ou, sem ele, lendo o .npy
        (float16) com struct; os dois caminhos dão a mesma similaridade."""
        try:
            vocab = json.loads((pasta / "vocabulario.json").read_text(encoding="utf-8"))
            bruto = (pasta / "vetores.npy").read_bytes()
        except (OSError, ValueError):
            return
        try:
            import numpy as np
            vetores = np.load(pasta / "vetores.npy").astype(np.float64)
            if len(vetores) == len(vocab):
                self.indice = {p: i for i, p in enumerate(vocab)}
                self.vetores = vetores
            return
        except ImportError:
            pass
        import ast
        import struct
        from array import array
        if bruto[:6] != b"\x93NUMPY":
            return
        tamanho = struct.unpack("<H", bruto[8:10])[0] if bruto[6] == 1 else struct.unpack("<I", bruto[8:12])[0]
        inicio = (10 if bruto[6] == 1 else 12) + tamanho
        cabecalho = ast.literal_eval(bruto[(10 if bruto[6] == 1 else 12):inicio].decode("latin1"))
        linhas, dim = cabecalho["shape"]
        if cabecalho["descr"] != "<f2" or cabecalho["fortran_order"] or linhas != len(vocab):
            return
        self._puro = (array("d", struct.unpack("<%de" % (linhas * dim), bruto[inicio:inicio + 2 * linhas * dim])), dim)
        self.indice = {p: i for i, p in enumerate(vocab)}

    @property
    def disponivel(self):
        return self.vetores is not None or self._puro is not None

    def similaridade(self, a, b):
        if not self.disponivel:
            return 0.0
        i, j = self.indice.get(_normalizar(a)), self.indice.get(_normalizar(b))
        if i is None or j is None:
            return 0.0
        if self._puro is not None:
            dados, d = self._puro
            return float(sum(x * y for x, y in zip(dados[i * d:(i + 1) * d], dados[j * d:(j + 1) * d])))
        return float(self.vetores[i] @ self.vetores[j])

    def mais_parecida(self, palavra, candidatas, limiar):
        """Melhor candidata com similaridade >= limiar, ou None."""
        melhor, nota = None, limiar
        for c in candidatas:
            s = self.similaridade(palavra, c)
            if s >= nota:
                melhor, nota = c, s
        return melhor
