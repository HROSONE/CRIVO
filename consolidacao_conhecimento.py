"""Consolidacao factual: recuperacao semantica + encadeamento explicavel.

Esta camada nao cria fatos. Ela procura unidades editoriais ja cadastradas,
usa aliases unicos para fixar os assuntos e, quando existe ligacao textual
explicita entre conceitos, pode encadear no maximo um segundo fato.

Objetivos:
* recuperar o mesmo conhecimento sob parafrases;
* usar papeis/aspectos (definicao, causa, funcionamento, formacao, limite);
* combinar evidencias sem transformar ausencia em negacao;
* preservar proveniencia: o compositor continua exibindo apenas frases
  existentes no curriculo e suas fontes.

Nao e uma LLM e nao aprende com perguntas do usuario.
"""
import math
import re
import unicodedata
from collections import Counter
from typing import NamedTuple


def normalizar(texto):
    s = unicodedata.normalize("NFD", texto.casefold())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(re.findall(r"[a-z0-9]+", s))


# Grupos LINGUISTICOS gerais. Nenhum nome de planeta, pessoa ou resposta
# especifica aparece aqui. Eles servem para aproximar parafrases comuns.
GRUPOS_SEMANTICOS = (
    frozenset(("quente", "calor", "temperatura", "aquecimento", "aquecer")),
    frozenset(("frio", "gelado", "temperatura", "resfriamento", "resfriar")),
    frozenset(("vermelho", "avermelhado", "avermelhada", "vermelha", "vermelho")),
    frozenset(("azul", "azulada", "azulado", "coloracao", "cor")),
    frozenset(("manter", "mantem", "reter", "retendo", "conservar", "preservar")),
    frozenset(("formar", "formacao", "origem", "originar", "surgir", "nascer", "gerar")),
    frozenset(("causa", "causar", "provocar", "produzir", "gerar", "explicar", "motivo", "razao")),
    frozenset(("orbita", "orbitar", "orbitando", "revolucao", "girar", "circulacao")),
    frozenset(("inclinacao", "inclinado", "inclinada", "eixo")),
    frozenset(("estacao", "estacoes", "sazonal", "sazonais", "sazonalidade")),
    frozenset(("campo", "magnetico", "magnetica", "magnetismo")),
    frozenset(("evidencia", "evidencias", "sinal", "sinais", "indicio", "indicios")),
    frozenset(("limite", "limites", "limitacao", "limitacoes", "incerteza", "incertezas")),
    frozenset(("maior", "superior", "mais")),
    frozenset(("menor", "inferior", "menos")),
)


RUIDO = frozenset((
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da",
    "dos", "das", "em", "no", "na", "nos", "nas", "por", "para", "pra",
    "com", "sem", "e", "ou", "que", "qual", "quais", "quem", "como",
    "onde", "quando", "quanto", "me", "te", "se", "ao", "aos", "ser",
    "sao", "eh", "foi", "tem", "ter", "isso", "isto", "esse", "essa",
    "eu", "voce", "vc", "pode", "poderia", "consegue", "diga", "dizer",
    "explique", "explica", "fale", "falar", "conte", "sobre", "favor",
    "gentileza", "nosso", "nossa", "seu", "sua", "seus", "suas",
    "muito", "tanto", "mesmo", "tambem", "ainda", "exatamente",
    "precisamente", "precisao", "correto", "correta", "astronomia",
    "astronomico", "astronomica", "fisica", "espacial", "astro",
    "objeto", "termo", "conceito", "modo", "maneira", "jeito",
    "processo", "mecanismo", "funciona", "funcionam", "acontece",
    "ocorre", "ocorrem", "completa", "completar", "descreva", "descrever",
))

BLOQUEIOS = re.compile(
    r"\b(?:nao|nunca|jamais|nem|exceto|suponha|supondo|imagine|imaginando|"
    r"hipotetic[oa]|fictici[oa]|inventad[oa]|magic[oa]|diagnostico|"
    r"diagnostique|dosagem|dose|remedio|medicamento)\b"
)


class Unidade(NamedTuple):
    conceito: str
    indice: int
    papel: str
    aspecto: str
    texto: str
    tokens: frozenset
    mencoes: tuple


class PlanoConsolidacao(NamedTuple):
    intencao: str
    temas: tuple
    selecionados: tuple
    pontuacao: float
    provas: tuple


class ConsolidadorConhecimento:
    """Recuperador conservador sobre TODAS as fichas do compositor."""

    def __init__(self, itens, aliases, tokenizador):
        self.itens = itens
        self.tokenizador = tokenizador

        self.aliases = []
        for alias, ids in aliases.items():
            if len(ids) == 1 and alias:
                self.aliases.append((normalizar(alias), next(iter(ids))))
        # Nomes longos primeiro para "sistema solar" vencer "solar".
        self.aliases.sort(key=lambda x: (-len(x[0].split()), -len(x[0]), x[0]))

        unidades_brutas = []
        df = Counter()
        for conceito, item in itens.items():
            nomes = [item.get("nome", "")] + list(item.get("aliases", []))
            tokens_nome = set()
            for nome in nomes:
                tokens_nome.update(self._expandir(self.tokenizador(nome)))
            for indice, fato in enumerate(item.get("fatos", [])):
                texto = fato.get("texto", "")
                if not texto.strip():
                    continue
                base = set(self._expandir(self.tokenizador(texto))) | tokens_nome
                if not base:
                    continue
                mencoes = tuple(e for e in self._entidades(texto) if e != conceito)
                unidade = Unidade(
                    conceito, indice, fato.get("papel", "detalhe"),
                    fato.get("aspecto", ""), texto, frozenset(base), mencoes)
                unidades_brutas.append(unidade)
                df.update(set(base))

        self.unidades = tuple(unidades_brutas)
        total = max(1, len(self.unidades))
        self.idf = {t: 1.0 + math.log((1 + total) / (1 + f))
                    for t, f in df.items()}

    @staticmethod
    def _expandir(tokens):
        saida = set(tokens)
        alterou = True
        while alterou:
            alterou = False
            for grupo in GRUPOS_SEMANTICOS:
                if saida & grupo and not grupo <= saida:
                    saida.update(grupo)
                    alterou = True
        return saida

    def _entidades(self, texto):
        n = normalizar(texto)
        encontrados = []
        for alias, ident in self.aliases:
            for m in re.finditer(r"(?<![a-z0-9])" + re.escape(alias) +
                                 r"(?![a-z0-9])", n):
                encontrados.append((m.start(), m.end(), alias, ident))
        # Remove aliases menores que ocupem o mesmo trecho.
        escolhidos = []
        for inicio, fim, alias, ident in sorted(
                encontrados, key=lambda x: (-(x[1]-x[0]), x[0])):
            if any(not (fim <= a or inicio >= b) for a, b, _, _ in escolhidos):
                continue
            escolhidos.append((inicio, fim, alias, ident))
        escolhidos.sort()
        return tuple(dict.fromkeys(e[3] for e in escolhidos))

    @staticmethod
    def _intencao(texto):
        n = normalizar(texto)
        if re.search(r"\b(?:defina|definir|definicao|significa|significado|"
                     r"quer dizer|vem a ser|descreva|descrever)\b", n) or                 re.match(r"^(?:o que e|o que sao|que objeto e|como se define)\b", n):
            return "definicao"
        if re.search(r"\b(?:evidencia|evidencias|como sabemos|que sinais|indicios)\b", n):
            return "evidencia"
        if re.search(r"\b(?:limite|limites|limitacao|limitacoes|incerteza|incertezas)\b", n):
            return "limite"
        if re.search(r"\b(?:diferenca|compare|comparar|mais .+ que|menos .+ que|"
                     r"maior que|menor que|superior|inferior)\b", n):
            return "comparacao"
        if re.search(r"\b(?:origem|formacao|formou|formaram|surgiu|surgiram|"
                     r"nasceu|nasceram|veio|vieram)\b", n):
            return "formacao"
        if re.match(r"^(?:por que|porque|qual (?:e )?(?:o )?motivo|"
                    r"qual (?:e )?(?:a )?razao|o que faz|o que causa)\b", n):
            return "causal"
        if re.match(r"^(?:como|de que modo|de que maneira|por qual mecanismo)\b", n):
            return "mecanismo"
        return "geral"

    def _tokens_pergunta(self, texto, entidades):
        crus = set(self.tokenizador(texto))
        # Remove os tokens que apenas nomeiam uma entidade ja resolvida.
        tokens_entidades = set()
        for ident in entidades:
            item = self.itens.get(ident, {})
            for nome in [item.get("nome", "")] + list(item.get("aliases", [])):
                tokens_entidades.update(self.tokenizador(nome))
        conteudo = {t for t in crus if t not in RUIDO and t not in tokens_entidades}
        return crus, self._expandir(conteudo)

    def _bonus_intencao(self, intencao, unidade):
        if intencao == "definicao":
            return 1.65 if unidade.papel == "definicao" else -0.45
        if intencao == "formacao":
            return 1.45 if unidade.aspecto == "formacao" else (
                .35 if unidade.papel == "causa" else 0.0)
        if intencao == "causal":
            return (1.20 if unidade.papel == "causa" else 0.0) + (
                .85 if unidade.aspecto == "funcionamento" else 0.0)
        if intencao == "mecanismo":
            return (1.15 if unidade.aspecto == "funcionamento" else 0.0) + (
                .35 if unidade.papel == "causa" else 0.0)
        if intencao == "evidencia":
            return 1.50 if unidade.aspecto == "evidencias" else 0.0
        if intencao == "limite":
            return 1.55 if unidade.papel == "limite" else 0.0
        if intencao == "comparacao":
            return .30 if unidade.papel in ("detalhe", "limite") else 0.0
        return 0.0

    def _pontuar(self, unidade, entidades, conteudo, intencao):
        universo = {unidade.conceito} | set(unidade.mencoes)
        bonus_entidade = 0.0
        if unidade.conceito in entidades:
            bonus_entidade += 1.20
        bonus_entidade += .55 * sum(1 for e in entidades
                                    if e != unidade.conceito and e in unidade.mencoes)
        if len(entidades) >= 2 and set(entidades) <= universo:
            bonus_entidade += 1.10

        presentes = conteudo & set(unidade.tokens)
        total = sum(self.idf.get(t, 1.2) for t in conteudo) or 1.0
        cobertura = sum(self.idf.get(t, 1.2) for t in presentes) / total

        bonus = self._bonus_intencao(intencao, unidade)
        if intencao == "comparacao" and len(entidades) >= 2 and set(entidades) <= universo:
            bonus += 1.10

        # Definicao com entidade inequivoca pode ser respondida mesmo sem
        # palavras descritivas extras. Nos demais casos exigimos alguma
        # pista alem do nome do assunto.
        if not presentes and not (intencao == "definicao" and
                                  unidade.conceito in entidades and
                                  unidade.papel == "definicao"):
            return None

        score = bonus_entidade + bonus + 2.15 * cobertura + .18 * len(presentes)
        return score, presentes, cobertura

    def _qualificadores_desconhecidos(self, crus, entidade_ids, unidade):
        tokens_entidades = set()
        for ident in entidade_ids:
            item = self.itens.get(ident, {})
            for nome in [item.get("nome", "")] + list(item.get("aliases", [])):
                tokens_entidades.update(self.tokenizador(nome))
        relevantes = {t for t in crus if t not in RUIDO and
                      t not in tokens_entidades and len(t) >= 4}
        desconhecidos = []
        for termo in relevantes:
            equivalentes = self._expandir((termo,))
            if not (equivalentes & set(unidade.tokens)):
                desconhecidos.append(termo)
        return tuple(sorted(desconhecidos))

    def _encadear(self, primeira, selecionados):
        """Um unico salto, somente por conceito CITADO no primeiro fato."""
        if not primeira.mencoes:
            return None
        candidatos = []
        for unidade in self.unidades:
            if unidade.conceito not in primeira.mencoes:
                continue
            if (unidade.conceito, unidade.indice) in selecionados:
                continue
            if unidade.papel not in ("definicao", "causa", "detalhe"):
                continue
            if unidade.aspecto not in ("", "funcionamento"):
                continue
            compartilhados = set(primeira.tokens) & set(unidade.tokens)
            if not compartilhados:
                continue
            score = sum(self.idf.get(t, 1.0) for t in compartilhados)
            if unidade.aspecto == "funcionamento":
                score += .7
            if unidade.papel == "definicao":
                score += .25
            candidatos.append((score, unidade))
        if not candidatos:
            return None
        candidatos.sort(key=lambda x: x[0], reverse=True)
        return candidatos[0][1]

    def buscar(self, pergunta, contexto=()):
        if not isinstance(pergunta, str) or not pergunta.strip() or len(pergunta) > 600:
            return None
        n = normalizar(pergunta)
        if BLOQUEIOS.search(n):
            return None

        entidades = list(self._entidades(pergunta))
        for ident in contexto or ():
            if ident in self.itens and ident not in entidades:
                entidades.append(ident)
        if not entidades:
            # Sem assunto inequivoco, este motor nao adivinha por similaridade.
            return None
        entidades = tuple(entidades[:3])
        intencao = self._intencao(pergunta)
        crus, conteudo = self._tokens_pergunta(pergunta, entidades)

        candidatos = []
        for unidade in self.unidades:
            pontuado = self._pontuar(unidade, entidades, conteudo, intencao)
            if pontuado is None:
                continue
            score, presentes, cobertura = pontuado
            candidatos.append((score, cobertura, len(presentes), unidade))

        if not candidatos:
            return None
        candidatos.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        melhor_score, cobertura, _, melhor = candidatos[0]
        segundo = candidatos[1][0] if len(candidatos) > 1 else 0.0

        # Limiar absoluto + competicao. Definicoes diretas sao permitidas
        # com score menor porque o papel editorial "definicao" e o alias
        # exato ja sao duas provas independentes.
        minimo = 2.20 if intencao == "definicao" else 2.55
        if melhor_score < minimo:
            return None
        if intencao != "definicao" and segundo and melhor_score - segundo < .12:
            # Empates dentro do MESMO conceito podem ser desempatados por
            # cobertura; entre assuntos diferentes, abstencao.
            rival = candidatos[1][3]
            if rival.conceito != melhor.conceito and cobertura < .72:
                return None

        desconhecidos = self._qualificadores_desconhecidos(crus, entidades, melhor)
        if desconhecidos:
            # Um termo extra e tolerado quando ha varias pistas comprovadas;
            # dois qualificadores nao explicados tornam a consulta ambigua.
            presentes_reais = len(conteudo & set(melhor.tokens))
            if len(desconhecidos) >= 2 or presentes_reais <= 1:
                return None

        selecionados = [(melhor.conceito, melhor.indice)]
        provas = ["direto:{}:{}".format(melhor.conceito, melhor.indice)]
        if intencao in ("causal", "mecanismo", "formacao", "comparacao"):
            extra = self._encadear(melhor, set(selecionados))
            if extra is not None:
                selecionados.append((extra.conceito, extra.indice))
                provas.append("encadeado:{}:{}->{}:{}".format(
                    melhor.conceito, melhor.indice, extra.conceito, extra.indice))

        temas = tuple(dict.fromkeys(c for c, _ in selecionados))
        return PlanoConsolidacao(
            intencao, temas, tuple(selecionados), round(melhor_score, 4),
            tuple(provas))
