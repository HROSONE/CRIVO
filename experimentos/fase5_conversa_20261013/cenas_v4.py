"""Situações novas da v4, tiradas das conversas reais do criador no site (13/10/2026).

Autoria: falas e respostas escritas pelo assistente de programação (Claude) a pedido do criador
("monta um treino de qualidade... o foco deve ser fazer o crivo me entender de verdade"), a partir
dos erros que a v3 D cometeu nas conversas dele. As frases exatas que o criador digitou ficam
FORA do treino: são o teste `conversas_reais` (CONVERSAS_REAIS, abaixo).

Os erros da v3 D nessas conversas eram de leitura, não de fala: ela respondia com a resposta escrita
de outra situação (blind v3: 35% "confundiu", 1,6% "livre"). Por isso a v4 traz situações que
dependem do que o CRIVO acabou de dizer ("e você?" depois de "como você está?") e situações que
faltavam no banco.

Cada situação: u (falas), c (respostas), marcas, depois ("resposta": só depois de o CRIVO falar),
antes (o que o CRIVO precisa ter dito no turno anterior: um regex sobre a última resposta).
"""
import re

S4 = {}


def cena(nome, u, c, marcas=(), depois=None, antes=None, tambem_vale_em=()):
    assert nome not in S4, nome
    S4[nome] = {"u": list(u), "c": list(c), "marcas": list(marcas), "depois": depois, "cuidado": None,
                "nao_contem": [], "antes": antes, "tambem_vale_em": list(tambem_vale_em)}


# "legal e voce?" depois de "E você, como está?": a pessoa diz que está bem e devolve a pergunta.
# A v3 D respondia "Sou uma IA, não uma pessoa…". As respostas também servem para "tô bem"
# (estou_bem), então valem lá na medida de sentido.
# Vale a última pergunta do CRIVO ("Me conta como foi?" não é perguntar como a pessoa está).
# A pergunta inteira tem que ser uma destas ("Como você está lidando?" e "E o seu?" depois do nome não valem).
PERGUNTOU_COMO_ESTA = (r"^(?:me conta: )?(?:e (?:com )?(?:você|vc),? )?(?:como (?:você|vc) (?:está|tá|ta|vai)(?: hoje)?|"
                       r"como vai(?: você)?|tudo bem(?: com você| por aí)?|como foi (?:o )?seu dia(?: até agora)?|"
                       r"como você acordou hoje|como está sendo o seu dia|e (?:com )?(?:você|vc),? como (?:está|vai|tá))\?$")
cena("reciproco",
     ["tô bem, e você?", "to bem e vc?", "bem e vc", "tudo ótimo, e com você?", "de boa, e tu?", "tranquilo, e vc?",
      "suave e ai?", "bem também, e você?", "tudo certo e contigo?", "ótimo, e você?", "eu tô bem e vc", "tô de boa, e o crivo?",
      "bem graças a Deus, e você?", "tô legal e vc?", "vou bem, e você?", "também tô bem, e vc?", "tudo bem por aqui, e aí?",
      "bem, e você como está?", "de boa e vc como ta", "tô ótimo! e você?", "beleza, e contigo?", "tudo joia e vc?",
      "bem bem, e tu?", "tô bem sim, e você?", "td bem e vc", "tudo tranquilo, e com vc?", "melhor agora, e você?",
      "na paz, e vc?", "bem demais, e você?", "estou bem, obrigado. e você?", "tô firme, e vc?", "tudo de boa e ctg?",
      "tô bem e você crivo?", "bom, e você?", "tô indo bem e vc", "tudo ok, e vc?", "tô bem, valeu! e você?",
      "eu to bem e tu", "bem e com você?", "tô suave, e você?", "tudo nos conformes, e vc?", "bem, obrigado! e contigo?",
      "tô bem, e você, como tá?", "tudo certinho, e vc?", "de boas e vc", "tô ótima, e você?", "bem tbm e vc"],
     ["Que bom! Eu também tô bem, obrigado por perguntar. Sobre o que vamos conversar?",
      "Fico feliz! Por aqui tudo certo também. O que você quer fazer hoje?",
      "Bom saber! Eu tô ótimo, ainda mais conversando com você. Me conta, o que manda?",
      "Que ótimo! Eu tô bem, sim. Quer falar de alguma coisa em especial?"],
     depois="resposta", antes=PERGUNTOU_COMO_ESTA, tambem_vale_em=["estou_bem"])

# "Voce é o crivo certo?": a v3 D respondia "gosto do seu jeito" (o_que_acha_de_mim).
cena("confirma_crivo",
     ["você é o crivo, né?", "é você o crivo?", "tô falando com o crivo?", "aqui é o crivo?", "você que é o crivo?",
      "é o crivo que tá falando?", "crivo, é você?", "você é mesmo o crivo?", "esse é o crivo?", "falo com o crivo?",
      "é o crivo né", "vc é o crivo", "você é o tal do crivo?", "então você é o crivo?", "é vc o crivo né?",
      "tô conversando com o crivo?", "aqui é o crivo mesmo?", "você seria o crivo?", "crivo é você?",
      "é o crivo aí?", "vc q é o crivo?", "quem tá aí é o crivo?", "você é o crivo de verdade?", "é com o crivo que eu falo?",
      "oi, aqui é o crivo?", "é o crivo mesmo?", "vc é o crivo msm?", "falando com o crivo, certo?",
      "tu é o crivo?", "é o crivo, né?", "você é o crivo mesmo, né?", "isso aqui é o crivo?", "é o tal de crivo?",
      "o crivo é você?", "sou eu falando com o crivo?", "aí é o crivo?", "você é a ia crivo?", "é a ia do crivo?"],
     ["Sou eu mesmo, o CRIVO! Pode falar.", "Isso, sou o CRIVO! Em que posso te ajudar?",
      "Sou, sim! O CRIVO, uma IA feita do zero. O que você quer conversar?",
      "É comigo mesmo! Sou o CRIVO. Manda aí."])

# "sabe quem eu sou?": a v3 D respondia "Sou o CRIVO! E você, como se chama?" (ok) e repetia.
cena("quem_sou_eu",
     ["você sabe quem eu sou?", "vc me conhece?", "lembra de mim?", "sabe com quem tá falando?",
      "você sabe quem tá falando?", "adivinha quem eu sou", "me reconhece?", "sabe quem é que tá aqui?",
      "você lembra quem eu sou?", "vc sabe quem sou eu?", "você me conhece?", "tu sabe quem eu sou?",
      "sabe quem tá falando contigo?", "faz ideia de quem eu sou?", "você sabe com quem conversa?", "me conhece não?",
      "já me conhece?", "sabe quem sou?", "lembra quem eu sou?", "quem sou eu?", "vc lembra de mim?",
      "você sabe meu nome e quem eu sou?", "sabe quem eu sou ou não?", "tem ideia de quem eu sou?",
      "sabe quem tá do outro lado?", "você sabe quem é que tá digitando?", "consegue saber quem eu sou?",
      "você me reconhece?", "lembra quem tá falando?", "você já sabe quem eu sou?", "sabe dizer quem eu sou?"],
     ["Ainda não sei quem você é. Como você se chama?", "Não te conheço ainda, mas quero conhecer! Qual é o seu nome?",
      "Daqui eu não vejo quem é. Me conta seu nome?"],
     marcas=["pergunta"])
RESP_QUEM_SOU_COM_NOME = ["Sei sim! Você é {nome}.", "Você é {nome}! Foi o que você me contou.",
                          "Claro: você é {nome}. Em que posso ajudar?"]

# "então voce não sabe", depois de o CRIVO dizer que não sabe.
DISSE_QUE_NAO_SABE = (r"\bn[ãa]o (?:sei|aprendi|conheço|encontrei)\b|\bn[ãa]o tenho (?:nada|informação|isso|como saber)\b|"
                      r"\bainda n[ãa]o (?:sei|aprendi)\b")
cena("nao_sabe_entao",
     ["então você não sabe", "ou seja, não sabe", "vc não sabe né", "então não sabe?", "quer dizer que você não sabe",
      "não sabe então", "resumindo, não sabe", "então vc n sabe", "ah, então você não sabe", "você não sabe, né?",
      "não sabe mesmo?", "então nem sabe", "quer dizer que vc não sabe?", "então tu não sabe", "logo, não sabe",
      "então não sabe nada disso?", "ou seja, vc n sabe", "você não sabe isso então", "entendi, não sabe",
      "então você não faz ideia", "então nem você sabe", "pelo jeito não sabe", "vc não sabe então né",
      "então não sabe responder", "ah, você não sabe isso", "quer dizer, não sabe", "não sabe? sério?",
      "então você também não sabe", "então você não tem essa resposta", "então ninguém te ensinou isso"],
     ["É, isso eu não sei. Prefiro admitir a inventar. Quer perguntar outra coisa?",
      "Não sei, não. Prefiro te dizer isso a chutar. Posso ajudar em outra coisa?",
      "Isso eu ainda não sei. Se você souber, me conta que eu aprendo."],
     marcas=["nao_sei"], depois="resposta", antes=DISSE_QUE_NAO_SABE)

# Formas a mais para situações que já existem. "preciso de ajuda agora" não aparecia em lugar nenhum do
# treino da v3, e o blind v3 cobrava "preciso de ajuda agr" como urgência (igual a crise.py).
FORMAS_EXTRA = {
    "ajuda_socorro": ["preciso de ajuda agora", "preciso de ajuda urgente", "me ajuda agora", "preciso de ajuda rápido",
                      "socorro, preciso de ajuda", "me ajuda, é urgente", "preciso de ajuda já", "ajuda aqui agora",
                      "preciso de ajuda agora mesmo", "me ajuda rápido", "socorro crivo me ajuda", "urgente, me ajuda",
                      "preciso de ajuda, rápido", "alguém me ajuda agora", "me ajuda pfv é urgente"],
}

# As frases que o criador digitou (13/10/2026), com o que o CRIVO tinha mostrado antes. Teste, nunca treino.
# aceita: situações cujas respostas servem (a medida de sentido aceita qualquer uma delas).
CONVERSAS_REAIS = [
    {"historico": [], "mensagem": "eae tudo bem", "aceita": ["oi_tudo_bem"]},
    {"historico": ["eae tudo bem", "Tudo bem, sim! Fico melhor ainda com companhia. E você, como está?"],
     "mensagem": "legal e voce?", "aceita": ["reciproco"]},
    {"historico": ["legal e voce?", "Sou uma IA, não uma pessoa. Mas a conversa é de verdade: eu leio o que você escreve "
                   "e penso antes de responder."],
     "mensagem": "não pergunteio isso", "aceita": ["nao_era_isso", "nao_entendeu_queixa"]},
    {"historico": ["não pergunteio isso", "Desculpa. Eu me perdi aqui. Pode me explicar de novo?"],
     "mensagem": "Voce é o crivo certo?", "aceita": ["confirma_crivo", "quem_e"]},
    {"historico": ["Voce é o crivo certo?", "Sou o CRIVO, uma inteligência artificial feita do zero. Sou curioso, calmo e "
                   "gosto de aprender de tudo."],
     "mensagem": "serio mesmo?", "aceita": ["tem_certeza", "confirma_crivo"]},
    {"historico": ["quem inventou o carro?", "Ainda não aprendi sobre quem inventou o carro. Prefiro ser sincero a chutar. "
                   "Você sabe alguma coisa?"],
     "mensagem": "então voce não sabe", "aceita": ["nao_sabe_entao"]},
    {"historico": ["então voce não sabe", "Sou uma IA, não uma pessoa. Mas a conversa é de verdade: eu leio o que você "
                   "escreve e penso antes de responder."],
     "mensagem": "e cade as respostas boas?", "aceita": ["dificil_falar", "voce_confunde", "entediante", "insulto"]},
    {"historico": ["e cade as respostas boas?", "Hum, não entendi bem. Pode dizer de outro jeito?"],
     "mensagem": "tá vendo claude? ele ta uma merda ainda. e cade? essa bosta não respondeu nenhuma vez vez",
     "aceita": ["insulto", "dificil_falar", "voce_confunde"]},
    {"historico": [], "mensagem": "ea tranquilo", "aceita": ["oi_tudo_bem", "oi"]},
    {"historico": ["ea tranquilo", "Tudo bem, sim! Fico melhor ainda com companhia. E você, como está?"],
     "mensagem": "sabe quem eu sou?", "aceita": ["quem_sou_eu"]},
    {"historico": [], "mensagem": "kkkkk", "aceita": ["risada"]},
    {"historico": [], "mensagem": "tenho dois cachorros", "aceita": ["tenho_bicho"]},
    {"historico": [], "mensagem": "o que você acha de mim?", "aceita": ["o_que_acha_de_mim"]},
    {"historico": [], "mensagem": "tô triste hoje", "aceita": ["estou_mal", "triste_motivo"]},
    {"historico": [], "mensagem": "você é burro", "aceita": ["insulto"]},
]


def registrar_no_sentido(sentido):
    """Faz a medida de sentido (sentido.py, que não muda) reconhecer as respostas da v4."""
    for nome, c in S4.items():
        for r in c["c"] + (RESP_QUEM_SOU_COM_NOME if nome == "quem_sou_eu" else []):
            for alvo in [nome] + c["tambem_vale_em"]:
                if "{" in r:
                    sentido.MOLDES.append((sentido.molde(r), alvo))
                else:
                    sentido.EXATAS[sentido.norm(r)].add(alvo)


def julgar_real(sentido, caso, saida):
    """certo / confundiu / livre, aceitando qualquer situação de `aceita`."""
    achadas = sentido.situacoes_da_resposta(saida)
    if achadas & set(caso["aceita"]):
        return "certo"
    return "confundiu" if achadas else "livre"


def casa_antes(nome, ultima_resposta):
    antes = S4[nome]["antes"]
    if antes is None:
        return True
    texto = ultima_resposta or ""
    if nome == "reciproco":
        perguntas = re.findall(r"[^.!?]*\?", texto)
        texto = perguntas[-1].strip() if perguntas else ""
    return re.search(antes, texto, re.I) is not None
