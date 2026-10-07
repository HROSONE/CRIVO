"""Geração ancorada: o Transformer próprio redige a resposta a partir dos fatos.

Uso: python treinar_geracao_ancorada.py --pesos PASTA --dados PASTA_GERACAO --saida PASTA [--passos 1500]

Sequência: <documento> fato … <documento> fato <usuario> pergunta <assistente> resposta <fim>
Perda só nos tokens da resposta. Os fatos de cada exemplo são os citados pelo
tutor mais até dois outros da mesma ficha (embaralhados), para o modelo
aprender a escolher o que responde. Validação: 5% das fichas (por id) fora
do treino; mede a perda e, gerando com decodificação restrita, a fidelidade
(palavras de conteúdo só dos fatos e da pergunta; números só dos fatos) e a
sobreposição com a resposta do tutor.
"""
import argparse
import hashlib
import json
import math
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

SEMENTE = 20261007
LIGACAO = """a o as os um uma uns umas de do da dos das em no na nos nas por pelo pela pelos pelas para pra com sem
que qual quais quem quando onde como porque e ou mas se nao sim mais menos muito muita muitos muitas tambem ja
foi era sao ser e esta estao tem ter isso esse essa este esta ele ela eles elas seu sua seus suas ao aos à às
entao assim ou seja alem disso por isso isso porque ainda sobre ate entre cerca quase todo toda todos todas
outro outra outros outras mesmo mesma lhe lo la los las sendo foram eram havia ha pode podem deve devem""".split()


def norm(t):
    t = unicodedata.normalize("NFD", t.casefold())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def palavras_conteudo(t):
    return [w for w in re.findall(r"[a-z0-9]+", norm(t)) if len(w) >= 4 and w not in LIGACAO]


def fiel(resposta, fatos, pergunta):
    """Toda palavra de conteúdo da resposta tem raiz nos fatos ou na pergunta;
    todo número da resposta está nos fatos."""
    fonte = " ".join(fatos) + " " + pergunta
    raizes = {w[:4] for w in palavras_conteudo(fonte)}
    numeros_fonte = set(re.findall(r"\d+(?:[.,]\d+)*", fonte))
    if any(w[:4] not in raizes for w in palavras_conteudo(resposta)):
        return False
    return all(n in numeros_fonte for n in re.findall(r"\d+(?:[.,]\d+)*", resposta))


def verificado(resposta, fatos, pergunta, minimo=0.8):
    """Fiel e, frase a frase, apoiada num único fato: ao menos 80% das
    palavras de conteúdo da frase (fora as da pergunta) estão num mesmo fato.
    Barra misturas de pedaços de fatos diferentes."""
    if not fiel(resposta, fatos, pergunta):
        return False
    da_pergunta = {w[:4] for w in palavras_conteudo(pergunta)}
    raizes_fatos = [{w[:4] for w in palavras_conteudo(f)} for f in fatos]
    for frase in re.split(r"(?<=[.;!?])\s+|:\s+", resposta):
        ws = [w[:4] for w in palavras_conteudo(frase) if w[:4] not in da_pergunta]
        if len(ws) < 2:
            continue
        if max(sum(w in r for w in ws) / len(ws) for r in raizes_fatos) < minimo:
            return False
    return True


def f1(a, b):
    wa, wb = palavras_conteudo(a), palavras_conteudo(b)
    if not wa or not wb:
        return 0.0
    comum = sum(min(wa.count(w), wb.count(w)) for w in set(wa))
    if comum == 0:
        return 0.0
    p, r = comum / len(wa), comum / len(wb)
    return 2 * p * r / (p + r)


def carregar(dados, comp):
    exemplos = []
    for arq in sorted(Path(dados).glob("saida_*.jsonl")):
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if not linha.strip():
                continue
            e = json.loads(linha)
            it = comp.itens.get(e["id"])
            if it is None:
                continue
            fatos = [f["texto"] if isinstance(f, dict) else str(f) for f in it["fatos"]]
            if not e["fatos"] or any(i >= len(fatos) for i in e["fatos"]):
                continue
            citados = [fatos[i] for i in e["fatos"]]
            if not fiel(e["resposta"], citados, e["pergunta"]):
                continue  # o tutor também passa pela guarda
            exemplos.append({"id": e["id"], "pergunta": e["pergunta"], "resposta": e["resposta"],
                             "citados": list(e["fatos"]), "fatos": fatos})
    return exemplos


def contexto(e, rng, bpe, limite=170):
    """Fatos citados + até dois outros da ficha, embaralhados, dentro do limite."""
    outros = [i for i in range(len(e["fatos"])) if i not in e["citados"]]
    rng.shuffle(outros)
    escolhidos = list(e["citados"]) + outros[:2]
    rng.shuffle(escolhidos)
    ids, usados = [], []
    for i in escolhidos:
        t = [bpe.especiais["<documento>"]] + bpe.codificar(e["fatos"][i])
        if len(ids) + len(t) > limite and i not in e["citados"]:
            continue
        ids += t
        usados.append(i)
    return ids[:limite], usados


def sequencia(e, rng, bpe):
    esp = bpe.especiais
    ctx, usados = contexto(e, rng, bpe)
    prompt = ctx + [esp["<usuario>"]] + bpe.codificar(e["pergunta"])[:40] + [esp["<assistente>"]]
    alvo = bpe.codificar(e["resposta"])[:250 - len(prompt)] + [esp["<fim>"]]
    return prompt, alvo, usados


def permitidos(prompt_texto_ids, bpe, cache={}):
    if "ligacao" not in cache:
        base = set()
        for w in LIGACAO + [",", ".", ";", ":", "(", ")", "-", "–", "%", "°"]:
            for forma in (w, " " + w, w.capitalize(), " " + w.capitalize()):
                base.update(bpe.codificar(forma))
        cache["ligacao"] = base
    return cache["ligacao"] | set(prompt_texto_ids) | {bpe.especiais["<fim>"]}


def gerar(modelo, prompt, bpe, torch, max_tokens=70):
    """Gulosa, só com tokens permitidos e sem repetir trigramas."""
    permit = sorted(permitidos([t for t in prompt if t > 4], bpe))
    mascara = torch.full((modelo.config.vocabulario,), float("-inf"))
    mascara[permit] = 0.0
    ids, saida = list(prompt), []
    modelo.eval()
    with torch.no_grad():
        for _ in range(max_tokens):
            x = torch.tensor([ids[-modelo.config.contexto:]])
            logits, _ = modelo(x)
            l = logits[0, -1] + mascara
            for t in set(saida[-3:]):
                if saida.count(t) > 2:
                    l[t] -= 5.0
            if len(saida) >= 2:
                for k in range(len(saida) - 2):
                    if saida[k] == saida[-2] and saida[k + 1] == saida[-1] and k + 2 < len(saida):
                        l[saida[k + 2]] = float("-inf")
            prox = int(l.argmax())
            if prox == bpe.especiais["<fim>"]:
                break
            saida.append(prox)
            ids.append(prox)
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pesos", required=True)
    ap.add_argument("--dados", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--passos", type=int, default=1500)
    ap.add_argument("--lote", type=int, default=16)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--avaliar-a-cada", type=int, default=300)
    args = ap.parse_args()
    import numpy as np
    import torch
    from tokenizers import Tokenizer
    import treinar_codificador_sentido as tcs
    tcs.RAIZ = RAIZ
    from pontuador_frases import BPE
    from crivo import Crivo
    torch.manual_seed(SEMENTE)
    rng = random.Random(SEMENTE)
    comp = Crivo().compositor
    bpe = BPE(Path(args.pesos) / "tokenizer.json")
    tok = Tokenizer.from_file(str(Path(args.pesos) / "tokenizer.json"))
    modelo, cfg = tcs.construir(args.pesos)
    exemplos = carregar(args.dados, comp)
    val_ids = {e["id"] for e in exemplos if int(hashlib.sha256(e["id"].encode()).hexdigest()[:4], 16) % 20 == 0}
    treino = [e for e in exemplos if e["id"] not in val_ids]
    val = [e for e in exemplos if e["id"] in val_ids]
    print("exemplos fiéis:", len(exemplos), "| treino:", len(treino), "| validação:", len(val), flush=True)

    def perda_lote(lote):
        seqs = [sequencia(e, rng, bpe)[:2] for e in lote]
        t = max(len(p) + len(a) for p, a in seqs)
        ids = torch.zeros((len(seqs), t), dtype=torch.long)
        alvos = torch.full((len(seqs), t), -100, dtype=torch.long)
        for i, (p, a) in enumerate(seqs):
            s = p + a
            ids[i, :len(s)] = torch.tensor(s)
            alvos[i, len(p) - 1:len(s) - 1] = torch.tensor(a)
        _, perda = modelo(ids, alvos)
        return perda

    def avaliar(n_gerar=40):
        modelo.eval()
        r = random.Random(1)
        with torch.no_grad():
            perdas = [float(perda_lote(val[s:s + 16])) for s in range(0, len(val), 16)]
        fieis, verif, sobre, amostras = 0, 0, 0.0, []
        for e in val[:n_gerar]:
            prompt, _, usados = sequencia(e, r, bpe)
            out = tok.decode(gerar(modelo, prompt, bpe, torch)).strip()
            fatos_ctx = [e["fatos"][i] for i in usados]
            fieis += fiel(out, fatos_ctx, e["pergunta"])
            verif += verificado(out, fatos_ctx, e["pergunta"])
            sobre += f1(out, e["resposta"])
            if len(amostras) < 4:
                amostras.append((e["pergunta"], out))
        modelo.train()
        return {"perda_val": round(sum(perdas) / len(perdas), 3), "fiel": fieis, "verificado": verif,
                "f1": round(sobre / n_gerar, 3),
                "n": n_gerar}, amostras

    m, amostras = avaliar()
    print("antes:", m, flush=True)
    for q, o in amostras:
        print("   P:", q, "\n   R:", o, flush=True)
    opt = torch.optim.AdamW(modelo.parameters(), lr=args.lr, weight_decay=0.01)
    melhor, melhor_estado, historico = None, None, [dict(m, passo=0)]
    t0 = time.time()
    modelo.train()
    for passo in range(1, args.passos + 1):
        lote = [treino[rng.randrange(len(treino))] for _ in range(args.lote)]
        perda = perda_lote(lote)
        opt.zero_grad()
        perda.backward()
        torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
        opt.step()
        if passo % 50 == 0:
            print("passo %d perda %.3f | %.1fs/passo" % (passo, perda.item(), (time.time() - t0) / passo), flush=True)
        if passo % args.avaliar_a_cada == 0 or passo == args.passos:
            m, amostras = avaliar()
            historico.append(dict(m, passo=passo))
            print("passo %d validação %s" % (passo, m), flush=True)
            for q, o in amostras:
                print("   P:", q, "\n   R:", o, flush=True)
            if melhor is None or m["perda_val"] < melhor["perda_val"]:
                melhor = dict(m, passo=passo)
                melhor_estado = {k: v.detach().clone() for k, v in modelo.state_dict().items()}
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(saida / "pesos_numpy.npz", **{k: v.numpy().astype(np.float16) for k, v in melhor_estado.items()})
    (saida / "tokenizer.json").write_bytes((Path(args.pesos) / "tokenizer.json").read_bytes())
    (saida / "meta.json").write_text(json.dumps({
        "versao": 1, "papel": "geração ancorada: resposta a partir dos fatos", "base": {"config": cfg},
        "treino": {"exemplos": len(treino), "passos": args.passos, "lote": args.lote, "lr": args.lr, "semente": SEMENTE},
        "validacao": {"melhor": melhor, "historico": historico}, "pesos_externos": False},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("salvo em", saida, "| melhor", melhor, flush=True)


if __name__ == "__main__":
    main()
