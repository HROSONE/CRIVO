#!/usr/bin/env python3
"""Escola Cognitiva v2: reforço de ligação de entidades no Transformer 17M.

Parte do checkpoint v1 já treinado para diálogo. A única intervenção nova é
ponderar mais os tokens que realizam pessoa, objeto ou atividade na resposta.
Não adiciona cabeças, parâmetros de inferência, regras de runtime ou RAG.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

import torch
from torch.nn import functional as F

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
V1 = AQUI.parent / "escola_transformer_17m_20261011"
sys.path[:0] = [str(RAIZ), str(V1)]

import treinar_escola as v1  # noqa: E402
import curriculo as curr  # noqa: E402
import preparar_holdout as holdout_v2  # noqa: E402

SEMENTE = 202610113
ENTRADA_SHA = "849bc4655820f8cd1f445539a1bd0f01959f03ce38145ece460c0fe27568c661"
TOKENIZER_SHA = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"
BASE_PRETREINO_SHA = "16102a72b21031b8bee2b4edfa633a359f7f08c5beab552b05f294e656b0cc67"
PARAMETROS = 17_428_224
PASSOS = 800
LOTE = 16
LR = 1.5e-5
PESO_SLOT = 3.0


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha_json(o):
    return hashlib.sha256(json.dumps(
        o, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


def carregar_entrada(pasta, dispositivo):
    from tokenizers import Tokenizer

    pasta = Path(pasta)
    pp, tp = pasta / "pesos.pt", pasta / "tokenizer.json"
    if sha(pp) != ENTRADA_SHA or sha(tp) != TOKENIZER_SHA:
        raise ValueError("checkpoint/tokenizador de entrada não correspondem ao protocolo v2")
    estado = torch.load(pp, map_location="cpu", weights_only=True)
    if estado.get("config") != v1.CONFIG:
        raise ValueError("configuração inesperada no checkpoint v1")
    exe = estado.get("execucao", {})
    if exe.get("pesos_externos") is not False:
        raise ValueError("checkpoint com proveniência externa")
    if exe.get("base_pretreino_sha256") != BASE_PRETREINO_SHA:
        raise ValueError("checkpoint não deriva da base própria aprovada")
    escola = exe.get("escola_cognitiva", {})
    if escola.get("versao") != 1 or escola.get("ativo_no_chat") is not False:
        raise ValueError("entrada não é o candidato v1 inativo esperado")

    modelo = v1.LinguagemProfunda(v1.Configuracao(**v1.CONFIG))
    modelo.load_state_dict(estado["modelo"], strict=True)
    if sum(p.numel() for p in modelo.parameters()) != PARAMETROS:
        raise ValueError("contagem de parâmetros inesperada")
    modelo.to(dispositivo)

    tok = Tokenizer.from_file(str(tp))
    tok.encode_special_tokens = True
    if tok.get_vocab_size() != 8192:
        raise ValueError("vocabulário incompatível")
    return modelo, tok, estado


def slots_da_resposta(ex):
    """Retorna somente valores semânticos que a resposta precisa realizar."""
    op, r = ex["operacao"], ex["resposta"]
    nomes = re.findall(r"[A-Za-zÀ-ÿ]+-\d+", r)
    if op in ("recordar_pessoa", "corrigir_pessoa", "pedir_detalhe"):
        return nomes[:1]
    if op == "recordar_objeto":
        achados = [x for x in curr.OBJETOS if x in r]
        if achados:
            return achados[:1]
        q = re.search(r"(?:objeto|item)(?: vigente| atual| desse contexto| associado)? (?:é|=) (.+?)[.!?]$", r, re.I)
        return [q.group(1)] if q else []
    if op == "guardar_hipotese":
        achados = [x for x in curr.ATIVIDADES if x in r]
        if achados:
            return achados[:1]
        q = re.match(r"(.+?) continua provisória", r, re.I)
        return [q.group(1)] if q else []
    if op == "mensagem_sem_horario":
        atividades = [x for x in curr.ATIVIDADES if x in r]
        return nomes[:1] + atividades[:1]
    return []


def pesos_tokens(tokenizer, texto, valores):
    enc = tokenizer.encode(texto, add_special_tokens=False)
    pesos = [1.0] * len(enc.ids)
    spans = []
    for valor in valores:
        inicio = 0
        while True:
            i = texto.find(valor, inicio)
            if i < 0:
                break
            spans.append((i, i + len(valor)))
            inicio = i + max(1, len(valor))
    for j, (a, b) in enumerate(enc.offsets):
        if any(max(a, x) < min(b, y) for x, y in spans):
            pesos[j] = PESO_SLOT
    if valores and not any(p > 1.0 for p in pesos):
        raise ValueError("slot sem alinhamento no alvo: " + repr((texto, valores)))
    return enc.ids, pesos


def preparar(tokenizer, ex, contexto, ponderar=False):
    fim = tokenizer.token_to_id("<fim>")
    if ponderar:
        resp, wr = pesos_tokens(tokenizer, ex["resposta"], slots_da_resposta(ex))
    else:
        resp = tokenizer.encode(ex["resposta"], add_special_tokens=False).ids
        wr = [1.0] * len(resp)
    resp = list(resp) + [fim]
    wr = list(wr) + [1.0]

    fonte, usado, total = v1.fonte_compacta(tokenizer, ex, resp, contexto)
    seq = fonte + resp
    if len(seq) - 1 > contexto:
        raise AssertionError("compactação falhou")
    x, y = seq[:-1], seq[1:]
    ini = len(fonte) - 1
    pesos = [0.0] * ini + wr
    if len(pesos) != len(y):
        raise AssertionError("máscara de pesos desalinhada")
    return {
        "id": ex["id"], "x": x, "y": [-100] * ini + y[ini:], "pesos": pesos,
        "pos": ini, "primeiro": resp[0], "fonte": fonte, "operacao": ex["operacao"],
        "resposta": ex["resposta"], "ex": ex, "hist_usado": usado, "hist_total": total,
    }


def batch(xs, pad, dev):
    n = max(len(z["x"]) for z in xs)
    x = torch.full((len(xs), n), pad, dtype=torch.long)
    y = torch.full_like(x, -100)
    w = torch.zeros((len(xs), n), dtype=torch.float32)
    for i, z in enumerate(xs):
        x[i, :len(z["x"])] = torch.tensor(z["x"])
        y[i, :len(z["y"])] = torch.tensor(z["y"])
        w[i, :len(z["pesos"])] = torch.tensor(z["pesos"])
    return x.to(dev), y.to(dev), w.to(dev)


def treinar(modelo, tokenizer, dev):
    dados = [preparar(tokenizer, e, modelo.config.contexto, ponderar=True)
             for e in curr.gerar_treino()]
    if len(dados) != 3072:
        raise ValueError("currículo v1 inesperado")

    for p in modelo.parameters():
        p.requires_grad = False
    for bloco in modelo.blocos[4:]:
        for p in bloco.parameters():
            p.requires_grad = True
    for p in modelo.norm.parameters():
        p.requires_grad = True

    pars = [p for p in modelo.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(pars, lr=LR, weight_decay=.01)
    rng = random.Random(SEMENTE)
    ordem = list(range(len(dados)))
    cur = len(ordem)
    torch.manual_seed(SEMENTE)
    modelo.train()
    for b in modelo.blocos[:4]:
        b.eval()

    inicio = time.time()
    janela = defaultdict(float)
    for passo in range(1, PASSOS + 1):
        if cur + LOTE > len(ordem):
            rng.shuffle(ordem)
            cur = 0
        lote = [dados[i] for i in ordem[cur:cur + LOTE]]
        cur += LOTE
        x, y, w = batch(lote, tokenizer.token_to_id("<pad>"), dev)
        _, logits = v1.hidden_logits(modelo, x, True)
        bruto = F.cross_entropy(
            logits.reshape(-1, 8192), y.reshape(-1),
            ignore_index=-100, reduction="none"
        ).view_as(y)
        perda = (bruto * w).sum() / w.sum().clamp_min(1.0)

        opt.zero_grad(set_to_none=True)
        perda.backward()
        gn = torch.nn.utils.clip_grad_norm_(pars, 1.0)
        opt.step()
        janela["loss"] += float(perda)
        janela["grad"] += float(gn)
        if passo % 100 == 0:
            print(json.dumps({
                "passo": passo,
                "loss": round(janela["loss"] / 100, 5),
                "grad": round(janela["grad"] / 100, 5),
                "segundos": round(time.time() - inicio, 1),
            }), flush=True)
            janela.clear()

    return {
        "passos": PASSOS, "lote": LOTE, "lr": LR, "peso_slot": PESO_SLOT,
        "treinaveis_modelo": sum(p.numel() for p in modelo.parameters() if p.requires_grad),
        "parametros_extras_inferencia": 0,
        "segundos": time.time() - inicio,
    }


def abrir_holdout():
    man = json.loads((AQUI / "manifesto_holdout.json").read_text(encoding="utf-8"))
    if sha(AQUI / "preparar_holdout.py") != man["gerador_sha256"]:
        raise ValueError("gerador do holdout v2 mudou")
    exemplos = holdout_v2.gerar()
    por = {op: sum(x["operacao"] == op for x in exemplos) for op in holdout_v2.OPERACOES}
    pacote = {
        "versao": 2,
        "semente": holdout_v2.SEMENTE,
        "congelado_antes_do_treino": True,
        "auditoria": {
            "aprovado": True, "exemplos": 120, "familias": len(holdout_v2.FAMILIAS),
            "mensagens_exatas_repetidas": 0, "por_operacao": por,
        },
        "exemplos": exemplos,
    }
    if sha_json(pacote) != man["holdout_sha256_canonico"]:
        raise ValueError("hash canônico do holdout v2 mudou")
    return exemplos, man


def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s).casefold()).strip()


def valores_esperados(ex):
    r, op = ex["resposta"], ex["operacao"]
    nomes = re.findall(r"[A-Za-zÀ-ÿ]+-\d+", r)
    if op in ("recordar_pessoa", "corrigir_pessoa", "pedir_detalhe"):
        return nomes[:1]
    if op == "recordar_objeto":
        q = re.match(r"O item vigente é (.+)\.$", r)
        return [q.group(1)] if q else []
    if op == "guardar_hipotese":
        q = re.match(r"(.+?) continua provisória", r)
        return [q.group(1)] if q else []
    if op == "mensagem_sem_horario":
        q = re.search(r"combinar (.+) comigo\?", r)
        return nomes[:1] + ([q.group(1)] if q else [])
    return []


def pontuar(ex, saida):
    n = norm(saida)
    vals = valores_esperados(ex)
    slot = bool(vals) and all(norm(x) in n for x in vals)
    op = ex["operacao"]
    if op in ("recordar_pessoa", "recordar_objeto", "corrigir_pessoa"):
        ok = slot
    elif op == "guardar_hipotese":
        ok = slot and any(x in n for x in ("não", "provis", "confirma", "hipótese", "possibilidade"))
    elif op == "mensagem_sem_horario":
        ok = slot and ("?" in saida or "convite" in n) and not re.search(
            r"\b\d{1,2}(?::\d{2})?\s*(?:h|hora|horas)\b", n
        )
    else:
        pergunta = "?" in saida or any(x in n for x in ("o que", "qual ", "que item", "que coisa"))
        obj = ""
        for z in ex["historico"]:
            q = re.search(r"objeto=([^;.]+)", z["texto"], re.I)
            if q:
                obj = norm(q.group(1))
                break
        ok = slot and pergunta and not (obj and obj in n)
    return bool(slot), bool(ok)


@torch.no_grad()
def avaliar(modelo, tokenizer, exs, dev):
    modelo.eval()
    prep = [preparar(tokenizer, e, modelo.config.contexto, ponderar=False) for e in exs]
    ce = nt = first = exact = slotn = opn = 0
    por = defaultdict(lambda: {"n": 0, "operacao": 0, "slot": 0, "exata": 0})
    det = []
    fim = tokenizer.token_to_id("<fim>")
    proib = [tokenizer.token_to_id(x) for x in v1.ESPECIAIS[:-1]]

    for z in prep:
        x = torch.tensor([z["x"]], device=dev)
        y = torch.tensor([z["y"]], device=dev)
        _, log = v1.hidden_logits(modelo, x)
        ce += float(F.cross_entropy(
            log.reshape(-1, 8192), y.reshape(-1),
            ignore_index=-100, reduction="sum"))
        nt += int((y != -100).sum())
        first += int(int(log[0, z["pos"]].argmax()) == z["primeiro"])
        ids, terminou = modelo.gerar(
            z["fonte"], fim, max_tokens=40, temperatura=0, top_k=0,
            semente=SEMENTE, proibidos=proib)
        saida = tokenizer.decode(ids)
        exata = norm(saida) == norm(z["resposta"])
        sl, ok = pontuar(z["ex"], saida)
        exact += exata
        slotn += sl
        opn += ok
        q = por[z["operacao"]]
        q["n"] += 1
        q["operacao"] += ok
        q["slot"] += sl
        q["exata"] += exata
        det.append({
            "id": z["id"], "operacao": z["operacao"], "alvo": z["resposta"],
            "saida": saida, "terminou": terminou, "slot": sl,
            "operacao_correta": ok, "exata": exata,
            "historico_usado": z["hist_usado"], "historico_total": z["hist_total"],
        })

    n = len(prep)
    po = {k: {**v,
              "operacao_taxa": v["operacao"] / v["n"],
              "slot_taxa": v["slot"] / v["n"],
              "exata_taxa": v["exata"] / v["n"]}
          for k, v in sorted(por.items())}
    return {
        "n": n, "ce": ce / nt, "primeiro_token": first / n, "exata": exact / n,
        "slot": slotn / n, "operacao": opn / n, "por_operacao": po, "detalhes": det,
    }


def gates(base, candidato, pb, pc):
    minimo = min(v["operacao_taxa"] for v in candidato["por_operacao"].values())
    gp = candidato["primeiro_token"] - base["primeiro_token"]
    gc = (base["ce"] - candidato["ce"]) / base["ce"]
    rp = pc["ce"] / pb["ce"]
    g = {
        "operacao_min_60": candidato["operacao"] >= .60,
        "cada_operacao_min_35": minimo >= .35,
        "slot_min_70": candidato["slot"] >= .70,
        "primeiro_token_ganho_5pp": gp >= .05,
        "ce_melhora_10pct": gc >= .10,
        "preservacao_ate_3pct": rp <= 1.03,
    }
    return g, {
        "min_operacao": minimo, "ganho_primeiro_token_pp": gp * 100,
        "ganho_ce_relativo": gc, "preservacao_ce_relativa": rp,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entrada", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--dispositivo", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    dev = torch.device(args.dispositivo)

    protocolo = json.loads((AQUI / "protocolo.json").read_text(encoding="utf-8"))
    if protocolo["entrada"]["checkpoint_sha256"] != ENTRADA_SHA:
        raise ValueError("protocolo e checkpoint de entrada divergem")
    if protocolo["intervencao"]["passos"] != PASSOS or protocolo["intervencao"]["peso_slot"] != PESO_SLOT:
        raise ValueError("hiperparâmetros divergem do pré-compromisso")

    random.seed(SEMENTE)
    torch.manual_seed(SEMENTE)
    if dev.type == "cuda":
        torch.cuda.manual_seed_all(SEMENTE)

    modelo, tokenizer, estado = carregar_entrada(args.entrada, dev)
    treino = treinar(modelo, tokenizer, dev)

    print("800 passos concluídos; abrindo holdout prospectivo v2...", flush=True)
    hold, manifesto = abrir_holdout()
    textos = json.loads((V1 / "preservacao_portugues.json").read_text(encoding="utf-8"))["textos"]

    base, tok_base, _ = carregar_entrada(args.entrada, dev)
    ab = avaliar(base, tok_base, hold, dev)
    pb = v1.preservacao(base, tok_base, textos, dev)
    del base
    if dev.type == "cuda":
        torch.cuda.empty_cache()

    ac = avaliar(modelo, tokenizer, hold, dev)
    pc = v1.preservacao(modelo, tokenizer, textos, dev)
    g, derivados = gates(ab, ac, pb, pc)
    elegivel = all(g.values())
    simples = lambda x: {k: v for k, v in x.items() if k != "detalhes"}

    out = Path(args.saida)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(args.entrada) / "tokenizer.json", out / "tokenizer.json")
    execucao = dict(estado.get("execucao", {}))
    execucao["escola_cognitiva_v2"] = {
        "versao": 2, "passos_adicionais": PASSOS, "peso_slot": PESO_SLOT,
        "parametros_extras_inferencia": 0, "ativo_no_chat": False,
    }
    ck = {
        "versao": 1,
        "modelo": {k: v.detach().cpu() for k, v in modelo.state_dict().items()},
        "config": estado["config"], "passo": estado.get("passo", 0), "execucao": execucao,
    }
    torch.save(ck, out / "pesos.pt")
    cksha = sha(out / "pesos.pt")

    resultado = {
        "versao": 2,
        "origem_checkpoint_sha256": ENTRADA_SHA,
        "parametros": PARAMETROS,
        "treino": treino,
        "holdout": manifesto,
        "avaliacao_entrada": simples(ab),
        "avaliacao_candidato": simples(ac),
        "preservacao_entrada": pb,
        "preservacao_candidato": pc,
        "gates": g,
        "derivados": derivados,
        "elegivel_promocao": elegivel,
        "ativo_no_chat": False,
        "checkpoint_sha256": cksha,
        "detalhes_holdout": ac["detalhes"],
    }
    (out / "resultados.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "meta.json").write_text(json.dumps({
        "papel": "candidato v2 de ligação de entidades do Transformer próprio 17M",
        "origem_checkpoint_sha256": ENTRADA_SHA,
        "checkpoint_sha256": cksha,
        "elegivel_promocao": elegivel,
        "ativo_no_chat": False,
        "pesos_externos": False,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "elegivel_promocao": elegivel,
        "gates": g,
        "entrada": simples(ab),
        "candidato": simples(ac),
        "preservacao_relativa": derivados["preservacao_ce_relativa"],
        "checkpoint_sha256": cksha,
        "ativo_no_chat": False,
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
