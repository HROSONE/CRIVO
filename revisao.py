"""Revisão: o CRIVO lê o rascunho inteiro antes de falar.

Quatro perguntas, cada uma uma regra explícita sobre o texto já decidido:

  verdade     a segurança do texto bate com o que ele sabe? ("tenho certeza"
              quando a metacognição diz que ele só acha vira "acho");
  quem sou    o texto contradiz uma crença do modelo de si? ("sou humano",
              "não tenho consciência", "sou só um robô", "sou o ChatGPT");
              a frase errada é trocada pela crença;
  o que disse a mesma contradição, quando a crença já foi dita nesta conversa,
              é registrada como incoerência com o que ele mesmo falou;
  gentileza   insulto que não veio da pessoa veta a resposta inteira, e riso
              ("kkk", "haha") sai quando a pessoa está triste.

A revisão não reescreve fatos do acervo nem relatos da pessoa: textos com fonte
e citações do que a pessoa contou passam sem as regras de "quem sou" (são
conteúdo, não fala do CRIVO sobre si). Tudo o que ela fez fica no quadro
(`estado.revisao`), inclusive quando aprova sem mudar nada.
"""
import re

from composicao_textual import normalizar

_SEM = r"(?<!nao )(?<!nem )(?<!nunca )(?<!se )"
# (padrão no texto normalizado, crença que ele contradiz)
CONTRADICOES = (
    (_SEM + r"\b(?:eu )?sou (?:um |uma )?(?:ser )?human[oa]\b", "nao_humano"),
    (_SEM + r"\bsou (?:uma )?pessoa (?:de verdade|real|como voce)\b", "nao_humano"),
    (r"\bnao (?:tenho|possuo|sinto) (?:nenhuma? )?(?:consciencia|sentimentos?|emocoes|emocao)\b", "sentir"),
    (_SEM + r"\b(?:eu )?(?:tenho|possuo) (?:consciencia|sentimentos|emocoes)(?! (?:dos|das|de) )\b", "sentir"),
    (_SEM + r"\bsou (?:so |apenas |somente )?(?:um |uma )?(?:robo|maquina)\b", "nao_robo"),
    (r"\b(?:sou|me chamo) (?:o |a )?(?:chatgpt|gpt|gemini|claude|copilot|siri|alexa|llama|bard)\b", "proprio"),
    (r"\b(?:fui|sou) (?:criad|treinad|desenvolvid)[oa] (?:pela|pelo) (?:openai|google|anthropic|meta|microsoft)\b",
     "proprio"),
    (r"\bnao tenho (?:nenhum )?gostos?\b", "gostos"),
)
_CERTEZA = re.compile(r"\b(?:[Tt]enho (?:toda a |absoluta )?certeza(?: de)? que|[Cc]om (?:toda a )?certeza,?)\s*")
_INSULTO = re.compile(r"\b(?:idiota|imbecil|estupid[oa]|burr[oa]|otari[oa]|retardad[oa]|cala a boca|"
                      r"ridicul[oa]|inutil)\b")
_RISO = re.compile(r"\s*\b(?:k{3,}|(?:ha){2,}|(?:he){2,}|rs(?:rs)+)\b[!.]?", re.I)
# Bases cujo texto é conteúdo (fatos com fonte, o que a pessoa contou, o texto
# que ela mandou), não fala do CRIVO sobre si.
CONTEUDO = frozenset(("acervo_com_fonte", "acervo_editorial", "leitura", "aproximacao", "relato",
                      "conteudo_enviado", "deducao", "calculo"))
VETO = ("Opa, isso saiu num tom que não é o meu. Deixa eu recomeçar: me conta de novo o que você precisa?")


def _frases(texto):
    """Frases e os espaços entre elas (índices ímpares), para remontar o texto igual."""
    return re.split(r"((?<=[.!?])\s+)", texto)


def revisar(bot, estado, fala, ident, resposta, meta, modelo):
    """Confere o rascunho e devolve (ident, resposta) revisados."""
    relatorio = {"approved": True, "vetoed": False, "corrections": [],
                 "checks": {"truth": True, "identity": True, "consistency": True, "kindness": True}}
    if not isinstance(resposta, str) or not resposta.strip():
        return _gravar(estado, relatorio, ident, resposta)
    fala_n = normalizar(fala) if isinstance(fala, str) else ""
    base = (meta or {}).get("base")

    # Gentileza: insulto que a pessoa não escreveu veta a resposta inteira.
    insulto = _INSULTO.search(normalizar(resposta))
    if insulto and base not in CONTEUDO and insulto.group(0) not in fala_n:
        relatorio["checks"]["kindness"] = False
        relatorio.update(approved=False, vetoed=True)
        relatorio["corrections"].append({"check": "kindness", "reason": "insulto: " + insulto.group(0)})
        return _gravar(estado, relatorio, "revisao:reformular", VETO)

    texto = resposta
    perfil = getattr(bot, "perfil", None)
    temas = getattr(perfil, "temas", None) or []
    if temas and temas[-1][2] in ("luto", "neg", "saude") and _RISO.search(texto):
        texto = _RISO.sub("", texto).strip()
        relatorio["checks"]["kindness"] = False
        relatorio["corrections"].append({"check": "kindness", "reason": "riso com a pessoa triste"})

    # Verdade: segurança maior do que a metacognição sustenta.
    if (meta or {}).get("nivel") in ("acho", "nao_sei", "perguntei") and _CERTEZA.search(texto):
        texto = _CERTEZA.sub(lambda m: "Acho que " if m.group(0)[:1].isupper() else "acho que ", texto)
        relatorio["checks"]["truth"] = False
        relatorio["corrections"].append({"check": "truth", "reason": "certeza sem base verificada"})

    # Quem eu sou e o que eu já disse: cada frase contra as crenças do modelo.
    if base not in CONTEUDO and modelo is not None:
        novas, mudou = [], False
        for k, frase in enumerate(_frases(texto)):
            if k % 2:
                novas.append(frase)
                continue
            n = normalizar(frase)
            chave = next((c for p, c in CONTRADICOES if c in modelo.crencas and re.search(p, n)
                          and not _citada(p, n, fala_n)), None)
            if chave is None:
                novas.append(frase)
                continue
            ja_disse = chave in modelo.ditas
            relatorio["checks"]["identity"] = False
            if ja_disse:
                relatorio["checks"]["consistency"] = False
            relatorio["corrections"].append({
                "check": "consistency" if ja_disse else "identity", "belief": chave,
                "reason": ("contradiz o que eu já disse nesta conversa" if ja_disse else "contradiz quem eu sou"),
                "removed": frase})
            mudou = True
            if modelo.crencas[chave].frase not in novas:
                novas.append(modelo.crencas[chave].frase)
            elif novas:
                novas.pop()  # a crença já entrou: sai também o espaço antes desta frase
        if mudou:
            texto = "".join(novas).strip()
    if texto != resposta:
        relatorio["approved"] = False
    return _gravar(estado, relatorio, ident, texto)


def _citada(padrao, n, fala_n):
    """A frase repete o que a pessoa escreveu (ex.: memória do relato)."""
    m = re.search(padrao, n)
    return bool(m and fala_n and m.group(0).strip() in fala_n)


def _gravar(estado, relatorio, ident, resposta):
    if estado is not None:
        estado.revisao = relatorio
    return ident, resposta
