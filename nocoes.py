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
    r"a gente|nos|hoje|ontem|agora|de novo|acabei|acordei|comprei|vi|comi|dormi|perdi|esqueci|"
    r"passei|comecei|assisti|ganhei|cozinhei|corri|caminhei|cheguei|sai|voltei|"
    r"ta fazendo|esta fazendo|ta (?:muito |tao )?\w+ndo|esta (?:muito |tao )?\w+ndo)\b|"
    r"\b\w+(?:ou|eu|iu)\b(?!(?:a|o|os|as) (?:\w+ )?(?:de|da|do)\b)")
_EXCLAMACAO = re.compile(r"que (?:calor|frio|preguica|sono|fome|tedio|saudade|chuva|cansaco|dia|noite)\b")
_RECUSA = re.compile(r"\b(?:dose|dosagem|remedio|medicamento|diagnostico|tratamento|nao|nunca|sem)\b")


class NocoesPT:
    def __init__(self, caminho=CAMINHO):
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
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
            for m in re.finditer(re.escape(alvo), n):
                ini, fim = m.start(), m.end()
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
        partes = [sorteio.choice(self._ABERTURA[tom]), principal["costuma"]]
        if tom == "saude" and principal["tipo"] != "saude":
            partes.append("Espero que melhore logo.")
        partes.append(principal["pergunta"])
        return principal, " ".join(partes)

    def continuar(self, texto, anterior, sorteio):
        """Continuação de um assunto já contado, sem noção nova."""
        tom = self.valencia(texto, [])
        if tom in ("neg", "saude"):
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
        if nocao is None:
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
        nocao = self.por_nome(alvo) or self.por_nome(alvo.split()[0] if alvo.split() else "")
        resto = ""
        if nocao is None and nocao_contexto is not None and re.search(r"\b(?:dele|dela|nele|nela)\b", n):
            nocao, resto = nocao_contexto, re.sub(r"\s*\b(?:dele|dela)\b", "", alvo).strip()
        if nocao is None:
            return None
        if n.startswith("por que"):
            limite = "Não sei explicar o porquê disso."
        elif resto:
            limite = ("Não sei explicar como funciona essa parte (" + resto + ") " +
                      _de(nocao["nome"]) + ".")
        else:
            limite = "Não sei explicar como " + _artigo(nocao["nome"]) + " funciona por dentro."
        return nocao, "Sei só o básico, como noção: " + nocao["e"] + " " + limite


def _artigo(nome):
    feminino = nome.endswith(("a", "ção", "são", "dade", "agem")) and nome not in ("dia",)
    return ("a " if feminino else "o ") + nome


def _de(nome):
    feminino = nome.endswith(("a", "ção", "são", "dade", "agem"))
    return ("da " if feminino else "do ") + nome
