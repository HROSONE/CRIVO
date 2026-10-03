"""Noções de senso comum do dia a dia.

Três níveis de saber, sempre declarados na resposta:
  - sei:        ficha com fonte (fora deste módulo);
  - tenho noção: senso comum sem fonte, dito como "em geral"/"costuma";
  - não sei:    explicar como algo funciona por dentro, ou por quê.

Uma noção nunca vira fato com fonte e nunca responde pergunta técnica ou
de saúde; ela serve para conversar sobre o que a pessoa observa.
"""
import json
import re
from pathlib import Path

from linguagem_conversa import normalizar

CAMINHO = Path(__file__).resolve().parent / "dados" / "nocoes_pt.json"

# Não é afirmação sobre o dia: pergunta, pedido ou comando.
_NAO_AFIRMACAO = re.compile(
    r"(?:o que|qual|quais|quanto|quantos|quantas|quando|onde|como|por que|porque|pq|quem|sera|vai|"
    r"existe|existem|tem como|da pra|voce|vc|me |pode|poderia|consegue|sabe|"
    r"(?:eu )?(?:quero|queria|gostaria|preciso|vou te|posso)|crie|cria|escreva|escreve|liste|lista|"
    r"mostre|mostra|explique|explica|fale|fala|conte|conta|diga|diz|faca|faz|compare|compara|resuma|"
    r"traduza|calcule|defina|ensina|ensine|ajuda|ajude|continue|continua|resposta|ok|sim|nao|"
    r"valeu|obrigad[oa]|brigad[oa]|tchau|ate (?:mais|logo|amanha)|boa (?:noite|tarde)|bom dia|oi|ola)\b")
_PERGUNTA_DEFINICAO = re.compile(
    r"(?:(?:voce )?(?:sabe|conhece) )?(?:o que (?:e|eh|significa)|o que quer dizer) (?:(?:um|uma|o|a|os|as) )?(.+)")
_PERGUNTA_POR_DENTRO = re.compile(
    r"(?:como (?:funciona|funcionam|e feito|e feita) (?:(?:um|uma|o|a|os|as) )?(.+?)(?: por dentro)?|"
    r"como (?:(?:um|uma|o|a|os|as) )?(.+?) funciona(?:m)?(?: por dentro)?|"
    r"por que (?:(?:o|a|os|as|um|uma) )?(.+?) (?:\w+)(?: .*)?)")
# Marcas de relato: pessoa, tempo ou um acontecimento no passado.
_RELATO = re.compile(
    r"\b(?:eu|to|tou|estou|estava|tava|fiquei|fui|fiz|tive|tenho que|meu|minha|meus|minhas|"
    r"a gente|nos|hoje|ontem|amanha|agora|de novo|acabei|acordei|comprei|vi|comi|dormi|perdi|esqueci|"
    r"passei|comecei|assisti|ganhei|cozinhei|corri|caminhei|cheguei|sai|voltei|"
    r"ta fazendo|esta fazendo|ta (?:muito |tao )?\w+ndo|esta (?:muito |tao )?\w+ndo)\b|"
    r"\b\w{3,}ei\b|\b\w+(?:ou|eu|iu)\b|"
    # Avaliação do que aconteceu: "o show foi incrível", "a festa foi chata".
    r"\b(?:foi|tava|estava|ficou) (?:muito |tao |super |bem |meio )?(?:incrivel|otim[oa]|bo[am]|ruim|pessim[oa]|"
    r"legal|lind[oa]|demais|chat[oa]|cansativ[oa]|divertid[oa]|horrivel|top|massa|maravilhos[oa]|corrid[oa]|"
    r"tranquil[oa]|dificil|facil|estranh[oa]|engracad[oa])\b")
_EXCLAMACAO = re.compile(r"que (?:calor|frio|preguica|sono|fome|tedio|saudade|chuva|cansaco|dia|noite)\b")
_RECUSA = re.compile(r"\b(?:dose|dosagem|remedio|medicamento|diagnostico|tratamento|tratar|cura|curar|"
                     r"depressao|doenca|doencas|nao|nunca|sem)\b")


# Relato de algo que já aconteceu: verbo no passado ("fiz", "pedi", "foi",
# "comprou"). Gosto ("adoro pizza"), plano ("vou fazer") e fragmento
# ("principalmente massa") não são.
_PASSADO = re.compile(
    r"\b(?!(?:eu|seu|meu|teu|sou|vou|estou|dou|ou|ceu|chapeu|museu|pneu)\b)\w{2,}(?:ei|ou|eu|iu)\b|"
    r"\b(?:fui|fiz|tive|vi|vim|dei|pus|quis|comi|bebi|dormi|perdi|corri|li|cai|sai|ouvi|senti|abri|"
    r"assisti|decidi|subi|pedi|foi|fez|teve|viu|veio|disse|trouxe|estava|tava|era|tinha)\b")
_GOSTO = re.compile(r"\b(?:gosto|adoro|amo|odeio|detesto|prefiro|curto|queria|quero|gostaria)\b")


def evento_passado(texto):
    n = normalizar(texto)
    return bool(_PASSADO.search(n)) and not _GOSTO.search(n)


def pergunta_para(nocao, texto):
    """A pergunta específica ("Fez com qual molho?") supõe que algo
    aconteceu; fora de um relato assim, vale a pergunta aberta."""
    geral = nocao.get("pergunta_geral")
    if geral and not evento_passado(texto):
        return geral
    return nocao["pergunta"]


# Cena observada com outra pessoa ("vi uma menina abrindo o guarda-chuva"):
# o bicho, a pessoa ou o objeto da cena não são da pessoa que conta.
_CENA = re.compile(r"(?:vi|ouvi|reparei|notei|vimos|percebi)\b.*\b(?:menin[oa]|homem|mulher|moc[oa]|senhor[a]?|"
                   r"crianca|garot[oa]|cara|pessoa|gente|rapaz|moca|velhinh[oa])\b")
_ANIMAL = re.compile(r"(?:(?:meu|minha|o|a) )?(?:cachorro|cachorra|gato|gata|passarinho|peixe|cavalo|"
                     r"coelho|hamster|papagaio|calopsita|tartaruga|cachorrinho|gatinho)\b")


# Morte de alguém: pessoa ou bicho de estimação. "O celular morreu", "morri de
# rir" e "perdi o ônibus" não são perda.
_SER = (r"(?:pai|mae|avo|avoa|bisavo|bisavoa|vo|irmao|irma|filho|filha|tio|tia|primo|prima|sobrinho|"
        r"sobrinha|marido|esposa|esposo|mulher|namorado|namorada|amigo|amiga|padrinho|madrinha|sogro|sogra|"
        r"cunhado|cunhada|neto|neta|vizinho|vizinha|colega|professor|professora|chefe|"
        r"cachorro|cachorra|cachorrinho|cachorrinha|gato|gata|gatinho|gatinha|cao|passarinho|"
        r"calopsita|periquito|papagaio|peixinho|peixe|hamster|coelho|coelha|cavalo|egua|tartaruga|"
        r"bebe|pet|bichinho|bichinha)")
_MORTE = re.compile(r"\b(?:morreu|morreram|faleceu|faleceram|falecido|falecida|partiu|se foi|nos deixou|"
                    r"descansou|foi pro ceu|foi para o ceu)\b")
_NAO_MORTE = re.compile(r"\bmorr\w* de (?:rir|fome|sono|frio|calor|vontade|vergonha|medo|saudade|cansaco|tedio)\b")
_PERDA_DIRETA = re.compile(r"\b(?:velorio|enterro|falecimento|luto)\b|\bperd(?:i|emos|eu) (?:o |a |os |as )?"
                           r"(?:meu |minha |meus |minhas |nosso |nossa )?" + _SER + r"\b")


def _ocorrencias(texto, alvo):
    """Posições das ocorrências literais, sem sobreposição (como re.finditer)."""
    i = texto.find(alvo)
    while i != -1:
        yield i
        i = texto.find(alvo, i + max(1, len(alvo)))


def perda(texto):
    """A fala conta a morte de alguém próximo (pessoa ou animal)."""
    n = normalizar(texto)
    if _NAO_MORTE.search(n):
        return False
    if _PERDA_DIRETA.search(n):
        return True
    return bool(_MORTE.search(n) and re.search(r"\b" + _SER + r"\b", n))


def pertinencia(nocao, texto, tom="neutro"):
    """(o "costuma" combina, a pergunta combina) com o que aconteceu.

    "Gato costuma derrubar coisas" serve para "meu gato derrubou um copo",
    não para "meu gato sumiu". A noção diz em "eventos" com que
    acontecimentos combina; sem esse campo, combina com qualquer relato que
    a cite (chuva, pizza, trânsito…)."""
    n = normalizar(texto)
    if _CENA.match(n):
        # Cena vista de fora: nada ali aconteceu com quem conta.
        return False, False
    if nocao.get("tipo") == "saude" and _ANIMAL.match(n):
        # "Meu cachorro está doente": a noção de doença fala de gente.
        return False, False
    # Depois de um término, "Vocês estão juntos há quanto tempo?" não cabe.
    if nocao.get("nome") == "namoro" and re.search(
            r"\b(?:terminei|terminamos|terminou comigo|separamos|me separei|divorci\w*)\b", n):
        return False, False
    # "Não almocei", "ele não quer comer": o que não aconteceu não puxa
    # comentário sobre isso.
    formas = [normalizar(f) for f in nocao.get("formas", ())]
    if formas and re.search(r"\b(?:nao|sem|nem)\b(?: \w+){0,2} (?:%s)\b" % "|".join(re.escape(f) for f in formas), n):
        return False, False
    raizes = nocao.get("eventos")
    if not raizes:
        return True, True
    combina = bool(re.search(r"\b(?:%s)" % "|".join(re.escape(r) for r in raizes), n))
    livre = nocao.get("pergunta_livre")
    return combina, combina or livre is True or (isinstance(livre, list) and tom in livre)


class NocoesPT:
    def __init__(self, caminho=CAMINHO):
        try:
            dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # Pacote sem a pasta de dados: sem noções, o Crivo segue como antes.
            dados = {"nocoes": [], "eventos": {"neg": [], "pos": [], "saude": []}}
        self.nocoes = dados["nocoes"]
        self.eventos = {k: [normalizar(w) for w in v] for k, v in dados["eventos"].items()}
        self._formas = []
        for nocao in self.nocoes:
            for forma in {nocao["nome"], *nocao["formas"]}:
                self._formas.append((normalizar(forma), nocao))
        # Formas mais longas primeiro: "dor de cabeça" antes de "cabeça".
        self._formas.sort(key=lambda par: -len(par[0]))

    def encontrar(self, texto):
        """Noções citadas no texto, na ordem em que aparecem."""
        n = " " + normalizar(texto).replace("-", " ") + " "
        achadas, ocupado = [], []
        for forma, nocao in self._formas:
            alvo = " " + forma.replace("-", " ") + " "
            for ini in _ocorrencias(n, alvo):
                fim = ini + len(alvo)
                if any(ini < f - 1 and i < fim - 1 for i, f in ocupado):
                    continue
                ocupado.append((ini, fim))
                if nocao not in (a for _, a in achadas):
                    achadas.append((ini, nocao))
        return [nocao for _, nocao in sorted(achadas, key=lambda par: par[0])]

    def por_nome(self, texto):
        alvo = normalizar(texto).strip(" ?.!").replace("-", " ")
        alvo = re.sub(r"^(?:um|uma|o|a|os|as) ", "", alvo)
        for forma, nocao in self._formas:
            if forma.replace("-", " ") == alvo:
                return nocao
        return None

    @staticmethod
    def afirmacao(texto):
        """Relato pessoal ou observação do momento, não uma busca digitada
        sem interrogação ("receita de arroz", "planta precisa de sol")."""
        n = normalizar(texto).strip(" .!")
        if "?" in texto or len(n.split()) < 2 or _NAO_AFIRMACAO.match(n):
            return False
        return bool(_RELATO.search(n) or _EXCLAMACAO.match(n))

    def valencia(self, texto, nocoes):
        if perda(texto):
            return "luto"
        n = " " + normalizar(texto) + " "
        for tipo in ("saude", "pos", "neg"):
            if any(" " + w + " " in n for w in self.eventos[tipo]):
                return tipo
        for nocao in nocoes:
            if nocao.get("valencia"):
                return nocao["valencia"]
        return "neutro"

    # ----- respostas -------------------------------------------------
    _ABERTURA = {
        "neg": ("Poxa.", "Que chato.", "Puxa vida."),
        "saude": ("Sinto muito.", "Poxa, sinto muito."),
        "luto": ("Sinto muito pela sua perda.", "Meus sentimentos."),
        "pos": ("Que bom!", "Que legal!", "Que ótimo!"),
        "neutro": ("Entendi.", "Ah, entendi.", "Hmm, entendi."),
    }

    def observar(self, texto, sorteio, nocoes=None):
        """Reação a algo que a pessoa conta: abertura conforme o tom, uma
        noção dita como noção e uma pergunta de volta."""
        nocoes = nocoes or self.encontrar(texto)
        if not nocoes:
            return None
        # "meu filho começou na escola": o assunto é a escola, não o filho.
        # Lugar ou momento genérico ("em casa", "dia") cede para o específico.
        principal = next((x for x in nocoes if x["tipo"] != "pessoa" and not x.get("generica")),
                         next((x for x in nocoes if x["tipo"] != "pessoa"), nocoes[0]))
        tom = self.valencia(texto, nocoes)
        costuma, pergunta = pertinencia(principal, texto, tom)
        partes = [sorteio.choice(self._ABERTURA[tom])]
        if costuma:
            partes.append(principal["costuma"])
        if tom == "saude" and principal["tipo"] != "saude":
            partes.append("Espero que melhore logo.")
        partes.append(pergunta_para(principal, texto) if pergunta else "Me conta mais.")
        return principal, " ".join(partes)

    def continuar(self, texto, anterior, sorteio):
        """Continuação de um assunto já contado, sem noção nova."""
        tom = self.valencia(texto, [])
        if tom in ("neg", "saude", "luto"):
            return sorteio.choice(("Imagino.", "Entendo.")) + " E como você está lidando com isso?"
        if tom == "pos":
            return sorteio.choice(self._ABERTURA["pos"]) + " Me conta mais."
        return sorteio.choice(("Entendi. E como você está com tudo isso?",
                               "Entendi. E o que mais aconteceu?"))

    def definir(self, texto):
        m = _PERGUNTA_DEFINICAO.fullmatch(normalizar(texto).strip(" ?.!"))
        if not m or _RECUSA.search(normalizar(texto)):
            return None
        nocao = self.por_nome(m.group(1))
        if nocao is None or nocao["tipo"] == "saude":
            return None
        return nocao, "Tenho uma noção, sem fonte: " + nocao["e"] + " " + nocao["costuma"]

    def nao_sei(self, texto, nocao_contexto=None):
        n = normalizar(texto).strip(" ?.!")
        if _RECUSA.search(n):
            return None
        m = _PERGUNTA_POR_DENTRO.fullmatch(n)
        if not m:
            return None
        alvo = next(g for g in m.groups() if g)
        nocao = self.por_nome(alvo)
        resto = ""
        if nocao is None and nocao_contexto is not None and re.search(r"\b(?:dele|dela|nele|nela)\b", n):
            nocao, resto = nocao_contexto, re.sub(r"\s*\b(?:dele|dela)\b", "", alvo).strip()
        if nocao is None or nocao["tipo"] == "saude":
            return None
        if n.startswith("por que"):
            limite = "Não sei explicar o porquê disso."
        elif resto:
            limite = ("Não sei explicar como funciona essa parte (" + resto + ") " +
                      _de(nocao["nome"]) + ".")
        else:
            limite = "Não sei explicar como " + _artigo(nocao["nome"]) + " funciona por dentro."
        # Trecho com a palavra seguinte: "energia solar" é outro conceito.
        palavras = n.split()
        inicio = palavras.index(alvo.split()[0]) if alvo.split()[0] in palavras else 0
        trecho = " ".join(palavras[inicio:inicio + len(alvo.split()) + 1])
        return nocao, "Sei só o básico, como noção: " + nocao["e"] + " " + limite, trecho


def _artigo(nome):
    feminino = nome.endswith(("a", "ção", "são", "dade", "agem")) and nome not in ("dia",)
    return ("a " if feminino else "o ") + nome


def _de(nome):
    feminino = nome.endswith(("a", "ção", "são", "dade", "agem"))
    return ("da " if feminino else "do ") + nome
