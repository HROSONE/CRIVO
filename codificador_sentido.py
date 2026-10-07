"""Codificador de sentido: o Transformer do CRIVO transforma pergunta e fato em
vetores, e perguntas e fatos que dizem a mesma coisa ficam próximos mesmo sem
palavras em comum ("quem fez a tela mais famosa" e "pintou a Mona Lisa").

É o Transformer próprio do projeto (pré-treino do zero, nenhum modelo externo),
partindo do corpo do leitor e treinado de forma contrastiva
(scripts/treinar_codificador_sentido.py): cada pergunta do tutor precisa ficar
mais perto do seu fato do que dos fatos das outras perguntas do lote e de um
fato parecido de outra ficha escolhido pelo BM25 (negativo difícil). Fichas
dos testes congelados ficaram fora do treino.

O vetor é a média dos estados finais do Transformer, normalizada. Os vetores
dos fatos do acervo vêm pré-calculados (vetores_fatos.npz, por hash do texto);
fato novo ou alterado é codificado na hora. Inferência em NumPy, sobre o
executor de pontuador_frases.py. Só é usado se meta.json disser que foi
aprovado no controle; a busca (busca_semantica.py) o soma como um traço.
"""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "artefatos" / "sentido_pt"
CONTEXTO = 96


def chave(texto):
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()[:16]


class CodificadorSentido:
    def __init__(self, pasta=PASTA, exigir_aprovacao=True):
        self.disponivel = False
        self.motivo = ""
        pasta = Path(pasta)
        try:
            self.meta = json.loads((pasta / "meta.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.motivo = "sem meta.json"
            return
        if exigir_aprovacao and not self.meta.get("controle", {}).get("aprovado"):
            self.motivo = "não aprovado no controle"
            return
        from pontuador_frases import Pontuador
        self.modelo = Pontuador(pasta)
        if not self.modelo.disponivel:
            self.motivo = self.modelo.motivo
            return
        self.np = self.modelo.np
        self.peso = float(self.meta.get("controle", {}).get("peso", 2.0))
        self._cache = {}
        try:
            z = self.np.load(pasta / "vetores_fatos.npz")
            for k, v in zip(z["chaves"], z["vetores"].astype(self.np.float32)):
                self._cache[str(k)] = v
        except (OSError, KeyError, ValueError):
            pass
        self.disponivel = True

    def _ids(self, texto, papel):
        e = self.modelo.bpe.especiais
        corpo = self.modelo.bpe.codificar(texto)[:CONTEXTO - 2]
        return [e["<usuario>" if papel == "pergunta" else "<documento>"]] + corpo + [e["<fim>"]]

    def codificar(self, textos, papel, lote=32):
        """Matriz (n, dimensão) de vetores normalizados."""
        np = self.np
        saida = []
        for s in range(0, len(textos), lote):
            seqs = [self._ids(t, papel) for t in textos[s:s + lote]]
            ocultos = self.modelo.ocultos_lote(seqs)
            for i, ids in enumerate(seqs):
                v = ocultos[i, :len(ids)].mean(0)
                saida.append(v / (np.linalg.norm(v) + 1e-8))
        return np.stack(saida) if saida else np.zeros((0, ocultos.shape[-1]), dtype=np.float32)

    def vetores_fatos(self, textos):
        """Vetores dos fatos, pelo cache; os que faltam são codificados agora."""
        faltam = [t for t in dict.fromkeys(textos) if chave(t) not in self._cache]
        if faltam:
            for t, v in zip(faltam, self.codificar(faltam, "fato")):
                self._cache[chave(t)] = v
        return self.np.stack([self._cache[chave(t)] for t in textos])


@lru_cache(maxsize=2)
def codificador(pasta=str(PASTA), exigir_aprovacao=True):
    return CodificadorSentido(pasta, exigir_aprovacao)
