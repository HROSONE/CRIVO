"""Interpretação transversal restrita: intenção + entidades + provas.

Não consulta redes externas, não adiciona fatos e não reaproveita uma
semelhança lexical como prova. O grafo de relações é a única fonte
de evidência para perguntas estruturadas neste módulo.
"""
import re

from raciocinio import limpar


NEGACOES = re.compile(r"\b(nao|nunca|jamais|sem)\b")
ARTIGO = r"(?:o|a|os|as|um|uma|uns|umas)\s+"


def preparar_elipse_definicional(texto, contexto):
    """Transforma 'E o CSS?' em pergunta definicional SOMENTE se havia
    uma definição comprovadamente respondida no turno imediatamente anterior.

    Não remove modificadores nem presume semelhança entre conceitos.
    O chamador precisa procurar a resposta na própria base.
    """
    if contexto != "definicao":
        return None
    n = limpar(texto)
    m = re.fullmatch(r"e\s+(?:" + ARTIGO + r")?(.+)", n)
    if m is None:
        return None
    alvo = m.group(1).strip()
    if (not alvo or len(alvo) > 85 or
            NEGACOES.search(alvo) or
            re.search(r"\b(como|quando|porque|por que|qual|quais|quem|"
                      r"onde|quanto|melhor|mais|devo|posso|pode|tem|e|sao)\b",
                      alvo)):
        return None
    if len(alvo.split()) > 5:
        return None
    return "o que e " + alvo + "?"


class InterpretadorGeral:
    """Relações estruturadas independentes de assunto e sem resposta pré-pronta."""

    def __init__(self, grafo):
        self.grafo = grafo

    @staticmethod
    def _alvos(texto):
        n = limpar(texto)
        if NEGACOES.search(n) or n.startswith(("se ", "suponha ", "imagine ")):
            return None
        padroes = (
            ("comum", r"(?:o )?que (.+?) e (.+?) (?:tem|possuem) em comum"),
            ("comum", r"(?:qual (?:e )?a |que )?semelhanca entre (.+?) e (.+)"),
            ("ligacao", r"qual (?:e )?a relacao entre (.+?) e (.+)"),
            ("ligacao", r"como (.+?) se relaciona com (.+)"),
        )
        for modo, padrao in padroes:
            m = re.fullmatch(padrao, n)
            if m:
                return modo, m.group(1), m.group(2)
        return None

    def interpretar(self, pergunta):
        """Retorna (ID, resposta) ou None, sem inferência por ausência."""
        if self.grafo is None:
            return None
        parse = self._alvos(pergunta)
        if parse is None:
            return None
        modo, nome_a, nome_b = parse
        g = self.grafo
        a = g.aliases.get(limpar(nome_a))
        b = g.aliases.get(limpar(nome_b))
        # A presença de um termo aproximado na base textual não qualifica
        # uma nova entidade; a forma inteira deve ser um alias único.
        if not a or not b or a == b:
            return None

        if modo == "comum":
            caminhos_a = g._ancestrais_com_caminho(a)
            caminhos_b = g._ancestrais_com_caminho(b)
            mapa_b = {ident: caminho for ident, caminho in caminhos_b}
            candidatos = [(len(ca) + len(mapa_b[ident]), ca, mapa_b[ident])
                          for ident, ca in caminhos_a if ident in mapa_b]
            if not candidatos:
                return ("logica:sem_ligacao",
                        "Não encontrei uma classe comum para " + g.nomes[a] +
                        " e " + g.nomes[b] +
                        " nas relações cadastradas. Isso não prova que "
                        "não exista alguma semelhança.")
            _, ca, cb = min(candidatos, key=lambda x: x[0])
            nome_classe = g.nomes[ca[-1]]
            passos_a = " → ".join(g.nomes[n] for n in ca)
            passos_b = " → ".join(g.nomes[n] for n in cb)
            return ("logica:comum",
                    "Uma classificação comum registrada é " + nome_classe +
                    ". Provas: " + passos_a + "; " + passos_b +
                    ". Isso se baseia somente nas relações cadastradas.")

        # Uma relação direcional pode ser lida em qualquer ordem.
        # tipo_de e parte_de são transitivas; orbita é somente direta.
        # tem_caracteristica só herda pela taxonomia autorizada.
        for origem, destino in ((a, b), (b, a)):
            for tipo in ("tipo_de", "parte_de", "orbita", "tem_caracteristica"):
                caminho = g.provar(origem, destino, tipo)
                if caminho is None:
                    continue
                if tipo == "tipo_de":
                    texto = " → ".join(g.nomes[e] for e in caminho)
                    nome = "classificação"
                elif tipo == "parte_de":
                    texto = " → ".join(g.nomes[e] for e in caminho)
                    nome = "composição"
                elif tipo == "orbita":
                    texto = g.nomes[caminho[0]] + " --orbita--> " + g.nomes[caminho[1]]
                    nome = "órbita direta"
                else:
                    partes = []
                    for posicao, entidade in enumerate(caminho[1:], 1):
                        tipo_passo = ("tem_caracteristica"
                                     if posicao == len(caminho) - 1 else "tipo_de")
                        partes.append("--" + tipo_passo + "--> " + g.nomes[entidade])
                    texto = g.nomes[caminho[0]] + " " + " ".join(partes)
                    nome = "herança de propriedade"
                return ("logica:ligacao",
                        "Uma relação comprovável entre " + g.nomes[a] +
                        " e " + g.nomes[b] + " é " + nome + ": " + texto +
                        ". Cada etapa está cadastrada no grafo.")

        prova = g.provar_incompatibilidade(a, b)
        if prova is not None:
            ca, cb, _ = prova
            return ("logica:ligacao",
                    "Há incompatibilidade explícita entre classes: " +
                    " → ".join(g.nomes[e] for e in ca) +
                    " é disjunto de " + " → ".join(g.nomes[e] for e in cb) +
                    ". Isso é uma relação cadastrada, não dedução pela ausência.")

        return ("logica:sem_ligacao",
                "Não encontrei ligação comprovável cadastrada entre " +
                g.nomes[a] + " e " + g.nomes[b] +
                ". Isso não prova que não exista uma relação.")
