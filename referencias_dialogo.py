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
    # A normalização é usada somente para correspondência. Na mensagem
    # exibida preserve o termo original com os acentos do português.
    superficie = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", pergunta.lower())
    if not toks or len(toks) > 85 or len(superficie) != len(toks):
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
    alvos = [(toks[i + 1], superficie[i + 1])
             for i, palavra in enumerate(toks[:-1])
             if palavra in demonstrativos and toks[i + 1] not in ignorar]
    if len(alvos) != 1:
        return None
    alvo, alvo_exibicao = alvos[0]
    if len(alvo) < 3:
        return None

    fonte = {radical_simples(t) for t in
             normalizar_termos(resposta_anterior or "")}
    if radical_simples(alvo) not in fonte:
        return ("contexto:sem_referencia",
                "Qual " + alvo_exibicao + " você quer dizer? Não consegui "
                "identificar esse referente na minha resposta anterior. "
                "Pode especificar o objeto ou o assunto?")

    return ("contexto:detalhe_ausente",
            "Você está se referindo ao " + alvo_exibicao +
            " mencionado na minha resposta anterior. "
            "Reconheci o assunto, mas não tenho informação cadastrada "
            "suficiente para responder a esse detalhe com segurança. "
            "Não vou inventar um nome ou outra característica.")


def conferir_mencao_anterior(pergunta, resposta_anterior):
    """Confere se o assistente mencionou um termo no turno anterior.

    Diferencia perguntas sobre a conversa de perguntas factuais: não
    usar TF-IDF para dar a definição da Lua ao ouvir 'você falou da Lua?'.
    A presença é lexical, não prova conhecimento sobre o objeto.
    """
    termos = normalizar_termos(pergunta)
    if not termos or len(termos) > 85:
        return None
    n = " ".join(termos)
    m = re.fullmatch(
        r"(?:voce|vc) (?:falou|mencionou|citou) "
        r"(?:de|do|da|dos|das|sobre) ([a-z0-9 ]+)", n)
    if not m:
        return None
    tema = m.group(1).strip()
    if not tema or len(tema) > 80 or len(tema.split()) > 7:
        return None
    if not resposta_anterior:
        return ("contexto:sem_referencia",
                "Ainda não tenho uma resposta anterior disponível "
                "nesta conversa para conferir essa menção.")
    texto = " ".join(normalizar_termos(resposta_anterior))
    citado = (" " + tema + " ") in (" " + texto + " ")
    if citado:
        return ("contexto:mencao",
                "Sim, mencionei esse termo na minha última resposta. "
                "Isso não significa que eu tenha mais detalhes cadastrados.")
    return ("contexto:nao_mencionado",
            "Não encontrei esse termo na minha última resposta. "
            "Posso verificar apenas o texto que acabei de apresentar.")
