"""Raciocínio relacional determinístico: deduz cadeias, sem LLM ou API.

Apenas dois tipos de relação são transitivos quando cadastrados:
* tipo_de: pinguim -> ave -> vertebrado -> animal
* parte_de: Terra -> Sistema Solar -> Via Láctea

Um caminho afirmativo é demonstrável; a ausência de caminho NÃO prova uma
negação. O módulo só aceita fatos estruturados sob curadoria, não frases livres.
"""
import json
import re
import unicodedata
from collections import deque
from pathlib import Path


RELACOES = {
    "tipo_de": "é um tipo de", "parte_de": "faz parte de",
    "tem_caracteristica": "tem como característica", "orbita": "orbita",
}
TRANSITIVAS = frozenset(("tipo_de", "parte_de"))
ARTIGO = re.compile(r"^(?:o|a|os|as|um|uma|uns|umas)\s+")


def limpar(texto):
    """Normalização mínima que mantém a ordem de palavras e os termos."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9_\s-]", " ", texto)
    texto = " ".join(texto.split())
    return ARTIGO.sub("", texto)


class GrafoRaciocinio:
    """Motor genérico com caminhos explicáveis e sem conclusão por ausência."""

    def __init__(self, dados):
        if not isinstance(dados, dict) or dados.get("versao") != 1:
            raise ValueError("Versão inválida para as relações")
        entidades = dados.get("entidades")
        fatos = dados.get("fatos")
        if (not isinstance(entidades, dict) or not isinstance(fatos, list)
                or len(entidades) > 2048 or len(fatos) > 8192):
            raise ValueError("Entidades ou fatos inválidos")
        self.nomes = {}
        self.aliases = {}
        self.arestas = {r: {} for r in RELACOES}
        for ident, entidade in entidades.items():
            if (not isinstance(ident, str) or
                    not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", ident) or
                    not isinstance(entidade, dict) or
                    not isinstance(entidade.get("nome"), str) or
                    not entidade["nome"].strip()):
                raise ValueError("Entidade malformada")
            self.nomes[ident] = entidade["nome"]
            palavras = [ident.replace("_", " "), entidade["nome"]]
            apelidos = entidade.get("aliases", [])
            if not isinstance(apelidos, list) or not all(isinstance(a, str) for a in apelidos):
                raise ValueError("Aliases inválidos")
            for palavra in palavras + apelidos:
                chave = limpar(palavra)
                if not chave or (chave in self.aliases and self.aliases[chave] != ident):
                    raise ValueError("Alias ambíguo: " + palavra)
                self.aliases[chave] = ident
        vistos = set()
        for fato in fatos:
            if (not isinstance(fato, dict) or
                    fato.get("relacao") not in RELACOES or
                    fato.get("sujeito") not in entidades or
                    fato.get("objeto") not in entidades):
                raise ValueError("Relação malformada ou entidade desconhecida")
            s, r, o = fato["sujeito"], fato["relacao"], fato["objeto"]
            if s == o or (s, r, o) in vistos:
                raise ValueError("Relação redundante ou reflexiva")
            # Propriedades não são superclasses nem objetos orbitados.
            propriedade_s = entidades[s].get("tipo") == "caracteristica"
            propriedade_o = entidades[o].get("tipo") == "caracteristica"
            if (r == "tem_caracteristica" and (propriedade_s or not propriedade_o)):
                raise ValueError("Destino de tem_caracteristica deve ser caracteristica")
            if r != "tem_caracteristica" and (propriedade_s or propriedade_o):
                raise ValueError("caracteristica nao pode ser tipo_de, parte_de ou orbita")
            # Somente relações transitivas requerem teste de ciclo.
            if r in TRANSITIVAS and self.provar(o, s, r):
                raise ValueError("Ciclo detectado na relação " + r)
            vistos.add((s, r, o))
            self.arestas[r].setdefault(s, []).append(o)

    @classmethod
    def carregar(cls, caminho):
        with Path(caminho).open(encoding="utf-8") as arquivo:
            return cls(json.load(arquivo))

    def provar(self, origem, destino, relacao):
        """Prova estruturada ou None. Ausência de prova não significa falsidade."""
        if relacao not in RELACOES:
            raise ValueError("Tipo de relação desconhecido")
        if origem not in self.nomes or destino not in self.nomes:
            return None
        if relacao == "tem_caracteristica":
            return self.provar_caracteristica(origem, destino)
        if relacao not in TRANSITIVAS:
            # Orbitar não é transitivo: Lua->Terra e Terra->Sol não
            # autorizam inferir uma aresta Lua->Sol neste tipo de dado.
            return ([origem, destino] if destino in self.arestas[relacao].get(
                origem, ()) else None)
        fila = deque([(origem, [origem])])
        vistos = {origem}
        while fila:
            atual, caminho = fila.popleft()
            for seguinte in self.arestas[relacao].get(atual, ()):
                if seguinte == destino:
                    return caminho + [seguinte]
                if seguinte not in vistos:
                    vistos.add(seguinte)
                    fila.append((seguinte, caminho + [seguinte]))
        return None

    def provar_caracteristica(self, origem, propriedade):
        """Herda somente propriedades afirmadas para a própria classe.

        Derivação autorizada: X tipo_de* Classe; Classe
        tem_caracteristica Propriedade. Não faz composição arbitrária
        de propriedades, relações orbitais ou parte_de.
        """
        if origem not in self.nomes or propriedade not in self.nomes:
            return None
        fila = deque([(origem, [origem])])
        vistos = {origem}
        while fila:
            classe, caminho = fila.popleft()
            if propriedade in self.arestas["tem_caracteristica"].get(classe, ()):
                return caminho + [propriedade]
            for superior in self.arestas["tipo_de"].get(classe, ()):
                if superior not in vistos:
                    vistos.add(superior)
                    fila.append((superior, caminho + [superior]))
        return None

    @staticmethod
    def _proposicao_hipotetica(texto):
        """Lê somente `X é Y` (sem negação), não extrai fatos de texto livre."""
        n = limpar(texto)
        n = re.sub(r"^(?:todo|toda|todos|todas)\s+", "", n)
        n = limpar(n)
        m = re.fullmatch(r"(.+?)\s+(?:e|eh)\s+(?:(?:um|uma|tipo de)\s+)?(.+)", n)
        if not m:
            return None
        x, y = limpar(m.group(1)), limpar(m.group(2))
        if not x or not y or len(x) > 80 or len(y) > 80:
            return None
        return x, y

    def interpretar_hipotese(self, pergunta):
        """Dedução nova a partir de duas premissas informadas no mesmo turno.

        Formato deliberadamente limitado: 'Se A é B, B é C, então A é C?'.
        Não grava as premissas no conhecimento nem as trata como verdades.
        """
        n = unicodedata.normalize("NFD", pergunta.lower())
        n = "".join(c for c in n if unicodedata.category(c) != "Mn")
        n = " ".join(n.strip().rstrip("?!.").split())
        if not n.startswith("se ") or re.search(r"\b(nao|nunca|jamais)\b", n):
            return None
        partes = re.split(r"\s*[,;]\s*", n)
        if len(partes) != 3:
            return None
        partes[0] = partes[0][3:]
        partes[2] = re.sub(r"^entao\s+", "", partes[2])
        proposicoes = [self._proposicao_hipotetica(p) for p in partes]
        if any(p is None for p in proposicoes):
            return None
        p1, p2, pergunta_final = proposicoes
        termos = sorted(set(p1 + p2 + pergunta_final))
        entidades = {"hip_%d" % i: {"nome": palavra}
                    for i, palavra in enumerate(termos)}
        ids = {palavra: "hip_%d" % i for i, palavra in enumerate(termos)}
        fatos = [{"sujeito": ids[x], "relacao": "tipo_de", "objeto": ids[y]}
                 for x, y in (p1, p2)]
        try:
            assumido = GrafoRaciocinio({"versao": 1, "entidades": entidades,
                                        "fatos": fatos})
        except ValueError:
            return ("logica:hipotese_indeterminada",
                    "Não consigo aplicar essas premissas como uma cadeia válida.")
        caminho = assumido.provar(ids[pergunta_final[0]],
                                  ids[pergunta_final[1]], "tipo_de")
        if caminho:
            passos = " → ".join(assumido.nomes[etapa] for etapa in caminho)
            return ("logica:hipotese",
                    "Sim, somente se assumirmos as premissas informadas: " +
                    passos + ". Isso não comprova que as premissas sejam reais.")
        return ("logica:hipotese_indeterminada",
                "Essa conclusão não decorre das duas premissas informadas. "
                "Isso não comprova que ela seja falsa.")

    def interpretar(self, pergunta):
        """Responde a relações conhecidas e hipóteses estruturadas."""
        hipotese = self.interpretar_hipotese(pergunta)
        if hipotese is not None:
            return hipotese
        n = limpar(pergunta)
        if re.search(r"\b(nao|nunca|jamais|sem)\b", n):
            return None
        n = re.sub(r"^(?:por que|como sabemos que)\s+", "", n)
        relacao = None
        m = re.fullmatch(r"(.+?)\s+(?:tem|possui|apresenta)\s+(?:(?:um|uma|o|a|os|as)\s+)?(.+)", n)
        if m:
            relacao = "tem_caracteristica"
        else:
            m = re.fullmatch(
                r"(.+?)\s+(?:orbita|gira em torno (?:de|da|do|dos|das))\s+(.+)", n)
            if m:
                relacao = "orbita"
            else:
                m = re.fullmatch(
                    r"(.+?)\s+(?:faz parte|e parte)\s+(?:de|da|do|dos|das)\s+(.+)", n)
                if m:
                    relacao = "parte_de"
                else:
                    m = re.fullmatch(
                        r"(.+?)\s+(?:e|eh)\s+(?:um|uma|tipo de|uma especie de)?\s*(.+)", n)
                    if m:
                        relacao = "tipo_de"
        if not m:
            return None
        sujeito = self.aliases.get(limpar(m.group(1)))
        objeto = self.aliases.get(limpar(m.group(2)))
        # Não captura toda pergunta geral parecida com "é": exige dois
        # nomes identificados no grafo para evitar distorcer o recuperador.
        if not sujeito or not objeto:
            return None
        cadeia = self.provar(sujeito, objeto, relacao)
        if cadeia:
            if relacao == "tem_caracteristica":
                passos = self.nomes[cadeia[0]]
                for posicao, identificador in enumerate(cadeia[1:], 1):
                    aresta = ("tem_caracteristica" if posicao == len(cadeia)-1
                              else "tipo_de")
                    passos += " --" + aresta + "--> " + self.nomes[identificador]
            elif relacao == "orbita":
                passos = self.nomes[cadeia[0]] + " --orbita--> " + self.nomes[cadeia[1]]
            else:
                passos = " → ".join(self.nomes[e] for e in cadeia)
            return ("logica:" + relacao,
                    "Sim. Consigo concluir isso pelas relações cadastradas: " +
                    passos + ".")
        return ("logica:desconhecido",
                "Não tenho uma relação afirmativa cadastrada que permita "
                "concluir isso. Isso não significa que a afirmação seja falsa.")

