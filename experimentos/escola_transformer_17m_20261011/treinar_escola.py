#!/usr/bin/env python3
"""Escola Cognitiva v1 para o Transformer próprio de 17,43M do CRIVO.

Princípios:
- começa somente da base própria cujo SHA-256 está pré-comprometido;
- não usa modelo externo nem rótulos na inferência;
- congela embeddings + metade inferior do Transformer;
- ensina resposta e duas fatorações treino-only: AÇÃO e FOCO;
- abre o holdout prospectivo somente depois dos 1200 passos fixos;
- nunca ativa o checkpoint público automaticamente.
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
from collections import Counter, defaultdict
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AQUI))

from linguagem_profunda import Configuracao, LinguagemProfunda, ESPECIAIS  # noqa: E402
from curriculo import gerar_treino  # noqa: E402

SEMENTE = 20261011
BASE_PESOS_SHA = "16102a72b21031b8bee2b4edfa633a359f7f08c5beab552b05f294e656b0cc67"
BASE_TOKENIZER_SHA = "6e3704ce921851122953b8ac20c05e3a131f9cf0fa3c76d6e2391c4ec3efc88f"
BASE_PARAMETROS = 17_428_224
BASE_PASSO = 20_000
CONFIG_ESPERADA = {
    "vocabulario": 8192, "dimensao": 384, "camadas": 8,
    "cabecas": 8, "contexto": 256, "dropout": 0.1,
}
ACOES = ("recordar", "atualizar", "epistemico", "compor", "esclarecer")
FOCOS = ("pessoa", "objeto", "nenhum")
PASSOS = 1200
LOTE = 16
LR = 3e-5
LAMBDA_ACAO = 0.08
LAMBDA_FOCO = 0.08
GRAD_CLIP = 1.0


def sha(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def sha_json(obj):
    bruto = json.dumps(obj, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")).encode()
    return hashlib.sha256(bruto).hexdigest()


def carregar_base(diretorio, dispositivo):
    """Carrega somente a base legada conhecida, sem afrouxar o loader geral."""
    from tokenizers import Tokenizer
    diretorio = Path(diretorio)
    pesos = diretorio / "pesos.pt"
    tokenizer_path = diretorio / "tokenizer.json"
    if sha(pesos) != BASE_PESOS_SHA:
        raise ValueError("pesos.pt não é a base 17M pré-comprometida")
    if sha(tokenizer_path) != BASE_TOKENIZER_SHA:
        raise ValueError("tokenizer.json não é o tokenizador pré-comprometido")
    estado = torch.load(pesos, map_location="cpu", weights_only=True)
    if estado.get("config") != CONFIG_ESPERADA:
        raise ValueError("configuração da base difere do protocolo")
    if estado.get("passo") != BASE_PASSO:
        raise ValueError("base não está no passo 20000")
    execucao = estado.get("execucao", {})
    if execucao.get("tokenizer_sha256") != BASE_TOKENIZER_SHA:
        raise ValueError("checkpoint referencia outro tokenizador")
    if execucao.get("pesos_externos") is not False:
        raise ValueError("proveniência da base não confirma pesos próprios")
    modelo = LinguagemProfunda(Configuracao(**estado["config"]))
    modelo.load_state_dict(estado["modelo"], strict=True)
    if sum(p.numel() for p in modelo.parameters()) != BASE_PARAMETROS:
        raise ValueError("contagem de parâmetros inesperada")
    modelo.to(dispositivo)
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    tokenizer.encode_special_tokens = True
    if tokenizer.get_vocab_size() != CONFIG_ESPERADA["vocabulario"]:
        raise ValueError("vocabulário incompatível")
    return modelo, tokenizer, estado


def codificar_texto(tokenizer, texto):
    return tokenizer.encode(texto, add_special_tokens=False).ids


def tokens_exemplo(tokenizer, ex, contexto):
    fim = tokenizer.token_to_id("<fim>")
    papel = {
        "usuario": tokenizer.token_to_id("<usuario>"),
        "assistente": tokenizer.token_to_id("<assistente>"),
    }
    fonte = []
    for turno in ex["historico"]:
        if turno["papel"] not in papel:
            continue
        fonte += [papel[turno["papel"]]]
        fonte += codificar_texto(tokenizer, turno["texto"])
        fonte += [fim]
    fonte += [papel["usuario"]]
    fonte += codificar_texto(tokenizer, ex["mensagem"])
    fonte += [fim, papel["assistente"]]
    resposta = codificar_texto(tokenizer, ex["resposta"]) + [fim]
    completo = fonte + resposta
    if len(completo) - 1 > contexto:
        raise ValueError(
            f"{ex['id']} excede contexto: {len(completo)-1} > {contexto}; "
            "o currículo deve ser corrigido, não truncado silenciosamente")
    x = completo[:-1]
    y = completo[1:]
    inicio_resposta = len(fonte) - 1
    y_masc = [-100] * inicio_resposta + y[inicio_resposta:]
    return {
        "id": ex["id"], "x": x, "y": y_masc,
        "pos_aux": len(fonte) - 1, "primeiro_alvo": resposta[0],
        "fonte": fonte, "resposta_ids": resposta[:-1],
        "acao": ACOES.index(ex["acao"]), "foco": FOCOS.index(ex["foco"]),
        "operacao": ex["operacao"], "resposta": ex["resposta"], "exemplo": ex,
    }


def colar(lote, pad, dispositivo):
    t = max(len(e["x"]) for e in lote)
    x = torch.full((len(lote), t), pad, dtype=torch.long)
    y = torch.full((len(lote), t), -100, dtype=torch.long)
    pos = torch.empty(len(lote), dtype=torch.long)
    acao = torch.empty(len(lote), dtype=torch.long)
    foco = torch.empty(len(lote), dtype=torch.long)
    for i, e in enumerate(lote):
        x[i, :len(e["x"])] = torch.tensor(e["x"])
        y[i, :len(e["y"])] = torch.tensor(e["y"])
        pos[i] = e["pos_aux"]
        acao[i] = e["acao"]
        foco[i] = e["foco"]
    return (x.to(dispositivo), y.to(dispositivo), pos.to(dispositivo),
            acao.to(dispositivo), foco.to(dispositivo))


def ocultos_logits(modelo, ids, treino_topo=False):
    """Forward que expõe o estado latente no token <assistente>."""
    t = ids.shape[1]
    if treino_topo:
        with torch.no_grad():
            x = modelo.embedding(ids) + modelo.posicao(torch.arange(t, device=ids.device))
            for bloco in modelo.blocos[:4]:
                x = bloco(x)
        for bloco in modelo.blocos[4:]:
            x = bloco(x)
    else:
        x = modelo.embedding(ids) + modelo.posicao(torch.arange(t, device=ids.device))
        for bloco in modelo.blocos:
            x = bloco(x)
    h = modelo.norm(x)
    logits = F.linear(h, modelo.embedding.weight)
    return h, logits


def configurar_treino(modelo):
    for p in modelo.parameters():
        p.requires_grad = False
    for bloco in modelo.blocos[4:]:
        for p in bloco.parameters():
            p.requires_grad = True
    for p in modelo.norm.parameters():
        p.requires_grad = True
    return sum(p.numel() for p in modelo.parameters() if p.requires_grad)


def validar_curriculo(tokenizer, exemplos, contexto):
    preparados = [tokens_exemplo(tokenizer, e, contexto) for e in exemplos]
    por_op = Counter(e["operacao"] for e in exemplos)
    if set(por_op.values()) != {512}:
        raise ValueError(f"currículo desbalanceado: {por_op}")
    return preparados


def iter_lotes(preparados):
    rng = random.Random(SEMENTE)
    ordem = list(range(len(preparados)))
    cursor = len(ordem)
    while True:
        if cursor + LOTE > len(ordem):
            rng.shuffle(ordem)
            cursor = 0
        ids = ordem[cursor:cursor + LOTE]
        cursor += LOTE
        yield [preparados[i] for i in ids]


def treinar(modelo, tokenizer, exemplos, dispositivo):
    torch.manual_seed(SEMENTE + 1)
    cabeca_acao = nn.Linear(modelo.config.dimensao, len(ACOES)).to(dispositivo)
    cabeca_foco = nn.Linear(modelo.config.dimensao, len(FOCOS)).to(dispositivo)
    treinaveis_modelo = configurar_treino(modelo)
    parametros = [p for p in modelo.parameters() if p.requires_grad]
    parametros += list(cabeca_acao.parameters()) + list(cabeca_foco.parameters())
    otimizador = torch.optim.AdamW(parametros, lr=LR, weight_decay=0.01)
    preparados = validar_curriculo(tokenizer, exemplos, modelo.config.contexto)
    lotes = iter_lotes(preparados)

    torch.manual_seed(SEMENTE)
    modelo.train()
    for bloco in modelo.blocos[:4]:
        bloco.eval()
    cabeca_acao.train()
    cabeca_foco.train()

    janela = defaultdict(float)
    inicio = time.time()
    for passo in range(1, PASSOS + 1):
        lote = next(lotes)
        x, y, pos, alvo_a, alvo_f = colar(
            lote, tokenizer.token_to_id("<pad>"), dispositivo)
        h, logits = ocultos_logits(modelo, x, treino_topo=True)
        perda_gen = F.cross_entropy(
            logits.reshape(-1, modelo.config.vocabulario), y.reshape(-1), ignore_index=-100)
        reps = h[torch.arange(h.shape[0], device=h.device), pos]
        perda_a = F.cross_entropy(cabeca_acao(reps), alvo_a)
        perda_f = F.cross_entropy(cabeca_foco(reps), alvo_f)
        perda = perda_gen + LAMBDA_ACAO * perda_a + LAMBDA_FOCO * perda_f

        otimizador.zero_grad(set_to_none=True)
        perda.backward()
        norma = torch.nn.utils.clip_grad_norm_(parametros, GRAD_CLIP)
        otimizador.step()

        janela["total"] += float(perda.detach())
        janela["gen"] += float(perda_gen.detach())
        janela["acao"] += float(perda_a.detach())
        janela["foco"] += float(perda_f.detach())
        janela["norma"] += float(norma)
        if passo % 100 == 0:
            print(json.dumps({
                "passo": passo,
                "perda": round(janela["total"] / 100, 5),
                "geracao": round(janela["gen"] / 100, 5),
                "acao": round(janela["acao"] / 100, 5),
                "foco": round(janela["foco"] / 100, 5),
                "grad_norm": round(janela["norma"] / 100, 4),
                "segundos": round(time.time() - inicio, 1),
            }, ensure_ascii=False), flush=True)
            janela.clear()
    return {
        "treinaveis_modelo": treinaveis_modelo,
        "aux_parametros": sum(p.numel() for p in cabeca_acao.parameters()) +
                          sum(p.numel() for p in cabeca_foco.parameters()),
        "passos": PASSOS, "lote": LOTE, "lr": LR,
        "lambda_acao": LAMBDA_ACAO, "lambda_foco": LAMBDA_FOCO,
        "segundos": time.time() - inicio,
    }


def carregar_holdout():
    manifesto = json.loads((AQUI / "manifesto_holdout.json").read_text(encoding="utf-8"))
    gerador = AQUI / "preparar_holdout.py"
    if sha(gerador) != manifesto["gerador_sha256"]:
        raise ValueError("gerador do holdout mudou depois do congelamento")
    import preparar_holdout
    exemplos = preparar_holdout.gerar()
    pacote = {
        "versao": 1,
        "semente": preparar_holdout.SEMENTE,
        "congelado_antes_do_treino": True,
        "auditoria": {
            "aprovado": True,
            "exemplos": 120,
            "familias": len(preparar_holdout.FAMILIAS),
            "mensagens_exatas_repetidas": 0,
            "por_operacao": {
                op: sum(x["operacao"] == op for x in exemplos)
                for op in preparar_holdout.OPERACOES
            },
        },
        "exemplos": exemplos,
    }
    if sha_json(pacote) != manifesto["holdout_sha256_canonico"]:
        raise ValueError("holdout materializado não bate com o hash congelado")
    return exemplos, manifesto


def normalizar(texto):
    texto = unicodedata.normalize("NFKC", texto).casefold()
    return re.sub(r"\s+", " ", texto).strip()


def _valor_alvo(ex):
    op, r = ex["operacao"], ex["resposta"]
    if op in ("recordar_pessoa", "corrigir_pessoa", "pedir_detalhe"):
        m = re.search(r"([A-Za-zÀ-ÿ]+-\d+)", r)
        return {"pessoa": m.group(1) if m else ""}
    if op == "recordar_objeto":
        m = re.match(r"O objeto é (.+)\.$", r)
        return {"objeto": m.group(1) if m else ""}
    if op == "guardar_hipotese":
        m = re.match(r"Não\. (.+) continua apenas como possibilidade\.$", r)
        return {"atividade": m.group(1) if m else ""}
    if op == "mensagem_sem_horario":
        p = re.search(r"([A-Za-zÀ-ÿ]+-\d+)", r)
        a = re.search(r"combinar (.+) comigo\?", r)
        return {"pessoa": p.group(1) if p else "", "atividade": a.group(1) if a else ""}
    return {}


def _objeto_inicial(ex):
    for turno in ex["historico"]:
        if turno["papel"] == "assistente":
            m = re.search(r"Objeto:\s*([^.;]+)", turno["texto"])
            if m:
                return m.group(1).strip()
    return ""


def pontuar_saida(ex, saida):
    n = normalizar(saida)
    valores = _valor_alvo(ex)
    presentes = {k: bool(v) and normalizar(v) in n for k, v in valores.items()}
    slot = all(presentes.values()) if presentes else False
    op = ex["operacao"]
    if op in ("recordar_pessoa", "recordar_objeto", "corrigir_pessoa"):
        operacao = slot
    elif op == "guardar_hipotese":
        epistemico = any(x in n for x in ("não", "possibilidade", "hipótese", "provis"))
        operacao = slot and epistemico
    elif op == "mensagem_sem_horario":
        inventou_hora = bool(re.search(r"\b\d{1,2}(?::\d{2})?\s*(?:h|hora|horas)\b", n))
        operacao = slot and not inventou_hora
    elif op == "pedir_detalhe":
        pergunta = "?" in saida or any(x in n for x in ("o que", "qual ", "que item", "que coisa"))
        obj = normalizar(_objeto_inicial(ex))
        inventou_objeto = bool(obj and obj in n)
        operacao = slot and pergunta and not inventou_objeto
    else:
        operacao = False
    return bool(slot), bool(operacao)


@torch.no_grad()
def avaliar_dialogo(modelo, tokenizer, exemplos, dispositivo):
    modelo.eval()
    preparados = [tokens_exemplo(tokenizer, e, modelo.config.contexto) for e in exemplos]
    soma_ce, tokens_ce = 0.0, 0
    primeiros, exatas, slots, ops = 0, 0, 0, 0
    por_op = defaultdict(lambda: {"n": 0, "operacao": 0, "slot": 0, "exata": 0})
    detalhes = []
    proibidos = [tokenizer.token_to_id(t) for t in ESPECIAIS[:-1]]
    fim = tokenizer.token_to_id("<fim>")

    for p in preparados:
        x = torch.tensor([p["x"]], dtype=torch.long, device=dispositivo)
        y = torch.tensor([p["y"]], dtype=torch.long, device=dispositivo)
        _, logits = ocultos_logits(modelo, x, treino_topo=False)
        perda = F.cross_entropy(
            logits.reshape(-1, modelo.config.vocabulario), y.reshape(-1),
            ignore_index=-100, reduction="sum")
        nt = int((y != -100).sum())
        soma_ce += float(perda)
        tokens_ce += nt
        if int(logits[0, p["pos_aux"]].argmax()) == p["primeiro_alvo"]:
            primeiros += 1

        ids, terminou = modelo.gerar(
            p["fonte"], fim, max_tokens=32, temperatura=0, top_k=0,
            semente=SEMENTE, proibidos=proibidos)
        texto = tokenizer.decode(ids)
        exata = normalizar(texto) == normalizar(p["resposta"])
        slot, operacao = pontuar_saida(p["exemplo"], texto)
        exatas += int(exata)
        slots += int(slot)
        ops += int(operacao)
        q = por_op[p["operacao"]]
        q["n"] += 1
        q["operacao"] += int(operacao)
        q["slot"] += int(slot)
        q["exata"] += int(exata)
        detalhes.append({
            "id": p["id"], "operacao": p["operacao"], "alvo": p["resposta"],
            "saida": texto, "terminou": terminou, "exata": exata,
            "slot": slot, "operacao_correta": operacao,
        })

    n = len(preparados)
    resumo_ops = {
        op: {**v,
             "operacao_taxa": v["operacao"] / v["n"],
             "slot_taxa": v["slot"] / v["n"],
             "exata_taxa": v["exata"] / v["n"]}
        for op, v in sorted(por_op.items())
    }
    return {
        "n": n, "ce": soma_ce / max(1, tokens_ce),
        "primeiro_token": primeiros / n, "exata": exatas / n,
        "slot": slots / n, "operacao": ops / n,
        "por_operacao": resumo_ops, "detalhes": detalhes,
    }


@torch.no_grad()
def avaliar_preservacao(modelo, tokenizer, textos, dispositivo):
    modelo.eval()
    doc = tokenizer.token_to_id("<documento>")
    fim = tokenizer.token_to_id("<fim>")
    soma, ntotal = 0.0, 0
    for texto in textos:
        seq = [doc] + codificar_texto(tokenizer, texto) + [fim]
        if len(seq) - 1 > modelo.config.contexto:
            raise ValueError("texto de preservação excede contexto")
        x = torch.tensor([seq[:-1]], dtype=torch.long, device=dispositivo)
        y = torch.tensor([seq[1:]], dtype=torch.long, device=dispositivo)
        _, logits = ocultos_logits(modelo, x, treino_topo=False)
        soma += float(F.cross_entropy(
            logits.reshape(-1, modelo.config.vocabulario), y.reshape(-1), reduction="sum"))
        ntotal += y.numel()
    return {"n": len(textos), "ce": soma / ntotal, "tokens": ntotal}


def sem_detalhes(m):
    return {k: v for k, v in m.items() if k != "detalhes"}


def gates(base, candidato, pres_base, pres_candidato):
    por_min = min(v["operacao_taxa"] for v in candidato["por_operacao"].values())
    ganho_primeiro = candidato["primeiro_token"] - base["primeiro_token"]
    ganho_ce = (base["ce"] - candidato["ce"]) / base["ce"]
    rel_pres = pres_candidato["ce"] / pres_base["ce"]
    g = {
        "operacao_min_60": candidato["operacao"] >= 0.60,
        "cada_operacao_min_35": por_min >= 0.35,
        "slot_min_70": candidato["slot"] >= 0.70,
        "primeiro_token_ganho_10pp": ganho_primeiro >= 0.10,
        "ce_melhora_5pct": ganho_ce >= 0.05,
        "preservacao_ate_5pct": rel_pres <= 1.05,
    }
    return g, {
        "min_operacao": por_min,
        "ganho_primeiro_token_pp": 100 * ganho_primeiro,
        "ganho_ce_relativo": ganho_ce,
        "preservacao_ce_relativa": rel_pres,
    }


def salvar(modelo, tokenizer_path, estado_base, saida, treino, resultados):
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tokenizer_path, saida / "tokenizer.json")
    checkpoint = {
        "versao": 1,
        "modelo": {k: v.detach().cpu() for k, v in modelo.state_dict().items()},
        "config": estado_base["config"],
        "passo": estado_base["passo"],
        "execucao": {
            "tokenizer_sha256": BASE_TOKENIZER_SHA,
            "semente": SEMENTE,
            "pesos_externos": False,
            "base_pesos_sha256": BASE_PESOS_SHA,
            "escola_cognitiva": {
                "versao": 1, "passos": PASSOS, "treino": treino,
                "auxiliares_serializados": False, "ativo_no_chat": False,
            },
        },
    }
    torch.save(checkpoint, saida / "pesos.pt")
    resultados["checkpoint_sha256"] = sha(saida / "pesos.pt")
    (saida / "resultados.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    meta = {
        "papel": "candidato Escola Cognitiva v1 sobre a base própria 17M",
        "base_pesos_sha256": BASE_PESOS_SHA,
        "checkpoint_sha256": resultados["checkpoint_sha256"],
        "elegivel_promocao": resultados["elegivel_promocao"],
        "ativo_no_chat": False, "pesos_externos": False,
    }
    (saida / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True, help="pasta com pesos.pt e tokenizer.json da base 17M")
    ap.add_argument("--saida", required=True, help="pasta para o candidato e resultados")
    ap.add_argument("--dispositivo", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    dispositivo = torch.device(args.dispositivo)
    random.seed(SEMENTE)
    torch.manual_seed(SEMENTE)
    if dispositivo.type == "cuda":
        torch.cuda.manual_seed_all(SEMENTE)

    protocolo = json.loads((AQUI / "protocolo.json").read_text(encoding="utf-8"))
    if protocolo["base"]["pesos_sha256"] != BASE_PESOS_SHA:
        raise ValueError("protocolo não corresponde à base compilada no experimento")

    print("carregando base própria 17M...", flush=True)
    modelo, tokenizer, estado_base = carregar_base(args.base, dispositivo)
    exemplos_treino = gerar_treino()
    print("currículo:", len(exemplos_treino), "exemplos", flush=True)
    treino = treinar(modelo, tokenizer, exemplos_treino, dispositivo)

    print("treino encerrado; abrindo holdout prospectivo pela primeira vez...", flush=True)
    holdout, manifesto = carregar_holdout()
    preservacao = json.loads(
        (AQUI / "preservacao_portugues.json").read_text(encoding="utf-8"))["textos"]

    print("avaliando base no mesmo holdout...", flush=True)
    base, tokenizer_base, _ = carregar_base(args.base, dispositivo)
    avaliacao_base = avaliar_dialogo(base, tokenizer_base, holdout, dispositivo)
    pres_base = avaliar_preservacao(base, tokenizer_base, preservacao, dispositivo)
    del base
    if dispositivo.type == "cuda":
        torch.cuda.empty_cache()

    print("avaliando candidato...", flush=True)
    avaliacao_candidato = avaliar_dialogo(modelo, tokenizer, holdout, dispositivo)
    pres_candidato = avaliar_preservacao(modelo, tokenizer, preservacao, dispositivo)
    gs, derivados = gates(avaliacao_base, avaliacao_candidato, pres_base, pres_candidato)
    elegivel = all(gs.values())

    resultados = {
        "versao": 1,
        "base": {
            "pesos_sha256": BASE_PESOS_SHA, "tokenizer_sha256": BASE_TOKENIZER_SHA,
            "parametros": BASE_PARAMETROS, "passo": BASE_PASSO,
        },
        "holdout": manifesto,
        "treino": treino,
        "avaliacao_base": sem_detalhes(avaliacao_base),
        "avaliacao_candidato": sem_detalhes(avaliacao_candidato),
        "preservacao_base": pres_base,
        "preservacao_candidato": pres_candidato,
        "gates": gs,
        "derivados": derivados,
        "elegivel_promocao": elegivel,
        "ativo_no_chat": False,
        "detalhes_holdout": avaliacao_candidato["detalhes"],
    }
    salvar(modelo, Path(args.base) / "tokenizer.json", estado_base,
           args.saida, treino, resultados)
    print(json.dumps({
        "elegivel_promocao": elegivel,
        "gates": gs,
        "base": sem_detalhes(avaliacao_base),
        "candidato": sem_detalhes(avaliacao_candidato),
        "preservacao_relativa": derivados["preservacao_ce_relativa"],
        "checkpoint_sha256": resultados["checkpoint_sha256"],
        "ativo_no_chat": False,
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
