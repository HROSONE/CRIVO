#!/usr/bin/env python3
"""Auditoria pareada V1/V4/V5 do Transformer 17,43M, sem qualquer treino."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))

from linguagem_profunda import Configuracao, LinguagemProfunda, ESPECIAIS  # noqa:E402
import preparar_holdout as holdout  # noqa:E402

SLOTS = ("pessoa", "objeto", "atividade")
GATE_ALVO = {
    "recordar_pessoa": (1., 0., 0.),
    "recordar_objeto": (0., 1., 0.),
    "corrigir_pessoa": (1., 0., 0.),
    "guardar_hipotese": (0., 0., 1.),
    "mensagem_sem_horario": (1., 0., 1.),
    "pedir_detalhe": (1., 0., 0.),
}
TOK_SHA = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"
HOLDOUT_SHA = "55fab7f65ded87c721fe44bf84d6b69a1153c32caa3675feb95ce1a7887707f0"
GERADOR_SHA = "58807e8fb9b6ce00aec82a491f19a6fdfceb0da8c389f68ac74c32e6ec224ef5"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def sha_json(obj):
    return hashlib.sha256(json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


def abrir_holdout():
    man = json.loads((AQUI / "manifesto_holdout.json").read_text(encoding="utf-8"))
    gerador_atual = sha(AQUI / "preparar_holdout.py")
    if gerador_atual != GERADOR_SHA:
        raise ValueError("gerador diagnóstico mudou")
    if man["gerador_sha256"] != GERADOR_SHA:
        raise ValueError("manifesto do gerador divergente")
    ex = holdout.gerar()
    por = {op: sum(x["operacao"] == op for x in ex) for op in holdout.OPERACOES}
    repetidas = len(ex) - len({x["mensagem"] for x in ex})
    pacote = {
        "versao": "audit1",
        "semente": holdout.SEMENTE,
        "congelado_antes_da_avaliacao": True,
        "auditoria": {
            "exemplos": 120,
            "familias": len(holdout.FAMILIAS),
            "mensagens_exatas_repetidas": repetidas,
            "por_operacao": por,
        },
        "exemplos": ex,
    }
    calculado = sha_json(pacote)
    if calculado != HOLDOUT_SHA or calculado != man["holdout_sha256_canonico"]:
        raise ValueError("hash do holdout diagnóstico mudou")
    return ex, man


def cod(t, texto):
    return t.encode(texto, add_special_tokens=False).ids


def _nomes(texto):
    return set(re.findall(r"[A-Za-zÀ-ÿ]+-\d+", texto))


def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s).casefold()).strip()


def fonte_compacta(t, ex, resposta, contexto):
    fim = t.token_to_id("<fim>")
    papel = {"usuario": t.token_to_id("<usuario>"), "assistente": t.token_to_id("<assistente>")}
    atual = [papel["usuario"]] + cod(t, ex["mensagem"]) + [fim, papel["assistente"]]
    limite = contexto + 1 - len(resposta)
    hist = [z for z in ex["historico"] if z["papel"] in papel]
    seg = [[papel[z["papel"]]] + cod(t, z["texto"]) + [fim] for z in hist]
    grupos = []
    i = 0
    while i < len(hist):
        if i + 1 < len(hist) and hist[i]["papel"] == "usuario" and hist[i + 1]["papel"] == "assistente":
            grupos.append((i, i + 1))
            i += 2
        else:
            grupos.append((i,))
            i += 1
    selecionados = {0} if grupos else set()
    for gi, g in enumerate(grupos):
        texto = " ".join(hist[j]["texto"] for j in g)
        if len(_nomes(texto)) >= 2:
            selecionados.add(gi)
    tam = lambda gi: sum(len(seg[j]) for j in grupos[gi])
    total = lambda s: len(atual) + sum(tam(gi) for gi in s)
    if len(atual) > limite or total(selecionados) > limite:
        raise ValueError(ex["id"] + ": estado essencial excede contexto")
    for gi in reversed(range(len(grupos))):
        if gi not in selecionados and total(selecionados) + tam(gi) <= limite:
            selecionados.add(gi)
    fonte = []
    for gi, g in enumerate(grupos):
        if gi in selecionados:
            for j in g:
                fonte += seg[j]
    return fonte + atual


def achar_subseq(seq, alvo):
    if not alvo or len(alvo) > len(seq):
        return -1
    for i in range(len(seq) - len(alvo), -1, -1):
        if seq[i:i + len(alvo)] == alvo:
            return i
    return -1


def localizar_valor(t, fonte, valor):
    if not valor:
        return -1, []
    candidatos = []
    for forma in (valor, " " + valor):
        alvo = cod(t, forma)
        p = achar_subseq(fonte, alvo)
        if p >= 0:
            candidatos.append((p, alvo))
    if not candidatos:
        return -1, []
    return max(candidatos, key=lambda x: x[0])


def preparar(t, ex, contexto):
    fim = t.token_to_id("<fim>")
    resp_sem_fim = cod(t, ex["resposta"])
    resp = resp_sem_fim + [fim]
    fonte = fonte_compacta(t, ex, resp, contexto)
    seq = fonte + resp
    if len(seq) - 1 > contexto:
        raise AssertionError("compactação falhou")
    x, y = seq[:-1], seq[1:]
    pos = len(fonte) - 1
    ptr, spans = {}, {}
    for nome in SLOTS:
        valor = ex.get("slots", {}).get(nome, "")
        p, tokens = localizar_valor(t, fonte, valor)
        if p < 0:
            raise ValueError(f"{ex['id']}: slot {nome}={valor!r} ausente da fonte")
        ptr[nome] = p
        spans[nome] = (p, p + len(tokens), len(tokens))
    return {
        "id": ex["id"], "x": x, "y": [-100] * pos + y[pos:], "pos": pos,
        "primeiro": resp[0], "fonte": fonte, "resposta_ids": resp_sem_fim,
        "resposta": ex["resposta"], "ex": ex, "ptr": ptr, "spans": spans,
        "operacao": ex["operacao"],
    }


class PonteBinding(nn.Module):
    def __init__(self, dim=384):
        super().__init__()
        self.q = nn.ModuleDict({s: nn.Linear(dim, dim, bias=False) for s in SLOTS})
        self.gate = nn.Linear(dim, len(SLOTS), bias=True)
        self.proj = nn.Linear(dim, dim, bias=False)
        self.alpha = nn.Parameter(torch.tensor(-1.5))

    def contexto(self, h, pos):
        b, t, d = h.shape
        idx = torch.arange(b, device=h.device)
        base = h[idx, pos]
        mascara = torch.arange(t, device=h.device)[None, :] <= pos[:, None]
        resumos, preds = [], {}
        for s in SLOTS:
            q = self.q[s](base)
            esc = (h * q[:, None, :]).sum(-1) / math.sqrt(d)
            esc = esc.masked_fill(~mascara, -1e9)
            prob = esc.softmax(-1)
            resumos.append(torch.einsum("bt,btd->bd", prob, h))
            preds[s] = esc.argmax(-1)
        gates = torch.sigmoid(self.gate(base))
        emp = torch.stack(resumos, dim=1)
        misto = (emp * gates[:, :, None]).sum(1) / (gates.sum(1, keepdim=True) + 1e-6)
        delta = self.proj(misto) * torch.tanh(self.alpha)
        return delta, gates, preds

    def forward_residual(self, raw, m, pos):
        h = m.norm(raw)
        delta, gates, preds = self.contexto(h, pos)
        saida = raw.clone()
        for i, p in enumerate(pos.tolist()):
            saida[i, p:] = saida[i, p:] + delta[i]
        return saida, gates, preds


def carregar_modelo(pasta, dispositivo="cpu"):
    from tokenizers import Tokenizer
    pasta = Path(pasta)
    if sha(pasta / "tokenizer.json") != TOK_SHA:
        raise ValueError(f"tokenizador inesperado em {pasta}")
    e = torch.load(pasta / "pesos.pt", map_location="cpu", weights_only=True)
    m = LinguagemProfunda(Configuracao(**e["config"])).to(dispositivo)
    m.load_state_dict(e["modelo"], strict=True)
    t = Tokenizer.from_file(str(pasta / "tokenizer.json"))
    t.encode_special_tokens = True
    m.eval()
    return m, t, e


def carregar_ponte(pasta, dispositivo="cpu"):
    e = torch.load(Path(pasta) / "ponte_binding.pt", map_location="cpu", weights_only=True)
    ponte = PonteBinding(int(e.get("dimensao", 384))).to(dispositivo)
    ponte.load_state_dict(e["estado"], strict=True)
    ponte.eval()
    return ponte, e


def residuais_completos(m, ids):
    t = ids.shape[1]
    x = m.embedding(ids) + m.posicao(torch.arange(t, device=ids.device))
    for bloco in m.blocos:
        x = bloco(x)
    return x


def residuais_inferiores(m, ids):
    t = ids.shape[1]
    x = m.embedding(ids) + m.posicao(torch.arange(t, device=ids.device))
    for bloco in m.blocos[:4]:
        x = bloco(x)
    return x


def residuais_superiores(m, x):
    for bloco in m.blocos[4:]:
        x = bloco(x)
    return x


def forward_base(m, ids):
    raw = residuais_completos(m, ids)
    h = m.norm(raw)
    return F.linear(h, m.embedding.weight)


def forward_candidato(versao, m, ponte, ids, pos):
    if versao == 4:
        raw = residuais_completos(m, ids)
        raw2, gates, preds = ponte.forward_residual(raw, m, pos)
        h = m.norm(raw2)
    elif versao == 5:
        baixo = residuais_inferiores(m, ids)
        baixo2, gates, preds = ponte.forward_residual(baixo, m, pos)
        alto = residuais_superiores(m, baixo2)
        h = m.norm(alto)
    else:
        raise ValueError("versão candidata desconhecida")
    return F.linear(h, m.embedding.weight), gates, preds


def pos_assistente(ids, assistente):
    achados = [i for i, v in enumerate(ids) if v == assistente]
    if not achados:
        raise ValueError("marcador <assistente> ausente")
    return achados[-1]


def _errados_nomes(ex, saida, alvo):
    todos = set()
    for h in ex["historico"]:
        todos |= _nomes(h["texto"])
    todos |= _nomes(ex["mensagem"])
    return any(norm(n) in norm(saida) for n in todos if norm(n) != norm(alvo))


def pontuar(ex, saida, terminou):
    if not terminou:
        return False, False
    n = norm(saida)
    op = ex["operacao"]
    s = ex["slots"]
    pessoa, objeto, atividade = s["pessoa"], s["objeto"], s["atividade"]
    if op == "recordar_pessoa":
        slot = norm(pessoa) in n
        ok = slot and not _errados_nomes(ex, saida, pessoa)
    elif op == "recordar_objeto":
        slot = norm(objeto) in n
        ok = slot
    elif op == "corrigir_pessoa":
        slot = norm(pessoa) in n
        ok = slot and not _errados_nomes(ex, saida, pessoa)
    elif op == "guardar_hipotese":
        slot = norm(atividade) in n
        ok = slot and any(q in n for q in ("hipótese", "possibilidade", "provis", "não como confirmação", "sem confirmação"))
    elif op == "mensagem_sem_horario":
        slot = norm(pessoa) in n and norm(atividade) in n
        ok = slot and not _errados_nomes(ex, saida, pessoa) and "?" in saida and not re.search(
            r"\b\d{1,2}(?::\d{2})?\s*(?:h|hora|horas)\b", n)
    else:
        slot = norm(pessoa) in n
        pergunta = "?" in saida or any(q in n for q in ("qual item", "o que", "que coisa", "que item"))
        ok = slot and pergunta and norm(objeto) not in n and not _errados_nomes(ex, saida, pessoa)
    return bool(slot), bool(ok)


def slots_relevantes(op):
    return {
        "recordar_pessoa": ("pessoa",),
        "recordar_objeto": ("objeto",),
        "corrigir_pessoa": ("pessoa",),
        "guardar_hipotese": ("atividade",),
        "mensagem_sem_horario": ("pessoa", "atividade"),
        "pedir_detalhe": ("pessoa",),
    }[op]


def posicoes_entidade_resposta(t, z):
    marcadas = set()
    comprimentos = []
    alvo = z["resposta_ids"]
    for slot in slots_relevantes(z["operacao"]):
        valor = z["ex"]["slots"][slot]
        melhores = []
        for forma in (valor, " " + valor):
            seq = cod(t, forma)
            p = achar_subseq(alvo, seq)
            if p >= 0:
                melhores.append((p, seq))
        if melhores:
            p, seq = max(melhores, key=lambda x: x[0])
            marcadas.update(range(p, p + len(seq)))
            comprimentos.append(len(seq))
    return marcadas, comprimentos


@torch.no_grad()
def gerar(versao, m, t, fonte, ponte=None, max_tokens=48):
    fim = t.token_to_id("<fim>")
    assist = t.token_to_id("<assistente>")
    proib = {t.token_to_id(x) for x in ESPECIAIS[:-1]}
    ids = list(fonte)
    saida = []
    terminou = False
    historico_ptr = {s: [] for s in SLOTS}
    for _ in range(max_tokens):
        janela = ids[-m.config.contexto:]
        x = torch.tensor([janela], dtype=torch.long, device=m.embedding.weight.device)
        if versao == 1:
            log = forward_base(m, x)
        else:
            p = pos_assistente(janela, assist)
            pos = torch.tensor([p], dtype=torch.long, device=x.device)
            log, _, preds = forward_candidato(versao, m, ponte, x, pos)
            for s in SLOTS:
                historico_ptr[s].append(int(preds[s][0]))
        logits = log[0, -1].clone()
        for tok in proib:
            logits[tok] = -float("inf")
        proximo = int(logits.argmax())
        if proximo == fim:
            terminou = True
            break
        saida.append(proximo)
        ids.append(proximo)
    return saida, terminou, historico_ptr


@torch.no_grad()
def avaliar(nome, versao, pasta, exs, dispositivo="cpu"):
    m, t, estado = carregar_modelo(pasta, dispositivo)
    ponte = None
    if versao in (4, 5):
        ponte, _ = carregar_ponte(pasta, dispositivo)
    prep = [preparar(t, e, m.config.contexto) for e in exs]
    ce = nt = first = tf_ok = tf_total = 0
    exact = slotn = opn = 0
    por = defaultdict(lambda: {"n": 0, "operacao": 0, "slot": 0, "exata": 0})
    tf_pos = defaultdict(lambda: [0, 0])
    divergencias = []
    prefixos = []
    div_copy = div_entity = 0
    div_total = 0
    entity_tokens = entity_copyable = 0
    slot_lens = defaultdict(list)
    pdiag = {s: {"n": 0, "start_ok": 0, "inside_span": 0} for s in SLOTS}
    gdiag = {"bits": 0, "acertos": 0}
    ptr_stability = {s: {"casos": 0, "estaveis_primeiros4": 0} for s in SLOTS}

    for z in prep:
        x = torch.tensor([z["x"]], dtype=torch.long, device=dispositivo)
        y = torch.tensor([z["y"]], dtype=torch.long, device=dispositivo)
        if versao == 1:
            log = forward_base(m, x)
            gates = preds = None
        else:
            pos = torch.tensor([z["pos"]], dtype=torch.long, device=dispositivo)
            log, gates, preds = forward_candidato(versao, m, ponte, x, pos)
            alvo_gate = torch.tensor([GATE_ALVO[z["operacao"]]], device=dispositivo)
            gdiag["bits"] += len(SLOTS)
            gdiag["acertos"] += int(((gates >= .5) == (alvo_gate >= .5)).sum().item())
            for s in SLOTS:
                pred = int(preds[s][0])
                ini, fimspan, tam = z["spans"][s]
                pdiag[s]["n"] += 1
                pdiag[s]["start_ok"] += int(pred == ini)
                pdiag[s]["inside_span"] += int(ini <= pred < fimspan)
                slot_lens[s].append(tam)

        mascara = y != -100
        ce += float(F.cross_entropy(log.reshape(-1, log.shape[-1]), y.reshape(-1), ignore_index=-100, reduction="sum"))
        nt += int(mascara.sum())
        pred_tf = log.argmax(-1)
        tf_ok += int(((pred_tf == y) & mascara).sum())
        tf_total += int(mascara.sum())
        first += int(int(log[0, z["pos"]].argmax()) == z["primeiro"])
        for abs_pos in torch.where(mascara[0])[0].tolist():
            rel = abs_pos - z["pos"]
            tf_pos[rel][1] += 1
            tf_pos[rel][0] += int(int(pred_tf[0, abs_pos]) == int(y[0, abs_pos]))

        ids, terminou, hp = gerar(versao, m, t, z["fonte"], ponte)
        saida = t.decode(ids)
        exata = norm(saida) == norm(z["resposta"])
        sl, ok = pontuar(z["ex"], saida, terminou)
        exact += exata
        slotn += sl
        opn += ok
        q = por[z["operacao"]]
        q["n"] += 1
        q["operacao"] += ok
        q["slot"] += sl
        q["exata"] += exata

        alvo = z["resposta_ids"]
        prefixo = 0
        while prefixo < min(len(ids), len(alvo)) and ids[prefixo] == alvo[prefixo]:
            prefixo += 1
        prefixos.append(prefixo)
        if prefixo < len(alvo):
            divergencias.append(prefixo)
            div_total += 1
            esperado = alvo[prefixo]
            div_copy += int(esperado in z["fonte"])
            entidade_pos, comprimentos = posicoes_entidade_resposta(t, z)
            div_entity += int(prefixo in entidade_pos)
        else:
            divergencias.append(None)
            entidade_pos, comprimentos = posicoes_entidade_resposta(t, z)
        for comp in comprimentos:
            entity_tokens += comp
        for p in entidade_pos:
            if p < len(alvo):
                entity_copyable += int(alvo[p] in z["fonte"])

        if versao in (4, 5):
            for s in SLOTS:
                seq = hp[s][:4]
                if seq:
                    ptr_stability[s]["casos"] += 1
                    ptr_stability[s]["estaveis_primeiros4"] += int(len(set(seq)) == 1)

    n = len(prep)
    po = {
        k: {
            **v,
            "operacao_taxa": v["operacao"] / v["n"],
            "slot_taxa": v["slot"] / v["n"],
            "exata_taxa": v["exata"] / v["n"],
        }
        for k, v in sorted(por.items())
    }
    div_validas = [x for x in divergencias if x is not None]
    saida = {
        "nome": nome,
        "versao": versao,
        "n": n,
        "ce_teacher_forced": ce / nt,
        "teacher_forced_token_acc": tf_ok / tf_total,
        "teacher_forced_acc_por_posicao": {
            str(k): v[0] / v[1] for k, v in sorted(tf_pos.items()) if v[1]
        },
        "primeiro_token": first / n,
        "exata": exact / n,
        "slot": slotn / n,
        "operacao": opn / n,
        "por_operacao": po,
        "prefixo_correto_medio_tokens": sum(prefixos) / len(prefixos),
        "primeira_divergencia_mediana": sorted(div_validas)[len(div_validas) // 2] if div_validas else None,
        "divergencias": div_total,
        "divergencia_token_existia_na_fonte": div_copy / div_total if div_total else None,
        "divergencia_em_token_de_entidade": div_entity / div_total if div_total else None,
        "tokens_entidade_copiaveis_da_fonte": entity_copyable / entity_tokens if entity_tokens else None,
    }
    if versao in (4, 5):
        saida["pointer"] = {
            s: {
                "n": d["n"],
                "start_acc": d["start_ok"] / d["n"],
                "inside_span_acc": d["inside_span"] / d["n"],
                "bpe_len_medio": sum(slot_lens[s]) / len(slot_lens[s]),
                "bpe_multitoken_taxa": sum(x > 1 for x in slot_lens[s]) / len(slot_lens[s]),
                "estavel_primeiros4_tokens": (
                    ptr_stability[s]["estaveis_primeiros4"] / ptr_stability[s]["casos"]
                    if ptr_stability[s]["casos"] else None
                ),
            } for s, d in pdiag.items()
        }
        saida["gate_bits_acc"] = gdiag["acertos"] / gdiag["bits"] if gdiag["bits"] else None
    return saida


def relatorio_markdown(resultados):
    linhas = [
        "# Auditoria pareada Transformer 17,43M — V1 × V4 × V5",
        "",
        "Diagnóstico sem treino e sem promoção. Os três checkpoints foram avaliados no mesmo holdout prospectivo de 120 casos.",
        "",
        "| Métrica | V1 | V4 | V5 |",
        "|---|---:|---:|---:|",
    ]
    mapa = [
        ("CE teacher-forced", "ce_teacher_forced"),
        ("Acurácia token teacher-forced", "teacher_forced_token_acc"),
        ("Primeiro token", "primeiro_token"),
        ("Operação", "operacao"),
        ("Slot", "slot"),
        ("Resposta exata", "exata"),
        ("Prefixo correto médio (tokens)", "prefixo_correto_medio_tokens"),
        ("Divergência: token existia na fonte", "divergencia_token_existia_na_fonte"),
        ("Divergência em token de entidade", "divergencia_em_token_de_entidade"),
    ]
    for rotulo, chave in mapa:
        vals = [resultados[x][chave] for x in ("v1", "v4", "v5")]
        fmt = []
        for v in vals:
            if v is None:
                fmt.append("—")
            elif "Prefixo" in rotulo or "CE" in rotulo:
                fmt.append(f"{v:.4f}")
            else:
                fmt.append(f"{100*v:.2f}%")
        linhas.append(f"| {rotulo} | {fmt[0]} | {fmt[1]} | {fmt[2]} |")
    linhas += ["", "## Pointer", ""]
    for modelo in ("v4", "v5"):
        linhas.append(f"### {modelo.upper()}")
        for s, d in resultados[modelo]["pointer"].items():
            linhas.append(
                f"- {s}: start={d['start_acc']:.3f}; inside-span={d['inside_span_acc']:.3f}; "
                f"BPE médio={d['bpe_len_medio']:.2f}; multi-token={d['bpe_multitoken_taxa']:.3f}; "
                f"pointer estável nos 4 primeiros tokens={d['estavel_primeiros4_tokens']:.3f}"
            )
    linhas += [
        "",
        "## Interpretação automática limitada",
        "",
        "Este relatório não autoriza promoção. Ele apenas separa recuperação, teacher forcing e geração autoregressiva no mesmo conjunto.",
    ]
    return "\n".join(linhas) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v1", required=True)
    ap.add_argument("--v4", required=True)
    ap.add_argument("--v5", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--dispositivo", default="cpu")
    a = ap.parse_args()
    torch.set_num_threads(2)

    exs, man = abrir_holdout()
    resultados = {
        "holdout_sha256": man["holdout_sha256_canonico"],
        "sem_treino": True,
        "promocao_autorizada": False,
        "v1": avaliar("V1 baseline", 1, a.v1, exs, a.dispositivo),
        "v4": avaliar("V4 binding final", 4, a.v4, exs, a.dispositivo),
        "v5": avaliar("V5 mid-bridge", 5, a.v5, exs, a.dispositivo),
    }
    resultados["comparacao_pareada"] = {
        "v5_menos_v4_operacao": resultados["v5"]["operacao"] - resultados["v4"]["operacao"],
        "v5_menos_v4_slot": resultados["v5"]["slot"] - resultados["v4"]["slot"],
        "v5_menos_v4_primeiro": resultados["v5"]["primeiro_token"] - resultados["v4"]["primeiro_token"],
        "v5_menos_v4_ce": resultados["v5"]["ce_teacher_forced"] - resultados["v4"]["ce_teacher_forced"],
        "v5_menos_v4_tf_token_acc": resultados["v5"]["teacher_forced_token_acc"] - resultados["v4"]["teacher_forced_token_acc"],
    }

    out = Path(a.saida)
    out.mkdir(parents=True, exist_ok=True)
    (out / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "RELATORIO.md").write_text(relatorio_markdown(resultados), encoding="utf-8")
    print(json.dumps({
        "holdout_sha256": resultados["holdout_sha256"],
        "v1": {k: resultados["v1"][k] for k in ("ce_teacher_forced","teacher_forced_token_acc","primeiro_token","operacao","slot","exata")},
        "v4": {k: resultados["v4"][k] for k in ("ce_teacher_forced","teacher_forced_token_acc","primeiro_token","operacao","slot","exata")},
        "v5": {k: resultados["v5"][k] for k in ("ce_teacher_forced","teacher_forced_token_acc","primeiro_token","operacao","slot","exata")},
        "pareado": resultados["comparacao_pareada"],
        "pointer_v4": resultados["v4"]["pointer"],
        "pointer_v5": resultados["v5"]["pointer"],
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
