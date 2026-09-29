"""Planos de consulta com uma variável e condições comprováveis.

Gramática controlada, sem respostas específicas por assunto. Uma condição
não reconhecida invalida a consulta inteira. Falta de prova não é falsidade.
Só tipo_de admite negação, demonstrada por disjunção explícita no grafo.
"""
import re
from functools import lru_cache
from typing import NamedTuple, Optional, Tuple

from analisador_portugues import AnalisadorPortugues
from raciocinio import RELACOES, limpar


MAX_CONDICOES = 6
MAX_EXIBIDOS = 20


class Condicao(NamedTuple):
    relacao: str
    alvo: str
    inversa: bool = False
    negativa: bool = False


class PlanoConsulta(NamedTuple):
    condicoes: Tuple[Condicao, ...]
    sujeito: Optional[str] = None
    candidatos: Optional[Tuple[str, ...]] = None


class ConsultaInvalida(ValueError):
    pass


# Sujeito omitido = variável procurada; passiva inverte os argumentos.
PREDICADOS = (
    ("tipo_de", False, r"(?:e|eh|sao|seja|sejam) (.+)"),
    ("tipo_de", False,
     r"(?:pertence|pertencem) (?:ao|a|aos|as) (?:grupo|classe|categoria) "
     r"(?:de|do|da|dos|das) (.+)"),
    ("parte_de", False,
     r"(?:(?:faz|fazem) parte|sao parte|e parte) (?:de|do|da|dos|das) (.+)"),
    ("parte_de", True, r"(?:contem|inclui|incluem|abriga|abrigam) (.+)"),
    ("orbita", False,
     r"(?:orbita|orbitam|gira|giram) (?:em torno |ao redor )?"
     r"(?:(?:de|do|da|dos|das) )?(.+)"),
    ("orbita", True,
     r"(?:e|sao) (?:orbitado|orbitada|orbitados|orbitadas) "
     r"(?:por|pelo|pela|pelos|pelas) (.+)"),
    ("tem_caracteristica", False,
     r"(?:tem|possuem|possui|apresenta|apresentam) (.+)"),
)


class ConsultasRelacionais:
    def __init__(self, grafo):
        self.grafo = grafo
        self.aliases = sorted(grafo.aliases, key=lambda s: (-len(s), s)) if grafo else []

    def _entidade(self, texto):
        return self.grafo.aliases.get(limpar(texto)) if self.grafo else None

    def _prefixo_entidade(self, texto):
        n = limpar(texto)
        for alias in self.aliases:
            if n == alias or n.startswith(alias + " "):
                return self.grafo.aliases[alias], n[len(alias):].strip()
        return None, n

    def _predicado(self, texto):
        n = re.sub(r"^que ", "", texto.strip())
        negativa = n.startswith("nao ")
        if negativa:
            n = n[4:]
        for relacao, inversa, padrao in PREDICADOS:
            m = re.fullmatch(padrao, n)
            if m:
                alvo = self._entidade(m.group(1))
                if alvo and (not negativa or relacao == "tipo_de"):
                    return Condicao(relacao, alvo, inversa, negativa)
        # Objeto interrogativo omitido: "quais planetas a Lua orbita?".
        m = re.fullmatch(r"(.+?) (?:orbita|orbitam)", n)
        if m and not negativa:
            sujeito = self._entidade(m.group(1))
            if sujeito:
                return Condicao("orbita", sujeito, True)
        return None

    def _condicoes(self, texto):
        # Não separar todo 'e': após normalizar, o verbo 'é' tem a mesma
        # grafia. Cada trecho precisa formar um predicado COMPLETO.
        # Ex.: 'é ave e não é mamífero' são duas condições, não três.
        @lru_cache(maxsize=128)
        def resolver(trecho, limite):
            if not limite:
                return ()
            possibilidades = []
            inteira = self._predicado(trecho)
            if inteira:
                possibilidades.append((inteira,))
            for m in re.finditer(r"(?<= )e(?= )", trecho):
                primeira = self._predicado(trecho[:m.start()].strip())
                if primeira is None:
                    continue
                resto = trecho[m.end():].strip()
                for cauda in resolver(resto, limite - 1):
                    possibilidades.append((primeira,) + cauda)
                    if len(possibilidades) > 1:
                        return tuple(possibilidades[:2])
            return tuple(possibilidades)

        possibilidades = resolver(texto.strip(), MAX_CONDICOES)
        if len(possibilidades) > 1:
            raise ConsultaInvalida("As condições têm mais de uma interpretação. Separe os pedidos para esclarecer.")
        if not possibilidades:
            if re.search(r"\b(?:nao|nunca|jamais)\b", texto):
                raise ConsultaInvalida(
                    "Não interpretei todas as condições dessa negação. "
                    "Aqui só verifico 'não é/não são' com incompatibilidade "
                    "explícita entre classes; não deduzo ausência de propriedades.")
            raise ConsultaInvalida(
                "Não consegui interpretar todas as condições da consulta. "
                "Use relações cadastradas e ligue as condições com 'e'. "
                "Não vou descartar uma condição para responder só à outra.")
        return possibilidades[0]

    def analisar(self, texto, contexto=None):
        n = AnalisadorPortugues._preparar(texto)
        if not n:
            return None
        # Referências usam só os resultados efetivamente exibidos no turno
        # anterior, nunca todo o catálogo ou itens ocultos pela paginação.
        m = re.fullmatch(
            r"(?:(?:desses|dessas|destes|destas) (?:quais|quem)|e quais) (.+)", n)
        if m:
            if not contexto:
                raise ConsultaInvalida(
                    "Preciso de uma lista de resultados no turno anterior "
                    "para saber a quais itens você se refere.")
            return PlanoConsulta(self._condicoes(m.group(1)), candidatos=tuple(contexto))

        if self.grafo is None:
            return None
        if len(n) > 600:
            return None

        # Pergunta sobre o destino de uma relação, preservando sua direção.
        m = re.fullmatch(r"(.+?) orbita (?:o que|quem)", n)
        if m and self._entidade(m.group(1)):
            return PlanoConsulta((Condicao("orbita", self._entidade(m.group(1)), True),))
        m = re.fullmatch(r"(?:de que|do que) (.+?) faz parte", n)
        if m and self._entidade(m.group(1)):
            return PlanoConsulta((Condicao("parte_de", self._entidade(m.group(1)), True),))

        # 'O que é uma ave?' permanece uma DEFINIÇÃO. A forma passiva
        # 'o que é orbitado...' é uma busca pelo objeto de uma relação.
        m = re.fullmatch(r"(?:quem|o que) (.+)", n)
        if m and re.match(
                r"(?:e|eh|sao|nao|faz|tem|possui|apresenta|orbita|gira|contem|inclui)\b",
                m.group(1)) and (n.startswith("quem ") or re.match(
                r"(?:faz parte|tem |possui |apresenta |orbita |gira |"
                r"e orbitad[oa] |contem |inclui )", m.group(1))):
            return PlanoConsulta(self._condicoes(m.group(1)))

        m = re.fullmatch(r"(?:quais|que|liste|mostre) (?:sao )?(.+)", n)
        if m:
            categoria, resto = self._prefixo_entidade(m.group(1))
            if categoria:
                condicoes = (Condicao("tipo_de", categoria),)
                if resto:
                    condicoes += self._condicoes(re.sub(r"^que ", "", resto))
                if len(condicoes) > MAX_CONDICOES:
                    raise ConsultaInvalida("Há condições demais; use no máximo seis por consulta.")
                return PlanoConsulta(condicoes)
            # Uma classe desconhecida não autoriza buscar somente a parte
            # da frase que reconhecemos. Outras perguntas seguem no motor.
            if (n.startswith(("quais ", "liste ", "mostre "))
                    and not re.match(r"(?:as? )?(?:caracteristicas?|propriedades?)\b", m.group(1))
                    and re.search(r"\b(?:orbitam|tem|possuem|sao|fazem parte)\b", m.group(1))):
                raise ConsultaInvalida("Não reconheci a categoria ou todas as condições da consulta.")
            return None

        # Conjunção sobre um mesmo sujeito: todas as condições são
        # verificadas; nenhuma definição aproximada substitui uma prova.
        sujeito, resto = self._prefixo_entidade(n)
        if (sujeito and " e " in resto and re.match(
                r"(?:e|eh|sao|nao|tem|possui|apresenta|orbita|gira|faz|contem)\b", resto)):
            condicoes = self._condicoes(resto)
            if len(condicoes) >= 2:
                return PlanoConsulta(condicoes, sujeito)
        return None

    def _texto_caminho(self, caminho, relacao):
        partes = [self.grafo.nomes[caminho[0]]]
        for i, entidade in enumerate(caminho[1:], 1):
            tipo = ("tipo_de" if relacao == "tem_caracteristica"
                    and i < len(caminho) - 1 else relacao)
            partes.append(" --" + RELACOES[tipo] + "--> " + self.grafo.nomes[entidade])
        return "".join(partes)

    def _verificar(self, candidato, condicao):
        g = self.grafo
        s, o = ((condicao.alvo, candidato) if condicao.inversa
                else (candidato, condicao.alvo))
        caminho = g.provar(s, o, condicao.relacao)
        if caminho:
            return ("falso" if condicao.negativa else "verdadeiro",
                    self._texto_caminho(caminho, condicao.relacao))
        if condicao.relacao == "tipo_de":
            negativa = g.provar_incompatibilidade(s, o)
            if negativa:
                a, b, _ = negativa
                prova = (self._texto_caminho(a, "tipo_de") + "; " +
                         self._texto_caminho(b, "tipo_de") + "; " +
                         g.nomes[a[-1]] + " é explicitamente incompatível com " +
                         g.nomes[b[-1]])
                return "verdadeiro" if condicao.negativa else "falso", prova
        return "desconhecido", "Sem prova para: " + self._descrever(candidato, condicao)

    def _descrever(self, candidato, c):
        s, o = ((c.alvo, candidato) if c.inversa else (candidato, c.alvo))
        return (self.grafo.nomes[s] + (" NÃO " if c.negativa else " ") +
                RELACOES[c.relacao] + " " + self.grafo.nomes[o])

    def executar(self, plano):
        """Lista (entidade, avaliações); cada avaliação traz estado + prova.

        O catálogo é limitado pelo validador do grafo. Não há execução de
        código, chamadas externas ou alteração dos fatos durante consultas.
        """
        if (self.grafo is None or not plano.condicoes
                or len(plano.condicoes) > MAX_CONDICOES):
            return []
        candidatos = ((plano.sujeito,) if plano.sujeito else
                      plano.candidatos if plano.candidatos is not None else
                      self.grafo.nomes)
        resultados = []
        for entidade in sorted(set(candidatos), key=lambda e: (
                limpar(self.grafo.nomes.get(e, e)), e)):
            if entidade not in self.grafo.nomes:
                continue
            provas = tuple(self._verificar(entidade, c) for c in plano.condicoes)
            if plano.sujeito or all(p[0] == "verdadeiro" for p in provas):
                resultados.append((entidade, provas))
        return resultados

    def _contradicao(self, condicoes):
        """Incompatibilidade entre condições, sem presumir itens existentes.

        X é A e X não é A é impossível mesmo sem exemplares de A. Também
        podemos usar a taxonomia e disjunções explícitas entre classes.
        Não mistura propriedades, composição e órbitas nesse cálculo.
        """
        classes = [c for c in condicoes if c.relacao == "tipo_de" and not c.inversa]
        for a in classes:
            if a.negativa:
                continue
            for b in classes:
                if a == b:
                    continue
                if b.negativa:
                    caminho = ([a.alvo] if a.alvo == b.alvo else
                               self.grafo.provar(a.alvo, b.alvo, "tipo_de"))
                    if caminho:
                        return ("As condições exigem pertencer a " + self.grafo.nomes[a.alvo] +
                                " e não pertencer a " + self.grafo.nomes[b.alvo] +
                                ". Isso é incompatível: " + self._texto_caminho(caminho, "tipo_de") + ".")
                elif self.grafo.provar_incompatibilidade(a.alvo, b.alvo):
                    _, prova = self._verificar(a.alvo, Condicao("tipo_de", b.alvo))
                    return "As duas classificações pedidas são incompatíveis. Prova: " + prova + "."
        return None

    def responder(self, texto, contexto=None):
        """(id, texto, contexto) ou None. Contexto contém só IDs exibidos."""
        try:
            plano = self.analisar(texto, contexto)
        except ConsultaInvalida as exc:
            return "duvida", str(exc), None
        if plano is None:
            return None
        contradicao = self._contradicao(plano.condicoes)
        if contradicao:
            if plano.sujeito:
                return "logica:conjuncao_falsa", "Não. " + contradicao, None
            return ("logica:consulta_impossivel", contradicao +
                    " Nenhum item pode satisfazer todas essas condições ao mesmo tempo.", None)
        resultados = self.executar(plano)
        if plano.sujeito:
            provas = resultados[0][1]
            estados = [p[0] for p in provas]
            if "falso" in estados:
                ident = "logica:conjuncao_falsa"
                inicio = "Não. Pelo menos uma das condições é contrariada por uma prova cadastrada."
            elif "desconhecido" in estados:
                ident = "logica:desconhecido"
                inicio = "Ainda não tenho prova de todas as condições. Não posso confirmar a frase inteira."
            else:
                ident = "logica:conjuncao"
                inicio = "Sim. Todas as condições têm prova nas relações cadastradas."
            detalhes = ["- " + estado + ": " + prova for estado, prova in provas]
            return ident, inicio + "\n" + "\n".join(detalhes), None
        if not resultados:
            return ("logica:desconhecido",
                    "Não encontrei itens com prova de todas as condições na base. "
                    "Isso não prova que não existam; podem faltar relações cadastradas.", None)
        exibidos = resultados[:MAX_EXIBIDOS]
        nomes = [self.grafo.nomes[e] for e, _ in exibidos]
        linhas = ["Encontrei na base: " + "; ".join(nomes) + "."]
        for entidade, provas in exibidos:
            linhas.append("- " + self.grafo.nomes[entidade] + ": " +
                          "; ".join(p[1] for p in provas) + ".")
        if len(resultados) > len(exibidos):
            linhas.append("Exibindo {} de {} resultados comprovados. 'Desses' filtra "
                          "somente os itens exibidos.".format(len(exibidos), len(resultados)))
        linhas.append("Só incluí itens com prova de todas as condições. "
                      "A lista cobre apenas os fatos cadastrados; pode haver outros exemplos.")
        return "logica:consulta", "\n".join(linhas), tuple(e for e, _ in exibidos)
