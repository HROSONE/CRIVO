"""Voz própria do CRIVO: dizer os fatos verificados como numa conversa.

O conteúdo continua vindo do acervo, com fonte. A voz só muda a forma: como
abrir, como ligar uma frase à outra e como fechar (um limite importante ou
a oferta de continuar). Cada escolha é feita por um pequeno modelo treinado
do zero com respostas de um tutor (scripts/treinar_voz.py); nenhuma IA roda
no CRIVO.

A voz é uma espécie do ecossistema regulada pela guarda de fidelidade:
qualquer palavra de conteúdo que não esteja nos fatos do assunto, na
pergunta ou no vocabulário de conversa abaixo descarta a frase, e o CRIVO
volta ao texto de sempre.
"""
import json
import re
import zlib
from pathlib import Path

from gerador_frases import FUNCIONAIS
from linguagem_conversa import normalizar

PASTA = Path(__file__).resolve().parent / "artefatos" / "voz_pt"
VERSAO = "voz-decisoes-v1"

# Palavras de conversa que a voz pode usar sem acrescentar fato: ligam,
# situam ou oferecem continuidade. Nada aqui afirma algo sobre o mundo.
DISCURSO = """
basicamente resumo resumindo ou seja pratica exemplo exemplos detalhe curiosidade curiosamente
vale lembrar lembrando importante quiser posso conto conta contar explico explicar falo falar
mais outro outra outros outras parte ponto ideia jeito forma seja inclusive alias assim antes depois
dois duas caso dela dele deles delas nele nela ali isso esse essa entre dessa desse disso
fica ficam aparece aparecem existe existem mostra mostram tambem quer saber continuar seguir
diferenca diferencas cada principal coisa agora sobre algo junto juntos
essas esses estas estes pode podem vista visto faz fazem alem
"""


def _raizes(texto):
    return {w[:4] for w in re.findall(r"[a-z0-9]+", normalizar(texto))
            if len(w) >= 3 and w not in FUNCIONAIS}


_RAIZES_DISCURSO = _raizes(DISCURSO)


def palavras_inventadas(resposta, fontes):
    """Raízes de conteúdo da resposta que não vêm das fontes (fatos do
    assunto, pergunta, nomes ligados) nem do vocabulário de conversa."""
    permitidas = set(_RAIZES_DISCURSO)
    for f in fontes:
        permitidas |= _raizes(f or "")
    return sorted(_raizes(resposta) - permitidas)


# ----------------------------------------------------------------- forma ---

_FEMININOS = frozenset("lei luz voz paz vez cruz raiz foz noz cor dor flor mulher mae tribo".split())
_MASCULINOS_EM_A = frozenset("dia mapa planeta cometa poeta clima idioma sistema problema tema "
                             "bioma dogma drama poema programa esquema cinema genoma trauma pampa".split())
_ADJETIVOS = frozenset("grande grandes segunda segundo primeira primeiro nova novo novas novos velho velha".split())


def _genero_palavra(palavra):
    """Gênero provável de um substantivo pela terminação."""
    p = normalizar(palavra)
    if p in _FEMININOS:
        return "f"
    if p in _MASCULINOS_EM_A or p.endswith("ma"):
        return "m"
    if p.endswith(("cao", "sao", "giao", "niao", "dade", "tude", "agem", "ise", "ite", "encia", "ancia",
                   "eza", "ura", "ade", "a", "as", "cia", "gem")) or palavra.lower().endswith("ã"):
        return "f"
    return "m"


def _genero_numero(item):
    """(gênero, plural) do nome do assunto. Primeiro, o artigo com que os
    próprios fatos usam o nome (“A evaporação participa…”); senão, a
    terminação da primeira palavra do nome."""
    nome = item["nome"]
    alvo = re.escape(nome.split()[0].lower())
    femininos = {"a", "as", "na", "nas", "da", "das", "pela", "pelas"}
    plurais = {"os", "as", "nos", "nas", "dos", "das", "pelos", "pelas"}
    for f in item["fatos"]:
        m = re.search(r"(?:^|\s)(o|a|os|as|no|na|nos|nas|do|da|dos|das|pelo|pela|pelos|pelas)\s+" + alvo + r"\b",
                      f["texto"].lower())
        if m:
            art = m.group(1)
            return ("f" if art in femininos else "m"), art in plurais
    if item.get("area") == "pessoas":
        # Para pessoas, a própria definição diz: “foi uma física”, “foi um monge”.
        m = re.search(r"(?<!\w)(?:foi|era|é)\s+(um|uma|o|a)\b", item["fatos"][0]["texto"])
        if m:
            return ("f" if m.group(1) in ("uma", "a") else "m"), False
    palavras = nome.split()
    nucleo = next((p for p in palavras if normalizar(p) not in _ADJETIVOS), palavras[0])
    definicao = normalizar(item["fatos"][0]["texto"])
    plural = bool(re.match(re.escape(normalizar(nome)) + r"\s+(?:sao|foram|eram)\b", definicao)) or (
        normalizar(nucleo).endswith("s") and not normalizar(nucleo).endswith(("is", "us", "es")))
    singular = nucleo
    if plural:
        n = normalizar(nucleo)
        singular = (nucleo[:-3] + "ão") if n.endswith("oes") else nucleo[:-1] if n.endswith("s") else nucleo
    genero = _genero_palavra(singular)
    # “gigante vermelha”, “anã branca”: o adjetivo concorda e desfaz a dúvida.
    if len(palavras) > 1 and normalizar(nucleo).endswith("e") and normalizar(palavras[1]).endswith("a"):
        genero = "f"
    return genero, plural

def _artigo(item, pergunta):
    """Artigo do nome: o que a pessoa usou na pergunta, senão pelo gênero da
    definição e pelo número do próprio nome (“os neutrinos”, “o neutrino”)."""
    nome = normalizar(item["nome"])
    m = re.search(r"\b(o|a|os|as)\s+" + re.escape(nome) + r"\b", normalizar(pergunta))
    if m:
        return m.group(1)
    genero, plural = _genero_numero(item)
    return {("m", False): "o", ("f", False): "a", ("m", True): "os", ("f", True): "as"}[(genero, plural)]


def _sem_artigo(item, pergunta, textos):
    """Nomes de pessoas e nomes próprios sem artigo na pergunta: “sobre
    Albert Einstein”, não “sobre o Albert Einstein”."""
    if _nome_com_artigo_na_pergunta(item, pergunta):
        return False
    return item["nome"][:1].isupper() and item.get("area") in ("pessoas", "astronomia", "literatura")


def _proprio(palavra, textos):
    """Nome próprio ou sigla: não vira minúscula depois de um conectivo."""
    if not palavra or not palavra[0].isupper():
        return False
    if (len(palavra) > 1 and palavra.isupper()) or re.search(r"\d", palavra):
        return True
    padrao = re.compile(r"[^.!?\s]\s+" + re.escape(palavra) + r"\b")
    return any(padrao.search(t) for t in textos)


def _minuscula(frase, textos):
    primeira = frase.split(" ", 1)[0].strip(",.;:")
    if _proprio(primeira, textos):
        return frase
    return frase[:1].lower() + frase[1:]


_VERBO_INICIAL = re.compile(r"^(?:[a-z]+(?:ou|eu|iu|ava|ia|aram|eram|iram|am|em)|"
                            r"foi|era|tem|teve|fez|pintou|ficou|recebeu|inclui|reune|busca|ocupa|"
                            r"narra|serve|defendia|valorizava|liderados|terminou|comecou|fundou)$")


_IMPESSOAIS = frozenset("existe existem ha houve havia predomina predominam restam resta faltam falta".split())


def _comeca_com_verbo(frase):
    primeira = normalizar(frase.split(" ", 1)[0])
    return bool(_VERBO_INICIAL.match(primeira)) and primeira not in _IMPESSOAIS and primeira not in (
        "nem", "em", "sem", "quem", "tambem", "porem", "alem", "bem", "ninguem", "alguem", "cem")


def _verbo_plural(frase):
    primeira = normalizar(frase.split(" ", 1)[0])
    return primeira.endswith(("am", "em", "ram")) and primeira not in ("tem", "fazem")


def _comeca_sem_sujeito(frase, item):
    """Definição que começa direto pelo núcleo: “Nuvem de gás…”."""
    nome = normalizar(item["nome"])
    n = normalizar(frase)
    return not n.startswith(nome) and not re.match(r"(?:o|a|os|as|um|uma|em)\s", n) and \
        not re.search(r"(?<!\w)(?:é|foi|são|foram|era)(?!\w)", frase.lower().split(",")[0])


def _pronome(item):
    genero, plural = _genero_numero(item)
    return {("m", False): "Ele", ("f", False): "Ela", ("m", True): "Eles", ("f", True): "Elas"}[(genero, plural)]


def _nome_com_artigo_na_pergunta(item, pergunta):
    return bool(re.search(r"\b(?:o|a|os|as)\s+" + re.escape(normalizar(item["nome"])) + r"\b",
                          normalizar(pergunta)))


def _opcoes_abertura(frase, item, pergunta, textos, papel=None):
    opcoes = ["fato"]
    nome = item["nome"]
    if frase.startswith(nome) and (_nome_com_artigo_na_pergunta(item, pergunta)
                                   or not _sem_artigo(item, pergunta, textos)):
        opcoes.append("artigo")
    # Só a definição pode ganhar sujeito: “Nuvem de gás…” → “Uma nebulosa é
    # uma nuvem de gás…”. Um fato de aspecto não é definição do assunto.
    if papel == "definicao" and _comeca_sem_sujeito(frase, item):
        opcoes += ["sujeito", "sujeito_definido"]
    return opcoes


def _aplicar_abertura(frase, item, pergunta, escolha, textos):
    nome = item["nome"]
    if escolha == "artigo":
        return _artigo(item, pergunta).capitalize() + " " + nome + frase[len(nome):]
    if escolha in ("sujeito", "sujeito_definido"):
        genero, plural = _genero_numero(item)
        definido = escolha == "sujeito_definido"
        if plural:
            art = "Os" if genero == "m" else "As"
        elif definido:
            art = "O" if genero == "m" else "A"
        else:
            art = "Um" if genero == "m" else "Uma"
        verbo = "são" if plural else "é"
        nucleo = _minuscula(frase, textos)
        masc = _genero_palavra(nucleo.split()[0]) == "m"
        if plural:
            det = ""
        elif definido:
            det = "o " if masc else "a "
        else:
            det = "um " if masc else "uma "
        if re.match(r"(?:um|uma|o|a)\s", normalizar(nucleo)):
            det = ""
        return art + " " + nome + " " + verbo + " " + det + nucleo
    return frase


def _opcoes_conectivo(frase, papel, item):
    opcoes = ["nada", "pratica"]
    if item.get("area") in ("historia", "pessoas"):
        opcoes += ["depois", "antes"]
    if _comeca_com_verbo(frase) and _verbo_plural(frase) == _genero_numero(item)[1]:
        opcoes.append("pronome")
    if papel == "exemplo" or re.search(r"\b(?:como|exemplo|exemplos)\b", normalizar(frase)) or "'" in frase:
        opcoes.append("exemplo")
    if papel == "limite":
        opcoes.append("lembrar")
    return opcoes


_PREFIXOS = {"exemplo": "Por exemplo, ", "pratica": "Na prática, ", "depois": "Depois, ",
             "antes": "Antes disso, ", "lembrar": "Vale lembrar que "}


def _aplicar_conectivo(frase, item, escolha, textos):
    if escolha == "pronome":
        return _pronome(item) + " " + _minuscula(frase, textos)
    prefixo = _PREFIXOS.get(escolha)
    if prefixo is None:
        return frase
    return prefixo + _minuscula(frase, textos)


def _limite_nao_mostrado(item, mostrados):
    for i, f in enumerate(item["fatos"]):
        if i not in mostrados and f.get("papel") == "limite":
            return i
    return None


def _ha_mais(item, mostrados):
    return any(i not in mostrados and f.get("papel") != "limite" for i, f in enumerate(item["fatos"]))


def _opcoes_fecho(item, mostrados, pergunta=""):
    opcoes = ["nada"]
    # Um limite geral (“não tem superfície sólida”) não responde a um aspecto
    # pedido (“como se formou?”); ali, só a oferta de continuar.
    aspecto = re.search(r"\b(?:como|para que|por que|porque|quando|onde)\b", normalizar(pergunta))
    if _limite_nao_mostrado(item, mostrados) is not None and not aspecto:
        opcoes.append("limite")
    if _ha_mais(item, mostrados):
        opcoes.append("oferta")
    return opcoes


def _aplicar_fecho(item, pergunta, mostrados, escolha, textos):
    if escolha == "limite":
        frase = item["fatos"][_limite_nao_mostrado(item, mostrados)]["texto"]
        return "Vale lembrar que " + _minuscula(frase, textos)
    if escolha == "oferta":
        nome = item["nome"]
        return ("Se quiser, conto mais sobre " + ("" if _sem_artigo(item, pergunta, textos)
                                                  else _artigo(item, pergunta) + " ") + nome + ".")
    return None


# ------------------------------------------------------------ decisões ---

def _hash(texto, dimensao):
    return zlib.crc32(texto.encode("utf-8")) % dimensao


def _forma_pergunta(pergunta):
    n = normalizar(pergunta)
    for chave, padrao in (("quem", r"^quem\b"), ("o_que_foi", r"^o que (?:foi|foram)\b"),
                          ("o_que", r"^o que\b"), ("explica", r"\bexplica"), ("fala", r"\b(?:fala|conta)\b")):
        if re.search(padrao, n):
            return chave
    return "outra"


def caracteristicas(tipo, contexto):
    """Características textuais de um ponto de decisão (abertura, conectivo
    ou fecho). Viram índices com hash para o modelo."""
    feats = ["t=" + tipo, "q=" + contexto["forma"], "area=" + contexto.get("area", "")]
    frase = contexto.get("frase")
    if frase:
        n = normalizar(frase)
        palavras = re.findall(r"[a-z0-9]+", n)
        if palavras:
            feats += ["w0=" + palavras[0], "suf0=" + palavras[0][-3:]]
            if len(palavras) > 1:
                feats.append("w01=" + palavras[0] + "_" + palavras[1])
        feats += ["papel=" + str(contexto.get("papel")), "pos=" + str(min(contexto.get("pos", 0), 3))]
        if _comeca_com_verbo(frase):
            feats.append("verbo_inicial")
        for marca, padrao in (("como", r"\bcomo\b"), ("exemplo", r"\bexemplo"), ("num", r"\d"),
                              ("ele", r"^(?:ele|ela|eles|elas)\b"), ("prep", r"^(?:em|na|no|nos|nas|durante|com)\b")):
            if re.search(padrao, n):
                feats.append("tem_" + marca)
        if ";" in frase:
            feats.append("tem_pontovirg")
    if contexto.get("nome"):
        feats.append("nome0=" + normalizar(contexto["nome"]).split()[0])
    for chave in ("ha_limite", "ha_mais", "sem_sujeito", "nome_inicio", "artigo_pergunta"):
        if contexto.get(chave):
            feats.append(chave)
    feats.append("n=" + str(min(contexto.get("n", 0), 4)))
    return feats


class ModeloDecisoes:
    """Softmax linear por tipo de decisão sobre características com hash."""

    def __init__(self, pasta=PASTA):
        self.ativo = False
        self.motivo = ""
        try:
            meta = json.loads((Path(pasta) / "meta.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            self.motivo = "pesos ausentes: %s" % exc
            return
        if meta.get("versao") != VERSAO or not meta.get("controle", {}).get("aprovado"):
            self.motivo = "pesos não aprovados no controle de qualidade"
            return
        self.dimensao = meta["dimensao"]
        self.pesos = meta["pesos"]  # {tipo: {opcao: {indice: peso, "b": viés}}}
        self.meta = meta
        self.ativo = True

    def pontuar(self, tipo, contexto, opcao):
        idx = [str(_hash(f, self.dimensao)) for f in caracteristicas(tipo, contexto)]
        w = self.pesos.get(tipo, {}).get(opcao, {})
        return sum(w.get(i, 0.0) for i in idx) + w.get("b", 0.0)

    def escolher(self, tipo, contexto, opcoes):
        if len(opcoes) == 1:
            return opcoes[0]
        return max(opcoes, key=lambda o: self.pontuar(tipo, contexto, o))


_MODELO = []


def modelo():
    if not _MODELO:
        _MODELO.append(ModeloDecisoes())
    return _MODELO[0]


# ------------------------------------------------------------- realizar ---

def pontos_de_decisao(pergunta, item, mostrados):
    """Sequência de (tipo, contexto, opções) para um assunto e fatos mostrados."""
    textos = [f["texto"] for f in item["fatos"]] + [item["nome"]]
    base = {"forma": _forma_pergunta(pergunta), "area": item.get("area", ""), "n": len(mostrados),
            "ha_limite": _limite_nao_mostrado(item, mostrados) is not None,
            "ha_mais": _ha_mais(item, mostrados),
            "artigo_pergunta": _nome_com_artigo_na_pergunta(item, pergunta)}
    primeira = item["fatos"][mostrados[0]]["texto"]
    ctx = dict(base, frase=primeira, papel=item["fatos"][mostrados[0]].get("papel"), pos=0,
               sem_sujeito=_comeca_sem_sujeito(primeira, item), nome_inicio=primeira.startswith(item["nome"]),
               nome=item["nome"])
    pontos = [("abertura", ctx, _opcoes_abertura(primeira, item, pergunta, textos,
                                                  item["fatos"][mostrados[0]].get("papel")))]
    for pos, i in enumerate(mostrados[1:], start=1):
        f = item["fatos"][i]
        pontos.append(("conectivo", dict(base, frase=f["texto"], papel=f.get("papel"), pos=pos),
                       _opcoes_conectivo(f["texto"], f.get("papel"), item)))
    pontos.append(("fecho", dict(base), _opcoes_fecho(item, mostrados, pergunta)))
    return pontos, textos


def montar(pergunta, item, mostrados, escolhas):
    """Texto a partir de uma escolha por ponto de decisão."""
    textos = [f["texto"] for f in item["fatos"]] + [item["nome"]]
    frases = [_aplicar_abertura(item["fatos"][mostrados[0]]["texto"], item, pergunta, escolhas[0], textos)]
    for k, i in enumerate(mostrados[1:], start=1):
        frases.append(_aplicar_conectivo(item["fatos"][i]["texto"], item, escolhas[k], textos))
    fecho = _aplicar_fecho(item, pergunta, mostrados, escolhas[-1], textos)
    if fecho:
        frases.append(fecho)
    return " ".join(frases)


def realizar(pergunta, item, mostrados, decisor=None):
    """Resposta na voz própria, ou None se o modelo estiver desligado ou a
    guarda de fidelidade recusar."""
    decisor = decisor or modelo()
    if not decisor.ativo or not mostrados:
        return None
    pontos, textos = pontos_de_decisao(pergunta, item, mostrados)
    escolhas = [decisor.escolher(tipo, ctx, opcoes) for tipo, ctx, opcoes in pontos]
    resposta = montar(pergunta, item, mostrados, escolhas)
    if palavras_inventadas(resposta, [pergunta] + textos + item.get("aliases", [])):
        return None
    return resposta
