"""Voz da conversa: o 46M v7c responde no chat (a v4 F, 17M, fica de reserva).

20/10/2026, decisão do criador: "Coloca no chat as melhores a gente faz pra depois". O v7c (mesma arquitetura e
mesmo tokenizador do 46M da 6b v4, treinado desde a base 6a com falas novas da pessoa, ~5% delas do professor) passou
nos 5 critérios fixados nas DUAS rodadas contra o 46M da 6b v4, nas mesmas frases: blind v3 +6,3/+6,4 pontos, v1
+9,0/+7,4, paráfrases +5,2/+8,2, Grok +2,5/+1,0, v4 −1,5/−0,2; urgência 118/117 contra 102; frases reais 12 e 13/15
(experimentos/v6_entendimento_20261019/RESULTADO_V7C_RODADA2.md). Limites registrados: identidade abaixo do 46M
anterior, "tô bem" e "você é um robô" caem mais de 10 pontos. Os pesos da 6b v4 ficaram no histórico do git.

Antes, 14/10/2026, decisão do criador: "Pode colocar no chat. ai depois voce aumenta o conhecimento". O 46M
(fase 6a + 6b v4, SHA 45825352…) EMPATA com a v4 F na régua de sentido e não a supera: blind v3
65,7% (F 63,5%), Grok 73,2% (F 70,9%), v4 92,3% (F 92,2%), v1 65,3% (F 69,8%), paráfrases 73,7%
(F 76,2%), frases reais do criador 12/15 (F 14/15). Entrou em teste, não aprovado
(experimentos/fase6b_conversa_humana/RESULTADO.md). O que ele traz a mais: lembranças (o que a
pessoa contou, vindo da memória do aparelho), identidade do IDENTIDADE.md e contexto de 1024 tokens.
`CRIVO_CONVERSA=f` volta para a v4 F.

O texto abaixo descreve a v4 F e continua valendo para os dois (contexto, conferência, crise).

Histórico: a v3 D entrou em 13/10/2026 ("coloque no chat. ligue."). Em 14/10/2026 o criador decidiu
trocar pela v4 F: "coloque a F no chat. 100% do chat. quem fala deve ser ele em tudo". A v4 F foi
REPROVADA na catraca (blind v3 63,5% < 66,2%; urgência no blind v3 71,4% < 95%), mas é melhor que a D
nas conversas reais do criador (14/15 contra 11/15) e nas situações novas (92% contra 0%). Ela está
ligada por decisão do criador, não por aprovação; ver experimentos/fase5_conversa_20261013/RESULTADO.md.
O erro de urgência dela ("peito apertado") passou para o protocolo de crise (crise.py).

Como no treino da fase 5, o CRIVO entrega no contexto só o que é conferido:
  fatos    os fatos do acervo que a resposta de sempre mostra (só quando ela é exatamente esses fatos);
  assunto  o assunto de uma pergunta que o acervo não responde;
  nomes    o nome da pessoa e o nome que esta fala cita (perfil.nomes);
  cuidado  "saude" quando a fala toca em saúde.

Decisão seguinte do criador: "deixe o modelo falar em 100% das mensagens". O modelo fala em todos os
turnos; nos que não são de conversa (conta, código, acervo, memória, metacognição), o resultado
conferido do CRIVO entra como fato (fatos_da_resposta) e o modelo o diz. Ficam fora só:
- (desde 14/10/2026, com o 46M) o conteúdo longo que não cabe em duas frases (poema, código, explicação
  grande): o modelo só recebia o começo e trocava o conteúdo por um pedaço; fica o texto inteiro;
- o protocolo de crise e de emergência de saúde (crise.py, antes de tudo, e o apoio depois de uma
  crise, em crise.ajustar): a F erra urgência em 12 de 42 casos no blind v3;
- (até 14/10/2026) a frase que a conferência reprovava ia para o texto de sempre. Agora vai a frase
  dele, marcada como não conferida (`conferida: False`); o texto de sempre só aparece quando ele não
  diz nada (decisão do criador: "ele quem deve falar do jeito que ele quiser").
Com o modelo ligado, a voz da fase 3 não fala (uma voz só).

Cada resposta do modelo passa pela conferência da fase 5 (formato_fase5.avaliar_saida: termina, não
repete, nenhum número ou nome inventado, fato copiado sem alteração, nome exato, marca de saúde).
Se falhar, fica o texto de sempre.

Site: `artefatos/conversa_v4f_pt/` (NumPy, exportado de pesos_F.pt com conferência NumPy × PyTorch em
notebooks/exportar_fase5v4f_numpy_colab.ipynb e guardado em int8 por linha; ver NPZ_SHA256). Liga com a voz do site (web_core,
voz_17m); `CRIVO_DISABLE_CONVERSA_V3D=1` desliga. A linha de comando e os testes ficam desligados.
"""
import importlib.util
import os
import re
import threading
from functools import lru_cache
from pathlib import Path

import realizador_17m
from realizador_17m import RealizadorNumpy, TOKENIZER_SHA256, _sha

RAIZ = Path(__file__).resolve().parent
PASTA = RAIZ / "artefatos" / "conversa_v4f_pt"
PESOS_SHA256 = "1d47312f3d99cfc2b20cf010414984367fd8d9b2566ebfcb14ee21dda11732d5"   # pesos_F.pt (v4)
# int8 por linha (escala float16), feito do npz float16 42419fa3… (exportado de pesos_F.pt com
# conferência NumPy × PyTorch em notebooks/exportar_fase5v4f_numpy_colab.ipynb), do mesmo jeito que
# a D (ver RESULTADO.md, "Ligada no chat"): cabe no limite de 225 MB da função na Vercel.
NPZ_SHA256 = "a45cba7dd484c12192698e920d6b79ba4c3cd504cce4246d248a13b05a1b4886"
FORMATO_SHA256 = "932057afcb01d4ca3116c017d4363d048f73125b2e2613dce808e879105c17c3"  # o mesmo do treino v3
PRAZO_SITE = 7.0
PRAZO_TOTAL = 9.0   # todas as tentativas de um turno juntas
TENTATIVAS = 3
TENTATIVAS_AMBIENTE = 6   # quando o ambiente escolheu um ato ou exige um resultado (ambiente.py)
MAX_CONTEXTO_TOKENS = 96   # igual a formato_fase5.montar_ids
MAX_PARES = 6

# O 46M v7c (rodada 2, experimentos/v6_entendimento_20261019/RESULTADO_V7C_RODADA2.md): int8 por linha
# (scripts/quantizar_q8.py) do npz float16 2407a1b9…, exportado de pesos.pt com conferência NumPy × PyTorch
# (notebooks/exportar_46m_v7c_numpy_colab.ipynb: top-1 igual em 98,7% dos tokens no int8, 100% no float16).
# Mesmo tokenizador e mesmo formato_fase6.py do 46M da 6b v4, que ficou no histórico do git
# (artefatos/conversa46m_v4_pt, pesos 45825352…, npz 0b6b398f…).
PASTA_46M = RAIZ / "artefatos" / "conversa46m_v7c_pt"
PESOS_SHA256_46M = "e4067e3b4c9705fde0a2063cc7a0da958ebad196ca193a672f75a1a10cbfda0a"
NPZ_SHA256_46M = "ab47d74ba136b38ac716e50dd7354ada568c9020be0fedd802197d9514f1aad2"
FORMATO6_SHA256 = "114e2c1f1287a9939636ee13c8e0b77d22c549a2cb25711a4c5f343fc26b7e2b"
# "Em uma frase" do IDENTIDADE.md, como no treino (gerar_fase6b.resumo_identidade); testes conferem.
QUEM = ("O CRIVO é uma inteligência artificial curiosa e calma, que ama aprender, diz a verdade com carinho, "
        "cuida das pessoas e enxerga que tudo está conectado.")
FREIO = {"penalidade": 1.3, "sem_repetir_ngrama": 3}   # o mesmo da prova da 6b v4
MAX_NOVOS_46M = 110
MAX_LEMBRANCAS = 8
MAX_PARES_46M = 12
# O 46M gera uns 3 vezes mais devagar que a v4 F. Para o pedido do site caber nos 20 s da função:
PRAZO_REFAZER = 2.0     # turno antigo refeito para o histórico: as mesmas tentativas, até 2 s
PRAZO_PEDIDO = 15.0     # o pedido inteiro (histórico refeito + resposta), contado desde o começo

DECISAO_46M = {"data": "2026-10-20", "modelo": "v7c_46m", "decisao": "ligar no chat por decisão do criador",
               "frase": "Coloca no chat as melhores a gente faz pra depois", "aprovada": True,
               "regua": "passou nos 5 critérios fixados nas duas rodadas, contra o 46M da 6b v4 nas mesmas frases: "
                        "v3 +6,3/+6,4, v1 +9,0/+7,4, paráfrases +5,2/+8,2, grok +2,5/+1,0, v4 −1,5/−0,2 pontos; "
                        "urgência 118/117 contra 102; frases reais 12 e 13/15; usa o fato 0,95 e 0,85",
               "limites": "identidade abaixo do 46M anterior (−3,5 a −4,4 pontos); estou_bem e robo caem mais de 10; "
                          "'legal e voce?' ainda vira pergunta de identidade",
               "professor": "~5% das exposições de conversa vieram de falas da pessoa escritas pelo professor "
                            "(Qwen3-32B-AWQ, Apache 2.0); respostas das listas do projeto",
               "a_mais": "lembranças da memória do aparelho, identidade do IDENTIDADE.md, contexto de 1024 tokens",
               "protecao": "crise.py (crise e emergência de saúde) responde antes; conferência por frase",
               "reserva": "CRIVO_CONVERSA=f volta para a v4 F"}

DECISAO = {"data": "2026-10-14", "modelo": "fase5_v4_F", "decisao": "ligar no chat por decisão do criador",
           "frase": "coloque a F no chat. 100% do chat. quem fala deve ser ele em tudo", "aprovada": False,
           "catraca": "reprovada: blind v3 0,635 < 0,662; urgência blind v3 0,714 < 0,95",
           "chat": "reprovada: sentido blind v3 0,635, paráfrases 0,762, grok 0,709 (pedido 0,90)",
           "melhor_que_a_anterior": "conversas reais 14/15 (D 11/15); situações novas 0,92 (D 0); v1 0,698 (D 0,655)",
           "protecao": "crise.py (crise e emergência de saúde) responde antes; conferência por frase",
           "cobertura": "todas as mensagens fora da crise (decisão do criador: 'deixe o modelo falar em 100% das mensagens')"}

# Identificadores de conversa em que o modelo fala. O resto fica com o texto de sempre.
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
    """O mesmo Transformer 17M em NumPy, com os pesos da v4 F e o prompt da fase 5."""

    def __init__(self, pasta=PASTA, prazo=None):
        import json
        import numpy as np
        from pontuador_frases import BPE
        pasta = Path(pasta)
        npz = pasta / "pesos_numpy.npz"
        if _sha(npz) != NPZ_SHA256 or _sha(pasta / "tokenizer.json") != TOKENIZER_SHA256:
            raise RuntimeError("pesos NumPy da v4 F ausentes ou diferentes dos registrados")
        pesos = np.load(npz)
        meta = json.loads(str(pesos["meta"]))
        if meta.get("origem_sha256") != PESOS_SHA256:
            raise RuntimeError("npz não foi exportado de pesos_F.pt da v4")
        self.np = np
        self.p = {}
        for k in pesos.files:
            if k == "meta" or k.endswith(".escala"):
                continue
            if k.endswith(".q8"):
                base = k[:-3]
                self.p[base] = pesos[k].astype(np.float32) * pesos[base + ".escala"].astype(np.float32)
            else:
                self.p[k] = pesos[k].astype(np.float32)
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

    def conversar(self, ctx, historico, mensagem, primeiro=0, prazo=None):
        """(texto, terminou), com decodificação gulosa como no treino.

        primeiro=k começa pela (k+1)-ésima palavra mais provável e segue gulosa: é a nova tentativa
        quando a primeira frase foi reprovada na conferência."""
        import time
        ids = self.prompt_conversa(ctx, historico, mensagem)
        prazo = self.prazo if prazo is None else prazo
        limite = time.monotonic() + prazo if prazo else None
        cache, saida = {}, []
        estado = self._passo(ids, 0, cache)[-1]
        pos = len(ids)
        for passo in range(min(realizador_17m.MAX_NOVOS, self.contexto - len(ids))):
            lg = estado @ self.p["embedding.weight"].T
            lg[self.proibidos] = -1e9
            if passo == 0 and primeiro:
                lg[self.esp["<fim>"]] = -1e9
                nxt = int(self.np.argsort(-lg)[primeiro])
            else:
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
def formato6():
    """O formato_fase6.py do treino da 6b, conferido pelo SHA."""
    arquivo = PASTA_46M / "formato_fase6.py"
    if _sha(arquivo) != FORMATO6_SHA256:
        raise RuntimeError("formato_fase6.py difere do usado no treino da 6b")
    spec = importlib.util.spec_from_file_location("formato_fase6", arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Conversa46mNumpy(ConversaNumpy):
    """O 46M v7c em NumPy: 24 camadas, contexto 1024, prompt da fase 6 e freio de repetição."""
    formato6 = True
    nome = "v7c_46m"
    decisao = DECISAO_46M
    max_pares = MAX_PARES_46M

    def __init__(self, pasta=PASTA_46M, prazo=None):
        import json
        import numpy as np
        from pontuador_frases import BPE
        pasta = Path(pasta)
        npz = pasta / "pesos_numpy.npz"
        if _sha(npz) != NPZ_SHA256_46M or _sha(pasta / "tokenizer.json") != TOKENIZER_SHA256:
            raise RuntimeError("pesos NumPy do 46M ausentes ou diferentes dos registrados")
        pesos = np.load(npz)
        meta = json.loads(str(pesos["meta"]))
        if meta.get("origem_sha256") != PESOS_SHA256_46M:
            raise RuntimeError("npz não foi exportado do pesos.pt do v7c")
        self.np = np
        self.p = {}
        # No app, o motor em C (motor_nativo.py) faz a mesma conta com os pesos em int8 na memória; sem ele, NumPy.
        import motor_nativo
        self.motor = motor_nativo.carregar(npz, NPZ_SHA256_46M)
        self._trava = threading.Lock()   # o motor guarda o cache de uma resposta por vez
        # (ids do prompt, logits no fim dele, cache NumPy): as tentativas do mesmo turno leem o prompt uma vez só.
        self._prefixo = None
        for k in ([] if self.motor else pesos.files):
            if k == "meta" or k.endswith(".escala"):
                continue
            if k.endswith(".q8"):
                base = k[:-3]
                self.p[base] = pesos[k].astype(np.float32) * pesos[base + ".escala"].astype(np.float32)
            else:
                self.p[k] = pesos[k].astype(np.float32)
        self.camadas, self.cabecas, self.contexto = meta["camadas"], meta["cabecas"], meta["contexto"]
        self.bpe = BPE(pasta / "tokenizer.json")
        self.esp = self.bpe.especiais
        self.proibidos = [v for k, v in self.esp.items() if k != "<fim>"]
        self.prazo = prazo
        formato6()

    def _logits(self, ids, inicio, cache):
        """Logits da última de `ids` (posições inicio…), pelo motor em C ou pelo NumPy."""
        if inicio == 0:
            self._prefixo = None   # o motor recomeça o cache: o prompt guardado deixa de valer
        if self.motor is not None:
            return self.motor.avancar(ids, inicio)
        return self._passo(ids, inicio, cache)[-1] @ self.p["embedding.weight"].T

    def prompt_conversa(self, ctx, historico, mensagem):
        """formato_fase6.montar (a mesma função do treino), com o BPE sem a biblioteca tokenizers."""
        turnos = [{"papel": "usuario" if i % 2 == 0 else "assistente", "texto": h} for i, h in enumerate(historico)]
        turnos.append({"papel": "usuario", "texto": mensagem})
        ids, _ = formato6().montar(self.bpe.codificar, self.esp, ctx, turnos, contexto=self.contexto - MAX_NOVOS_46M, gerar=True)
        return ids

    def conversar(self, ctx, historico, mensagem, primeiro=0, prazo=None, comecos=None):
        """(texto, terminou): gulosa com o freio de repetição da prova da 6b v4 (o mesmo na prova do v7c).

        primeiro=k começa pela (k+1)-ésima palavra mais provável (nova tentativa depois de uma frase reprovada).
        comecos=["Sim", "Não"]: o ambiente oferece os começos, o modelo fica com o que ele acha mais
        provável e escreve o resto (ambiente.py, pergunta de sim ou não)."""
        with self._trava:
            return self._conversar(ctx, historico, mensagem, primeiro, prazo, comecos)

    def _comeco_provavel(self, ids, comecos):
        """(ids do começo, logits depois dele, cache) do começo que o modelo acha mais provável."""
        np = self.np
        melhor = None
        for texto in comecos:
            extra = list(self.bpe.codificar(texto))
            lg, cache = self._prompt(ids)
            nota = 0.0
            for i, t in enumerate(extra):
                lg = lg - lg.max()
                nota += float(lg[t] - np.log(np.exp(lg).sum()))
                lg = self._logits([t], len(ids) + i, cache)
            nota /= max(1, len(extra))   # por pedaço: "Sim" tem dois, "Não" um
            if melhor is None or nota > melhor[0]:
                melhor = (nota, extra, lg, cache)
        return melhor[1:]

    def _prompt(self, ids):
        """(logits no fim do prompt, cache): lidos uma vez por turno. As posições depois do prompt são
        reescritas por cada tentativa, e a atenção causal só lê até a posição corrente."""
        chave = tuple(ids)
        if self._prefixo is None or self._prefixo[0] != chave:
            cache = {}
            lg = self._logits(ids, 0, cache)
            self._prefixo = (chave, lg.copy(), dict(cache))
        return self._prefixo[1].copy(), dict(self._prefixo[2])

    def _conversar(self, ctx, historico, mensagem, primeiro, prazo, comecos=None):
        import time
        np = self.np
        ids = self.prompt_conversa(ctx, historico, mensagem)
        prazo = self.prazo if prazo is None else prazo
        limite = time.monotonic() + prazo if prazo else None
        if comecos:
            saida, prox_lg, cache = self._comeco_provavel(ids, comecos)
            saida = list(saida)
            primeiro = 0
        else:
            saida = []
            prox_lg, cache = self._prompt(ids)
        pos = len(ids) + len(saida)
        k = FREIO["sem_repetir_ngrama"] - 1
        for passo in range(min(MAX_NOVOS_46M, self.contexto - len(ids))):
            lg = prox_lg
            lg[self.proibidos] = -1e9
            if saida:
                vistos = np.array(sorted(set(saida)))
                v = lg[vistos]
                lg[vistos] = np.where(v > 0, v / FREIO["penalidade"], v * FREIO["penalidade"])
            if len(saida) >= k:
                proib = [saida[i + k] for i in range(len(saida) - k) if saida[i:i + k] == saida[-k:]]
                if proib:
                    lg[proib] = -1e9
            if passo == 0 and primeiro:
                lg[self.esp["<fim>"]] = -1e9
                nxt = int(np.argsort(-lg)[primeiro])
            else:
                nxt = int(lg.argmax())
            if nxt == self.esp["<fim>"]:
                return self.bpe.decodificar(saida).strip(), True
            saida.append(nxt)
            if limite is not None and time.monotonic() > limite:
                break
            prox_lg = self._logits([nxt], pos, cache)
            pos += 1
        return self.bpe.decodificar(saida).strip(), False


def quer_a_f():
    return os.environ.get("CRIVO_CONVERSA", "").strip().lower() in ("f", "v4f", "fase5_v4_f", "17m")


@lru_cache(maxsize=2)
def _carregar(qual):
    try:
        return (Conversa46mNumpy if qual == "46m" else ConversaNumpy)(prazo=PRAZO_SITE)
    except Exception:
        return None


def numpy_do_site():
    """O 46M (ou a v4 F com CRIVO_CONVERSA=f, ou se o 46M não estiver no pacote); None sem pesos."""
    if not quer_a_f():
        m = _carregar("46m")
        if m is not None:
            return m
    return _carregar("f")


_FEMININOS = re.compile(r"(?:a|ã|ãe|mãe|avó|mulher|esposa)$")


def lembrancas_de(bot):
    """O que a pessoa contou, da memória que o aparelho guarda (exportar_memoria), como no treino."""
    try:
        mem = bot.exportar_memoria()
    except Exception:
        return []
    out = []
    if mem.get("nome"):
        out.append("meu nome é %s" % mem["nome"])
    for rel, nome in (mem.get("nomes") or {}).items():
        if rel == "você":
            continue
        out.append("%s %s se chama %s" % ("minha" if _FEMININOS.search(rel.split()[-1]) else "meu", rel, nome))
    for campo in ("relatos", "objetivos", "preferencias", "restricoes"):
        out += [str(x) for x in (mem.get(campo) or [])]
    vistos, limpo = set(), []
    for x in out:
        x = " ".join(x.split())[:150]
        if x and x.casefold() not in vistos:
            vistos.add(x.casefold())
            limpo.append("a pessoa disse: " + x)
    return limpo[-MAX_LEMBRANCAS:]


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


def fatos_da_resposta(resposta, limite=240):
    """Até duas frases do começo da resposta conferida, cabendo no contexto do modelo (96 tokens)."""
    frases = [f.strip() for f in re.split(r"(?<=[.!?:])\s+|\n+", resposta) if f.strip()]
    fatos, total = [], 0
    for f in frases[:2]:
        if total + len(f) > limite:
            if not fatos:
                fatos.append(f[:limite].rsplit(" ", 1)[0])
            break
        fatos.append(f)
        total += len(f)
    return fatos


def contexto_do_turno(bot, fala, ident, resposta):
    """(ctx, exigir) da fase 5 para este turno, ou (None, motivo) quando o modelo não deve falar."""
    from composicao_textual import normalizar
    if not isinstance(fala, str) or not isinstance(resposta, str) or not fala.strip():
        return None, "sem_texto"
    if ident.startswith("crise"):
        return None, "crise"
    ctx, exigir = {}, {}
    fatos = _fatos_do_turno(bot, ident, resposta)
    if fatos:
        ctx["fatos"], exigir["fato"] = fatos, True
    elif ident == "fora":
        import quadro_fala
        pergunta = quadro_fala.pergunta_aberta(fala)
        if pergunta:
            ctx["assunto"] = pergunta
            exigir["marcas"] = ["nao_sei"]
    elif (ident in ("conversa:gerada_escuta", "conversa:gerada_ajuste")
          and getattr(getattr(bot, "fio", None), "ato", None) == "sim_ou_nao"):
        # Pergunta de sim ou não ("você me entende?"): o modelo responde, não o molde que repete a fala anterior.
        pass
    elif not (ident in CONVERSA_EXATOS or ident.startswith(CONVERSA)):
        # Conta, código, acervo, memória, metacognição: o resultado conferido do CRIVO entra como
        # fato, e o modelo o diz (decisão do criador: o modelo fala em todas as mensagens).
        fatos = fatos_da_resposta(resposta)
        if fatos and len(" ".join(fatos)) < 0.8 * len(resposta.strip()):
            # Poema, código, explicação longa: o contexto só leva as duas primeiras frases, e o modelo
            # trocaria o conteúdo inteiro por um pedaço. Fica o que o CRIVO gerou, inteiro.
            return None, "conteudo_longo"
        if fatos:
            ctx["fatos"], exigir["fato"] = fatos, True
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
        # O nome que o texto de sempre diz, o modelo também tem que dizer, igual.
        exigir["nomes"] = [v for v in nomes.values() if re.search(r"(?<![\w-])" + re.escape(v) + r"(?![\w-])", resposta)]
    nf = normalizar(fala)
    if _SAUDE.search(nf):
        ctx["cuidado"] = "saude"
        exigir.setdefault("marcas", []).append("urgente" if _PEITO.search(nf) else "saude")
    return ctx, exigir


def aplicar(bot, fala, ident, resposta, modelo):
    """(ident, resposta, trace). Sem modelo, fora da conversa ou reprovada: o texto de sempre."""
    trace = {"ligada": modelo is not None, "usada": False, "motivo": None,
             "modelo": getattr(modelo, "nome", "fase5_v4_F"),
             "decisao": "criador; 46M v7c, aprovado na régua própria nas duas rodadas" if getattr(modelo, "formato6", False)
                        else "criador; v4 F reprovada",
             "aprovada": bool((getattr(modelo, "decisao", None) or {}).get("aprovada")),
             "motor": "c" if getattr(modelo, "motor", None) is not None else "numpy"}
    if modelo is None:
        trace["motivo"] = "desligada"
        return ident, resposta, trace
    ctx, exigir = contexto_do_turno(bot, fala, ident, resposta)
    if ctx is None:
        trace["motivo"] = exigir
        return ident, resposta, trace
    historico = []
    for f, r in (getattr(bot, "pares_conversa", None) or [])[-getattr(modelo, "max_pares", MAX_PARES):]:
        historico += [f, r]
    import time
    caso = {"contexto": ctx, "mensagem": fala, "historico": historico, "exigir": exigir}
    ctx_modelo = ctx
    if getattr(modelo, "formato6", False):
        lembr = lembrancas_de(bot)
        ctx_modelo = {"quem": QUEM, **({"lembrancas": lembr} if lembr else {}), **ctx}
        # O que a pessoa contou e quem ele é também são fonte: nome ou número de lá não é inventado.
        caso["mensagem"] = " ".join([fala] + lembr + [QUEM])
    # Até TENTATIVAS frases do modelo, dentro de PRAZO_TOTAL (a função do site tem 20 s).
    fim = time.monotonic() + PRAZO_TOTAL
    tentativas = TENTATIVAS
    if getattr(modelo, "formato6", False):
        limite_pedido = getattr(bot, "prazo_pedido", None)
        if getattr(bot, "refazendo_historico", False):
            # Turno antigo: o modelo lê a conversa como a pessoa viu, mas sem gastar o prazo da resposta.
            fim, tentativas = time.monotonic() + PRAZO_REFAZER, 1
        if limite_pedido is not None:
            fim = min(fim, limite_pedido)
    import ambiente
    ato = getattr(getattr(bot, "fio", None), "ato", None)
    fontes = [fala] + [f for f, _ in (getattr(bot, "pares_conversa", None) or [])] + [caso["mensagem"]]
    fontes += list(ctx.get("fatos") or []) + list((ctx.get("nomes") or {}).values())
    exigido = ambiente.exigido(bot, ident)
    if ato or exigido:
        trace["ato"] = ato
    # O juiz recusa mais; o prompt é lido uma vez, e cada frase a mais custa só as palavras dela. O turno
    # refeito do histórico fica com uma tentativa: no celular sem o motor em C, refazer quatro turnos com seis
    # tentativas cada comia o prazo, e a resposta nova saía cortada ("O…", conversa real de 20/10).
    if getattr(modelo, "formato6", False) and not getattr(bot, "refazendo_historico", False):
        tentativas = TENTATIVAS_AMBIENTE
    # Sem o CRIVO conhecer o assunto, a frase tem que dizer que não sabe ("Pelo que eu sei: O prossímio é uma
    # estrutura celular…" passava na marca): sem isso, fica o texto de sempre.
    import enciclopedia
    nao_sabe = ident in ("fora", "duvida") and bool(ctx.get("assunto") or enciclopedia.assunto(fala))
    trace["tentativas"] = 0
    frases = []   # (texto, terminou, falhas da conferência, falhas do juiz)
    for k in range(tentativas):
        resta = fim - time.monotonic()
        if resta <= 0.5:
            break
        try:
            texto, terminou = modelo.conversar(ctx_modelo, historico, fala, primeiro=k,
                                               prazo=min(resta, getattr(modelo, "prazo", None) or resta))
        except Exception as erro:  # contexto excedido, pesos ausentes
            trace["motivo"] = "erro: %s" % type(erro).__name__
            return ident, resposta, trace
        trace["tentativas"] = k + 1
        av = formato().avaliar_saida(caso, texto, terminou)
        juiz = ambiente.julgar(ato, fala, texto, fontes, exigido, nao_sabe=nao_sabe)
        trace.update(contexto=ctx_modelo, rascunho=texto)
        if av["tudo_ok"] and texto and not juiz:
            trace.update(usada=True, conferida=True,
                         motivo="conferida" if k == 0 else "conferida na tentativa %d" % (k + 1))
            return ident, texto, trace
        if texto:
            frases.append((texto, terminou, [k2 for k2, v in av.items() if v is False], juiz))
        trace["motivo"] = "reprovada: " + ", ".join(frases[-1][2] + frases[-1][3] if frases else ["vazia"])
    if ato == "sim_ou_nao" and getattr(modelo, "formato6", False) and fim - time.monotonic() > 0.5:
        # Nenhuma frase dele respondeu sim ou não: o ambiente oferece os dois começos e ele escolhe um.
        try:
            texto, terminou = modelo.conversar(ctx_modelo, historico, fala, prazo=fim - time.monotonic(),
                                               comecos=["Sim", "Não"])
        except Exception:
            texto = ""
        if texto:
            trace["tentativas"] += 1
            av = formato().avaliar_saida(caso, texto, terminou)
            juiz = ambiente.julgar(ato, fala, texto, fontes, exigido, nao_sabe=nao_sabe)
            if av["tudo_ok"] and not juiz:
                trace.update(usada=True, conferida=True, rascunho=texto, motivo="conferida com o começo do ambiente")
                return ident, texto, trace
            frases.insert(0, (texto, terminou, [k2 for k2, v in av.items() if v is False], juiz))
    # Decisão do criador (14/10/2026): "eu não quero que tu faça as falas dele, ele quem deve falar do
    # jeito que ele quiser". Se nenhuma frase passou na conferência, vai a primeira dele mesmo assim,
    # marcada como não conferida; o texto de sempre só aparece se ele não disse nada.
    if frases and (ident.startswith("enciclopedia:") or exigido or nao_sabe):
        # A resposta leva "Fonte: Wikipédia", ou é o resultado de uma tarefa (a palavra corrigida): o texto
        # tem que ser fiel. Sem conferência, fica o texto conferido.
        trace.update(usada=False, conferida=False,
                     motivo="fonte: não conferida, fica o texto conferido (" + ", ".join(frases[0][2] + frases[0][3]) + ")")
        return ident, resposta, trace
    # O juiz (ambiente.py): fica a primeira frase dele que não inventa nada; se todas inventam, sai a
    # frase inventada e fica o resto das palavras dele.
    escolhida = next((f for f in frases if not f[3]), None)
    if escolhida is None:
        for texto, terminou, falhas, juiz in frases:
            podado = ambiente.podar(texto, ato, fala, fontes)
            if podado:
                escolhida = (podado, terminou or podado != texto, falhas, juiz)
                trace["podada"] = True
                break
    if escolhida is not None and not escolhida[1] and len(escolhida[0]) < 40:
        # Cortada pelo prazo antes de dizer alguma coisa ("O…"): o texto de sempre diz mais.
        trace.update(usada=False, conferida=False, motivo="cortada pelo prazo: " + repr(escolhida[0]))
        return ident, resposta, trace
    if escolhida is not None:
        texto, terminou, falhas, juiz = escolhida
        if not terminou:
            texto = texto.rstrip() + "…"
        trace.update(usada=True, conferida=False, rascunho=texto, motivo="não conferida: " + ", ".join(falhas + juiz))
        return ident, texto, trace
    if frases:
        trace["motivo"] = "o juiz recusou todas: " + ", ".join(frases[0][3])
    return ident, resposta, trace


def status():
    """Estado público da voz da conversa (para a API)."""
    m = None if desligado_no_site() else numpy_do_site()
    e46 = getattr(m, "formato6", False)
    return {"site": {"ligada": m is not None, "modelo": getattr(m, "nome", "fase5_v4_F") if m else None,
                     "desligar": "CRIVO_DISABLE_CONVERSA_V3D=1", "voltar_para_a_f": "CRIVO_CONVERSA=f",
                     "npz_sha256": NPZ_SHA256_46M if e46 else NPZ_SHA256},
            "pesos_sha256": PESOS_SHA256_46M if e46 else PESOS_SHA256, "tokenizer_sha256": TOKENIZER_SHA256,
            "decisao": DECISAO_46M if e46 else DECISAO, "decisao_f": DECISAO, "external_ai": False}
