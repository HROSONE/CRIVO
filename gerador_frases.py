"""Gerador de frases com verificador de fidelidade.

O conteúdo de uma resposta é decidido antes (o plano): a reação ao tom, o
que a pessoa contou na voz dela (eco), a causa que ela deu, uma noção e uma
pergunta. Este módulo só decide a forma:

  1. monta várias realizações do mesmo plano (ordem, conectores, eco como
     pergunta, "É, …" antes da noção…);
  2. o verificador descarta qualquer candidata que acrescente palavra de
     conteúdo que não veio da fala, do plano ou do vocabulário de conversa,
     que perca parte do plano, ou que repita reação ("Que legal… Que bom");
  3. o pontuador neural (pontuador_frases) escolhe a que soa mais natural,
     evitando a mesma estrutura da resposta anterior.

Sem pontuador (sem NumPy), fica a primeira candidata válida.
"""
import re
from dataclasses import dataclass, field

from linguagem_conversa import normalizar

# Palavras sem conteúdo: podem aparecer em qualquer realização.
FUNCIONAIS = set("""a o as os um uma uns umas de do da dos das em no na nos nas ao aos à às que e é
    ou se eu tu ele ela eles elas você voce vocês voces seu sua seus suas meu minha meus minhas
    me te lhe nós nos pra para por pelo pela com sem mas mais muito muita bem só so já ja também
    tambem ainda isso isto esse essa este esta aquilo aquele aquela lá la aqui aí ai então entao
    né ne pois porque quando como onde qual quais quem quanto não nao sim tão tao foi ser são sao
    está esta estão estao tem ter era há ha vai vou""".split())
# Conectores que o gerador pode acrescentar sem mudar o conteúdo.
CONECTORES = ("É,", "Pois é,", "E")
_ABERTURA_INICIO = re.compile(
    r"(?:poxa|que (?:chato|pena|bom|legal|otimo|demais|delicia)|puxa|putz|ah, que pena|sinto muito|"
    r"espero que melhore|olha so|boa!|entendi|ah, entendi|hum, sei|saquei|certo|parabens|"
    r"imagino|entendo|pois e!|demais!|merecido)")


def _raizes(texto):
    return {w[:4] for w in re.findall(r"[a-z0-9]+", normalizar(texto))
            if len(w) >= 3 and w not in FUNCIONAIS}


def _vocabulario_conversa():
    from presenca import ABERTURAS, ACOLHER_CURTO, CONTINUAR, INICIATIVA, REACAO_NOME, SEGUIR_OBJETIVO
    textos = [t.replace("%s", "") for d in (ABERTURAS, ACOLHER_CURTO, CONTINUAR, REACAO_NOME)
              for v in d.values() for t in v]
    textos += [t.replace("%s", "") for t in INICIATIVA + SEGUIR_OBJETIVO]
    textos += list(_CONQUISTA) + list(_SAUDE) + list(CONECTORES)
    textos += ["E foi porque, né? Tudo isso porque. Ah, então foi porque."]
    raizes = set()
    for t in textos:
        raizes |= _raizes(t)
    return raizes


_CONQUISTA = ("Parabéns!", "Parabéns, que conquista!", "Que demais, parabéns!")
_SAUDE = ("Sinto muito.", "Poxa, sinto muito.", "Espero que melhore logo.")
_VOCABULARIO = []


def vocabulario():
    if not _VOCABULARIO:
        _VOCABULARIO.append(_vocabulario_conversa())
    return _VOCABULARIO[0]


def frases(texto):
    return [f for f in re.split(r"(?<=[.!?])\s+", texto.strip()) if f]


def estrutura(texto):
    """Esqueleto da resposta: A = reação sozinha, Ae = reação + eco na
    mesma frase, E? = eco como pergunta, N = afirmação, P = pergunta."""
    rotulos = []
    for f in frases(texto):
        n = normalizar(f)
        m = _ABERTURA_INICIO.match(n)
        if m:
            resto = n[m.end():].strip(" ,.!?")
            rotulos.append("Ae" if len(resto) > 3 else "A")
        elif f.endswith("?"):
            rotulos.append("E?" if not rotulos and re.match(r"(?:voce|seu|sua|seus|suas)\b", n) else "P")
        else:
            rotulos.append("N")
    return tuple(rotulos)


def palavras_novas(resposta, fontes):
    """Raízes de conteúdo da resposta que não vêm de nenhuma fonte (a fala,
    o plano) nem do vocabulário de conversa: candidatas a fato inventado."""
    from presenca import verbo_para_voce
    permitidas = set(vocabulario())
    for f in fontes:
        permitidas |= _raizes(f or "")
        # O eco passa a fala para "você": "fiz" → "fez", "vi" → "viu".
        for w in re.findall(r"[^\W\d_]+", (f or "").lower()):
            v = verbo_para_voce(w)
            if v:
                permitidas |= _raizes(v)
    return sorted(_raizes(resposta) - permitidas)


def reacoes_repetidas(resposta):
    return sum(1 for f in frases(resposta) if _ABERTURA_INICIO.match(normalizar(f))) > 1


@dataclass
class Plano:
    tom: str
    aberturas: tuple            # reações possíveis, já sem as usadas há pouco
    eco: str = ""               # o que a pessoa contou, na voz dela
    eco_na_abertura: bool = False
    causa: str = ""
    nocao: str = ""             # frase da noção ("X costuma…")
    perguntas: tuple = ()       # opções de pergunta, em ordem de preferência
    fala: str = ""
    extras: list = field(default_factory=list)

    def fontes(self):
        return [self.fala, self.eco, self.causa, self.nocao, *self.perguntas, *self.extras]

    def obrigatorias(self):
        return [p for p in (self.eco if self.eco_na_abertura or self.tom == "saude" else "",
                            self.causa, self.nocao) if p]


def _maiuscula(t):
    return t[0].upper() + t[1:] if t else t


def _minuscula(t):
    # "Noite mal dormida costuma…" → "noite mal dormida costuma…"; nomes próprios
    # e siglas ficam como estão.
    if not t or (len(t) > 1 and t[1].isupper()):
        return t
    return t[0].lower() + t[1:]


def candidatos(plano):
    """Realizações do plano: (texto, esqueleto de construção)."""
    sinal = "!" if plano.tom == "pos" else "."
    inicios = []
    for ab in plano.aberturas:
        if plano.tom == "saude" and plano.eco:
            inicios.append((_maiuscula(plano.eco) + "? " + ab, "eco?"))
            continue
        if plano.eco and plano.eco_na_abertura:
            inicios.append((ab.rstrip(".!") + ", " + plano.eco + sinal, "ab,eco"))
            # "Você passou na prova? Parabéns!": eco como pergunta só com reação
            # curta de surpresa e sem "ainda/também", que pedem a afirmação.
            if plano.tom in ("neg", "pos") and ab not in ("Ah, que pena.", "Que chato.") \
                    and not re.search(r"\b(?:ainda|tambem|de novo|mais uma vez)\b", normalizar(plano.eco)):
                inicios.append((_maiuscula(plano.eco) + "? " + ab, "eco?"))
        else:
            inicios.append((ab, "ab"))
    causas = [""]
    if plano.causa:
        causas = ["E foi porque %s, né?" % plano.causa, "Tudo isso porque %s." % plano.causa,
                  "Ah, então foi porque %s." % plano.causa]
    nocoes = [""]
    if plano.nocao:
        nocoes = [plano.nocao]
        if plano.tom in ("neg", "neutro") and not plano.causa:
            nocoes.append("É, " + _minuscula(plano.nocao))
    perguntas = []
    for p in plano.perguntas or ("",):
        perguntas.append(p)
        if p.endswith("?") and not re.match(r"(?:E|Se|Me|Quer|Que)\b", p) and len(p.split()) > 2:
            perguntas.append("E " + _minuscula(p))
    saida = []
    for ini, forma in inicios:
        for c in causas:
            for n in nocoes:
                for p in perguntas:
                    texto = " ".join(x for x in (ini, c, n, p) if x)
                    saida.append((texto, forma))
    return saida


def verificar(texto, plano):
    """None se a candidata é fiel ao plano; senão, o motivo."""
    novas = palavras_novas(texto, plano.fontes())
    if novas:
        return "acrescenta: " + ", ".join(novas)
    presentes = _raizes(texto)
    for parte in plano.obrigatorias():
        if not _raizes(parte) <= presentes:
            return "perde: " + parte
    if plano.nocao and not _raizes(plano.nocao) <= presentes:
        return "perde a noção"
    fontes = " ".join(normalizar(f) for f in plano.fontes() if f)
    for neg in ("nao", "nunca", "nem", "jamais"):
        if len(re.findall(r"\b%s\b" % neg, normalizar(texto))) > len(re.findall(r"\b%s\b" % neg, fontes)):
            return "acrescenta negação"
    if reacoes_repetidas(texto):
        return "reação repetida"
    return None


def realizar(plano, variacao, anterior=None):
    """Escolhe a realização: fiel ao plano, sem repetir a estrutura da
    resposta anterior e, entre as que sobram, a mais natural."""
    validas = [(t, f) for t, f in candidatos(plano) if verificar(t, plano) is None]
    if not validas:
        return None
    variadas = [(t, f) for t, f in validas if f != anterior] or validas
    escolha = variadas[0]
    from pontuador_frases import pontuador
    p = pontuador()
    if p.disponivel and len(variadas) > 1:
        try:
            notas = p.pontuar_varias(plano.fala, [t for t, _ in variadas])
            escolha = variadas[max(range(len(variadas)), key=notas.__getitem__)]
        except Exception:
            escolha = variadas[0]
    texto, forma = escolha
    for ab in plano.aberturas:
        if ab.rstrip(".!") in texto:
            variacao.usadas.append(ab)
            break
    for p_ in plano.perguntas:
        if _minuscula(p_) in texto or p_ in texto:
            variacao.usadas.append(p_)
            break
    return texto, forma


_FUTURO = re.compile(r"\b(?:vou|vamos|vai|amanha|semana que vem|mes que vem|ano que vem|"
                     r"proxim[oa]|depois|a gente vai)\b")
_PASSADO = re.compile(r"\b(?!(?:eu|seu|meu|teu|sou|vou|estou|dou|ou|deu|ceu|chapeu)\b)\w{2,}(?:ou|eu|iu)\b")


def tempo_compativel(fala, pergunta):
    """"vou comemorar com uma pizza" não combina com "Qual sabor você pediu?"."""
    n = normalizar(fala)
    if _FUTURO.search(n) and not re.search(r"\b\w{2,}ei\b", n):
        return not _PASSADO.search(normalizar(pergunta))
    return True
