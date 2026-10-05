"""Compreensão neural própria: de uma pergunta livre ao assunto que o CRIVO conhece.

Rede treinada do zero em NumPy (scripts/treinar_entendimento.py), sem pesos
ou vocabulário externos. Lê n-gramas de palavras e de caracteres com hash
(tolera erros de digitação e fala informal), passa por uma camada oculta e
escolhe entre as intenções da base, os conceitos com ficha e a classe
``fora`` — perguntas que o CRIVO não sabe responder.

Ela não escreve respostas: só aponta o assunto. O CRIVO então responde pela
pergunta canônica desse assunto, com as mesmas fontes e verificações de
sempre. A rede só é consultada quando as regras não entenderam e só decide
acima de um limiar escolhido na validação; o resto continua como antes.
Sem NumPy ou sem pesos aprovados no controle de qualidade, fica desligada.
"""
import json
import re
import unicodedata
import zlib
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "artefatos" / "entendimento_pt"
FORA = "__fora__"
VERSAO = "entendimento-hash-mlp-v1"

INFORMAL = {
    "vc": "voce", "vcs": "voces", "ce": "voce", "pra": "para", "pro": "para o", "pros": "para os",
    "pras": "para as", "ta": "esta", "to": "estou", "tou": "estou", "tava": "estava", "q": "que",
    "oq": "o que", "pq": "por que", "porque": "por que", "tb": "tambem", "tbm": "tambem",
    "mto": "muito", "mt": "muito", "hj": "hoje", "msm": "mesmo", "td": "tudo", "naum": "nao",
    "n": "nao", "eh": "e", "d": "de", "ap": "apartamento", "apto": "apartamento", "agr": "agora",
    "dps": "depois", "qnd": "quando", "qdo": "quando", "cmg": "comigo", "blz": "beleza",
    "js": "javascript", "py": "python", "ts": "typescript",
}


def normalizar(texto):
    n = unicodedata.normalize("NFD", texto.casefold())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    palavras = re.findall(r"[a-z0-9]+", n)
    saida = []
    for p in palavras:
        saida.extend(INFORMAL.get(p, p).split())
    return saida


def _hash(texto, dimensao):
    return zlib.crc32(texto.encode("utf-8")) % dimensao


def caracteristicas(texto, dimensao):
    """Índices com hash: palavras, pares de palavras e n-gramas de 3 a 5 letras."""
    palavras = normalizar(texto)
    feats = set()
    for i, p in enumerate(palavras):
        feats.add("w:" + p)
        if i + 1 < len(palavras):
            feats.add("b:" + p + "_" + palavras[i + 1])
        if len(p) >= 3:
            marcada = "<" + p + ">"
            for n in (3, 4, 5):
                for j in range(len(marcada) - n + 1):
                    feats.add("c:" + marcada[j:j + n])
    return sorted({_hash(f, dimensao) for f in feats})


# Palavras de pergunta e de conversa que não mudam o assunto pedido.
GENERICAS = frozenset("""
a o as os um uma uns umas de do da dos das em no na nos nas por para com sem e ou que qual quais
quem como onde quando quanto quantos quantas porque por que se me te voce voces eu ele ela isso isto
esse essa este esta aquele aquela meu minha seu sua nosso nossa ja so mais menos muito pouco bem mal
sim nao tambem entao ai la aqui agora hoje oi ola ei olha bom boa dia tarde noite obrigado obrigada
valeu favor por favor licenca crivo duvida duvidas pergunta perguntas queria quero gostaria preciso
precisava pode poderia consegue sabe saber sei conhece conhecer entender entendo compreender explica
explicar explique explicacao fala falar fale conta contar conte diz dizer diga mostra mostrar ensina
ensinar aprender estudar estudando estudo escola prova trabalho resumo resumir informacao informacoes
sobre respeito acerca tema assunto coisa coisas ideia significa significado conceito definicao define
definir vem ser foi era sao e esta estao tem ter tinha existe existem acontece aconteceu rolou houve
funciona funcionamento serve servir importancia importante quer dizer tal tipo essa ajuda ajudar
ajude rapidinho direitinho exatamente afinal mesmo verdade principal basico basicamente geral
""".split())


def _raiz(p):
    return p[:5]


def guarda_vocabulario(texto, rotulo, nomes, vocabulario):
    """Se o nome do assunto aparece na pergunta, o restante precisa caber no
    vocabulário desse assunto ou em palavras genéricas de pergunta. “Qual o
    signo de Isaac Newton?” cita Newton, mas pede algo que a ficha não trata."""
    palavras = normalizar(texto)
    restantes = list(palavras)
    ancorado = False
    for nome in sorted(nomes.get(rotulo, ()), key=len, reverse=True):
        n = len(nome)
        for i in range(len(restantes) - n + 1):
            if restantes[i:i + n] == nome:
                del restantes[i:i + n]
                ancorado = True
                break
    if not ancorado:
        return True
    raizes = vocabulario.get(rotulo, ())
    extras = [p for p in restantes if len(p) >= 3 and p not in GENERICAS and _raiz(p) not in raizes]
    return not extras


class EntendimentoNeural:
    """Carrega pesos aprovados e prevê (rótulo, probabilidade, margem)."""

    def __init__(self, pasta=PASTA):
        self.ativo = False
        self.motivo = ""
        try:
            import numpy as np
        except ImportError:
            self.motivo = "NumPy ausente"
            return
        try:
            meta = json.loads((Path(pasta) / "meta.json").read_text(encoding="utf-8"))
            pesos = np.load(Path(pasta) / "modelo.npz")
        except (OSError, ValueError) as exc:
            self.motivo = "pesos ausentes: %s" % exc
            return
        if meta.get("versao") != VERSAO or not meta.get("controle", {}).get("aprovado"):
            self.motivo = "pesos não aprovados no controle de qualidade"
            return
        self.np = np
        self.meta = meta
        self.rotulos = meta["rotulos"]
        self.canonicas = meta["canonicas"]
        self.dimensao = meta["dimensao"]
        self.nomes = {r: [n for n in ns] for r, ns in meta.get("nomes", {}).items()}
        self.vocabulario = {r: frozenset(v) for r, v in meta.get("vocabulario", {}).items()}
        self.limiar = meta["controle"]["limiar"]
        self.margem = meta["controle"]["margem"]
        self.w1 = pesos["w1"].astype(np.float32)
        self.b1 = pesos["b1"].astype(np.float32)
        self.w2 = pesos["w2"].astype(np.float32)
        self.b2 = pesos["b2"].astype(np.float32)
        self.ativo = True

    def probabilidades(self, texto):
        np = self.np
        idx = caracteristicas(texto, self.dimensao)
        if not idx:
            return None
        h = self.w1[idx].sum(axis=0) / np.sqrt(len(idx)) + self.b1
        h = np.maximum(h, 0)
        z = h @ self.w2 + self.b2
        z = z - z.max()
        p = np.exp(z)
        return p / p.sum()

    def prever(self, texto):
        if not self.ativo or not isinstance(texto, str) or not texto.strip() or len(texto) > 600:
            return None
        p = self.probabilidades(texto)
        if p is None:
            return None
        ordem = p.argsort()[::-1]
        melhor, segundo = int(ordem[0]), int(ordem[1])
        return self.rotulos[melhor], float(p[melhor]), float(p[melhor] - p[segundo])

    def decidir(self, texto):
        """Rótulo e pergunta canônica, só acima do limiar e da margem validados."""
        previsto = self.prever(texto)
        if previsto is None:
            return None
        rotulo, prob, margem = previsto
        if rotulo == FORA or prob < self.limiar or margem < self.margem:
            return None
        if not guarda_vocabulario(texto, rotulo, self.nomes, self.vocabulario):
            return None
        return rotulo, self.canonicas[rotulo], prob


_INSTANCIA = None


def entendimento():
    global _INSTANCIA
    if _INSTANCIA is None:
        _INSTANCIA = EntendimentoNeural()
    return _INSTANCIA
