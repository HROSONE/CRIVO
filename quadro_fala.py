"""Da decisão do CRIVO ao quadro que o realizador 17M aprendeu a falar (fase 3).

O realizador não decide nada: ele recebe o ato e o conteúdo que o CRIVO já decidiu e diz
isso em português. Esta peça só traduz o turno já respondido para o formato da fase 3
(`experimentos/fase3_realizador_20261012/formato_fase3.py`), e só nos casos em que o
conteúdo está inteiro e verificado:

  explicar          a resposta mostrou fatos de uma ficha (com fonte): os fatos vão
                    literalmente, no máximo dois;
  registrar         a pessoa deu um nome (memoria_nomes): relação e nome;
  recordar          o CRIVO lembrou um nome guardado;
  aceitar_correcao  a pessoa corrigiu um nome guardado;
  acolher           um relato com um sentimento que a fase 3 conhece;
  saudar            um cumprimento simples ("oi", "olá, Crivo", "e aí");
  nao_sei           uma recusa a "o que é X?" com X dito pela pessoa, ou a uma pergunta aberta
                    ("quem inventou o carro?") que o CRIVO não soube responder;
  falar_de_si       perguntas inteiras sobre o que o CRIVO é, nos pontos que a fase 3 treinou;
  esclarecer        um pedido vago ("preciso de uma ajuda", "isso é bom?") que o CRIVO não resolveu.

Qualquer outro turno devolve None e fica com o texto de sempre. Nenhum fato, nome ou
motivo é criado aqui.
"""
import re

from composicao_textual import normalizar

# Relações que o realizador viu no treino da fase 3 (todas no masculino). Fora delas ele
# errou o gênero na porta v1 ("seu irmão se chama Lia"); ficam com o texto de sempre.
RELACOES_TREINADAS = ("cachorro", "gato", "peixe", "papagaio", "cavalo", "coelho", "irmão", "primo", "amigo",
                      "vizinho")
SENTIMENTOS = ("triste", "cansado", "ansioso", "sozinho", "preocupado", "desanimado", "feliz", "animado")
_SENTIMENTO = re.compile(r"\b(?:estou|to|tô|ando|acordei|me sinto|me sentindo|fiquei|hoje estou)\b(?: \w+){0,2}? (?P<s>"
                         + "|".join(SENTIMENTOS) + r")\b")
_O_QUE_E = re.compile(r"^\s*(?:o que (?:é|e)|você conhece|vc conhece|me fala sobre|quem (?:é|foi))\s+(?:o |a |um |uma )?"
                      r"(?P<x>[\wÀ-ÿ][\wÀ-ÿ -]{1,40}?)\s*\??\s*$", re.I)
# Sem período do dia: o realizador responde "Oi!"/"Olá!", e trocar "boa noite" por "oi" piora (porta v1).
_SAUDACAO = re.compile(r"^(?:oi+|ol[áa]|e a[ií]|eae|opa)(?:[, ]+(?:crivo|tudo bem|tudo bom|td bem|beleza))*[!.?]*$",
                       re.I)
MAX_FATOS = 2
# Porta v3: a voz falava em 1 de 18 turnos da conversa real do criador do projeto. Os atos abaixo a
# fase 3 já treinou; só entram em falas inteiras que não deixam dúvida do que se pede.
_SI = (("quem_e", r"(?:quem (?:e|é) (?:voce|vc)|(?:voce|vc) (?:e|é) o qu[eê]|o que (?:voce|vc) (?:e|é))"),
       # Sem "você é uma IA?": o 17M começa com "Não do jeito que você é", resposta de outra pergunta.
       ("ser_ia", r"(?:voce|vc) (?:e|é) (?:humano|uma pessoa|gente)"),
       ("robo", r"(?:voce|vc) (?:e|é) (?:so |apenas )?um robo"),
       ("sentir", r"(?:voce|vc) (?:sente alguma coisa|sente algo|tem sentimentos|tem emocoes|sente emocoes)"))
_VAGO = (("detalhe", r"(?:me ajuda com uma coisa|preciso de (?:uma )?ajuda|tenho uma duvida|posso te perguntar uma coisa)"),
         ("assunto", r"(?:isso (?:e|é) bom|como faz|quanto tempo demora|isso funciona|vale a pena)"))
# Pergunta aberta curta, sem a pessoa nem o CRIVO como assunto e sem saúde ou risco: "não sei"
# com a própria pergunta como assunto ("Sobre quem inventou o carro eu ainda não sei nada").
_ABERTA = re.compile(r"^(?:quem|quando|onde|como|qual|quais|quanto|quantos|quantas|por que)\s+\S.{2,70}$", re.I)
_PESSOAL = re.compile(r"\b(?:eu|me|meu|minha|meus|minhas|voce|vc|tu|te|seu|sua|crivo)\b")
_RISCO = re.compile(r"(?:morr|suic|matar|mata|dor\b|doen|remedi|sangu|gravid|febre|machuc|droga|veneno|arma|"
                    r"socorro|emergenc|hospital|sintoma|infart|avc|overdose)")


def _limpa(fala):
    return re.sub(r"[^\w\s]", " ", normalizar(fala)).split()


def _inteira(padrao, fala):
    return re.fullmatch(padrao, " ".join(_limpa(fala))) is not None


def pergunta_aberta(fala):
    texto = re.sub(r"\s+", " ", fala.strip()).rstrip("?!. ")
    if not _ABERTA.match(texto) or len(texto.split()) > 10 or not 3 <= len(texto.split()):
        return None
    base = " ".join(_limpa(texto))
    if _PESSOAL.search(base) or _RISCO.search(base):
        return None
    return texto[0].lower() + texto[1:]


def quadro_do_turno(bot, fala, ident, resposta):
    """Quadro da fase 3 para este turno, ou None quando o realizador não deve falar."""
    if not isinstance(fala, str) or not isinstance(resposta, str):
        return None
    evento = getattr(bot, "evento_nome", None)
    if evento and evento.get("fala") == fala:
        if evento["rel"] not in RELACOES_TREINADAS:
            return None
        # Quem corrigiu foi a pessoa, não o CRIVO: aceitar_correcao ("desculpa, errei")
        # seria uma culpa falsa (porta v1). A correção é um registro novo.
        if evento["tipo"] in ("registro", "correcao"):
            return {"ato": "registrar", "relacao": evento["rel"], "nome": evento["nome"]}
        if evento["tipo"] == "recordar":
            return {"ato": "recordar", "relacao": evento["rel"], "nome": evento["nome"]}
        return None
    if ident.startswith("crise"):
        return None
    # "Oi, tudo bem?" fica com o texto de sempre: o 17M responde "Oi! Pode chegar…" e ignora o
    # "tudo bem?", que o CRIVO de hoje responde (porta v3).
    if ident == "social:oi" and _SAUDACAO.match(fala.strip()):
        return {"ato": "saudar"}
    for ponto, padrao in _SI:
        if _inteira(padrao, fala):
            return {"ato": "falar_de_si", "ponto": ponto}
    if ident in ("fora", "duvida") or ident.startswith("clima_"):
        for falta, padrao in _VAGO:
            if _inteira(padrao, fala):
                return {"ato": "esclarecer", "falta": falta}
    ctx = getattr(bot, "contexto_textual", None)
    if ctx is not None and getattr(ctx, "exibidos", None) and not ident.startswith(("escrita:", "leitura:")):
        temas = {e for e, _ in ctx.exibidos}
        if len(temas) == 1 and len(ctx.exibidos) <= MAX_FATOS:
            from curriculo_mundo import texto_fato
            assunto = temas.pop()
            item = bot.compositor.itens.get(assunto)
            if item is None or any(item["fatos"][i].get("natureza") == "religioso" for _, i in ctx.exibidos):
                return None
            fatos = [texto_fato(item["fatos"][i]) for _, i in ctx.exibidos]
            # Só quando a resposta é exatamente esses fatos: um aviso ("Vale lembrar que…")
            # ou uma oferta de continuar sumiriam na voz do 17M (porta v1).
            sobra = normalizar(resposta)
            for f in fatos:
                sobra = sobra.replace(normalizar(f), " ")
            if (all(normalizar(f) in normalizar(resposta) for f in fatos) and len(re.findall(r"\w+", sobra)) <= 3
                    and not getattr(bot, "oferta_pendente", None)):
                return {"ato": "explicar", "assunto": item["nome"], "fatos": fatos}
        return None
    if ident == "conversa:relato":
        m = _SENTIMENTO.search(normalizar(fala))
        if m:
            return {"ato": "acolher", "sentimento": m.group("s")}
        return None
    if ident == "fora":
        m = _O_QUE_E.match(fala)
        if m and len(m.group("x").split()) <= 3:
            return {"ato": "nao_sei", "assunto": m.group("x").strip()}
        # O 17M só copia bem um nome próprio de uma palavra (na fase 3 o assunto do "não sei" era
        # sempre um nome). Com "o carro" ou "motor a jato" ele trocava o assunto ("jato") ou se
        # repetia; esses ficam com o texto de sempre.
        pergunta = pergunta_aberta(fala)
        proprios = re.findall(r"(?<!^)\b[A-ZÁÉÍÓÚÂÊÔÃÕ][\wÀ-ÿ]+", pergunta or "")
        if pergunta and len(proprios) == 1:
            return {"ato": "nao_sei", "assunto": proprios[0]}
    return None
