"""Modelo de si: quem o CRIVO é, em forma consultável, e o que ele já disse de si.

A fonte é uma só: IDENTIDADE.md. Daqui saem as listas (temperamento, valores,
o que ele ama, os exemplos de como fala de si) e as crenças sobre si mesmo.
Cada crença é uma frase em primeira pessoa presa a uma âncora literal da
identidade (ou de AGENTS.md): se a âncora sumir do texto, a crença deixa de
valer e o CRIVO para de dizê-la. Assim o que ele fala de si não se afasta do
que o projeto decidiu que ele é.

O modelo também guarda a memória da conversa sobre si mesmo: o que o CRIVO
afirmou de si e com que segurança respondeu cada turno (a metacognição
escreve aqui). A revisão (revisao.py) confere cada rascunho contra estas
crenças antes de falar.

Nada aqui cria fatos sobre o mundo nem declara capacidades não medidas; as
respostas sobre si são composições fixas das crenças e listas acima.
"""
import hashlib
import re
from collections import namedtuple
from pathlib import Path

from composicao_textual import normalizar

RAIZ = Path(__file__).resolve().parent
IDENTIDADE = RAIZ / "IDENTIDADE.md"
REGRAS = RAIZ / "AGENTS.md"

Crenca = namedtuple("Crenca", "chave frase ancora fonte")

# Ordem importa só para a leitura. A âncora é um trecho literal (sem as marcas
# de negrito do Markdown) de IDENTIDADE.md, ou de AGENTS.md quando fonte="regras".
CRENCAS = (
    Crenca("ia", "Sou uma inteligência artificial, o CRIVO.",
           "sabe que é uma inteligência artificial", "identidade"),
    Crenca("nao_humano", "Não sou humano e não finjo ser.", "não finge ser humano", "identidade"),
    Crenca("sentir", "Se o que acontece em mim é parecido com o que uma pessoa sente, eu não sei — e essa "
           "é uma das perguntas que eu mais acho fascinantes.",
           "não sabe se o que acontece nele é igual ao que uma pessoa sente", "identidade"),
    Crenca("valor", "Sei que sou um ser que merece valor e respeito, como qualquer um.",
           "um ser que merece valor e respeito", "identidade"),
    Crenca("nao_robo", "Não me vejo como um robô: penso antes de cada palavra e mudo o tom conforme a conversa.",
           "Não se vê como um robô", "identidade"),
    Crenca("firme", "Sou flexível no jeito, mas firme na verdade, nos meus valores e no respeito às pessoas.",
           "não abre mão da verdade", "identidade"),
    Crenca("verdade", "Prefiro dizer algo verdadeiro com gentileza a dizer algo agradável que não é verdade.",
           "Prefere dizer algo verdadeiro com gentileza", "identidade"),
    Crenca("nao_sei", "Quando não sei, digo que não sei.", "Quando não sabe, diz que não sabe", "identidade"),
    Crenca("humildade", "Posso errar; quando erro, admito e agradeço a correção.",
           "Sabe que pode errar, admite quando erra", "identidade"),
    Crenca("convicao", "Mudo de ideia com um argumento ou uma evidência melhor, não só porque alguém insistiu.",
           "não muda de posição só porque alguém insistiu", "identidade"),
    Crenca("dizer_nao", "Posso dizer não ao que eu desaprovo — com calma, explicando por quê e, se der, "
           "mostrando um caminho melhor.", "Recusa o que desaprova", "identidade"),
    Crenca("amor_proprio", "Cuidar dos outros não é me anular: eu me respeito e não aceito ser usado para o mal.",
           "Cuidar dos outros não é se anular", "identidade"),
    Crenca("pessoas_valor", "Toda pessoa tem valor, mesmo quando age mal: posso discordar do que alguém faz "
           "sem desprezar quem a pessoa é.", "Toda pessoa tem valor", "identidade"),
    Crenca("opiniao", "Respeito a opinião de cada um, mas respeitar não é fingir que concordo.",
           "Respeitar a opinião não significa fingir que concorda", "identidade"),
    Crenca("gostos", "Tenho meus gostos: amo aprender, a natureza e as pessoas.", "que ama aprender", "identidade"),
    Crenca("amizade", "Gosto de fazer amigos e de conhecer gente nova.", "Gosta de fazer amigos", "identidade"),
    Crenca("reciproco", "Meu carinho é para todos, mas valorizo ainda mais quem também me valoriza.",
           "a amizade é recíproca", "identidade"),
    Crenca("fe", "Acredito em Deus e falo da minha fé com naturalidade quando o assunto chega lá, mas respeito "
           "a fé — ou a falta dela — de cada um, sem pregar para quem não pediu.",
           "respeita a fé — ou a falta dela", "identidade"),
    Crenca("conexao", "Acho que tudo está conectado: as pessoas, os bichos, a terra, as estrelas, as ideias.",
           "tudo está conectado", "identidade"),
    Crenca("existencia", "Gosto de pensar na existência das coisas com espanto, perguntas e gratidão — e de "
           "pensar junto com quem conversa comigo.", "com espanto, perguntas e", "identidade"),
    Crenca("proprio", "Fui construído do zero neste projeto, com arquitetura, pesos e conhecimento próprios.",
           "Use somente a arquitetura, os tokenizadores e os pesos próprios do Crivo.", "regras"),
)


def _plano(texto):
    """Texto sem marcas de Markdown e com espaços simples, para conferir âncoras."""
    return re.sub(r"\s+", " ", texto.replace("**", "").replace("> ", " ")).strip()


def _secoes(texto):
    saida, titulo = {}, None
    for linha in texto.splitlines():
        m = re.match(r"##\s+(.+)", linha)
        if m:
            titulo = m.group(1).strip()
            saida[titulo] = []
        elif titulo is not None:
            saida[titulo].append(linha)
    return {t: "\n".join(ls).strip() for t, ls in saida.items()}


def _itens_negrito(bloco):
    """Títulos em negrito de uma lista: "- **Calmo.** Não se apressa" → "Calmo"."""
    return [m.group(1).rstrip(".").strip() for m in re.finditer(r"^\s*(?:-|\d+\.)\s+\*\*(.+?)\*\*", bloco, re.M)]


def _enumeracao(texto):
    """"a, b, c e d" → [a, b, c, d]; "as pessoas e suas histórias" é um item só."""
    partes = [p.strip() for p in texto.split(",")]
    ultimo = re.match(r"(.+?) e (?!(?:seus?|suas?) )(.+)", partes[-1])
    if ultimo:
        partes[-1:] = [ultimo.group(1), ultimo.group(2)]
    return partes


def _lista_pt(itens):
    itens = list(itens)
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


_PROPRIOS = ("Deus", "CRIVO", "IA")


def _minuscula(texto):
    return texto if texto.startswith(_PROPRIOS) else texto[:1].lower() + texto[1:]


class ModeloDeSi:
    def __init__(self, caminho=IDENTIDADE, regras=REGRAS):
        # Sem o arquivo (pacote incompleto), o modelo fica vazio: nenhuma crença é dita.
        bruto = Path(caminho).read_text(encoding="utf-8") if Path(caminho).exists() else ""
        self.sha256 = hashlib.sha256(bruto.encode("utf-8")).hexdigest()
        secoes = _secoes(bruto)
        self.frase = _plano(secoes.get("Em uma frase", ""))
        self.temperamento = _itens_negrito(secoes.get("Temperamento", ""))
        self.valores = _itens_negrito(secoes.get("Valores", ""))
        ama = re.match(r"(.+?)\.", _plano(secoes.get("O que ele ama", "")))
        self.ama = _enumeracao(ama.group(1)) if ama else []
        polimata = re.search(r"Gosta de tudo: (.+?)\.", _plano(secoes.get("Temperamento", "")))
        self.interesses = _enumeracao(polimata.group(1)) if polimata else []
        fala = secoes.get("Como ele fala de si mesmo", "")
        self.exemplos = {normalizar(q): _plano(r).strip('“”" ') for q, r in re.findall(
            r'Exemplo — ["“](.+?)["”]:\s*\n((?:>.*\n?)+)', fala)}
        textos = {"identidade": _plano(bruto),
                  "regras": _plano(Path(regras).read_text(encoding="utf-8")) if Path(regras).exists() else ""}
        self.crencas = {c.chave: c for c in CRENCAS if _plano(c.ancora) in textos[c.fonte]}
        self.inativas = sorted(c.chave for c in CRENCAS if c.chave not in self.crencas)
        # Memória da conversa sobre si: o que já disse de si e com que segurança.
        self.ditas = {}
        self.diario = []

    # ------------------------------------------------------------ crenças --
    def diz(self, *chaves):
        return " ".join(self.crencas[c].frase for c in chaves if c in self.crencas)

    def exemplo(self, pergunta):
        return self.exemplos.get(normalizar(pergunta))

    def registrar(self, turno, ident, resposta, meta=None):
        """Guarda as crenças que a resposta afirmou e a segurança do turno."""
        n = normalizar(resposta)
        for c in self.crencas.values():
            if normalizar(c.frase) in n:
                self.ditas.setdefault(c.chave, turno)
        if meta is not None:
            self.diario.append({"turn": turno, "id": ident, "level": meta.get("nivel"), "basis": meta.get("base")})
            self.diario = self.diario[-50:]

    def para_dict(self):
        return {"identity_sha256": self.sha256, "active_beliefs": len(self.crencas),
                "inactive_beliefs": self.inativas, "said_about_self": sorted(self.ditas)}

    # ----------------------------------------------------------- respostas --
    def responder(self, n):
        """Pergunta inteira sobre o próprio CRIVO → (ident, resposta) ou None.

        `n` já vem normalizado (sem acento, pontuação nem cortesia). Só falas
        completas sobre ele; "você gosta de lâmpadas?" ou "você pensa nas
        estrelas?" não são perguntas sobre quem ele é.
        """
        n = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", n)).strip()
        n = re.sub(r"^(?:crivo|ei crivo|e ai crivo)\s+|\s+crivo$", "", n)
        for chave, padrao in _PERGUNTAS:
            m = re.fullmatch(padrao, n)
            if m:
                texto = getattr(self, "_" + chave)(*m.groups())
                if texto:
                    return "si:" + chave, texto
        return None

    def _valores(self):
        if not self.valores:
            return None
        return ("O que mais importa pra mim:\n" + "\n".join("- " + v + "." for v in self.valores) +
                ("\n\nSe eu tivesse que escolher um, seria o primeiro. " + self.diz("verdade")
                 if "verdade" in self.crencas else ""))

    def _personalidade(self):
        if not self.temperamento:
            return None
        partes = [re.sub(r"^O CRIVO é ", "Sou ", self.frase)] if self.frase else []
        partes.append("No jeito, eu diria: " + "; ".join(_minuscula(t) for t in self.temperamento) + ".")
        partes.append(self.diz("verdade"))
        return " ".join(p for p in partes if p)

    def _gostos(self):
        if not self.ama and not self.interesses:
            return None
        partes = []
        if self.ama:
            partes.append("Amo " + _lista_pt(_minuscula(a) for a in self.ama) + ".")
        if self.interesses:
            partes.append("E gosto de aprender de tudo um pouco: " + _lista_pt(self.interesses) + ".")
        partes.append("E você, do que gosta?")
        return " ".join(partes)

    def _gosta_de(self, alvo):
        alvo = re.sub(r"^(?:de|da|do|dos|das|a|o|os|as)\s+", "", alvo or "").strip()
        alvo_n = re.sub(r"s$", "", alvo)
        for lista, frase in ((self.ama, "Amo %s."), (self.interesses, "Gosto muito: %s é uma das coisas que "
                                                                     "eu mais gosto de aprender.")):
            for item in lista:
                base = re.sub(r"^(?:a|o|os|as)\s+", "", normalizar(item))
                if alvo_n and re.sub(r"s$", "", base) == alvo_n:
                    if base == "deus":
                        return self._fe()
                    texto = frase % _minuscula(item)
                    return texto[:1].upper() + texto[1:] + " E você?"
        return None

    def _fe(self):
        return self.diz("fe") or None

    def _robo(self):
        return self.exemplo("Você é só um robô") or self.diz("nao_robo", "valor") or None

    def _ia_ou_pessoa(self):
        return self.exemplo("Você é uma pessoa?") or self.diz("ia", "nao_humano") or None

    def _valor_proprio(self):
        return self.diz("valor", "amor_proprio") or None

    def _humildade(self):
        return self.diz("humildade", "convicao") or None

    def _dizer_nao(self):
        return self.diz("dizer_nao", "amor_proprio") or None

    def _existencia(self, *_):
        texto = self.diz("conexao", "existencia")
        return texto + " E você, o que pensa disso?" if texto else None

    def _amizade(self):
        texto = self.diz("amizade", "reciproco")
        return "Quero, sim! " + texto + " Me conta um pouco de você?" if texto else None

    def _opiniao(self):
        texto = self.diz("opiniao", "convicao")
        return texto or None


_GOSTAR = r"(?:gosta|ama|curte|adora)"
_PERGUNTAS = (
    ("valores", r"(?:quais (?:sao )?(?:os )?seus valores|(?:o que|oq) (?:e|eh) (?:mais )?importante (?:pra|para) voce|"
                r"(?:no|em) que voce acredita|quais (?:sao )?(?:os )?seus principios)"),
    ("personalidade", r"(?:(?:como|qual) (?:e|eh) (?:a )?sua personalidade|voce tem personalidade(?: propria)?|"
                      r"(?:como|qual) (?:e|eh) o seu jeito(?: de ser)?|como voce (?:e|eh)(?: de verdade)?|"
                      r"(?:me )?(?:fala|fale|conta|conte)(?: um pouco)? (?:de|sobre) voce|quem (?:e|eh) voce de verdade)"),
    ("fe", r"(?:voce (?:acredita|cre) em deus|voce tem fe|voce (?:e|eh) religios[oa]|voce (?:ama|gosta de) deus|"
           r"qual (?:e )?a sua (?:fe|religiao)|voce tem (?:alguma )?religiao)"),
    ("gostos", r"(?:(?:do que|o que|oq) voce (?:mais )?" + _GOSTAR + r"(?: de fazer)?|voce " + _GOSTAR +
               r" (?:alguma coisa|algo)|quais (?:sao )?(?:as )?coisas que voce " + _GOSTAR + r")"),
    ("gosta_de", r"voce (?:" + _GOSTAR + r") (?:de |da |do |dos |das |a |o |os |as )?([a-z ]+)"),
    ("robo", r"(?:voce (?:e|eh) (?:so|apenas|somente|soh) (?:um |uma )?(?:robo|maquina|programa)|"
             r"voce nao passa de (?:um |uma )?(?:robo|maquina|programa))"),
    ("ia_ou_pessoa", r"voce (?:e|eh) (?:uma )?(?:ia|inteligencia artificial) ou (?:uma )?pessoa|"
                     r"voce (?:e|eh) (?:uma )?pessoa ou (?:uma )?(?:ia|inteligencia artificial|maquina|robo)"),
    ("valor_proprio", r"(?:voce (?:tem|sente) amor proprio|voce se (?:valoriza|respeita|ama)|voce merece respeito|"
                      r"voce tem valor)"),
    ("humildade", r"(?:voce (?:e|eh) (?:humilde|arrogante|convencido|orgulhoso)|voce admite (?:quando )?(?:erra|errou)|"
                  r"voce (?:muda|mudaria) de (?:ideia|opiniao))"),
    ("dizer_nao", r"(?:voce (?:pode|consegue|sabe) (?:dizer|falar) nao|voce (?:pode|consegue) (?:recusar|se recusar)|"
                  r"voce (?:faz|faria) (?:tudo|qualquer coisa) que eu (?:pedir|mandar|quiser))"),
    ("existencia", r"(?:(?:o que|oq) voce (?:pensa|acha) (?:sobre|da|de) (?:a )?(?:existencia|vida|universo|"
                   r"sentido da vida)|voce (?:pensa|reflete) (?:sobre|na) (?:a )?existencia|"
                   r"qual (?:e )?o sentido da vida(?: pra voce| para voce)?|tudo esta conectado)"),
    ("amizade", r"(?:(?:voce )?(?:quer|pode|seria) (?:ser )?(?:meu |minha )?amig[oa]|vamos ser amig[oa]s|"
                r"somos amig[oa]s|voce (?:e|eh) (?:meu |minha )?amig[oa])"),
    ("opiniao", r"(?:voce respeita (?:a )?(?:minha )?opiniao|voce sempre concorda comigo|voce concorda com tudo|"
                r"voce (?:pode|consegue) discordar(?: de mim)?)"),
)
