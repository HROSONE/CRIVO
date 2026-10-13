"""Metacognição: quanto o CRIVO sabe do que acabou de dizer, e como sabe.

Depois de cada turno, olha quem respondeu (a espécie no quadro), a decisão do
árbitro e a evidência que havia (ficha com fonte, leitura com probabilidade,
noção geral, cálculo, relato da pessoa, recusa) e grava no quadro:

  nivel       "sei", "acho", "nao_sei" ou "perguntei";
  base        de onde veio a resposta;
  confianca   a probabilidade medida, quando a espécie mede uma (leitura da
              ficha e busca aprendida); nas demais fica None — não se inventa
              número sem medida;
  escolha     responder, perguntar ou admitir que não sabe;
  explicacao  como ele sabe, em primeira pessoa.

Com isso o CRIVO responde a "tem certeza?", "como você sabe disso?" e "por que
você respondeu isso?" sobre a própria resposta anterior, sem reabrir a
pergunta. O nível é uma regra explícita sobre o mecanismo e a evidência; não é
uma probabilidade calibrada de acerto.
"""
import re

from composicao_textual import normalizar

RECUSAS = frozenset(("fora", "social:nao_entendido", "vazio"))
PERGUNTAS = frozenset(("duvida", "conversa:esclarecer", "contexto:sem_referencia"))
_RECUSA_TEXTO = re.compile(r"^(?:nao tenho|ainda nao|nao sei|nao reconheci|nao consegui|nao encontrei|"
                           r"hum nao entendi|reconheci o assunto)")

_INTROSPECCAO = (
    ("certeza", r"(?:(?:voce )?tem (?:certeza|ctz)(?: (?:disso|do que (?:voce )?(?:disse|falou)|absoluta))?|"
                r"certeza mesmo|(?:voce )?(?:ta|esta) (?:certo|segur[oa])(?: disso)?|(?:isso )?(?:e|eh) verdade(?: mesmo)?|"
                r"(?:voce )?(?:ta|esta) (?:chutando|inventando)|(?:voce )?inventou (?:isso|essa)|"
                r"(?:voce )?(?:confia|acredita) nisso|(?:o )?quanto voce confia (?:nisso|nessa resposta)|"
                r"(?:voce )?sabe (?:mesmo|disso mesmo)|serio mesmo)"),
    ("como_sabe", r"(?:como (?:e que )?voce sabe(?: (?:disso|isso))?|como voce (?:soube|descobriu)(?: isso)?|"
                  r"(?:de onde|da onde) (?:veio|vem) (?:isso|essa resposta))"),
    ("por_que", r"(?:por ?que voce (?:respondeu|disse|falou) (?:isso|assim|desse jeito)|"
                r"como voce chegou (?:nisso|nessa resposta|a essa resposta)|o que voce pensou (?:pra|para) responder)"),
)


def _assuntos(bot):
    ctx = getattr(bot, "contexto_textual", None)
    if ctx is None or not getattr(ctx, "exibidos", None):
        return []
    nomes = []
    for e, _ in ctx.exibidos:
        nome = bot.compositor.itens.get(e, {}).get("nome")
        if nome and nome not in nomes:
            nomes.append(nome)
    return nomes


def avaliar(bot, estado, fala, ident, resposta):
    """Metacognição do turno que acabou de ser decidido."""
    registro = bot.historico[-1] if getattr(bot, "historico", None) else {}
    if registro.get("pergunta") not in (fala, getattr(estado, "fala", None)):
        registro = {}
    decisao = getattr(estado, "decisao", None) or {}
    mecanismo = registro.get("mecanismo") or decisao.get("especie")
    leitura = registro.get("leitura") or {}
    assuntos = _assuntos(bot)
    n = normalizar(resposta or "")
    geracao = getattr(bot, "ultima_geracao", None) or {}
    meta = {"nivel": "acho", "base": "sem_fonte", "confianca": None, "escolha": "responder",
            "assuntos": assuntos, "mecanismo": mecanismo,
            "motivo": decisao.get("motivo")}

    def definir(nivel, base, explicacao, escolha="responder", confianca=None):
        meta.update(nivel=nivel, base=base, explicacao=explicacao, escolha=escolha, confianca=confianca)
        return meta

    ficha = " e ".join(assuntos)
    if ident in RECUSAS or _RECUSA_TEXTO.match(n) and not ident.startswith(("si:", "metacognicao:")):
        return definir("nao_sei", "sem_evidencia",
                       "Eu não tinha evidência no que sei para responder isso, então preferi dizer que não sei.",
                       "admitir")
    if ident in PERGUNTAS or ident.startswith("esclarecimento") or mecanismo == "compreensao_neural":
        return definir("perguntei", "ambiguo",
                       "Eu não tinha certeza do que você queria, então perguntei antes de responder.", "perguntar")
    if ident == "leitura:aproximacao":
        return definir("acho", "aproximacao",
                       "Não achei a resposta exata. Mostrei o fato mais próximo que encontrei na ficha sobre %s."
                       % (ficha or "um assunto vizinho"), confianca=leitura.get("probability"))
    if ident.startswith("metacognicao:"):
        return definir("sei", "introspeccao", "Olhei para a minha própria resposta anterior e para o que "
                                              "ficou registrado no meu quadro.")
    if ident.startswith("si:") or mecanismo in ("modelo_de_si", "conversa_assistente") and ident.startswith("social:"):
        return definir("sei", "identidade", "Isso é sobre mim: vem de quem eu sou, da minha identidade, "
                                            "não do acervo de fatos.")
    if ident.startswith(("calculo:", "conversa:raciocinio")) or mecanismo == "raciocinio_conversa_verificavel":
        return definir("sei", "calculo", "Eu calculei a partir dos números que você me deu; dá para refazer a conta.")
    if ident.startswith("logica:") or mecanismo in ("raciocinio_relacional", "raciocinio_ativo", "raciocinio_e_base"):
        return definir("sei", "deducao", "Deduzi isso de relações registradas no meu conhecimento; "
                                         "a prova pode ser mostrada.")
    if ident.startswith(("memoria:", "conversa:memoria", "conversa:sessao")) or (mecanismo or "").startswith(
            ("memoria_", "conversa_sessao")):
        return definir("sei", "relato", "Isso foi o que você me contou nesta conversa. Guardo como relato seu, "
                                        "não como fato do mundo.")
    if ident.startswith("nocao:") or mecanismo == "nocao":
        return definir("acho", "nocao", "É uma noção geral, de senso comum, não um fato verificado com fonte "
                                        "no meu acervo.")
    if geracao.get("usada"):
        return definir("acho", "geracao", "Escrevi essa com a minha geração experimental, presa aos fatos do "
                                          "acervo; vale conferir as fontes.")
    if mecanismo in ("leitura_ficha", "busca_aprendida") and leitura:
        p = leitura.get("probability")
        nivel = "sei" if p is not None and p >= 0.8 else "acho"
        return definir(nivel, "leitura", "Achei isso na ficha sobre %s, que tem fonte, e a minha leitura conferiu que "
                                         "o fato cobre a sua pergunta." % (ficha or leitura.get("subject", "um assunto")),
                       confianca=p)
    if assuntos:
        return definir("sei", "acervo_com_fonte", "Isso vem da ficha sobre %s, no meu acervo, e cada fato ali tem "
                                                  "fonte. Se quiser, pergunte “qual a fonte disso?”." % ficha)
    editoriais = getattr(bot, "_ids_editoriais", None) or ()
    if ident in editoriais:
        return definir("sei", "acervo_editorial", "Isso vem do meu acervo revisado, não de um palpite.")
    if (mecanismo or "").startswith(("analise_conteudo", "correcao_texto")):
        return definir("sei", "conteudo_enviado", "Analisei o texto que você mandou com regras explícitas.")
    if ident.startswith(("social:", "conversa:", "nocao:")):
        return definir("sei", "conversa", "Foi uma resposta de conversa, sobre o que você disse — não uma "
                                          "afirmação sobre o mundo.")
    return definir("acho", "sem_fonte", "Respondi sem uma fonte verificada que eu possa te mostrar.")


def introspectar(n, anterior, modelo=None):
    """Pergunta sobre a própria resposta anterior → (ident, texto) ou None."""
    n = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", n)).strip()
    n = re.sub(r"^(?:crivo|mas|e|hum|ue|hm)\s+|\s+crivo$", "", n)
    tipo = next((t for t, p in _INTROSPECCAO if re.fullmatch(p, n)), None)
    if tipo is None or not anterior:
        return None
    nivel, explicacao = anterior.get("nivel"), anterior.get("explicacao", "")
    if tipo == "por_que":
        motivo = anterior.get("motivo")
        partes = ["Pensei assim: " + explicacao[:1].lower() + explicacao[1:]]
        if anterior.get("escolha") == "perguntar":
            partes.append("Por isso preferi perguntar em vez de arriscar.")
        elif anterior.get("escolha") == "admitir":
            partes.append("Por isso preferi admitir que não sabia em vez de inventar.")
        if motivo:
            partes.append("No meu quadro ficou registrado: “%s”." % motivo)
        return "metacognicao:por_que", " ".join(partes)
    if nivel == "sei":
        abertura = "Tenho, sim. " if tipo == "certeza" else ""
        fecho = (" Mesmo assim posso errar: se você tiver uma fonte que diga outra coisa, me mostra que eu reviso."
                 if anterior.get("base") in ("acervo_com_fonte", "acervo_editorial", "leitura") else "")
        texto = abertura + explicacao + fecho
    elif nivel == "acho":
        p = anterior.get("confianca")
        medida = " A leitura da ficha deu %d%% de confiança." % round(100 * p) if isinstance(p, (int, float)) else ""
        texto = "Não totalmente. " + explicacao + medida + " Se quiser, a gente confere junto."
    elif nivel == "nao_sei":
        texto = "Não — e foi por isso que eu disse que não sabia. " + explicacao
    else:
        texto = "Ainda não: " + explicacao + " Me diz o que você quis perguntar que eu tento de novo."
    return "metacognicao:" + tipo, texto
