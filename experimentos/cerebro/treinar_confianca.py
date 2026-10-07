"""Treina o árbitro que aprende em quem confiar (confianca.py).

Uso: python scripts/treinar_confianca.py [--sem-gravar]

Exemplos: perguntas de DESENVOLVIMENTO com a resposta conhecida (lacunas dev,
bateria dev, tutor da leitura, sem nome dev, tutor do decisor). Para cada uma
o CRIVO responde (sem o veto); cada resposta factual vira (sinais do turno,
certa?). Uma regressão logística aprende a chance de acerto; o limiar é o que
maximiza certos − 3 × errados por validação cruzada em 5 partes (agrupadas por
conjunto e pergunta). Testes congelados não entram.

Aprovado só se, na validação cruzada, vetar reduz os erros mais do que três
vezes os acertos perdidos (ganho > 0 em certos − 3 × errados).
"""
import argparse
import json
import math
import random
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

SEMENTE = 20261007
CUSTO_ERRO = 3.0


def _n(t):
    t = unicodedata.normalize("NFKD", t.casefold())
    return "".join(c for c in t if not unicodedata.combining(c))


def _ler(c):
    return json.loads((RAIZ / c).read_text(encoding="utf-8"))


def casos():
    """[(conjunto, pergunta, conferir(bot, resposta) -> bool ou None se sem resposta)]"""
    saida = []
    for c in _ler("avaliacoes/lacunas_v1/dev.json")["casos"]:
        saida.append(("lacunas", c["pergunta"], lambda b, r, e=c["esperado"]: any(_n(x) in _n(r) for x in e)))
    for c in _ler("avaliacoes/bateria_v1/dev.json")["casos"]:
        if c.get("tipo") == "recusa":
            saida.append(("bateria", c["p"], lambda b, r: False))
        else:
            saida.append(("bateria", c["p"], lambda b, r, e=c["contem"]: any(_n(x) in _n(r) for x in e)))
    for nome in ("dados/leitura_ficha_tutor.json", "avaliacoes/busca_sem_nome_v1/dev.json", "dados/decisor_tutor.json"):
        for c in _ler(nome)["casos"]:
            if c.get("assunto") is None or c.get("fato") is None:
                saida.append((nome, c["pergunta"], lambda b, r: False))
            else:
                def conferir(b, r, a=c["assunto"], i=c["fato"]):
                    if a not in b.compositor.itens or i >= len(b.compositor.itens[a]["fatos"]):
                        return None
                    f = b.compositor.itens[a]["fatos"][i]
                    alvo = _n(f["texto"] if isinstance(f, dict) else str(f))[:80]
                    ctx = b.contexto_textual
                    return (ctx is not None and (a, i) in tuple(ctx.exibidos)) or alvo in _n(r)
                saida.append((nome, c["pergunta"], conferir))
    return saida


def coletar():
    import confianca
    from crivo import Crivo
    exemplos = []
    for conjunto, pergunta, conferir in casos():
        bot = Crivo()
        bot.usar_confianca = False
        ident, resposta = bot.responder(pergunta)
        if bot._ids_editoriais is None:
            bot._ids_editoriais = frozenset(e["id"] for e in bot.base)
        factual = ident in confianca.FACTUAIS or ident.startswith("conhecimento:") or (
            ":" not in ident and ident in bot._ids_editoriais and "?" in pergunta)
        if not factual:
            continue
        certo = conferir(bot, resposta)
        if certo is None:
            continue
        exemplos.append({"conjunto": conjunto, "pergunta": pergunta, "id": ident, "certo": bool(certo),
                         "x": confianca.tracos(bot, pergunta, ident, resposta)})
    return exemplos


def treinar(ex, l2=0.01, passos=400, lr=0.1):
    nomes = sorted(ex[0]["x"])
    w = {k: 0.0 for k in nomes}
    m = {k: 0.0 for k in nomes}
    v = {k: 0.0 for k in nomes}
    for t in range(1, passos + 1):
        g = {k: l2 * w[k] for k in nomes}
        for e in ex:
            z = sum(w[k] * e["x"][k] for k in nomes)
            p = 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
            d = (p - (1.0 if e["certo"] else 0.0)) / len(ex)
            for k in nomes:
                g[k] += d * e["x"][k]
        for k in nomes:
            m[k] = 0.9 * m[k] + 0.1 * g[k]
            v[k] = 0.999 * v[k] + 0.001 * g[k] * g[k]
            w[k] -= lr * (m[k] / (1 - 0.9 ** t)) / (math.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8)
    return w


def prob(w, x):
    z = sum(w.get(k, 0.0) * val for k, val in x.items())
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))


def ganho(ps, ex, limiar):
    """(acertos perdidos, erros evitados, ganho) ao vetar abaixo do limiar."""
    perdidos = sum(1 for p, e in zip(ps, ex) if p < limiar and e["certo"])
    evitados = sum(1 for p, e in zip(ps, ex) if p < limiar and not e["certo"])
    return perdidos, evitados, evitados * CUSTO_ERRO - perdidos * 1.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sem-gravar", action="store_true")
    ap.add_argument("--exemplos", help="usar exemplos já coletados (json)")
    args = ap.parse_args()
    rng = random.Random(SEMENTE)
    if args.exemplos:
        ex = json.loads(Path(args.exemplos).read_text(encoding="utf-8"))
    else:
        ex = coletar()
        destino = RAIZ / "artefatos" / "confianca" / "exemplos_dev.json"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(ex, ensure_ascii=False), encoding="utf-8")
    print("exemplos:", len(ex), "| certos:", sum(e["certo"] for e in ex), "| errados:",
          sum(not e["certo"] for e in ex), flush=True)
    # Validação cruzada agrupada por pergunta.
    perguntas = sorted({e["pergunta"] for e in ex})
    rng.shuffle(perguntas)
    parte = {q: i % 5 for i, q in enumerate(perguntas)}
    ps = [0.0] * len(ex)
    for k in range(5):
        treino = [e for e in ex if parte[e["pergunta"]] != k]
        w = treinar(treino)
        for i, e in enumerate(ex):
            if parte[e["pergunta"]] == k:
                ps[i] = prob(w, e["x"])
    limiares = [i / 100 for i in range(5, 80)]
    melhor = max(limiares, key=lambda l: (ganho(ps, ex, l)[2], -l))
    perdidos, evitados, g = ganho(ps, ex, melhor)
    print("validação cruzada: limiar %.2f → erros evitados %d, acertos perdidos %d, ganho %.1f"
          % (melhor, evitados, perdidos, g), flush=True)
    w = treinar(ex)
    aprovado = g > 0
    meta = {"versao": 1, "pesos": {k: round(v, 5) for k, v in w.items()}, "limiar": melhor,
            "custo_erro": CUSTO_ERRO,
            "treino": {"exemplos": len(ex), "certos": sum(e["certo"] for e in ex), "semente": SEMENTE,
                       "dados": "lacunas dev, bateria dev, tutor da leitura, sem nome dev, tutor do decisor"},
            "validacao_cruzada": {"limiar": melhor, "erros_evitados": evitados, "acertos_perdidos": perdidos,
                                  "ganho": g},
            "controle": {"aprovado": aprovado,
                         "criterio": "na validação cruzada, erros evitados × 3 > acertos perdidos"}}
    print("aprovado:", aprovado, "| pesos:", {k: round(v, 2) for k, v in sorted(w.items(), key=lambda kv: -abs(kv[1]))[:10]},
          flush=True)
    if not args.sem_gravar:
        (RAIZ / "artefatos" / "confianca" / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
