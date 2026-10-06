"""Estado interno do turno: o quadro que as espécies leem e escrevem.

Antes, cada mecanismo recebia o texto, decidia sozinho e devolvia uma resposta
ou uma recusa. Se a busca factual não achava as palavras exatas, dizia
"Reconheci o assunto Titã, mas não tenho evidência", mesmo com a ficha de Titã
falando de chuva. O conhecimento existia, mas nenhuma outra parte via a
recusa nem o que já tinha sido entendido.

Agora cada fala monta um estado único:

  compreensão   tipo de pergunta, entidades (da fala ou do contexto),
                pistas de conteúdo, negação;
  memória       assunto da conversa, turno anterior, oferta pendente;
  conhecimento  fatos e ligações das entidades;
  propostas     o que cada espécie propõe (responder, recusar, aproximar),
                com a evidência que tem;
  decisão       quem falou e por quê.

O árbitro lê as propostas. Quando a espécie que respondeu recusou e a leitura
da ficha tem evidência forte sobre a mesma entidade, a leitura fala. Com
evidência média, a resposta diz que não tem a resposta exata e mostra o fato
mais próximo. Sem evidência, a recusa fica.

O estado não é uma rede nem uma representação aprendida de ponta a ponta. É o
contrato comum que permite a várias espécies (regras, redes e acervo) operar
sobre o mesmo entendimento do turno. A API o expõe em `internal_state`.
"""
import re
from collections import namedtuple

from composicao_textual import normalizar

Entidade = namedtuple("Entidade", "id nome origem")
Proposta = namedtuple("Proposta", "especie ident acao evidencia")

RECUSAS = frozenset(("fora", "duvida", "social:nao_entendido"))
_RECUSA_TEXTO = ("não tenho", "ainda não", "reconheci o assunto", "não reconheci", "não consegui",
                 "não encontrei", "hum, não entendi")
_PRONOME = re.compile(r"\b(?:ele|ela|eles|elas|dele|dela|deles|delas|isso|disso|nele|nela)\b")
_ESCRITA = re.compile(r"\b(?:escrev\w*|resum\w*|frases?|roteiro|topicos|paragrafos?|linhas?|redacao|poema)\b")
_PESSOAL = re.compile(r"\b(?:voce|vc|seu|sua|te|contigo)\b")


class EstadoInterno:
    def __init__(self, fala):
        self.fala = fala
        self.quadro = None
        self.tipo = None
        self.entidades = []
        self.pistas = []
        self.negacao = False
        self.memoria = {}
        self.conhecimento = {}
        self.propostas = []
        self.decisao = None

    @property
    def entidade(self):
        """A entidade principal, quando há exatamente uma."""
        return self.entidades[0] if len(self.entidades) == 1 else None

    def propor(self, especie, ident, acao, evidencia=None):
        self.propostas.append(Proposta(especie, ident, acao, evidencia or {}))

    def decidir(self, especie, acao, motivo):
        self.decisao = {"especie": especie, "acao": acao, "motivo": motivo}

    def para_dict(self):
        return {
            "understanding": {"question_type": self.tipo,
                              "entities": [e._asdict() for e in self.entidades],
                              "cues": [p for _, p in self.pistas], "negation": self.negacao},
            "memory": self.memoria,
            "knowledge": self.conhecimento,
            "proposals": [{"species": p.especie, "id": p.ident, "action": p.acao, "evidence": p.evidencia}
                          for p in self.propostas],
            "decision": None if self.decisao is None else {
                "species": self.decisao["especie"], "action": self.decisao["acao"],
                "reason": self.decisao["motivo"]},
        }


def construir(bot, fala):
    """Estado inicial do turno, antes de qualquer espécie responder."""
    estado = EstadoInterno(fala)
    if not isinstance(fala, str):
        return estado
    from leitura_ficha import GENERICAS, tipo_pergunta
    c = bot.compositor
    n = normalizar(fala)
    quadro = c.interpretar(fala)
    estado.quadro = quadro
    estado.tipo = tipo_pergunta(n.strip())
    estado.negacao = bool(re.search(r"\b(?:nao|nunca|jamais|nem)\b", n))
    if quadro is not None:
        estado.pistas = [(r, p) for r, p in quadro.pistas if p not in GENERICAS]
        for ident in ((quadro.assunto,) if quadro.assunto else ()) + tuple(quadro.outros):
            estado.entidades.append(Entidade(ident, c.itens[ident]["nome"], "fala"))
    assunto = getattr(bot, "assunto_conversa", None)
    if not estado.entidades and assunto in c.itens and _PRONOME.search(n):
        estado.entidades.append(Entidade(assunto, c.itens[assunto]["nome"], "contexto"))
    turno = getattr(bot, "ultimo_turno", None) or {}
    estado.memoria = {
        "conversation_subject": c.itens[assunto]["nome"] if assunto in c.itens else None,
        "previous_turn_id": turno.get("id"),
        "pending_offer": bool(getattr(bot, "oferta_pendente", None)),
    }
    for e in estado.entidades:
        item = c.itens[e.id]
        estado.conhecimento[e.id] = {
            "facts": len(item["fatos"]),
            "links": sum(1 for r in c.ligacoes_mundo if e.id in (r["origem"], r["destino"])),
        }
    return estado


def recusou(ident, resposta):
    return ident in RECUSAS or resposta.strip().lower().startswith(_RECUSA_TEXTO)


# Só a recusa por falta de evidência pode ser revista pela leitura. "duvida"
# (consulta lógica composta ou ambígua) e "logica:desconhecido" são recusas
# deliberadas de quem entendeu a pergunta.
REVISAVEIS = frozenset(("fora", "social:nao_entendido"))


def _pode_ler(estado):
    """A leitura da ficha só entra numa pergunta factual sobre UMA entidade
    citada na fala, sem negação, pedido de escrita ou pergunta pessoal."""
    q = estado.quadro
    if q is None or q.recusa or q.outros or estado.negacao:
        return False
    e = estado.entidade
    if e is None or e.origem != "fala" or e.id != q.assunto:
        return False
    n = normalizar(estado.fala)
    return not (_ESCRITA.search(n) or _PESSOAL.search(n))


def arbitrar(bot, estado, ident, resposta):
    """Registra a proposta da espécie que respondeu e, se ela recusou, ouve
    a leitura da ficha. Devolve (ident, resposta) finais."""
    from ecossistema import mecanismo_do_turno
    especie = mecanismo_do_turno(bot, estado.fala, ident)
    recusa = recusou(ident, resposta)
    estado.propor(especie, ident, "recusar" if recusa else "responder")
    if not recusa or not isinstance(estado.fala, str) or not getattr(bot, "usar_leitura_ficha", True):
        estado.decidir(especie, "recusar" if recusa else "responder", "primeira espécie a responder")
        return ident, resposta
    if ident not in REVISAVEIS or not _pode_ler(estado):
        estado.decidir(especie, "recusar", "leitura fora do nicho (negação, relação, escrita ou sem entidade)")
        return ident, resposta
    leitor = bot.leitura_ficha
    leitura = leitor.ler(estado.quadro, estado.entidade.id)
    decisao = leitor.decisao(leitura)
    evidencia = None if leitura is None else {
        "fact": leitura.indice, "probability": leitura.prob, "margin": leitura.margem,
        "cues_covered": leitura.cobertura, "question_type": leitura.tipo}
    estado.propor("leitura_ficha", None, decisao or "calar", evidencia)
    if decisao is None:
        estado.decidir(especie, "recusar", "a leitura da ficha não achou evidência suficiente")
        return ident, resposta
    assunto, i = leitura.assunto, leitura.indice
    novo_ident, texto, ctx = bot.compositor.compor((assunto,), "explicacao", selecionados=((assunto, i),),
                                                  origem="conhecimento")
    bot.contexto_textual = ctx
    if decisao == "afirmar":
        novo_ident = "escrita:explicacao"
        texto, com_voz = bot._dar_voz(estado.fala, texto)
        bot.ultima_resposta_mostrada = texto
    else:
        novo_ident = "leitura:aproximacao"
        com_voz = False
        bot.oferta_pendente = None
        texto = ("Não tenho uma resposta exata para essa pergunta. O que a ficha de %s traz de mais "
                 "próximo é:\n\n%s" % (bot.compositor.itens[assunto]["nome"], texto))
    registro = {"pergunta": estado.fala, "id": novo_ident, "mecanismo": "leitura_ficha",
                "leitura": dict(evidencia, decision=decisao, subject=assunto)}
    if com_voz:
        registro["voz"] = "voz_propria"
    if bot.historico and bot.historico[-1].get("pergunta") == estado.fala:
        bot.historico[-1].clear()
        bot.historico[-1].update(registro)
    else:
        bot.historico.append(registro)
        bot.historico = bot.historico[-20:]
    bot.ultimo_turno = {"pergunta": estado.fala, "id": novo_ident}
    bot.assunto_conversa = assunto
    bot.esclarecimento = None
    estado.decidir("leitura_ficha", decisao, "%s recusou; a ficha de %s tem evidência (p=%.2f)"
                   % (especie, bot.compositor.itens[assunto]["nome"], leitura.prob))
    return novo_ident, texto
