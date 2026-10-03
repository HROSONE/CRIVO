"""Presença na conversa: refletir o que a pessoa disse, variar o jeito de
falar, lembrar o que ela contou e retomar na hora certa.

Nada aqui cria fatos: a reflexão repete o que a pessoa contou (passado
para a segunda pessoa), as noções continuam marcadas como noções e as
inferências como prováveis.
"""
import re

from linguagem_conversa import normalizar

# ---------------------------------------------------------------------------
# Primeira pessoa → "você" (3ª pessoa do singular)

IRREGULARES = {
    "fui": "foi", "fiz": "fez", "tive": "teve", "estive": "esteve", "pude": "pôde", "quis": "quis",
    "disse": "disse", "trouxe": "trouxe", "vi": "viu", "vim": "veio", "dei": "deu", "soube": "soube",
    "pus": "pôs", "li": "leu", "caí": "caiu", "sai": "saiu", "saí": "saiu", "ouvi": "ouviu",
    "estou": "está", "tô": "está", "sou": "é", "vou": "vai", "faço": "faz", "posso": "pode",
    "quero": "quer", "sei": "sabe", "tenho": "tem", "durmo": "dorme", "consigo": "consegue",
    "peço": "pede", "perco": "perde", "ouço": "ouve", "digo": "diz", "trago": "traz", "vejo": "vê",
    "venho": "vem", "dou": "dá", "estava": "estava", "era": "era", "ia": "ia", "tinha": "tinha",
    "acordei": "acordou", "esqueci": "esqueceu", "perdi": "perdeu", "comi": "comeu", "bebi": "bebeu",
    "dormi": "dormiu", "corri": "correu", "vendi": "vendeu", "escrevi": "escreveu", "aprendi": "aprendeu",
    "consegui": "conseguiu", "senti": "sentiu", "abri": "abriu", "parti": "partiu", "assisti": "assistiu",
    "decidi": "decidiu", "descobri": "descobriu", "subi": "subiu", "cheguei": "chegou",
    "farei": "fará", "direi": "dirá", "trarei": "trará", "irei": "irá",
}
# Presente em primeira pessoa que o etiquetador às vezes lê como substantivo
# ("eu gosto", "mas fico"): só vira verbo depois de sujeito ou advérbio.
PRESENTES = {"gosto": "gosta", "fico": "fica", "acho": "acha", "adoro": "adora", "odeio": "odeia",
             "amo": "ama", "prefiro": "prefere", "preciso": "precisa", "moro": "mora", "trabalho": "trabalha",
             "estudo": "estuda", "penso": "pensa", "sinto": "sente", "consigo": "consegue", "durmo": "dorme",
             "canso": "cansa", "esqueço": "esquece", "acordo": "acorda", "corro": "corre", "leio": "lê"}
_ANTES_DO_VERBO = ("eu", "nao", "ja", "tambem", "ainda", "so", "nunca", "sempre", "mas", "e", "que", "hoje")
POSSESSIVOS = {"meu": "seu", "minha": "sua", "meus": "seus", "minhas": "suas", "eu": "você",
               "mim": "você", "comigo": "com você", "nosso": "de vocês", "nossa": "de vocês"}


def verbo_para_voce(forma, lema=""):
    f = forma.lower()
    if f in IRREGULARES:
        return IRREGULARES[f]
    if f in PRESENTES:
        return PRESENTES[f]
    l = lema.lower()
    if f.endswith(("arei", "erei", "irei")) and l == f[:-2] and len(l) >= 4:
        return f[:-2] + "á"  # futuro: "comerei" → "comerá" (mas "parei" → "parou")
    if f.endswith("ei") and len(f) > 3:
        # Pretérito de verbo em -ar, pela grafia (o lema do etiquetador pode
        # errar): "peguei" → "pegou", "fiquei" → "ficou", "comecei" → "começou".
        raiz = f[:-2]
        if raiz.endswith("gu"):
            raiz = raiz[:-1]
        elif raiz.endswith("qu"):
            raiz = raiz[:-2] + "c"
        elif raiz.endswith("c"):
            raiz = raiz[:-1] + "ç"
        return raiz + "ou"
    if f.endswith("i") and l.endswith("er"):
        return f[:-1] + "eu"
    if f.endswith("i") and l.endswith("ir"):
        return f[:-1] + "iu"
    if f.endswith("o") and l.endswith("ar") and f[:-1] == l[:-2]:
        return f[:-1] + "a"
    if f.endswith("o") and l.endswith(("er", "ir")) and f[:-1] == l[:-2]:
        return f[:-1] + "e"
    if f.endswith(("ava", "ia")):
        return f
    return None


def para_voce(palavras, nucleo_id=None):
    """Palavras da análise (forma, lema, classe…) → texto na voz de "você".
    Devolve None se houver algo que não sabemos converter com segurança
    (clíticos de primeira pessoa, verbos irregulares desconhecidos)."""
    saida = []
    sujeito_explicito = any(normalizar(p.forma) == "eu" for p in palavras)
    formas = [p.forma.lower() for p in palavras]
    if "gente" in formas and "a" in formas or "nós" in formas:
        return None  # "a gente"/"nós" pedem "vocês" e outra conjugação
    palavras = _juntar_consigo(palavras)
    verbos = [_verbo_primeira(p, palavras[i - 1] if i else None) for i, p in enumerate(palavras)]
    for p, verbo in zip(palavras, verbos):
        baixo = p.forma.lower()
        if baixo in ("me", "nos", "comigo") and p.classe == "PRON":
            return None
        if baixo in POSSESSIVOS:
            saida.append(POSSESSIVOS[baixo])
            continue
        if verbo:
            v = verbo_para_voce(p.forma, p.lema)
            if v is None or (p.forma.lower().endswith("i") and not p.lema.lower().endswith(("er", "ir"))):
                v = verbo_para_voce(p.forma, _infinitivo_i(p.forma) or p.lema) or v
            if v is None:
                return None
            saida.append(v)
            continue
        saida.append(p.forma)
    if not sujeito_explicito and any(verbos):
        k = verbos.index(True)
        # "não", "também", "ainda" ficam junto do verbo: "você não foi".
        while k > 0 and palavras[k - 1].classe == "ADV" and normalizar(palavras[k - 1].forma) in (
                "nao", "tambem", "ainda", "ja", "so", "nunca", "sempre"):
            k -= 1
        saida.insert(k, "você")
        if k + 1 < len(saida) and palavras[k].classe != "PROPN" and saida[k + 1] == palavras[k].forma:
            saida[k + 1] = saida[k + 1].lower()
    if saida and palavras and palavras[0].classe != "PROPN" and saida[0] == palavras[0].forma:
        saida[0] = saida[0].lower()
    return " ".join(saida)


def _primeira_pessoa(p):
    f = normalizar(p.forma)
    lema = normalizar(p.lema)
    if f.endswith("o") and lema.endswith(("ar", "er", "ir")) and f[:-1] == lema[:-2]:
        return True  # presente: "gosto", "acho", "como"
    return (p.forma.lower() in IRREGULARES and p.forma.lower() not in ("estava", "era", "ia", "tinha")) or \
        (f.endswith("ei") and len(f) > 3) or (f.endswith("i") and len(f) > 3 and p.lema.lower().endswith(("er", "ir"))
                                               and f != normalizar(p.lema))


def _juntar_consigo(palavras):
    """O tokenizador separa "consigo" em "com si" (como no treebank); depois
    de "eu"/"não" é o verbo conseguir."""
    saida, i = [], 0
    while i < len(palavras):
        p = palavras[i]
        if (p.forma.lower() == "com" and i + 1 < len(palavras) and palavras[i + 1].forma.lower() == "si"
                and saida and normalizar(saida[-1].forma) in _ANTES_DO_VERBO):
            saida.append(type(p)(p.id, "consigo", "conseguir", "VERB", p.pai, p.ligacao))
            i += 2
            continue
        saida.append(p)
        i += 1
    return saida


def _infinitivo_i(forma):
    """"discuti" → "discutir", "comi" → "comer", pelo vocabulário dos vetores
    de palavras; None se não houver exatamente um infinitivo conhecido."""
    f = forma.lower()
    if not f.endswith("i") or len(f) < 5:
        return None
    try:
        from conversa_cotidiana import _leitor
        leitor = _leitor()
        vocab = getattr(getattr(leitor, "a", None), "_biafim", None)
        vocab = vocab.vet_id if vocab is not None else None
    except Exception:
        vocab = None
    if not vocab:
        return None
    achados = [f[:-1] + fim for fim in ("er", "ir") if f[:-1] + fim in vocab]
    return achados[0] if len(achados) == 1 else None


def _verbo_primeira(p, anterior):
    if p.classe in ("VERB", "AUX") and _primeira_pessoa(p):
        return True
    # No começo da fala, "comi"/"bebi"/"fiz" são o verbo, mesmo quando o
    # etiquetador os lê como substantivo ("comi pizza ontem").
    if anterior is None and p.forma.lower() in IRREGULARES and \
            p.forma.lower() not in ("estava", "era", "ia", "tinha", "sai", "sou"):
        return True
    # "Briguei com…", "Discuti com…": pretérito no começo da fala, mesmo lido
    # como substantivo por causa da maiúscula.
    if anterior is None and normalizar(p.forma).endswith("ei") and len(p.forma) > 4:
        return True
    if anterior is None and _infinitivo_i(p.forma):
        return True
    return p.forma.lower() in PRESENTES and (anterior is None or normalizar(anterior.forma) in _ANTES_DO_VERBO)


def _primeira_pessoa_algum(palavras):
    return any(p.classe in ("VERB", "AUX") and _primeira_pessoa(p) for p in palavras)


# ---------------------------------------------------------------------------
# Variação: não repetir a mesma frase na mesma conversa

class Variacao:
    def __init__(self, sorteio):
        self.sorteio = sorteio
        self.usadas = []

    def escolher(self, opcoes):
        livres = [o for o in opcoes if o not in self.usadas[-12:]]
        escolha = self.sorteio.choice(livres or list(opcoes))
        self.usadas.append(escolha)
        return escolha


# ---------------------------------------------------------------------------
# Perfil da conversa: o que a pessoa contou e como ela está

class Perfil:
    def __init__(self):
        self.temas = []  # (turno, nome da noção, tom, reflexão em "você", agente em "você")
        self.turno = 0
        self.nocoes_usadas = set()
        self.perguntas_usadas = set()
        self.nomes = {}  # nome da noção → nome próprio ("cachorro" → "Thor")
        self.ultima_forma = None  # esqueleto da última resposta montada pelo gerador

    def anotar(self, nome, tom, reflexao, agente=""):
        self.temas.append((self.turno, nome, tom, reflexao, agente))
        self.temas = self.temas[-12:]

    def recente(self, distancia=3):
        return bool(self.temas) and self.turno - self.temas[-1][0] <= distancia

    def marcante(self):
        """O assunto mais marcante recente: saúde e coisas ruins primeiro."""
        if not self.temas:
            return None
        recentes = self.temas[-6:]
        for tom in ("luto", "saude", "neg", "pos"):
            for t in reversed(recentes):
                if t[2] == tom:
                    return t
        return recentes[-1]


ABERTURAS = {
    "neg": ("Poxa.", "Que chato.", "Puxa vida.", "Ah, que pena.", "Putz."),
    "saude": ("Sinto muito.", "Poxa, sinto muito.", "Ah, espero que melhore logo."),
    # Morte de alguém (pessoa ou bicho): pêsames, nunca "que chato".
    "luto": ("Sinto muito pela sua perda.", "Meus sentimentos.", "Sinto muito, de verdade."),
    "pos": ("Que bom!", "Que legal!", "Que ótimo!", "Olha só, que bom!", "Boa!"),
    "neutro": ("Entendi.", "Ah, entendi.", "Hum, sei.", "Saquei.", "Certo."),
}

ACOLHER_CURTO = {
    "neg": ("É, cansa mesmo.", "Imagino.", "Faz parte, mas pesa, né?", "Entendo.", "É chato mesmo."),
    "saude": ("Imagino a preocupação.", "Entendo.", "Força aí."),
    "luto": ("Imagino a falta que faz.", "Entendo.", "Leva o tempo que precisar."),
    "pos": ("Pois é!", "Demais!", "Merecido!"),
    "neutro": ("Tranquilo.", "Sem pressa.", "Entendi.", "Faz sentido."),
}

CONTINUAR = {
    "neg": ("Quer desabafar mais um pouco ou prefere mudar de assunto?",
            "Se quiser contar mais, tô aqui.",
            "E você, como está agora?"),
    "saude": ("Como você está com isso?", "Se quiser, me conta como estão as coisas."),
    "luto": ("Como você está com isso?", "Se quiser falar sobre isso, estou aqui.",
             "Quer me contar um pouco mais?"),
    "pos": ("Me conta mais!", "E o que mais tem de novo?", "Que bom saber disso. O que mais aconteceu?"),
    "neutro": ("Me conta mais.", "E o que mais?", "Como foi isso?"),
}

# Perguntas leves para puxar conversa quando a pessoa não traz assunto.
INICIATIVA = (
    "Posso te perguntar uma coisa? O que você mais gosta de fazer quando tem um tempo livre?",
    "Então me conta: como está sendo a sua semana?",
    "Tem alguma coisa que você está esperando para fazer nos próximos dias?",
    "Qual foi a melhor parte do seu dia hoje, mesmo que pequena?",
    "Se você pudesse fazer qualquer coisa agora, o que seria?",
)


SEGUIR_OBJETIVO = ("Se quiser, a gente pensa num primeiro passo pequeno para %s.",
                   "E sobre %s: tem alguma ideia de por onde começar?")

# Reação ao nome de alguém que a pessoa contou ("ele se chama Thor").
REACAO_NOME = {
    "animal": ("%s! Gostei do nome. Faz tempo que vocês estão juntos?", "%s, que nome bom! Vou lembrar."),
    "evento": ("%s, que nome lindo! Parabéns de novo.", "Que lindo, %s! Vou lembrar."),
    "outro": ("%s, anotado! Vou lembrar.", "Ah, %s. Legal saber o nome!"),
}


def nome_tratamento(bot):
    dados = getattr(getattr(bot.conversacao, "dialogo", None), "dados", {}) or {}
    nome = dados.get("nome")
    return nome if isinstance(nome, str) and 1 < len(nome) < 30 else None


def despedida(bot, variacao, fala=""):
    """Despedida que lembra o que a pessoa contou."""
    perfil = getattr(bot, "perfil", None)
    nome = nome_tratamento(bot)
    marcante = perfil.marcante() if perfil else None
    vocativo = (", " + nome) if nome else ""
    if re.search(r"\b(?:descansar|dormir|deitar)\b", normalizar(fala)):
        extra = ""
        if marcante is not None and marcante[2] in ("neg", "saude", "luto"):
            extra = " Depois de tudo isso, você merece."
        return "Descansa bem%s!%s Boa noite." % (vocativo, extra)
    if marcante is None:
        return variacao.escolher(("Até mais%s! Foi bom conversar." % vocativo,
                                  "Tchau%s! Volta quando quiser." % vocativo))
    _, tema, tom, _, agente = marcante
    if tom == "luto":
        return "Até mais%s. Se cuida, e quando quiser conversar, estou aqui." % vocativo
    if tom == "saude":
        quem = agente if agente and agente != "você" else "você"
        return "Até mais%s! Espero que %s melhore logo." % (vocativo, quem)
    if tom == "neg":
        return variacao.escolher(("Até mais%s! Descansa um pouco depois de tudo isso." % vocativo,
                                  "Boa noite%s! Que amanhã seja um dia mais leve." % vocativo,
                                  "Vai lá%s, e descansa. Amanhã é outro dia." % vocativo))
    return variacao.escolher(("Até mais%s! Aproveita!" % vocativo,
                              "Tchau%s! Foi ótimo saber disso." % vocativo))


def apelido(bot, tema):
    perfil = getattr(bot, "perfil", None)
    return (perfil.nomes.get(tema) if perfil else None)


def retomada(bot, variacao):
    """"E aí, tudo bem?" depois de a pessoa ter contado algo: perguntar por ele."""
    perfil = getattr(bot, "perfil", None)
    marcante = perfil.marcante() if perfil else None
    if marcante is None:
        return None
    _, tema, tom, reflexao, agente = marcante
    # Alguém com nome (a bebê Clara, o cachorro Thor) é o melhor gancho.
    for t in reversed(perfil.temas):
        proprio_t = perfil.nomes.get(t[1])
        if proprio_t and t[2] in ("pos", "neutro", tom):
            artigo = "a" if (t[4] or "").startswith(("sua", "minha")) else "o"
            return variacao.escolher(("Tudo ótimo por aqui! E %s %s, como está?" % (artigo, proprio_t),
                                      "Tudo certo! E como vai %s %s?" % (artigo, proprio_t)))
    if tom == "luto":
        return "Por aqui tudo bem. E você, como está se sentindo?"
    if tom == "saude":
        if agente and agente != "você":
            return variacao.escolher(("Tudo bem por aqui! E %s, já melhorou?" % agente,
                                      "Por aqui tudo certo. E %s, como está?" % agente))
        return "Tudo bem por aqui! E você, já está melhor?"
    proprio = perfil.nomes.get(tema)
    if tom == "neg" and tema in ("cansaço", "sono", "estresse", "tristeza", "preguiça"):
        return variacao.escolher(("Tudo bem por aqui! E você, um pouco mais descansado?",
                                  "Por aqui tudo certo. E você, como está o ânimo agora?"))
    if tom == "neg":
        if proprio:
            return "Tudo bem por aqui! E o %s, sossegou?" % proprio
        return variacao.escolher(("Tudo bem por aqui! E você, mais tranquilo depois daquilo que me contou?",
                                  "Por aqui tudo certo. E você, como está se sentindo agora?"))
    if proprio:
        return "Tudo ótimo! E a %s, como está?" % proprio if tema in ("bebê", "filho") else \
            "Tudo ótimo! E o %s, como está?" % proprio
    return "Tudo ótimo! E você, ainda animado com %s?" % _com_artigo(tema)


def _com_artigo(tema):
    feminino = tema.endswith(("a", "ção", "dade", "gem")) and tema not in ("dia",)
    if " " in tema or tema in ("gripe", "doença"):
        feminino = tema.endswith("a") or tema in ("gripe", "doença")
    return ("a " if feminino else "o ") + tema


def de_volta(bot, variacao):
    """Primeiro "oi" de quem já conversou antes e pediu para ser lembrado."""
    perfil = getattr(bot, "perfil", None)
    nome = nome_tratamento(bot)
    oi = "Oi de novo%s!" % ((", " + nome) if nome else "")
    if perfil is None:
        return oi + " Que bom te ver."
    for t in reversed(perfil.temas):
        proprio = perfil.nomes.get(t[1])
        if proprio:
            artigo = "a" if (t[4] or "").startswith(("sua", "minha")) else "o"
            return oi + " E %s %s, como está?" % (artigo, proprio)
    marcante = perfil.marcante()
    if marcante is None:
        return oi + " Que bom te ver. Como você está?"
    _, tema, tom, _, agente = marcante
    if tom == "saude" and agente and agente != "você":
        return oi + " E %s, já melhorou?" % agente
    if tom in ("neg", "saude", "luto"):
        return oi + " Da última vez você não estava num dia muito bom. Como estão as coisas agora?"
    return oi + " Da última vez você estava animado. Como estão as coisas?"
