"""Roteador pequeno autoral: atos sobre fatos pessoais e uma classe fora."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from intencao_gerativa import atributos, assinatura_atributos, DIMENSAO
from rede_sequencial import RedeSequencial, softmax

ACOES = ('sugerir', 'explicar', 'resumir', 'consultar', 'perguntar', 'fora')


def assinatura():
    return hashlib.sha256((assinatura_atributos() + repr(ACOES)).encode()).hexdigest()


class IntencaoSessao:
    def __init__(self, dados):
        if dados.get('assinatura') != assinatura() or not dados.get('aprovado'):
            raise ValueError('Roteador de sessão sem validação compatível')
        self.rede = RedeSequencial.de_dados(dados['rede'])
        if self.rede.dimensao != DIMENSAO or tuple(self.rede.rotulos) != ACOES:
            raise ValueError('Contrato do roteador de sessão incompatível')
        self.lexico = frozenset(dados['lexico'])

    def analisar(self, texto, estado):
        ps = softmax(self.rede.logits(atributos(texto, estado, self.lexico)), self.rede.temperatura)
        ordem = sorted(range(len(ps)), key=lambda i: ps[i], reverse=True)
        i, j = ordem[:2]
        return dict(acao=ACOES[i], confianca=ps[i], margem=ps[i]-ps[j],
                    aceita=ACOES[i] != 'fora' and ps[i] >= .80 and ps[i]-ps[j] >= .20)


@lru_cache(maxsize=2)
def carregar(caminho, mtime):
    return IntencaoSessao(json.loads(Path(caminho).read_text(encoding='utf-8')))
