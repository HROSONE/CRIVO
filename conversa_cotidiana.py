"""Atos curtos do bate-papo: respostas ao "como você está?", reações,
confirmações, pedidos de repetição, de continuação e de curiosidade.

Cada ato é reconhecido pela frase INTEIRA e interpretado com o turno
anterior. Nada aqui cria fatos: continuações e curiosidades apenas
selecionam unidades já cadastradas no compositor, com suas fontes.
"""
import random
import re

from conversa_assistente import normalizar

_POSITIVO = (r"(?:bem|muito bem|bem demais|otimo|otima|beleza|tranquilo|tranquila|"
             r"de boa|joia|show|feliz|em paz|bem sim|bem tambem|otimo tambem)")
_ESTADO = re.compile(
    r"(?:(?:sim|ah|ahh|opa)\s+)?"
    r"(?:(?:eu\s+)?(?:estou|to|tou|ando|me sinto|vou)|(?:ta\s+)?tudo|tudo (?:certo|joia|tranquilo) e)"
    r"\s+" + _POSITIVO +
    r"(?:\s+(?:tambem|sim|por aqui|e voce|obrigad[oa]|valeu|graças a deus|gracas a deus|"
    r"obrigad[oa] por perguntar|e com voce|e ai|e voce como esta|e voce como vai))*")
_RISADA = re.compile(r"(?:k{3,}|(?:ha){2,}h?|(?:he){2,}|(?:rs)+|lol|hahaha\w*|kkk\w*)")
_RECONHECIMENTO = re.compile(
    r"(?:(?:ah|ahh|hum|hmm|nossa|uau|uau|caramba|poxa|que|muito|bem)\s+)*"
    r"(?:legal|massa|show|top|bacana|bom|boa|otimo|interessante|incrivel|demais|"
    r"entendi|saquei|faz sentido|ok|okay|certo|ta bom|ta|ta certo|blz|beleza|"
    r"maravilha|perfeito|uau|que coisa)"
    r"(?:\s+(?:entao|mesmo|demais|hein|ne|isso|obrigad[oa]|valeu))*")
_DUVIDA_REACAO = re.compile(r"(?:serio|e mesmo|mesmo|verdade|jura|e serio|nao acredito)")
_SIM = re.compile(r"(?:sim|quero|claro|pode ser|pode|bora|manda|manda ver|com certeza|"
                  r"quero sim|sim por favor|pode falar|claro que sim|s)")
_NAO = re.compile(r"(?:nao|nao obrigad[oa]|agora nao|deixa pra la|deixa|tanto faz|nao precisa|"
                  r"nao quero|nao valeu)")
_MAIS = re.compile(r"(?:(?:(?:muito )?interessante|legal|que legal|show|massa|uau)\s+)?"
                   r"(?:me\s+)?(?:fala|fale|conta|conte|diga|diz|explica|explique)\s+mais"
                   r"(?:\s+(?:sobre isso|disso|sobre (?:ele|ela)|por favor))?|"
                   r"(?:quero saber|quero|tem|e) mais(?:\s+(?:sobre isso|disso|coisa))?|"
                   r"o que mais(?: voce sabe)?(?: sobre isso)?|continua|continue|mais")
_REPETIR = re.compile(r"(?:pode |poderia |consegue )?(?:repetir|repete|repita|falar de novo|"
                      r"dizer de novo)(?: (?:isso|a resposta|por favor|o que (?:voce )?disse))*|"
                      r"o que voce disse|como e que e")
_CURIOSIDADE = re.compile(
    r"(?:(?:me )?(?:conta|conte|diga|diz|fala|fale|da|de|manda|mande|tem|sabe)\s+)?"
    r"(?:uma|alguma|outra|mais uma)\s+curiosidade(?:\s+(?:sobre|de|do|da|dos|das)\s+(.+))?")
_PIADA = re.compile(r"(?:(?:me )?(?:conta|conte|fala|fale|sabe|manda)\s+)?(?:uma|alguma)\s+piada.*")
_GOSTO = re.compile(r"(?:voce )?gosta (?:de|do|da|dos|das) (.+)|"
                    r"(?:qual|quais) (?:e |sao )?(?:o |a |os |as )?(?:seu|sua|seus|suas) (.+?) "
                    r"(?:favorit[oa]s?|preferid[oa]s?)|"
                    r"voce tem (?:algum |alguma |um |uma )?(.+?) (?:favorit[oa]|preferid[oa])")
_MEU_NOME = re.compile(r"(?:qual (?:e )?(?:o )?meu nome|voce (?:sabe|lembra) (?:o )?meu nome|"
                       r"como (?:eu )?me chamo|quem sou eu|lembra (?:do|o) meu nome)")


def _limpar(texto):
    n = normalizar(texto)
    n = re.sub(r"^(?:crivo|ei crivo)\s+|\s+(?:crivo)$", "", n)
    return n.strip()


def _contexto_unico(bot):
    ctx = bot.contexto_textual
    if ctx is not None and len(ctx.temas) == 1 and ctx.temas[0] in bot.compositor.itens:
        return ctx
    # Uma resposta antiga ("E sobre Marte?") não tem contexto editorial,
    # mas a pergunta pode citar um único conceito com ficha e fontes.
    anterior = bot.ultimo_turno or {}
    if anterior.get("pergunta") and not anterior.get("id", "").startswith(("social:", "conversa:", "fora", "duvida")):
        ident = bot.compositor.assunto_mencionado(anterior["pergunta"])
        if ident is not None:
            from composicao_textual import ContextoTexto
            return ContextoTexto((ident,), (), (), "texto", "", "conhecimento")
    return None


def _nome_tema(bot, ctx):
    return bot.compositor.itens[ctx.temas[0]]["nome"]


def _continuar(bot, ctx):
    extras = bot.compositor._selecionar(ctx.temas, 2, ctx.usados)
    if not extras:
        return ("escrita:fim", "Já mostrei tudo o que tenho cadastrado sobre " + _nome_tema(bot, ctx) +
                ". Quer ver as fontes ou falar de outro assunto?", ctx, "")
    ident, resposta, novo = bot.compositor.compor(ctx.temas, "continuacao", anterior=ctx,
                                                   selecionados=extras)
    if bot.compositor._selecionar(novo.temas, 1, novo.usados):
        bot.conversacao.oferta = "continuar"
        resposta += "\n\nQuer saber mais?"
        novo = novo._replace(texto=resposta)
    return ident, resposta, novo, ""


def _curiosidade(bot, alvo):
    c = bot.compositor
    if alvo:
        ident = c.resolver(alvo)
        if ident not in c.expandidos:
            area = normalizar(alvo)
            candidatos = [e for e in c.expandidos if normalizar(c.itens[e].get("area", "")) == area]
            if not candidatos:
                return ("fora", "Ainda não tenho fatos cadastrados sobre “" + alvo +
                        "”. Quer uma curiosidade de astronomia?", None, "")
        else:
            candidatos = [ident]
    else:
        candidatos = [e for e in c.expandidos if c.itens[e].get("area") == "astronomia"] or list(c.expandidos)
    usados = bot.conversacao.curiosidades_usadas
    pares = [(e, i) for e in sorted(candidatos) for i, f in enumerate(c.itens[e]["fatos"])
             if f.get("papel") in ("detalhe", "exemplo") and (e, i) not in usados]
    if not pares:
        return ("escrita:fim", "Já contei as curiosidades que tenho sobre esse assunto.", None, "")
    escolha = bot.conversacao.sorteio.choice(pares)
    usados.add(escolha)
    _, texto, ctx = c.compor((escolha[0],), "explicacao", selecionados=(escolha,),
                             origem="conhecimento")
    resposta = ("Uma curiosidade sobre " + c.itens[escolha[0]]["nome"] + ": " +
                c._minuscula_inicial(texto) + "\n\nQuer saber mais sobre isso, a fonte ou outra curiosidade?")
    return "escrita:curiosidade", resposta, ctx._replace(texto=resposta), ""


def _convite(bot):
    return "Sobre o que você quer conversar? Posso falar de astronomia, natureza, ciência ou programação."


def responder(texto, bot):
    """Retorna (id, resposta, contexto, origem) ou None."""
    if not isinstance(texto, str) or len(texto) > 160:
        return None
    n = _limpar(texto)
    if not n:
        return None
    conversa = bot.conversacao
    anterior = bot.ultimo_turno or {}
    id_anterior = anterior.get("id", "")
    ctx_cache = []

    def contexto():
        if not ctx_cache:
            ctx_cache.append(_contexto_unico(bot))
        return ctx_cache[0]
    # Um "sim/não" pode estar respondendo a um esclarecimento pendente,
    # que tem fluxo próprio e não deve ser decidido aqui.
    pendente = bool(getattr(bot, "esclarecimento", None)) or id_anterior == "duvida"
    oferta = conversa.oferta
    conversa.oferta = None

    if _ESTADO.fullmatch(n):
        if id_anterior in ("social:oi", "social:tudobem"):
            ident = "social:acolhimento"
        else:
            ident = "social:estado"
        resposta = "Que bom!"
        if re.search(r"\be (?:com )?voce\b|\be ai\b", n):
            resposta += " Por aqui está tudo certo, obrigado por perguntar."
        return ident, resposta + " " + _convite(bot), None, ""

    if _MEU_NOME.fullmatch(n):
        nome = conversa.dialogo.dados.get("nome")
        if nome:
            return "conversa:memoria", "Você me disse que seu nome é " + nome + ".", None, ""
        return ("conversa:memoria", "Você ainda não me disse seu nome nesta conversa. "
                "Como quer que eu te chame?", None, "")

    if _REPETIR.fullmatch(n):
        ultima = conversa.ultima_resposta_texto
        if ultima:
            return "conversa:repeticao", ultima, bot.contexto_textual, ""
        return "duvida", "Ainda não respondi nada nesta conversa. O que você quer saber?", None, ""

    curiosidade = _CURIOSIDADE.fullmatch(n)
    if curiosidade:
        return _curiosidade(bot, curiosidade.group(1))

    if _PIADA.fullmatch(n):
        conversa.oferta = "curiosidade"
        return ("social:piada", "Ainda não sei contar piadas: só falo com base nos fatos que "
                "tenho cadastrados. Mas posso contar uma curiosidade de astronomia. Quer?", None, "")

    gosto = _GOSTO.fullmatch(n)
    if gosto and not re.search(r"\b(?:eu|meu|minha)\b", n):
        assunto = next(g for g in gosto.groups() if g)
        assunto = re.sub(r"^(?:o|a|os|as) ", "", assunto)
        c = bot.compositor
        conhecido = (c.resolver(assunto) in c.expandidos or c.resolver(re.sub(r"s$", "", assunto)) in c.expandidos
                     or any(normalizar(i.get("area", "")) == assunto for i in c.itens.values()))
        if not conhecido:
            return None
        conversa.oferta = "curiosidade:" + assunto
        return ("social:preferencia", "Não tenho gostos pessoais: sou um programa e não sinto "
                "preferência. Mas posso falar sobre " + assunto + " com o que tenho cadastrado. "
                "Quer uma curiosidade?", None, "")

    if _MAIS.fullmatch(n) and contexto() is not None:
        return _continuar(bot, contexto())

    if pendente and (_SIM.fullmatch(n) or _NAO.fullmatch(n)):
        return None

    if _SIM.fullmatch(n):
        if oferta == "curiosidade" or (oferta or "").startswith("curiosidade:"):
            alvo = oferta.partition(":")[2] or None
            if alvo and not bot.compositor.resolver(alvo) and not any(
                    normalizar(i.get("area", "")) == normalizar(alvo) for i in bot.compositor.itens.values()):
                alvo = None
            return _curiosidade(bot, alvo)
        ctx = contexto()
        if oferta == "continuar" and ctx is not None:
            return _continuar(bot, ctx)
        if id_anterior in ("social:oi", "social:tudobem"):
            return "social:acolhimento", "Que bom! " + _convite(bot), None, ""
        if ctx is not None:
            conversa.oferta = "continuar"
            return ("social:confirmacao", "Certo! Quer saber mais sobre " + _nome_tema(bot, ctx) +
                    " ou perguntar outra coisa?", ctx, "")
        if anterior:
            return "social:confirmacao", "Certo! O que você quer saber ou comentar?", None, ""
        return None

    if re.fullmatch(r"(?:talvez|nao sei|sei la|acho que (?:sim|nao)|mais ou menos|depende)", n) and anterior:
        return ("social:incerteza", "Sem problema. Se quiser, me conte mais ou faça uma pergunta "
                "sobre qualquer assunto.", None, "")

    if _NAO.fullmatch(n) and anterior:
        return "social:recusa", "Tudo bem! Se quiser, pergunte outra coisa ou mude de assunto.", None, ""

    if _RISADA.fullmatch(n):
        return ("social:risada", "Haha! Que bom que achou graça. Quer continuar no assunto ou "
                "perguntar outra coisa?", contexto(), "")

    if _DUVIDA_REACAO.fullmatch(n):
        ctx = contexto()
        if ctx is not None:
            conversa.oferta = "continuar"
            return ("social:confirmacao", "Sim, é o que dizem os fatos que tenho cadastrados sobre " +
                    _nome_tema(bot, ctx) + ". Se quiser conferir, peça “qual é a fonte?”. "
                    "Quer saber mais?", ctx, "")
        return "social:reacao", "Pois é! Quer me contar mais ou perguntar alguma coisa?", None, ""

    if _RECONHECIMENTO.fullmatch(n):
        # "Beleza?" sem conversa anterior é cumprimento, tratado adiante.
        if n in ("beleza", "blz") and (not anterior or "?" in texto):
            return None
        ctx = contexto()
        if ctx is not None:
            conversa.oferta = "continuar"
            return ("social:reconhecimento", "Que bom! Quer saber mais sobre " + _nome_tema(bot, ctx) +
                    "? É só dizer “sim”, ou pergunte outra coisa.", ctx, "")
        if anterior:
            return "social:reconhecimento", "Certo! " + _convite(bot), None, ""
    return None
