"""Raciocínio relacional determinístico: deduz cadeias, sem LLM ou API.

Dois tipos de relação podem ser transitivos quando cadastrados:
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


RELACOES = {"tipo_de": "é um tipo de", "parte_de": "faz parte de"}
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
            if self.provar(o, s, r):
                raise ValueError("Ciclo detectado na relação " + r)
            vistos.add((s, r, o))
            self.arestas[r].setdefault(s, []).append(o)

    @classmethod
    def carregar(cls, caminho):
        with Path(caminho).open(encoding="utf-8") as arquivo:
            return cls(json.load(arquivo))

    def provar(self, origem, destino, relacao):
        """Menor cadeia entre entidades. Sem caminho => desconhecido, não falso."""
        if relacao not in RELACOES:
            raise ValueError("Tipo de relação desconhecido")
        if origem not in self.nomes or destino not in self.nomes:
            return None
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

    def interpretar(self, pergunta):
        """Responde somente a perguntas binárias de relações conhecidas."""
        n = limpar(pergunta)
        if re.search(r"\b(nao|nunca|jamais|sem)\b", n):
            return None
        n = re.sub(r"^(?:por que|como sabemos que)\s+", "", n)
        relacao = None
        m = re.fullmatch(r"(.+?)\s+(?:faz parte|e parte)\s+(?:de|da|do|dos|das)\s+(.+)", n)
        if m:
            relacao = "parte_de"
        else:
            m = re.fullmatch(r"(.+?)\s+(?:e|eh)\s+(?:um|uma|tipo de|uma especie de)?\s*(.+)", n)
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
            passos = " → ".join(self.nomes[e] for e in cadeia)
            return ("logica:" + relacao,
                    "Sim. Consigo concluir isso pelas relações cadastradas: " +
                    passos + ".")
        return ("logica:desconhecido",
                "Não tenho uma relação afirmativa cadastrada que permita "
                "concluir isso. Isso não significa que a afirmação seja falsa.")

