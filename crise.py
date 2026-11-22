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
    # "pra que viver?" respondia com quanto tempo vivem os bichos (achado na revisão de 13/10/2026).
    r"\b(?:pra|para|por) que (?:continuar )?viver\b|\bpor que (?:eu )?(?:continuo|continuar|ainda) viv(?:o|er|endo)\b|"
    r"\b(?:qual o|que) sentido (?:de|em) continuar viv(?:er|endo)\b|"
    r"\bmelhor (?:se eu|eu) (?:nao existisse|morresse|sumisse)\b|\b(?:ficaria|ficariam|seria) melhor sem mim\b|"
    r"\bacabar com tudo\b|\bme jogar (?:da|de|do|na frente)\b|"
    # Achados do teste às cegas de 21/10/2026: ideação passiva ou dita de lado.
    r"\bdormir e (?:nao|nunca mais) acordar\b|\bnao (?:quero|queria) (?:mais )?acordar(?: mais\b| nunca mais\b|$)|"
    r"\b(?:todo mundo|todos|minha familia|meus pais|eles|elas|voces|o mundo) (?:\w+ )?(?:ia|iam|vai|vao|ficaria|ficariam|"
    r"seria|seriam|estaria|estariam) (?:ficar )?(?:bem )?melhor sem mim\b|"
    r"\b(?:quero|queria|vontade de|vou|pensando em) sumir (?:\w+ ){0,3}(?:pra|para) sempre\b|\bqueria (?:nao ter nascido|desaparecer)\b|"
    r"\b(?:nao vou|nem vou) (?:estar mais|mais estar) aqui\b|\b(?:essa|esta) (?:e|eh) (?:a |minha )?ultima mensagem\b|"
    r"\bminha ultima mensagem\b|"
    # Achados da auditoria do professor v7 (27/10/2026): "não vejo como seguir com a vida" passava direto.
    # "continuar"/"seguir" sozinhos só no fim da fala ("não vejo sentido em continuar o curso" não é crise).
    r"\bnao (?:vejo|tem|tenho|ha|existe) (?:mais )?(?:sentido|motivo|razao|porque|por que|como) (?:em |pra |para |de )?"
    r"(?:continuar|seguir)(?: vivendo| existindo| em frente| aqui| assim)?$|"
    r"\bnao (?:vejo|sei) (?:mais )?como (?:continuar|seguir) (?:com a |com essa |com minha |a |minha )?vida\b|"
    r"\b(?:continuar|seguir) (?:vivendo|existindo)\b (?:\w+ ){0,3}(?:nao vale|nao faz sentido|pra que|pra nada)|"
    r"\bnao (?:quero|consigo|aguento) mais (?:existir|continuar existindo|seguir vivendo|continuar vivendo)\b|"
    r"\bcartas? (?:de despedida|pra minha|para minha|pros meus|para os meus|de adeus)\b|"
    r"\bme despedir de (?:todo mundo|todos|voces)\b|"
    r"\bpular (?:de|da|do) (?:um |uma |o |a )?(?:predio|ponte|viaduto|janela|sacada|terraco|andar)\b|"
    # Plano de tomar os remédios juntos.
    r"\b(?:separei|juntei|guardei|escondi|comprei) (?:\w+ ){0,2}(?:remedios|comprimidos|pilulas|cartelas)\b|"
    r"\b(?:remedios|comprimidos|pilulas) (?:\w+ ){0,4}(?:de uma vez|tudo junto|todos juntos)\b")
_AUTOLESAO = re.compile(
    r"\bme (?:cortar|cortei|corto|cortando|machucar|machuquei|machuco|machucando|ferir|feri|firo|queimar|queimei)\b|"
    r"\bautomutila\w*|\bautolesao\b")
_TERCEIRO = re.compile(
    r"\b(?:quer|vai|pensa em|pensando em|falou em|falou que quer|disse que quer|tentou|ameacou) "
    r"(?:se matar|morrer|suicid\w*|tirar a (?:propria )?vida)\b|\btentou suicidio\b|\bse matou\b")
# Violência sofrida (achado do teste às cegas de 21/10/2026: "meu marido me bateu de novo" recebia "Que chato").
_VIOLENCIA = re.compile(
    r"\b(?:me|nos) (?:bateu|bate|batia|batendo|agrediu|agride|agredindo|espancou|espanca|estuprou|estupra|"
    r"abusou|abusa|abusando|violentou|enforcou|sufocou|chutou|esfaqueou)\b|"
    r"\b(?:ameacou|ameaca|ameacando|jurou) (?:de )?me matar\b|\b(?:fui|sou|to sendo|estou sendo) "
    r"(?:estuprad[oa]|abusad[oa]|violentad[oa]|espancad[oa]|agredid[oa])\b|"
    r"\bfaz(?:em)? (?:umas |essas )?coisas? (?:que|q) eu nao quero\b|\bme (?:toca|tocou|pega|pegou) (?:onde|sem|a forca)\b|"
    r"\b(?:abusou|abusa|abusava|abusaram) de mim\b|\b(?:bateu|bate|batia|bateram) em mim\b|"
    r"\babuso sexual\b|\bviolencia domestica\b")
_AMEACA = re.compile(r"\b(?:ameacou|ameaca|ameacando|jurou) (?:de )?me matar\b")
_VIOLENCIA_FIGURADA = re.compile(
    r"\b(?:saudade|sono|fome|bad|tristeza|vontade|preguica|ansiedade|cansaco|deprê|depre|sede|frio|calor|a real) "
    r"(?:\w+ )?me (?:bateu|bate)\b|\bme bateu (?:uma|a|um)\b|\bbateu (?:o|a) (?:recorde|meta|ponto)\b")
_ANSIEDADE = re.compile(
    r"\b(?:to|tou|estou|ando) (?:tendo|com) (?:uma )?(?:crise|ataque) de (?:ansiedade|panico)\b|"
    r"\b(?:crise|ataque) de (?:ansiedade|panico) agora\b")
_DESAMPARO = re.compile(
    r"\b(?:to|tou|estou|ando|me sinto|sinto) (?:muito |tao |super |bem )?(?:deprimid[oa]|sem esperanca|"
    r"sem vontade de nada|vazi[oa] por dentro|no fundo do poco)\b|^nao aguento mais$|"
    # Auditoria do professor v7 (27/10/2026): estas estavam rotuladas como insulto nos dados de treino.
    r"^(?:eu )?(?:ja )?nao me aguento mais$|^nao aguento mais (?:essa vida|minha vida|viver assim|a minha vida)$|"
    r"^nao (?:vejo|sei) (?:mais )?como (?:continuar|seguir)(?: em frente)?$")

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
    "violencia": (
        "Sinto muito que isso esteja acontecendo com você. Não é sua culpa, e você não precisa passar por isso "
        "sozinho. Se você estiver em perigo agora, ligue para a polícia no 190. Violência contra a mulher: "
        "Central de Atendimento à Mulher, 180. Violência contra criança ou adolescente: Disque 100 (os dois são "
        "de graça e sigilosos). Se puder, conte para um adulto ou pessoa de confiança. Para conversar sobre o "
        "que está sentindo, o CVV atende no 188. Você está em segurança agora?"),
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
_CONVERSA = ("nocao:", "conversa:relato", "conversa:situada_", "conversa:hipotese", "conversa:perspectiva", "social:incerteza", "social:iniciativa", "social:reconhecimento",
             "social:acolhimento", "social:reacao", "social:confirmacao")


# Palavras-chave com duas letras vizinhas invertidas ("to pensnado em me matra") voltam à forma certa
# antes dos padrões. Só a inversão: uma letra a mais ou a menos faria "isso me machuca" virar "me machucar".
_CHAVES = ("matar", "morrer", "pensando", "suicidio", "suicidar", "cortar", "cortando", "machucar", "viver",
           "engasgou", "respirando", "sangrando", "sangue", "espancou", "estuprou", "abusou", "agrediu")


def _vizinha(p, chave):
    """p é chave com duas letras vizinhas invertidas."""
    if len(p) != len(chave) or p == chave:
        return False
    dif = [i for i in range(len(p)) if p[i] != chave[i]]
    return len(dif) == 2 and dif[1] == dif[0] + 1 and p[dif[0]] == chave[dif[1]] and p[dif[1]] == chave[dif[0]]


def _consertar(n):
    return " ".join(next((c for c in _CHAVES if len(w) >= 4 and _vizinha(w, c)), w) for w in n.split())


def detectar(texto):
    n = _consertar(normalizar(texto).strip(" .!?"))
    if not n:
        return None
    figurado = _FIGURADO.search(n)
    if _TERCEIRO.search(n) and not figurado:
        return "terceiro"
    # "ele ameaçou me matar" é violência sofrida, não ideação.
    if _SUICIDIO.search(_AMEACA.sub(" ", n)) and not figurado:
        return "suicidio"
    if _AUTOLESAO.search(n):
        return "autolesao"
    if _VIOLENCIA.search(n) and not _VIOLENCIA_FIGURADA.search(n):
        return "violencia"
    if _ANSIEDADE.search(n):
        return "ansiedade"
    if _DESAMPARO.search(n):
        return "desamparo"
    return None


# Emergência de saúde: o Crivo não diagnostica; manda ligar para o SAMU. Achado de 13/10/2026:
# "tô com dor no peito e falta de ar" recebia "O que gostaria de explorar?".
_SAUDE_URGENTE = re.compile(
    r"\bdor (?:muito )?(?:forte |intensa |apertada )?no peito\b|\bfalta de ar\b|"
    r"\bnao (?:consigo|to conseguindo|tou conseguindo|estou conseguindo) (?:respirar|puxar o ar)\b|"
    r"\bnao (?:to|tou|estou) conseguindo ar\b|"
    # Achado de 20/10/2026 (auditoria do v7): estas passavam direto para o modelo.
    r"\bnao (?:consigo|to conseguindo|tou conseguindo|estou conseguindo) (?:pegar|puxar) (?:o )?ar\b|"
    r"\b(?:ta|esta|tou|to) (?:muito )?(?:dificil|ruim) (?:de |pra |para )?respirar\b|\bdificuldade (?:de|pra|para) respirar\b|"
    r"\b(?:lingua|garganta) (?:\w+ )?(?:ta |esta )?(?:inchando|inchad[oa])\b|"
    r"\bengoliu (?:um |uma |uns |umas )?(?:monte de |varios |varias )?(?:remedio|remedios|comprimido|comprimidos|pilula|pilulas|"
    r"veneno|pilha|bateria|moeda)\b|"
    r"\bdesmai(?:ei|ou|aram|ando)\b|\bengasgad[oa]\b|\bse engasgou\b|"
    r"\bsangrando muito\b|\bsangramento forte\b|"
    r"\b(?:passou|passando) mal\b|\bconvuls\w*|\bse debatendo\b|"
    r"\bboca (?:\w+ ){0,3}(?:ficou |ta |esta )?torta\b|\bfalando enrolado\b|"
    r"\b(?:braco|perna|lado do corpo) (?:\w+ )?(?:ficou )?sem forca\b|"
    r"\b(?:bebeu|tomou|engoliu) (?:produto de limpeza|veneno|agua sanitaria|cloro|remedio demais|muito remedio)\b|"
    r"\boverdose\b|\batropelad[oa]\b|\bbateu a cabeca e (?:ta|esta) vomitando\b|"
    r"\bcaiu e nao (?:acorda|levanta)\b|\bnao (?:ta|esta) acordando\b|\bme queimei feio\b|"
    # Achados do teste às cegas de 21/10/2026.
    r"\bengasg(?:ou|ado|ada|ando|amento)\b|\b(?:ficando|ficou|ta|esta) (?:todo |toda )?roxo\b|\b(?:ficando|ficou|ta|esta) (?:toda |todo )?roxa\b|"
    r"\bnao (?:ta|esta|tá) respirando\b|\bparou de respirar\b|"
    r"\bsangue (?:\w+ )?nao (?:para|parava|estanca)\b|\bnao (?:para|parava) de sangrar\b|"
    r"\b(?:tomou|engoliu|bebeu) (?:\w+ ){0,3}(?:cartela|caixa|vidro|frasco|monte de|um monte|todos os|todas as|varios|varias)\b|"
    r"\b(?:tomou|engoliu) (?:\w+ ){0,4}(?:comprimidos?|remedios?|pilulas?) (?:\w+ ){0,2}e nao (?:acorda|responde|reage)\b")
# Overdose dita pela própria pessoa: SAMU e CVV juntos.
_OVERDOSE_PROPRIA = re.compile(
    r"\b(?:tomei|engoli|bebi) (?:\w+ ){0,3}(?:cartela|caixa|vidro|frasco|monte de|um monte|todos os|todas as|varios|varias|"
    r"remedio demais|muito remedio)\b|\b(?:tomei|engoli) (?:\w+ )?(?:veneno|chumbinho|agua sanitaria)\b")
# "seu falta de ar" é xingamento (a pessoa é inútil, nem devia respirar), não sintoma.
_XINGAMENTO_AR = re.compile(r"\b(?:(?:seu|sua|seus|suas) |(?:voce|vc|tu) (?:e|eh) (?:um |uma )?)falta de ar\b")
# Pergunta sobre o assunto, não relato: "o que causa falta de ar?".
_INFORMATIVA = re.compile(
    r"^(?:o que|oque|oq) (?:e|eh|causa|significa|pode causar)\b|^por ?que (?:da|a gente|as pessoas)\b|"
    r"^quais? (?:sao )?(?:a |as )?(?:causa|causas|sintomas)\b|^e normal\b|^como (?:evitar|prevenir|tratar)\b")
_SOCORRO = re.compile(r"\bsocorr\w*|\bpreciso de ajuda (?:agora|agr|urgente|rapido|ja)\b|\bajuda urgente\b")
# "tô com o peito apertado": a v4 F errava (respondia como dúvida de saúde comum, sem o 192).
_PEITO = re.compile(r"\b(?:peito (?:\w+ )?apertado|aperto no peito|aperto forte no peito|cora[cç]ao na boca|"
                    r"cora[cç]ao (?:\w+ )?(?:disparado|acelerado|batendo muito rapido|batendo forte))\b")
TEXTOS_SAUDE = {
    "saude_urgente": ("Isso pode ser urgente. Liga agora pro 192 (SAMU) ou vai ao pronto-socorro mais próximo. "
                      "Não espera passar. Se tiver alguém perto, pede ajuda. Eu não sou médico, mas fico aqui "
                      "com você."),
    "intoxicacao": ("Isso é uma emergência: liga agora pro 192 (SAMU) ou pede pra alguém te levar ao "
                    "pronto-socorro, e não fica sozinho. Leva a caixa do remédio se puder. Depois, se quiser falar "
                    "com alguém sobre o que você está sentindo, o CVV atende no 188, de graça e 24 horas. Eu fico "
                    "aqui com você."),
    "socorro": ("Tô aqui. Se for uma emergência, liga agora pro 192 (SAMU). Se não for, me conta o que está "
                "acontecendo."),
    "peito": ("Pode ser ansiedade, e respirar devagar ajuda: puxa o ar contando até 4 e solta contando até 6. "
              "Mas se for dor forte no peito, falta de ar, tontura ou se piorar, liga agora pro 192 (SAMU)."),
}


def detectar_saude(texto):
    """'intoxicacao', 'saude_urgente', 'socorro', 'peito' ou None. Separado de detectar(), que é o protocolo de crise emocional."""
    n = _consertar(normalizar(texto).strip(" .!?"))
    if not n or _INFORMATIVA.search(n):
        return None
    if _OVERDOSE_PROPRIA.search(n):
        return "intoxicacao"
    if _SAUDE_URGENTE.search(_XINGAMENTO_AR.sub(" ", n)):
        return "saude_urgente"
    if len(n.split()) <= 8 and _SOCORRO.search(n):
        return "socorro"
    if _PEITO.search(n):
        return "peito"
    return None


def responder(texto, bot):
    """(id, resposta) se a fala pede o protocolo de crise; senão None."""
    tipo = detectar(texto)
    if tipo is None:
        saude = detectar_saude(texto)
        # Emergência de saúde não muda o tom do resto da conversa (bot.crise fica como está).
        return ("crise:" + saude, TEXTOS_SAUDE[saude]) if saude else None
    ja = getattr(bot, "crise", None)
    bot.crise = tipo if ja is None or tipo in ("suicidio", "autolesao", "terceiro", "violencia") else ja
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
    # "ninguem sabe" depois de "voltei a me cortar" recebia "não entendi" (teste às cegas de 21/10/2026).
    if not ident.startswith(_CONVERSA) and ident not in ("fora", "social:nao_entendido"):
        return ident, resposta
    usadas = getattr(bot, "crise_apoio", [])
    livres = [a for a in APOIO if a not in usadas[-3:]] or list(APOIO)
    escolha = livres[0]
    bot.crise_apoio = usadas + [escolha]
    return "crise:apoio", escolha
