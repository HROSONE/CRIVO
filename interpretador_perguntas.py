"""Interpretador de perguntas sobre conceitos.

Separa duas coisas que antes vinham juntas numa regra por frase:

1. O CONCEITO: o nome (ou sinônimo) de um conceito conhecido em qualquer
   lugar da fala, com tolerância a um erro de digitação em nomes longos.
2. O PEDIDO: o resto da fala precisa ser feito só de palavras de pedido
   ("o que é", "explica", "fala um pouco", "tenho uma dúvida", "me ajuda",
   "pra prova"...). Se sobrar outra palavra de conteúdo ("Morcego é ave?",
   "estou com ansiedade hoje"), não é um pedido de explicação e o
   interpretador não interfere.

Quando reconhece o pedido, devolve a forma canônica "O que é <conceito>?",
que o restante do CRIVO já responde. Não inventa conteúdo: só reescreve.
"""
import re

from linguagem_conversa import normalizar

# Palavras que podem cercar o conceito num pedido de explicação. Lista geral
# de palavras funcionais e de pedido do português, não de frases inteiras.
PEDIDO = set("""
a o as os um uma uns umas de do da dos das d em no na nos nas num numa ao aos à às pra pro pras pros para por
pelo pela e ou que q oq oque qual quais quale como cmo onde quando quem porque pq
é e eh ser seria sera era sao são esta está isso isto esse essa este esta aquilo ai aí la lá ta tá
me mim te pra-mim vc voce você voces vocês alguem alguém pf pfv pls favor por-favor obrigado obrigada valeu
eu to tô tou estou ando
explica explique explicar explicaria explicação explicacao explicacão expliquei
fala fale falar fala-me conta conte contar diz diga dizer dizendo mostra mostre ensina ensine ensinar
resume resuma resumir resumo resumao resumão define defina definir definição definicao conceito conceitos
significa significado quer querem dizer sentido ideia idéia
sabe sabes saberia saber sei entender entendo entendi entende compreender compreendo
duvida dúvida duvidas dúvidas pergunta perguntinha questao questão
ajuda ajude ajudar socorro help preciso precisava queria quero gostaria podia poderia pode pode-me
estudando estudar estudo estudei prova provas trabalho escola faculdade aula
simples simplificado facil fácil rapido rápido resumido detalhe detalhes direito melhor bem pouco mais
exatamente afinal mesmo assim tipo jeito forma maneira palavras básico basico basicamente geral
sobre acerca respeito tema assunto materia matéria coisa nada tudo
funciona funcionam serve servem
""".split())

# "como assim", "o que vem a ser" e parecidos usam só palavras de PEDIDO.

_RELATO = re.compile(r"\b(?:estou|to|tô|tou|ando|fiquei|sinto|senti|tive|tenho)\b(?! (?:uma |umas )?d[uú]vidas?\b)")
_PALAVRA = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _distancia(a, b, limite):
    """Distância de edição com corte: devolve limite + 1 se passar dele."""
    if abs(len(a) - len(b)) > limite:
        return limite + 1
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i] + [0] * len(b)
        menor = atual[0]
        for j, cb in enumerate(b, 1):
            atual[j] = min(anterior[j] + 1, atual[j - 1] + 1, anterior[j - 1] + (ca != cb))
            menor = min(menor, atual[j])
        if menor > limite:
            return limite + 1
        anterior = atual
    return anterior[-1]


def _tolerancia(nome):
    """Erros aceitos: nenhum em nomes curtos, um em médios, dois em longos."""
    n = len(nome.replace(" ", ""))
    return 0 if n < 6 else 1 if n < 11 else 2


class InterpretadorPerguntas:
    def __init__(self, itens):
        """itens: {id: {"nome":..., "aliases": [...]}} (o compositor)."""
        self.lexico = {}
        for ident, item in itens.items():
            for nome in [item["nome"]] + list(item.get("aliases", [])):
                chave = " ".join(_PALAVRA.findall(normalizar(nome)))
                if chave:
                    self.lexico.setdefault(chave, set()).add(ident)
        self.nomes = {ident: item["nome"] for ident, item in itens.items()}
        self.maior = max((len(k.split()) for k in self.lexico), default=1)

    def conceito(self, palavras):
        """(id, inicio, fim) do conceito citado, ou None se ausente/ambíguo."""
        exatos, aproximados = [], []
        for tamanho in range(min(self.maior, len(palavras)), 0, -1):
            for ini in range(len(palavras) - tamanho + 1):
                trecho = " ".join(palavras[ini:ini + tamanho])
                ids = self.lexico.get(trecho)
                if ids:
                    exatos.append((tamanho, ini, ids))
            if exatos:
                break
        if exatos:
            tamanho, ini, ids = max(exatos, key=lambda e: e[0])
            if len({frozenset(e[2]) for e in exatos if e[0] == tamanho}) > 1 or len(ids) != 1:
                return None
            return next(iter(ids)), ini, ini + tamanho
        # Sem nome exato: um erro de digitação ("entrpia"), só se for único.
        for tamanho in range(min(self.maior, len(palavras)), 0, -1):
            for ini in range(len(palavras) - tamanho + 1):
                trecho = " ".join(palavras[ini:ini + tamanho])
                if trecho in PEDIDO or len(trecho) < 6:
                    continue
                for chave, ids in self.lexico.items():
                    if len(chave.split()) != tamanho or len(ids) != 1:
                        continue
                    limite = _tolerancia(chave)
                    if limite and _distancia(trecho, chave, limite) <= limite:
                        aproximados.append((next(iter(ids)), ini, ini + tamanho))
            if aproximados:
                break
        if len({a[0] for a in aproximados}) == 1:
            return aproximados[0]
        return None

    def reescrever(self, texto):
        """"O que é <conceito>?" se a fala pede explicação de um conceito
        conhecido; None caso contrário."""
        if not isinstance(texto, str) or len(texto) > 200:
            return None
        n = normalizar(texto)
        palavras = _PALAVRA.findall(n)
        if not palavras or len(palavras) > 16:
            return None
        achado = self.conceito(palavras)
        if achado is None:
            return None
        ident, ini, fim = achado
        resto = palavras[:ini] + palavras[fim:]
        # Qualquer outra palavra de conteúdo muda a pergunta: não interferir.
        if any(p not in PEDIDO for p in resto):
            return None
        pede = "?" in texto or not resto or any(p not in ("a", "o", "e", "de", "do", "da", "eu", "to", "tô", "estou")
                                                for p in resto)
        if not pede:
            return None
        # "Estou com ansiedade": relato, não pedido (sem "dúvida", "explica"...).
        if _RELATO.search(n) and not re.search(
                r"\b(?:explica\w*|duvida\w*|d[uú]vida\w*|ajud\w*|socorro|entend\w*|significa\w*|resum\w*|"
                r"defin\w*|conceito|o que|oq|o q|qual|como)\b", n):
            return None
        return "O que é " + self.nomes[ident] + "?"
