"""Microcircuito associativo local: atencao ao assunto + memoria factual.

Inspiracao COMPUTACIONAL: associacao por coativacao, competicao lateral e
plasticidade local supervisionada. Nao simula neocortex biologico, nao
compreende linguagem livre e nao infere fatos nao cadastrados. Cada unidade
factual depende de uma fonte verificavel ja presente no compositor.

Os exemplos usados para formar as sinapses sao somente as afirmacoes
editoriais do curriculo, NUNCA as perguntas da prova retida.
"""
import math
import re
import unicodedata
from collections import Counter
from typing import NamedTuple


def normalizar(texto):
    s = unicodedata.normalize("NFD", texto.casefold())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return " ".join(re.findall(r"[a-z0-9]+", s))


class LembrancaFactual(NamedTuple):
    conceito: str
    indice: int
    aspecto: str
    fonte: str
    texto: str


class Ativacao(NamedTuple):
    conceito: str
    indice: int
    potencia: float
    concorrente: float
    pistas: tuple
    fonte: str


class CortexAssociativo:
    """Associacao local sem modelos externos nem autoaprendizado por chat.

    Os fatos sao representados por unidades individuais. Cada unidade
    recebe sinapses de palavras presentes em uma fonte aprovada. Uma
    correção supervisionada pode fortalecer/enfraquecer sinapses *locais*
    sem reescrever as outras unidades, mas a interface do usuario nao
    recebe permissão de consolidar automaticamente um fato.
    """

    def __init__(self, itens, aliases, fontes, tokenizador):
        self.itens = itens
        self.aliases = aliases
        self.fontes = fontes
        self.tokenizador = tokenizador
        self.unidades = {}
        self.sinapses = {}
        document_freq = Counter()
        for conceito, item in itens.items():
            for i, fato in enumerate(item["fatos"]):
                fonte = fato.get("fonte")
                if fonte not in fontes:
                    continue
                # Apenas evidencias de mecanismo e formacao. Nao tentar
                # apresentar uma definicao ou limite como resposta causal.
                aspecto = fato.get("aspecto")
                if aspecto not in ("funcionamento", "formacao"):
                    continue
                evidencias = set(tokenizador(fato["texto"]))
                if not evidencias:
                    continue
                chave = (conceito, i)
                self.unidades[chave] = LembrancaFactual(
                    conceito, i, aspecto, fonte, fato["texto"])
                document_freq.update(evidencias)
                self.sinapses[chave] = {t: 0.0 for t in evidencias}
        self.idf = {t: 1.0 + math.log((1 + len(self.unidades))/(1 + f))
                    for t, f in document_freq.items()}
        for chave, pesos in self.sinapses.items():
            self._potenciar(chave, pesos.keys(), intensidade=.40, repeticoes=4)

    def _potenciar(self, chave, pistas, intensidade, repeticoes=1):
        """Coativacao local saturante: w <- w + eta*(1-w)."""
        for _ in range(repeticoes):
            for termo in pistas:
                antigo = self.sinapses[chave].get(termo, 0.0)
                self.sinapses[chave][termo] = antigo + intensidade * (1.0 - antigo)

    def ajustar_com_prova(self, conceito, indice, pistas, correto, autorizado=False):
        """Plasticidade por erro, bloqueada sem revisao/rotulacao confiavel."""
        chave = (conceito, indice)
        if not autorizado or chave not in self.unidades or type(correto) is not bool:
            raise ValueError("Ajuste sinaptico exige fonte registrada e revisao explicita")
        pistas = set(self.tokenizador(pistas))
        if not pistas:
            raise ValueError("Sem sinal de aprendizagem")
        # Rejeitar pistas novas que nao constem da evidencia: aprender
        # apenas a discriminacao entre atributos ja verificaveis.
        if not pistas <= set(self.sinapses[chave]):
            raise ValueError("Pistas fora do texto-fonte nao viram novas verdades")
        if correto:
            self._potenciar(chave, pistas, intensidade=.30)
        else:
            for termo in pistas:
                self.sinapses[chave][termo] *= .60

    def _sujeito_exato(self, consulta):
        """Atencao: um unico referente literal, sem supor sinonimos."""
        encontrados = []
        for alias, ids in self.aliases.items():
            if len(ids) != 1 or not alias:
                continue
            alvo = re.search(r"(?<![a-z0-9])" + re.escape(normalizar(alias)) +
                             r"(?![a-z0-9])", consulta)
            if alvo:
                encontrados.append((len(alias), next(iter(ids)), alvo.group()))
        if not encontrados:
            return None
        conceitos = {c for _, c, _ in encontrados}
        if len(conceitos) > 1:
            return None
        return max(encontrados)[1:]

    def associar(self, pergunta, min_cobertura=.66, min_margem=.12):
        """Recuperacao EXPLICAVEL sob alto limiar, nunca inferencia causal.

        Nomes inteiros fixam o assunto. Os outros termos ativam sinapses
        de fatos do MESMO assunto. Se duas unidades empatam ou faltam
        caracteristicas distintivas, nao fornece resposta.
        """
        consulta = normalizar(pergunta)
        if len(consulta) > 320 or not re.match(
                r"^(?:como |de que modo |qual (?:e )?o mecanismo )", consulta):
            return None
        if re.search(r"\b(nao|nunca|jamais|nem|se|supondo|imaginando|"
                     r"fictici[oa]|inventad[oa]|hipotetic[oa]|"
                     r"dosagem|dose|medicamento)\b", consulta):
            return None
        sujeito = self._sujeito_exato(consulta)
        if sujeito is None:
            return None
        conceito, alias = sujeito
        sem_entidade = re.sub(r"(?<![a-z0-9])" + re.escape(alias) +
                             r"(?![a-z0-9])", " ", consulta, count=1)
        formacao = bool(re.search(
            r"\b(formar|forma|formam|formacao|origem|originou|surgiu|"
            r"surge|nasce|nascer|criou|criar|geracao|gerou)\b", sem_entidade))
        aspecto = "formacao" if formacao else "funcionamento"
        ruido = {"como", "de", "que", "modo", "qual", "e", "o", "a", "os", "as",
                 "um", "uma", "do", "da", "dos", "das", "no", "na", "nos", "nas",
                 "ao", "aos", "para", "por", "porque", "me", "pode", "faz",
                 "acontece", "funciona", "funcionamento", "sistema", "processo",
                 "mecanismo", "explica", "ocorre", "ocorrem", "isso"}
        pistas = set(self.tokenizador(sem_entidade)) - ruido
        # Pergunta só com assunto e verbo generico pertence ao compositor
        # tradicional, que conhece o aspecto tipado.
        if len(pistas) < 2 or len(pistas) > 12:
            return None
        denominador = sum(self.idf.get(t, 2.) for t in pistas)
        concorrentes = []
        for chave, unidade in self.unidades.items():
            if unidade.conceito != conceito or unidade.aspecto != aspecto:
                continue
            pesos = self.sinapses[chave]
            presentes = [t for t in pistas if pesos.get(t, 0.0) > .3]
            if len(presentes) < 2:
                continue
            # Similaridade ponderada pela prova presente, nao pelo numero
            # de palavras de assunto que seriam compartilhadas por todos.
            ativacao = sum(self.idf.get(t, 2.)*pesos[t] for t in presentes)
            cobertura = ativacao / denominador if denominador else 0.0
            concorrentes.append((cobertura, chave, presentes))
        concorrentes.sort(reverse=True)
        if not concorrentes:
            return None
        vencedor, chave, presentes = concorrentes[0]
        rival = concorrentes[1][0] if len(concorrentes) > 1 else 0.0
        if vencedor < min_cobertura or vencedor - rival < min_margem:
            return None
        unidade = self.unidades[chave]
        return Ativacao(conceito, unidade.indice, round(vencedor, 4),
                        round(rival, 4), tuple(sorted(presentes)), unidade.fonte)
