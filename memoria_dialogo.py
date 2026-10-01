"""Memória curta de diálogo, com fontes e isolamento por instância.

O texto do usuário é um relato, não um fato global. Spans do intérprete só
entram na memória se apontam para o texto original; respostas do modelo
continuam separadas de evidências explicitamente verificadas pelo chamador.
Nenhum dado desta classe é gravado em arquivo ou compartilhado entre bots.
"""
import copy
import math
import re
import unicodedata
from collections import deque


PAPEIS = frozenset(("evento", "sentimento", "tema", "objetivo", "restricao",
                    "interlocutor", "modo", "referencia", "modo_recusado"))


def _aceito(frame):
    """A memória consome a análise; ela não substitui o intérprete."""
    if not isinstance(frame, dict) or frame.get("aceita") is not True:
        return False
    confianca = frame.get("confianca")
    return (not isinstance(confianca, bool) and
            isinstance(confianca, (int, float)) and math.isfinite(confianca) and
            0 <= confianca <= 1)


def _normalizar(texto):
    n = unicodedata.normalize("NFD", texto.casefold())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return " ".join(re.findall(r"[\w'-]+", n))


def _fonte(texto, turno, origem, identificador, inicio=0, fim=None):
    fim = len(texto) if fim is None else fim
    return {"valor": texto[inicio:fim], "turno": turno, "origem": origem,
            "id": identificador, "fonte": {"texto": texto, "inicio": inicio, "fim": fim}}


def _dentro_citacao(texto, posicao):
    """Aspas são fala atribuída; não proíbem o resto de um relato."""
    return any(m.start() <= posicao < m.end() for m in
               re.finditer(r'"[^"\n]*"|“[^”\n]*”|‘[^’\n]*’|\'[^\'\n]*\'', texto))


def _hipotese(texto, frame):
    return bool(frame.get("hipotese") or frame.get("estatuto") == "hipotese" or
                re.match(r"(?:se|caso|suponha|imagine|hipoteticamente)\b", _normalizar(texto)))


def _emocao_propria(texto, inicio, frame, span):
    if (_hipotese(texto, frame) or _dentro_citacao(texto, inicio) or
            span.get("polaridade") in ("negativa", "negado", False) or
            span.get("atribuicao", "user") not in ("user", "usuario", "eu", "propria")):
        return False
    prefixo = _normalizar(texto[max(0, inicio - 100):inicio])
    prefixo = re.split(r"\b(?:mas|porem|e sim)\b", prefixo)[-1]
    if re.search(r"\b(?:nao|nunca|nem|talvez|seria|estaria|estivesse)\b", prefixo):
        return False
    # A cabeça semântica pode localizar 'triste' em fala de outra pessoa.
    # Exige declaração direta própria antes de afirmar emoção do usuário.
    return bool(re.search(r"(?:^|\b)(?:(?:eu|hoje|agora|ultimamente) )?"
                          r"(?:me sinto|me senti|estou|to|tou|fico|fiquei|ando|sinto|tenho) "
                          r"(?:(?:meio|muito|bem|um pouco|com|uma|um|mais|menos|realmente) )*$", prefixo + " "))


def _negacao_direta(texto, inicio, fim, papel):
    """Não transforma uma vontade explicitamente recusada em objetivo.

    É uma restrição de atribuição sobre spans já encontrados pelo encoder,
    não um reconhecimento de atos. Uma nova oração afirmativa encerra o
    escopo; 'quero não desistir' conserva a vontade que o usuário declarou.
    """
    trecho = re.split(r"[.!?,;]|\b(?:mas|porém|porem)\b", texto[:fim], flags=re.I)[-1]
    trecho = _normalizar(trecho)
    if papel == "objetivo":
        verbos = list(re.finditer(r"\b(?:(?:nao|nunca|nem) )?"
                                  r"(?:quero|pretendo|vou|planejo|desejo|busco)\b", trecho))
        return bool(verbos and re.match(r"(?:nao|nunca|nem)\b", verbos[-1].group()))
    if papel == "interlocutor":
        prefixo = re.split(r"[.!?,;]|\b(?:mas|porém|porem)\b", texto[:inicio], flags=re.I)[-1]
        prefixo = _normalizar(prefixo)
        return bool(re.search(r"\b(?:nao|nunca|nem) (?:foi|era|e)(?: a| o)?$", prefixo))
    return False


def _controles(texto, frame, informacoes):
    """Transições dependem de atos e argumentos aceitos, nunca de palavras."""
    citado = bool(re.fullmatch(r'\s*(?:"[^"\n]*"|“[^”\n]*”|‘[^’\n]*’|\'[^\'\n]*\')\s*[.!?]?\s*', texto))
    ato = frame.get("ato") if _aceito(frame) and not citado and not _hipotese(texto, frame) else ""
    retomadas = [i["valor"] for i in informacoes
                 if i["papel"] in ("referencia", "tema", "objetivo", "interlocutor") and
                 i.get("estatuto") not in ("hipotese", "citado") and
                 i.get("polaridade") not in ("negativa", "negado", False)]
    return {"reset": ato in ("reinicio", "reset"),
            "mudanca": ato == "mudar_assunto",
            "retomar": retomadas if ato == "retomar" else []}


class MemoriaDialogo:
    """Conserva até doze turnos; mudanças de assunto criam segmentos.

    ``frame`` aceita a saída do encoder: ato, confianca, aceita e spans
    contendo papel/inicio/fim/texto/confianca. Metadados opcionais de spans
    são atribuicao, polaridade e estatuto. ``evidencias`` deve ser uma lista
    de {texto, fonte, verificada: True}; o texto precisa aparecer na resposta.
    Sem essa evidência, toda resposta permanece na categoria ``model``.
    """
    def __init__(self, max_turnos=12):
        if isinstance(max_turnos, bool) or not isinstance(max_turnos, int) or not 1 <= max_turnos <= 12:
            raise ValueError("A memória deve conservar entre um e doze turnos")
        self.max_turnos = max_turnos
        self.limpar()

    def limpar(self):
        self.turno = self.segmento = self._proximo_segmento = 0
        self.turnos = deque(maxlen=self.max_turnos)

    def _recentes(self, turno=None):
        turno = self.turno if turno is None else turno
        return [r for r in self.turnos if turno - r["turno"] < self.max_turnos]

    def _retomada(self, alvos, registros):
        if not alvos:
            return None
        alvos = {re.sub(r"^(?:o|a|meu|minha) ", "", _normalizar(alvo)) for alvo in alvos}
        encontrados = set()
        for r in registros:
            for i in r["informacoes"]:
                if i["papel"] in ("tema", "objetivo", "interlocutor"):
                    if (i.get("estatuto") in ("hipotese", "citado") or
                            i.get("polaridade") in ("negativa", "negado", False)):
                        continue
                    valor = re.sub(r"^(?:o|a|meu|minha) ", "", _normalizar(i["valor"]))
                    if valor in alvos:
                        encontrados.add(r["segmento"])
        return next(iter(encontrados)) if len(encontrados) == 1 else None

    def _spans(self, texto, identificador, frame, turno=None):
        informacoes = []
        if not _aceito(frame):
            return informacoes
        turno = self.turno if turno is None else turno
        for s in frame.get("spans", ()):
            if not isinstance(s, dict) or s.get("papel") not in PAPEIS:
                continue
            inicio, fim = s.get("inicio"), s.get("fim")
            confianca = s.get("confianca")
            if (isinstance(inicio, bool) or isinstance(fim, bool) or
                    not isinstance(inicio, int) or not isinstance(fim, int) or
                    not 0 <= inicio < fim <= len(texto) or
                    isinstance(confianca, bool) or not isinstance(confianca, (int, float)) or not math.isfinite(confianca) or
                    not .5 <= confianca <= 1):
                continue
            literal = texto[inicio:fim]
            if ("texto" in s and s["texto"] != literal or "valor" in s and s["valor"] != literal):
                continue
            i = _fonte(texto, turno, "user", identificador, inicio, fim)
            citado = _dentro_citacao(texto, inicio)
            estatuto = "hipotese" if _hipotese(texto, frame) else ("citado" if citado else s.get("estatuto", "relatado"))
            i.update(papel=s["papel"], confianca=confianca,
                     estatuto=estatuto,
                     atribuicao=s.get("atribuicao", "user"), polaridade=s.get("polaridade", "positiva"))
            if _negacao_direta(texto, inicio, fim, s["papel"]):
                i["polaridade"] = "negado"
            if i["papel"] == "sentimento":
                i["declarada"] = _emocao_propria(texto, inicio, frame, s)
            informacoes.append(i)
        return informacoes

    def registrar(self, texto, resposta, identificador, frame=None):
        if not all(isinstance(x, str) for x in (texto, resposta, identificador)):
            raise ValueError("Turno de memória exige textos e identificador")
        if frame is None:
            frame = {}
        if not isinstance(frame, dict) or not isinstance(frame.get("spans", []), (list, tuple)):
            raise ValueError("Quadro de memória inválido")
        self.turno += 1
        informacoes = self._spans(texto, identificador, frame)
        c = _controles(texto, frame, informacoes)
        if identificador == "conversa:reinicio" or c["reset"]:
            self.turnos.clear()
            self._proximo_segmento += 1
            self.segmento = self._proximo_segmento
        elif c["mudanca"]:
            self._proximo_segmento += 1
            self.segmento = self._proximo_segmento
        elif c["retomar"]:
            anterior = self._retomada(c["retomar"], self._recentes())
            if anterior is not None:
                self.segmento = anterior
        evidencias = []
        for e in (frame.get("evidencias") or ()):
            if (isinstance(e, dict) and e.get("verificada") is True and
                    isinstance(e.get("texto"), str) and e["texto"] and e["texto"] in resposta and
                    isinstance(e.get("fonte"), (str, dict)) and e["fonte"]):
                inicio = resposta.find(e["texto"])
                i = _fonte(resposta, self.turno, "verified", identificador, inicio, inicio + len(e["texto"]))
                i["evidencia"] = copy.deepcopy(e["fonte"])
                evidencias.append(i)
        r = {"turno": self.turno, "segmento": self.segmento, "id": identificador,
             "usuario": _fonte(texto, self.turno, "user", identificador),
             "modelo": _fonte(resposta, self.turno, "model", identificador),
             "informacoes": informacoes, "evidencias": evidencias,
             "ato": frame.get("ato", "") if _aceito(frame) else "",
             "confianca": frame.get("confianca") if _aceito(frame) else None,
             "retificacoes": self._retificacoes(texto, identificador, frame, informacoes)}
        self.turnos.append(r)
        return copy.deepcopy(r)

    def _retificacoes(self, texto, identificador, frame, informacoes):
        if not _aceito(frame) or frame.get("ato") not in ("correcao", "reparo"):
            return []
        m = re.fullmatch(r"\s*(?:n[aã]o|corrigindo[,]? n[aã]o) (?:foi|era|[eé]) "
                         r"(?P<antes>.+?)[,;] (?:foi|era|[eé]) (?P<depois>.+?)\s*[.!]?\s*", texto, re.I)
        novos = [i for i in informacoes if i["papel"] == "interlocutor" and
                 i.get("estatuto") not in ("hipotese", "citado") and
                 i.get("polaridade") not in ("negativa", "negado", False)]
        if len(novos) != 1:
            return []
        novo = novos[0]
        if m and _normalizar(m.group("depois")) == _normalizar(novo["valor"]):
            return [{"antes": _fonte(texto, self.turno, "user", identificador, *m.span("antes")),
                     "depois": copy.deepcopy(novo)}]
        # O ato também pode acrescentar um detalhe que faltava. Um novo
        # interlocutor, sozinho, não autoriza apagar uma pessoa anterior.
        return []

    def contexto(self, texto="", frame=None):
        if not isinstance(texto, str):
            raise ValueError("A consulta de contexto deve ser texto")
        if frame is None:
            frame = {}
        if not isinstance(frame, dict) or not isinstance(frame.get("spans", []), (list, tuple)):
            raise ValueError("Quadro de memória inválido")
        consulta_turno = self.turno + bool(texto.strip())
        registros = self._recentes(consulta_turno)
        historico = list(registros)
        atuais = self._spans(texto, "", frame, consulta_turno)
        for i in atuais:
            i["provisorio"] = True
        c = _controles(texto, frame, atuais)
        segmento = self.segmento
        if c["reset"] or c["mudanca"]:
            registros = []
            if c["reset"]:
                historico = []
        elif c["retomar"]:
            retomado = self._retomada(c["retomar"], registros)
            if retomado is not None:
                segmento = retomado
        registros = [r for r in registros if r["segmento"] == segmento]
        infos = [copy.deepcopy(i) for r in registros for i in r["informacoes"]] + atuais
        retificacoes = [copy.deepcopy(i) for r in registros for i in r["retificacoes"]]
        for correcao in retificacoes:
            antes, depois = correcao["antes"], correcao["depois"]
            for i in infos:
                if (i["turno"] >= depois["turno"] or
                        i.get("estatuto") in ("hipotese", "citado") or
                        i.get("polaridade") in ("negativa", "negado", False)):
                    continue
                regra = re.compile(r"(?<!\w)" + re.escape(antes["valor"]) + r"(?!\w)", re.I)
                if regra.search(i["valor"]):
                    anterior = copy.deepcopy(i)
                    i["valor"] = regra.sub(lambda m: m.group() if _dentro_citacao(anterior["valor"], m.start()) else depois["valor"], i["valor"])
                    i.update(turno=depois["turno"], estatuto="retificado", derivado=True,
                             fontes=[anterior, depois])
        ativos = [i for i in infos if i.get("estatuto") not in ("hipotese", "citado") and
                  i.get("polaridade") not in ("negativa", "negado", False) and
                  i.get("atribuicao", "user") in ("user", "usuario", "eu", "propria")]
        recusados = [i for i in ativos if i["papel"] == "modo_recusado"]
        modos = [i for i in ativos if i["papel"] == "modo"]
        por_papel = lambda papel: [i for i in ativos if i["papel"] == papel]
        ultimo = lambda papel: (por_papel(papel) or [None])[-1]
        entidades = []
        vistos = set()
        for i in reversed(por_papel("interlocutor")):
            chave = _normalizar(i["valor"])
            if chave not in vistos:
                entidades.insert(0, i)
                vistos.add(chave)
        mencionadas = [i for i in entidades if re.search(
            r"(?<!\w)" + re.escape(i["valor"]) + r"(?!\w)", texto, re.I)]
        pronome = bool(re.search(r"\b(?:ele|ela|eles|elas|dele|dela|deles|delas)\b", _normalizar(texto)))
        referidas = mencionadas or (entidades if pronome else [])
        resposta = copy.deepcopy(registros[-1]["modelo"]) if registros else None
        pendente = None
        if resposta:
            perguntas = list(re.finditer(r"[^.!?\n]+\?", resposta["valor"]))
            if perguntas:
                p = perguntas[-1]
                inicio = p.start() + len(p.group()) - len(p.group().lstrip())
                pendente = _fonte(resposta["valor"], resposta["turno"], "model", resposta["id"], inicio, p.end())
        return {"turno": self.turno, "segmento": segmento,
                "objetivo": ultimo("objetivo"), "evento": ultimo("evento"),
                "eventos": por_papel("evento"), "restricoes": por_papel("restricao"),
                "topico": ultimo("tema"), "modo": (modos or [None])[-1],
                "focos_recusados": recusados, "entidades": entidades,
                "entidades_referidas": referidas,
                "referencia_ambigua": pronome and not mencionadas and len(entidades) > 1,
                "emocao_declarada": [i for i in por_papel("sentimento") if i.get("declarada")],
                "hipoteses": [i for i in infos if i.get("estatuto") == "hipotese"],
                "ultima_resposta": resposta, "questao_pendente": pendente,
                "retificacoes": retificacoes,
                "historico": [{"papel": papel, "texto": r[chave]["valor"]}
                              for r in historico
                              for papel, chave in (("usuario", "usuario"), ("assistente", "modelo"))],
                "historico_ativo": [{"papel": papel, "texto": r[chave]["valor"]}
                                    for r in registros
                                    for papel, chave in (("usuario", "usuario"), ("assistente", "modelo"))],
                "turnos": [{"turno": r["turno"], "usuario": r["usuario"]["valor"],
                            "assistente": r["modelo"]["valor"], "id": r["id"]} for r in registros],
                "fontes": {"user": [copy.deepcopy(r["usuario"]) for r in registros],
                           "model": [copy.deepcopy(r["modelo"]) for r in registros],
                           "verified": [copy.deepcopy(e) for r in registros for e in r["evidencias"]]}}

    def fontes_relevantes(self, texto="", frame=None, limite=2):
        """Reabre até duas falas literais que uma memória aceita pode usar.

        Só há seleção pela procedência dos campos ativos e pela recência.
        Uma resposta do assistente, uma hipótese ou um trecho citado nunca
        entram como uma declaração do usuário. A fala atual já faz parte da
        entrada do encoder; este método retorna apenas falas armazenadas.
        """
        if isinstance(limite, bool) or not isinstance(limite, int) or not 1 <= limite <= 2:
            raise ValueError("A seleção conserva uma ou duas fontes")
        if not _aceito(frame) or frame.get("ato") not in ("memoria", "retomar"):
            return []
        contexto = self.contexto(texto, frame)
        armazenadas = {r["turno"]: r["usuario"] for r in self.turnos}
        candidatos = {}

        def adicionar(informacao):
            if not informacao or informacao.get("origem") != "user":
                return
            if (informacao.get("estatuto") in ("hipotese", "citado") or
                    informacao.get("polaridade") in ("negativa", "negado", False)):
                return
            derivacoes = informacao.get("fontes")
            if derivacoes:
                for fonte in derivacoes:
                    adicionar(fonte)
                return
            turno = informacao.get("turno")
            original = armazenadas.get(turno)
            fonte = informacao.get("fonte", {})
            if original and fonte.get("texto") == original["valor"]:
                candidatos[turno] = original["valor"]

        for nome in ("objetivo", "evento", "topico"):
            adicionar(contexto[nome])
        for nome in ("restricoes", "emocao_declarada"):
            for informacao in contexto[nome]:
                adicionar(informacao)
        for entidade in contexto["entidades_referidas"] or contexto["entidades"]:
            adicionar(entidade)
        selecionados = sorted(candidatos.items(), reverse=True)[:limite]
        return [{"papel": "usuario", "texto": literal}
                for _, literal in sorted(selecionados)]

    def quadro_resumido(self):
        """Inspeção do último ato e de seus argumentos literais, sem prova."""
        if not self.turnos:
            return None
        r = self.turnos[-1]
        return {"ato": r["ato"], "confianca": r["confianca"],
                "alvos": [{"papel": i["papel"], "texto": i["valor"],
                           "inicio": i["fonte"]["inicio"], "fim": i["fonte"]["fim"]}
                          for i in r["informacoes"]],
                "fontes": {"user": [copy.deepcopy(r["usuario"])],
                           "model": [copy.deepcopy(r["modelo"])],
                           "verified": copy.deepcopy(r["evidencias"])}}
