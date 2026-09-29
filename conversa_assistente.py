"""Autodescrição apoiada na configuração ativa, sem recuperação por semelhança."""
import re
import unicodedata


def normalizar(texto):
    n = unicodedata.normalize("NFD", texto.lower())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    n = " ".join(re.findall(r"[a-z0-9]+", n))
    return re.sub(r"\b(?:vc|tu)\b", "voce", n)


def preparar_pedido(texto):
    # Retira somente um ato introdutório de pedido ou opinião. O conteúdo
    # completo continua no motor factual; não se apagam qualificadores.
    sujeito = r"(?:voc[eê]|vc|tu)"
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
    if bot.compositor.itens:
        funcoes.append("compor textos, resumos, tópicos e roteiros curtos com fatos cadastrados")
    if bot.raciocinio is not None:
        funcoes.append("consultar relações, combinar condições e mostrar as provas disponíveis")
    if bot.compositor.fontes:
        funcoes.append("mostrar as fontes dos fatos usados quando elas estão cadastradas")
    if bot.frutas is not None:
        funcoes.append("consultar propriedades e classificações de frutas cadastradas")
    texto = "Posso " + "; ".join(funcoes) + ".\n\n"
    texto += "Assuntos desta instalação: " + assuntos(bot, rotulos, completo) + "."
    if completo:
        texto += ("\n\nExperimente pedir um texto sobre um conceito conhecido e depois "
                  "'mais curto', 'em tópicos' ou 'continue'. Mantenho o contexto curto "
                  "da conversa. Minha escrita é limitada aos fatos disponíveis; "
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
    n = normalizar(n)
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
