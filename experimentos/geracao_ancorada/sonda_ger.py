import sys
from crivo import Crivo
PERGUNTAS = [
 "Quando foi a Guerra do Paraguai e quem lutou nela?",
 "Qual presidente americano libertou os escravizados e como ele morreu?",
 "Quem convocou as Cruzadas e o que aconteceu com Jerusalém?",
 "Como a tuberculose é transmitida?",
 "Por que o céu é azul?",
 "Quem pintou a Mona Lisa e onde ela está?",
 "Quando o Brasil ficou independente e quem proclamou?",
 "O que causa a intolerância à lactose e quais os sintomas?",
 "Onde fica o Egito e qual a capital?",
 "Quem foi Pelé?",
 "Como funciona a vacina?",
 "Qual a diferença entre vírus e bactéria?",
]
for p in PERGUNTAS:
    a = Crivo(); i0, r0 = a.responder(p)
    b = Crivo(); b.usar_geracao = True; i1, r1 = b.responder(p)
    print("P:", p, "|", i0, "|", (a.historico[-1].get("mecanismo") if a.historico else None))
    print("  ANTES :", r0[:300].replace("\n", " "))
    if r1 != r0:
        print("  DEPOIS:", r1[:300].replace("\n", " "), "[%s]" % b.voz_do_turno)
