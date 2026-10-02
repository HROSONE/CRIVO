"""Sentido das frases: quem fez o quê, por quê, quando, onde e sob que condição.

A partir da árvore do analisador_frases, cada oração vira um Evento:
ação (lema do verbo), agente (sujeito), objeto, tempo, lugar, negação e
as relações com outras orações marcadas por conectivos:
  porque/pois/já que → causa;  quando/enquanto → tempo;  se/caso → condição;
  para/pra → finalidade;  embora → concessão.

A MemoriaRelatos guarda os eventos que a pessoa conta e responde perguntas
sobre eles ("por que ele latiu?", "quem quebrou a janela?"), sempre como
"você me contou" — nunca como fato do conhecimento. Se a pergunta não casa
com nada que foi contado, a memória não responde e o Crivo segue o caminho
normal.
"""
import re

from analisador_frases import analisador, sem_acento

CONECTIVOS = {
    "porque": "causa", "pois": "causa", "ja que": "causa", "visto que": "causa", "uma vez que": "causa",
    "quando": "quando", "enquanto": "quando", "assim que": "quando", "depois que": "quando",
    "antes que": "quando", "se": "condicao", "caso": "condicao", "para": "finalidade",
    "pra": "finalidade", "para que": "finalidade", "embora": "concessao", "apesar de": "concessao",
}
TEMPO = set("""ontem hoje amanha anteontem agora cedo tarde noite manha madrugada semana mes ano dia
    domingo segunda terca quarta quinta sexta sabado feriado fim natal janeiro fevereiro marco abril
    maio junho julho agosto setembro outubro novembro dezembro hora horas minutos vez""".split())
PREP_LUGAR = {"em", "sobre", "sob", "dentro", "embaixo", "debaixo", "atras", "perto", "longe", "entre",
              "ate", "para", "a", "de"}
SEGUNDA_PESSOA = {"meu": "seu", "minha": "sua", "meus": "seus", "minhas": "suas"}
PRONOMES_CORINGA = {"ele", "ela", "eles", "elas", "isso", "aquilo"}
GENERICOS = {"fazer", "acontecer", "ser", "estar", "ter", "ir"}


class Evento:
    def __init__(self):
        self.acao = ""        # lema
        self.verbo = ""       # forma
        self.agente = ""      # texto do sujeito
        self.agente_nucleo = ""
        self.objeto = ""
        self.tempo = []
        self.lugar = []
        self.complementos = []
        self.negado = False
        self.primeira_pessoa = False
        self.texto = ""       # oração sem as subordinadas
        self.relacoes = {}    # tipo → Evento

    def __repr__(self):
        return "Evento(%s, agente=%r, objeto=%r, tempo=%r, lugar=%r, neg=%s, rel=%s)" % (
            self.acao, self.agente, self.objeto, self.tempo, self.lugar, self.negado,
            {k: v.texto for k, v in self.relacoes.items()})


def _juntar(formas, contracoes_inv):
    saida = []
    for f in formas:
        if saida and (saida[-1].lower(), f.lower()) in contracoes_inv:
            junto = contracoes_inv[(saida[-1].lower(), f.lower())]
            saida[-1] = junto.capitalize() if saida[-1][:1].isupper() else junto
            continue
        saida.append(f)
    texto = " ".join(saida)
    return re.sub(r"\s+([,.;:!?])", r"\1", texto)


class Leitor:
    def __init__(self, analisador_=None):
        self.a = analisador_ or analisador()
        self.disponivel = self.a.disponivel
        inv = {}
        if self.disponivel:
            for forma, partes in self.a.tokenizar.contracoes.items():
                if len(partes) == 2:
                    inv.setdefault(tuple(partes), forma)
        self.contracoes_inv = inv

    # -- árvore -------------------------------------------------------
    def _filhos(self, palavras):
        filhos = {p.id: [] for p in palavras}
        filhos[0] = []
        for p in palavras:
            filhos[p.pai].append(p)
        return filhos

    def _sub(self, no, filhos, excluir=()):
        ids = [no.id]
        for f in filhos[no.id]:
            if f.ligacao in excluir:
                continue
            ids += self._sub(f, filhos, ())
        return sorted(ids)

    def _texto(self, ids, por_id):
        formas = [por_id[i].forma for i in ids if por_id[i].ligacao != "punct" or i != ids[-1]]
        return _juntar(formas, self.contracoes_inv).strip(" ,")

    def eventos(self, texto):
        """Eventos principais da frase (orações coordenadas viram eventos
        separados); subordinadas ficam em relacoes."""
        if not self.disponivel:
            return []
        palavras = self.a.analisar(texto)
        if not palavras:
            return []
        por_id = {p.id: p for p in palavras}
        filhos = self._filhos(palavras)
        raiz = next((p for p in palavras if p.pai == 0), None)
        if raiz is None:
            return []
        principais = [raiz] + [f for f in filhos[raiz.id] if f.ligacao == "conj"
                               and f.classe in ("VERB", "AUX", "ADJ")]
        saida = []
        for no in principais:
            ev = self._evento(no, filhos, por_id)
            if not ev.agente and saida:
                ev.agente, ev.agente_nucleo = saida[0].agente, saida[0].agente_nucleo
            saida.append(ev)
        return saida

    def evento_pergunta(self, texto):
        """Evento do primeiro verbo da pergunta (em "o que sua mãe fez?" a
        raiz da árvore é "o", não o verbo)."""
        if not self.disponivel:
            return None
        palavras = self.a.analisar(texto)
        if not palavras:
            return None
        por_id = {p.id: p for p in palavras}
        filhos = self._filhos(palavras)
        no = (next((p for p in palavras if p.classe == "VERB"), None)
              or next((p for p in palavras if p.pai == 0), None))
        return self._evento(no, filhos, por_id) if no else None

    def _evento(self, no, filhos, por_id):
        ev = Evento()
        ev.acao, ev.verbo = no.lema.lower(), no.forma
        subordinadas = ("advcl", "conj", "cc", "punct", "parataxis")
        ev.texto = self._texto(self._sub(no, filhos, subordinadas + ("mark",)), por_id)
        for f in filhos[no.id]:
            lig = f.ligacao
            if lig in ("nsubj", "nsubj:pass", "csubj"):
                ev.agente = self._texto(self._sub(f, filhos, subordinadas), por_id)
                ev.agente_nucleo = sem_acento(f.lema)
                ev.primeira_pessoa = sem_acento(f.forma) in ("eu", "nos") or ev.agente.lower() == "a gente"
            elif lig == "obj":
                ev.objeto = self._texto(self._sub(f, filhos, subordinadas), por_id)
            elif lig in ("obl", "obl:agent", "advmod", "nmod:tmod"):
                trecho = self._texto(self._sub(f, filhos, subordinadas), por_id)
                if sem_acento(f.forma) in ("nao", "nunca", "jamais"):
                    ev.negado = True
                    continue
                prep = next((sem_acento(c.forma) for c in filhos[f.id] if c.ligacao == "case"), "")
                if sem_acento(f.lema) in TEMPO or any(sem_acento(w) in TEMPO for w in trecho.split()[:3]):
                    ev.tempo.append(trecho)
                elif lig == "obl" and prep in PREP_LUGAR:
                    ev.lugar.append(trecho)
                else:
                    ev.complementos.append(trecho)
            elif lig == "cop":
                ev.acao = no.lema.lower()
            elif lig == "advcl":
                # O conectivo pode ter ficado preso à oração encaixada
                # ("porque começou a chover": "porque" ligado a "chover").
                nos = [f] + [c for c in filhos[f.id] if c.ligacao in ("xcomp", "ccomp")]
                marca = " ".join(sem_acento(c.forma) for x in nos for c in filhos[x.id] if c.ligacao == "mark")
                tipo = CONECTIVOS.get(marca) or next((CONECTIVOS[m] for m in marca.split() if m in CONECTIVOS), None)
                if tipo:
                    ev.relacoes[tipo] = self._evento(f, filhos, por_id)
        if not ev.agente:
            # Sujeito oculto de primeira pessoa: "viajei", "esqueci".
            v = sem_acento(no.forma)
            ev.primeira_pessoa = v.endswith("ei") or (v.endswith("i") and len(v) > 3 and
                                                      no.lema.endswith(("er", "ir")) and v != no.lema)
        return ev


# ---------------------------------------------------------------------------
# Perguntas sobre o que foi contado

_PERGUNTA = [
    ("causa", re.compile(r"(?:e )?(?:por que|porque|pq|por qual motivo|qual (?:foi )?o motivo de)\b")),
    ("agente", re.compile(r"(?:e )?quem\b")),
    ("tempo", re.compile(r"(?:e )?quando\b")),
    ("lugar", re.compile(r"(?:e )?(?:onde|aonde)\b")),
    ("objeto", re.compile(r"(?:e )?(?:o que|que|qual)\b")),
]


def _casa_verbo(a, b):
    a, b = sem_acento(a), sem_acento(b)
    return a == b or (len(a) >= 4 and len(b) >= 4 and a[:4] == b[:4])


def _segunda_pessoa(texto):
    palavras = texto.split()
    return " ".join(SEGUNDA_PESSOA.get(w.lower(), w) if w.lower() in SEGUNDA_PESSOA else w for w in palavras)


def _sem_possessivo(nucleo_texto):
    return " ".join(w for w in sem_acento(nucleo_texto).split()
                    if w not in ("meu", "minha", "meus", "minhas", "seu", "sua", "seus", "suas", "o", "a",
                                 "os", "as", "um", "uma", "teu", "tua"))


class MemoriaRelatos:
    LIMITE = 30

    def __init__(self, leitor=None):
        self._leitor = leitor
        self.eventos = []  # (evento, frase original)

    @property
    def leitor(self):
        if self._leitor is None:
            self._leitor = Leitor()
        return self._leitor

    def guardar(self, frase):
        if not self.leitor.disponivel:
            return []
        evs = [e for e in self.leitor.eventos(frase) if e.acao]
        for e in evs:
            self.eventos.append((e, frase.strip()))
        self.eventos = self.eventos[-self.LIMITE:]
        return evs

    def responder(self, pergunta):
        """(resposta, evento) se a pergunta é sobre algo contado; senão None."""
        if not self.eventos or not self.leitor.disponivel:
            return None
        n = sem_acento(pergunta).strip(" ?!.")
        tipo = next((t for t, padrao in _PERGUNTA if padrao.match(n)), None)
        if tipo is None:
            return None
        condicao = None
        m = re.search(r"\bse (\w+)", n)
        if m and tipo == "objeto":
            condicao = m.group(1)
        qe = self.leitor.evento_pergunta(pergunta)
        if qe is None:
            return None
        verbo_q = qe.acao
        # "o que X fez?" pergunta pela ação; o verbo genérico não precisa casar.
        generico = verbo_q in GENERICOS or sem_acento(verbo_q) in GENERICOS
        agente_q = _sem_possessivo(qe.agente)
        candidatos = []
        for idx, (ev, frase) in enumerate(self.eventos):
            pont = 0
            if condicao:
                cond = ev.relacoes.get("condicao")
                if cond is None or not _casa_verbo(cond.acao, condicao):
                    continue
                pont += 2
            verbo_casou = False
            if condicao:
                verbo_casou = True
            elif _casa_verbo(ev.acao, verbo_q) or _casa_verbo(sem_acento(ev.verbo), sem_acento(qe.verbo)):
                pont += 2
                verbo_casou = True
            elif not generico:
                continue
            agente_ev = _sem_possessivo(ev.agente)
            if condicao:
                pass  # a condição já identifica o relato
            elif agente_q and agente_q not in PRONOMES_CORINGA:
                if agente_q in ("eu", "voce", "voces", "nos", "gente") and ev.primeira_pessoa:
                    pont += 1
                elif agente_ev and (agente_q == agente_ev or agente_q.split()[-1] == agente_ev.split()[-1]):
                    pont += 1
                elif tipo != "agente":
                    continue
            elif generico and not verbo_casou:
                continue
            if qe.objeto and ev.objeto:
                if _sem_possessivo(qe.objeto).split()[-1:] == _sem_possessivo(ev.objeto).split()[-1:]:
                    pont += 1
            if qe.negado != ev.negado and tipo == "causa":
                continue
            candidatos.append((pont, idx, ev, frase))
        if not candidatos:
            return None
        _, _, ev, frase = max(candidatos, key=lambda c: (c[0], c[1]))
        return self._resposta(tipo, ev, frase, condicao), ev

    def _resposta(self, tipo, ev, frase, condicao):
        citar = "Você me contou: “%s”." % frase
        if condicao:
            return citar
        if tipo == "causa":
            causa = ev.relacoes.get("causa")
            if causa is None:
                return ("Você me contou que %s, mas não disse por quê." % self._oracao(ev)
                        if not ev.primeira_pessoa else "Você me contou: “%s”, mas não disse por quê." % frase)
            causa.texto = re.sub(r"^(?:porque|pois|ja que|já que|visto que)\s+", "", causa.texto, flags=re.I)
            if causa.primeira_pessoa or ev.primeira_pessoa:
                return "Você me contou que foi porque “%s”." % causa.texto
            return "Você me contou que foi porque %s." % _segunda_pessoa(causa.texto)
        if tipo == "agente":
            if not ev.agente:
                return citar
            return "Pelo que você me contou, foi %s." % ("você" if ev.primeira_pessoa else _segunda_pessoa(ev.agente))
        if tipo == "tempo":
            quando = ev.tempo or ([ev.relacoes["quando"].texto] if "quando" in ev.relacoes else [])
            return ("Você me contou que foi %s." % " ".join(quando)) if quando else (
                "Você me contou isso, mas não disse quando: “%s”." % frase)
        if tipo == "lugar":
            return ("Você me contou que foi %s." % ev.lugar[0]) if ev.lugar else (
                "Você me contou isso, mas não disse onde: “%s”." % frase)
        # objeto / o que fez
        if ev.primeira_pessoa:
            return citar
        return "Você me contou que %s." % self._oracao(ev)

    @staticmethod
    def _oracao(ev):
        return _segunda_pessoa(ev.texto[0].lower() + ev.texto[1:]) if ev.texto else ev.acao
