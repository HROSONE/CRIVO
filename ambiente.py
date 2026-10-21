"""O ambiente à volta do modelo: casa, moradia segura e alimento.

O 46M fala em todas as mensagens (decisão do criador). Sozinho, ele boia: não lembra que perguntou
"como foi o seu dia?", não sabe que a pessoa ainda espera a palavra corrigida, e às vezes inventa
um parente. O ambiente não fala por ele; ele cerca o modelo:

    casa      o fio da conversa (Fio): a última pergunta do CRIVO, a tarefa em aberto, o que a pessoa
              disse; uma fala curta ("me mande a palavra corrigida", "quer saber o quê?") é lida
              dentro desse fio;
    alimento  o ato do turno (ato_do_turno), escolhido antes de o modelo falar, e o que ele recebe para
              dizer: o resultado da tarefa, a pergunta que ele fez;
    moradia   o juiz (julgar): entre as frases do modelo, fica a que não inventa parente, responde
              "sim" ou "não" quando a pergunta pede, não repete a fala da pessoa entre aspas; uma frase
              inventada sai da resposta, e o resto das palavras dele fica.

Nada aqui é modelo; são regras sobre o que a pessoa disse e o que o CRIVO conferiu.
"""
import re

from composicao_textual import normalizar

IDENT_TAREFA = "ambiente:tarefa"
IDENT_PERGUNTA = "ambiente:minha_pergunta"

# --- casa: o fio da conversa ---------------------------------------------------------------------


class Fio:
    """O que a conversa já tem: a última pergunta do CRIVO e a tarefa em aberto."""

    def __init__(self):
        self.ultima_pergunta = None   # a última pergunta do CRIVO, até dois turnos depois
        self.idade_pergunta = 0
        self.anterior = None          # a última resposta do CRIVO, inteira
        self.fala_anterior = None     # a última fala da pessoa, dita por inteiro
        self.ident_anterior = None    # de onde veio a última resposta
        self.tarefa = None            # {"tipo": "correcao", "original", "corrigido", "trocadas"}
        self.ato = None               # o ato do turno corrente
        self.exigido = None           # o que a resposta do turno tem que dizer (a palavra corrigida)

    def observar(self, bot, fala, ident, resposta):
        """Depois de cada turno: guarda a pergunta que o CRIVO deixou e a tarefa que ele fez."""
        if not isinstance(resposta, str):
            return
        frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", resposta.strip()) if f.strip()]
        perguntas = [f for f in frases if f.endswith("?")]
        if perguntas:
            self.ultima_pergunta, self.idade_pergunta = perguntas[-1], 0
        else:
            # "Como foi o seu dia?" → "Nem começou ainda" → "Quer saber o quê?": a pergunta vale mais um turno.
            self.idade_pergunta += 1
            if self.idade_pergunta > 1:
                self.ultima_pergunta = None
        self.anterior = resposta
        self.fala_anterior = fala
        self.ident_anterior = ident
        correcao = getattr(bot, "ultima_correcao_texto", None)
        if ident == "texto:correcao" and correcao:
            self.tarefa = {"tipo": "correcao", "original": correcao["original"], "corrigido": correcao["corrigido"],
                           "trocadas": [a for a in correcao["alteracoes"] if a["antes"].strip(" .")]}
        elif ident.startswith("texto:") and ident != "texto:alteracoes":
            self.tarefa = None


_PEDE_NOME = re.compile(r"\b(?:e (?:o )?seu|e (?:o )?teu|qual (?:e )?(?:o )?seu nome|como (?:voce )?se chama|"
                        r"como (?:eu )?(?:te|posso te) chamo|e voce)\b")


_PERGUNTA_O_QUE = re.compile(r"^(?:o que|que|quem)\s+(?:e|eh|sao|foi|foram|era)\b")
_E_O = re.compile(r"^[Ee]\s+(?:(?:o|a|os|as)\s+)?(?P<x>[^?!.,]{2,40}?)\s*\?*$")


# "A Lua é um planeta? Responde sim ou não": o "não" do pedido caía no detector de negação.
_PEDE_SIM_OU_NAO = re.compile(r"[\s,.;:-]*(?:me )?(?:(?:responde|responda|resposta|diz|diga|fala|so|só)[:,]?\s+)?"
                              r"(?:com\s+)?sim\s+ou\s+n[aã]o\s*[?!.]*\s*$", re.I)
# "E da Espanha?" depois de "Qual a capital da França?": a mesma pergunta, com o outro assunto no lugar.
_E_LIGADO = re.compile(r"^[Ee]\s+(?:(?P<lig>o|a|os|as|do|da|dos|das|de|no|na|nos|nas|em|pelo|pela)\s+)?"
                       r"(?P<x>[^?!.,]{2,40}?)\s*\?*$")
_INTERROGA = re.compile(r"^(?:qual|quais|quem|onde|quando|quanto|quantos|quantas|como|em que|de que|que)\b")
_NAO_ASSUNTO = {"voce", "vc", "tu", "ai", "dai", "agora", "entao", "depois", "isso", "aquilo", "o seu", "a sua", "seu",
                "sua", "o teu", "a tua", "ele", "ela", "eles", "elas", "mais", "o resto", "outro", "outra", "voces"}


_ARTIGO = {"o": 0, "a": 1, "os": 2, "as": 3}
_CONTRAI = {"de": ("do", "da", "dos", "das"), "em": ("no", "na", "nos", "nas"), "por": ("pelo", "pela", "pelos", "pelas")}
_CLASSE = {w: c for c, formas in _CONTRAI.items() for w in formas + (c,)}


def _mesma_pergunta(anterior, lig, x):
    """A pergunta anterior com x no lugar do último assunto (depois do último artigo ou de "de/em/por"
    contraídos), ou None. "Qual é a função da mitocôndria?" + "E o ribossomo?" → "...função do ribossomo?"."""
    achados = [m for m in re.finditer(r"\b(\w+)\b", anterior)
               if m.group(1).lower() in _ARTIGO or m.group(1).lower() in _CLASSE]
    if achados:
        m = achados[-1]
        velho = m.group(1).lower()
        if not lig:
            novo = m.group(1)
        elif velho in _CLASSE and lig in _ARTIGO:
            novo = _CONTRAI[_CLASSE[velho]][_ARTIGO[lig]]   # "da" + "o" → "do"
        else:
            novo = lig
        return anterior[:m.start()] + novo + " " + x + "?"
    if not lig:
        m = list(re.finditer(r"\b(?:é|e|são|sao)\b", anterior))  # "Quanto é 7 vezes 8?" → "e 9 vezes 8?"
        if m:
            return anterior[:m[-1].end()] + " " + x + "?"
    return None


def mesma_pergunta(fio, fala):
    """ "e da Espanha?" depois de "Qual a capital da França?" → "Qual a capital da Espanha?", ou None.
    O CRIVO tenta antes a fala como veio (o acervo já reconstrói "E o ribossomo?" depois da função da
    mitocôndria); esta é a segunda tentativa, quando a primeira não entendeu ou não soube."""
    anterior = getattr(fio, "fala_anterior", None) if fio is not None else None
    ligado = _E_LIGADO.match(fala.strip()) if isinstance(fala, str) else None
    if not (ligado and anterior and _INTERROGA.match(normalizar(anterior)) and not _PERGUNTA_O_QUE.match(normalizar(anterior))
            and len(ligado.group("x").split()) <= 4 and normalizar(ligado.group("x")) not in _NAO_ASSUNTO
            and normalizar(ligado.group("x")) not in normalizar(anterior)):
        return None
    return _mesma_pergunta(anterior.strip().rstrip("?!. "), (ligado.group("lig") or "").lower(), ligado.group("x").strip())


def completar(fio, fala):
    """A fala curta dita por inteiro, lida no fio: "O meu é Henrique" depois de "Meu nome é CRIVO. E o seu?"
    vira "Meu nome é Henrique", para a memória e o modelo entenderem. Sem fio que a complete, a mesma fala."""
    if fio is None or not isinstance(fala, str):
        return fala
    pedido = _PEDE_SIM_OU_NAO.search(fala)
    fio.pediu_sim_ou_nao = bool(pedido and fala[:pedido.start()].strip())
    if fio.pediu_sim_ou_nao:
        fala = fala[:pedido.start()].strip().rstrip("?,.;:- ") + "?"
    # "O que são primatas?" → "E o símio?": a mesma pergunta, sobre o outro assunto.
    m = _E_O.match(fala.strip())
    anterior = getattr(fio, "fala_anterior", None)
    # Só depois da enciclopédia ou de um "não sei": o acervo já resolve "E a Lua?" depois de "O que é o Sol?".
    de_fora = str(getattr(fio, "ident_anterior", "") or "").startswith(("enciclopedia:", "fora", "duvida"))
    if m and anterior and de_fora and _PERGUNTA_O_QUE.match(normalizar(anterior)) and len(m.group("x").split()) <= 4:
        quem = normalizar(anterior).startswith("quem")
        return ("Quem é %s?" if quem else "O que é %s?") % m.group("x").strip()
    if not fio.ultima_pergunta or fio.idade_pergunta:
        return fala
    pergunta = normalizar(fio.ultima_pergunta)
    if _PEDE_NOME.search(pergunta) and re.search(r"\bnome\b", normalizar(fio.anterior or "")):
        m = re.match(r"^(?:[Oo] meu (?:é|e)|[Mm]eu (?:é|e)|[ÉéEe]|[Oo] meu nome é)\s+([A-ZÀ-Ý][\wÀ-ÿ'-]+)[.!]?$",
                     fala.strip())
        if m:
            return "Meu nome é %s" % m.group(1)
    return fala


def _sem_aspas(texto):
    return texto.strip().strip("\"'“”«» ").strip()


# --- alimento: o ato do turno --------------------------------------------------------------------

_PEDE_RESULTADO = re.compile(
    r"\b(?:(?:me )?(?:manda|mande|mandar|passa|passe|diz|diga|dizer|fala|fale|escreve|escreva|mostra|mostre|"
    r"da|de|envia|envie)(?: pra mim| para mim)? (?:a|as|o|os) (?:palavras?|textos?|frases?|corre[cç][aã]o)"
    r"(?: (?:corrigid[ao]s?|cert[ao]s?|corret[ao]s?|revisad[ao]s?))?|"
    r"qual (?:e |eh )?(?:a|o) (?:palavra|texto|frase) (?:corrigid[ao]|cert[ao]|corret[ao])|"
    r"cade (?:a|o) (?:palavra|texto|frase|corre[cç][aã]o)|e (?:a|o) (?:palavra|texto) corrigid[ao])\b")
_RECLAMA_RESULTADO = re.compile(
    r"\b(?:nao|nem) (?:me )?(?:deu|mandou|passou|disse|falou|corrigiu|escreveu|mostrou)\b.*\b(?:palavra|texto|frase|"
    r"corre[cç][aã]o|cert[ao]|corrigid[ao])\b|\b(?:continua|ta|esta|ficou) (?:errad[ao]|igual)\b")
_O_QUE = re.compile(
    r"^(?:(?:voce )?(?:quer|queria) saber (?:o que|o que exatamente|do que|sobre o que)|o que (?:voce )?(?:quer|queria) "
    r"saber|(?:voce )?perguntou o que)\s*\??$")
_SIM_NAO_INICIO = re.compile(
    r"^(?:voce|vc|tu|o crivo)\s+(?!(?:sabe|sabia)\s+(?:o que|quem|onde|quando|como|qual|por que|quanto))\w+")
_INTERROGATIVA = re.compile(r"\b(?:o que|quem|onde|quando|como|qual|quais|por que|porque|quanto|quantos|quantas)\b|"
                            r"\b(?:de|com|em|por|pra|para) que\b|\bque$")


def ato_do_turno(fio, fala):
    """O ato que o ambiente escolhe antes de o modelo falar, ou None (conversa livre)."""
    if not isinstance(fala, str) or fio is None:
        return None
    n = normalizar(fala).strip(" .!")
    pergunta = fala.strip().endswith("?")
    if fio.tarefa and (_PEDE_RESULTADO.search(n) or _RECLAMA_RESULTADO.search(n)):
        return "reclamar_tarefa" if _RECLAMA_RESULTADO.search(n) else "entregar_tarefa"
    if fio.ultima_pergunta and _O_QUE.match(n):
        return "explicar_minha_pergunta"
    if pergunta and (getattr(fio, "pediu_sim_ou_nao", False)
                     or _SIM_NAO_INICIO.match(n) and not _INTERROGATIVA.search(n.split(" ", 1)[-1])):
        return "sim_ou_nao"
    return None


# Atos sociais curtos que caíam em "não entendi" ou num assunto parecido ("esquece" → plantas).
_ATOS_CURTOS = (
    (re.compile(r"(?:ah,? |entao,? )?(?:esquece|esqueca|deixa (?:pra la|quieto|isso pra la|isso)|deixa|nada nao|"
                r"nao importa|deixa pra la)(?: entao| isso| ai| crivo)?"),
     "social:deixa", "Tudo bem, deixa pra lá. Se quiser falar de outra coisa, estou aqui."),
    (re.compile(r"(?:(?:muito|mt) )?(?:obrigad[oa]|obg|obgd|brigad[oa]|brigadu|valeu|vlw|valew|grat[oa])(?: mesmo| demais)?"
                r"(?: (?:pela|pelo|por) (?:a |o )?(?:explicacao|resposta|informacao|info|dica|ajuda|paciencia|aula|"
                r"conversa|papo|atencao|forca))?(?: (?:mano|cara|parceiro|amigo|amiga|crivo|viu|ta|irmao))?"),
     "social:obrigado", "Por nada! Se quiser saber mais alguma coisa, é só perguntar."),
    (re.compile(r"(?:(?:eu )?posso|da pra|deixa eu|queria) (?:te )?(?:fazer|perguntar) (?:uma|outra|mais uma) (?:pergunta|coisa)"
                r"(?: (?:pra|para) (?:voce|vc|ti))?"),
     "social:convite", "Claro, pode perguntar."),
    (re.compile(r"(?:(?:voce|vc) )?(?:quer|queres) (?:saber|ouvir|ver|conhecer) (?:uma|um) (?:coisa|piada|segredo|"
                r"curiosidade|historia|fato|novidade)(?: (?:legal|engracada|interessante))?"),
     "social:oferta", "Quero! Conta."),
)
# Confirmação curta sem nada a confirmar: só quando o resto do CRIVO não entendeu.
_RECONHECE = re.compile(r"(?:ok|okay|okey|blz|beleza|ta bom|ta|certo|entendi|entendido|ah ta|ahh ta|show|top|suave|"
                        r"de boa|tranquilo|legal|ah legal|que legal|interessante|massa|aham|uhum|hum+|hm+|ata)(?: entao)?")


def ato_curto(bot, fala):
    """(ident, resposta) para um ato social curto dito por inteiro, ou None. Depois de uma crise, só o
    agradecimento (o crise.py dá o tom); o resto segue o cuidado de sempre."""
    n = normalizar(fala).strip(" .!?")
    for padrao, ident, resposta in _ATOS_CURTOS:
        if not padrao.fullmatch(n):
            continue
        if not getattr(bot, "crise", None) or ident == "social:obrigado":
            return ident, resposta
        if ident == "social:deixa":
            return "crise:apoio", ("Tudo bem, não precisa falar disso agora. Estou aqui se quiser voltar a conversar, "
                                   "e o CVV atende no 188, a qualquer hora.")
    return None


def reconhecimento(fala):
    """Resposta a um "ok"/"beleza" que o resto do CRIVO não entendeu, ou None."""
    if _RECONHECE.fullmatch(normalizar(fala).strip(" .!?")):
        return "social:ok", "Beleza! Se quiser, é só perguntar ou me contar alguma coisa."
    return None


def retomar(bot, fala):
    """(ident, resposta) quando o ato pede o que o CRIVO já tem (o resultado da tarefa, a pergunta
    que ele fez); a resposta é conferida e entra como fato para o modelo dizer. Senão, None."""
    fio = getattr(bot, "fio", None)
    ato = ato_do_turno(fio, fala)
    if fio is not None:
        fio.ato, fio.exigido = ato, None
    if ato in ("entregar_tarefa", "reclamar_tarefa"):
        t = fio.tarefa
        corrigido = _sem_aspas(t["corrigido"])
        uma_palavra = bool(re.fullmatch(r"[^\W\d_]+", corrigido))
        if not t["trocadas"]:
            resposta = ("Não achei outra grafia para “%s” nas minhas listas. Pode me dizer o que queria escrever?"
                        % _sem_aspas(t["original"]))
        elif uma_palavra:
            resposta = "A palavra corrigida é %s." % corrigido.lower() if corrigido.istitle() else \
                "A palavra corrigida é %s." % corrigido
        else:
            resposta = "O texto corrigido é: %s" % corrigido
        if ato == "reclamar_tarefa" and t["trocadas"]:
            resposta = "Desculpa. " + resposta
        fio.exigido = corrigido if t["trocadas"] else None
        return IDENT_TAREFA, resposta
    if ato == "explicar_minha_pergunta":
        pergunta = fio.ultima_pergunta
        fio.exigido = pergunta.rstrip("?").strip()
        return IDENT_PERGUNTA, "Eu perguntei: %s" % (pergunta[:1].lower() + pergunta[1:])
    return ato_curto(bot, fala)


def exigido(bot, ident):
    """O trecho que a frase do modelo tem que trazer neste turno, ou None."""
    fio = getattr(bot, "fio", None)
    if fio is None or ident not in (IDENT_TAREFA, IDENT_PERGUNTA):
        return None
    return fio.exigido


# --- moradia segura: o juiz das frases do modelo -------------------------------------------------

PARENTES = ("pai", "mae", "irmao", "irma", "filho", "filha", "filhos", "esposa", "marido", "namorado",
            "namorada", "avo", "avos", "tio", "tia", "primo", "prima", "neto", "neta", "sogra", "sogro",
            "cunhado", "cunhada", "noivo", "noiva", "esposo")
# "seu país" e "seus pais" ficam iguais sem acento: só "seus/teus/dos pais" conta como parente.
_PARENTE = re.compile(r"\b(?:seu|sua|seus|suas|teu|tua|do|da|dos|das)\s+(" + "|".join(PARENTES) + r")\b|"
                      r"\b(?:seus|teus|dos)\s+(pais)\b")
_SIM_NAO_RESPOSTA = re.compile(
    r"^(?:sim|nao|claro|com certeza|acho que (?:sim|nao)|as vezes|em parte|nem sempre|nem tudo|mais ou menos|"
    r"um pouco|depende|ainda nao)\b")
# A resposta que repete o verbo ("Você pensa?" → "Penso…") também responde.
_EU = {"consegue": "consigo", "sabe": "sei", "tem": "tenho", "pode": "posso", "e": "sou", "esta": "estou",
       "ta": "to", "quer": "quero", "vai": "vou", "faz": "faco", "ve": "vejo", "ouve": "ouco", "le": "leio"}


def _verbo_da_pergunta(fala):
    m = re.match(r"^(?:voce|vc|tu|o crivo)\s+(?:me |te |se |nao )*(\w+)", normalizar(fala))
    if not m:
        return None
    v = m.group(1)
    return _EU.get(v) or (v[:-1] + "o" if v.endswith(("a", "e")) and len(v) > 3 else None)


_NADA_ACONTECEU = re.compile(r"^(?:nem|nada|nao|ainda nao|nenhum|nenhuma)\b")
_O_QUE_ACONTECEU = re.compile(r"\bo que (?:aconteceu|houve|rolou)\b")


_SOBRE_OUTRO = re.compile(r"^(?:e\s+)?(?:quem|que|o que|oq)\s+(?:e|eh|foi|era|sao|eram|significa)\s+(?P<x>.+)$")
_DE_SI = re.compile(r"\b(?:sou o crivo|sou uma (?:ia|inteligencia artificial)|me criou|me fez|meu nome e crivo|"
                    r"sou feito do zero)\b")
_NAO_SEI = re.compile(r"\b(?:nao sei|nao tenho (?:essa|uma|esse|a|o)?\s*(?:informacao|resposta|definicao)|"
                      r"nao conheco|ainda nao (?:sei|aprendi|me ensinaram)|nao encontrei)\b")


def julgar(ato, fala, texto, fontes, exigido=None, nao_sabe=False):
    """Falhas de uma frase do modelo (lista vazia: passa). fontes: o que a pessoa disse e o que o
    CRIVO sabe (falas, lembranças, contexto); exigido: o trecho que a frase tem que trazer; nao_sabe:
    o CRIVO não conhece o assunto, e a frase tem que dizer isso."""
    falhas = []
    n = normalizar(texto)
    nf0 = normalizar(fala).strip(" .!?")
    outro = _SOBRE_OUTRO.match(nf0)
    if outro and not re.match(r"(?:voce|vc|tu|o crivo|crivo|seu nome|teu nome)\b", outro.group("x")) and _DE_SI.search(n):
        # "Quem é Freud?" → "Sou o CRIVO…": a pergunta é sobre outro.
        falhas.append("falou_de_si")
    if nao_sabe and not _NAO_SEI.search(n):
        falhas.append("inventou_sem_fonte")
    if len(nf0) > 6 and n.strip(" .!?") == nf0:
        falhas.append("repetiu_a_pergunta")   # "Quem é psicopata?" → "Quem é psicopata?"
    if exigido and normalizar(exigido) not in n:
        falhas.append("faltou_resultado")
    nf = normalizar(fala).strip(" .!?")
    if len(nf.split()) <= 5 and _NADA_ACONTECEU.match(nf) and _O_QUE_ACONTECEU.search(n):
        # "Nem começou ainda" → "O que aconteceu?": pergunta por um acontecimento que a pessoa negou.
        falhas.append("pergunta_contraria")
    base = " " + normalizar(" ".join(fontes)) + " "
    for rel in (a or b for a, b in _PARENTE.findall(n)):
        if not re.search(r"\b%s\b" % rel, base):
            falhas.append("inventou_parente:" + rel)
    if ato == "sim_ou_nao":
        exige = re.search(r"\bsim ou nao\b", normalizar(fala))
        inicio = n.lstrip(" \"'“").strip()
        verbo = _verbo_da_pergunta(fala)
        responde = _SIM_NAO_RESPOSTA.match(inicio) or verbo and re.match(r"(?:(?:eu|nao|ainda nao) )?%s\b" % verbo, inicio)
        if exige and not re.match(r"(?:sim|nao)\b", inicio) or not exige and not responde:
            falhas.append("nao_respondeu_sim_ou_nao")
    # Eco: a fala anterior da pessoa repetida entre aspas ("Você trouxe “Me mande…”").
    for citado in re.findall(r"[“\"]([^”\"]{12,})[”\"]", texto):
        if normalizar(citado) in base and normalizar(citado) != normalizar(fala):
            falhas.append("eco")
            break
    return falhas


def podar(texto, ato, fala, fontes):
    """As frases do modelo que passam no juiz, na ordem dele; '' se nenhuma passa.

    Uma frase inventada ("Fico feliz que você me contou sobre seu pai.") sai; as outras ficam."""
    frases = [f for f in re.split(r"(?<=[.!?…])\s+", texto.strip()) if f]
    boas = [f for f in frases if not any(x.startswith("inventou_parente") or x in ("eco", "falou_de_si")
                                         for x in julgar(None, fala, f, fontes))]
    if not boas or len(boas) == len(frases):
        return texto if len(boas) == len(frases) else ""
    resto = " ".join(boas)
    return resto if not julgar(ato, fala, resto, fontes) else ""
