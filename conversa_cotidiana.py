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
    r"maravilha|perfeito|uau|que coisa|nao sabia(?: disso)?|que interessante)"
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
_SUFIXO_SIMPLES = (r"(?: como se eu (?:tivesse|fosse) .+| de (?:um )?jeito (?:simples|facil)|"
                   r" de forma simples| para (?:uma )?crianca)")
_ENSINO = re.compile(
    r"(?:(?:eu )?(?:quero|queria|gostaria de) (?:aprender|estudar)(?: mais)?"
    r" (?:sobre|a respeito de) (.+?)" + _SUFIXO_SIMPLES + r"?|"
    r"(?:me )?(?:ensina|ensine)(?: (?:alguma coisa|algo|um pouco|mais))?(?: (?:legal|interessante|bacana))?"
    r" (?:sobre|de|do|da|dos|das|a respeito de) (.+?)" + _SUFIXO_SIMPLES + r"?|"
    r"(?:me )?(?:explica|explique|ensina|ensine) (.+?)" + _SUFIXO_SIMPLES + r")")
_SIMPLES = re.compile(r"como se eu (?:tivesse|fosse)|jeito (?:simples|facil)|forma simples|para (?:uma )?crianca")
_SOBRE_MIM = (
    (re.compile(r"voce (?:e|eh) (?:melhor|pior|mais inteligente) (?:que|do que) (?:o |a )?.+|"
                r"voce (?:e|eh) (?:o |a )?(?:chatgpt|gpt|gemini|copilot|siri|alexa)"),
     "Sou bem menor e mais limitado que assistentes como o ChatGPT. Fui construído do zero, "
     "com redes pequenas e fichas de conhecimento com fonte. Em compensação, não invento: "
     "quando não tenho o fato cadastrado, digo que não sei, e posso mostrar a fonte do que respondo."),
    (re.compile(r"voce aprende (?:comigo|com (?:a |as )?(?:conversa|conversas|o que eu (?:falo|digo))|sozinho)"),
     "Não aprendo sozinho com as conversas. Durante esta conversa lembro o que você me contou, "
     "como seu nome e o assunto atual, mas isso não muda meu conhecimento. Meu conhecimento "
     "cresce quando novas fichas com fonte são revisadas e adicionadas ao projeto."),
    (re.compile(r"o que voce nao sabe|quais (?:sao )?(?:os )?seus limites|voce sabe tudo"),
     "Sei apenas o que está nas minhas fichas, e há muita coisa fora delas. Em astronomia, por "
     "exemplo, conheço planetas, luas, estrelas e galáxias, mas não tenho dados sobre muitos "
     "objetos específicos. Quando não sei, prefiro dizer isso a inventar."),
    (re.compile(r"por que voce (?:erra|errou|se engana)|voce (?:erra|pode errar)"),
     "Erro principalmente quando interpreto mal a pergunta, por exemplo uma palavra que eu "
     "não conheço ou uma frase muito diferente das que já vi. Se a resposta não fizer sentido, "
     "me diga; isso ajuda a corrigir o projeto."),
)
_FONTE_DISSO = re.compile(r"(?:qual (?:e )?a fonte|quais (?:sao )?as fontes) (?:disso|dessa (?:resposta|informacao))|"
                          r"de onde (?:voce )?tirou (?:isso|essa informacao)|onde (?:voce )?(?:leu|viu) isso")
_OUTRA_COISA = re.compile(r"(?:(?:valeu|obrigad[oa]|ok|certo|beleza),? )?(?:outra coisa|tenho outra pergunta|"
                          r"mudando de assunto|outra pergunta|deixa eu (?:te )?perguntar outra coisa)")
_QUIZ = re.compile(r"(?:me )?(?:faz|faca|faça|manda|mande|da|de) (?:umas?|algumas?|mais umas?) perguntas?(?: (?:para|pra) (?:eu )?(?:treinar|estudar|praticar))?(?: sobre (.+))?|"
                   r"(?:me )?(?:testa|teste)(?: sobre (.+))?|quero (?:treinar|praticar|ser testado)(?: sobre (.+))?")
_TEMA = re.compile(r"(?:o )?(?:tema|assunto|conteudo|materia) (?:e|eh|vai ser|sera) (?:sobre )?(.+)")
_O_QUE_CONTEI = re.compile(r"(?:(?:e )?(?:sobre )?o que (?:foi que )?eu (?:te )?(?:falei|contei|disse)(?: antes| hoje| ate agora)?|"
                           r"(?:do que|sobre o que) (?:a gente|nos) (?:falou|falamos|conversamos)(?: ate agora)?|"
                           r"(?:voce )?lembra o que eu (?:te )?(?:falei|contei|disse))")
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


_ORDINAIS = ("primeiro", "segundo", "terceiro", "quarto", "quinto", "sexto", "setimo", "oitavo")


def _lacuna(texto, nome):
    """Escolhe a palavra a esconder: número, ordinal ou nome próprio
    (que não seja o próprio assunto). Devolve (pergunta, resposta)."""
    palavras = texto.split()
    alvo = None
    for k, w in enumerate(palavras):
        limpa = w.strip(".,;:()")
        if re.fullmatch(r"\d[\d.,]*", limpa) and not re.fullmatch(r"(?:19|20)\d\d", limpa):
            alvo = k
            break
    if alvo is None:
        for k, w in enumerate(palavras):
            if normalizar(w.strip(".,;:()")) in _ORDINAIS:
                alvo = k
                break
    if alvo is None:
        nomes = set(normalizar(nome).split())
        for k, w in enumerate(palavras[1:], 1):
            limpa = w.strip(".,;:()")
            seguinte = palavras[k + 1] if k + 1 < len(palavras) else ""
            # Nome composto ("Via Láctea") não vira lacuna pela metade.
            if (limpa[:1].isupper() and normalizar(limpa) not in nomes and len(limpa) > 2
                    and not seguinte[:1].isupper() and not palavras[k - 1][:1].isupper()):
                alvo = k
                break
    if alvo is None:
        return None
    resposta = palavras[alvo].strip(".,;:()")
    lacunado = " ".join("_____" + w[len(w.rstrip(".,;:()")):] if k == alvo else w
                        for k, w in enumerate(palavras))
    return lacunado, resposta


def _escopo_quiz(bot, alvo):
    c = bot.compositor
    if alvo:
        alvo = re.sub(r"^(?:o|a|os|as) ", "", normalizar(alvo))
        ident = c.resolver(alvo) or c.aliases_busca.get(alvo)
        if ident:
            return [ident]
        area = [e for e in c.expandidos if normalizar(c.itens[e].get("area", "")) == alvo
                or alvo in normalizar(c.itens[e]["nome"])]
        if area:
            return area
    elif bot.assunto_conversa in c.itens:
        return [bot.assunto_conversa]
    return [e for e in c.expandidos if c.itens[e].get("area") == "astronomia"]


def _opcoes_quiz(bot, candidatos):
    c = bot.compositor
    usados = bot.conversacao.curiosidades_usadas
    opcoes = []
    for e in sorted(candidatos):
        for i, f in enumerate(c.itens[e]["fatos"]):
            if (e, i) in usados or f.get("papel") not in ("definicao", "detalhe", "exemplo"):
                continue
            if re.search(r"\bn[aã]o\b", f["texto"]) or len(f["texto"]) > 170:
                continue
            lacuna = _lacuna(f["texto"], c.itens[e]["nome"])
            if lacuna:
                opcoes.append((e, i, lacuna))
    return opcoes


def _quiz(bot, alvo, continuar=False):
    """Pergunta de completar a frase. O escopo (um conceito ou uma área)
    fica guardado para que “outra” continue no mesmo tema; quando o
    conceito se esgota, as perguntas passam para a área dele."""
    c = bot.compositor
    conversa = bot.conversacao
    escopo = getattr(conversa, "quiz_escopo", None)
    if not (continuar and escopo):
        escopo = _escopo_quiz(bot, alvo)
    opcoes = _opcoes_quiz(bot, escopo)
    aviso = ""
    if not opcoes and len(escopo) == 1:
        area = c.itens[escopo[0]].get("area")
        escopo = [e for e in c.expandidos if c.itens[e].get("area") == area]
        opcoes = _opcoes_quiz(bot, escopo)
        if opcoes:
            aviso = "Acabaram as perguntas sobre esse assunto; vamos para " + (area or "outro tema") + ".\n\n"
    conversa.quiz_escopo = escopo
    if not opcoes:
        return ("escrita:fim", "Não tenho mais perguntas prontas sobre esse assunto. "
                "Quer treinar outro tema?", None, "")
    e, i, (pergunta, resposta) = conversa.sorteio.choice(opcoes)
    conversa.curiosidades_usadas.add((e, i))
    conversa.quiz = {"resposta": resposta, "par": (e, i), "assunto": e}
    return ("estudo:pergunta", aviso + "Complete a frase:\n\n" + pergunta +
            "\n\nResponda com a palavra que falta. Se quiser, diga “não sei”.", None, "")


def _corrigir_quiz(bot, texto):
    quiz = bot.conversacao.quiz
    bot.conversacao.quiz = None
    c = bot.compositor
    e, i = quiz["par"]
    _, fato, ctx = c.compor((e,), "explicacao", selecionados=((e, i),), origem="conhecimento")
    n = normalizar(texto)
    n = re.sub(r"^(?:a resposta (?:e|eh)|e|acho que (?:e|eh)?|seria|eh)\s+", "", n).strip(" .!?")
    certa = normalizar(quiz["resposta"])
    bot.conversacao.quiz_acertou = False
    if re.fullmatch(r"(?:nao sei|sei la|desisto|passo|pula)", n):
        inicio = "Sem problema. A resposta é “" + quiz["resposta"] + "”."
    elif n == certa or re.search(r"(?<![\w,.])" + re.escape(certa) + r"(?![\w,])", n):
        inicio = "Acertou!"
        bot.conversacao.quiz_acertou = True
    else:
        inicio = "Não foi dessa vez. A resposta é “" + quiz["resposta"] + "”."
    resposta = inicio + "\n\n" + fato + "\n\nQuer outra pergunta? É só dizer “outra”."
    bot.conversacao.oferta = "quiz"
    return "estudo:correcao", resposta, ctx._replace(texto=resposta), ""


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

    # Resposta a uma pergunta de estudo pendente vem antes de tudo.
    if getattr(conversa, "quiz", None):
        if re.fullmatch(r"(?:outra|proxima|mais uma|pula|passa)", n):
            conversa.quiz = None
            return _quiz(bot, None, continuar=True)
        else:
            return _corrigir_quiz(bot, texto)

    if id_anterior.startswith("nocao:") and re.fullmatch(
            r"(?:pois e|pois e ne|e mesmo|ne|aham|uhum|verdade|e|sim|e verdade|sei la|fazer o que|"
            r"e assim mesmo|e a vida|ta|ta bom|ok)", n):
        return "nocao:reacao", "Pois é. Quer me contar mais sobre isso?", None, ""

    if _O_QUE_CONTEI.fullmatch(n) and conversa.relatos and not conversa.assunto:
        contados = list(conversa.relatos)[-3:]
        return ("conversa:memoria", "Você me contou: “" + "”; “".join(contados) + "”. "
                "Quer continuar em algum desses assuntos?", None, "")

    estudando = oferta == "quiz" or (id_anterior or "").startswith("estudo:")
    if estudando and getattr(conversa, "quiz_acertou", None) is not None and \
            re.fullmatch(r"(?:e )?(?:eu )?(?:acertei|errei|ta certo|esta certo|certo)", n):
        acertou = conversa.quiz_acertou
        conversa.oferta = "quiz"
        return ("estudo:resultado", ("Sim, você acertou!" if acertou else "Dessa vez não; a resposta certa "
                "está logo acima.") + " Quer outra pergunta? É só dizer “outra”.", None, "")
    quiz = _QUIZ.fullmatch(n)
    if quiz:
        alvo_quiz = next((g for g in quiz.groups() if g), None)
        # "me faça uma pergunta sobre isso" é exploração do relato, não quiz.
        if alvo_quiz and re.fullmatch(r"(?:isso|isto|ele|ela|(?:a|o|minha|meu) .+)", alvo_quiz) \
                and not (bot.compositor.resolver(alvo_quiz) or bot.compositor.aliases_busca.get(alvo_quiz)):
            quiz = None
        elif not alvo_quiz and not re.search(r"\b(?:perguntas|treinar|estudar|praticar|testa|teste|testado)\b", n):
            quiz = None
    if quiz or (estudando and re.fullmatch(r"(?:outra|proxima|mais uma|sim|quero|manda)", n)):
        alvo = next((g for g in (quiz.groups() if quiz else ()) if g), None)
        return _quiz(bot, alvo, continuar=not quiz)

    for padrao, texto_mim in _SOBRE_MIM:
        if padrao.fullmatch(n):
            return "social:sobre_mim", texto_mim, None, ""

    if _FONTE_DISSO.fullmatch(n):
        ctx = bot.contexto_textual
        if ctx is not None:
            return (*bot.compositor._fontes(ctx), "")
        return ("duvida", "Minha última resposta não veio de uma ficha com fonte cadastrada. "
                "Sobre qual informação você quer a fonte?", None, "")

    tema_estudo = _TEMA.fullmatch(n)
    if tema_estudo:
        c = bot.compositor
        alvo = re.sub(r"^(?:o|a|os|as) ", "", tema_estudo.group(1))
        ident = c.resolver(alvo) or c.aliases_busca.get(alvo)
        if ident in c.itens:
            bot.assunto_conversa = ident
            conversa.oferta = "tema"
            return ("social:tema", "Ótimo, vamos de " + c.itens[ident]["nome"][:1].upper() + c.itens[ident]["nome"][1:] + ". Quer que eu explique "
                    "o básico ou que faça perguntas para você treinar?", None, "")

    if oferta == "tema" and bot.assunto_conversa in bot.compositor.itens:
        if re.search(r"\b(?:pergunta|perguntas|treinar|testa|teste|quiz)\b", n):
            conversa.quiz_escopo = None
            return _quiz(bot, None)
        if re.search(r"\b(?:explica|explique|basico|explicar|ensina)\b", n):
            c = bot.compositor
            ident_r, resposta, ctx = c.compor((bot.assunto_conversa,), "explicacao", limite=3)
            return ident_r, resposta, ctx._replace(texto=resposta), ""

    if _OUTRA_COISA.fullmatch(n):
        return "social:convite", "Claro! Pode perguntar.", None, ""

    ensino = _ENSINO.fullmatch(n)
    if ensino:
        alvo = next(g for g in ensino.groups() if g)
        alvo = re.sub(r"^(?:sobre|a respeito de) ", "", alvo)
        alvo = re.sub(r"^(?:o|a|os|as|um|uma) ", "", alvo).strip()
        if re.match(r"(?:como|por que|porque|quando|onde|quanto|quantos|quantas|qual|quais|se|o que) ", alvo):
            alvo = ""
        c = bot.compositor
        ident = c.resolver(alvo) or c.aliases_busca.get(alvo) or c.resolver(re.sub(r"s$", "", alvo)) \
            or c.aliases_busca.get(re.sub(r"s$", "", alvo))
        if ident in c.itens:
            simples = bool(_SIMPLES.search(n))
            ident_r, resposta, ctx = c.compor((ident,), "simples" if simples else "explicacao",
                                              limite=2 if simples else 3)
            conversa.oferta = "continuar"
            resposta += "\n\nQuer saber mais, ver a fonte ou treinar com perguntas sobre isso?"
            return ident_r, resposta, ctx._replace(texto=resposta), ""
        if any(normalizar(i.get("area", "")) == alvo for i in c.itens.values()):
            return _curiosidade(bot, alvo)

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
    return _observacao(texto, bot, id_anterior)


_NOCOES = []


def nocoes():
    if not _NOCOES:
        from nocoes import NocoesPT
        _NOCOES.append(NocoesPT())
    return _NOCOES[0]


def _observacao(texto, bot, id_anterior):
    """Algo que a pessoa conta sobre o dia ("hoje choveu o dia todo"):
    reagir com uma noção dita como noção e perguntar de volta, em vez de
    dar uma explicação que ninguém pediu."""
    conversa = bot.conversacao
    base = nocoes()
    # Uma conversa guiada em andamento ("quero conversar sobre meu
    # desenho", objetivo, escolha entre opções) continua com o diálogo.
    guiada = (conversa.assunto not in (None, "sua situação") or conversa.objetivo
              or conversa.dialogo.espera in ("interesse", "preferencia", "obstaculo", "criterio",
                                             "argumento", "tema"))
    if not base.afirmacao(texto) or guiada or getattr(bot, "esclarecimento", None):
        return None
    # Relato que é exatamente o tema de uma resposta da base (ex.: folhas
    # amarelas) fica com a base, que tem a orientação.
    ranking = bot._ranking(texto)
    if ranking and ranking[0][0] >= 1.4 and bot._base_cobre(texto, normalizar(texto), None, tolerancia=1):
        return None
    achadas = base.encontrar(texto)
    if achadas:
        principal, resposta = base.observar(texto, conversa.sorteio, achadas)
        ident = "nocao:observacao"
    elif (id_anterior.startswith("nocao:") and getattr(bot, "nocao_conversa", None)
          and len(normalizar(texto).split()) >= 3):
        principal = bot.nocao_conversa
        resposta = base.continuar(texto, principal, conversa.sorteio)
        ident = "nocao:continuacao"
    else:
        return None
    bot.nocao_conversa = principal
    conversa.relatos.append(texto.strip()[:600])
    return ident, resposta, None, ""
