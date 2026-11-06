"""Filtro de coerência das falas do professor (20/10/2026, v7c).

Nas situações em que a pessoa pergunta algo AO CRIVO ("você tem medo?", "do que você não gosta?"), as falas antigas do
treino quase sempre se dirigem a ele (você, vc, tu, crivo…). Parte das falas do professor nessas situações fala da
própria pessoa: "Não gosto de quando todo mundo quer só elogiar" (nao_gosta), "Tenho medo de que o tempo me tire…"
(medo), "Acho que o Brasil precisa de…" (opiniao_politica). Com a resposta da situação ("Não sei se sinto medo como
você…"), isso ensina a responder sobre o CRIVO quando a pessoa fala de si, e tira espaço de outras situações.

Regra (fixada antes do treino): numa situação em que ≥ 80% das falas antigas do treino se dirigem ao CRIVO, sai a fala
do professor que **não** se dirige a ele **e** começa falando de si (eu, tenho, acho, gosto, odeio, me irrita, minha…).
Exceções: o_que_acha_de_mim e te_amo, em que falar de si faz parte da situação ("eu sou legal?", "me dá um abraço").
A mesma regra aplicada às falas antigas tira 0 de quase todas essas situações (medido: te_amo 4/158, dificil_falar 2/647).
"""
import re
import unicodedata

LIMIAR_DIRIGIDAS = 0.80
EXCECOES = {"o_que_acha_de_mim", "te_amo"}
TU = re.compile(r"\b(voce|vc|vcs|tu|te|ti|contigo|teu|tua|seu|sua|crivo|ia|robo|bot|maquina|programa|ce)\b")
DE_SI = re.compile(r"^\W*(?:eu\b|nao gosto|gosto|odeio|detesto|curto|nao curto|fico\b|tento|sinto|penso|acho\b|tenho\b|to\b"
                   r"|tou\b|estou\b|preciso|quero|me (?:irrita|incomoda|chateia|da|deixa)|o que (?:eu|me)\b|minha?\b|meus?\b"
                   r"|as vezes|tem dias|hoje eu|ontem)")


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def dirigida(u):
    return bool(TU.search(norm(u)))


def fala_de_si(u):
    return not dirigida(u) and bool(DE_SI.search(norm(u)))


def situacoes_dirigidas(treino):
    """{situação} em que ≥ LIMIAR_DIRIGIDAS das falas antigas se dirigem ao CRIVO. treino: {situação: [falas]}."""
    return {s for s, L in treino.items() if L and s not in EXCECOES and sum(map(dirigida, L)) / len(L) >= LIMIAR_DIRIGIDAS}


def fora(situacao, fala, dirigidas):
    return situacao in dirigidas and fala_de_si(fala)
