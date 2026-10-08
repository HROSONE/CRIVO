"""Confere campos explícitos antes de oferecer uma aproximação neural.

Um ano de nascimento não responde a uma quantidade; citar uma pessoa não
atribui a ela a autoria. Este verificador não escolhe fatos nem cria valores.
Se o campo pedido não tem suporte explícito, mantém a recusa.
"""
import re
import unicodedata

from composicao_textual import normalizar

_NUMERO = r"(?:\d[\d.,]*|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|dezenas|centenas)"
_ESCALA = r"(?:\s+(?:mil|milhao|milhoes|bilhao|bilhoes)(?:\s+de)?)?"
_NOME = r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ú-]+"
_AUTORIA = re.compile(
    r"\b(?:autor\w*|escrit\w*|escrev\w*|escrito por|comp[oô]s|compositor\w*|pintou)\b|"
    r"\b(?:romance|livro|obra|conto|poema|peca|pintura|quadro|escultura)\s+(?:de|do|da)\s+\w")
_CRIACAO = re.compile(r"\b(?:criou|criad[oa]s?|criador[ae]s?|criacao|inventou|inventad[oa]s?|inventor[ae]s?|"
                       r"fundou|fundad[oa]s?|fundador[ae]s?|fundacao|propos|formulou|formulad[oa]s?|"
                       r"desenvolveu|desenvolvid[oa]s?)\b")
_DESCOBERTA = re.compile(r"\b(?:descobriu|descobert[oa]s?|identificou|identificad[oa]s?|detectou|detectad[oa]s?)\b")
_LOCAL = re.compile(r"\b(?:em|no|na|nos|nas|do|da|de)\s+" + _NOME)


def _medida(texto, unidade):
    return bool(re.search(r"\b" + _NUMERO + _ESCALA + r"\s*" + unidade, texto))


def verificar_campo(pergunta, fato, tracos, area=None):
    """Nome do campo verificado, ou None. Usa o texto cadastrado inteiro."""
    q = normalizar(pergunta)
    # A normalização lexical remove /, °, ^ e símbolos monetários. Aqui esses
    # sinais são parte da unidade: 12 km/h não é uma medida de comprimento.
    f = " ".join("".join(c for c in unicodedata.normalize("NFD", fato.lower())
                         if unicodedata.category(c) != "Mn").split())
    if re.search(r"\bquem\s+(?:escrev\w*|pint\w*|compo\w*)\b|\b(?:autor|autora|autoria)\b", q):
        return "autoria" if _AUTORIA.search(f) else None
    if re.search(r"\bquem\s+(?:cri\w*|invent\w*|fund\w*|propos|formul\w*|desenvolv\w*)\b", q):
        return "criacao" if _CRIACAO.search(f) else None
    if re.search(r"\bquem\s+(?:descobr\w*|identific\w*|detect\w*)\b", q):
        return "descoberta" if _DESCOBERTA.search(f) else None
    if re.search(r"\b(?:de que pais|qual\s+(?:e\s+)?a nacionalidade|de onde\s+\w*\s*era)\b", q):
        # A origem de um planeta não é uma nacionalidade. O assunto precisa
        # ser uma pessoa e o fato precisa trazer origem ou nacionalidade.
        origem = re.search(r"\b(?:origem|nasc\w*|natural\w*|nacionalidade)\b", f)
        nacionalidade = re.search(r"\b(?:brasileir|portugues|frances|francesa|polones|polonesa|alemao|alema|"
                                  r"ingles|inglesa|grego|grega|italian|espanhol|estadunidense|american|"
                                  r"argentino|argentina|japones|japonesa|chines|chinesa)\w*\b", f)
        return "origem_pessoa" if area == "pessoas" and (nacionalidade or origem and _LOCAL.search(fato)) else None
    if re.search(r"\b(?:onde|em que (?:pais|cidade|lugar|regiao))\b", q):
        if not _LOCAL.search(fato):
            return None
        if re.search(r"\bnasc\w*\b", q):
            return "nascimento_local" if re.search(r"\bnasc\w*\b", f) else None
        if re.search(r"\b(?:mor\w*|viv\w*|resid\w*)\b", q):
            return "residencia" if re.search(r"\b(?:mor\w*|viv\w*|resid\w*)\b", f) else None
        if re.search(r"\b(?:fic\w*|localiz\w*|situad\w*)\b", q):
            return "localizacao" if re.search(r"\b(?:fic\w*|localiz\w*|situad\w*)\b", f) else None
        return "pistas" if tracos.get("todas") else None
    if re.search(r"\b(?:composicao|constituicao|composto|composta|feito|feita)\b", q):
        return "composicao" if re.search(r"\b(?:compost\w*|constitui\w*|formad[oa]s?\s+por|feit[oa]s?\s+de)\b", f) else None
    if re.search(r"\b(?:nome|chama|chamam|chamava|denominad\w*)\b", q):
        # Nome precisa de uma atribuição, ou de objeto + nome próprio, como
        # "o navio Beagle". Só um nome de pessoa no texto é insuficiente.
        if re.search(r"\b(?:chamad\w*|denominad\w*|nome|conhecid\w*\s+como)\b", f):
            return "nome" if tracos.get("todas") or tracos.get("relacao", 0.0) > 0.0 else None
        for objeto, padrao in (("embarcacao", "(?:navio|barco|embarcação)"),
                               ("navio", "navio"), ("barco", "(?:navio|barco)")):
            if objeto in q and re.search(r"\b" + padrao + r"\s+" + _NOME, fato):
                return "nome_objeto"
        return None
    medidas = (
        (r"\b(?:quanto tempo|duracao|dura\w*|demora\w*)\b", r"(?:segundos?|minutos?|horas?|dias?|semanas?|meses|anos?|seculos?)\b", "duracao"),
        (r"\btemperatur\w*\b", r"(?:°\s*[cf]|kelvins?|k\b|graus\b)", "temperatura"),
        (r"\b(?:massa|peso)\b", r"(?:kg\b|g\b|gramas?|quilogramas?|toneladas?)\b", "massa"),
        (r"\bvelocidade\b", r"(?:km/h|m/s|quilometros por hora|metros por segundo)\b", "velocidade"),
        (r"\b(?:distancia|altura|largura|comprimento|diametro)\b",
         r"(?:km|m|cm|metros?|quilometros?|anos[- ]luz)\b(?!\s*(?:/|\^|[23²³]|quadrad\w*|cubic\w*|por\b))",
         "comprimento"),
        (r"\bpopulacao\b", r"(?:habitantes?|pessoas?)\b", "populacao"),
    )
    for pergunta_medida, unidade, campo in medidas:
        if re.search(pergunta_medida, q):
            return campo if _medida(f, unidade) else None
    if re.search(r"\b(?:quanto custa|preco|custo)\b", q):
        moeda = _medida(f, r"(?:reais|real|dolares|euros)\b") or re.search(r"(?:r\$|us\$|€)\s*\d", f)
        return "preco" if moeda else None
    m = re.search(r"\bquant[oa]s?\s+([a-z]+)\b", q)
    if m:
        unidade = m.group(1)
        # Contagem liga o número ao objeto contado. "1881" em uma frase que
        # menciona um livro não é a quantidade de capítulos desse livro.
        raiz = unidade[:-1] if unidade.endswith("s") else unidade
        return "contagem" if _medida(f, re.escape(raiz) + r"\w*\b") else None
    # Fora dos campos explicitamente verificáveis, cada pista precisa estar
    # apoiada. O leitor não autoriza um detalhe ausente só pela confiança.
    return "pistas" if tracos.get("todas") else None
