"""Codificador de sentido: pergunta e fato viram vetores comparáveis.

Uso: python scripts/treinar_codificador_sentido.py --pesos leitor_transformer/ [--passos 1500]

Por que não o leitor (scripts/treinar_leitor_transformer.py): ele julgava um
par (pergunta, fato) por vez, com negativos fáceis, e aprendeu pouco além do
que o BM25 já faz (acerto de 55% na validação do tutor). Recuperação densa se
aprende de outro jeito (DPR, ANCE, Contriever):
  - dois lados independentes: os vetores dos fatos são calculados uma vez e
    no site só a pergunta passa pelo Transformer;
  - perda contrastiva (InfoNCE): a pergunta contra todos os fatos do lote
    (negativos do lote) e um negativo difícil por pergunta, um fato de OUTRA
    ficha que o BM25 põe no topo (o mesmo tema, sem a resposta); fatos da
    mesma ficha nunca são negativos (falso negativo);
  - perguntas com outras palavras: as 320 do tutor do decisor
    (dados/decisor_tutor.json, sem o nome do assunto, fichas fora dos
    testes) e perguntas sintéticas sem o nome e com sinônimos.

Ponto de partida: o corpo do Transformer próprio (pré-treino em português do
zero + leitor), nenhum peso externo. Validação (escolhe o passo): perguntas do
tutor da leitura e o dev das perguntas sem nome, recuperação entre TODOS os
fatos do acervo. Os testes congelados não entram aqui.

Saída: artefatos/sentido_pt/{pesos_numpy.npz, tokenizer.json, meta.json}; depois,
scripts/instalar_sentido.py prepara o executor NumPy e os vetores dos fatos.
"""
import argparse
import hashlib
import json
import math
import random
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

SEMENTE = 20261007
SAIDA = RAIZ / "artefatos" / "sentido_pt"


def _ler(caminho):
    return json.loads((RAIZ / caminho).read_text(encoding="utf-8"))


def texto_fato(f):
    return f["texto"] if isinstance(f, dict) else str(f)


def ids_texto(bpe, texto, papel, contexto=96):
    """<usuario> pergunta <fim> ou <documento> fato <fim>, cortado no contexto."""
    e = bpe.especiais
    corpo = bpe.codificar(texto)[:contexto - 2]
    return [e["<usuario>" if papel == "pergunta" else "<documento>"]] + corpo + [e["<fim>"]]


def assuntos_fora(comp):
    fora = {c["assunto"] for c in _ler("dados/leitura_ficha_tutor.json")["casos"]}
    for teste in ("avaliacoes/leitura_ficha_v1/teste.json", "avaliacoes/leitura_ficha_v2/teste.json",
                  "avaliacoes/busca_sem_nome_v1/teste.json", "avaliacoes/busca_sem_nome_v1/dev.json"):
        fora |= {c["assunto"] for c in _ler(teste)["casos"] if c.get("assunto")}
    return fora


def pares_treino(comp, rng):
    """[(pergunta, assunto, índice do fato)] para o contraste."""
    from perguntas_sinteticas import frases, perguntas_da_frase
    from treinar_leitor_transformer import _variar
    fora = assuntos_fora(comp)
    pares = []
    for c in _ler("dados/decisor_tutor.json")["casos"]:
        if c["assunto"] and c["assunto"] in comp.itens and c["assunto"] not in fora:
            for _ in range(4):  # poucas e valiosas: pesam mais
                pares.append((c["pergunta"], c["assunto"], c["fato"]))
    for ident, it in sorted(comp.itens.items()):
        if ident in fora or not it.get("fatos"):
            continue
        pessoa = it.get("area") == "pessoas"
        pares.append(("O que é " + it["nome"] + "?", ident, 0))
        for i, f in enumerate(it["fatos"]):
            for frase in frases(texto_fato(f)) or [texto_fato(f)]:
                for q, _ in perguntas_da_frase(frase, it["nome"], pessoa):
                    sem_nome = re.sub(r"\s*\b" + re.escape(it["nome"]) + r"\b", "", q, flags=re.I)
                    alvo = sem_nome if sem_nome != q and len(sem_nome.split()) >= 4 and rng.random() < 0.6 else q
                    pares.append((_variar(alvo, comp.lexico, rng) if rng.random() < 0.5 else alvo, ident, i))
    rng.shuffle(pares)
    return pares


def validacao(comp):
    casos = [(c["pergunta"], c["assunto"], c["fato"]) for c in _ler("dados/leitura_ficha_tutor.json")["casos"]
             if c.get("fato") is not None and c["assunto"] in comp.itens]
    casos += [(c["pergunta"], c["assunto"], c["fato"]) for c in _ler("avaliacoes/busca_sem_nome_v1/dev.json")["casos"]
              if c.get("fato") is not None and c["assunto"] in comp.itens]
    return casos


def construir(pasta):
    import numpy as np
    import torch
    from linguagem_profunda import Configuracao, LinguagemProfunda
    z = np.load(Path(pasta) / "pesos_numpy.npz", allow_pickle=False)
    meta = json.loads((Path(pasta) / "meta.json").read_text(encoding="utf-8"))
    cfg = meta["base"]["config"]
    config = Configuracao(**cfg)
    modelo = LinguagemProfunda(config)
    estado = modelo.state_dict()
    carregado = {k: torch.tensor(z[k]).float() for k in estado if k in z.files}
    faltam = [k for k in estado if k not in carregado]
    if faltam:
        raise ValueError("Pesos sem: %s" % faltam[:5])
    modelo.load_state_dict(carregado)
    return modelo, cfg


def codificar(modelo, lotes_ids, torch):
    """Média dos estados finais nas posições reais, normalizada."""
    t = max(len(s) for s in lotes_ids)
    ids = torch.zeros((len(lotes_ids), t), dtype=torch.long)
    mascara = torch.zeros((len(lotes_ids), t))
    for i, s in enumerate(lotes_ids):
        ids[i, :len(s)] = torch.tensor(s)
        mascara[i, :len(s)] = 1
    b = modelo
    x = b.embedding(ids) + b.posicao(torch.arange(t))
    for bloco in b.blocos:
        x = bloco(x)
    x = b.norm(x)
    v = (x * mascara.unsqueeze(-1)).sum(1) / mascara.sum(1, keepdim=True)
    return torch.nn.functional.normalize(v, dim=-1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pesos", required=True, help="pasta com pesos_numpy.npz, meta.json e tokenizer.json")
    ap.add_argument("--passos", type=int, default=1500)
    ap.add_argument("--lote", type=int, default=48)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--temperatura", type=float, default=0.05)
    ap.add_argument("--avaliar-a-cada", type=int, default=250)
    ap.add_argument("--saida", default=str(SAIDA))
    args = ap.parse_args()
    import numpy as np
    import torch
    torch.manual_seed(SEMENTE)
    rng = random.Random(SEMENTE)
    random.seed(SEMENTE)
    from crivo import Crivo
    from busca_semantica import BuscaSemantica
    from pontuador_frases import BPE
    comp = Crivo().compositor
    bpe = BPE(Path(args.pesos) / "tokenizer.json")
    modelo, cfg = construir(args.pesos)
    fatos = [(ident, i, texto_fato(f)) for ident, it in sorted(comp.itens.items())
             for i, f in enumerate(it.get("fatos", []))]
    pos = {(a, i): j for j, (a, i, _) in enumerate(fatos)}
    ids_fatos = [ids_texto(bpe, t, "fato") for _, _, t in fatos]
    busca = BuscaSemantica(comp, caminho_modelo=RAIZ / "nao-existe.json")
    pares = [(q, pos[(a, i)]) for q, a, i in pares_treino(comp, rng) if (a, i) in pos]
    val = [(q, pos[(a, i)]) for q, a, i in validacao(comp) if (a, i) in pos]
    print("fatos:", len(fatos), "| pares de treino:", len(pares), "| validação:", len(val), flush=True)

    def negativo_dificil(q, j):
        assunto = fatos[j][0]
        notas = busca.bm.notas(__import__("busca_semantica").termos(q))
        for k in sorted(notas, key=lambda k: -notas[k])[:20]:
            if fatos[k][0] != assunto:
                return k
        return rng.randrange(len(fatos))

    def avaliar():
        modelo.eval()
        with torch.no_grad():
            vf = torch.cat([codificar(modelo, ids_fatos[s:s + 128], torch) for s in range(0, len(ids_fatos), 128)])
            vq = torch.cat([codificar(modelo, [ids_texto(bpe, q, "pergunta") for q, _ in val[s:s + 128]], torch)
                            for s in range(0, len(val), 128)])
        sim = vq @ vf.T
        ordem = sim.argsort(dim=1, descending=True)[:, :10]
        r1 = sum(int(ordem[i, 0]) == j for i, (_, j) in enumerate(val))
        r10 = sum(j in ordem[i].tolist() for i, (_, j) in enumerate(val))
        f1 = sum(fatos[int(ordem[i, 0])][0] == fatos[j][0] for i, (_, j) in enumerate(val))
        modelo.train()
        return {"fato@1": r1, "fato@10": r10, "ficha@1": f1, "n": len(val)}

    inicial = avaliar()
    print("antes do treino:", inicial, flush=True)
    opt = torch.optim.AdamW(modelo.parameters(), lr=args.lr, weight_decay=0.01)
    melhor, melhor_estado, historico = inicial, None, [dict(inicial, passo=0)]
    t0 = time.time()
    modelo.train()
    for passo in range(1, args.passos + 1):
        lote = [pares[rng.randrange(len(pares))] for _ in range(args.lote)]
        js = [j for _, j in lote]
        negs = [negativo_dificil(q, j) for q, j in lote]
        vq = codificar(modelo, [ids_texto(bpe, q, "pergunta") for q, _ in lote], torch)
        vf = codificar(modelo, [ids_fatos[j] for j in js] + [ids_fatos[k] for k in negs], torch)
        sim = vq @ vf.T / args.temperatura
        # Fato da mesma ficha (ou o mesmo fato repetido no lote) não é negativo.
        fichas = [fatos[j][0] for j in js] + [fatos[k][0] for k in negs]
        mascara = torch.zeros_like(sim, dtype=torch.bool)
        for a in range(len(lote)):
            for b in range(len(fichas)):
                if b != a and fichas[b] == fatos[js[a]][0]:
                    mascara[a, b] = True
        sim = sim.masked_fill(mascara, -1e4)
        perda = torch.nn.functional.cross_entropy(sim, torch.arange(len(lote)))
        opt.zero_grad()
        perda.backward()
        torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
        opt.step()
        if passo % 25 == 0:
            print("passo %d perda %.3f | %.1fs/passo" % (passo, perda.item(), (time.time() - t0) / passo), flush=True)
        if passo % args.avaliar_a_cada == 0 or passo == args.passos:
            m = avaliar()
            historico.append(dict(m, passo=passo))
            print("passo %d validação %s" % (passo, m), flush=True)
            if m["fato@1"] + m["ficha@1"] > melhor["fato@1"] + melhor["ficha@1"]:
                melhor = dict(m, passo=passo)
                melhor_estado = {k: v.detach().clone() for k, v in modelo.state_dict().items()}
    if melhor_estado is None:
        print("o treino não melhorou a validação; nada salvo", flush=True)
        return
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(saida / "pesos_numpy.npz", **{k: v.numpy().astype(np.float16) for k, v in melhor_estado.items()})
    (saida / "tokenizer.json").write_bytes((Path(args.pesos) / "tokenizer.json").read_bytes())
    meta = {"versao": 1, "papel": "codificador de sentido: vetores de pergunta e fato (média dos estados finais)",
            "base": {"config": cfg, "origem": "Transformer próprio (pré-treino do zero) + leitor"},
            "treino": {"passos": args.passos, "lote": args.lote, "lr": args.lr, "temperatura": args.temperatura,
                       "semente": SEMENTE, "pares": len(pares),
                       "dados": "tutor do decisor (paráfrases reais, sem o nome) + sintéticas sem o nome e com sinônimos; "
                                "negativo difícil do BM25 de outra ficha; mesma ficha nunca é negativo"},
            "validacao": {"antes": inicial, "melhor": melhor, "historico": historico},
            "tokenizer_sha256": hashlib.sha256((saida / "tokenizer.json").read_bytes()).hexdigest(),
            "pesos_externos": False}
    (saida / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("salvo em", saida, "| melhor", melhor, flush=True)


if __name__ == "__main__":
    main()
