"""Treina o Transformer próprio como leitor: este fato responde a esta pergunta?

Ponto de partida (--base): um checkpoint do Transformer do projeto (pesos.pt +
tokenizer.json), de preferência o pré-treino em português de 16M parâmetros
guardado no Drive pelo caderno notebooks/treinar_transformer_16m_colab.ipynb
(<experimento>/pretreino/melhor). Sem ele, artefatos/linguagem_profunda (2,6M)
serve para testar o caminho em CPU.

Dados de treino: só perguntas sintéticas tiradas das fichas
(scripts/perguntas_sinteticas.py), com variações (sinônimos do léxico,
palavras retiradas) e perguntas sem resposta (pergunta de outra ficha com o
nome trocado). Ficam de fora, para medir sem vazamento:
  - as fichas das perguntas do tutor (dados/leitura_ficha_tutor.json);
  - as fichas dos testes congelados v1 e v2 da leitura;
  - toda a astronomia (a bateria de medição é de astronomia).

Validação: as perguntas do tutor (que o leitor nunca vê no treino). Guarda o
melhor passo por acerto do fato + separação entre respondíveis e sem resposta.

Saída (--saida, padrão artefatos/leitor_transformer): pesos_numpy.npz para o
executor NumPy (leitor_transformer.py), tokenizer.json e meta.json com o
controle "aprovado": false. Quem aprova é scripts/treinar_leitura_ficha.py
--com-transformer, e só se melhorar a validação; o teste congelado v2 decide
se fica ligado.

Uso:
  python scripts/treinar_leitor_transformer.py --base artefatos/linguagem_profunda --passos 300
  python scripts/treinar_leitor_transformer.py --base /content/drive/.../pretreino/melhor \\
      --dispositivo cuda --passos 4000 --lote 64
"""
import argparse
import hashlib
import json
import random
import re
import shutil
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

SEMENTE = 20261006


def _ler(caminho):
    return json.loads((RAIZ / caminho).read_text(encoding="utf-8"))


def assuntos_excluidos(compositor):
    fora = {c["assunto"] for c in _ler("dados/leitura_ficha_tutor.json")["casos"]}
    for teste in ("avaliacoes/leitura_ficha_v1/teste.json", "avaliacoes/leitura_ficha_v2/teste.json"):
        fora |= {c["assunto"] for c in _ler(teste)["casos"]}
    fora |= {i for i, it in compositor.itens.items() if it.get("area") == "astronomia"}
    return fora


def _variar(pergunta, lexico, rng):
    """Troca uma palavra por sinônimo do léxico ou tira uma palavra acessória."""
    palavras = pergunta.rstrip("?").split()
    if rng.random() < 0.5:
        for i in rng.sample(range(len(palavras)), len(palavras)):
            w = palavras[i].lower()
            sinonimos = sorted(lexico.sinonimos.get(w, ()))
            if sinonimos:
                palavras[i] = rng.choice(sinonimos)
                return " ".join(palavras) + "?"
    if len(palavras) > 5:
        del palavras[rng.randrange(2, len(palavras))]
    return " ".join(palavras) + "?"


def exemplos_sinteticos(compositor, rng):
    """[(pergunta, [fatos], índice certo ou None)] das fichas permitidas."""
    from perguntas_sinteticas import frases, perguntas_da_frase
    fora = assuntos_excluidos(compositor)
    grupos, por_assunto = [], {}
    for ident, it in sorted(compositor.itens.items()):
        if ident in fora or len(it["fatos"]) < 2:
            continue
        fatos = [f["texto"] for f in it["fatos"]]
        pessoa = it.get("area") == "pessoas"
        for i, fato in enumerate(fatos):
            for frase in frases(fato) or [fato]:
                for q, _ in perguntas_da_frase(frase, it["nome"], pessoa):
                    if not re.search(re.escape(it["nome"].split()[0]), q, re.I):
                        q = q.rstrip("?") + " (" + it["nome"] + ")?"
                    grupos.append((q, fatos, i))
                    por_assunto.setdefault(ident, []).append(q)
                    if rng.random() < 0.7:
                        grupos.append((_variar(q, compositor.lexico, rng), fatos, i))
        grupos.append(("O que é " + it["nome"] + "?", fatos, 0))
    # Sem resposta: pergunta de outra ficha com o nome trocado.
    ids = sorted(por_assunto)
    for ident in ids:
        it = compositor.itens[ident]
        outro = rng.choice(ids)
        if outro == ident:
            continue
        q = rng.choice(por_assunto[outro])
        nome_outro = compositor.itens[outro]["nome"]
        if nome_outro.lower() not in q.lower():
            continue
        q = re.sub(re.escape(nome_outro), it["nome"], q, flags=re.I)
        grupos.append((q, [f["texto"] for f in it["fatos"]], None))
    rng.shuffle(grupos)
    return grupos


def exemplos_tutor(compositor):
    saida = []
    for c in _ler("dados/leitura_ficha_tutor.json")["casos"]:
        if c["assunto"] in compositor.itens:
            saida.append((c["pergunta"], [f["texto"] for f in compositor.itens[c["assunto"]]["fatos"]], c["fato"]))
    return saida


def construir(base, dispositivo):
    import torch
    from torch import nn
    from linguagem_profunda import Configuracao, LinguagemProfunda
    from pontuador_frases import BPE
    base = Path(base)
    estado = torch.load(base / "pesos.pt", map_location="cpu", weights_only=True)
    sha = hashlib.sha256((base / "tokenizer.json").read_bytes()).hexdigest()
    if sha != estado["execucao"]["tokenizer_sha256"]:
        raise ValueError("Tokenizador difere do usado no pré-treino")
    config = Configuracao(**estado["config"])

    class Leitor(nn.Module):
        def __init__(self):
            super().__init__()
            self.base = LinguagemProfunda(config)
            self.base.load_state_dict(estado["modelo"])
            self.cabeca = nn.Linear(config.dimensao, 1)

        def forward(self, ids, ultimos):
            b = self.base
            x = b.embedding(ids) + b.posicao(torch.arange(ids.shape[1], device=ids.device))
            for bloco in b.blocos:
                x = bloco(x)
            x = b.norm(x)
            return self.cabeca(x[torch.arange(ids.shape[0], device=ids.device), ultimos]).squeeze(-1)

    modelo = Leitor().to(dispositivo)
    return modelo, BPE(base / "tokenizer.json"), estado, sha


def lote_tensores(pares, bpe, contexto, dispositivo):
    import torch
    from leitor_transformer import sequencia
    seqs = [sequencia(bpe, contexto, q, f) for q, f in pares]
    t = max(len(s) for s in seqs)
    ids = torch.zeros((len(seqs), t), dtype=torch.long)
    for i, s in enumerate(seqs):
        ids[i, :len(s)] = torch.tensor(s)
    ultimos = torch.tensor([len(s) - 1 for s in seqs])
    return ids.to(dispositivo), ultimos.to(dispositivo)


def avaliar(modelo, bpe, contexto, grupos, dispositivo):
    """Acerto do fato nas respondíveis e AUC (respondível × sem resposta) da
    maior probabilidade."""
    import torch
    modelo.eval()
    maiores, certos, n_resp = [], 0, 0
    with torch.no_grad():
        for q, fatos, alvo in grupos:
            ids, ult = lote_tensores([(q, f) for f in fatos], bpe, contexto, dispositivo)
            p = torch.sigmoid(modelo(ids, ult)).cpu().tolist()
            m = max(range(len(p)), key=lambda i: p[i])
            maiores.append((p[m], alvo is not None))
            if alvo is not None:
                n_resp += 1
                certos += m == alvo
    modelo.train()
    pos = [p for p, r in maiores if r]
    neg = [p for p, r in maiores if not r]
    auc = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg) / max(1, len(pos) * len(neg))
    return {"acerto_fato": round(certos / max(1, n_resp), 4), "auc_respondivel": round(auc, 4),
            "respondiveis": n_resp, "sem_resposta": len(neg)}


def exportar(modelo, estado, sha, base, saida, passo, metricas, args):
    import numpy as np
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(base) / "tokenizer.json", saida / "tokenizer.json")
    pesos = {k: v.detach().float().cpu().numpy().astype(np.float16)
             for k, v in modelo.base.state_dict().items()}
    pesos["cabeca.weight"] = modelo.cabeca.weight.detach().float().cpu().numpy()
    pesos["cabeca.bias"] = modelo.cabeca.bias.detach().float().cpu().numpy()
    meta_npz = dict(estado["config"], passo=passo, tokenizer_sha256=sha)
    np.savez_compressed(saida / "pesos_numpy.npz", meta=np.array(json.dumps(meta_npz)), **pesos)
    meta = {
        "versao": 1,
        "papel": "leitor: probabilidade de um fato da ficha responder à pergunta",
        "base": {"pasta": str(base), "pesos_sha256": hashlib.sha256((Path(base) / "pesos.pt").read_bytes()).hexdigest(),
                 "config": estado["config"], "passo_pretreino": estado.get("passo")},
        "treino": {"passo": passo, "passos": args.passos, "lote": args.lote, "lr": args.lr,
                   "semente": SEMENTE, "dados": "sintéticos das fichas (sem tutor, testes v1/v2 e astronomia)"},
        "validacao_tutor": metricas,
        "controle": {"aprovado": False,
                     "criterio": "aprovado por scripts/treinar_leitura_ficha.py --com-transformer só se a "
                                 "validação por assunto melhorar; fica ligado só se o teste congelado v2 melhorar"},
    }
    (saida / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main():
    import torch
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=str(RAIZ / "artefatos" / "linguagem_profunda"))
    ap.add_argument("--saida", default=str(RAIZ / "artefatos" / "leitor_transformer"))
    ap.add_argument("--passos", type=int, default=600)
    ap.add_argument("--lote", type=int, default=32, help="pares por passo")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--avaliar-a-cada", type=int, default=100)
    ap.add_argument("--dispositivo", default="cpu")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--limite-minutos", type=float, default=0)
    args = ap.parse_args()
    torch.manual_seed(SEMENTE)
    torch.set_num_threads(args.threads)
    rng = random.Random(SEMENTE)
    from crivo import Crivo
    comp = Crivo().compositor
    treino = exemplos_sinteticos(comp, rng)
    validacao = exemplos_tutor(comp)
    pares = [(q, f, 1.0 if alvo == i else 0.0) for q, fatos, alvo in treino for i, f in enumerate(fatos)]
    positivos = sum(y for _, _, y in pares)
    print("grupos de treino:", len(treino), "| pares:", len(pares), "| positivos:", int(positivos),
          "| validação (tutor):", len(validacao), flush=True)
    modelo, bpe, estado, sha = construir(args.base, args.dispositivo)
    contexto = modelo.base.config.contexto
    opt = torch.optim.AdamW(modelo.parameters(), lr=args.lr, weight_decay=0.01)
    peso_pos = torch.tensor((len(pares) - positivos) / max(1.0, positivos), device=args.dispositivo)
    melhor, melhor_nota = None, -1.0
    inicio = time.time()
    metricas = avaliar(modelo, bpe, contexto, validacao, args.dispositivo)
    print("passo 0", metricas, flush=True)
    for passo in range(1, args.passos + 1):
        amostra = rng.sample(pares, min(args.lote, len(pares)))
        ids, ult = lote_tensores([(q, f) for q, f, _ in amostra], bpe, contexto, args.dispositivo)
        y = torch.tensor([y for _, _, y in amostra], device=args.dispositivo)
        perda = torch.nn.functional.binary_cross_entropy_with_logits(modelo(ids, ult), y, pos_weight=peso_pos)
        opt.zero_grad()
        perda.backward()
        torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
        opt.step()
        fim_tempo = args.limite_minutos and time.time() - inicio > args.limite_minutos * 60
        if passo % args.avaliar_a_cada == 0 or passo == args.passos or fim_tempo:
            metricas = avaliar(modelo, bpe, contexto, validacao, args.dispositivo)
            nota = metricas["acerto_fato"] + metricas["auc_respondivel"]
            print("passo", passo, "perda %.4f" % perda.item(), metricas, flush=True)
            if nota > melhor_nota:
                melhor_nota, melhor = nota, (passo, metricas)
                exportar(modelo, estado, sha, args.base, args.saida, passo, metricas, args)
        if fim_tempo:
            print("limite de tempo atingido", flush=True)
            break
    print("melhor:", melhor, "->", args.saida, flush=True)


if __name__ == "__main__":
    main()
