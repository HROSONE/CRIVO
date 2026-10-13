"""Voz experimental: o Transformer 17M da fase 3 diz o que o quadro decidiu.

Dois jeitos de rodar, com os mesmos pesos aprovados nos gates da fase 3
(`experimentos/fase3_realizador_20261012/RESULTADO.md`):

  NumPy (site e PC)   `artefatos/realizador_pt/pesos_numpy.npz` (float16, exportado de
                      pesos.pt com conferência NumPy × PyTorch), sem PyTorch nem a
                      biblioteca tokenizers. O servidor do site (api/chat.py) liga por
                      padrão; `CRIVO_DISABLE_REALIZADOR=1` desliga.
  PyTorch (pesquisa)  `CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR=1` e `CRIVO_REALIZADOR_DIR`
                      com pesos.pt e tokenizer.json.

Os dois exigem o SHA-256 exato; nada é baixado nem descoberto sozinho. O `Crivo()` da
linha de comando e dos testes continua desligado, a não ser com a variável acima.

Cada frase do realizador passa pela mesma métrica do blind da fase 3 (termina, não
repete, fatos copiados sem alteração, nome exato, ato realizado, nenhum nome inventado).
Se qualquer critério falhar, o CRIVO fala o texto de sempre. Depois disso, a revisão
(revisao.py) ainda confere a frase como confere qualquer outra.
"""
import hashlib
import importlib.util
import re
import os
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PESOS_SHA256 = "745a2500615559d822f4fdb4d3d1c72850f64a9eac32a210bd6e5881f1d0b293"
TOKENIZER_SHA256 = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"
FORMATO = RAIZ / "experimentos" / "fase3_realizador_20261012" / "formato_fase3.py"
FORMATO_SHA256 = "d1b4ab176c89b29f4042d83ddd7df32f5c24ca09d253603992d836ce17d96abb"
MAX_NOVOS = 120
# No site a função tem 20 s (vercel.json). Passado o prazo, a frase sai sem <fim>, a
# conferência recusa e fica o texto de sempre.
PRAZO_SITE = 8.0
PASTA_NUMPY = RAIZ / "artefatos" / "realizador_pt"
# O pacote do site não leva experimentos/: lá vale a cópia ao lado dos pesos, com o mesmo SHA.
FORMATO_SITE = PASTA_NUMPY / "formato_fase3.py"
NPZ_SHA256 = "57cc2da792344ce16ae9d74e023a547d4776f3f936daddc05c3ee393cdf4a5fe"  # exportação conferida (notebooks/exportar_realizador_numpy_colab.ipynb)
# Decisões do criador do projeto depois da porta conversacional v2 (13/10/2026): primeiro
# o opt-in experimental para todos os atos; depois, ligar no servidor do site (main e site
# público). A linha de comando e os testes continuam desligados por padrão.
# Depois do preview do PR #171, o criador achou a voz rara; a porta v3 abriu os atos que a fase 3
# já treinou onde o 17M é igual ou melhor que o texto de hoje. O 17M "respondendo tudo" foi testado
# e recusado (sem quadro ele mistura frases decoradas e entra em laço); decisão: "liga ele só no
# que ele é bom".
DECISAO_OPT_IN = {"data": "2026-10-13", "atos": "os que a porta v3 aprovou na leitura",
                  "porta": "fase4 v2: 0 regressões, 18/18; v3: 0 regressões, 19/19, voz em 19 de 47 turnos",
                  "site_publico": True, "promovido": "servidor do site", "padrao_linha_de_comando": "desligado",
                  "recusado": "17M respondendo tudo, sem quadro"}


def _ligado(nome):
    return os.environ.get(nome, "").strip().lower() in ("1", "true", "yes", "on", "sim")


def _sha(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def habilitado():
    return _ligado("CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR") and bool(os.environ.get("CRIVO_REALIZADOR_DIR", "").strip())


def desligado_no_site():
    return _ligado("CRIVO_DISABLE_REALIZADOR")


class RealizadorNumpy:
    """O mesmo realizador em NumPy, com cache de chaves e valores (uma passada por token)."""

    def __init__(self, pasta=PASTA_NUMPY, prazo=None):
        import json
        import numpy as np
        from pontuador_frases import BPE
        pasta = Path(pasta)
        npz = pasta / "pesos_numpy.npz"
        if NPZ_SHA256 is None or _sha(npz) != NPZ_SHA256 or _sha(pasta / "tokenizer.json") != TOKENIZER_SHA256:
            raise RuntimeError("pesos NumPy do realizador ausentes ou diferentes dos aprovados")
        pesos = np.load(npz)
        meta = json.loads(str(pesos["meta"]))
        if meta.get("origem_sha256") != PESOS_SHA256:
            raise RuntimeError("npz não foi exportado dos pesos aprovados")
        self.np = np
        self.p = {k: pesos[k].astype(np.float32) for k in pesos.files if k != "meta"}
        self.camadas, self.cabecas, self.contexto = meta["camadas"], meta["cabecas"], meta["contexto"]
        self.bpe = BPE(pasta / "tokenizer.json")
        self.esp = self.bpe.especiais
        self.proibidos = [v for k, v in self.esp.items() if k != "<fim>"]
        self.prazo = prazo

    def _norm(self, x, nome):
        np = self.np
        m = x.mean(-1, keepdims=True)
        v = ((x - m) ** 2).mean(-1, keepdims=True)
        return (x - m) / np.sqrt(v + 1e-5) * self.p[nome + ".weight"] + self.p[nome + ".bias"]

    def _passo(self, ids, inicio, cache):
        """Estados de `ids` (posições inicio…) usando e atualizando o cache de K e V."""
        import math
        from pontuador_frases import _erf
        np, p = self.np, self.p
        t = len(ids)
        x = p["embedding.weight"][ids] + p["posicao.weight"][inicio:inicio + t]
        h = self.cabecas
        d = x.shape[-1] // h
        for c in range(self.camadas):
            b = "blocos.%d." % c
            q, k, v = np.split(self._norm(x, b + "norm1") @ p[b + "qkv.weight"].T, 3, axis=-1)
            q, k, v = [a.reshape(t, h, d).transpose(1, 0, 2) for a in (q, k, v)]
            if c in cache:
                k = np.concatenate([cache[c][0], k], axis=1)
                v = np.concatenate([cache[c][1], v], axis=1)
            cache[c] = (k, v)
            total = k.shape[1]
            s = q @ k.transpose(0, 2, 1) / math.sqrt(d)
            # causal: a posição inicio+i vê até inicio+i
            mascara = np.arange(total)[None, :] > (inicio + np.arange(t))[:, None]
            s = np.where(mascara[None], -np.inf, s)
            s = np.exp(s - s.max(-1, keepdims=True))
            s /= s.sum(-1, keepdims=True)
            a = (s @ v).transpose(1, 0, 2).reshape(t, h * d)
            x = x + a @ p[b + "projecao.weight"].T
            m = self._norm(x, b + "norm2") @ p[b + "mlp.0.weight"].T + p[b + "mlp.0.bias"]
            m = 0.5 * m * (1.0 + _erf(m / math.sqrt(2.0), np))
            x = x + m @ p[b + "mlp.2.weight"].T + p[b + "mlp.2.bias"]
        return self._norm(x, "norm")

    def prompt(self, quadro, mensagem):
        """Igual a formato_fase3.montar_ids, sem a biblioteca tokenizers."""
        e = self.esp
        ids = ([e["<documento>"]] + self.bpe.codificar(formato().serializar_quadro(quadro)) + [e["<fim>"]]
               + [e["<usuario>"]] + self.bpe.codificar(mensagem) + [e["<fim>"], e["<assistente>"]])
        if len(ids) > self.contexto:
            raise ValueError("caso excede o contexto")
        return ids

    def realizar(self, quadro, mensagem):
        import time
        limite = time.monotonic() + self.prazo if self.prazo else None
        ids = self.prompt(quadro, mensagem)
        cache, saida = {}, []
        estado = self._passo(ids, 0, cache)[-1]
        pos = len(ids)
        for _ in range(min(MAX_NOVOS, self.contexto - len(ids))):
            lg = estado @ self.p["embedding.weight"].T
            lg[self.proibidos] = -1e9
            nxt = int(lg.argmax())
            if nxt == self.esp["<fim>"]:
                return self.bpe.decodificar(saida).strip(), True
            saida.append(nxt)
            if limite is not None and time.monotonic() > limite:
                break
            estado = self._passo([nxt], pos, cache)[-1]
            pos += 1
        return self.bpe.decodificar(saida).strip(), False


@lru_cache(maxsize=1)
def numpy_do_site():
    """Realizador NumPy embutido, ou None quando os pesos não estão no pacote."""
    try:
        return RealizadorNumpy(prazo=PRAZO_SITE)
    except Exception:
        return None


@lru_cache(maxsize=1)
def formato():
    """O mesmo formato_fase3.py do treino, conferido pelo SHA."""
    arquivo = FORMATO if FORMATO.is_file() else FORMATO_SITE
    if _sha(arquivo) != FORMATO_SHA256:
        raise RuntimeError("formato_fase3.py difere do usado no treino")
    spec = importlib.util.spec_from_file_location("formato_fase3", arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def status():
    """Estado público da voz experimental (para a API)."""
    return {"habilitado": habilitado(), "site": {"ligado": not desligado_no_site() and numpy_do_site() is not None,
                                                 "desligar": "CRIVO_DISABLE_REALIZADOR=1", "npz_sha256": NPZ_SHA256},
            "pesos_sha256": PESOS_SHA256, "tokenizer_sha256": TOKENIZER_SHA256,
            "travas_pesquisa": ["CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR=1", "CRIVO_REALIZADOR_DIR"],
            "decisao": DECISAO_OPT_IN, "external_ai": False}


class Realizador:
    def __init__(self, pasta):
        import linguagem_profunda as lp
        pasta = Path(pasta).expanduser().resolve()
        if _sha(pasta / "pesos.pt") != PESOS_SHA256 or _sha(pasta / "tokenizer.json") != TOKENIZER_SHA256:
            raise RuntimeError("pesos ou tokenizador do realizador diferem dos aprovados")
        self.lp = lp
        self.modelo, self.tokenizer, _ = lp.carregar(pasta, dispositivo="cpu")
        self.ids = {s: self.tokenizer.token_to_id(s) for s in lp.ESPECIAIS}
        self.proibidos = [self.ids[s] for s in lp.ESPECIAIS if s != "<fim>"]

    def realizar(self, quadro, mensagem):
        import torch
        prompt, _ = formato().montar_ids(self.lp, self.tokenizer, quadro, mensagem, None, self.modelo.config.contexto)
        ids, saida = list(prompt), []
        with torch.no_grad():
            for _ in range(min(MAX_NOVOS, self.modelo.config.contexto - len(ids))):
                lg = self.modelo(torch.tensor([ids]))[0][0, -1]
                lg[self.proibidos] = -1e9
                nxt = int(lg.argmax())
                if nxt == self.ids["<fim>"]:
                    return self.tokenizer.decode(saida).strip(), True
                saida.append(nxt)
                ids.append(nxt)
        return self.tokenizer.decode(saida).strip(), False


def relacao_certa(quadro, texto):
    """Nenhuma relação diferente da do quadro ("irmão" no lugar de "irmã") e nenhum
    "seu nome" quando o assunto é o nome de outra pessoa ou bicho (porta v1)."""
    from composicao_textual import normalizar
    from memoria_nomes import RELACOES
    rel = quadro.get("relacao")
    n = " " + normalizar(texto) + " "
    if rel is None:
        return True
    if re.search(r"\b(?:seu|sua|teu|tua) nome\b", n):
        return False
    alvo = normalizar(rel)
    return not any(re.search(r"\b" + re.escape(normalizar(r)) + r"\b", n) for r in RELACOES
                   if normalizar(r) != alvo and normalizar(r) not in alvo.split())


@lru_cache(maxsize=1)
def _carregado(pasta):
    return Realizador(pasta)


def aplicar(bot, fala, ident, resposta, realizador=None):
    """(ident, resposta, trace). Sem opt-in, sem quadro ou sem aprovação: o texto de sempre."""
    import quadro_fala
    trace = {"habilitado": bool(realizador) or habilitado(), "usada": False, "motivo": None, "quadro": None}
    if not trace["habilitado"]:
        trace["motivo"] = "desligado"
        return ident, resposta, trace
    quadro = quadro_fala.quadro_do_turno(bot, fala, ident, resposta)
    trace["quadro"] = quadro
    if quadro is None:
        trace["motivo"] = "sem_quadro"
        return ident, resposta, trace
    try:
        realizador = realizador or _carregado(os.environ["CRIVO_REALIZADOR_DIR"].strip())
        texto, terminou = realizador.realizar(quadro, fala)
    except Exception as erro:  # pesos ausentes, SHA errado, contexto excedido
        trace["motivo"] = "erro: %s" % type(erro).__name__
        return ident, resposta, trace
    avaliacao = formato().avaliar_saida({"quadro": quadro, "mensagem": fala}, texto, terminou)
    avaliacao["relacao_certa"] = relacao_certa(quadro, texto)
    trace.update(rascunho=texto, avaliacao={k: v for k, v in avaliacao.items() if k != "inventados"})
    if not avaliacao["tudo_ok"] or not avaliacao["relacao_certa"] or not texto:
        trace["motivo"] = "reprovado: " + ", ".join(k for k in ("terminou", "sem_repeticao", "fatos_fieis", "nome_exato",
                                                              "ato_ok", "sem_nome_inventado", "relacao_certa")
                                                   if avaliacao.get(k) is False)
        return ident, resposta, trace
    trace.update(usada=True, motivo="aprovado")
    return ident, texto, trace
