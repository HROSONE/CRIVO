"""Separa o ato de pedir informação do conteúdo factual do pedido.

O parser não contém categorias ou respostas do currículo. Produz um quadro
de intenção/alvo/condições; a execução resolve o alvo no grafo ativo e usa
o provador existente. Não é um parser universal de português.
"""
import re
from typing import NamedTuple

from analisador_portugues import AnalisadorPortugues
from consultas_relacionais import Condicao, ConsultaInvalida, MAX_CONDICOES, MAX_EXIBIDOS
from raciocinio import RELACOES, limpar


class Pedido(NamedTuple):
    intencao: str
    alvo: str
    condicoes: str = ""
    modo: str = "exemplos"


class InterpretadorPedidos:
    def __init__(self, grafo, consultor):
        self.grafo = grafo
        self.consultor = consultor
        # Destinos de tipo_de são classes da taxonomia. Intermediários
        # não são apresentados como exemplares em pedidos de exemplos.
        self.classes = {c for pais in grafo.arestas["tipo_de"].values() for c in pais} if grafo else set()

    def analisar(self, texto):
        n = AnalisadorPortugues._preparar(texto)
        n = re.sub(r"\b(?:vc|tu|ce)\b", "voce", n)
        n = re.sub(r"^(?:voce )?(?:pode|poderia|consegue) (?:me )?"
                   r"(?=(?:citar|listar|mostrar|dar)\b)", "", n)
        # O conteúdo pode conter qualificadores: eles ficam no alvo ou
        # nas condições e precisam ser reconhecidos na execução inteira.
        m = re.fullmatch(
            r"(?:quais|que) (?:sao )?(?:os |as )?(.+?) (?:que )?(?:voce )?"
            r"(?:conhece|sabe listar|consegue citar|pode citar)(?: (que .+))?", n)
        if m:
            alvo, condicoes = m.group(1), m.group(2) or ""
        else:
            m = re.fullmatch(r"(?:quais|que) (?:sao )?(?:os |as )?(.+?) existem", n)
            if m:
                alvo, condicoes = m.group(1), ""
            else:
                m = re.fullmatch(
                    r"(?:(?:me )?(?:de|dar|cite|citar|liste|listar|mostre|mostrar|diga) )?"
                    r"(?:(?:alguns|algumas) )?(?:nomes|exemplos|tipos) (?:de|do|da|dos|das) (.+)", n)
                if m:
                    modo = "tipos" if re.search(r"\btipos\b", n) else "exemplos"
                    return Pedido("listar", m.group(1), modo=modo)
                alvo = None
        if alvo is not None:
            tipos = re.fullmatch(r"(?:tipos|classes|categorias) de (.+)", alvo)
            return Pedido("listar", tipos.group(1) if tipos else alvo,
                          condicoes, "tipos" if tipos else "exemplos")

        m = re.fullmatch(r"o que (?:voce )?(?:sabe|conhece) (?:sobre|de|a respeito de) (.+)", n)
        if m:
            return Pedido("informar", m.group(1))
        m = re.fullmatch(
            r"(?:voce )?(?:conhece|tem informacoes sobre|tem conhecimento sobre|"
            r"sabe algo sobre|sabe falar sobre) (.+)", n)
        if m:
            return Pedido("disponibilidade", m.group(1))
        m = re.fullmatch(
            r"(?:(?:fale|conte|explique)(?: sobre)? )?(?:a|o) "
            r"(primeir[oa]|segund[oa]|terceir[oa])", n)
        if m:
            return Pedido("retomar_item", m.group(1))
        return None

    def responder(self, pedido):
        """Executa listagens; informação sobre um conceito segue no motor factual.

        Retorna (id, texto, IDs exibidos), ou None para pedir a definição do
        alvo completo. Não adiciona fatos nem presume listas exaustivas.
        """
        if pedido.intencao not in ("listar", "disponibilidade"):
            return None
        if self.grafo is None:
            return None
        categoria, qualificadores = self.consultor._prefixo_entidade(pedido.alvo)
        if pedido.intencao == "disponibilidade" and categoria not in self.classes:
            return None
        if categoria is None:
            return None
        restricao = " ".join(s for s in (qualificadores, pedido.condicoes) if s)
        try:
            condicoes = (Condicao("tipo_de", categoria),)
            if restricao:
                condicoes += self.consultor._condicoes(restricao)
            if len(condicoes) > MAX_CONDICOES:
                raise ConsultaInvalida("Condições demais")
        except ConsultaInvalida:
            return ("duvida", "Entendi que você quer uma lista, mas não reconheci a condição completa “" +
                    restricao + "”. Pode esclarecer esse critério?", None)
        from consultas_relacionais import PlanoConsulta
        plano = PlanoConsulta(condicoes)
        resultados = self.consultor.executar(plano)
        resultados = [(e, provas) for e, provas in resultados
                      if (e in self.classes) == (pedido.modo == "tipos")]
        if not resultados:
            return ("logica:desconhecido", "Não encontrei " + pedido.modo +
                    " com essas condições na base. Isso não prova que não existam; podem faltar registros.", None)
        exibidos = resultados[:MAX_EXIBIDOS]
        nomes = "; ".join(self.grafo.nomes[e] for e, _ in exibidos)
        linhas = [pedido.modo.capitalize() + " cadastrados de " + self.grafo.nomes[categoria] + ": " + nomes + "."]
        linhas += ["- " + self.grafo.nomes[e] + ": " + "; ".join(p[1] for p in provas) + "."
                   for e, provas in exibidos]
        if len(resultados) > len(exibidos):
            linhas.append("Exibindo {} de {} resultados da base.".format(len(exibidos), len(resultados)))
        linhas.append("Esta lista cobre os registros da base; outros exemplos podem existir fora dela.")
        return "logica:consulta", "\n".join(linhas), tuple(e for e, _ in exibidos)

    def informacoes(self, alvo):
        """Explica relações diretas de uma entidade sem verbete editorial.

        Resolve o alvo inteiro e conserva a direção de cada aresta; nenhuma
        frase é completada por semelhança ou por falta de um fato.
        """
        if self.grafo is None:
            return None
        entidade = self.grafo.aliases.get(limpar(alvo))
        if entidade is None:
            return None
        linhas = []
        for relacao, arestas in self.grafo.arestas.items():
            if relacao == "disjunto_de":
                continue
            for sujeito, objetos in arestas.items():
                for objeto in objetos:
                    if entidade in (sujeito, objeto):
                        linhas.append("- " + self.grafo.nomes[sujeito] + " " +
                                      RELACOES[relacao] + " " + self.grafo.nomes[objeto] + ".")
        if not linhas:
            return None
        resposta = "Fatos cadastrados sobre " + self.grafo.nomes[entidade] + ":\n" + "\n".join(linhas[:12])
        return "logica:fatos", resposta, None

    def retomar(self, pedido, contexto):
        if pedido.intencao != "retomar_item":
            return None
        indice = {"primeiro": 0, "primeira": 0, "segundo": 1, "segunda": 1,
                  "terceiro": 2, "terceira": 2}[pedido.alvo]
        if not contexto or indice >= len(contexto) or self.grafo is None:
            return None
        return self.grafo.nomes[contexto[indice]]
