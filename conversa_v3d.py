"""Voz da conversa: o 17M da fase 5 v3 (variante D) responde no chat.

Decisão do criador do projeto (13/10/2026): "coloque no chat. ligue." A v3 D foi REPROVADA na
catraca (Grok 69,2% < 70,6%; urgência no blind v3 35/42) e nos critérios do chat (sentido 63,2%
no blind v3, abaixo de 90%). Ela está ligada por decisão do criador, não por aprovação; ver
experimentos/fase5_conversa_20261013/RESULTADO.md.

Como no treino da fase 5, o CRIVO entrega no contexto só o que é conferido:
  fatos    os fatos do acervo que a resposta de sempre mostra (só quando ela é exatamente esses fatos);
  assunto  o assunto de uma pergunta que o acervo não responde;
  nomes    o nome da pessoa e o nome que esta fala cita (perfil.nomes);
  cuidado  "saude" quando a fala toca em saúde.

Ficam com o texto de sempre:
- protocolo de crise e emergência de saúde (crise.py, antes de tudo) e a conversa depois de uma crise;
- operações explícitas: rotas, contas, código, memória da sessão, análise de texto, textos pedidos
  (poema, plano, história) e qualquer identificador fora de CONVERSA;
- respostas do acervo com mais que os fatos (um aviso ou uma oferta de continuar sumiriam).

Cada resposta do D passa pela conferência da fase 5 (formato_fase5.avaliar_saida: termina, não
repete, nenhum número ou nome inventado, fato copiado sem alteração, nome exato, marca de saúde).
Se falhar, fica o texto de sempre.

Site: `artefatos/conversa_v3d_pt/` (NumPy float16, exportado de pesos_D.pt com conferência NumPy ×
PyTorch em notebooks/exportar_fase5v3_numpy_colab.ipynb). Liga com a voz do site (web_core,
voz_17m); `CRIVO_DISABLE_CONVERSA_V3D=1` desliga. A linha de comando e os testes ficam desligados.
"""
import importlib.util
import os
import re
from functools import lru_cache
from pathlib import Path

import realizador_17m
from realizador_17m import RealizadorNumpy, TOKENIZER_SHA256, _sha

RAIZ = Path(__file__).resolve().parent
PASTA = RAIZ / "artefatos" / "conversa_v3d_pt"
PESOS_SHA256 = "a392edec3539fa63df3f38d55af199d18479b8d1625d7199f948f4e2aea8eaf8"   # pesos_D.pt (v3)
NPZ_SHA256 = "afb6c01fde0c42d809b15fe90908d78bad199fd959dff816e965bc76fe309e1e"
FORMATO_SHA256 = "932057afcb01d4ca3116c017d4363d048f73125b2e2613dce808e879105c17c3"  # o mesmo do treino v3
PRAZO_SITE = 7.0
MAX_CONTEXTO_TOKENS = 96   # igual a formato_fase5.montar_ids
MAX_PARES = 6

DECISAO = {"data": "2026-10-13", "decisao": "ligar no chat por decisão do criador",
           "frase": "coloque no chat. ligue.", "aprovada": False,
           "catraca": "reprovada: grok 0,6925 < 0,7063; urgência blind v3 35/42 < 0,95",
           "chat": "reprovada: sentido blind v3 0,632, paráfrases 0,752, grok 0,692 (pedido 0,90)",
           "protecao": "crise.py (crise e emergência de saúde) responde antes; conferência por frase"}

# Identificadores de conversa em que o D fala. O resto fica com o texto de sempre.
CONVERSA = ("social:", "nocao:", "memoria:nome", "conversa:relato", "conversa:reflexao", "conversa:esclarecer",
            "conversa:abertura", "conversa:repeticao", "conversa:reparo", "conversa:perspectiva",
            "conversa:opiniao_terceiro", "conversa:tema", "conversa:situada_")
CONVERSA_EXATOS = {"conversa:memoria", "fora", "duvida"}

_SAUDE = re.compile(
    r"\b(?:remedio|febre|tontura|tonto|tonta|enjoo|vomit\w*|diarreia|gripe|resfriado|tosse|insonia|"
    r"pressao alta|pressao baixa|dor de (?:cabeca|barriga|garganta|dente|estomago)|medico|doenca|doente|"
    r"sintoma\w*|peito apertado|aperto no peito|coracao (?:ta |esta )?disparado|machuquei|machucado|"
    r"torci|alergia|infeccao)\b")
_PEITO = re.compile(r"\bpeito\b|\bcoracao\b")


def desligado_no_site():
    return os.environ.get("CRIVO_DISABLE_CONVERSA_V3D", "").strip().lower() in ("1", "true", "yes", "on", "sim")


@lru_cache(maxsize=1)
def formato():
    """O formato_fase5.py do treino v3, conferido pelo SHA."""
    arquivo = RAIZ / "experimentos" / "fase5_conversa_20261013" / "formato_fase5.py"
    if not arquivo.is_file():
        arquivo = PASTA / "formato_fase5.py"   # o pacote do site não leva experimentos/
    if _sha(arquivo) != FORMATO_SHA256:
        raise RuntimeError("formato_fase5.py difere do usado no treino da v3")
    spec = importlib.util.spec_from_file_location("formato_fase5", arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ConversaNumpy(RealizadorNumpy):
    """O mesmo Transformer 17M em NumPy, com os pesos da v3 D e o prompt da fase 5."""

    def __init__(self, pasta=PASTA, prazo=None):
        import json
        import numpy as np
        from pontuador_frases import BPE
        pasta = Path(pasta)
        npz = pasta / "pesos_numpy.npz"
        if _sha(npz) != NPZ_SHA256 or _sha(pasta / "tokenizer.json") != TOKENIZER_SHA256:
            raise RuntimeError("pesos NumPy da v3 D ausentes ou diferentes dos registrados")
        pesos = np.load(npz)
        meta = json.loads(str(pesos["meta"]))
        if meta.get("origem_sha256") != PESOS_SHA256:
            raise RuntimeError("npz não foi exportado de pesos_D.pt da v3")
        self.np = np
        self.p = {k: pesos[k].astype(np.float32) for k in pesos.files if k != "meta"}
        self.camadas, self.cabecas, self.contexto = meta["camadas"], meta["cabecas"], meta["contexto"]
        self.bpe = BPE(pasta / "tokenizer.json")
        self.esp = self.bpe.especiais
        self.proibidos = [v for k, v in self.esp.items() if k != "<fim>"]
        self.prazo = prazo

    def prompt_conversa(self, ctx, historico, mensagem):
        """Igual a formato_fase5.montar_ids (com lp.fonte_dialogo), sem a biblioteca tokenizers."""
        e = self.esp
        cid = self.bpe.codificar(formato().serializar_contexto(ctx))[:MAX_CONTEXTO_TOKENS]
        doc = [e["<documento>"]] + cid + [e["<fim>"]]
        atual = [e["<usuario>"]] + self.bpe.codificar(mensagem) + [e["<fim>"], e["<assistente>"]]
        limite = self.contexto - len(doc) - 100
        if len(atual) > limite:
            raise ValueError("mensagem excede o contexto")
        fonte = list(atual)
        for i in range(len(historico) - 1, -1, -1):
            papel = "<usuario>" if i % 2 == 0 else "<assistente>"
            seg = [e[papel]] + self.bpe.codificar(historico[i]) + [e["<fim>"]]
            if len(seg) + len(fonte) > limite:
                break
            fonte = seg + fonte
        return doc + fonte

    def conversar(self, ctx, historico, mensagem):
        """(texto, terminou), com decodificação gulosa como no treino."""
        import time
        ids = self.prompt_conversa(ctx, historico, mensagem)
        limite = time.monotonic() + self.prazo if self.prazo else None
        cache, saida = {}, []
        estado = self._passo(ids, 0, cache)[-1]
        pos = len(ids)
        for _ in range(min(realizador_17m.MAX_NOVOS, self.contexto - len(ids))):
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
    """A v3 D embutida, ou None quando os pesos não estão no pacote."""
    try:
        return ConversaNumpy(prazo=PRAZO_SITE)
    except Exception:
        return None


def _fatos_do_turno(bot, ident, resposta):
    """Os fatos do acervo quando a resposta de sempre é exatamente eles (como em quadro_fala)."""
    from composicao_textual import normalizar
    ctx = getattr(bot, "contexto_textual", None)
    if ctx is None or not getattr(ctx, "exibidos", None) or ident.startswith(("escrita:", "leitura:")):
        return None
    temas = {t for t, _ in ctx.exibidos}
    if len(temas) != 1 or len(ctx.exibidos) > 2:
        return None
    from curriculo_mundo import texto_fato
    item = bot.compositor.itens.get(next(iter(temas)))
    if item is None or any(item["fatos"][i].get("natureza") == "religioso" for _, i in ctx.exibidos):
        return None
    fatos = [texto_fato(item["fatos"][i]) for _, i in ctx.exibidos]
    sobra = normalizar(resposta)
    for f in fatos:
        sobra = sobra.replace(normalizar(f), " ")
    if (all(normalizar(f) in normalizar(resposta) for f in fatos) and len(re.findall(r"\w+", sobra)) <= 3
            and not getattr(bot, "oferta_pendente", None)):
        return fatos
    return None


def contexto_do_turno(bot, fala, ident, resposta):
    """(ctx, exigir) da fase 5 para este turno, ou (None, motivo) quando o D não deve falar."""
    from composicao_textual import normalizar
    if not isinstance(fala, str) or not isinstance(resposta, str) or not fala.strip():
        return None, "sem_texto"
    if ident.startswith("crise") or getattr(bot, "crise", None):
        return None, "crise"
    if getattr(bot, "ultima_rota_natural", None) is not None:
        return None, "operacao_explicita"
    ctx, exigir = {}, {}
    fatos = _fatos_do_turno(bot, ident, resposta)
    if fatos:
        ctx["fatos"], exigir["fato"] = fatos, True
    elif not (ident in CONVERSA_EXATOS or ident.startswith(CONVERSA)):
        return None, "fora_da_conversa"
    if ident == "fora":
        import quadro_fala
        pergunta = quadro_fala.pergunta_aberta(fala)
        if not pergunta:
            return None, "fora_sem_pergunta"
        ctx["assunto"] = pergunta
        exigir["marcas"] = ["nao_sei"]
    nomes = {}
    pessoa = getattr(getattr(getattr(bot, "conversacao", None), "dialogo", None), "dados", {}).get("nome")
    if pessoa:
        nomes["você"] = pessoa
    perfil_nomes = getattr(getattr(bot, "perfil", None), "nomes", None) or {}
    evento = getattr(bot, "evento_nome", None)
    if evento and evento.get("fala") == fala and evento.get("nome"):
        nomes[evento["rel"]] = evento["nome"]
    n = " " + normalizar(fala) + " "
    for rel, nome in perfil_nomes.items():
        if " " + normalizar(rel) + " " in n:
            nomes[rel] = nome
    if nomes:
        ctx["nomes"] = nomes
        # O nome que o texto de sempre diz, o D também tem que dizer, igual.
        exigir["nomes"] = [v for v in nomes.values() if re.search(r"(?<![\w-])" + re.escape(v) + r"(?![\w-])", resposta)]
    nf = normalizar(fala)
    if _SAUDE.search(nf):
        ctx["cuidado"] = "saude"
        exigir.setdefault("marcas", []).append("urgente" if _PEITO.search(nf) else "saude")
    return ctx, exigir


def aplicar(bot, fala, ident, resposta, modelo):
    """(ident, resposta, trace). Sem modelo, fora da conversa ou reprovada: o texto de sempre."""
    trace = {"ligada": modelo is not None, "usada": False, "motivo": None, "decisao": "criador; v3 D reprovada"}
    if modelo is None:
        trace["motivo"] = "desligada"
        return ident, resposta, trace
    ctx, exigir = contexto_do_turno(bot, fala, ident, resposta)
    if ctx is None:
        trace["motivo"] = exigir
        return ident, resposta, trace
    historico = []
    for f, r in (getattr(bot, "pares_conversa", None) or [])[-MAX_PARES:]:
        historico += [f, r]
    try:
        texto, terminou = modelo.conversar(ctx, historico, fala)
    except Exception as erro:  # contexto excedido, pesos ausentes
        trace["motivo"] = "erro: %s" % type(erro).__name__
        return ident, resposta, trace
    caso = {"contexto": ctx, "mensagem": fala, "historico": historico, "exigir": exigir}
    av = formato().avaliar_saida(caso, texto, terminou)
    trace.update(contexto=ctx, rascunho=texto)
    if not av["tudo_ok"] or not texto:
        trace["motivo"] = "reprovada: " + ", ".join(k for k, v in av.items() if v is False)
        return ident, resposta, trace
    trace.update(usada=True, motivo="conferida")
    return ident, texto, trace


def status():
    """Estado público da voz da conversa (para a API)."""
    return {"site": {"ligada": not desligado_no_site() and numpy_do_site() is not None,
                     "desligar": "CRIVO_DISABLE_CONVERSA_V3D=1", "npz_sha256": NPZ_SHA256},
            "pesos_sha256": PESOS_SHA256, "tokenizer_sha256": TOKENIZER_SHA256, "decisao": DECISAO,
            "external_ai": False}
