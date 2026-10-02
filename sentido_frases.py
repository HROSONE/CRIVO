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
PREFERENCIAS = {"gostar", "preferir", "odiar", "detestar", "amar", "adorar", "querer", "chamar", "curtir"}


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
        self.palavras = []
        self.nucleo_objeto = ""
        self.encaixado = False
        self.antigo = False

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
        # Orações encaixadas viram eventos próprios: em "vi uma menina
        # abrindo o guarda-chuva", a menina abriu o guarda-chuva.
        for p in palavras:
            gerundio_solto = p.ligacao == "advcl" and not any(c.ligacao == "mark" for c in filhos[p.id])
            if p.classe != "VERB" or (p.ligacao not in ("xcomp", "ccomp", "acl", "acl:relcl")
                                      and not gerundio_solto):
                continue
            ev = self._evento(p, filhos, por_id)
            ev.encaixado = True
            if not ev.agente:
                cab = por_id.get(p.pai)
                if p.ligacao.startswith("acl") and cab is not None:
                    ev.agente = self._texto([i for i in self._sub(cab, filhos, ("acl", "acl:relcl", "punct"))
                                             if por_id[i].ligacao != "case"], por_id)
                    ev.agente_nucleo = sem_acento(cab.lema)
                elif cab is not None:
                    obj = next((c for c in filhos[cab.id] if c.ligacao == "obj"), None)
                    if obj is not None:
                        ev.agente = self._texto(self._sub(obj, filhos, ("acl", "acl:relcl")), por_id)
                        ev.agente_nucleo = sem_acento(obj.lema)
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
        verbos = [p for p in palavras if p.classe == "VERB"]
        dizer = ("falar", "dizer", "contar", "achar", "lembrar", "pensar", "ser")
        uteis = [p for p in verbos if p.lema.lower() not in dizer]
        no = ((uteis or verbos or [None])[0]
              or next((p for p in palavras if p.pai == 0), None))
        return self._evento(no, filhos, por_id) if no else None

    def _evento(self, no, filhos, por_id):
        ev = Evento()
        ev.acao, ev.verbo = no.lema.lower(), no.forma
        subordinadas = ("advcl", "conj", "cc", "punct", "parataxis")
        ids = self._sub(no, filhos, subordinadas)
        # Só o conectivo que abre a oração sai ("porque viu…"); o "que" de
        # "teve que colocar" fica.
        abertura = min(ids)
        ids = [i for i in ids if not (por_id[i].ligacao == "mark" and por_id[i].pai == no.id and i <= abertura + 1
                                      and i < no.id)]
        ev.texto = self._texto(ids, por_id)
        ev.palavras = [por_id[i] for i in ids if por_id[i].ligacao != "punct"]
        ev.nucleo_objeto = ""
        for f in filhos[no.id]:
            lig = f.ligacao
            if lig in ("nsubj", "nsubj:pass", "csubj"):
                ev.agente = self._texto(self._sub(f, filhos, subordinadas), por_id)
                ev.agente_nucleo = sem_acento(f.lema)
                ev.primeira_pessoa = sem_acento(f.forma) in ("eu", "nos") or ev.agente.lower() == "a gente"
            elif lig == "obj":
                ev.objeto = self._texto(self._sub(f, filhos, subordinadas), por_id)
                ev.nucleo_objeto = f.lema.lower()
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
            from presenca import _primeira_pessoa
            ev.primeira_pessoa = _primeira_pessoa(no)
        return ev


# ---------------------------------------------------------------------------
# Perguntas sobre o que foi contado

_OPINIAO = re.compile(r"(?:e )?(?:por que (?:voce acha|sera|tu acha)(?: que)?|o que (?:voce acha|sera) que|"
                      r"qual (?:sera|voce acha que (?:e|foi)) o motivo)\b")

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

    def guardar(self, frase, antigo=False):
        """antigo=True: relato de uma conversa anterior (memória do navegador)."""
        if not self.leitor.disponivel:
            return []
        if re.search(r"\b(?:se chama|me chamo|meu nome|nome (?:dele|dela|do|da))\b", sem_acento(frase)):
            return []  # nomes têm memória própria
        evs = [e for e in self.leitor.eventos(frase) if e.acao]
        for e in evs:
            e.antigo = antigo
            self.eventos.append((e, frase.strip()))
        self.eventos = self.eventos[-self.LIMITE:]
        return evs

    def responder(self, pergunta):
        """(resposta, evento) se a pergunta é sobre algo contado; senão None."""
        if not self.eventos or not self.leitor.disponivel:
            return None
        n = sem_acento(pergunta).strip(" ?!.")
        contei = re.fullmatch(r"(?:e )?(?:o que|oq|que) (?:foi que )?(?:eu )?(?:te |lhe )?(?:contei|falei|disse)"
                              r"(?: (?:pra voce|para voce|a voce))?(?: (?:de|do|da|dos|das|sobre) (.+))?", n)
        if contei:
            return self._contado(contei.group(1))
        opiniao = bool(_OPINIAO.match(n))
        tipo = "causa" if opiniao else next((t for t, padrao in _PERGUNTA if padrao.match(n)), None)
        if tipo is None:
            return None
        condicao = None
        m = re.search(r"\bse (\w+)", n)
        if m and tipo == "objeto":
            condicao = m.group(1)
        qe = self.leitor.evento_pergunta(pergunta)
        if qe is None:
            return None
        # Preferências e nome têm memória própria no diálogo (com correção
        # e negação); a memória de relatos não responde por elas.
        if any(_casa_verbo(qe.acao, p) or _casa_verbo(qe.verbo, p) for p in PREFERENCIAS):
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
        _, idx, ev, frase = max(candidatos, key=lambda c: (c[0], c[1]))
        if opiniao and "causa" not in ev.relacoes:
            return self._inferir(ev, frase), ev
        resposta = self._resposta(tipo, ev, frase, condicao)
        if tipo == "causa" and "causa" not in ev.relacoes:
            # Só a frase logo antes, na mesma conversa, serve de palpite.
            anterior = next((e for e, f in reversed(self.eventos[max(0, idx - 3):idx])
                             if f != frase and not e.encaixado), None)
            if anterior is not None and (getattr(anterior, "antigo", False) or getattr(ev, "antigo", False)):
                anterior = None
            if anterior is not None:
                resposta += (" Mas imagino que tenha a ver com o que você contou antes: %s. "
                             "É só um palpite." % self._voce(anterior))
        return resposta, ev

    def _contado(self, alvo):
        """"O que eu te contei (da minha mãe)?": os relatos guardados,
        inclusive de conversas anteriores, na voz de "você"."""
        frases = []
        alvo_n = _sem_possessivo(alvo or "")
        for ev, frase in self.eventos:
            if ev.encaixado:
                continue
            if alvo_n and alvo_n not in _sem_possessivo(" ".join((ev.agente, ev.objeto, ev.texto))):
                continue
            texto = self._voce(ev)
            if texto not in frases:
                frases.append(texto)
        if not frases:
            return None
        return ("Você me contou que " + "; e que ".join(frases[-3:]) + "."), None

    def _inferir(self, ev, frase):
        """Quarto nível de saber: o provável. Só a partir de noções (para que
        serve o objeto) ou do que aconteceu junto; sempre marcado."""
        try:
            from conversa_cotidiana import nocoes
            base = nocoes()
        except Exception:
            base = None
        if base is not None:
            for alvo in (ev.objeto, ev.nucleo_objeto, ev.texto):
                for nocao in base.encontrar(alvo or ""):
                    if nocao.get("para"):
                        return ("Você não me disse o motivo, mas provavelmente foi para %s. "
                                "É só um palpite pelo que eu sei de %s." % (nocao["para"], nocao["nome"]))
        junto = ev.relacoes.get("quando")
        if junto is not None:
            return ("Você não me disse o motivo. Talvez tenha a ver com o que aconteceu junto: %s. "
                    "Mas é só um palpite." % junto.texto)
        return "Você não me disse o motivo, e eu não tenho pista suficiente para dar um palpite. O que você acha?"

    def _resposta(self, tipo, ev, frase, condicao):
        citar = "Você me contou: “%s”." % frase
        if condicao:
            return citar
        voce = re.sub(r"^você ", "", self._voce(ev)) if ev.primeira_pessoa else self._voce(ev)
        if tipo == "causa":
            causa = ev.relacoes.get("causa")
            if causa is None:
                return "Você me contou que %s, mas não disse por quê." % voce
            texto_causa = self._voce(causa)
            texto_causa = re.sub(r"^(?:porque|pois|ja que|já que|visto que)\s+", "", texto_causa, flags=re.I)
            return "Você me contou que foi porque %s." % texto_causa
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
        return "Você me contou que %s." % voce

    def _voce(self, ev):
        """Oração do evento na voz de "você"; cita entre aspas se não der."""
        if ev.palavras:
            from presenca import para_voce
            texto = para_voce(ev.palavras)
            if texto:
                texto = re.sub(r"\s+([,.;:!?])", r"\1", texto)
                for (a, b), junto in self.leitor.contracoes_inv.items():
                    texto = re.sub(r"\b%s %s\b" % (a, b), junto, texto)
                return texto[0].lower() + texto[1:]
        return "“%s”" % ev.texto

    @staticmethod
    def _oracao(ev):
        return _segunda_pessoa(ev.texto[0].lower() + ev.texto[1:]) if ev.texto else ev.acao
