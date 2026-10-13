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
  saudar            um cumprimento simples;
  nao_sei           uma recusa a "o que é X?" com X dito pela pessoa.

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
# Só "oi"/"olá": o realizador responde sempre "Oi!", e trocar "boa noite" por "oi" piora (porta v1).
_SAUDACAO = re.compile(r"^(?:oi+|ol[áa])(?:[, ]+(?:crivo|tudo bem))*[!.?]*$", re.I)
MAX_FATOS = 2


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
    if ident in ("social:oi",) and _SAUDACAO.match(fala.strip()):
        return {"ato": "saudar"}
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
    return None
