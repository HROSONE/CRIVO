"""Gerador autoral autoregressivo: GRU condicional, com cópia de argumentos.

Os pesos aprendem a prever a próxima palavra de uma resposta. Não há
catálogo de respostas no checkpoint. Argumentos fora do vocabulário são
copiados de slots declarados na sessão, nunca aprendidos globalmente.
Treinamento usa NumPy; a inferência também funciona com Python padrão.
"""
import hashlib
import inspect
import json
import math
import random
import re
from functools import lru_cache
from pathlib import Path

VERSAO = "gru-contextual-v3"
DIMENSAO = 192
VARIANTES = 8
ACOES = ("historia", "poema", "final", "escuta", "alternativa", "ajuste", "apoio", "ideia",
         "mensagem", "dialogo", "continuacao", "resumo", "reformulacao", "exploracao", "plano", "reflexao")
ESTILOS = ("neutro", "leve", "aventura", "simples", "carinhoso", "formal", "divertido", "misterioso")
SLOTS = ("tema1", "tema2", "relato", "objetivo", "restricao",
         "destinatario", "premissa", "conclusao", "detalhe", "sentimento")
ESPECIAIS = ("<pad>", "<inicio>", "<fim>", "<desconhecido>")


def tokenizar(texto):
    return re.findall(r"@\w+|\w+(?:[-']\w+)*|⏎|[^\w\s]", texto.replace("\n", " ⏎ "), re.UNICODE)


def detokenizar(tokens):
    texto = " ".join(tokens)
    texto = re.sub(r"\s+([.,;:!?%\)\]\}»”])", r"\1", texto)
    texto = re.sub(r"([\(\[\{«“])\s+", r"\1", texto)
    return re.sub(r" *⏎ *", "\n", texto).strip()


def slots_requeridos(acao, slots):
    """Argumentos que uma resposta contextual deve conservar literalmente."""
    if acao not in ACOES:
        raise ValueError("Ação desconhecida")
    if acao in ("historia", "poema", "final", "ideia", "dialogo", "continuacao"):
        requeridos = {"tema1"} | ({"tema2"} if slots.get("tema2") else set())
        if acao == "continuacao" and slots.get("detalhe"):
            requeridos.add("detalhe")
    elif acao == "alternativa":
        requeridos = {"objetivo" if slots.get("objetivo") else "relato"}
        if slots.get("restricao"):
            requeridos.add("restricao")
    elif acao == "plano":
        requeridos = {"objetivo"} | ({"restricao"} if slots.get("restricao") else set())
    elif acao == "reflexao":
        requeridos = {"premissa", "conclusao"}
    elif acao == "mensagem":
        requeridos = {"relato"} | ({"destinatario"} if slots.get("destinatario") else set())
    else:
        requeridos = {"relato"}
        if acao in ("resumo", "reformulacao", "exploracao") and slots.get("detalhe"):
            requeridos.add("detalhe")
        if acao == "exploracao" and slots.get("sentimento"):
            requeridos.add("sentimento")
    return requeridos


def atributos(contexto):
    """Pedido/estado e resposta anterior ocupam áreas separadas do vetor."""
    acao, estilo = contexto["acao"], contexto.get("estilo", "neutro")
    if acao not in ACOES or estilo not in ESTILOS:
        raise ValueError("Ação ou estilo de geração desconhecido")
    slots = contexto.get("slots", {})
    if not isinstance(slots, dict) or any(nome not in SLOTS or not isinstance(valor, str)
                                         for nome, valor in slots.items()):
        raise ValueError("Slot de geração inválido")
    hs = contexto.get("historico", [])
    mensagem = contexto.get("mensagem", "")
    anterior = contexto.get("resposta_anterior", "")
    if (not isinstance(hs, list) or any(not isinstance(x, str) for x in hs) or
            not isinstance(mensagem, str) or not isinstance(anterior, str) or len(anterior)>2400):
        raise ValueError("Texto de contexto inválido")
    v = [0.0] * DIMENSAO
    v[ACOES.index(acao)] = 1.0
    v[16 + ESTILOS.index(estilo)] = .8
    v[24 + int(contexto.get("variante", 0)) % VARIANTES] = .6
    for i, nome in enumerate(SLOTS):
        if slots.get(nome):
            v[32 + i] = .5
    partes = [" ".join(hs[-3:] + [mensagem]), anterior]
    for parte, texto in enumerate(partes):
        for nome, valor in sorted(slots.items(), key=lambda p: -len(p[1])):
            if valor:
                texto = texto.replace(valor, "@" + nome)
        for t in tokenizar(texto.casefold())[-140:]:
            h = int.from_bytes(hashlib.sha256(t.encode("utf-8")).digest()[:4], "big")
            v[64 + parte*64 + h % 64] += .035
        inicio = 64 + parte*64
        norma = math.sqrt(sum(x*x for x in v[inicio:inicio+64])) or 1.0
        # O estado estruturado decide a ação. Texto é uma influência residual
        # limitada, para não substituir slots/tom por padrões do histórico.
        v[inicio:inicio+64] = [x * min(1.0, .15 / norma) for x in v[inicio:inicio+64]]
    return v


def assinatura_atributos():
    texto = VERSAO + repr((DIMENSAO, VARIANTES, ACOES, ESTILOS, SLOTS, ESPECIAIS))
    texto += inspect.getsource(atributos) + inspect.getsource(tokenizar)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def softmax(valores):
    pico = max(valores)
    exps = [math.exp(max(-70.0, x - pico)) for x in valores]
    soma = sum(exps)
    return [x / soma for x in exps]


def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, x))))


def _produto(vetor, matriz):
    return [sum(x * linha[j] for x, linha in zip(vetor, matriz)) for j in range(len(matriz[0]))]


class GeradorGRU:
    def __init__(self, dados, acelerar=True):
        if dados.get("versao") != 1 or dados.get("assinatura_atributos") != assinatura_atributos():
            raise ValueError("Checkpoint generativo incompatível; treine novamente")
        self.vocabulario = dados["vocabulario"]
        if (not 8 <= len(self.vocabulario) <= 2048 or
                len(self.vocabulario) != len(set(self.vocabulario)) or
                self.vocabulario[:4] != list(ESPECIAIS)):
            raise ValueError("Vocabulário generativo inválido")
        self.indices = {t: i for i, t in enumerate(self.vocabulario)}
        self.ocultos, self.embeddings = dados["ocultos"], dados["embeddings"]
        if not 8 <= self.ocultos <= 96 or not 8 <= self.embeddings <= 64:
            raise ValueError("Dimensões generativas inválidas")
        self.pesos = dados["pesos"]
        h, e, v = self.ocultos, self.embeddings, len(self.vocabulario)
        formas = {"E": (v,e), "F": (DIMENSAO,h), "bc": (h,), "O": (h,v), "bo": (v,)}
        for g in "zrn":
            formas["W"+g], formas["U"+g], formas["b"+g] = (e+h,h), (h,h), (h,)
        if set(self.pesos) != set(formas):
            raise ValueError("Matrizes generativas incompletas")
        for nome, forma in formas.items():
            a = self.pesos[nome]
            if len(a) != forma[0] or len(forma) == 2 and any(len(l) != forma[1] for l in a):
                raise ValueError("Matriz generativa com forma inválida: " + nome)
            valores = [x for l in a for x in l] if len(forma) == 2 else a
            if any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in valores):
                raise ValueError("Peso generativo inválido")
        self.np = None
        if acelerar:
            try:
                import numpy as np
                self.np = np
                self.pesos = {k: np.asarray(v, dtype=np.float64) for k,v in self.pesos.items()}
            except ImportError:
                pass

    def iniciar(self, contexto):
        f = atributos(contexto)
        if self.np is not None:
            c = self.np.tanh(self.np.asarray(f) @ self.pesos["F"] + self.pesos["bc"])
        else:
            c = [math.tanh(x+b) for x,b in zip(_produto(f,self.pesos["F"]),self.pesos["bc"])]
        return c, c.copy() if self.np is not None else list(c)

    def passo(self, token, h, c):
        p, np = self.pesos, self.np
        if np is not None:
            x = np.concatenate((p["E"][token], c))
            z = 1 / (1 + np.exp(-np.clip(x@p["Wz"] + h@p["Uz"] + p["bz"], -60,60)))
            r = 1 / (1 + np.exp(-np.clip(x@p["Wr"] + h@p["Ur"] + p["br"], -60,60)))
            n = np.tanh(x@p["Wn"] + (r*h)@p["Un"] + p["bn"])
            novo = (1-z)*h + z*n
            logits = novo@p["O"] + p["bo"]
            return novo, logits.tolist()
        x = p["E"][token] + c
        z = [_sigmoid(a+b+d) for a,b,d in zip(_produto(x,p["Wz"]),_produto(h,p["Uz"]),p["bz"])]
        r = [_sigmoid(a+b+d) for a,b,d in zip(_produto(x,p["Wr"]),_produto(h,p["Ur"]),p["br"])]
        n = [math.tanh(a+b+d) for a,b,d in zip(_produto(x,p["Wn"]),_produto([a*b for a,b in zip(r,h)],p["Un"]),p["bn"])]
        novo = [(1-a)*b + a*d for a,b,d in zip(z,h,n)]
        return novo, [a+b for a,b in zip(_produto(novo,p["O"]),p["bo"])]

    def probabilidades(self, contexto, prefixo=()):
        c, h = self.iniciar(contexto)
        h, logits = self.passo(1,h,c)
        for t in prefixo:
            h, logits = self.passo(self.indices.get(t,3),h,c)
        return softmax(logits)

    def gerar(self, contexto, max_tokens=96, temperatura=0.0, semente=0):
        if not 1 <= max_tokens <= 128 or not 0 <= temperatura <= 1.5:
            raise ValueError("Limite ou temperatura inválidos")
        c, h = self.iniciar(contexto)
        ultimo, tokens, logs = 1, [], []
        rng = random.Random(semente)
        completa = False
        for _ in range(max_tokens):
            h, logits = self.passo(ultimo,h,c)
            # Controle estrutural: slots só existem quando fornecidos;
            # tokens de padding/início/desconhecido nunca vão ao usuário.
            proibidos = {0,1,3}
            for nome in SLOTS:
                if not contexto.get("slots",{}).get(nome) and "@"+nome in self.indices:
                    proibidos.add(self.indices["@"+nome])
            for i in proibidos:
                logits[i] = -1e9
            ps = softmax(logits)
            if temperatura:
                candidatos = sorted(range(len(ps)),key=lambda i:ps[i],reverse=True)[:4]
                vals = softmax([logits[i]/temperatura for i in candidatos])
                ultimo = rng.choices(candidatos,weights=vals,k=1)[0]
            else:
                ultimo = max(range(len(ps)),key=lambda i:ps[i])
            logs.append(math.log(max(ps[ultimo],1e-12)))
            if ultimo == 2:
                completa = True
                break
            tokens.append(self.vocabulario[ultimo])
        return {"tokens":tokens,"texto":detokenizar(tokens),"completa":completa,
                "log_prob_media":sum(logs)/max(1,len(logs)),"quantidade_tokens":len(tokens)}


def renderizar(geracao, slots):
    """Substituição de uma passagem, sem interpretar marcadores nos valores."""
    tokens = geracao["tokens"]
    for t in tokens:
        if t.startswith("@") and (t[1:] not in SLOTS or not slots.get(t[1:])):
            raise ValueError("Geração referenciou um argumento ausente")
    # Primeiro compõe a linguagem, depois copia dados literalmente; eles
    # não são tokenizados novamente nem usados como código/formatação.
    texto = detokenizar(tokens)
    return re.sub(r"@(" + "|".join(SLOTS) + r")\b",lambda m:slots[m.group(1)],texto)


@lru_cache(maxsize=2)
def carregar(caminho, mtime):
    return GeradorGRU(json.loads(Path(caminho).read_text(encoding="utf-8")))
