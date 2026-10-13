"""Memória de nomes da conversa: "meu gato se chama Tupo" → "Qual é o nome do meu gato?".

Antes, o CRIVO respondia a "Meu gato se chama Tupo" com uma reflexão, mas não guardava o
nome: "Qual é o nome do meu gato?" caía em dicas de cuidados com gatos. Esta peça só faz
duas coisas, com frases inteiras e sem rede:

  observar   lê cada fala da pessoa e, quando ela dá um nome a um bicho ou a alguém
             próximo ("meu gato se chama Tupo", "tenho uma irmã chamada Lia",
             "na verdade, meu gato se chama Dano"), grava em `perfil.nomes` — a mesma
             memória que a presença já usa e que a API devolve ao navegador;
  recordar   responde a "qual é o nome do meu gato?" com o nome guardado, ou diz que a
             pessoa ainda não contou.

O nome é sempre o que a pessoa escreveu, com a grafia dela. Frase negada ("meu gato não
se chama"), condicional ("se meu gato se chama"), citação entre aspas ou ficção não
gravam nada. Nada é escrito em disco: só vale para esta conversa (e para a memória que o
navegador guarda, como já acontecia).
"""
import re

from composicao_textual import normalizar

# relação → (artigo possessivo de quem fala, de quem ouve)
RELACOES = {
    "gato": "seu", "gata": "sua", "cachorro": "seu", "cachorra": "sua", "cadela": "sua", "cão": "seu",
    "peixe": "seu", "cavalo": "seu", "égua": "sua", "papagaio": "seu", "passarinho": "seu", "calopsita": "sua",
    "coelho": "seu", "coelha": "sua", "tartaruga": "sua", "hamster": "seu", "pet": "seu",
    "irmão": "seu", "irmã": "sua", "amigo": "seu", "amiga": "sua", "melhor amigo": "seu", "melhor amiga": "sua",
    "vizinho": "seu", "vizinha": "sua", "primo": "seu", "prima": "sua", "tio": "seu", "tia": "sua",
    "avô": "seu", "avó": "sua", "filho": "seu", "filha": "sua", "sobrinho": "seu", "sobrinha": "sua",
    "neto": "seu", "neta": "sua", "namorado": "seu", "namorada": "sua", "marido": "seu", "esposa": "sua",
    "colega": "seu", "chefe": "seu", "professor": "seu", "professora": "sua",
}
_REL = "(?P<rel>" + "|".join(sorted((re.escape(r) for r in RELACOES), key=len, reverse=True)) + ")"
_NOME = r"(?P<nome>[A-ZÀ-Ý][a-zà-ÿ'-]+(?: [A-ZÀ-Ý][a-zà-ÿ'-]+)?)"
_POS = r"(?:meu|minha)"
_FIM = r"\s*[.!]?\s*$"
REGISTRO = [re.compile(p) for p in (
    r"^(?i:(?:o |a )?" + _POS + r" " + _REL + r" (?:se chama|chama|tem o nome de) )" + _NOME + _FIM,
    r"^(?i:o nome d[oa] " + _POS + r" " + _REL + r" é )" + _NOME + _FIM,
    r"^(?i:(?:eu )?tenho (?:um|uma) " + _REL + r" (?:chamad[oa]|que se chama) )" + _NOME + _FIM,
    r"^(?i:(?:quero te apresentar|te apresento|esse é|essa é|este é|esta é) (?:o |a )?" + _POS + r" " + _REL
    + r"[,:]? )" + _NOME + _FIM,
)]
CORRECAO = re.compile(r"^(?i:(?:na verdade|corrigindo|me enganei|errei|correção|ops|desculpa)[,:]?\s+)")
CORRECAO_DIRETA = re.compile(r"^(?i:(?:você errou|errou)[,:]? o nome d[oa] " + _POS + r" " + _REL + r" é )" + _NOME + _FIM)
RECORDAR = re.compile(
    r"^(?:(?:e )?qual (?:é |e )?o nome d[oa]|como (?:é que )?se chama (?:o |a )?|(?:voce |vc )?(?:se )?lembra(?: do nome)? d[oa]"
    r"|(?:voce |vc )?lembra como (?:o |a )?)\s*(?P<pos>meu|minha) (?P<rel>[a-z ]+?)(?: se chama)?(?: mesmo)?$")


def _sem_risco(texto):
    """Fala que não pode gravar nome: citação, negação ou condição."""
    n = normalizar(texto)
    return not (any(c in texto for c in '"“”') or re.search(r"\b(?:nao|nunca|se meu|se minha|caso)\b", n))


def observar(perfil, texto, ficcao=False):
    """Grava o nome dado nesta fala. Devolve o evento ({tipo, rel, nome, antigo}) ou None."""
    if perfil is None or not isinstance(texto, str) or ficcao or len(texto) > 160:
        return None
    original = texto.strip()
    correcao = bool(CORRECAO.match(original))
    corpo = CORRECAO.sub("", original, count=1)
    if not _sem_risco(corpo):
        return None
    m = CORRECAO_DIRETA.match(corpo)
    if m:
        correcao = True
    else:
        m = next((p.match(corpo) for p in REGISTRO if p.match(corpo)), None)
    if not m:
        return None
    rel = m.group("rel").lower()
    if rel not in RELACOES:
        return None
    nome = m.group("nome")
    nomes = getattr(perfil, "nomes", None)
    if nomes is None:
        return None
    antigo = nomes.get(rel)
    nomes[rel] = nome
    tipo = "correcao" if (correcao or antigo) and antigo and antigo != nome else "registro"
    return {"tipo": tipo, "rel": rel, "nome": nome, "antigo": antigo if tipo == "correcao" else None}


def recordar(perfil, texto):
    """'Qual é o nome do meu gato?' → (ident, resposta, evento) ou None."""
    if perfil is None or not isinstance(texto, str):
        return None
    m = RECORDAR.match(normalizar(texto).strip(" ?!."))
    if not m:
        return None
    alvo = m.group("rel").strip()
    # "avô" e "avó" ficam iguais sem acento: o possessivo ("meu"/"minha") desempata.
    quer = "seu" if m.group("pos") == "meu" else "sua"
    opcoes = [r for r in RELACOES if normalizar(r) == alvo]
    rel = next((r for r in opcoes if RELACOES[r] == quer), opcoes[0] if opcoes else None)
    if rel is None:
        return None
    pos = RELACOES[rel]
    nome = (getattr(perfil, "nomes", None) or {}).get(rel)
    if nome is None:
        return ("memoria:nome_desconhecido",
                "Você ainda não me contou o nome d%s %s %s. Como se chama?" % ("o" if pos == "seu" else "a", pos, rel),
                {"tipo": "desconhecido", "rel": rel, "nome": None, "antigo": None})
    return ("memoria:nome", "%s! %s %s se chama %s — foi o que você me contou." % (nome, pos.capitalize(), rel, nome),
            {"tipo": "recordar", "rel": rel, "nome": nome, "antigo": None})
