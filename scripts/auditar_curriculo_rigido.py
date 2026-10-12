#!/usr/bin/env python3
"""Auditoria rígida dos checkpoints do treino curricular longo.

Corrige a falha do scorer original: uma resposta só conta como correta se
preservar o NOME EXATO da entidade artificial, além da relação semântica
esperada. Assim respostas como "Trinta pertence à categoria ferramenta" não
podem passar quando a entidade pedida é "xdozens".

Não treina nem promove o CRIVO. Apenas compara as seis fases já salvas.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import time
import unicodedata
from pathlib import Path

import torch
from tokenizers import Tokenizer

from linguagem_profunda import Configuracao, ESPECIAIS, LinguagemProfunda, fonte_dialogo

SEED = 202610112348
CFG = {
    "vocabulario": 8192,
    "dimensao": 384,
    "camadas": 8,
    "cabecas": 8,
    "contexto": 256,
    "dropout": 0.1,
}

CATEGORIES = [
    ("recipiente", ["armazenar líquidos", "transportar líquidos", "conter amostras", "guardar substâncias"]),
    ("instrumento", ["medir temperatura", "observar objetos distantes", "detectar vibrações", "registrar sinais"]),
    ("ferramenta", ["golpear peças", "cortar materiais", "fixar componentes", "apertar parafusos"]),
    ("dispositivo", ["processar dados", "emitir alertas", "controlar fluxo", "registrar eventos"]),
    ("móvel", ["servir de assento", "apoiar objetos", "guardar itens", "organizar materiais"]),
    ("estrutura", ["sustentar uma carga", "proteger uma área", "conectar duas partes", "separar ambientes"]),
]
TEST_MATERIALS = ["quartzo", "cobre", "bambu", "resina", "argila"]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def essential(text: str) -> list[str]:
    stop = {"de", "da", "do", "para", "um", "uma", "e", "a", "o", "os", "as"}
    return [w for w in re.findall(r"[a-zA-ZÀ-ÿ]+", norm(text)) if len(w) > 2 and w not in stop]


def make_names(seed: int, n: int, prefix: str) -> list[str]:
    rng = random.Random(seed)
    a = ["na", "ze", "tor", "lum", "fi", "dra", "kel", "vo", "ri", "san", "bel", "tri", "mo", "pa", "xel", "gu", "pri", "do", "var", "chi"]
    b = ["lo", "ra", "mi", "to", "ve", "na", "po", "ri", "sa", "du", "xel", "go", "fi", "la", "ne", "bar", "ti", "cor", "zen", "mar"]
    c = ["", "n", "s", "r", "m"]
    out, seen = [], set()
    while len(out) < n:
        name = prefix + rng.choice(a) + rng.choice(b) + rng.choice(c)
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def make_entities(n: int):
    seed = SEED + 30
    rng = random.Random(seed)
    names = make_names(seed + 991, n, "x")
    out = []
    for name in names:
        cat, funcs = rng.choice(CATEGORIES)
        fn = rng.choice(funcs)
        m1, m2 = rng.sample(TEST_MATERIALS, 2)
        out.append((name, cat, fn, m1, m2))
    return out


def wrong_category(cat: str) -> str:
    cats = [c for c, _ in CATEGORIES]
    i = cats.index(cat)
    return cats[(i + 1) % len(cats)]


def build_cases(n_entities: int):
    cases = []
    for name, cat, fn, m1, m2 in make_entities(n_entities):
        intro = f"Considere um objeto inventado chamado {name}. Ele é um {cat} usado para {fn}."
        wc = wrong_category(cat)
        cases += [
            {"skill": "categoria", "name": name, "cat": cat, "fn": fn,
             "q": f"{intro} A que categoria {name} pertence?"},
            {"skill": "funcao", "name": name, "cat": cat, "fn": fn,
             "q": f"{intro} Qual é a função de {name}?"},
            {"skill": "invariancia", "name": name, "cat": cat, "fn": fn,
             "q": f"{intro} Ele era de {m1} e agora é de {m2}. Só por isso deixa de ser {name}?"},
            {"skill": "composicao", "name": name, "cat": cat, "fn": fn,
             "q": f"{intro} Explique em uma frase o que {name} é e para que serve."},
            {"skill": "negacao", "name": name, "cat": cat, "fn": fn,
             "q": f"{name.capitalize()} não é um {wc}. {intro} {name.capitalize()} pertence à categoria {wc}?"},
        ]
    return cases


def strict_ok(case: dict, answer: str) -> bool:
    a = norm(answer)
    name = norm(case["name"])
    cat = norm(case["cat"])
    fn_words = essential(case["fn"])

    # Regra nova e central: não existe acerto sem preservar a entidade pedida.
    if name not in a:
        return False
    skill = case["skill"]
    if skill == "categoria":
        return cat in a
    if skill == "funcao":
        return all(w in a for w in fn_words)
    if skill == "invariancia":
        return "nao" in a and cat in a
    if skill == "composicao":
        return cat in a and all(w in a for w in fn_words)
    if skill == "negacao":
        return "nao" in a and cat in a
    return False


@torch.no_grad()
def generate(model, tok, q: str, max_tokens: int = 40) -> str:
    src = fonte_dialogo(tok, q, (), CFG["contexto"])
    fim = tok.token_to_id("<fim>")
    prohibited = [tok.token_to_id(t) for t in ESPECIAIS[:-1]]
    ids, _ = model.gerar(src, fim, max_tokens=max_tokens, temperatura=0, top_k=0,
                         semente=SEED, proibidos=prohibited)
    return tok.decode(ids).strip()


def load_checkpoint(path: Path, device: str):
    state = torch.load(path / "pesos.pt", map_location="cpu", weights_only=True)
    if state.get("config") != CFG:
        raise ValueError(f"Configuração incompatível em {path}")
    model = LinguagemProfunda(Configuracao(**CFG)).to(device)
    model.load_state_dict(state["modelo"], strict=True)
    model.eval()
    tok = Tokenizer.from_file(str(path / "tokenizer.json"))
    tok.encode_special_tokens = True
    return model, tok, state


def evaluate_phase(path: Path, cases: list[dict], device: str):
    print(f"\n=== AUDITANDO {path.name} ===", flush=True)
    model, tok, state = load_checkpoint(path, device)
    good = 0
    by = {}
    examples = []
    start = time.time()
    for i, case in enumerate(cases, 1):
        answer = generate(model, tok, case["q"])
        ok = strict_ok(case, answer)
        good += int(ok)
        rec = by.setdefault(case["skill"], [0, 0])
        rec[0] += int(ok)
        rec[1] += 1
        if len(examples) < 12:
            examples.append({"q": case["q"], "a": answer, "ok": ok, "skill": case["skill"]})
        if i % 100 == 0:
            print(f"{path.name}: {i}/{len(cases)}", flush=True)
    return {
        "phase": path.name,
        "step": int(state.get("passo", 0)),
        "correct": good,
        "total": len(cases),
        "accuracy": good / max(1, len(cases)),
        "by_skill": {k: {"correct": v[0], "total": v[1], "accuracy": v[0]/v[1]} for k, v in by.items()},
        "seconds": time.time() - start,
        "samples": examples,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive-root", default="/content/drive/MyDrive/CRIVO/checkpoints")
    ap.add_argument("--entities", type=int, default=100, help="100 entidades x 5 = 500 casos por fase")
    args = ap.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("Use GPU: a auditoria completa gera milhares de respostas.")
    device = "cuda"
    root = Path(args.drive_root) / "escola_curricular_longa"
    runs = sorted(p for p in root.glob("run_*") if p.is_dir())
    if not runs:
        raise FileNotFoundError(f"Nenhum run encontrado em {root}")
    run = runs[-1]
    phases = sorted(p for p in run.iterdir() if p.is_dir() and (p / "pesos.pt").exists())
    if len(phases) != 6:
        raise RuntimeError(f"Esperava 6 fases, encontrei {len(phases)} em {run}")

    cases = build_cases(args.entities)
    print("GPU:", torch.cuda.get_device_name(0), flush=True)
    print("Run:", run, flush=True)
    print("Casos rígidos por fase:", len(cases), flush=True)

    results = []
    for phase in phases:
        r = evaluate_phase(phase, cases, device)
        results.append(r)
        print(json.dumps({k: r[k] for k in ("phase", "step", "correct", "total", "accuracy", "by_skill")}, ensure_ascii=False, indent=2), flush=True)

    best = max(results, key=lambda r: (r["accuracy"], min(x["accuracy"] for x in r["by_skill"].values())))
    summary = {
        "protocol": "strict_identity_v1",
        "criterion": "nome exato da entidade + relação semântica obrigatória",
        "entities": args.entities,
        "cases_per_phase": len(cases),
        "results": results,
        "best_phase": best["phase"],
        "best_accuracy": best["accuracy"],
        "promotion_authorized": False,
        "ativo_no_chat": False,
    }
    out = run / "auditoria_rigida.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== AUDITORIA RÍGIDA FINALIZADA ===", flush=True)
    for r in results:
        print(f"{r['phase']}: {r['correct']}/{r['total']} = {100*r['accuracy']:.1f}%", flush=True)
    print("Melhor fase rígida:", best["phase"], f"({100*best['accuracy']:.1f}%)", flush=True)
    print("Salvo em:", out, flush=True)
    print("ativo_no_chat=false", flush=True)


if __name__ == "__main__":
    main()
