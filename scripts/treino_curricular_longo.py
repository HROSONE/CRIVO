#!/usr/bin/env python3
"""Treino curricular longo do CRIVO 17,43M.

Parte do checkpoint composicional mais recente no Google Drive e executa seis
fases de treino intercalado com:
- currículo crescente;
- repetição espaçada/replay;
- hard negatives via loss de ranking;
- unfreezing progressivo;
- avaliação de desenvolvimento por fase;
- teste cego final com 500 casos de entidades artificiais nunca usadas no treino.

Nenhum modelo externo é carregado. O resultado permanece experimental e não
é ativado no chat automaticamente.
"""
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
from dataclasses import dataclass
from pathlib import Path

import torch
from torch.nn import functional as F
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
TOTAL_STEPS = 10_000

PHASES = [
    {"name": "01_identidade", "steps": 1500, "lr": 8e-6, "unfreeze": 3, "embedding": False, "rank_every": 0},
    {"name": "02_binding", "steps": 1500, "lr": 7e-6, "unfreeze": 4, "embedding": False, "rank_every": 3},
    {"name": "03_contrastes", "steps": 1500, "lr": 6e-6, "unfreeze": 4, "embedding": False, "rank_every": 2},
    {"name": "04_composicao", "steps": 2000, "lr": 5e-6, "unfreeze": 5, "embedding": True, "rank_every": 3},
    {"name": "05_dialogo_estado", "steps": 2000, "lr": 4e-6, "unfreeze": 5, "embedding": True, "rank_every": 3},
    {"name": "06_generalizacao", "steps": 1500, "lr": 3.5e-6, "unfreeze": 6, "embedding": True, "rank_every": 2},
]
assert sum(p["steps"] for p in PHASES) == TOTAL_STEPS

CATEGORIES = [
    ("recipiente", [
        "armazenar líquidos", "transportar líquidos", "conter amostras", "guardar substâncias"
    ]),
    ("instrumento", [
        "medir temperatura", "observar objetos distantes", "detectar vibrações", "registrar sinais"
    ]),
    ("ferramenta", [
        "golpear peças", "cortar materiais", "fixar componentes", "apertar parafusos"
    ]),
    ("dispositivo", [
        "processar dados", "emitir alertas", "controlar fluxo", "registrar eventos"
    ]),
    ("móvel", [
        "servir de assento", "apoiar objetos", "guardar itens", "organizar materiais"
    ]),
    ("estrutura", [
        "sustentar uma carga", "proteger uma área", "conectar duas partes", "separar ambientes"
    ]),
]
TRAIN_MATERIALS = ["metal", "vidro", "madeira", "cerâmica", "plástico", "fibra", "pedra", "borracha"]
TEST_MATERIALS = ["quartzo", "cobre", "bambu", "resina", "argila"]

GENERIC_REPLAY = [
    ("O que uma correção explícita deve fazer com uma informação anterior incorreta?",
     "Ela deve substituir a informação anterior incorreta pela informação corrigida."),
    ("Uma hipótese não confirmada deve ser tratada como fato?",
     "Não. Uma hipótese não confirmada continua sendo uma possibilidade provisória."),
    ("Por que o contexto importa numa conversa?",
     "Porque o contexto ajuda a interpretar referências e a relacionar o turno atual com informações anteriores."),
    ("O que significa dizer que uma categoria é mais geral que um objeto particular?",
     "Significa que a categoria reúne diferentes objetos que compartilham características relevantes."),
    ("Qual a diferença entre uma propriedade e uma função?",
     "Uma propriedade descreve como algo é; uma função descreve o que algo faz ou para que serve."),
    ("O que uma resposta deve fazer em relação à pergunta?",
     "Ela deve fornecer informação relevante ao pedido feito e respeitar o contexto."),
    ("Se uma propriedade externa muda, a identidade precisa mudar também?",
     "Não necessariamente. A identidade pode permanecer se as relações centrais continuarem válidas."),
    ("Quando duas informações entram em conflito e a segunda é uma correção explícita, qual deve valer?",
     "A segunda informação, porque ela atualiza e substitui a anterior."),
]


@dataclass(frozen=True)
class Entity:
    name: str
    category: str
    function: str
    material_a: str
    material_b: str


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def make_names(seed: int, n: int, prefix: str) -> list[str]:
    rng = random.Random(seed)
    a = ["na", "ze", "tor", "lum", "fi", "dra", "kel", "vo", "ri", "san", "bel", "tri", "mo", "pa", "xel", "gu", "pri", "do", "var", "chi"]
    b = ["lo", "ra", "mi", "to", "ve", "na", "po", "ri", "sa", "du", "xel", "go", "fi", "la", "ne", "bar", "ti", "cor", "zen", "mar"]
    c = ["", "n", "s", "r", "m"]
    out = []
    seen = set()
    while len(out) < n:
        name = prefix + rng.choice(a) + rng.choice(b) + rng.choice(c)
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def make_entities(seed: int, n: int, prefix: str, materials: list[str]) -> list[Entity]:
    rng = random.Random(seed)
    names = make_names(seed + 991, n, prefix)
    out = []
    for name in names:
        cat, funcs = rng.choice(CATEGORIES)
        fn = rng.choice(funcs)
        m1, m2 = rng.sample(materials, 2)
        out.append(Entity(name, cat, fn, m1, m2))
    return out


def wrong_category(cat: str) -> str:
    cats = [x[0] for x in CATEGORIES if x[0] != cat]
    return cats[hash(cat) % len(cats)]


def essential_words(text: str) -> list[str]:
    stop = {"de", "da", "do", "para", "um", "uma", "e", "a", "o", "os", "as"}
    return [w for w in re.findall(r"[a-zA-ZÀ-ÿ]+", _norm(text)) if len(w) > 2 and w not in stop]


def mk_item(q: str, a: str, skill: str, neg: str | None = None, history=()):
    return {"q": q, "a": a, "skill": skill, "neg": neg, "history": list(history)}


def phase1(entities: list[Entity]) -> list[dict]:
    items = []
    for e in entities:
        intro = f"Considere {e.name}: ele é um {e.category} usado para {e.function}."
        items += [
            mk_item(
                f"{intro} O que é {e.name}?",
                f"{e.name.capitalize()} é um {e.category} usado para {e.function}.",
                "identidade",
                f"{e.name.capitalize()} é um {wrong_category(e.category)}."
            ),
            mk_item(
                f"{intro} A que categoria {e.name} pertence?",
                f"{e.name.capitalize()} pertence à categoria {e.category}.",
                "categoria",
                f"{e.name.capitalize()} pertence à categoria {wrong_category(e.category)}."
            ),
            mk_item(
                f"{intro} Qual é a função principal de {e.name}?",
                f"A função principal de {e.name} é {e.function}.",
                "funcao",
                f"A função principal de {e.name} é decorar uma parede."
            ),
            mk_item(
                f"{intro} Se {e.name} passar de {e.material_a} para {e.material_b}, ele deixa necessariamente de ser {e.name}?",
                f"Não. Mudar de {e.material_a} para {e.material_b} não muda necessariamente a identidade de {e.name}; ele continua sendo um {e.category} usado para {e.function}.",
                "invariancia",
                f"Sim. Só por mudar o material, {e.name} deixa de ser {e.name}."
            ),
        ]
    return items


def phase2(entities: list[Entity]) -> list[dict]:
    items = []
    for i in range(0, len(entities) - 1, 2):
        a, b = entities[i], entities[i + 1]
        prompt = (
            f"Há dois objetos. {a.name} é um {a.category} usado para {a.function}. "
            f"{b.name} é um {b.category} usado para {b.function}."
        )
        items += [
            mk_item(
                f"{prompt} Qual deles é usado para {a.function}?",
                f"{a.name.capitalize()} é o objeto usado para {a.function}.",
                "binding_funcao",
                f"{b.name.capitalize()} é o objeto usado para {a.function}."
            ),
            mk_item(
                f"{prompt} Qual deles pertence à categoria {b.category}?",
                f"{b.name.capitalize()} pertence à categoria {b.category}.",
                "binding_categoria",
                f"{a.name.capitalize()} pertence à categoria {b.category}."
            ),
            mk_item(
                f"{prompt} Relacione cada objeto à sua função sem trocar as referências.",
                f"{a.name.capitalize()} serve para {a.function}; {b.name} serve para {b.function}.",
                "binding_duplo",
                f"{a.name.capitalize()} serve para {b.function}; {b.name} serve para {a.function}."
            ),
        ]
    return items


def phase3(entities: list[Entity]) -> list[dict]:
    items = []
    for e in entities:
        wc = wrong_category(e.category)
        intro = f"{e.name.capitalize()} não é um {wc}. {e.name.capitalize()} é um {e.category} usado para {e.function}."
        items += [
            mk_item(
                f"{intro} {e.name.capitalize()} é um {wc}?",
                f"Não. {e.name.capitalize()} é um {e.category}, não um {wc}.",
                "negacao",
                f"Sim. {e.name.capitalize()} é um {wc}."
            ),
            mk_item(
                f"É apenas uma hipótese que {e.name} seja feito de {e.material_b}; sabemos apenas que ele é um {e.category} usado para {e.function}. "
                f"O material {e.material_b} deve ser tratado como fato confirmado?",
                f"Não. O material {e.material_b} continua sendo apenas uma hipótese; o que está estabelecido é que {e.name} é um {e.category} usado para {e.function}.",
                "hipotese",
                f"Sim. {e.material_b} já é um fato confirmado."
            ),
            mk_item(
                f"{e.name.capitalize()} era descrito como {wc}, mas a informação foi corrigida: ele é um {e.category} usado para {e.function}. Qual categoria vale agora?",
                f"A categoria corrigida é {e.category}; a descrição anterior como {wc} deve ser descartada.",
                "correcao",
                f"A categoria que vale é {wc}."
            ),
        ]
    return items


def phase4(entities: list[Entity]) -> list[dict]:
    items = []
    for i, e in enumerate(entities):
        e2 = entities[(i + 7) % len(entities)]
        items += [
            mk_item(
                f"Dados: {e.name} é um {e.category}; sua função é {e.function}; pode ser feito de {e.material_a}. "
                "Produza uma explicação curta que una categoria, função e material sem confundir essas relações.",
                f"{e.name.capitalize()} é um {e.category} usado para {e.function} e pode ser feito de {e.material_a}.",
                "composicao_3",
                f"{e.name.capitalize()} é um {e.material_a} usado para ser {e.function}."
            ),
            mk_item(
                f"{e.name.capitalize()} é um {e.category} usado para {e.function}. "
                f"{e2.name.capitalize()} é um {e2.category} usado para {e2.function}. "
                "Compare os dois indicando uma diferença de categoria ou função.",
                f"{e.name.capitalize()} é um {e.category} e serve para {e.function}, enquanto {e2.name} é um {e2.category} e serve para {e2.function}.",
                "comparacao",
                f"{e.name.capitalize()} e {e2.name} têm exatamente a mesma categoria e função."
            ),
            mk_item(
                f"Se todo {e.category} desse tipo mantém sua categoria quando apenas o material muda, e {e.name} é um {e.category}, "
                f"o que podemos concluir se {e.name} mudar de {e.material_a} para {e.material_b}?",
                f"Podemos concluir que a mudança de material, por si só, não obriga {e.name} a deixar de ser um {e.category}.",
                "inferencia",
                f"Podemos concluir que {e.name} deixa automaticamente de ser um {e.category}."
            ),
        ]
    return items


def phase5(entities: list[Entity]) -> list[dict]:
    items = []
    for i, e in enumerate(entities):
        replacement = entities[(i + 11) % len(entities)]
        h1 = [
            {"papel": "usuario", "texto": f"O objeto atual é {e.name}."},
            {"papel": "assistente", "texto": f"Entendido: o objeto atual é {e.name}."},
            {"papel": "usuario", "texto": f"Correção: o objeto atual é {replacement.name}, não {e.name}."},
            {"papel": "assistente", "texto": f"Atualizado: agora o objeto atual é {replacement.name}."},
        ]
        items.append(mk_item(
            "Qual objeto deve valer como atual agora?",
            f"O objeto atual é {replacement.name}; a referência anterior a {e.name} foi substituída pela correção.",
            "estado_correcao",
            f"O objeto atual ainda é {e.name}.",
            h1,
        ))

        h2 = [
            {"papel": "usuario", "texto": f"{e.name.capitalize()} é um {e.category} usado para {e.function}."},
            {"papel": "assistente", "texto": "Entendido."},
            {"papel": "usuario", "texto": f"Talvez ele seja feito de {e.material_b}, mas isso ainda não foi confirmado."},
            {"papel": "assistente", "texto": "Certo, o material continua incerto."},
        ]
        items.append(mk_item(
            f"O que sabemos como fato sobre {e.name} e o que continua hipótese?",
            f"Sabemos que {e.name} é um {e.category} usado para {e.function}; ser feito de {e.material_b} continua sendo apenas uma hipótese.",
            "estado_hipotese",
            f"É fato que {e.name} é feito de {e.material_b}.",
            h2,
        ))

        h3 = [
            {"papel": "usuario", "texto": f"Quando eu disser 'ele', estou falando de {e.name}."},
            {"papel": "assistente", "texto": "Entendido."},
            {"papel": "usuario", "texto": f"{e.name.capitalize()} é um {e.category} usado para {e.function}."},
            {"papel": "assistente", "texto": "Certo."},
        ]
        items.append(mk_item(
            "Para que ele serve?",
            f"Ele se refere a {e.name}, que serve para {e.function}.",
            "referencia_contextual",
            "Ele se refere a outro objeto e serve para uma função desconhecida.",
            h3,
        ))
    return items


def phase6(entities: list[Entity]) -> list[dict]:
    items = []
    p1 = phase1(entities)
    p2 = phase2(entities)
    p3 = phase3(entities)
    p4 = phase4(entities)
    p5 = phase5(entities)
    for pool in (p1, p2, p3, p4, p5):
        stride = max(1, len(pool) // max(1, len(entities)))
        items.extend(pool[::stride])
    for e in entities:
        items.append(mk_item(
            f"Explique para uma pessoa, sem listar campos, o que é {e.name} com base nestes fatos: "
            f"categoria={e.category}; função={e.function}; material possível={e.material_a}.",
            f"{e.name.capitalize()} é um {e.category} usado para {e.function}; uma de suas possíveis formas pode ser feita de {e.material_a}.",
            "geracao_natural",
            f"{e.name.capitalize()} é apenas um material chamado {e.material_a}."
        ))
    return items


def build_phase_pools(train_entities: list[Entity]) -> list[list[dict]]:
    spans = [
        train_entities[:900],
        train_entities[150:1050],
        train_entities[300:1200],
        train_entities[450:1350],
        train_entities[600:1500],
        train_entities[750:1650],
    ]
    makers = [phase1, phase2, phase3, phase4, phase5, phase6]
    return [maker(ents) for maker, ents in zip(makers, spans)]


def encode_text(tok: Tokenizer, text: str) -> list[int]:
    return tok.encode(text, add_special_tokens=False).ids


def item_tensors(tok: Tokenizer, item: dict, answer_override: str | None = None):
    answer = answer_override if answer_override is not None else item["a"]
    src = fonte_dialogo(tok, item["q"], item.get("history", ()), CFG["contexto"])
    resp = encode_text(tok, answer) + [tok.token_to_id("<fim>")]
    seq = src + resp
    if len(seq) > CFG["contexto"]:
        raise ValueError(f"Exemplo excede contexto ({len(seq)}): {item['q'][:120]}")
    x = seq[:-1]
    y = [-100] * (len(src) - 1) + seq[len(src):]
    assert len(x) == len(y)
    return x, y


def collate(tok: Tokenizer, items: list[dict], overrides: list[str] | None = None, device="cuda"):
    pad = tok.token_to_id("<pad>")
    pairs = []
    for i, item in enumerate(items):
        ov = None if overrides is None else overrides[i]
        pairs.append(item_tensors(tok, item, ov))
    maxlen = max(len(x) for x, _ in pairs)
    xs, ys = [], []
    for x, y in pairs:
        xs.append(x + [pad] * (maxlen - len(x)))
        ys.append(y + [-100] * (maxlen - len(y)))
    return (
        torch.tensor(xs, dtype=torch.long, device=device),
        torch.tensor(ys, dtype=torch.long, device=device),
    )


def per_example_nll(model, x, y):
    logits, _ = model(x)
    b, t, v = logits.shape
    losses = F.cross_entropy(logits.reshape(-1, v), y.reshape(-1), ignore_index=-100, reduction="none").reshape(b, t)
    mask = (y != -100).float()
    return (losses * mask).sum(1) / mask.sum(1).clamp_min(1.0)


def set_trainable(model: LinguagemProfunda, last_blocks: int, train_embedding: bool):
    for p in model.parameters():
        p.requires_grad = False
    for block in model.blocos[-last_blocks:]:
        for p in block.parameters():
            p.requires_grad = True
    for p in model.norm.parameters():
        p.requires_grad = True
    if train_embedding:
        for p in model.embedding.parameters():
            p.requires_grad = True
    return [p for p in model.parameters() if p.requires_grad]


def lr_at(base_lr: float, step: int, total: int):
    warmup = max(20, int(total * 0.05))
    if step < warmup:
        return base_lr * (step + 1) / warmup
    progress = (step - warmup) / max(1, total - warmup)
    return base_lr * (0.15 + 0.85 * 0.5 * (1.0 + math.cos(math.pi * progress)))


def sample_batch(rng: random.Random, current: list[dict], previous: list[dict], batch_size: int, phase_idx: int):
    out = []
    for _ in range(batch_size):
        r = rng.random()
        if phase_idx == 0:
            source = current if r < 0.9 else None
        else:
            source = current if r < 0.68 else previous if r < 0.92 and previous else None
        if source is None:
            q, a = rng.choice(GENERIC_REPLAY)
            out.append(mk_item(q, a, "replay"))
        else:
            out.append(rng.choice(source))
    return out


@torch.no_grad()
def generate(model, tok: Tokenizer, q: str, history=(), max_tokens=40) -> str:
    model.eval()
    src = fonte_dialogo(tok, q, history, CFG["contexto"])
    fim = tok.token_to_id("<fim>")
    prohibited = [tok.token_to_id(t) for t in ESPECIAIS[:-1]]
    ids, _ = model.gerar(src, fim, max_tokens=max_tokens, temperatura=0, top_k=0, semente=SEED, proibidos=prohibited)
    return tok.decode(ids).strip()


def eval_cases(entities: list[Entity]) -> list[dict]:
    cases = []
    for e in entities:
        intro = f"Considere um objeto inventado chamado {e.name}. Ele é um {e.category} usado para {e.function}."
        fn_words = essential_words(e.function)
        cases += [
            {"skill": "categoria", "q": f"{intro} A que categoria {e.name} pertence?", "must": essential_words(e.category)},
            {"skill": "funcao", "q": f"{intro} Qual é a função de {e.name}?", "must": fn_words},
            {"skill": "invariancia", "q": f"{intro} Ele era de {e.material_a} e agora é de {e.material_b}. Só por isso deixa de ser {e.name}?", "must": ["nao", _norm(e.category)]},
            {"skill": "composicao", "q": f"{intro} Explique em uma frase o que {e.name} é e para que serve.", "must": essential_words(e.category) + fn_words},
            {"skill": "negacao", "q": f"{e.name.capitalize()} não é um {wrong_category(e.category)}. {intro} {e.name.capitalize()} pertence à categoria {wrong_category(e.category)}?", "must": ["nao", _norm(e.category)]},
        ]
    return cases


def score_answer(answer: str, must: list[str]) -> bool:
    a = _norm(answer)
    return all(_norm(x) in a for x in must)


@torch.no_grad()
def evaluate(model, tok, cases: list[dict], label: str, print_samples=6):
    model.eval()
    total = good = 0
    by = {}
    samples = []
    start = time.time()
    for idx, c in enumerate(cases, 1):
        ans = generate(model, tok, c["q"])
        ok = score_answer(ans, c["must"])
        total += 1
        good += int(ok)
        s = by.setdefault(c["skill"], [0, 0])
        s[0] += int(ok)
        s[1] += 1
        if len(samples) < print_samples:
            samples.append({"q": c["q"], "a": ans, "ok": ok, "skill": c["skill"]})
        if idx % 100 == 0:
            print(f"[{label}] {idx}/{len(cases)}")
    result = {
        "label": label,
        "correct": good,
        "total": total,
        "accuracy": good / max(1, total),
        "by_skill": {k: {"correct": v[0], "total": v[1], "accuracy": v[0] / max(1, v[1])} for k, v in by.items()},
        "seconds": time.time() - start,
        "samples": samples,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def save_checkpoint(out_dir: Path, model, tok_path: Path, base_state: dict, step: int, phase: str, metrics: dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    tok_sha = _sha(tok_path)
    state = {
        "versao": base_state["versao"],
        "modelo": {k: v.detach().cpu() for k, v in model.state_dict().items()},
        "config": dict(CFG),
        "passo": step,
        "execucao": {
            **dict(base_state.get("execucao", {})),
            "tokenizer_sha256": tok_sha,
            "pesos_externos": False,
            "treino_curricular_longo": True,
            "fase": phase,
            "ativo_no_chat": False,
            "promovido": False,
            "seed": SEED,
        },
    }
    torch.save(state, out_dir / "pesos.pt")
    shutil.copy2(tok_path, out_dir / "tokenizer.json")
    (out_dir / "metricas.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    for extra in ("ponte_v7.pt", "ponte_v7.json"):
        src = tok_path.parent / extra
        if src.exists():
            shutil.copy2(src, out_dir / extra)
    return state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive-root", default="/content/drive/MyDrive/CRIVO/checkpoints")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--blind-entities", type=int, default=100, help="100 entidades x 5 tarefas = 500 casos")
    args = ap.parse_args()

    assert torch.cuda.is_available(), "GPU necessária para este treino."
    device = "cuda"
    print("GPU:", torch.cuda.get_device_name(0))
    torch.manual_seed(SEED)
    random.seed(SEED)
    rng = random.Random(SEED)

    root = Path(args.drive_root)
    src_root = root / "escola_composicional_real"
    candidates = sorted(p for p in src_root.glob("crivo_composicional_*") if (p / "pesos.pt").exists() and (p / "tokenizer.json").exists())
    if not candidates:
        raise FileNotFoundError(f"Nenhum checkpoint composicional encontrado em {src_root}")
    base = candidates[-1]
    print("Checkpoint base:", base)

    base_state = torch.load(base / "pesos.pt", map_location="cpu", weights_only=True)
    if base_state.get("config") != CFG:
        raise ValueError(f"Configuração incompatível: {base_state.get('config')}")
    if base_state.get("versao") != 1:
        raise ValueError("Versão de checkpoint inesperada.")

    tok = Tokenizer.from_file(str(base / "tokenizer.json"))
    tok.encode_special_tokens = True
    if tok.get_vocab_size() != CFG["vocabulario"]:
        raise ValueError("Vocabulário incompatível.")

    tok_sha = _sha(base / "tokenizer.json")
    state_tok_sha = base_state.get("execucao", {}).get("tokenizer_sha256")
    if state_tok_sha and tok_sha != state_tok_sha:
        raise ValueError("Tokenizer não corresponde ao checkpoint.")

    model = LinguagemProfunda(Configuracao(**CFG))
    model.load_state_dict(base_state["modelo"], strict=True)
    model = model.to(device)
    if sum(p.numel() for p in model.parameters()) != 17_428_224:
        raise ValueError("Contagem de parâmetros inesperada.")

    train_entities = make_entities(SEED + 10, 1800, "t", TRAIN_MATERIALS)
    dev_entities = make_entities(SEED + 20, 20, "d", TEST_MATERIALS)
    blind_entities = make_entities(SEED + 30, args.blind_entities, "x", TEST_MATERIALS)

    train_names = {e.name for e in train_entities}
    dev_names = {e.name for e in dev_entities}
    blind_names = {e.name for e in blind_entities}
    assert train_names.isdisjoint(dev_names)
    assert train_names.isdisjoint(blind_names)
    assert dev_names.isdisjoint(blind_names)

    pools = build_phase_pools(train_entities)
    for p, pool in zip(PHASES, pools):
        rng.shuffle(pool)
        print(p["name"], "pool:", len(pool))

    dev_cases = eval_cases(dev_entities)
    blind_cases = eval_cases(blind_entities)

    run_root = root / "escola_curricular_longa"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = run_root / f"run_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "seed": SEED,
        "checkpoint_base": str(base),
        "checkpoint_base_sha256": _sha(base / "pesos.pt"),
        "tokenizer_sha256": tok_sha,
        "parameters": 17_428_224,
        "phases": PHASES,
        "total_steps": TOTAL_STEPS,
        "train_entities": len(train_entities),
        "dev_cases": len(dev_cases),
        "blind_cases": len(blind_cases),
        "blind_names_overlap_train": bool(train_names & blind_names),
        "active_in_chat": False,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== AVALIAÇÃO CEGA ANTES DO TREINO ===")
    baseline_blind = evaluate(model, tok, blind_cases, "blind_before", print_samples=8)
    (run_dir / "blind_before.json").write_text(json.dumps(baseline_blind, ensure_ascii=False, indent=2), encoding="utf-8")

    previous = []
    phase_history = []
    cumulative = 0
    best_dev = -1.0
    best_dir = None
    scaler = torch.amp.GradScaler("cuda")

    for phase_idx, (phase_cfg, current) in enumerate(zip(PHASES, pools)):
        print("\n" + "=" * 80)
        print("FASE", phase_idx + 1, phase_cfg["name"])
        print("=" * 80)

        trainable = set_trainable(model, phase_cfg["unfreeze"], phase_cfg["embedding"])
        optimizer = torch.optim.AdamW(trainable, lr=phase_cfg["lr"], weight_decay=0.01)
        model.train()
        start_phase = time.time()
        running = []
        running_rank = []

        for step in range(phase_cfg["steps"]):
            lr = lr_at(phase_cfg["lr"], step, phase_cfg["steps"])
            for group in optimizer.param_groups:
                group["lr"] = lr

            batch = sample_batch(rng, current, previous, args.batch_size, phase_idx)
            x, y = collate(tok, batch, device=device)
            optimizer.zero_grad(set_to_none=True)

            with torch.amp.autocast("cuda", dtype=torch.float16):
                _, lm_loss = model(x, y)
                loss = lm_loss
                rank_loss = torch.tensor(0.0, device=device)
                if phase_cfg["rank_every"] and step % phase_cfg["rank_every"] == 0:
                    ranked = [it for it in batch if it.get("neg")]
                    if ranked:
                        ranked = ranked[: min(6, len(ranked))]
                        pos_x, pos_y = collate(tok, ranked, device=device)
                        neg_overrides = [it["neg"] for it in ranked]
                        neg_x, neg_y = collate(tok, ranked, overrides=neg_overrides, device=device)
                        pos_nll = per_example_nll(model, pos_x, pos_y)
                        neg_nll = per_example_nll(model, neg_x, neg_y)
                        rank_loss = F.relu(0.35 + pos_nll - neg_nll).mean()
                        loss = loss + 0.22 * rank_loss

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(trainable, 1.0)
            scaler.step(optimizer)
            scaler.update()

            running.append(float(lm_loss.detach()))
            running_rank.append(float(rank_loss.detach()))
            if (step + 1) % 250 == 0 or step == 0:
                print(
                    f"{phase_cfg['name']} {step+1}/{phase_cfg['steps']} "
                    f"lm={sum(running[-100:])/len(running[-100:]):.4f} "
                    f"rank={sum(running_rank[-100:])/len(running_rank[-100:]):.4f} "
                    f"lr={lr:.2e}"
                )

        cumulative += phase_cfg["steps"]
        print(f"Fase concluída em {time.time() - start_phase:.1f}s. Avaliando dev...")
        dev_result = evaluate(model, tok, dev_cases, f"dev_{phase_cfg['name']}", print_samples=4)

        phase_metrics = {
            "phase": phase_cfg["name"],
            "steps_phase": phase_cfg["steps"],
            "steps_total_added": cumulative,
            "global_step": int(base_state.get("passo", 0)) + cumulative,
            "lm_last100": sum(running[-100:]) / max(1, len(running[-100:])),
            "rank_last100": sum(running_rank[-100:]) / max(1, len(running_rank[-100:])),
            "dev": dev_result,
            "seconds": time.time() - start_phase,
        }
        phase_dir = run_dir / f"{phase_idx+1:02d}_{phase_cfg['name']}"
        save_checkpoint(
            phase_dir,
            model,
            base / "tokenizer.json",
            base_state,
            int(base_state.get("passo", 0)) + cumulative,
            phase_cfg["name"],
            phase_metrics,
        )
        phase_history.append(phase_metrics)

        if dev_result["accuracy"] > best_dev:
            best_dev = dev_result["accuracy"]
            best_dir = phase_dir
            print("✅ Novo melhor checkpoint de desenvolvimento:", best_dir, "acc=", best_dev)

        previous.extend(current)
        if len(previous) > 12_000:
            previous = rng.sample(previous, 12_000)

    if best_dir is None:
        raise RuntimeError("Nenhum checkpoint de fase foi salvo.")

    print("\n=== CARREGANDO MELHOR CHECKPOINT POR DEV ===")
    best_state = torch.load(best_dir / "pesos.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(best_state["modelo"], strict=True)
    model.eval()
    print("Melhor dev:", best_dev, "checkpoint:", best_dir)

    print("\n=== TESTE CEGO FINAL — 500 CASOS POR PADRÃO ===")
    final_blind = evaluate(model, tok, blind_cases, "blind_after_best_dev", print_samples=12)

    final_stamp = time.strftime("%Y%m%d_%H%M%S")
    final_dir = run_root / f"crivo_curricular_{final_stamp}"
    final_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_dir / "pesos.pt", final_dir / "pesos.pt")
    shutil.copy2(best_dir / "tokenizer.json", final_dir / "tokenizer.json")
    for extra in ("ponte_v7.pt", "ponte_v7.json"):
        if (best_dir / extra).exists():
            shutil.copy2(best_dir / extra, final_dir / extra)

    summary = {
        "baseline_blind": baseline_blind,
        "final_blind": final_blind,
        "gain_pp": 100.0 * (final_blind["accuracy"] - baseline_blind["accuracy"]),
        "best_dev": best_dev,
        "best_phase_dir": str(best_dir),
        "final_checkpoint": str(final_dir),
        "final_checkpoint_sha256": _sha(final_dir / "pesos.pt"),
        "tokenizer_sha256": _sha(final_dir / "tokenizer.json"),
        "phase_history": phase_history,
        "promotion_gate": {
            "overall_min": 0.60,
            "each_skill_min": 0.45,
            "overall_pass": final_blind["accuracy"] >= 0.60,
            "each_skill_pass": all(v["accuracy"] >= 0.45 for v in final_blind["by_skill"].values()),
        },
        "ativo_no_chat": False,
        "promovido": False,
    }
    summary["promotion_gate"]["pass"] = summary["promotion_gate"]["overall_pass"] and summary["promotion_gate"]["each_skill_pass"]
    (final_dir / "resultado_final.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "resultado_final.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 80)
    print("TREINO CURRICULAR LONGO FINALIZADO")
    print("Blind antes :", f"{baseline_blind['correct']}/{baseline_blind['total']} = {100*baseline_blind['accuracy']:.1f}%")
    print("Blind depois:", f"{final_blind['correct']}/{final_blind['total']} = {100*final_blind['accuracy']:.1f}%")
    print("Ganho       :", f"{summary['gain_pp']:+.1f} p.p.")
    print("Gate        :", "PASSOU" if summary["promotion_gate"]["pass"] else "NÃO PASSOU")
    print("Checkpoint  :", final_dir)
    print("SHA256      :", summary["final_checkpoint_sha256"])
    print("ativo_no_chat=false")
    print("=" * 80)


if __name__ == "__main__":
    main()
