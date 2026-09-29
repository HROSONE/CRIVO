"""Referências demonstrativas em perguntas de seguimento.

Lê SOMENTE a resposta imediatamente anterior do assistente, nunca o
texto de outros turnos como fato. Reconhece o referente lexical exato
(singular/plural simples), mas NÃO inventa nomes, datas ou detalhes que
não estavam no conhecimento cadastrado. Sem IA externa.
"""
import re
import unicodedata


def normalizar_termos(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", texto)


def radical_simples(palavra):
    if len(palavra) > 4 and palavra.endswith("oes"):
        return palavra[:-3] + "ao"
    if len(palavra) > 3 and palavra.endswith("s"):
        return palavra[:-1]
    return palavra


def interpretar_referencia(pergunta, resposta_anterior):
    """Retorna (id, resposta) ou None para perguntas SEM demonstrativo.

    Requer forma interrogativa e alvo explícito com esse/essa/desse/dessa
    e semelhantes; uma coincidência isolada com palavras anteriores
    nunca autoriza uma resposta factual. Se não houver referente no
    último turno, pede esclarecimento.
    """
    toks = normalizar_termos(pergunta)
    if not toks or len(toks) > 85:
        return None
    primeiro = toks[0]
    if primeiro not in ("qual", "quais", "como", "onde", "quando",
                        "quanto", "quantos", "quantas", "por", "que",
                        "quem", "me", "voce", "poderia", "pode"):
        return None

    demonstrativos = {
        "esse", "essa", "esses", "essas", "desse", "dessa", "desses",
        "dessas", "aquele", "aquela", "aqueles", "aquelas",
        "daquele", "daquela", "daqueles", "daquelas"
    }
    ignorar = {"que", "qual", "quais", "nome", "tipo", "outra", "outro",
               "mesmo", "mesma", "coisa", "algo", "assunto", "isso", "isto"}
    alvos = [toks[i + 1] for i, palavra in enumerate(toks[:-1])
             if palavra in demonstrativos and toks[i + 1] not in ignorar]
    if len(alvos) != 1:
        return None
    alvo = alvos[0]
    if len(alvo) < 3:
        return None

    fonte = {radical_simples(t) for t in
             normalizar_termos(resposta_anterior or "")}
    if radical_simples(alvo) not in fonte:
        return ("contexto:sem_referencia",
                "Qual " + alvo + " você quer dizer? Não consegui "
                "identificar esse referente na minha resposta anterior. "
                "Pode especificar o objeto ou o assunto?")

    return ("contexto:detalhe_ausente",
            "Você está se referindo ao " + alvo +
            " mencionado na minha resposta anterior. "
            "Reconheci o assunto, mas não tenho informação cadastrada "
            "suficiente para responder a esse detalhe com segurança. "
            "Não vou inventar um nome ou outra característica.")
