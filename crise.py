"""Protocolo de crise: vem antes de qualquer outra resposta.

Quando a pessoa fala em se matar, em se machucar, que alguém próximo corre
esse risco, que está numa crise de ansiedade ou muito deprimida, o Crivo
não conversa como de costume (nada de "que legal", de plano de ação ou de
noção): acolhe, diz com clareza onde há ajuda agora e pergunta se ela está
em segurança. O Crivo não é atendimento de saúde e não diagnostica.

Recursos no Brasil: CVV 188 (ligação gratuita, 24 horas; chat em
cvv.org.br) e SAMU 192 em perigo imediato.
"""
import re

from linguagem_conversa import normalizar

# Expressões do dia a dia que usam as mesmas palavras sem risco.
_FIGURADO = re.compile(
    r"\bmorr\w* de (?:rir|fome|sono|vergonha|calor|frio|saudade|tedio|inveja|medo|cansaco|preguica|curiosidade)\b|"
    r"\b(?:me|ta me|esta me|tao me) matando\b|\bmatar (?:a saudade|aula|o tempo|um processo|o processo|a fome|a sede)\b|"
    r"\besquadrao suicida\b|\bse mata no final\b")

_SUICIDIO = re.compile(
    r"\b(?:quero|queria|vou|penso em|pensando em|pensei em|tenho vontade de|vontade de|da vontade de) "
    r"(?:me matar|morrer|sumir de vez|acabar com (?:a )?minha vida|tirar (?:a )?minha (?:propria )?vida|"
    r"me jogar)\b|"
    r"\bsuicid\w*|\bme matar\b|\btirar (?:a )?minha (?:propria )?vida\b|"
    r"\bnao (?:quero|aguento|consigo) mais viver\b|\bnao (?:vejo|tem|tenho) (?:mais )?(?:sentido|motivo|razao) "
    r"(?:em|pra|para|de) viver\b|\bnao vale a pena (?:viver|continuar vivendo)\b|"
    r"\bmelhor (?:se eu|eu) (?:nao existisse|morresse|sumisse)\b|\b(?:ficaria|ficariam|seria) melhor sem mim\b|"
    r"\bacabar com tudo\b|\bme jogar (?:da|de|do|na frente)\b")
_AUTOLESAO = re.compile(
    r"\bme (?:cortar|cortei|corto|cortando|machucar|machuquei|machuco|machucando|ferir|feri|firo|queimar|queimei)\b|"
    r"\bautomutila\w*|\bautolesao\b")
_TERCEIRO = re.compile(
    r"\b(?:quer|vai|pensa em|pensando em|falou em|falou que quer|disse que quer|tentou|ameacou) "
    r"(?:se matar|morrer|suicid\w*|tirar a (?:propria )?vida)\b|\btentou suicidio\b|\bse matou\b")
_ANSIEDADE = re.compile(
    r"\b(?:to|tou|estou|ando) (?:tendo|com) (?:uma )?(?:crise|ataque) de (?:ansiedade|panico)\b|"
    r"\b(?:crise|ataque) de (?:ansiedade|panico) agora\b")
_DESAMPARO = re.compile(
    r"\b(?:to|tou|estou|ando|me sinto|sinto) (?:muito |tao |super |bem )?(?:deprimid[oa]|sem esperanca|"
    r"sem vontade de nada|vazi[oa] por dentro|no fundo do poco)\b|^nao aguento mais$")

TEXTOS = {
    "suicidio": (
        "Sinto muito que você esteja passando por isso, e obrigado por me contar. O que você está sentindo "
        "importa, e você não precisa enfrentar isso sozinho. Por favor, fale agora com alguém que possa te "
        "ajudar: o CVV atende pelo 188, de graça e 24 horas, ou pelo chat em cvv.org.br. Se você estiver em "
        "perigo neste momento, ligue para o SAMU no 192 ou vá a um pronto-socorro. Você está em segurança "
        "agora?"),
    "autolesao": (
        "Obrigado por me contar, sei que não é fácil. Você merece cuidado, não julgamento. Se tiver algum "
        "ferimento, cuide dele ou procure atendimento; em perigo agora, o SAMU atende no 192. Para conversar "
        "com alguém sobre o que está sentindo, o CVV atende pelo 188, de graça e 24 horas, ou em cvv.org.br. "
        "Você está em segurança neste momento?"),
    "terceiro": (
        "Isso é sério, e é muito bom que você esteja atento. Se a pessoa estiver em perigo agora, ligue para "
        "o SAMU no 192 e não a deixe sozinha. Converse com ela com calma, sem julgar, e incentive a buscar "
        "ajuda: o CVV atende pelo 188, de graça e 24 horas, e também pode orientar você. Ela está em segurança "
        "neste momento?"),
    "ansiedade": (
        "Sinto muito, deve estar sendo muito difícil agora. Tenta respirar devagar comigo: puxa o ar contando "
        "até 4 e solta contando até 6, algumas vezes. Crises assim costumam passar em alguns minutos, mesmo "
        "que pareçam não ter fim. Se houver dor no peito, falta de ar forte ou for a primeira vez, procure "
        "atendimento (SAMU 192). Se quiser conversar com alguém agora, o CVV atende no 188. Estou aqui: "
        "como você está?"),
    "desamparo": (
        "Sinto muito que você esteja se sentindo assim, e obrigado por me contar. Você não precisa passar por "
        "isso sozinho: conversar com alguém de confiança ou com um profissional de saúde pode ajudar, e o CVV "
        "atende pelo 188, de graça e 24 horas, só para ouvir. Se em algum momento pensar em se machucar, "
        "procure ajuda na hora. Quer me contar o que está acontecendo?"),
}
CONTINUAR = ("Estou aqui com você. Se precisar falar com alguém agora, o CVV atende no 188, de graça e 24 "
             "horas, e o SAMU no 192 em caso de perigo. Quer me contar mais?")
# Depois de uma crise, a conversa continua com cuidado: sem reação alegre,
# sem puxar assunto leve e lembrando, de vez em quando, onde há ajuda.
APOIO = (
    "Estou aqui. Como você está se sentindo agora?",
    "Obrigado por continuar conversando comigo. O que está pesando mais agora?",
    "Entendo. Lembra que o CVV atende no 188, a qualquer hora, se você quiser falar com alguém. "
    "Quer continuar me contando?",
    "Faz sentido. Você tem alguém de confiança por perto com quem possa falar hoje?",
)
_ALEGRE = re.compile(r"\b(?:que legal|que bom|que otimo|que demais|parabens|boa!|olha so|merecido|que delicia)\b")
_CONVERSA = ("nocao:", "conversa:relato", "social:incerteza", "social:iniciativa", "social:reconhecimento",
             "social:acolhimento", "social:reacao", "social:confirmacao")


def detectar(texto):
    n = normalizar(texto).strip(" .!?")
    if not n:
        return None
    figurado = _FIGURADO.search(n)
    if _TERCEIRO.search(n) and not figurado:
        return "terceiro"
    if _SUICIDIO.search(n) and not figurado:
        return "suicidio"
    if _AUTOLESAO.search(n):
        return "autolesao"
    if _ANSIEDADE.search(n):
        return "ansiedade"
    if _DESAMPARO.search(n):
        return "desamparo"
    return None


def responder(texto, bot):
    """(id, resposta) se a fala pede o protocolo de crise; senão None."""
    tipo = detectar(texto)
    if tipo is None:
        return None
    ja = getattr(bot, "crise", None)
    bot.crise = tipo if ja is None or tipo in ("suicidio", "autolesao", "terceiro") else ja
    if ja == tipo:
        return "crise:" + tipo, CONTINUAR
    return "crise:" + tipo, TEXTOS[tipo]


def ajustar(ident, resposta, bot):
    """Depois de uma crise na conversa, as respostas de conversa (reações,
    noções, puxar assunto) viram acolhimento; perguntas sobre fatos seguem."""
    if not getattr(bot, "crise", None):
        return ident, resposta
    if ident in ("social:obrigado", "social:despedida", "social:tchau"):
        return ident, ("Fico feliz em ter conversado com você. Se cuida, e lembra: o CVV atende no 188, de graça "
                       "e a qualquer hora, e o SAMU no 192 em caso de perigo. Estou aqui se quiser voltar a conversar.")
    if not ident.startswith(_CONVERSA):
        return ident, resposta
    usadas = getattr(bot, "crise_apoio", [])
    livres = [a for a in APOIO if a not in usadas[-3:]] or list(APOIO)
    escolha = livres[0]
    bot.crise_apoio = usadas + [escolha]
    return "crise:apoio", escolha
