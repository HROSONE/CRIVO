"""Leitor Transformer: diz se um fato da ficha responde a uma pergunta.

É o Transformer próprio do CRIVO (pesos treinados do zero, nenhum modelo
externo) no papel de leitor, não de gerador. A sequência

    <documento> fato <usuario> pergunta <fim>

passa pelo Transformer causal; o estado final da última posição, que já viu o
fato e a pergunta inteiros, vai para uma camada linear que dá a probabilidade
de o fato responder à pergunta. O ponto de partida é o pré-treino em português
(scripts/treinar_leitor_transformer.py --base), para que paráfrases como "o
quadro mais famoso" e "pintou Abaporu" fiquem próximas.

Inferência em NumPy (sem PyTorch no site), sobre o mesmo executor de
pontuador_frases.py. Só é usado se meta.json disser que foi aprovado: ele
entra como um traço a mais da leitura da ficha (leitura_ficha.py), e a
aprovação exige melhorar o teste congelado avaliacoes/leitura_ficha_v2.
"""
import json
import math
from functools import lru_cache
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "artefatos" / "leitor_transformer"


def sequencia(bpe, contexto, pergunta, fato):
    """Ids de <documento> fato <usuario> pergunta <fim>, cortando o fato se
    preciso (a pergunta nunca é cortada)."""
    e = bpe.especiais
    q = bpe.codificar(pergunta)[:contexto // 3]
    f = bpe.codificar(fato)
    cabe = contexto - len(q) - 3
    return [e["<documento>"]] + f[:cabe] + [e["<usuario>"]] + q + [e["<fim>"]]


class LeitorTransformer:
    def __init__(self, pasta=PASTA, exigir_aprovacao=True):
        self.disponivel = False
        self.motivo = ""
        pasta = Path(pasta)
        try:
            meta = json.loads((pasta / "meta.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.motivo = "sem meta.json"
            return
        if exigir_aprovacao and not meta.get("controle", {}).get("aprovado"):
            self.motivo = "não aprovado no controle"
            return
        from pontuador_frases import Pontuador
        self.modelo = Pontuador(pasta)
        if not self.modelo.disponivel:
            self.motivo = self.modelo.motivo
            return
        self.meta = meta
        self.disponivel = True

    def probabilidades(self, pergunta, fatos):
        """Probabilidade de cada fato responder à pergunta."""
        if not self.disponivel or not fatos:
            return [0.0] * len(fatos)
        m = self.modelo
        seqs = [sequencia(m.bpe, m.contexto, pergunta, f) for f in fatos]
        ocultos = m.ocultos_lote(seqs)
        w, b = m.p["cabeca.weight"], m.p["cabeca.bias"]
        saida = []
        for i, ids in enumerate(seqs):
            z = float(ocultos[i, len(ids) - 1] @ w[0] + b[0])
            saida.append(1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z)))))
        return saida


@lru_cache(maxsize=4)
def leitor(pasta=str(PASTA), exigir_aprovacao=True):
    return LeitorTransformer(pasta, exigir_aprovacao)
