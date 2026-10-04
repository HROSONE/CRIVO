"""Reconhece pedidos de conceitos do acervo ativo, sem produzir fatos.

Nome e pedido são analisados separadamente. Uma correção de digitação só é
aceita quando o alvo é único e o restante tem sentido de pedido. Relações,
causas, condições, negações e relatos pessoais ficam com os motores existentes.
Não há pesos nem modelo externo neste módulo.
"""
import re
from typing import NamedTuple

from linguagem_conversa import normalizar

_PALAVRA = re.compile(r"[a-z0-9_]+(?:\+\+|#)?(?:-[a-z0-9_]+)*")
PEDIDO = set("""
a o as os um uma uns umas de do da dos das em no na nos nas ao aos pra pro pras pros para
pelo pela que q oq oque qual quais e eh ser seria sao isso isto esse essa este esta
me mim te vc voce voces alguem pf pfv pls favor obrigado obrigada valeu eu
explica explique explicar explicaria explicacao fala fale falar conta conte contar
diz diga dizer mostra mostre ensina ensine ensinar resume resuma resumir resumo
resumao define defina definir definicao conceito significa significado quer dizer sentido ideia
sabe saber sei entender entendo entende compreender compreendo duvida duvidas pergunta questao
ajuda ajude ajudar preciso queria quero gostaria podia poderia pode
estudando estudar estudo prova provas trabalho escola faculdade aula
simples simplificado facil rapido resumido detalhe detalhes direito melhor bem pouco mais
exatamente afinal mesmo assim tipo jeito forma maneira palavras basico basicamente
sobre acerca respeito tema assunto materia funciona funcionam serve servem como cmo to tou estou
""".split())
_EXPLICITO = set("""
explica explique explicar explicaria explicacao fala fale falar conta conte contar diz diga
mostra mostre ensina ensine ensinar resume resuma resumir resumo resumao define defina definir
definicao conceito significa significado sentido ideia entender entende compreender duvida duvidas
""".split())
_EDUCACAO = {"estudando", "estudar", "estudo", "prova", "provas", "escola", "faculdade", "aula"}
_RELATO = {"to", "tou", "estou", "tenho", "ando", "sinto", "senti", "fiquei", "tive"}


class PerguntaConceito(NamedTuple):
    conceito: str
    nome: str
    alias: str
    consulta: str
    distancia: int
    intencao: str
    formato: str
    educacional: bool


def _distancia(a, b, limite):
    if abs(len(a) - len(b)) > limite:
        return limite + 1
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i]
        for j, cb in enumerate(b, 1):
            atual.append(min(anterior[j] + 1, atual[j - 1] + 1,
                             anterior[j - 1] + (ca != cb)))
        if min(atual) > limite:
            return limite + 1
        anterior = atual
    return anterior[-1]


def _tolerancia(nome):
    n = len(nome.replace(" ", ""))
    return 0 if n < 6 else 1 if n < 11 else 2


class InterpretadorPerguntas:
    def __init__(self, itens):
        self.lexico = {}
        self.nomes = {ident: item["nome"] for ident, item in itens.items()}
        for ident, item in itens.items():
            for nome in [item["nome"]] + list(item.get("aliases", [])):
                chave = " ".join(_PALAVRA.findall(normalizar(nome)))
                if chave:
                    self.lexico.setdefault(chave, set()).add(ident)
        self.maior = max((len(k.split()) for k in self.lexico), default=1)
        self.aproximados = {}
        for alias, ids in self.lexico.items():
            limite = _tolerancia(alias)
            if limite:
                self.aproximados.setdefault((len(alias.split()), len(alias)), []).append(
                    (alias, tuple(sorted(ids)), limite))

    def _candidatos(self, palavras):
        for tamanho in range(min(self.maior, len(palavras)), 0, -1):
            for ini in range(len(palavras) - tamanho + 1):
                trecho = " ".join(palavras[ini:ini + tamanho])
                ids = self.lexico.get(trecho)
                if ids is not None:
                    # Alias ambíguo não pode ser corrigido para outro nome.
                    for ident in ids:
                        yield ident, ini, ini + tamanho, trecho, 0
                    continue
                if trecho in PEDIDO or len(trecho.replace(" ", "")) < 5:
                    continue
                for comprimento in range(len(trecho) - 2, len(trecho) + 3):
                    for alias, ids, limite in self.aproximados.get((tamanho, comprimento), ()):
                        distancia = _distancia(trecho, alias, limite)
                        if distancia <= limite:
                            for ident in ids:
                                yield ident, ini, ini + tamanho, alias, distancia

    def conceito(self, palavras):
        """Compatibilidade: alvo único no maior trecho, ou None."""
        candidatos = list(self._candidatos(palavras))
        if not candidatos:
            return None
        maior = max(c[2] - c[1] for c in candidatos)
        candidatos = [c for c in candidatos if c[2] - c[1] == maior]
        menor = min(c[4] for c in candidatos)
        candidatos = [c for c in candidatos if c[4] == menor]
        if len({c[0] for c in candidatos}) != 1:
            return None
        return candidatos[0][:3]

    def _pedido(self, palavras, ini, fim):
        resto = palavras[:ini] + palavras[fim:]
        duvida = "duvida" in resto or "duvidas" in resto
        permitido = PEDIDO | ({"tenho"} if duvida else set())
        if any(p not in permitido for p in resto):
            return None
        educacional = bool(set(resto) & _EDUCACAO or duvida)
        if set(resto) & _RELATO and not educacional:
            return None
        explicito = bool(set(resto) & _EXPLICITO)
        definicao = any(p in resto for p in ("oq", "oque", "q", "qual")) or (
            "que" in resto and any(p in resto for p in ("e", "eh", "ser", "seria", "sao")))
        mecanismo = "funciona" in resto or "funcionam" in resto
        funcao = "serve" in resto or "servem" in resto
        if "como" in resto or "cmo" in resto:
            if not (mecanismo or funcao):
                return None
        ajuda_estudo = educacional and bool(set(resto) & {"ajuda", "ajude", "ajudar"})
        if resto and not (explicito or definicao or mecanismo or funcao or
                          ajuda_estudo or "saber" in resto):
            return None
        formato = "resumo" if set(resto) & {"resume", "resuma", "resumir", "resumo", "resumao", "resumido"} else ""
        if set(resto) & {"simples", "simplificado", "basico"} and not formato:
            formato = "simples"
        return ("funcionamento" if mecanismo else "funcao" if funcao else "definir",
                formato, educacional)

    def analisar(self, texto):
        if not isinstance(texto, str) or len(texto) > 200:
            return None
        if re.search(r"[;{}=<>`\n]", texto):
            return None
        palavras = _PALAVRA.findall(normalizar(texto))
        if not palavras or len(palavras) > 20:
            return None
        candidatos = []
        for ident, ini, fim, alias, distancia in self._candidatos(palavras):
            # Um nome isolado desconhecido exige esclarecimento. "planta"
            # não autoriza trocar o tema para "planeta" por distância de edição.
            if distancia and ini == 0 and fim == len(palavras):
                continue
            pedido = self._pedido(palavras, ini, fim)
            if pedido is not None:
                candidatos.append((ident, ini, fim, alias, distancia, pedido))
        if not candidatos:
            return None
        maior = max(c[2] - c[1] for c in candidatos)
        candidatos = [c for c in candidatos if c[2] - c[1] == maior]
        menor = min(c[4] for c in candidatos)
        candidatos = [c for c in candidatos if c[4] == menor]
        if len({c[0] for c in candidatos}) != 1:
            return None
        ident, ini, fim, alias, distancia, pedido = candidatos[0]
        intencao, formato, educacional = pedido
        prefixo = {"definir": "O que é ", "funcionamento": "Como funciona ",
                   "funcao": "Para que serve "}[intencao]
        return PerguntaConceito(ident, self.nomes[ident], alias,
                               prefixo + self.nomes[ident] + "?", distancia,
                               intencao, formato, educacional)

    def reescrever(self, texto):
        quadro = self.analisar(texto)
        return quadro.consulta if quadro else None
