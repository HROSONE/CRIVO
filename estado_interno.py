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
# Pedido de escrita (imperativo); "quem escreveu" é pergunta factual.
_PEDIDO_ESCRITA = re.compile(r"\b(?:escreva|escreve|escrever|resum\w*|redija|frases?|roteiro|topicos|"
                             r"paragrafos?|linhas?|redacao|poema)\b")
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
    # "Onde fica o Egito?" e "O que fazem os rins?" não têm pistas além do
    # assunto: o tipo da pergunta guia a leitura, que confere sozinha.
    if q is None or q.recusa and q.recusa != "sem_pistas" or q.outros or estado.negacao:
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
    if ident in REVISAVEIS and _pode_buscar(estado):
        return _ler_pela_busca(bot, estado, especie, ident, resposta)
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
        # A ficha citada não tem a resposta; numa pergunta aberta, ela pode
        # estar em outra ("Que cientista estudou a evolução?"). Sim/não e
        # "o que é X" são sobre a ficha citada: a recusa fica.
        if estado.tipo != "simnao" and not estado.quadro.pedido_nome:
            return _ler_pela_busca(bot, estado, especie, ident, resposta, citado=estado.entidade.id)
        estado.decidir(especie, "recusar", "a leitura da ficha não achou evidência suficiente")
        return ident, resposta
    return _responder_com_leitura(bot, estado, especie, leitura, decisao, evidencia)


def _responder_com_leitura(bot, estado, especie, leitura, decisao, evidencia, motivo=None):
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
    # Achado pela busca (fora da ficha citada) ou lido na ficha citada.
    mecanismo = "busca_aprendida" if "search_subject" in evidencia else "leitura_ficha"
    registro = {"pergunta": estado.fala, "id": novo_ident, "mecanismo": mecanismo,
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
    estado.decidir(mecanismo, decisao, motivo or "%s recusou; a ficha de %s tem evidência (p=%.2f)"
                   % (especie, bot.compositor.itens[assunto]["nome"], leitura.prob))
    return novo_ident, texto


# Busca aprendida (busca_semantica.py): quando a pergunta não cita o nome de
# nenhum assunto, a busca procura o fato no acervo inteiro e a leitura da
# ficha confere se ele responde. A busca ordena bem, mas não sabe quando não
# há resposta; por isso só fala quando a leitura do fato achado o confirma
# (pelo menos duas pistas cobertas; afirmar exige todas).
LIMIAR_BUSCA = 0.5
LIMIAR_BUSCA_APROXIMAR = 0.7
LIMIAR_BUSCA_MINIMO = 0.2


def _pode_buscar(estado):
    """Pergunta factual sem nenhuma entidade reconhecida (nem da conversa),
    sem negação, relação, pedido de escrita ou pergunta pessoal. "O que é
    Ceres?" sem ficha de Ceres pede a identidade de algo desconhecido: um
    fato que só cita o nome não é a resposta, e a recusa continua."""
    q = estado.quadro
    if q is None or q.pedido_nome or estado.negacao:
        return False
    # "Qual organela produz ATP nas células?" cita dois conceitos, e a
    # resposta está numa terceira ficha. Relação com direção ("a memória
    # ajuda o sono?") continua recusada: só perguntas abertas, não sim/não.
    relacao = q.recusa == "relacao_entre_conceitos" and estado.tipo != "simnao"
    # Muitas palavras de conteúdo ("Por que uma geada que destrói parte da
    # safra de café faz o preço subir?") desanimam a busca por palavras
    # exatas, não a busca aprendida; a leitura continua conferindo cada pista.
    longa = q.recusa == "tamanho" and len(estado.fala) <= 200 or q.recusa == "sem_pistas" and len(q.pistas) > 6
    if not (relacao or longa) and (q.recusa or q.assunto or q.outros or estado.entidades):
        return False
    if longa and (q.assunto or q.outros or estado.entidades):
        return False
    if relacao and any(e.origem != "fala" for e in estado.entidades):
        return False
    n = normalizar(estado.fala)
    return not (_PEDIDO_ESCRITA.search(n) or _PESSOAL.search(n))


def _ler_pela_busca(bot, estado, especie, ident, resposta, citado=None):
    """citado: a ficha citada na fala, cuja leitura já não achou resposta; a
    busca só fala se achar outra ficha. Duas propostas, a da busca aprendida e
    a da busca só por palavras (melhor quando a pergunta não traz nome
    nenhum); a leitura confere cada uma e fala a que ela confirmar."""
    from leitura_ficha import busca_aprendida
    busca = busca_aprendida(bot.compositor)
    # As fichas citadas já foram lidas (ou a pergunta as relaciona): vale o
    # melhor fato de outra ficha.
    citados = {e.id for e in estado.entidades} | ({citado} if citado else set())
    achados = [a for a in (busca.buscar(estado.fala, k=10) if busca.aprendida else ()) if a[1] not in citados]
    if not achados:
        estado.decidir(especie, "recusar", "a leitura da ficha não achou evidência suficiente" if citado
                       else "sem fato achado pela busca fora das fichas citadas")
        return ident, resposta
    # Probabilidade entre os fatos que sobraram (fora das fichas citadas).
    total = sum(a[0] for a in achados)
    probs = {(a[1], a[2]): a[0] / total for a in achados}
    propostas = [achados[0][1:]]
    palavras = next((a for a in busca.buscar_palavras(estado.fala, k=10) if a[0] not in citados), None)
    if palavras is not None and palavras not in propostas:
        propostas.append(palavras)
    conferidas = [_conferir(bot, estado, busca, probs.get(alvo, 0.0), *alvo) for alvo in propostas]
    ordem = {"afirmar": 2, "aproximar": 1, None: 0}
    decisao, leitura, evidencia, prob = max(
        conferidas, key=lambda c: (ordem[c[0]], c[1].prob if c[1] is not None else 0.0))
    assunto = evidencia["search_subject"]
    estado.propor("busca_aprendida", None, decisao or "calar", evidencia)
    if decisao is None:
        estado.decidir(especie, "recusar", "a busca achou %s, mas a leitura não confirmou"
                       % bot.compositor.itens[assunto]["nome"])
        return ident, resposta
    return _responder_com_leitura(
        bot, estado, especie, leitura, decisao, evidencia,
        "%s recusou; a busca achou %s (p=%.2f) e a leitura confirmou (p=%.2f)"
        % (especie, bot.compositor.itens[assunto]["nome"], prob, leitura.prob))


def _conferir(bot, estado, busca, prob, assunto, indice):
    """Leitura do fato proposto pela busca: (decisão, leitura, evidência, prob)."""
    from busca_semantica import PARADAS
    from leitura_ficha import GENERICAS
    # Pistas: todas as palavras de conteúdo da fala, inclusive os nomes de
    # conceitos citados ("ATP", "células"), menos o nome do assunto achado.
    c = bot.compositor
    nome = {w for f in busca.nomes.get(assunto, ()) for w in f.split()}
    raizes_nome = {w[:5] for w in nome}
    pistas = []
    for palavra in estado.quadro.forma.replace("-", " ").replace(",", " ").split():
        palavra = palavra.strip("?!.;:")
        if (palavra in c._FORMA_PERGUNTA or palavra in PARADAS or palavra in GENERICAS or len(palavra) < 3
                or palavra in nome or palavra[:5] in raizes_nome):
            continue
        palavra = c._FORMAS_VER.get(palavra, palavra)
        raiz = c._raiz(palavra)
        if raiz not in (r for r, _ in pistas):
            pistas.append((raiz, palavra))
    pistas = tuple(pistas)
    quadro = estado.quadro._replace(assunto=assunto, outros=(), pistas=pistas, recusa="")
    leitor = bot.leitura_ficha
    # A leitura confere o fato que a busca achou: todas as pistas cobertas.
    leitura = leitor.ler(quadro, assunto, indice) if pistas else None
    decisao = leitor.decisao(leitura)
    evidencia = {"search_subject": assunto, "search_fact": indice, "search_probability": round(prob, 4)}
    if leitura is not None:
        evidencia.update({"fact": leitura.indice, "probability": leitura.prob, "margin": leitura.margem,
                          "cues_covered": leitura.cobertura, "question_type": leitura.tipo})
    # Duas pistas cobertas no mínimo: uma só palavra em comum não basta para
    # dizer que um fato achado sem o nome do assunto responde. Aproximar ("não
    # tenho a resposta exata; o mais próximo é…") pede a busca mais confiante.
    cob = leitura.cobertura if leitura is not None else 0
    # Pergunta longa: a leitura só aproxima se faltar no máximo uma pista;
    # aqui basta cobrir três ou mais e pelo menos metade delas (perguntas sem
    # resposta no acervo cobrem uma ou nenhuma).
    if (decisao is None and leitura is not None and leitor.aprendida and cob >= 3
            and 2 * cob >= len(leitor.pistas(quadro)) and leitura.prob >= leitor.limiar_aproximar
            and leitura.tracos.get("pergunta_direta") and not leitura.tracos.get("absoluto")
            and not leitura.tracos.get("tipo_sem_par")):
        decisao = "aproximar"
    # A probabilidade da busca cai quando a ficha tem vários fatos parecidos;
    # com a leitura cobrindo três pistas ou mais, a evidência dela compensa.
    if not (cob >= 2 and (decisao == "afirmar" and prob >= LIMIAR_BUSCA
                          or decisao == "aproximar" and (prob >= LIMIAR_BUSCA_APROXIMAR
                                                         or cob >= 3 and prob >= LIMIAR_BUSCA_MINIMO))):
        decisao = None
    return decisao, leitura, evidencia, prob
