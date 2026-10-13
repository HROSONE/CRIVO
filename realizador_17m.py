"""Voz experimental: o Transformer 17M da fase 3 diz o que o quadro decidiu.

Desligado por padrão. Só liga com as duas travas, como no #168:

  CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR=1   opt-in explícito;
  CRIVO_REALIZADOR_DIR=/caminho            pasta com pesos.pt e tokenizer.json;

e os pesos precisam ter exatamente o SHA-256 aprovado nos gates da fase 3
(`experimentos/fase3_realizador_20261012/RESULTADO.md`). Nada é baixado nem descoberto
sozinho.

Cada frase do realizador passa pela mesma métrica do blind da fase 3 (termina, não
repete, fatos copiados sem alteração, nome exato, ato realizado, nenhum nome inventado).
Se qualquer critério falhar, o CRIVO fala o texto de sempre. Depois disso, a revisão
(revisao.py) ainda confere a frase como confere qualquer outra.
"""
import hashlib
import importlib.util
import os
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PESOS_SHA256 = "745a2500615559d822f4fdb4d3d1c72850f64a9eac32a210bd6e5881f1d0b293"
TOKENIZER_SHA256 = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"
FORMATO = RAIZ / "experimentos" / "fase3_realizador_20261012" / "formato_fase3.py"
FORMATO_SHA256 = "d1b4ab176c89b29f4042d83ddd7df32f5c24ca09d253603992d836ce17d96abb"
MAX_NOVOS = 120


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


@lru_cache(maxsize=1)
def formato():
    """O mesmo formato_fase3.py do treino, conferido pelo SHA."""
    if _sha(FORMATO) != FORMATO_SHA256:
        raise RuntimeError("formato_fase3.py difere do usado no treino")
    spec = importlib.util.spec_from_file_location("formato_fase3", FORMATO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    trace.update(rascunho=texto, avaliacao={k: v for k, v in avaliacao.items() if k != "inventados"})
    if not avaliacao["tudo_ok"] or not texto:
        trace["motivo"] = "reprovado: " + ", ".join(k for k in ("terminou", "sem_repeticao", "fatos_fieis", "nome_exato",
                                                              "ato_ok", "sem_nome_inventado")
                                                   if avaliacao.get(k) is False)
        return ident, resposta, trace
    trace.update(usada=True, motivo="aprovado")
    return ident, texto, trace
