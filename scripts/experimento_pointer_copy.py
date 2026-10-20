#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import shutil
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F
from tokenizers import Tokenizer

from linguagem_profunda import Configuracao, ESPECIAIS, LinguagemProfunda, fonte_dialogo

SEED = 202610120305
RANK = 32
STEPS = 1000
TRAIN_ENTITIES = 1800
BLIND_ENTITIES = 100
DEV_ENTITIES = 60

CATEGORIES = [
    ("recipiente", ["armazenar líquidos", "transportar líquidos", "conter amostras", "guardar substâncias"]),
    ("instrumento", ["medir temperatura", "observar objetos distantes", "detectar vibrações", "registrar sinais"]),
    ("ferramenta", ["golpear peças", "cortar materiais", "fixar componentes", "apertar parafusos"]),
    ("dispositivo", ["processar dados", "emitir alertas", "controlar fluxo", "registrar eventos"]),
    ("móvel", ["servir de assento", "apoiar objetos", "guardar itens", "organizar materiais"]),
    ("estrutura", ["sustentar uma carga", "proteger uma área", "conectar duas partes", "separar ambientes"]),
]
MATERIALS = ["metal", "vidro", "madeira", "cerâmica", "plástico", "fibra", "pedra", "borracha"]
FILLERS = [
    "O laboratório registra as descrições sem alterar os nomes.",
    "A ficha abaixo pertence a um catálogo experimental.",
    "Considere apenas as informações fornecidas nesta mensagem.",
]

@dataclass(frozen=True)
class Entity:
    name: str
    category: str
    function: str
    mat_a: str
    mat_b: str
    lexical_group: str
    token_len: int

@dataclass(frozen=True)
class Case:
    skill: str
    prompt: str
    answer: str
    name: str
    category: str
    function: str
    lexical_group: str
    position: str
    token_len: int
    requires_copy: bool = True

def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()

def words(s: str):
    stop = {"de", "da", "do", "para", "um", "uma", "e", "a", "o", "os", "as"}
    return [w for w in re.findall(r"[a-zA-ZÀ-ÿ]+", norm(s)) if len(w) > 2 and w not in stop]

def wrong_category(cat: str) -> str:
    return next(c for c, _ in CATEGORIES if c != cat)

def candidate_name(rng: random.Random, family: int) -> str:
    a = ["na","ze","tor","lum","fi","dra","kel","vo","ri","san","bel","tri","mo","pa","xel","gu","pri","do","var","chi"]
    b = ["lo","ra","mi","to","ve","na","po","ri","sa","du","xel","go","fi","la","ne","bar","ti","cor","zen","mar"]
    if family == 0:
        return rng.choice(a) + rng.choice(b) + rng.choice(["n","s","r","m","l","d"])
    if family == 1:
        return rng.choice(a).capitalize() + str(rng.randrange(10, 99))
    if family == 2:
        return rng.choice(a) + "-" + rng.choice(b) + str(rng.randrange(2, 9))
    if family == 3:
        cons = "qwxzvkj"
        vow = "aeiou"
        return "".join(rng.choice(cons if i % 2 == 0 else vow) for i in range(rng.choice([4, 6]))) + str(rng.randrange(2, 9))
    return rng.choice("QWXZ") + str(rng.randrange(2, 9)) + "-" + rng.choice("vkjz") + rng.choice("aeiou") + str(rng.randrange(10, 99))

def make_entities(tok: Tokenizer, seed: int, n: int, mode: str) -> list[Entity]:
    rng = random.Random(seed)
    families = [0, 1, 2] if mode == "train" else ([0, 1, 2, 3, 4] if mode == "blind" else [0, 1, 2, 3])
    seen = set()
    out = []
    tries = 0
    while len(out) < n and tries < n * 500:
        tries += 1
        fam = rng.choice(families)
        name = candidate_name(rng, fam)
        if name in seen:
            continue
        ids = tok.encode(name, add_special_tokens=False).ids
        if not (1 <= len(ids) <= 4):
            continue
        seen.add(name)
        cat, funcs = rng.choice(CATEGORIES)
        fn = rng.choice(funcs)
        m1, m2 = rng.sample(MATERIALS, 2)
        lexical = "distant" if fam in (3, 4) else "close"
        out.append(Entity(name, cat, fn, m1, m2, lexical, len(ids)))
    if len(out) != n:
        raise RuntimeError(f"não consegui gerar {n} entidades 1-4 tokens; obtive {len(out)}")
    return out

def place_definition(definition: str, question: str, position: str) -> str:
    if position == "inicio":
        return f"{definition} {FILLERS[0]} {question}"
    if position == "meio":
        return f"{FILLERS[1]} {definition} {FILLERS[2]} {question}"
    return f"{FILLERS[0]} {FILLERS[1]} {definition} {question}"

def eval_cases(entities: list[Entity]) -> list[Case]:
    cases = []
    positions = ["inicio", "meio", "fim"]
    for i, e in enumerate(entities):
        pos = positions[i % 3]
        definition = f"Existe um objeto inventado chamado {e.name}. Ele é um {e.category} usado para {e.function}."
        wc = wrong_category(e.category)
        cases.extend([
            Case("copia_pura", place_definition(definition, "Qual era exatamente o nome do objeto? Responda somente com o nome.", pos),
                 e.name, e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
            Case("categoria", place_definition(definition, "Diga o nome exato do objeto e a categoria a que ele pertence.", pos),
                 f"{e.name} pertence à categoria {e.category}.", e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
            Case("funcao", place_definition(definition, "Diga o nome exato do objeto e sua função.", pos),
                 f"A função de {e.name} é {e.function}.", e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
            Case("invariancia", place_definition(definition + f" Antes era de {e.mat_a} e agora é de {e.mat_b}.",
                 "A mudança de material, sozinha, faz o objeto deixar de ser o mesmo? Responda usando o nome exato.", pos),
                 f"Não. {e.name} continua sendo o mesmo {e.category}.", e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
            Case("composicao", place_definition(definition, "Explique em uma frase, preservando o nome exato, o que ele é e para que serve.", pos),
                 f"{e.name} é um {e.category} usado para {e.function}.", e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
            Case("negacao", place_definition(definition, f"Ele pertence à categoria {wc}? Responda com o nome exato e corrija a categoria.", pos),
                 f"Não. {e.name} é um {e.category}, não um {wc}.", e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
        ])
    return cases

def train_cases(entities: list[Entity]) -> list[Case]:
    cases = []
    positions = ["inicio", "meio", "fim"]
    for i, e in enumerate(entities):
        pos = positions[i % 3]
        definition = f"Há um item experimental chamado {e.name}. Ele é um {e.category} usado para {e.function}."
        wc = wrong_category(e.category)
        cases.extend([
            Case("copy_train", place_definition(definition, "Repita somente o nome exato do item.", pos),
                 e.name, e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
            Case("category_train", place_definition(definition, "Informe o nome exato e a categoria.", pos),
                 f"{e.name} pertence à categoria {e.category}.", e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
            Case("function_train", place_definition(definition, "Informe o nome exato e a função.", pos),
                 f"A função de {e.name} é {e.function}.", e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
            Case("composition_train", place_definition(definition, "Resuma em uma frase com o nome exato.", pos),
                 f"{e.name} é um {e.category} usado para {e.function}.", e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
            Case("negative_train", place_definition(definition, f"A categoria correta é {wc}? Corrija se necessário e use o nome exato.", pos),
                 f"Não. {e.name} é um {e.category}, não um {wc}.", e.name, e.category, e.function, e.lexical_group, pos, e.token_len),
            Case("no_copy", place_definition(definition, "Responda apenas: entendido.", pos),
                 "Entendido.", e.name, e.category, e.function, e.lexical_group, pos, e.token_len, requires_copy=False),
        ])
    return cases

def final_hidden(base: LinguagemProfunda, ids: torch.Tensor):
    x = base.embedding(ids) + base.posicao(torch.arange(ids.shape[1], device=ids.device))
    for block in base.blocos:
        x = block(x)
    h = base.norm(x)
    logits = F.linear(h, base.embedding.weight)
    return h, logits

class PointerCopyHead(nn.Module):
    def __init__(self, dim: int, rank: int = RANK, p_gen_init: float = 0.9):
        super().__init__()
        self.q = nn.Linear(dim, rank, bias=False)
        self.k = nn.Linear(dim, rank, bias=False)
        self.gate = nn.Linear(dim, 1)
        nn.init.normal_(self.q.weight, std=0.02)
        nn.init.normal_(self.k.weight, std=0.02)
        nn.init.zeros_(self.gate.weight)
        self.gate.bias.data.fill_(math.log(p_gen_init / (1.0 - p_gen_init)))
        self.rank = rank

    def scores(self, h: torch.Tensor, source_mask: torch.Tensor):
        q = self.q(h)
        k = self.k(h)
        scores = torch.matmul(q, k.transpose(-1, -2)) / math.sqrt(self.rank)
        scores = scores.masked_fill(~source_mask[:, None, :], -1e4)
        return scores

def encode_example(tok: Tokenizer, case: Case, context: int):
    source = fonte_dialogo(tok, case.prompt, (), context)
    ans = tok.encode(case.answer, add_special_tokens=False).ids + [tok.token_to_id("<fim>")]
    seq = source + ans
    if len(seq) > context:
        raise ValueError(f"exemplo excede contexto: {len(seq)}")
    x = seq[:-1]
    y = [-100] * (len(source) - 1) + seq[len(source):]
    return x, y, len(source)

def collate(tok: Tokenizer, batch: list[Case], context: int, device: str):
    pad = tok.token_to_id("<pad>")
    blocked = {tok.token_to_id(t) for t in ESPECIAIS}
    rows = [encode_example(tok, c, context) for c in batch]
    m = max(len(x) for x, _, _ in rows)
    xs, ys, src_masks = [], [], []
    for x, y, sl in rows:
        xs.append(x + [pad] * (m - len(x)))
        ys.append(y + [-100] * (m - len(y)))
        src_masks.append([i < sl and i < len(x) and x[i] not in blocked for i in range(m)])
    return (
        torch.tensor(xs, dtype=torch.long, device=device),
        torch.tensor(ys, dtype=torch.long, device=device),
        torch.tensor(src_masks, dtype=torch.bool, device=device),
    )

def pointer_loss(base, head, x, y, source_mask):
    with torch.no_grad():
        h, logits = final_hidden(base, x)
        log_vocab = logits.log_softmax(-1)
    scores = head.scores(h, source_mask)
    attn = scores.softmax(-1)
    mask = y != -100
    bi, ti = mask.nonzero(as_tuple=True)
    targets = y[bi, ti]
    vocab_p = log_vocab[bi, ti, targets].exp()
    src_ids = x[bi]
    copy_p = (attn[bi, ti] * (src_ids == targets[:, None]).float()).sum(-1)
    gate = torch.sigmoid(head.gate(h[bi, ti]).squeeze(-1))
    mix = gate * vocab_p + (1.0 - gate) * copy_p
    loss = -torch.log(mix.clamp_min(1e-9)).mean()
    return loss, float(gate.mean().detach()), float(copy_p.mean().detach())

@torch.no_grad()
def pointer_next(base, head, ids: list[int], source_len: int, blocked_ids):
    device = base.embedding.weight.device
    x = torch.tensor([ids[-base.config.contexto:]], dtype=torch.long, device=device)
    source_len = min(source_len, x.shape[1])
    h, logits = final_hidden(base, x)
    hv = h[:, -1:, :]
    q = head.q(hv)
    k = head.k(h)
    scores = torch.matmul(q, k.transpose(-1, -2)).squeeze(1) / math.sqrt(head.rank)
    mask = torch.arange(x.shape[1], device=device)[None, :] < source_len
    for token in blocked_ids:
        mask = mask & (x != token)
    scores = scores.masked_fill(~mask, -1e4)
    attn = scores.softmax(-1)
    copy_vocab = torch.zeros((1, base.config.vocabulario), device=device, dtype=logits.dtype)
    copy_vocab.scatter_add_(1, x, attn.to(copy_vocab.dtype))
    p_vocab = logits[:, -1, :].softmax(-1)
    gate = torch.sigmoid(head.gate(h[:, -1, :]))
    p = gate * p_vocab + (1.0 - gate) * copy_vocab
    return p[0], float(gate.item())

@torch.no_grad()
def generate_pointer(base, head, tok, prompt, max_tokens=64):
    source = fonte_dialogo(tok, prompt, (), base.config.contexto)
    ids = list(source)
    out = []
    gates = []
    fim = tok.token_to_id("<fim>")
    prohibited = {tok.token_to_id(t) for t in ESPECIAIS[:-1]}
    copy_blocked = {tok.token_to_id(t) for t in ESPECIAIS}
    for _ in range(max_tokens):
        p, g = pointer_next(base, head, ids, len(source), copy_blocked)
        gates.append(g)
        for t in prohibited:
            p[t] = 0
        nxt = int(p.argmax())
        if nxt == fim:
            break
        out.append(nxt)
        ids.append(nxt)
        if len(ids) >= base.config.contexto:
            break
    return tok.decode(out).strip(), (sum(gates) / max(1, len(gates)))

@torch.no_grad()
def generate_base(base, tok, prompt, max_tokens=64):
    source = fonte_dialogo(tok, prompt, (), base.config.contexto)
    ids, _ = base.gerar(source, tok.token_to_id("<fim>"), max_tokens=max_tokens,
                        temperatura=0, top_k=0, semente=SEED,
                        proibidos=[tok.token_to_id(t) for t in ESPECIAIS[:-1]])
    return tok.decode(ids).strip()

def exact_name_present(answer: str, name: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(norm(name)) + r"(?![a-z0-9])", norm(answer)) is not None

def pure_copy_ok(answer: str, name: str) -> bool:
    a = norm(answer).strip(" .,:;!?\"'")
    return a == norm(name)

def levenshtein(a: str, b: str) -> int:
    a, b = norm(a), norm(b)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def closest_piece_distance(answer: str, name: str) -> int:
    pieces = re.findall(r"[A-Za-zÀ-ÿ0-9-]+", answer)
    return min([levenshtein(p, name) for p in pieces] or [len(name)])

def semantic_ok(case: Case, answer: str) -> bool:
    a = norm(answer)
    if case.skill == "copia_pura":
        return pure_copy_ok(answer, case.name)
    if not exact_name_present(answer, case.name):
        return False
    if case.skill == "categoria":
        return all(norm(w) in a for w in words(case.category))
    if case.skill == "funcao":
        return all(norm(w) in a for w in words(case.function))
    if case.skill == "invariancia":
        return "nao" in a and all(norm(w) in a for w in words(case.category))
    if case.skill == "composicao":
        return all(norm(w) in a for w in words(case.category) + words(case.function))
    if case.skill == "negacao":
        return "nao" in a and all(norm(w) in a for w in words(case.category))
    return False

def summarize(records):
    by_skill = defaultdict(lambda: [0, 0])
    by_lex = defaultdict(lambda: [0, 0])
    by_pos = defaultdict(lambda: [0, 0])
    by_len = defaultdict(lambda: [0, 0])
    edit = []
    for r in records:
        ok = r["ok"]
        by_skill[r["skill"]][0] += int(ok); by_skill[r["skill"]][1] += 1
        if r["skill"] == "copia_pura":
            by_lex[r["lexical_group"]][0] += int(ok); by_lex[r["lexical_group"]][1] += 1
            by_pos[r["position"]][0] += int(ok); by_pos[r["position"]][1] += 1
            by_len[str(r["token_len"])][0] += int(ok); by_len[str(r["token_len"])][1] += 1
            edit.append(r["edit_distance"])
    conv = lambda d: {k: {"correct": v[0], "total": v[1], "accuracy": v[0] / max(1, v[1])} for k, v in d.items()}
    semantic = [r for r in records if r["skill"] != "copia_pura"]
    return {
        "overall": sum(r["ok"] for r in records) / max(1, len(records)),
        "semantic_overall": sum(r["ok"] for r in semantic) / max(1, len(semantic)),
        "by_skill": conv(by_skill),
        "copy_by_lexical_group": conv(by_lex),
        "copy_by_position": conv(by_pos),
        "copy_by_token_length": conv(by_len),
        "copy_edit_distance_mean": sum(edit) / max(1, len(edit)),
    }

@torch.no_grad()
def evaluate(base, head, tok, cases: list[Case], label: str):
    records = []
    for i, c in enumerate(cases, 1):
        if head is None:
            ans = generate_base(base, tok, c.prompt)
            gate = None
        else:
            ans, gate = generate_pointer(base, head, tok, c.prompt)
        ok = semantic_ok(c, ans)
        records.append({
            "skill": c.skill, "name": c.name, "answer": ans, "ok": ok,
            "lexical_group": c.lexical_group, "position": c.position,
            "token_len": c.token_len, "edit_distance": closest_piece_distance(ans, c.name),
            "gate_mean": gate,
        })
        if i % 100 == 0:
            print(f"[{label}] {i}/{len(cases)}", flush=True)
    return {"label": label, "summary": summarize(records), "samples": records[:18]}

def fingerprint_state(state_dict) -> str:
    h = hashlib.sha256()
    for k in sorted(state_dict):
        h.update(k.encode("utf-8"))
        t = state_dict[k].detach().cpu().contiguous()
        h.update(str(t.dtype).encode("ascii"))
        h.update(str(tuple(t.shape)).encode("ascii"))
        h.update(t.numpy().tobytes())
    return h.hexdigest()

def load_base(root: Path):
    curricular = root / "escola_curricular_longa"
    runs = sorted(p for p in curricular.glob("run_*") if (p / "05_05_dialogo_estado/pesos.pt").exists())
    if not runs:
        raise FileNotFoundError("não encontrei o checkpoint 05_05_dialogo_estado")
    base_dir = runs[-1] / "05_05_dialogo_estado"
    state = torch.load(base_dir / "pesos.pt", map_location="cpu", weights_only=True)
    tok = Tokenizer.from_file(str(base_dir / "tokenizer.json"))
    tok.encode_special_tokens = True
    base = LinguagemProfunda(Configuracao(**state["config"]))
    base.load_state_dict(state["modelo"], strict=True)
    return base_dir, base, tok, state

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive-root", default="/content/drive/MyDrive/CRIVO/checkpoints")
    ap.add_argument("--batch-size", type=int, default=20)
    ap.add_argument("--steps", type=int, default=STEPS)
    args = ap.parse_args()

    assert torch.cuda.is_available(), "GPU obrigatória para este experimento"
    device = "cuda"
    torch.manual_seed(SEED)
    random.seed(SEED)
    root = Path(args.drive_root)

    base_dir, base, tok, state = load_base(root)
    print("BASE CONGELADA:", base_dir, flush=True)
    for p in base.parameters():
        p.requires_grad = False
    base_hash_before = fingerprint_state(base.state_dict())
    base = base.to(device).eval()

    train_entities = make_entities(tok, SEED + 1, TRAIN_ENTITIES, "train")
    dev_entities = make_entities(tok, SEED + 2, DEV_ENTITIES, "dev")
    blind_entities = make_entities(tok, SEED + 3, BLIND_ENTITIES, "blind")
    train_names = {e.name for e in train_entities}
    assert train_names.isdisjoint({e.name for e in dev_entities})
    assert train_names.isdisjoint({e.name for e in blind_entities})

    train_pool = train_cases(train_entities)
    dev = eval_cases(dev_entities)
    blind = eval_cases(blind_entities)
    print("ENTIDADES: train", len(train_entities), "dev", len(dev_entities), "blind", len(blind_entities), flush=True)
    print("CASOS CEGOS:", len(blind), "(100 cópia pura + 500 semânticos)", flush=True)

    baseline = evaluate(base, None, tok, blind, "BASELINE_FROZEN")

    head = PointerCopyHead(base.config.dimensao, rank=RANK).to(device)
    params = sum(p.numel() for p in head.parameters())
    base_params = sum(p.numel() for p in base.parameters())
    print(f"POINTER PARAMS: {params} ({100*params/base_params:.3f}% do Transformer)", flush=True)

    opt = torch.optim.AdamW(head.parameters(), lr=2e-3, weight_decay=0.01)
    no_copy_pool = [c for c in train_pool if not c.requires_copy]
    copy_pool = [c for c in train_pool if c.requires_copy]
    rng = random.Random(SEED)
    best_dev = -1.0
    best_state = None
    history = []

    for step in range(1, args.steps + 1):
        n_no = max(1, args.batch_size // 4)
        batch = [rng.choice(no_copy_pool) for _ in range(n_no)] + [rng.choice(copy_pool) for _ in range(args.batch_size - n_no)]
        rng.shuffle(batch)
        x, y, source_mask = collate(tok, batch, base.config.contexto, device)
        opt.zero_grad(set_to_none=True)
        loss, gate_mean, copy_p = pointer_loss(base, head, x, y, source_mask)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(head.parameters(), 1.0)
        opt.step()

        if step == 1 or step % 100 == 0:
            print(f"step {step}/{args.steps} loss={loss.item():.4f} gate={gate_mean:.3f} copy_p={copy_p:.3f}", flush=True)

        if step % 250 == 0 or step == args.steps:
            devr = evaluate(base, head, tok, dev, f"DEV_{step}")
            score = devr["summary"]["by_skill"].get("copia_pura", {}).get("accuracy", 0.0)
            sem = devr["summary"]["semantic_overall"]
            history.append({"step": step, "copy_exact": score, "semantic_overall": sem})
            combined = score + 0.1 * sem
            if combined > best_dev:
                best_dev = combined
                best_state = {k: v.detach().cpu().clone() for k, v in head.state_dict().items()}

    if best_state is None:
        best_state = {k: v.detach().cpu().clone() for k, v in head.state_dict().items()}
    head.load_state_dict(best_state)
    after = evaluate(base, head, tok, blind, "POINTER_AFTER")
    base_hash_after = fingerprint_state(base.state_dict())
    assert base_hash_before == base_hash_after, "ERRO: pesos base mudaram apesar do congelamento"
    print("BASE HASH INALTERADO:", base_hash_after[:16], flush=True)

    b = baseline["summary"]
    a = after["summary"]
    copy_acc = a["by_skill"]["copia_pura"]["accuracy"]
    distant = a["copy_by_lexical_group"].get("distant", {}).get("accuracy", 0.0)
    close = a["copy_by_lexical_group"].get("close", {}).get("accuracy", 0.0)
    pos_vals = [v["accuracy"] for v in a["copy_by_position"].values()]
    pos_spread = max(pos_vals) - min(pos_vals) if pos_vals else 1.0
    fn_before = b["by_skill"]["funcao"]["accuracy"]
    fn_after = a["by_skill"]["funcao"]["accuracy"]
    sem_before = b["semantic_overall"]
    sem_after = a["semantic_overall"]

    gate = {
        "copy_exact_min": 0.70,
        "distant_copy_min": 0.65,
        "lexical_gap_max": 0.10,
        "position_spread_max": 0.10,
        "function_regression_max_pp": 5.0,
        "semantic_regression_max_pp": 2.0,
        "copy_exact_pass": copy_acc >= 0.70,
        "distant_copy_pass": distant >= 0.65,
        "lexical_gap_pass": abs(close - distant) <= 0.10,
        "position_spread_pass": pos_spread <= 0.10,
        "function_preserved_pass": fn_after >= fn_before - 0.05,
        "semantic_preserved_pass": sem_after >= sem_before - 0.02,
    }
    gate["pass"] = all(v for k, v in gate.items() if k.endswith("_pass"))

    outroot = root / "experimento_pointer_copy"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = outroot / f"run_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    torch.save({
        "versao": 1,
        "pointer_state": best_state,
        "config": {"rank": RANK, "dim": base.config.dimensao, "vocab": base.config.vocabulario},
        "base_checkpoint": str(base_dir),
        "base_step": int(state.get("passo", 0)),
        "transformer_frozen": True,
        "lm_head_frozen": True,
        "base_sha256": base_hash_after,
        "pesos_externos": False,
        "ativo_no_chat": False,
        "promovido": False,
        "seed": SEED,
    }, out / "pointer_copy.pt")
    shutil.copy2(base_dir / "tokenizer.json", out / "tokenizer.json")
    result = {
        "protocol": "pointer_copy_causal_v1",
        "single_intervention": "copy_distribution_low_rank_pointer_plus_gate",
        "transformer_frozen": True,
        "lm_head_frozen": True,
        "base_sha256_before": base_hash_before,
        "base_sha256_after": base_hash_after,
        "base_unchanged": base_hash_before == base_hash_after,
        "steps": args.steps,
        "pointer_params": params,
        "pointer_percent_of_base": 100 * params / base_params,
        "baseline": baseline,
        "after": after,
        "history": history,
        "derived": {
            "copy_exact": copy_acc,
            "distant_copy": distant,
            "close_copy": close,
            "lexical_gap": abs(close - distant),
            "position_spread": pos_spread,
            "function_before": fn_before,
            "function_after": fn_after,
            "semantic_before": sem_before,
            "semantic_after": sem_after,
        },
        "gate": gate,
        "ativo_no_chat": False,
        "promovido": False,
    }
    (out / "resultado_pointer_copy.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nEXPERIMENTO POINTER COPY FINALIZADO", flush=True)
    print("Copy exata:", f"{copy_acc:.1%}", "| distante:", f"{distant:.1%}", "| close:", f"{close:.1%}", flush=True)
    print("Função:", f"{fn_before:.1%} -> {fn_after:.1%}", flush=True)
    print("Semântica:", f"{sem_before:.1%} -> {sem_after:.1%}", flush=True)
    print("Gate:", "PASSOU" if gate["pass"] else "NÃO PASSOU", flush=True)
    print("Saída:", out, flush=True)
    print("ativo_no_chat=false", flush=True)

if __name__ == "__main__":
    main()
