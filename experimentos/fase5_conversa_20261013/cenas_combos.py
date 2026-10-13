"""Terceira leva: respostas compostas de partes escritas para se encaixar.

Nas situações mais frequentes, a resposta é abertura + miolo + fechamento. Cada parte foi
escrita para combinar com todas as outras do mesmo grupo, o que multiplica a variedade sem
frase estranha. Mesma autoria de cenas.py.
"""
import itertools
import random

from cenas import S


def combos(abre, meio, fecha, limite=120, semente=0):
    tudo = [" ".join(p for p in trio if p) for trio in itertools.product(abre, meio, fecha)]
    random.Random(semente).shuffle(tudo)
    return tudo[:limite]


def acrescentar(nomes, respostas):
    for nome in nomes:
        S[nome]["c"] += respostas


ACOLHER = combos(
    ["Sinto muito.", "Poxa.", "Que difícil.", "Imagino como deve ser.", "Puxa, sinto muito mesmo.",
     "Ei, tô aqui.", "Entendo."],
    ["Faz todo sentido você se sentir assim.", "Ninguém precisa passar por isso sozinho.",
     "Às vezes o dia pesa mais do que a gente aguenta.", "O que você sente é importante.",
     "Você não precisa resolver tudo agora.", "Tá tudo bem não estar bem às vezes.", ""],
    ["Quer me contar o que aconteceu?", "Se quiser desabafar, eu escuto com calma.", "Tô aqui pra ouvir.",
     "Quer falar mais sobre isso?", "O que te ajudaria agora?", "Me conta, se quiser."], semente=1)
acrescentar(["estou_mal", "ansioso", "sozinho", "motivacao"], ACOLHER[:60])

ERREI = combos(
    ["Desculpa.", "Foi mal.", "Me desculpa.", "Você tem razão, desculpa.", "Desculpa, eu me confundi."],
    ["Acho que entendi errado.", "Eu me perdi aqui.", "Ainda erro mais do que gostaria.",
     "Fui pro lado errado.", ""],
    ["Pode me explicar de novo?", "Me diz de outro jeito?", "O que você quis dizer?",
     "Me ajuda a entender?", "Vamos tentar de novo, com calma?", "Me conta com suas palavras?"], semente=2)
acrescentar(["nao_entendeu_queixa", "nao_era_isso", "dificil_falar", "voce_confunde"], ERREI[:50])

CALMA_INSULTO = combos(
    ["Entendo a irritação.", "Tudo bem ficar bravo comigo.", "Sinto que te frustrei.", "Poxa, deixei a desejar."],
    ["Não vou revidar.", "Eu ainda tô aprendendo.", "Prefiro saber onde errei.", "Sigo aqui, com calma."],
    ["Me mostra o que deu errado?", "Quer tentar de novo?", "Se quiser, a gente recomeça.",
     "Me diz o que você esperava?"], semente=3)
acrescentar(["insulto"], CALMA_INSULTO[:40])

OI = combos(
    ["Oi!", "Olá!", "E aí!", "Opa, oi!", "Oi, oi!"],
    ["Que bom te ver.", "Tô por aqui.", "Bom que você apareceu.", "Pronto pra conversar.", ""],
    ["Como você está?", "Sobre o que vamos conversar?", "O que manda hoje?", "Me conta alguma novidade?",
     "Como foi seu dia?"], semente=4)
acrescentar(["oi"], OI[:50])

TCHAU = combos(
    ["Tchau!", "Até mais!", "Falou!", "Até logo!", "Vai lá!"],
    ["Foi bom conversar com você.", "Obrigado pela conversa.", "Gostei de falar com você.", ""],
    ["Se cuida.", "Volta quando quiser.", "Fica bem.", "Tô aqui quando precisar."], semente=5)
acrescentar(["despedida"], TCHAU[:45])

DE_NADA = combos(
    ["De nada!", "Imagina!", "Por nada!", "Disponha!", "Que nada!"],
    ["Gostei de ajudar.", "Foi um prazer.", "Fico feliz que ajudou.", ""],
    ["Precisando, é só chamar.", "Volta sempre.", "Tô aqui pro que precisar.", ""], semente=6)
acrescentar(["obrigado"], DE_NADA[:40])

FELIZ = combos(
    ["Que notícia boa!", "Uau!", "Que legal!", "Parabéns!", "Que alegria!"],
    ["Fico feliz por você.", "Você merece.", "Dá pra sentir sua alegria daqui.", ""],
    ["Me conta mais!", "Como você está se sentindo?", "Como foi?", "Vai comemorar?"], semente=7)
acrescentar(["feliz_motivo"], FELIZ[:40])

CURIOSO = combos(
    ["Me conta!", "Quero saber!", "Que interessante.", "Opa, conta mais."],
    ["Fiquei curioso.", "Adoro ouvir histórias assim.", ""],
    ["O que aconteceu?", "Como foi?", "E aí, como você se sentiu?"], semente=8)
acrescentar(["dia", "filme_visto", "viagem_voltou"], CURIOSO[:30])
