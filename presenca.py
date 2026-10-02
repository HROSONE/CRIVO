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
}
POSSESSIVOS = {"meu": "seu", "minha": "sua", "meus": "seus", "minhas": "suas", "eu": "você",
               "mim": "você", "comigo": "com você", "nosso": "de vocês", "nossa": "de vocês"}


def verbo_para_voce(forma, lema=""):
    f = forma.lower()
    if f in IRREGULARES:
        return IRREGULARES[f]
    l = lema.lower()
    if f.endswith("ei") and (l.endswith("ar") or not l):
        return f[:-2] + "ou"
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
    for p in palavras:
        baixo = p.forma.lower()
        if baixo in ("me", "nos", "comigo") and p.classe == "PRON":
            return None
        if baixo in POSSESSIVOS:
            saida.append(POSSESSIVOS[baixo])
            continue
        if p.classe in ("VERB", "AUX") and _primeira_pessoa(p):
            v = verbo_para_voce(p.forma, p.lema)
            if v is None:
                return None
            saida.append(v)
            continue
        saida.append(p.forma)
    texto = " ".join(saida)
    if not sujeito_explicito and saida and _primeira_pessoa_algum(palavras):
        texto = "você " + texto
    return texto


def _primeira_pessoa(p):
    f = normalizar(p.forma)
    lema = normalizar(p.lema)
    if f.endswith("o") and lema.endswith(("ar", "er", "ir")) and f[:-1] == lema[:-2]:
        return True  # presente: "gosto", "acho", "como"
    return (p.forma.lower() in IRREGULARES and p.forma.lower() not in ("estava", "era", "ia", "tinha")) or \
        (f.endswith("ei") and len(f) > 3) or (f.endswith("i") and len(f) > 3 and p.lema.lower().endswith(("er", "ir"))
                                               and f != normalizar(p.lema))


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
        for tom in ("saude", "neg", "pos"):
            for t in reversed(recentes):
                if t[2] == tom:
                    return t
        return recentes[-1]


ABERTURAS = {
    "neg": ("Poxa.", "Que chato.", "Puxa vida.", "Ah, que pena.", "Putz."),
    "saude": ("Sinto muito.", "Poxa, sinto muito.", "Ah, espero que melhore logo."),
    "pos": ("Que bom!", "Que legal!", "Que ótimo!", "Olha só, que bom!", "Boa!"),
    "neutro": ("Entendi.", "Ah, entendi.", "Hum, sei.", "Saquei.", "Certo."),
}

ACOLHER_CURTO = {
    "neg": ("É, cansa mesmo.", "Imagino.", "Faz parte, mas pesa, né?", "Entendo.", "É chato mesmo."),
    "saude": ("Imagino a preocupação.", "Entendo.", "Força aí."),
    "pos": ("Pois é!", "Demais!", "Merecido!"),
    "neutro": ("Tranquilo.", "Sem pressa.", "Entendi.", "Faz sentido."),
}

CONTINUAR = {
    "neg": ("Quer desabafar mais um pouco ou prefere mudar de assunto?",
            "Se quiser contar mais, tô aqui.",
            "E você, como está agora?"),
    "saude": ("Como você está com isso?", "Se quiser, me conta como estão as coisas."),
    "pos": ("Me conta mais!", "E o que mais tem de novo?", "Que bom saber disso. O que mais aconteceu?"),
    "neutro": ("Me conta mais.", "E o que mais?", "Como foi isso?"),
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
        if marcante is not None and marcante[2] in ("neg", "saude"):
            extra = " Depois de tudo isso, você merece."
        return "Descansa bem%s!%s Boa noite." % (vocativo, extra)
    if marcante is None:
        return variacao.escolher(("Até mais%s! Foi bom conversar." % vocativo,
                                  "Tchau%s! Volta quando quiser." % vocativo))
    _, tema, tom, _, agente = marcante
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
    if tom == "saude":
        if agente and agente != "você":
            return variacao.escolher(("Tudo bem por aqui! E %s, já melhorou?" % agente,
                                      "Por aqui tudo certo. E %s, como está?" % agente))
        return "Tudo bem por aqui! E você, já está melhor?"
    proprio = perfil.nomes.get(tema)
    if tom == "neg":
        if proprio:
            return "Tudo bem por aqui! E o %s, sossegou?" % proprio
        return "Tudo bem por aqui! E você, melhorou o ânimo depois daquilo de %s?" % tema
    return "Tudo ótimo! E você, ainda animado com %s?" % _com_artigo(tema)


def _com_artigo(tema):
    feminino = tema.endswith(("a", "ção", "dade", "gem")) and tema not in ("dia",)
    if " " in tema or tema in ("gripe", "doença"):
        feminino = tema.endswith("a") or tema in ("gripe", "doença")
    return ("a " if feminino else "o ") + tema
