"""Microcircuito associativo local: atencao ao assunto + memoria factual.

Inspiracao COMPUTACIONAL: associacao por coativacao, competicao lateral e
plasticidade local supervisionada. Nao simula neocortex biologico, nao
compreende linguagem livre e nao infere fatos nao cadastrados. Cada unidade
factual depende de uma fonte verificavel ja presente no compositor.

Os exemplos usados para formar as sinapses sao somente as afirmacoes
editoriais do curriculo, NUNCA as perguntas da prova retida.
"""
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
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

    def assinatura_conhecimento(self):
        """Mudancas nas provas invalidam pesos consolidados anteriormente."""
        dados = [(k[0], k[1], u.aspecto, u.fonte, u.texto)
                 for k, u in sorted(self.unidades.items())]
        bruto = json.dumps(dados, ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(bruto).hexdigest()

    def salvar_ajustes(self, caminho):
        """Persistir plasticidade apenas em arquivo explicitamente indicado."""
        dados = {
            "versao": 1,
            "assinatura_conhecimento": self.assinatura_conhecimento(),
            "sinapses": {"{}:{}".format(c, i): pesos for (c, i), pesos
                         in sorted(self.sinapses.items())}
        }
        Path(caminho).write_text(json.dumps(dados, ensure_ascii=False),
                                 encoding="utf-8")

    def carregar_ajustes(self, caminho):
        """Recusar pesos forjados, fontes diferentes ou pistas novas."""
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
        if (dados.get("versao") != 1 or
                dados.get("assinatura_conhecimento") != self.assinatura_conhecimento() or
                not isinstance(dados.get("sinapses"), dict)):
            raise ValueError("Memoria associativa desatualizada ou sem proveniencia")
        novo = {}
        for (conceito, indice), anterior in self.sinapses.items():
            pesos = dados["sinapses"].get("{}:{}".format(conceito, indice))
            if (not isinstance(pesos, dict) or set(pesos) != set(anterior) or
                    any(type(w) not in (int, float) or not math.isfinite(w) or
                        not 0 <= w <= 1 for w in pesos.values())):
                raise ValueError("Ajuste sinaptico sem provas compativeis")
            novo[(conceito, indice)] = {termo: float(w)
                                       for termo, w in pesos.items()}
        if len(dados["sinapses"]) != len(novo):
            raise ValueError("Pesos extras para unidades nao cadastradas")
        self.sinapses = novo

    def _sujeito_exato(self, consulta):
        """Vincula sujeito por PAPEL na frase, nao por saco de palavras.

        "Como Mercurio orbita o Sol?" fala de Mercurio, ainda que ambos
        sejam entidades conhecidas. Selecionar o primeiro nome do predicado
        principal impede que a mencao secundaria do Sol torne a frase
        ambigua e que uma entidade mencionada no complemento tome o lugar
        do sujeito. Nenhum alias parcial ou aproximado e inventado.
        """
        prefixo = re.match(
            r"^(?:de que modo|como|qual (?:e )?o mecanismo(?: (?:de|do|da))?) "
            r"(?:(?:o|a|os|as|um|uma) )?", consulta)
        if prefixo is None:
            return None
        restante = consulta[prefixo.end():]
        encontrados = []
        for alias, ids in self.aliases.items():
            if len(ids) != 1 or not alias:
                continue
            nome = normalizar(alias)
            if re.match(re.escape(nome) + r"(?:$| )", restante):
                encontrados.append((len(nome.split()), len(nome),
                                    next(iter(ids)), nome))
        if not encontrados:
            # Em "a atmosfera de Venus..." o topico recuperavel e Venus,
            # enquanto "atmosfera" e a PARTE investigada. Exigir um
            # possessivo curto e um alias inequivoco; a parte permanece nas
            # pistas e PRECISA aparecer no fato escolhido. Nunca usar um
            # nome secundario solto como sujeito.
            for alias, ids in self.aliases.items():
                if len(ids) != 1 or not alias:
                    continue
                nome = normalizar(alias)
                propriedade = re.match(
                    r"^([a-z0-9]+(?: [a-z0-9]+){0,3}) "
                    r"(?:de|do|da|dos|das) " + re.escape(nome) + r"(?:$| )",
                    restante)
                if propriedade is None:
                    continue
                parte = propriedade.group(1)
                if re.search(r"\b(?:e|ou|com|sem|nao)\b", parte):
                    continue
                # A parte tambem deve ser conhecimento efetivamente
                # presente em ao menos um fato tipado desse proprietario.
                pistas_parte = self.tokenizador(parte)
                if not pistas_parte or not any(
                    u.conceito == next(iter(ids)) and
                    all(p in self.sinapses[(u.conceito, u.indice)]
                        for p in pistas_parte)
                    for u in self.unidades.values()
                ):
                    continue
                encontrados.append((len(nome.split()), len(nome),
                                    next(iter(ids)), nome))
        if not encontrados:
            return None
        encontrados.sort(reverse=True)
        mais_longo = (encontrados[0][0], encontrados[0][1])
        unicos = {(ident, nome) for tokens_nome, tamanho, ident, nome
                  in encontrados if (tokens_nome, tamanho) == mais_longo}
        if len(unicos) != 1:
            return None
        conceito, alias = next(iter(unicos))
        fim_sujeito = re.search(r"(?<![a-z0-9])" + re.escape(alias) +
                                r"(?![a-z0-9])", restante)
        depois = restante[fim_sujeito.end():].strip()
        # Dois nomes unidos no sujeito sao comparacao/relacao, nao
        # recuperacao de um unico fato individual. O controle por palavras
        # desconhecidas continua atuando no predicado inteiro.
        if re.match(r"^(?:e|ou|com) (?:o |a |os |as )?", depois):
            return None
        return conceito, alias

    def associar(self, pergunta, min_cobertura=.66, min_margem=.12):
        """Recuperacao EXPLICAVEL sob alto limiar, nunca inferencia causal.

        Nomes inteiros fixam o assunto. Os outros termos ativam sinapses
        de fatos do MESMO assunto. Se duas unidades empatam ou faltam
        caracteristicas distintivas, nao fornece resposta.
        """
        consulta = normalizar(pergunta)
        if len(consulta) > 320 or not re.match(
                r"^(?:como |de que modo |qual (?:e )?o mecanismo(?: (?:de|do|da))? )", consulta):
            return None
        if re.search(r"\b(nao|nunca|jamais|nem|sem|exceto|se|supondo|imaginando|"
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
                 "mecanismo", "explica", "ocorre", "ocorrem", "isso",
                 "pelo", "pela", "pelos", "pelas", "via", "sob", "ate",
                 "entre", "atraves", "num", "numa", "sobre",
                 "devido", "devida", "devidos", "devidas"}
        # Filtrar palavras funcionais ANTES da reducao morfologica:
        # "através" pode virar "atrave" no tokenizador; nao e um
        # qualificador novo nem deve diluir a evidencia recuperada.
        pistas = {token for palavra in sem_entidade.split() if palavra not in ruido
                  for token in self.tokenizador(palavra) if token not in ruido}
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
        # Nao descartar silenciosamente um QUALIFICADOR preso ao fato.
        # "pulsos luminosos" e "pulsos magicos" nao sao a mesma
        # afirmacao. Um termo aberto colado a uma pista comprovada nao
        # pode receber evidencias de outra propriedade apenas porque
        # as demais palavras coincidem. Operadores e preposicoes separam
        # sintagmas; verbos livres ANTES da entidade nao criam um fato.
        palavras = sem_entidade.split()
        sinapses_vencedoras = self.sinapses[chave]
        for anterior, atual in zip(palavras, palavras[1:]):
            antes = self.tokenizador(anterior)
            depois = self.tokenizador(atual)
            if (len(antes) == len(depois) == 1 and
                    antes[0] in sinapses_vencedoras and
                    depois[0] not in sinapses_vencedoras and
                    atual not in ruido and depois[0] not in ruido):
                return None
        unidade = self.unidades[chave]
        return Ativacao(conceito, unidade.indice, round(vencedor, 4),
                        round(rival, 4), tuple(sorted(presentes)), unidade.fonte)
