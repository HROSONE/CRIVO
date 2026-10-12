"""Pré-treino continuado do Transformer próprio de 17,43M do CRIVO.

Por quê: a sonda de cópia em contexto ([A][B] … [A] → [B]) mostrou que o 17M
copia só 27% de uma sequência de tokens aleatórios que acabou de ver. Essa
capacidade ("induction heads") se forma no pré-treino; a base viu ~0,33 bilhão
de tokens (20.000 passos × 64 × 256), menos da metade do corpus próprio já
montado. Este script continua o MESMO modelo, com os mesmos dados e o mesmo
tokenizador, sem nenhum peso externo, e mede a cópia ao longo do treino.

Etapas (--etapa):
  treinar   parte do checkpoint de pré-treino (--origem, só leitura) e grava em
            outro arquivo (--checkpoint); retoma sozinho desse arquivo;
            re-aquecimento curto e cosseno por --passos-extra; uma fração
            --frac-repeticao das janelas recebe um trecho repetido dela mesma;
            sonda de cópia a cada --sonda-a-cada passos;
  exportar  grava pesos.pt + tokenizer.json + relatorio.json no formato de
            linguagem_profunda.carregar.

Os dados (treino.bin/validacao.bin) vêm das etapas `dados` e `tokenizar` de
scripts/pretreinar_leitor_16m.py, com o tokenizer.json da base (não retreinar).
"""
import argparse
import dataclasses
import hashlib
import json
import math
import random
import shutil
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

import pretreinar_leitor_16m as pt  # noqa: E402

TOKENIZER_SHA256 = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"
NOMES_SONDA = ["zedi", "vdvd", "Zorvak", "Pugi35", "xf200", "golu", "Biru81", "jkvx",
               "tavemo", "Kriluz", "qopa", "Mendrel"]


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def janelas_com_repeticao(dados, contexto, tamanho, gerador, frac, np):
    """Janelas contíguas do corpus; numa fração delas, um trecho reaparece mais adiante."""
    inicio = gerador.integers(0, len(dados) - contexto - 1, size=tamanho)
    w = np.stack([dados[i:i + contexto + 1] for i in inicio]).astype(np.int64)
    n_rep = 0
    for linha in np.nonzero(gerador.random(tamanho) < frac)[0]:
        L = int(gerador.integers(8, 49))
        s = int(gerador.integers(0, contexto // 2 - L))
        d = int(gerador.integers(s + L + 4, contexto + 1 - L))
        w[linha, d:d + L] = w[linha, s:s + L]
        n_rep += 1
    return w[:, :-1], w[:, 1:], n_rep


def sonda_copia(modelo, tok, dispositivo, np, torch, F, amostras=20, L=50):
    """Cópia de tokens aleatórios repetidos e 2ª menção de nomes inventados (semente fixa)."""
    modelo.eval()
    comuns = [i for i in range(5, tok.get_vocab_size()) if tok.id_to_token(i).startswith("Ġ")]
    rr = random.Random(0)
    acertos, p1, p2 = [], [], []
    with torch.no_grad():
        for _ in range(amostras):
            seq = [rr.choice(comuns) for _ in range(L)]
            x = torch.tensor([seq + seq], device=dispositivo)
            lg = modelo(x)[0][0].float()
            lp_ = F.log_softmax(lg[:-1], -1)
            perda = -lp_.gather(-1, x[0, 1:, None])[:, 0]
            p1.append(perda[:L - 1].mean().item())
            p2.append(perda[L:].mean().item())
            acertos.append((lg[L - 1:-1].argmax(-1) == x[0, L:]).float().mean().item())
        nomes1, nomes2 = [], []
        for nome in NOMES_SONDA:
            ids = tok.encode(f"Existe um objeto chamado {nome}. Ele serve para medir sinais. O objeto {nome}",
                             add_special_tokens=False).ids
            alvo = tok.encode(" " + nome, add_special_tokens=False).ids
            pos = [i for i in range(len(ids) - len(alvo) + 1) if ids[i:i + len(alvo)] == alvo]
            x = torch.tensor([ids], device=dispositivo)
            lp_ = F.log_softmax(modelo(x)[0][0].float()[:-1], -1)
            perda = -lp_.gather(-1, x[0, 1:, None])[:, 0]
            a, b = pos[0], pos[-1]
            nomes1.append(perda[a - 1:a - 1 + len(alvo)].mean().item())
            nomes2.append(perda[b - 1:b - 1 + len(alvo)].mean().item())
    modelo.train()
    return {"copia_top1": float(np.mean(acertos)), "perda_1a_vez": float(np.mean(p1)),
            "perda_2a_vez": float(np.mean(p2)), "nome_1a_mencao": float(np.mean(nomes1)),
            "nome_2a_mencao": float(np.mean(nomes2))}


def etapa_treinar(args):
    import numpy as np
    import torch
    import torch.nn.functional as F
    from tokenizers import Tokenizer
    from linguagem_profunda import Configuracao, LinguagemProfunda

    dados = Path(args.dados)
    origem, ckpt = Path(args.origem), Path(args.checkpoint)
    if origem.resolve() == ckpt.resolve():
        raise SystemExit("--checkpoint não pode ser o checkpoint de origem: a origem nunca é sobrescrita.")
    if sha256(dados / "tokenizer.json") != TOKENIZER_SHA256:
        raise SystemExit("tokenizer.json dos dados difere do tokenizador da base.")
    tok = Tokenizer.from_file(str(dados / "tokenizer.json"))
    dispositivo = args.dispositivo
    treino = np.memmap(dados / "treino.bin", dtype=np.uint16, mode="r")
    valid = np.memmap(dados / "validacao.bin", dtype=np.uint16, mode="r")
    config = Configuracao(**pt.MODELO)
    modelo = LinguagemProfunda(config).to(dispositivo)
    decai = [p for n, p in modelo.named_parameters() if p.dim() >= 2]
    sem_decai = [p for n, p in modelo.named_parameters() if p.dim() < 2]
    opt = torch.optim.AdamW([{"params": decai, "weight_decay": 0.1}, {"params": sem_decai, "weight_decay": 0.0}],
                            lr=args.lr, betas=(0.9, 0.95), fused=dispositivo == "cuda")
    bf16 = dispositivo == "cuda" and torch.cuda.is_bf16_supported()
    tipo = torch.bfloat16 if bf16 else torch.float16
    escala = torch.amp.GradScaler("cuda", enabled=dispositivo == "cuda" and not bf16)

    if ckpt.exists():
        estado = torch.load(ckpt, map_location="cpu", weights_only=False)
        print("retomando do checkpoint continuado:", ckpt, flush=True)
    else:
        if not origem.exists():
            raise SystemExit(f"checkpoint de origem não encontrado: {origem}")
        estado = torch.load(origem, map_location="cpu", weights_only=False)
        estado = {**estado, "passo_inicial": estado["passo"], "historico": [],
                  "origem": str(origem), "origem_sha256": sha256(origem)}
        print("partindo do checkpoint de pré-treino (só leitura):", origem, "passo", estado["passo"], flush=True)
    modelo.load_state_dict(estado["modelo"])
    opt.load_state_dict(estado["opt"])
    escala.load_state_dict(estado["escala"])
    passo, passo_inicial = estado["passo"], estado["passo_inicial"]
    melhor, melhor_estado = estado["melhor"], estado["melhor_estado"]
    historico = estado["historico"]
    origem_info = {"origem": estado["origem"], "origem_sha256": estado["origem_sha256"]}
    gerador = np.random.default_rng(pt.SEMENTE + 1_000_003 + passo)
    fim = passo_inicial + args.passos_extra
    print("parâmetros:", sum(p.numel() for p in modelo.parameters()), "| tokens de treino:", len(treino),
          "| passo", passo, "→", fim, "| frac repetição", args.frac_repeticao, flush=True)

    def taxa(p):
        rel = p - passo_inicial
        if rel < args.aquecimento:
            return args.lr * (rel + 1) / args.aquecimento
        progresso = min(1.0, (rel - args.aquecimento) / max(1, args.passos_extra - args.aquecimento))
        return args.lr * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * progresso)))

    @torch.no_grad()
    def validar():
        modelo.eval()
        g = np.random.default_rng(pt.SEMENTE)
        perdas = []
        for _ in range(args.lotes_validacao):
            x, y = pt._lote(valid, config.contexto, args.lote, g, np, torch, dispositivo)
            with torch.autocast(device_type="cuda", dtype=tipo, enabled=dispositivo == "cuda"):
                perdas.append(modelo(x, y)[1].item())
        modelo.train()
        return sum(perdas) / len(perdas)

    def registrar_sonda():
        with torch.autocast(device_type="cuda", dtype=tipo, enabled=dispositivo == "cuda"):
            s = sonda_copia(modelo, tok, dispositivo, np, torch, F)
        s.update({"passo": passo, "tokens_extra": (passo - passo_inicial) * args.lote * config.contexto,
                  "validacao": validar()})
        historico.append(s)
        print("SONDA passo %d | cópia top-1 %.1f%% | 2ª vez %.2f nats (1ª %.2f) | nome 2ª menção %.2f nats | validação %.4f" % (
            passo, 100 * s["copia_top1"], s["perda_2a_vez"], s["perda_1a_vez"], s["nome_2a_mencao"], s["validacao"]),
            flush=True)
        return s

    def checkpoint():
        pt.salvar_atomico({"modelo": modelo.state_dict(), "opt": opt.state_dict(), "escala": escala.state_dict(),
                           "passo": passo, "passo_inicial": passo_inicial, "melhor": melhor,
                           "melhor_estado": melhor_estado, "historico": historico,
                           "config": dataclasses.asdict(config), **origem_info}, ckpt)
        print("checkpoint gravado no passo", passo, "->", ckpt, flush=True)

    if not historico:
        registrar_sonda()  # linha de base, antes de qualquer passo extra
    inicio, ultimo, reps = time.time(), time.time(), 0
    modelo.train()
    while passo < fim:
        for g in opt.param_groups:
            g["lr"] = taxa(passo)
        xn, yn, n_rep = janelas_com_repeticao(treino, config.contexto, args.lote, gerador, args.frac_repeticao, np)
        reps += n_rep
        x = torch.from_numpy(xn).to(dispositivo, non_blocking=True)
        y = torch.from_numpy(yn).to(dispositivo, non_blocking=True)
        with torch.autocast(device_type="cuda", dtype=tipo, enabled=dispositivo == "cuda"):
            perda = modelo(x, y)[1]
        opt.zero_grad(set_to_none=True)
        escala.scale(perda).backward()
        escala.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
        escala.step(opt)
        escala.update()
        passo += 1
        if passo % 100 == 0:
            agora = time.time()
            print("passo %d/%d perda %.3f lr %.2e | %.0f tokens/s | janelas com repetição %d" % (
                passo, fim, perda.item(), taxa(passo), 100 * args.lote * config.contexto / (agora - ultimo), reps),
                flush=True)
            ultimo, reps = agora, 0
        if (passo - passo_inicial) % args.sonda_a_cada == 0 or passo == fim:
            s = registrar_sonda()
            if s["validacao"] < melhor:
                melhor = s["validacao"]
                melhor_estado = {k: t.detach().to("cpu", copy=True) for k, t in modelo.state_dict().items()}
        fim_tempo = args.max_horas and time.time() - inicio > args.max_horas * 3600
        if (passo - passo_inicial) % args.checkpoint_a_cada == 0 or passo == fim or fim_tempo:
            checkpoint()
        if fim_tempo:
            print("Orçamento de tempo atingido no passo", passo, "- rode de novo para continuar.", flush=True)
            return
    print("pré-treino continuado concluído no passo", passo, flush=True)


def etapa_exportar(args):
    import torch
    import linguagem_profunda as lp
    dados, saida, ckpt = Path(args.dados), Path(args.base), Path(args.checkpoint)
    estado = torch.load(ckpt, map_location="cpu", weights_only=False)
    fim = estado["passo_inicial"] + args.passos_extra
    if estado["passo"] < fim:
        raise SystemExit("Pré-treino continuado incompleto (%d de %d passos)." % (estado["passo"], fim))
    saida.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(dados / "tokenizer.json", saida / "tokenizer.json")
    sha_tok = sha256(saida / "tokenizer.json")
    if sha_tok != TOKENIZER_SHA256:
        raise SystemExit("tokenizer exportado difere do da base")
    # Exporta o estado final: o objetivo da fase é a cópia, medida na sonda, não só a perda.
    torch.save({"versao": lp.VERSAO, "modelo": estado["modelo"], "config": estado["config"],
                "passo": estado["passo"],
                "execucao": {"tokenizer_sha256": sha_tok, "pesos_externos": False,
                             "origem": estado["origem"], "origem_sha256": estado["origem_sha256"],
                             "passo_inicial": estado["passo_inicial"], "frac_repeticao": args.frac_repeticao}},
               saida / "pesos.pt")
    hist = estado["historico"]
    (saida / "relatorio.json").write_text(json.dumps({
        "papel": "17M do CRIVO após pré-treino continuado (fase 2 do salto)",
        "config": estado["config"], "passo_inicial": estado["passo_inicial"], "passo_final": estado["passo"],
        "tokens_extra": hist[-1]["tokens_extra"] if hist else None,
        "sonda_inicial": hist[0] if hist else None, "sonda_final": hist[-1] if hist else None,
        "historico_sonda": hist, "melhor_validacao": estado["melhor"],
        "pesos_sha256": sha256(saida / "pesos.pt"), "tokenizer_sha256": sha_tok,
        "pesos_externos": False, "ativo_no_chat": False, "promovido": False}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("base exportada em", saida, flush=True)
    if hist:
        print("cópia top-1: %.1f%% → %.1f%% | nome 2ª menção: %.2f → %.2f nats" % (
            100 * hist[0]["copia_top1"], 100 * hist[-1]["copia_top1"],
            hist[0]["nome_2a_mencao"], hist[-1]["nome_2a_mencao"]), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--etapa", required=True, choices=("treinar", "exportar"))
    ap.add_argument("--dados", default="/content/crivo-dados")
    ap.add_argument("--origem", default="/content/drive/MyDrive/CRIVO/transformer-leitor/checkpoint.pt")
    ap.add_argument("--checkpoint", default="/content/drive/MyDrive/CRIVO/transformer-17m-continuo/checkpoint.pt")
    ap.add_argument("--base", default="/content/drive/MyDrive/CRIVO/transformer-17m-continuo/base")
    ap.add_argument("--passos-extra", type=int, default=40000)
    ap.add_argument("--lote", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--aquecimento", type=int, default=500)
    ap.add_argument("--frac-repeticao", type=float, default=0.05)
    ap.add_argument("--sonda-a-cada", type=int, default=2500)
    ap.add_argument("--lotes-validacao", type=int, default=50)
    ap.add_argument("--checkpoint-a-cada", type=int, default=5000)
    ap.add_argument("--max-horas", type=float, default=0, help="pausa com checkpoint depois desse tempo")
    ap.add_argument("--dispositivo", default=None)
    args = ap.parse_args()
    # Arquivo único sobrescrito; cada versão substituída vai para a lixeira do Drive (~280 MB).
    # 5.000 passos ≈ 75 min na T4: limita a perda quando o Colab cai sem aviso.
    if args.etapa == "treinar" and "/drive/" in args.checkpoint and args.checkpoint_a_cada < 5000:
        raise SystemExit("Checkpoint no Drive a cada menos de 5.000 passos enche a lixeira do Drive; use 5.000 ou mais.")
    if args.dispositivo is None:
        import torch
        args.dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    random.seed(pt.SEMENTE)
    {"treinar": etapa_treinar, "exportar": etapa_exportar}[args.etapa](args)


if __name__ == "__main__":
    main()
