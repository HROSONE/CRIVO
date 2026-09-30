"""Classificador autoral de atos de diálogo com o estado anterior da conversa.

Não gera texto nem aprende fatos do usuário. A MLP seleciona uma operação;
o gerenciador de diálogo conserva os argumentos e compõe a resposta.
"""
import hashlib
import inspect
import json
import re
from functools import lru_cache
from pathlib import Path

from rede_sequencial import RedeSequencial, atributos_frase, palavras, softmax

VERSAO = "dialogo-contextual-v2"
DIMENSAO = 972
ESTADOS = ("livre", "pessoal", "factual", "pendente")
ATOS_PESSOAIS = frozenset(("relato", "preferencia", "objetivo", "ponto_de_vista", "resposta"))
FLEXOES = {"vc": "voce", "tu": "voce", "ce": "voce", "to": "estou",
           "tou": "estou", "tava": "estava", "q": "que", "pq": "porque",
           "tb": "tambem", "tbm": "tambem", "n": "nao"}


def atributos(texto, estado, lexico, dimensao=DIMENSAO):
    if estado not in ESTADOS or dimensao != DIMENSAO:
        raise ValueError("Estado ou representação de diálogo inválidos")
    ts = [FLEXOES.get(t, t) for t, _, _ in palavras(texto)]
    abstratos = [t if t in lexico else "conteudo" for t in ts]
    v = atributos_frase(" ".join(abstratos), 768)
    # Um canal menor conserva fragmentos das palavras originais. Assim
    # flexões e palavras fora do léxico não viram todas o mesmo argumento.
    v.update({768 + i: .35 * valor for i, valor in atributos_frase(" ".join(ts), 192).items()})
    v[960 + ESTADOS.index(estado)] = .65
    if "?" in texto:
        v[964] = .3
    if len(ts) <= 4:
        v[965] = .3
    if any(c in texto for c in ('`', '"', '“', '”')):
        v[966] = .3
    return v


def assinatura_atributos():
    fonte = VERSAO + str(DIMENSAO) + repr(ESTADOS) + repr(sorted(FLEXOES.items()))
    fonte += inspect.getsource(atributos) + inspect.getsource(atributos_frase) + inspect.getsource(palavras)
    return hashlib.sha256(fonte.encode("utf-8")).hexdigest()


class DialogoNeural:
    def __init__(self, dados):
        if dados.get("versao") != 1 or dados.get("assinatura_atributos") != assinatura_atributos():
            raise ValueError("Pesos incompatíveis com os atributos de diálogo; treine novamente")
        self.lexico = frozenset(dados["lexico"])
        self.rede = RedeSequencial.de_dados(dados["rede"])
        if self.rede.dimensao != DIMENSAO:
            raise ValueError("Dimensão de diálogo incompatível")
        self.limiar = dados["limiar"]
        if not .5 <= self.limiar <= 1:
            raise ValueError("Limiar de diálogo inválido")

    def analisar(self, texto, estado):
        ps = softmax(self.rede.logits(atributos(texto, estado, self.lexico)), self.rede.temperatura)
        indices = sorted(range(len(ps)), key=lambda k: ps[k], reverse=True)
        primeiro = indices[0]
        pessoal = sum(p for ato, p in zip(self.rede.rotulos, ps) if ato in ATOS_PESSOAIS)
        return dict(ato=self.rede.rotulos[primeiro], confianca=ps[primeiro],
                    margem=ps[primeiro] - ps[indices[1]], estado=estado, confianca_pessoal=pessoal)


@lru_cache(maxsize=4)
def carregar(caminho, mtime):
    return DialogoNeural(json.loads(Path(caminho).read_text(encoding="utf-8")))
