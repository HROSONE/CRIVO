"""Compara a decodificação gulosa com a decodificação por candidatos conferidos.

Candidatos: a gulosa + algumas amostras (top-k, temperatura baixa), todas
restritas aos tokens dos fatos e da pergunta. Fica o candidato de maior
verossimilhança média que passa no verificador por frase e não repete palavra;
se nenhum passa, a resposta é o fato (recuo extrativo).
"""
import argparse
import random
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import treinar_geracao_ancorada as tga  # noqa: E402


def _ws(t):
    return re.findall(r"[a-z0-9]+", tga.norm(t))


def repete_palavra(texto, fonte="", janela=5):
    """Palavra de conteúdo repetida perto de si mesma ("políticos e políticos"),
    a menos que a própria fonte repita essa palavra assim perto."""
    def perto(t):
        ws = [w for w in _ws(t) if len(w) >= 4 and w not in tga.LIGACAO]
        return {ws[i] for i in range(len(ws)) if ws[i] in ws[max(0, i - janela):i]}
    return bool(perto(texto) - perto(fonte))


def costura(texto, fonte, minimo=0.6, minimo_frase=0.5):
    """Pares de palavras vizinhas da resposta que existem na fonte. O tutor
    fica acima de 0,56 em 99% dos casos; colagens tortas ficam bem abaixo."""
    f = _ws(fonte)
    pares = set(zip(f, f[1:]))
    def cob(t):
        w = _ws(t)
        bs = list(zip(w, w[1:]))
        return sum(b in pares for b in bs) / len(bs) if bs else 1.0
    frases = [x for x in re.split(r"(?<=[.;!?])\s+", texto) if len(_ws(x)) >= 4]
    return cob(texto) >= minimo and all(cob(x) >= minimo_frase for x in frases)


def polaridade_inventada(texto):
    """"Sim"/"Não" no começo não se confere pelas palavras: fica de fora."""
    w = _ws(texto)
    return bool(w) and w[0] in ("sim", "nao")


def terminada(texto):
    return texto.rstrip().endswith((".", "!", "?"))


def amostrar(modelo, prompt, mascara, bpe, torch, gerador, temperatura=0.7, top_k=5, max_tokens=70):
    ids, saida, lp = list(prompt), [], 0.0
    with torch.no_grad():
        for _ in range(max_tokens):
            logits, _ = modelo(torch.tensor([ids[-modelo.config.contexto:]]))
            l = logits[0, -1] + mascara
            logp = torch.log_softmax(l, -1)
            if temperatura == 0:
                prox = int(l.argmax())
            else:
                v, i = torch.topk(l / temperatura, top_k)
                p = torch.softmax(v, -1)
                prox = int(i[int(torch.multinomial(p, 1, generator=gerador))])
            lp += float(logp[prox])
            if prox == bpe.especiais["<fim>"]:
                break
            saida.append(prox)
            ids.append(prox)
    return saida, lp / max(1, len(saida) + 1)


def conferida(modelo, prompt, bpe, tok, torch, fatos, pergunta, n=4, semente=0):
    permit = sorted(tga.permitidos([t for t in prompt if t > 4], bpe))
    mascara = torch.full((modelo.config.vocabulario,), float("-inf"))
    mascara[permit] = 0.0
    gerador = torch.Generator().manual_seed(semente)
    candidatos = [(tok.decode(tga.gerar(modelo, prompt, bpe, torch)).strip(), 1.0)]  # gulosa primeiro
    for _ in range(n - 1):
        s, lp = amostrar(modelo, prompt, mascara, bpe, torch, gerador)
        candidatos.append((tok.decode(s).strip(), lp))
    fonte = " ".join(fatos) + " " + pergunta
    bons = [(lp, c) for c, lp in candidatos
            if c and terminada(c) and not polaridade_inventada(c) and not repete_palavra(c, fonte) and costura(c, fonte)
            and tga.verificado(c, fatos, pergunta)]
    return (max(bons)[1], len(bons)) if bons else (None, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--pesos-base", required=True, help="pasta com o tokenizer original")
    ap.add_argument("--dados", required=True)
    ap.add_argument("--n", type=int, default=69)
    args = ap.parse_args()
    import hashlib
    import torch
    from tokenizers import Tokenizer
    import treinar_codificador_sentido as tcs
    tcs.RAIZ = tga.RAIZ
    from pontuador_frases import BPE
    from crivo import Crivo
    torch.manual_seed(tga.SEMENTE)
    comp = Crivo().compositor
    bpe = BPE(Path(args.modelo) / "tokenizer.json")
    tok = Tokenizer.from_file(str(Path(args.modelo) / "tokenizer.json"))
    modelo, _ = tcs.construir(args.modelo)
    modelo.eval()
    exemplos = tga.carregar(args.dados, comp)
    val = [e for e in exemplos if int(hashlib.sha256(e["id"].encode()).hexdigest()[:4], 16) % 20 == 0][:args.n]
    r = random.Random(1)
    gul = {"verificado": 0, "repete": 0, "f1": 0.0}
    conf = {"respondeu": 0, "recuo": 0, "f1": 0.0, "f1_recuo": 0.0}
    for k, e in enumerate(val):
        prompt, _, usados = tga.sequencia(e, r, bpe)
        fatos = [e["fatos"][i] for i in usados]
        g = tok.decode(tga.gerar(modelo, prompt, bpe, torch)).strip()
        gul["verificado"] += tga.verificado(g, fatos, e["pergunta"])
        gul["repete"] += repete_palavra(g, " ".join(fatos) + " " + e["pergunta"])
        gul["f1"] += tga.f1(g, e["resposta"])
        c, nbons = conferida(modelo, prompt, bpe, tok, torch, fatos, e["pergunta"], semente=k)
        if c is None:
            conf["recuo"] += 1
            recuo = e["fatos"][e["citados"][0]]
            conf["f1_recuo"] += tga.f1(recuo, e["resposta"])
            conf["f1"] += tga.f1(recuo, e["resposta"])
        else:
            conf["respondeu"] += 1
            conf["f1"] += tga.f1(c, e["resposta"])
        if k < 6 or (g != c and c is not None and k < 30):
            print("P:", e["pergunta"], "\n  gulosa:", g, "\n  conferida:", c, "(%d bons)" % nbons, flush=True)
    n = len(val)
    gul["f1"] = round(gul["f1"] / n, 3)
    conf["f1"] = round(conf["f1"] / n, 3)
    conf["f1_recuo"] = round(conf["f1_recuo"] / max(1, conf["recuo"]), 3)
    print("n", n, "| gulosa", gul, "| conferida", conf, flush=True)


if __name__ == "__main__":
    main()
