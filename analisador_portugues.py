"""Análise superficial reutilizável do português, sem IA externa.

Converte formulações reconhecidas em quadros:
    intenção, sujeito, predicado, objeto.
O vocabulário de entidades vem do grafo ATIVO (inclusive grafos de
teste), não de nomes hardcoded no interpretador. A gramática de ações
tem extensão limitada; desconhecimento não é negação.

Não é parser sintático de português livre: é uma gramática controlada,
determinística, conservadora e auditável, compatível com Python 3.8+.
"""
import re
import unicodedata
from typing import NamedTuple, Optional

from raciocinio import limpar


class QuadroSemantico(NamedTuple):
    intencao: str
    sujeito: str
    predicado: str
    objeto: Optional[str]


def simplificar(texto):
    """Normaliza acentos/pontuação sem eliminar a ordem nem artigos."""
    if not isinstance(texto, str) or len(texto) > 2000:
        return ""
    s = unicodedata.normalize("NFD", texto.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9_\s-]", " ", s)
    return " ".join(s.split())


# Ações e construções reutilizáveis. As entidades são TODAS resolvidas
# por aliases exatos, sem procurar palavras semelhantes em textos.
PRELUDIOS = (
    r"voce (?:poderia|pode|consegue) (?:me )?(?:dizer|explicar|contar)\s+",
    r"(?:pode|poderia) (?:me )?(?:dizer|explicar|contar)\s+",
    r"(?:queria|gostaria) de saber\s+",
    r"quero saber\s+",
    r"eu (?:queria|gostaria) de saber\s+",
    r"(?:me diga|me diz|me explique|me explica)\s+",
    r"por (?:favor|gentileza)\s+",
)
POLIDEZ_FINAL = r"\s+(?:pra mim|para mim|por favor|por gentileza)$"
NEGACAO = re.compile(r"\b(?:nao|nunca|jamais|nem)\b")
CONDICIONAL = re.compile(r"^(?:se|suponha|imagine|caso)\s+")


class AnalisadorPortugues:
    """Quadros de intenção + argumentos, demonstrados por grafo ativo."""

    def __init__(self, grafo):
        self.grafo = grafo

    def _entidade(self, texto):
        if self.grafo is None:
            return None
        return self.grafo.aliases.get(limpar(texto))

    def _par(self, modo, relacao, a, b, inverter=False):
        """Converte grupos sintáticos para IDs SEM correção aproximada."""
        sujeito = self._entidade(b if inverter else a)
        objeto = self._entidade(a if inverter else b)
        if not sujeito or not objeto or sujeito == objeto:
            return None
        return QuadroSemantico(modo, sujeito, relacao, objeto)

    @staticmethod
    def _preparar(texto):
        n = simplificar(texto)
        if not n:
            return ""
        # Apenas uma camada curta de atos de fala e de cortesia.
        # Não altera o conteúdo semântico de negações ou hipóteses.
        for _ in range(3):
            novo = n
            for padrao in PRELUDIOS:
                novo = re.sub(r"^" + padrao, "", novo)
                if novo != n:
                    break
            if novo == n:
                break
            n = novo.strip()
        n = re.sub(POLIDEZ_FINAL, "", n).strip()
        return n

    def analisar(self, texto):
        """Analisa uma pergunta sem responder nem introduzir fatos.

        Retorna None quando a forma é ambígua/não reconhecida. A
        conclusão nunca vem de apenas encontrar uma palavra na pergunta.
        """
        n = self._preparar(texto)
        if not n or len(n) > 450:
            return None
        if NEGACAO.search(n):
            return None

        # "Quero saber se X ..." é uma pergunta interrogativa indireta;
        # "Se X fosse Y ..." é hipótese: não autoriza prova factual.
        origem = simplificar(texto)
        if n.startswith("se ") and origem.startswith((
                "quero saber se ", "queria saber se ",
                "gostaria de saber se ", "eu queria saber se ",
                "eu gostaria de saber se ", "voce pode dizer se ",
                "voce poderia dizer se ", "pode me dizer se ",
                "poderia me dizer se ")):
            n = n[3:]
        if CONDICIONAL.search(n):
            return None

        # 1. Pedido de definição: a fonte será buscada na base editorial
        # pelo chamador. Não responde consultando a rede nem o grafo.
        definicoes = (
            r"o que (?:e|eh|sao) (.+)",
            r"o que significa (.+)",
            r"(?:qual (?:e )?o )?significado (?:de|da|do) (.+)",
            r"defina (.+)",
            r"definir (.+)",
            r"(?:pode|poderia) definir (.+)",
            r"como se define (.+)",
            r"explique o que (?:e|eh|sao) (.+)",
            r"explica o que (?:e|eh|sao) (.+)",
        )
        for padrao in definicoes:
            m = re.fullmatch(padrao, n)
            if m:
                alvo = limpar(m.group(1))
                # A definição de uma frase coordenada cabe ao módulo
                # existente de duas ou três definições.
                if (not alvo or len(alvo) > 85 or len(alvo.split()) > 8 or
                        re.search(r"\b(?:e|ou|porque|como|qual|quem|onde|que)\b", alvo)):
                    return None
                return QuadroSemantico("definir", alvo, "definicao", None)

        # 2. Classes de propriedades, verificadas individualmente no grafo.
        for padrao in (
                r"(?:qual|que) (?:e )?(?:a )?(?:caracteristica|propriedade)"
                r" (.+?) (?:tem|possuem|possui|apresentam|apresenta)",
                r"(?:quais|que) (?:caracteristicas|propriedades)"
                r" (.+?) (?:tem|possuem|possui|apresentam|apresenta)"):
            m = re.fullmatch(padrao, n)
            if m:
                s = self._entidade(m.group(1))
                if s:
                    return QuadroSemantico("enumerar", s, "tem_caracteristica", None)
                return None

        # 3. Ligações / semelhanças entre duas entidades nomeadas.
        relacoes = (
            ("comparar", "comum", r"em que (.+?) e (.+?) se parecem"),
            ("comparar", "comum", r"(.+?) e (.+?) compartilham "
             r"(?:alguma |uma )?(?:classificacao|categoria|caracteristica)"),
            ("comparar", "comum", r"(?:qual|quais) (?:sao as |as )?"
             r"semelhancas? (?:existem )?entre (.+?) e (.+)"),
            ("relacionar", "ligacao", r"existe (?:alguma |uma )?"
             r"(?:ligacao|relacao) entre (.+?) e (.+)"),
            ("relacionar", "ligacao", r"que relacao ha entre (.+?) e (.+)"),
            ("relacionar", "ligacao", r"como (.+?) e (.+?) se relacionam"),
            ("relacionar", "ligacao", r"como (.+?) e (.+?) estao relacionados"),
        )
        for modo, predicado, padrao in relacoes:
            m = re.fullmatch(padrao, n)
            if m:
                return self._par(modo, predicado, m.group(1), m.group(2))

        # 4. Verificar uma proposição sujeito/ação/objeto.
        # A posição dos argumentos é declarada em cada construção,
        # distinguindo formas ativas e passivas.
        predicados = (
            ("tipo_de", False,
             r"(.+?) (?:pertence|pertencem) (?:ao|a|aos|as) "
             r"(?:grupo|categoria|classe) (?:das|dos|da|do|de)?\s*(.+)"),
            ("tipo_de", False,
             r"(.+?) (?:se encaixa|se enquadra) (?:como |na categoria de |"
             r"no grupo de )?(.+)"),
            ("tipo_de", False,
             r"(.+?) (?:pode ser |e |eh |sao )?"
             r"(?:considerado|considerada|considerados|consideradas|"
             r"classificado|classificada|classificados|classificadas) "
             r"(?:como )?(.+)"),
            ("tipo_de", False,
             r"seria correto classificar (.+?) como (.+)"),
            ("parte_de", False,
             r"(.+?) (?:faz parte|e parte|eh parte) (?:de|do|da|dos|das) (.+)"),
            ("parte_de", False,
             r"(.+?) (?:esta dentro|esta contido|esta contida|esta incluido|"
             r"esta incluida) (?:de|do|da|dos|das|em|no|na) (.+)"),
            ("parte_de", True,
             r"(.+?) (?:contem|inclui|abriga) (.+)"),
            ("orbita", False,
             r"(.+?) (?:orbita|gira ao redor|gira em torno|"
             r"da voltas ao redor|da voltas em torno) "
             r"(?:de|do|da|dos|das|ao|a|o)?\s*(.+)"),
            ("orbita", True,
             r"(.+?) (?:e|eh|foi) (?:orbitado|orbitada) "
             r"(?:por|pelo|pela|pelos|pelas) (.+)"),
            ("tem_caracteristica", False,
             r"(.+?) (?:possui|tem|apresenta) (.+)"),
        )
        for relacao, inverter, padrao in predicados:
            m = re.fullmatch(padrao, n)
            if m:
                return self._par("verificar", relacao, m.group(1),
                                 m.group(2), inverter=inverter)
        return None

    def responder(self, quadro):
        """Executa o quadro com provas tipadas (ou admite ausência).

        Não transforma falta de prova em 'falso'. Uso de definições:
        devolve None, pois a única fonte permitida para elas é a base
        editorial do CRIVO, consultada pelo chamador.
        """
        if quadro is None or quadro.intencao == "definir" or self.grafo is None:
            return None
        g = self.grafo
        s, o, tipo = quadro.sujeito, quadro.objeto, quadro.predicado
        if quadro.intencao in ("relacionar", "comparar"):
            # Reutiliza o mesmo provador genérico das perguntas anteriores,
            # preservando provas, incompatibilidades e explicações.
            from interpretacao_geral import InterpretadorGeral
            prefixo = ("o que " + g.nomes[s] + " e " + g.nomes[o] +
                       " tem em comum?" if tipo == "comum" else
                       "qual a relacao entre " + g.nomes[s] + " e " +
                       g.nomes[o] + "?")
            return InterpretadorGeral(g).interpretar(prefixo)
        if quadro.intencao == "enumerar":
            provas = []
            atributos = sorted({alvo for grupo in
                               g.arestas["tem_caracteristica"].values()
                               for alvo in grupo})
            for atributo in atributos:
                caminho = g.provar_caracteristica(s, atributo)
                if caminho:
                    # Setas simples são só os passos taxonômicos;
                    # a última aresta é explicitamente uma propriedade.
                    p = " → ".join(g.nomes[id_] for id_ in caminho[:-1])
                    p += " --tem_caracteristica--> " + g.nomes[caminho[-1]]
                    provas.append(p)
            if not provas:
                return ("logica:desconhecido",
                        "Não tenho uma característica afirmativa cadastrada "
                        "que permita concluir isso. Isso não significa que "
                        "a afirmação seja falsa.")
            return ("logica:caracteristicas",
                    "Características demonstráveis de " + g.nomes[s] +
                    " nas relações cadastradas: " + "; ".join(provas) + ".")

        if quadro.intencao == "verificar":
            if tipo == "tipo_de":
                pergunta = g.nomes[s] + " é " + g.nomes[o] + "?"
            elif tipo == "parte_de":
                pergunta = g.nomes[s] + " faz parte de " + g.nomes[o] + "?"
            elif tipo == "orbita":
                pergunta = g.nomes[s] + " orbita " + g.nomes[o] + "?"
            elif tipo == "tem_caracteristica":
                pergunta = g.nomes[s] + " tem " + g.nomes[o] + "?"
            else:
                return None
            # Todo caminho e toda prova negativa continuam sob controle
            # do provador existente, inclusive suas restrições de tipos.
            return g.interpretar(pergunta)
        return None
