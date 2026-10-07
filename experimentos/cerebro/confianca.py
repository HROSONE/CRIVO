"""Árbitro que aprende em quem confiar (07/10/2026).

Depois que o árbitro (estado_interno.arbitrar) escolhe a resposta de um
especialista, este modelo estima a chance de a resposta factual estar certa,
a partir de sinais do próprio turno: que especialista respondeu, o tipo da
pergunta, a confiança da busca e da leitura, se é aproximação e quanto da
pergunta a resposta cobre. Abaixo do limiar aprendido, o CRIVO prefere dizer
que não tem certeza a afirmar.

Os pesos vêm de scripts/treinar_confianca.py (exemplos de desenvolvimento
com a resposta conhecida; testes congelados fora). Sem o arquivo de pesos, ou
se ele não foi aprovado, nada muda. Python puro: vale no CI sem NumPy.
"""
import json
import math
import re
from functools import lru_cache
from pathlib import Path

from composicao_textual import normalizar

CAMINHO = Path(__file__).resolve().parent / "artefatos" / "confianca" / "meta.json"

GRUPOS = ("base", "explicacao", "definicao", "aproximacao", "relacao", "comparacao", "logica", "outro")
TIPOS = ("quem", "quando", "onde", "quanto", "porque", "como", "simnao", "definicao", "qual")
PARADAS = frozenset("""a o os as um uma uns umas de do da dos das em no na nos nas por pelo pela pelos pelas para
pra com sem que qual quais quem quando onde como porque por que e ou se nao mais menos muito muita muitos
muitas ja foi era sao ser esta estao tem ter isso esse essa este esta aquele aquela me te voce vc sobre ate
entre ao aos sua seu suas seus meu minha""".split())


def grupo(ident):
    if ident.startswith("conhecimento:"):
        return "definicao"
    if ident == "leitura:aproximacao":
        return "aproximacao"
    if ident in ("escrita:explicacao", "aprendizado:sessao", "aprendizado:correcao"):
        return "explicacao"
    if ident == "escrita:relacao":
        return "relacao"
    if ident == "escrita:comparacao":
        return "comparacao"
    if ident.startswith("logica:"):
        return "logica"
    if ":" not in ident:
        return "base"
    return "outro"


def tipo_pergunta(texto):
    n = normalizar(texto)
    for tipo, padrao in (("quem", r"\bquem\b"), ("quando", r"\bquando\b|\bem que ano\b"), ("onde", r"\bonde\b"),
                         ("quanto", r"\bquant[oa]s?\b"), ("porque", r"\bpor que\b|\bporque\b|\bpq\b"),
                         ("como", r"^como\b"), ("definicao", r"^(?:o que (?:e|sao|significa)|defina)\b")):
        if re.search(padrao, n):
            return tipo
    if re.match(r"^(?:qual|quais)\b", n):
        return "qual"
    return "simnao"


def palavras(texto):
    return [w for w in re.findall(r"[a-z0-9]+", normalizar(texto)) if len(w) >= 3 and w not in PARADAS]


def suporte(pergunta, resposta):
    """Fração das palavras de conteúdo da pergunta que a resposta cobre."""
    ws = palavras(pergunta)
    if not ws:
        return 1.0
    raizes = {w[:5] for w in palavras(resposta)}
    return sum(w[:5] in raizes for w in ws) / len(ws)


def tracos(bot, pergunta, ident, resposta):
    """Dicionário de sinais do turno (todos numéricos)."""
    reg = bot.historico[-1] if bot.historico and bot.historico[-1].get("pergunta") == pergunta else {}
    leitura = reg.get("leitura") or {}
    g, t = grupo(ident), tipo_pergunta(pergunta)
    x = {"vies": 1.0, "suporte": suporte(pergunta, resposta),
         "palavras": min(len(palavras(pergunta)), 12) / 12.0,
         "prob_leitura": float(leitura.get("probability", 0.0) or 0.0),
         "prob_busca": float(leitura.get("search_probability", 0.0) or 0.0),
         "margem": float(leitura.get("margin", 0.0) or 0.0),
         "pistas_cobertas": min(float(leitura.get("cues_covered", 0) or 0), 6) / 6.0,
         "busca": 1.0 if reg.get("mecanismo") == "busca_aprendida" else 0.0}
    for nome in GRUPOS:
        x["g_" + nome] = 1.0 if g == nome else 0.0
    for nome in TIPOS:
        x["t_" + nome] = 1.0 if t == nome else 0.0
    x["suporte_base"] = x["suporte"] * x["g_base"]
    x["suporte_explicacao"] = x["suporte"] * x["g_explicacao"]
    return x


@lru_cache(maxsize=2)
def _modelo(caminho=str(CAMINHO)):
    try:
        meta = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return meta if meta.get("controle", {}).get("aprovado") else None


def probabilidade(x, meta):
    z = sum(meta["pesos"].get(k, 0.0) * v for k, v in x.items())
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


FACTUAIS = ("escrita:explicacao", "escrita:relacao", "escrita:comparacao", "leitura:aproximacao")


def avaliar_turno(bot, pergunta, ident, resposta, caminho=str(CAMINHO)):
    """(ident, resposta) finais: veta a resposta factual pouco confiável."""
    meta = _modelo(caminho)
    if meta is None or not isinstance(pergunta, str):
        return ident, resposta
    factual = ident in FACTUAIS or ident.startswith("conhecimento:") or (
        ":" not in ident and getattr(bot, "_ids_editoriais", None) and ident in bot._ids_editoriais
        and "?" in pergunta)
    if not factual:
        return ident, resposta
    p = probabilidade(tracos(bot, pergunta, ident, resposta), meta)
    if p >= meta["limiar"]:
        return ident, resposta
    if bot.historico and bot.historico[-1].get("pergunta") == pergunta:
        bot.historico[-1]["confianca"] = {"probabilidade": round(p, 3), "vetada": ident}
    return "fora", ("Não tenho certeza de que sei responder isso: o que encontrei não parece responder à sua "
                    "pergunta. Prefiro não arriscar.")
