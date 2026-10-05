"""Autodescrição apoiada na configuração ativa, sem recuperação por semelhança."""
import re
import unicodedata


def normalizar(texto):
    n = unicodedata.normalize("NFD", texto.lower())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    n = " ".join(re.findall(r"[a-z0-9]+", n))
    return re.sub(r"\b(?:vc|tu)\b", "voce", n)


# Gramática de atos completos. Palavras como 'burro', 'beleza' e 'errado'
# dentro de uma pergunta factual não bastam para classificar a mensagem.
_SAUDACAO = r"(?:oi+|ola|opa|salve|hey|hello|e ?ai|e ?ae|bom dia|boa tarde|boa noite)"
_VOCATIVO = r"(?:crivo|mano|cara|vei|velho|parceiro|parceira|amigo|amiga|meu amigo|minha amiga)"
_CONTATO = (
    r"(?:(?:tudo|td) (?:bem|bom|certo|beleza)|beleza|blz|tranquilo|de boa|"
    r"como (?:(?:voce|ce) )?(?:esta|ta|vai)|como (?:estao|vao) as coisas)"
)
_FINAL_CONTATO = r"(?: (?:ai|por ai|com voce|" + _VOCATIVO + r"))?"
_INTENSIDADE = r"(?:(?:muito|bem|tao|um|uma|completamente|totalmente|bastante) )*"
_CRITICA = (
    r"(?:(?:voce|crivo) (?:e|eh|esta|ta|foi|ficou) " + _INTENSIDADE +
    r"(?:burro|burra|idiota|ruim|confuso|confusa|limitado|limitada)|"
    r"(?:voce |crivo )?nao (?:sabe|entende|compreende) (?:de )?(?:nada|coisa nenhuma|nem o basico)|"
    r"(?:isso|essa resposta|sua resposta|a resposta) (?:e|eh|esta|ta|ficou) " + _INTENSIDADE +
    r"(?:errado|errada|ruim|confuso|confusa|sem sentido)|"
    r"(?:nao foi|nao e|nao era) (?:isso|o que) (?:que )?eu (?:perguntei|pedi|quis dizer)|"
    r"(?:nao foi|nao era) (?:bem |exatamente )?isso|"
    r"(?:voce )?nao (?:me )?entendeu(?: (?:minha pergunta|meu pedido|o que eu (?:pedi|perguntei)))?|"
    r"(?:isso|essa resposta|sua resposta) nao faz sentido|"
    r"nao gostei (?:disso|da resposta)|que resposta (?:ruim|confusa|errada))"
)
_OFENSA = r"(?:idiota|otario|otaria|imbecil|desgracado|desgracada|inutil)"
_OFENSAS_DIRIGIDAS = (
    r"(?:(?:seu|sua|infeliz) )?(?:" + _OFENSA + r"|infeliz burro|infeliz burra)|"
    r"(?:seu|sua) (?:burro|burra|lixo)|"
    r"(?:voce|crivo) (?:e|eh|esta|ta) " + _INTENSIDADE +
    r"(?:" + _OFENSA + r"|lixo)|vai (?:pro|para o) inferno"
)
_INTERROMPER = (
    r"(?:(?:crivo|voce) )?(?:cala a boca|cale a boca|"
    r"(?:pare|para) de (?:falar|responder)|fique quieto|fica quieto|"
    r"nao (?:responda|responde)(?: mais)?)"
    r"(?: (?:entao|agora|por favor))?"
)
_DESISTENCIA = r"(?:desisto|(?:deixa|deixe) (?:pra|para) la)(?: entao)?"


def frustracao_recente(historico):
    """Só atos reconhecidos no diálogo abrem uma janela de três turnos.

    Uma nova saudação, despedida ou reinício encerra a janela. Palavras
    ambíguas isoladas não criam o contexto que as classifica como crítica.
    """
    for turno in reversed(list(historico)[-3:]):
        ident = turno.get("id", "")
        if ident in ("social:oi", "social:tchau", "social:despedida", "conversa:reinicio"):
            return False
        if ident in ("social:critica", "social:interromper", "social:desistencia"):
            return True
    return False


def identificar_contato(texto, contexto_frustracao=False):
    # Citações e código descrevem conteúdo, não um ato dirigido ao bot.
    if any(c in texto for c in ('`', '"', '“', '”', "'", '‘', '’')):
        return None
    n = normalizar(texto)
    if re.fullmatch(r"(?:meu deus|nossa(?: senhora)?|caramba|eita|poxa|vixe|aff+)", n):
        return "reacao"
    if re.fullmatch("(?:" + _SAUDACAO + r"(?: " + _VOCATIVO + r")? )?(?:" +
                    _VOCATIVO + r" )?" + _CONTATO + _FINAL_CONTATO, n):
        return "contato"
    if re.fullmatch(_SAUDACAO + r"(?: " + _VOCATIVO + r")?", n):
        return "saudacao"
    if re.fullmatch(_INTERROMPER, n):
        return "interromper"
    if re.fullmatch(_DESISTENCIA, n):
        return "desistencia"
    if re.fullmatch("(?:" + _CRITICA + "|" + _OFENSAS_DIRIGIDAS +
                    r")(?: (?:tambem|mesmo|demais|hein))?", n):
        return "critica"
    if contexto_frustracao and re.fullmatch(r"(?:lixo|burro|burra)", n):
        return "critica"
    if re.fullmatch(
        r"(?:mandou bem|boa resposta|gostei(?: da resposta)?|muito bom|perfeito|"
        r"(?:voce|crivo) (?:e|eh) (?:muito )?(?:inteligente|legal|bom|boa))", n,
    ):
        return "elogio"
    if re.fullmatch(r"(?:obrigad[oa]|valeu|brigad[oa]|thanks)(?: crivo)?", n):
        return "agradecimento"
    if re.fullmatch(
        r"(?:vamos|bora|quero|podemos) (?:conversar|bater um papo)(?: com voce)?", n,
    ):
        return "conversar"
    return None


def preparar_conversa(texto):
    """Retira atos completos antes de um pedido, conservando seu conteúdo.

    Usa os índices da frase original, sem normalizar nomes, código ou a
    negação do pedido. Uma crítica só é separada com pontuação explícita.
    """
    if identificar_contato(texto) is not None:
        return texto
    texto = re.sub(r"^\s*(?:me (?:fala|diz|conta) uma coisa|"
                   r"(?:deixa|deixe) eu te perguntar(?: uma coisa)?)[,:;]\s*", "", texto, count=1, flags=re.I)
    for _ in range(4):
        # A vírgula pode separar um vocativo da saudação. Conservamos o
        # maior ato completo: “Oi, velho!” antes de começar a consulta.
        abertura = None
        for separador in re.finditer(r"[.!?;:,\n]+\s*", texto):
            prefixo = texto[:separador.start()]
            tipo = identificar_contato(prefixo)
            if tipo is not None and texto[separador.end():].strip():
                abertura = (separador.end(), tipo)
        if abertura is not None:
            texto = texto[abertura[0]:].strip()
            if abertura[1] == "critica":
                texto = re.sub(r"^mas\s+", "", texto, count=1, flags=re.I)
            continue
        # 'beleza o que é DNA?' não exige vírgula para uma abertura social.
        abertura = re.match(
            r"^(?:beleza|blz|tudo (?:bem|bom|certo)|de boa)\s+"
            r"(?=(?:o que|como|qual|quais|escreva|explique|voce|voc[eê])\b)",
            texto, re.I,
        )
        if abertura:
            texto = texto[abertura.end():]
            continue
        break
    # Vocativo sem vírgula também pode abrir uma consulta. Só removemos
    # a abertura se o restante começar por um pedido explícito conhecido.
    abertura = re.match(
        r"^([^.!?;:,\n]+?)\s+(?=(?:o que|como|qual|quais|escreva|explique|defina)\b)",
        texto, re.I,
    )
    if abertura and identificar_contato(abertura.group(1)) == "saudacao":
        texto = texto[abertura.end():]
    return texto


def responder_contato(texto, anterior=None, historico=()):
    if any(c in texto for c in ('`', '"', '“', '”', "'", '‘', '’')):
        return None
    tipo = identificar_contato(texto, frustracao_recente(historico))
    n = normalizar(texto)
    if (anterior and anterior["id"] in ("social:tudobem", "social:oi") and re.fullmatch(
            r"(?:sim|(?:estou|to|tou) (?:bem|de boa|tranquilo|tranquila)(?: tambem)?|"
            r"tudo (?:bem|certo)|de boa)(?: e voce)?", n)):
        return "social:acolhimento", "Certo! Sobre o que você quer conversar?"
    if tipo == "contato":
        return "social:tudobem", "Oi! Estou por aqui, pronto para conversar. E você, como está?"
    if tipo == "saudacao":
        periodo = re.match(r"bom dia|boa tarde|boa noite", n)
        if periodo:
            return "social:oi", periodo.group().capitalize() + "! Sou o Crivo. Sobre o que quer conversar?"
        return "social:oi", ("Oi! Sou o Crivo. Como você está? Pode me contar como foi seu dia "
                             "ou perguntar sobre astronomia, natureza, ciência ou programação.")
    if tipo == "interromper":
        return "social:interromper", "Tudo bem. Paro por aqui."
    if tipo == "desistencia":
        if frustracao_recente(historico):
            return "social:desistencia", "Tudo bem, podemos encerrar. A conversa não resolveu o que você precisava."
        return "social:desistencia", "Tudo bem, deixamos esse assunto por aqui."
    if tipo == "reacao":
        if anterior and anterior["id"] in ("fora", "duvida", "social:nao_entendido"):
            return "social:reacao", "Minha última resposta não resolveu seu pedido. O que você queria saber?"
        return "social:reacao", "O que chamou sua atenção? Quer perguntar ou comentar alguma coisa?"
    if tipo == "critica":
        if re.fullmatch(r"(?:voce |crivo )?nao sabe (?:de )?(?:nada|coisa nenhuma)(?: tambem| mesmo)?", n):
            texto = ("Meu conhecimento vem dos fatos cadastrados, e há muita coisa "
                     "que ainda não sei responder. Me faça uma pergunta concreta "
                     "para conferir o que consigo explicar.")
        elif anterior and anterior["id"] == "social:critica":
            repeticoes = sum(t.get("id") == "social:critica" for t in historico)
            opcoes = (
                "Vamos ao ponto: mande a pergunta que ficou sem resposta ou o trecho que você quer corrigir.",
                "Entendi que a conversa está ruim para você. Podemos encerrar ou conferir um pedido específico.",
                "Se quiser retomar, indique o que precisava descobrir. Posso conferir os fatos que tenho e dizer quando faltar informação.",
            )
            texto = opcoes[max(0, repeticoes - 1) % len(opcoes)]
        elif anterior and (not anterior["id"].startswith("social:") or
                           anterior["id"] == "social:nao_entendido"):
            pedido = anterior["pergunta"][:160]
            if anterior["id"] in ("fora", "duvida", "vazio", "social:nao_entendido"):
                texto = ("Não consegui resolver seu pedido anterior: “" + pedido +
                         "”. Pode dizer de outra forma o que você queria saber?")
            else:
                texto = ("Você está questionando minha resposta a “" + pedido +
                         "”. Qual trecho está errado ou não atende ao pedido? "
                         "Preciso conferir isso antes de mudar a resposta.")
        else:
            texto = ("Você está insatisfeito com a conversa. Ainda tenho limitações "
                     "para entender mensagens livres e posso responder mal. "
                     "Qual pergunta você queria que eu respondesse?")
        return "social:critica", texto
    if tipo == "elogio":
        return "social:elogio", "Obrigado pelo retorno! Quer continuar nesse assunto ou mudar de tema?"
    if tipo == "conversar":
        return "social:conversar", "Vamos conversar. O que você quer perguntar ou comentar?"
    return None


def limpar_cortesia(texto):
    """Remove marcadores nas bordas, preservando o conteúdo da pergunta.

    Nunca corta no meio da frase nem dentro de código ou citações.
    Qualificadores, negações, condições e pedidos adicionais permanecem.
    """
    if any(c in texto for c in ('`', '"', '“', '”')):
        return texto
    texto = re.sub(r"^\s*por (?:favor|gentileza)[,:;]?\s+", "", texto, flags=re.I)
    return re.sub(r"[,;!?]\s*por (?:favor|gentileza)[.!?\s]*$", "", texto, flags=re.I).strip()


def pedido_fontes_anterior(texto):
    n = normalizar(limpar_cortesia(texto))
    return bool(re.fullmatch(
        r"(?:(?:qual (?:e )?a|quais (?:sao )?as) (?:fontes?|referencias?)|"
        r"(?:mostre|cite|diga)(?: me)? (?:a|as) (?:fontes?|referencias?)) "
        r"(?:dessa|desta|daquela|da sua|da ultima) "
        r"(?:informacao|resposta|explicacao|afirmacao)", n))


def preparar_pedido(texto):
    # Retira somente um ato introdutório de pedido ou opinião. O conteúdo
    # completo continua no motor factual; não se apagam qualificadores.
    texto = limpar_cortesia(texto)
    sujeito = r"(?:voc[eê]|vc|tu)"
    definicao = re.match(
        r"^(?:" + sujeito + r"\s+)?(?:pode|poderia|consegue|conseguiria)\s+"
        r"(?:me\s+)?(?:definir|explicar\s+o\s+significado\s+de)\s+(.+)$", texto, re.I,
    )
    if definicao:
        return "defina " + definicao.group(1)
    # Reformulação explícita, sem apagar 'não quero' ou 'não sei se'.
    texto = re.sub(
        r"^(?:n[aã]o,\s*)?(?:(?:quero (?:saber|entender)|quis dizer)\s+"
        r"(?=(?:o que|como|por que|qual|quais|onde|quando|quanto)\b)|"
        r"(?:a )?minha pergunta [eé]\s*:?\s+)", "", texto, count=1, flags=re.I,
    )
    pergunta = r"(?=(?:o que|como|por que|qual|quais|onde|quando|quanto|se)\b)"
    padroes = (
        sujeito + r" (?:pode|poderia|consegue|sabe) (?:me )?(?:dizer|explicar|contar|mostrar) " + pergunta,
        sujeito + r" sabe " + pergunta,
        sujeito + r" (?:acha|pensa|acredita) que ",
    )
    for indice, padrao in enumerate(padroes):
        novo = re.sub(r"^" + padrao, "", texto, count=1, flags=re.I)
        if novo != texto:
            # 'Dizer se X é Y' é interrogativo indireto; 'achar que se
            # X fosse Y' continua condicional e deve conservar o 'se'.
            return (re.sub(r"^se\s+", "", novo, count=1, flags=re.I)
                    if indice < 2 else novo)
    return texto


def assuntos(bot, rotulos, completo=False):
    topicos = sorted({e["topico"] for e in bot.base})
    partes = []
    for topico in topicos:
        if topico == "programacao":
            areas = sorted({e["area"] for e in bot.base
                            if e["topico"] == topico and e.get("area")})
            partes.append("programação" + (" (" + ", ".join(areas) + ")" if areas else ""))
        else:
            partes.append(rotulos.get(topico, topico.replace("_", " ")))
    grupos = {}
    for item in bot.compositor.itens.values():
        if item["id"] not in bot.compositor.expandidos:
            continue
        grupos.setdefault(item.get("area", "conhecimento adicional"), []).append(item["nome"])
    for area, nomes in sorted(grupos.items()):
        exemplos = nomes if completo else nomes[:2]
        partes.append(area + " (" + ", ".join(exemplos) + ")")
    return "; ".join(partes) or "a base cadastrada nesta instalação"


def capacidades(bot, rotulos, completo=False):
    funcoes = ["explicar conceitos presentes na base"]
    if getattr(bot, "conversacao", None) is not None:
        funcoes.append("entender variações de pedidos, reformular explicações e retomar assuntos recentes")
        funcoes.append("explorar situações que você contar com perguntas de continuidade")
    if bot.compositor.itens:
        funcoes.append("compor textos, resumos, tópicos e roteiros curtos com fatos cadastrados")
    if bot.raciocinio is not None:
        funcoes.append("consultar relações, combinar condições e mostrar as provas disponíveis")
    if bot.compositor.fontes:
        funcoes.append("mostrar as fontes dos fatos usados quando elas estão cadastradas")
    if bot.frutas is not None:
        funcoes.append("consultar propriedades e classificações de frutas cadastradas")
    if getattr(bot, "motor_codigo", None) is not None:
        funcoes.append("interpretar código JavaScript limitado, rastrear estados e testar correções com exemplos de entrada e saída")
        funcoes.append("montar funções simples a partir desses exemplos")
    texto = "Posso " + "; ".join(funcoes) + ".\n\n"
    texto += "Assuntos desta instalação: " + assuntos(bot, rotulos, completo) + "."
    if completo:
        texto += ("\n\nExperimente pedir um texto sobre um conceito conhecido e depois "
                  "'fale com outras palavras', 'em tópicos' ou 'continue'. "
                  "Você também pode pedir 'retome' seguido do assunto para voltar à memória recente. "
                  "Minha escrita factual é limitada aos fatos disponíveis; "
                  "não controlo aplicativos nem pesquiso a internet durante a conversa.")
    else:
        texto += "\n\nDiga 'só isso?' para ver mais detalhes, ou escolha um assunto."
    return texto


def processamento(bot, completo=False):
    texto = ("Eu processo o texto e aplico os mecanismos do CRIVO: identifico "
             "pedidos, consulto a base e organizo respostas.")
    if bot.raciocinio is not None:
        texto += " Também verifico relações e encadeamentos registrados, mostrando a prova quando existe."
    if bot.rede is not None:
        texto += " Nesta instalação, uma rede neural classificadora também auxilia a seleção de intenções."
    texto += " Não tenho consciência, emoções ou experiências pessoais."
    if completo:
        texto += ("\n\nEsse processamento pode combinar fatos disponíveis, mas não "
                  "garante compreensão de qualquer frase. Quando não reconheço uma "
                  "pergunta, preciso admitir o limite ou pedir esclarecimento.")
    return texto


def responder(n, bot, rotulos, anterior=None):
    n = normalizar(limpar_cortesia(n))
    if re.fullmatch(r"(?:voce|crivo) (?:e|eh) (?:uma? )?(?:ia|inteligencia artificial|robo)", n):
        return "social:identidade", (
            "Sim, sou o Crivo, uma inteligência artificial experimental. "
            "Uso modelos próprios e conhecimento registrado para responder; posso errar.")
    if re.fullmatch(
        r"(?:voce )?(?:(?:consegue|pode) )?(?:me entende|entende|compreende|entendeu)"
        r"(?: (?:mesmo|minhas perguntas|meu pedido|o que (?:eu )?"
        r"(?:digo|falo|quero dizer|quis dizer)))?", n,
    ):
        return "social:compreensao", (
            "Tento interpretar sua mensagem junto com o contexto da conversa. "
            "Ainda posso perder o sentido ou confundir um pedido. Se eu responder "
            "algo diferente do que você quis dizer, pode me corrigir.")
    if re.fullmatch(
        r"(?:assuntos?|topicos?|capacidades|funcoes|ajuda|help|"
        r"o que voce (?:sabe(?: fazer)?|faz|consegue fazer|pode fazer)|"
        r"quais (?:sao )?(?:os |seus |suas )?(?:assuntos|topicos|capacidades|funcoes)|"
        r"sobre o que voce (?:sabe falar|fala|conversa)|"
        r"como voce (?:pode |consegue )?me ajudar)", n,
    ):
        return "social:assuntos", capacidades(bot, rotulos)
    if re.fullmatch(
        r"(?:(?:como |o que )?voce (?:(?:realmente|mesmo) )?(?:pensa|raciocina|sente)|"
        r"como voce (?:funciona|responde|processa respostas)|"
        r"voce (?:"
        r"(?:consegue|pode|sabe) (?:pensar|raciocinar|sentir)|"
        r"(?:tem|possui) (?:uma )?(?:consciencia|emocoes|sentimentos)|"
        r"(?:e|eh) (?:uma? )?(?:pessoa|humano|humana|ser humano|consciente|vivo|viva)))", n,
    ):
        return "social:pensamento", processamento(bot)
    curtos = {"so isso", "e so isso", "apenas isso", "e o que mais", "o que mais", "como assim"}
    continuacoes = {"mais", "continue", "conte mais", "explique melhor"}
    if n in curtos or n in continuacoes and anterior in ("social:assuntos", "social:pensamento"):
        if anterior == "social:assuntos":
            return "social:assuntos", capacidades(bot, rotulos, completo=True)
        if anterior == "social:pensamento":
            return "social:pensamento", processamento(bot, completo=True)
        return "duvida", "Sobre qual resposta você quer mais detalhes? Pode indicar o assunto?"
    return None


def pergunta_pessoal(texto):
    """Protege a passagem ao ranking; pedidos factuais foram tratados antes."""
    n = normalizar(texto)
    return bool(re.match(
        r"^(?:(?:o que|como|por que|quando|onde) )?voce\b|"
        r"^(?:qual|quais) (?:e |sao )?(?:o |a |os |as )?(?:seu|sua|seus|suas)\b", n,
    ))
