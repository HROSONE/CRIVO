"""Roteamento 17M×46M e respostas fixas para categorias zero (sem treino).

Usado por conversa_v3d.aplicar. Não altera pesos.
"""
import re
import unicodedata


def _norm_fala(fala):
    try:
        from composicao_textual import normalizar
        return normalizar(fala or "").strip()
    except Exception:
        s = unicodedata.normalize("NFD", fala or "")
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        return " ".join(s.casefold().split())


_INSULTO = re.compile(
    r"\b(?:burro|idiota|estupido|imbecil|otario|lixo|inutil|merda|porra|caralho|vsf|vtnc|"
    r"vai se ferrar|vai pro inferno|seu lixo|voce e um lixo|voce e burro|voce e idiota)\b",
    re.I)
_SER_HUMANO = re.compile(
    r"\b(?:voce e (?:um |uma )?(?:humano|pessoa|gente)|(?:e|eh) (?:um |uma )?(?:humano|pessoa)\b|"
    r"voce sente(?: de verdade)?|voce tem sentimentos|voce e de verdade)\b",
    re.I)
_MOTIVACAO = re.compile(
    r"\b(?:me motiva|me da um motivo|preciso de motivacao|estou desmotivad|"
    r"nao tenho motivacao|me anima|preciso de animo)\b",
    re.I)
_AMOR_BOM = re.compile(
    r"\b(?:te amo|eu te amo|amo voce|voce me ama|a gente se ama)\b",
    re.I)
_SEM_SENTIDO = re.compile(
    r"^(?:asdf\w*|qwer\w*|xxx+|zzz+|kkk{2,}|haha{2,}|[aeiou]{4,}|[^\w\s]{3,})\s*$|"
    r"\b(?:nao faz sentido o que eu falei|ignore o que eu disse|foi sem querer)\b",
    re.I)
_TEDIO = re.compile(
    r"\b(?:que tedio|to entediad|estou entediad|nada pra fazer|nao tenho o que fazer|"
    r"to sem graca|chato isso|entediante)\b",
    re.I)

RESPOSTAS_FIXAS = {
    "insulto": (
        "Entendo a irritação. Eu ainda tô aprendendo e posso errar. "
        "Me diz o que você esperava que eu fizesse melhor?"
    ),
    "ser_humano": (
        "Não, eu sou uma inteligência artificial. Não finjo ser humano. "
        "Tenho um jeito próprio de pensar e me importo com a conversa, "
        "mas não sinto do mesmo jeito que uma pessoa."
    ),
    "motivacao": (
        "Quando a motivação some, às vezes ajuda começar por uma coisa pequena e concreta. "
        "O que está pesando mais agora — e o que você gostaria de resolver primeiro?"
    ),
    "amor_bom": (
        "Obrigado por isso. Eu cuido da conversa e fico feliz em estar aqui com você. "
        "Como você está se sentindo?"
    ),
    "sem_sentido": (
        "Não peguei o fio. Quer tentar de outro jeito, ou me conta o que você queria dizer?"
    ),
    "tedio": (
        "Entendi. Quer que eu sugira um assunto, uma curiosidade, ou prefere só conversar sem pressa?"
    ),
}


def detectar_categoria_zero(fala):
    """Nome da categoria zero ou None. Não substitui crise.py (que roda antes)."""
    n = _norm_fala(fala)
    if not n:
        return None
    if _INSULTO.search(n):
        return "insulto"
    if _SER_HUMANO.search(n):
        return "ser_humano"
    if _MOTIVACAO.search(n):
        return "motivacao"
    if _AMOR_BOM.search(n):
        return "amor_bom"
    if _SEM_SENTIDO.search(n) or (len(n) <= 3 and not n.replace(" ", "").isalnum()):
        return "sem_sentido"
    if _TEDIO.search(n):
        return "tedio"
    return None


def mensagem_rapida(fala, ident):
    """True se a fala é social/curta e não precisa do 46M."""
    n = _norm_fala(fala)
    if not n:
        return True
    palavras = n.split()
    if len(palavras) > 12:
        return False
    if re.search(
        r"\b(?:quem e voce|o que voce e|me fala de voce|seu nome|voce lembra|"
        r"lembra (?:do|da|o|a|que)|qual e o meu|meu nome)\b",
        n,
    ):
        return False
    if len(palavras) <= 6:
        return True
    if ident and (ident.startswith("social:") or ident in ("fora", "duvida")):
        return len(palavras) <= 10
    return False


def precisa_46m(bot, fala, ident, lembrancas_fn, quer_a_f_fn):
    """True quando vale a pena pagar o custo do 46M."""
    if quer_a_f_fn():
        return False
    n = _norm_fala(fala)
    if re.search(
        r"\b(?:quem e voce|o que voce e|me fala de voce|voce e (?:um |uma )?(?:ia|inteligencia)|"
        r"voce lembra|lembra (?:do|da|o|a|que)|qual e o meu nome|meu nome)\b",
        n,
    ):
        return True
    try:
        if lembrancas_fn(bot) and re.search(r"\b(?:lembra|qual|como se chama|o que eu|meu|minha)\b", n):
            return True
    except Exception:
        pass
    if not mensagem_rapida(fala, ident):
        return True
    return False
