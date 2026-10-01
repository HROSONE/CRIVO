"""Compreensão contextual autoral: subpalavras, BiGRU, atenção e papéis BIO.

A rede lê as palavras atuais e as falas anteriores na ordem em que foram
ditas. Ela prevê um ato de conversa e trechos literais do pedido atual;
isso não demonstra que o conteúdo de um trecho seja verdadeiro. Nenhum
peso ou vocabulário vem de um modelo externo. NumPy é opcional na inferência.
"""
import hashlib
import io
import inspect
import json
import math
import re
import tokenize
import unicodedata
from functools import lru_cache
from pathlib import Path

VERSAO = "compreensao-contextual-bigru-bio-v1"
ORIGENS = ("usuario", "assistente", "memoria", "atual")
ROTAS = ("conversa", "consulta", "escrita")


def tokenizar(texto):
    return [(m.group(), m.start(), m.end()) for m in
            re.finditer(r"\w+(?:[-'’]\w+)*|[^\w\s]", texto, re.UNICODE)]


def normalizar_token(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.casefold())
                   if unicodedata.category(c) != "Mn")


def subpalavras(texto, baldes):
    t = "<" + normalizar_token(texto)[:48] + ">"
    unidades = [t] + [t[i:i + k] for k in (2, 3, 4)
                      for i in range(len(t) - k + 1)]
    return tuple(sorted({1 + int.from_bytes(hashlib.sha256(x.encode("utf-8")).digest()[:4],
                                             "big") % (baldes - 1) for x in unidades}))


def preparar_entrada(mensagem, historico=(), baldes=2048, max_atual=96, max_historico=64):
    if not isinstance(mensagem, str) or len(mensagem) > 6000:
        raise ValueError("Mensagem de compreensão inválida")
    if not isinstance(historico, (list, tuple)) or len(historico) > 32:
        raise ValueError("Histórico de compreensão inválido")
    anteriores = []
    for fala in historico:
        if (not isinstance(fala, dict) or fala.get("papel") not in ORIGENS[:-1] or
                not isinstance(fala.get("texto"), str) or len(fala["texto"]) > 6000):
            raise ValueError("Fala anterior de compreensão inválida")
        origem = ORIGENS.index(fala["papel"])
        anteriores.append(("<" + fala["papel"] + ">", origem, None))
        anteriores.extend((t, origem, None) for t, _, _ in tokenizar(fala["texto"]))
    anteriores = anteriores[-max_historico:] if max_historico else []
    atuais = tokenizar(mensagem)
    truncado = len(atuais) > max_atual
    unidades = anteriores + [("<atual>", 3, None)] + [
        (t, 3, (inicio, fim)) for t, inicio, fim in atuais[:max_atual]]
    return {"unidades": [subpalavras(t, baldes) for t, _, _ in unidades],
            "origens": [o for _, o, _ in unidades],
            "offsets": [offset for _, _, offset in unidades],
            "tokens_atuais": len(atuais), "contexto_truncado": truncado,
            "historico_tokens": len(anteriores)}


def assinatura_entrada():
    fonte = repr((VERSAO, ORIGENS))
    # Tokens evitam diferenças de AST entre Python 3.8, 3.11 e 3.13.
    # Conservam operações e blocos, mas ignoram comentários, espaços e
    # o cache de desempenho, que não altera as entradas matemáticas.
    for funcao in (tokenizar, normalizar_token, subpalavras, preparar_entrada):
        codigo = re.sub(r"^@lru_cache\([^\n]*\)\n", "", inspect.getsource(funcao))
        unidades = []
        for t in tokenize.generate_tokens(io.StringIO(codigo).readline):
            if t.type in (tokenize.COMMENT, tokenize.NL, tokenize.ENDMARKER):
                continue
            valor = "" if t.type in (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE) else t.string
            unidades.append((tokenize.tok_name[t.type], valor))
        fonte += repr(unidades)
    return hashlib.sha256(fonte.encode("utf-8")).hexdigest()


def softmax(valores):
    pico = max(valores)
    exps = [math.exp(max(-70.0, x - pico)) for x in valores]
    soma = sum(exps)
    return [x / soma for x in exps]


def _produto(vetor, matriz):
    return [sum(x * linha[j] for x, linha in zip(vetor, matriz))
            for j in range(len(matriz[0]))]


def _sigmoid(x):
    return 1 / (1 + math.exp(-max(-40.0, min(40.0, x))))


def decodificar_bio(probabilidades, papeis):
    """Viterbi com transições BIO legais; não impõe palavras de um assunto."""
    if not probabilidades:
        return []
    n = 1 + 2 * len(papeis)
    anterior = [-1e30] * n
    for j in range(n):
        if j == 0 or j % 2:
            anterior[j] = math.log(max(probabilidades[0][j], 1e-12))
    caminhos = []
    for ps in probabilidades[1:]:
        proximo, ponteiros = [], []
        for j in range(n):
            possiveis = (j - 1, j) if j and j % 2 == 0 else range(n)
            k = max(possiveis, key=lambda i: anterior[i])
            proximo.append(anterior[k] + math.log(max(ps[j], 1e-12)))
            ponteiros.append(k)
        anterior = proximo
        caminhos.append(ponteiros)
    ultimo = max(range(n), key=lambda j: anterior[j])
    caminho = [ultimo]
    for ponteiros in reversed(caminhos):
        ultimo = ponteiros[ultimo]
        caminho.append(ultimo)
    return list(reversed(caminho))


class CompreensaoNeural:
    def __init__(self, dados, acelerar=True):
        if (dados.get("versao") != 1 or dados.get("assinatura_entrada") != assinatura_entrada() or
                dados.get("arquitetura") != VERSAO):
            raise ValueError("Checkpoint de compreensão incompatível")
        self.atos, self.papeis = dados.get("atos"), dados.get("papeis")
        for catalogo, minimo, maximo in ((self.atos, 2, 64), (self.papeis, 1, 24)):
            if (not isinstance(catalogo, list) or not minimo <= len(catalogo) <= maximo or
                    len(set(catalogo)) != len(catalogo) or
                    any(not isinstance(t, str) or not re.fullmatch(r"[a-z][a-z_]{0,39}", t)
                        for t in catalogo)):
                raise ValueError("Catálogo de compreensão inválido")
        self.ocultos, self.embeddings, self.baldes = (dados.get(k) for k in
                                                   ("ocultos", "embeddings", "baldes"))
        if (not isinstance(self.ocultos, int) or not 8 <= self.ocultos <= 96 or
                not isinstance(self.embeddings, int) or not 8 <= self.embeddings <= 64 or
                not isinstance(self.baldes, int) or not 128 <= self.baldes <= 8192):
            raise ValueError("Dimensões de compreensão inválidas")
        self.max_atual, self.max_historico = dados.get("max_atual", 96), dados.get("max_historico", 64)
        if (not isinstance(self.max_atual, int) or not 8 <= self.max_atual <= 256 or
                not isinstance(self.max_historico, int) or not 0 <= self.max_historico <= 256):
            raise ValueError("Limites de compreensão inválidos")
        self.limiar, self.margem_minima, self.limiar_span = (dados.get(k, v) for k, v in
                            (("limiar", .65), ("margem_minima", .15), ("limiar_span", .55)))
        if any(not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= 1
               for x in (self.limiar, self.margem_minima, self.limiar_span)):
            raise ValueError("Limiares de compreensão inválidos")
        self.temperatura = dados.get("temperatura", 1.0)
        if (not isinstance(self.temperatura, (int, float)) or
                not math.isfinite(self.temperatura) or not .2 <= self.temperatura <= 10):
            raise ValueError("Temperatura de compreensão inválida")
        pesos_declarados = dados.get("pesos")
        self.tem_rota = isinstance(pesos_declarados, dict) and ("L" in pesos_declarados or "bl" in pesos_declarados)
        self.temperatura_rota = dados.get("temperatura_rota", 1.0)
        self.limiar_rota, self.margem_rota = dados.get("limiar_rota", .8), dados.get("margem_rota", .15)
        if (not isinstance(self.temperatura_rota, (int, float)) or
                not math.isfinite(self.temperatura_rota) or not .2 <= self.temperatura_rota <= 10 or
                any(not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= 1
                    for x in (self.limiar_rota, self.margem_rota))):
            raise ValueError("Calibração de rota inválida")
        h, e = self.ocultos, self.embeddings
        formas = {"E": (self.baldes, e), "R": (len(ORIGENS), e), "q": (2 * h,),
                  "A": (2 * h, len(self.atos)), "ba": (len(self.atos),),
                  "S": (2 * h, 1 + 2 * len(self.papeis)), "bs": (1 + 2 * len(self.papeis),)}
        if self.tem_rota:
            formas.update(L=(2 * h, len(ROTAS)), bl=(len(ROTAS),))
        for pref in ("a", "b"):
            for g in "zrn":
                formas[pref + "W" + g] = (e, h)
                formas[pref + "U" + g] = (h, h)
                formas[pref + "b" + g] = (h,)
        self.pesos = dados.get("pesos")
        if not isinstance(self.pesos, dict) or set(self.pesos) != set(formas):
            raise ValueError("Matrizes de compreensão incompletas")
        for nome, forma in formas.items():
            matriz = self.pesos[nome]
            if (not isinstance(matriz, list) or len(matriz) != forma[0] or
                    len(forma) == 2 and any(not isinstance(l, list) or len(l) != forma[1] for l in matriz)):
                raise ValueError("Matriz de compreensão com forma inválida: " + nome)
            valores = [x for l in matriz for x in l] if len(forma) == 2 else matriz
            if any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in valores):
                raise ValueError("Peso de compreensão inválido")
        self.np = None
        if acelerar:
            try:
                import numpy as np
                self.np = np
                self.pesos = {k: np.asarray(v, dtype=np.float64) for k, v in self.pesos.items()}
            except ImportError:
                pass

    def _representar(self, entrada):
        p, np = self.pesos, self.np
        if np is not None:
            x = np.asarray([p["E"][list(us)].sum(axis=0) / math.sqrt(len(us)) + p["R"][origem]
                            for us, origem in zip(entrada["unidades"], entrada["origens"])])
            sequencias = []
            for pref, ordem in (("a", range(len(x))), ("b", reversed(range(len(x))))):
                h, saidas = np.zeros(self.ocultos), [None] * len(x)
                for i in ordem:
                    z = 1 / (1 + np.exp(-np.clip(x[i] @ p[pref + "Wz"] + h @ p[pref + "Uz"] + p[pref + "bz"], -40, 40)))
                    r = 1 / (1 + np.exp(-np.clip(x[i] @ p[pref + "Wr"] + h @ p[pref + "Ur"] + p[pref + "br"], -40, 40)))
                    n = np.tanh(x[i] @ p[pref + "Wn"] + (r * h) @ p[pref + "Un"] + p[pref + "bn"])
                    h = (1 - z) * h + z * n
                    saidas[i] = h
                sequencias.append(saidas)
            return np.concatenate(sequencias, axis=1)
        x = [[sum(p["E"][i][j] for i in us) / math.sqrt(len(us)) + p["R"][origem][j]
              for j in range(self.embeddings)] for us, origem in zip(entrada["unidades"], entrada["origens"])]
        sequencias = []
        for pref, ordem in (("a", range(len(x))), ("b", reversed(range(len(x))))):
            h, saidas = [0.0] * self.ocultos, [None] * len(x)
            for i in ordem:
                z = [_sigmoid(a + b + c) for a, b, c in zip(_produto(x[i], p[pref + "Wz"]), _produto(h, p[pref + "Uz"]), p[pref + "bz"])]
                r = [_sigmoid(a + b + c) for a, b, c in zip(_produto(x[i], p[pref + "Wr"]), _produto(h, p[pref + "Ur"]), p[pref + "br"])]
                n = [math.tanh(a + b + c) for a, b, c in zip(_produto(x[i], p[pref + "Wn"]), _produto([a * b for a, b in zip(r, h)], p[pref + "Un"]), p[pref + "bn"])]
                h = [(1 - a) * b + a * c for a, b, c in zip(z, h, n)]
                saidas[i] = h
            sequencias.append(saidas)
        return [a + b for a, b in zip(*sequencias)]

    def analisar(self, mensagem, historico=()):
        entrada = preparar_entrada(mensagem, historico, self.baldes, self.max_atual, self.max_historico)
        hs = self._representar(entrada)
        atuais = [i for i, offset in enumerate(entrada["offsets"]) if offset is not None]
        indices_pool = atuais or [len(entrada["offsets"]) - 1]
        if self.np is not None:
            selecionados = hs[indices_pool]
            scores = (selecionados @ self.pesos["q"]).tolist()
            atencao = softmax(scores)
            pool = (selecionados * self.np.asarray(atencao)[:, None]).sum(axis=0)
            logits = (pool @ self.pesos["A"] + self.pesos["ba"]).tolist()
            tags = [softmax((hs[i] @ self.pesos["S"] + self.pesos["bs"]).tolist()) for i in atuais]
        else:
            scores = [sum(a * b for a, b in zip(hs[i], self.pesos["q"])) for i in indices_pool]
            atencao = softmax(scores)
            pool = [sum(peso * hs[i][j] for peso, i in zip(atencao, indices_pool)) for j in range(2 * self.ocultos)]
            logits = [a + b for a, b in zip(_produto(pool, self.pesos["A"]), self.pesos["ba"])]
            tags = [softmax([a + b for a, b in zip(_produto(hs[i], self.pesos["S"]), self.pesos["bs"])]) for i in atuais]
        probabilidades = softmax([x / self.temperatura for x in logits])
        ordem = sorted(range(len(probabilidades)), key=lambda i: probabilidades[i], reverse=True)
        escolhido = ordem[0]
        confianca = probabilidades[escolhido]
        margem = confianca - probabilidades[ordem[1]]
        rota, confianca_rota, margem_rota, probabilidades_rota = None, 0.0, 0.0, []
        if self.tem_rota:
            if self.np is not None:
                logits_rota = (pool @ self.pesos["L"] + self.pesos["bl"]).tolist()
            else:
                logits_rota = [a + b for a, b in zip(_produto(pool, self.pesos["L"]), self.pesos["bl"])]
            probabilidades_rota = softmax([x / self.temperatura_rota for x in logits_rota])
            ordem_rota = sorted(range(len(ROTAS)), key=lambda i: probabilidades_rota[i], reverse=True)
            rota = ROTAS[ordem_rota[0]]
            confianca_rota = probabilidades_rota[ordem_rota[0]]
            margem_rota = confianca_rota - probabilidades_rota[ordem_rota[1]]
        bio = decodificar_bio(tags, self.papeis)
        spans, inicio_tag = [], None
        for j in range(len(bio) + 1):
            tag = bio[j] if j < len(bio) else 0
            if inicio_tag is not None and (tag == 0 or tag % 2 or tag != bio[inicio_tag] + 1):
                inicio = entrada["offsets"][atuais[inicio_tag]][0]
                fim = entrada["offsets"][atuais[j - 1]][1]
                seguranca = math.exp(sum(math.log(max(tags[k][bio[k]], 1e-12)) for k in range(inicio_tag, j)) / (j - inicio_tag))
                if seguranca >= self.limiar_span:
                    spans.append({"papel": self.papeis[(bio[inicio_tag] - 1) // 2],
                                  "inicio": inicio, "fim": fim, "texto": mensagem[inicio:fim], "confianca": seguranca})
                inicio_tag = None
            if tag and tag % 2:
                inicio_tag = j
        return {"ato": self.atos[escolhido], "confianca": confianca, "margem": margem,
                "aceita": bool(atuais) and not entrada["contexto_truncado"] and
                           confianca >= self.limiar and margem >= self.margem_minima,
                "spans": spans, "distribuicao": dict(zip(self.atos, probabilidades)),
                "rota": rota, "confianca_rota": confianca_rota, "margem_rota": margem_rota,
                "distribuicao_rotas": dict(zip(ROTAS, probabilidades_rota)),
                "aceita_rota": bool(atuais) and not entrada["contexto_truncado"] and self.tem_rota and
                               confianca_rota >= self.limiar_rota and margem_rota >= self.margem_rota,
                "contexto_truncado": entrada["contexto_truncado"],
                "tokens_atuais": entrada["tokens_atuais"], "historico_tokens": entrada["historico_tokens"]}


@lru_cache(maxsize=2)
def carregar(caminho, mtime):
    from arquivos_contextuais import ler_json
    return CompreensaoNeural(ler_json(caminho))


def caminho_padrao():
    from arquivos_contextuais import localizar
    return localizar(Path(__file__).with_name("rede_compreensao.json"))
