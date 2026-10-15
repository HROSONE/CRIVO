"""Roda um professor (vLLM) sobre as perguntas e guarda as respostas brutas, em pedaços que recomeçam.

Só no Colab (AGENTS.md: o professor nunca roda no CRIVO que conversa). Os pesos do professor ficam
no disco local do Colab (HF_HOME) e nunca vão para o Drive nem para o repositório.

Uso: python gerar_professor.py --modelo Qwen/Qwen3-8B --rotulo medio --perguntas perguntas.jsonl.gz --saida pasta
"""
import argparse
import gzip
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import professor as P  # noqa: E402

LICENCAS = {"apache-2.0", "mit"}   # permitem treinar outro modelo com as saídas
PEDACO = 4000
MAX_MODELO = 4096


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--rotulo", required=True)
    ap.add_argument("--perguntas", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--limite", type=int, default=0, help="só as N primeiras perguntas (teste rápido)")
    a = ap.parse_args()

    from huggingface_hub import model_info
    info = model_info(a.modelo)
    licenca = str(getattr(info.card_data, "license", None) or next(
        (t.split(":", 1)[1] for t in (info.tags or []) if t.startswith("license:")), "")).lower()
    if licenca not in LICENCAS:
        raise SystemExit(f"ERRO: {a.modelo} tem licença {licenca!r}; só {sorted(LICENCAS)} (AGENTS.md).")
    import vllm
    from vllm import LLM, SamplingParams
    prof = {"rotulo": a.rotulo, "modelo": a.modelo, "revisao": info.sha, "licenca": licenca,
            "data": date.today().isoformat(), "vllm": vllm.__version__}
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / f"professor_{a.rotulo}.json").write_text(json.dumps(prof, indent=1))

    with gzip.open(a.perguntas, "rt", encoding="utf-8") as f:
        perguntas = [json.loads(l) for l in f]
    if a.limite:
        perguntas = perguntas[:a.limite]
    pedacos = [perguntas[i:i + PEDACO] for i in range(0, len(perguntas), PEDACO)]
    faltam = [i for i in range(len(pedacos)) if not (saida / f"bruto_{a.rotulo}_{i:03d}.jsonl.gz").is_file()]
    print(f"{a.modelo} @ {info.sha[:10]} ({licenca}) | {len(perguntas)} perguntas, {len(pedacos)} pedaços, faltam {len(faltam)}",
          flush=True)
    if not faltam:
        return

    llm = LLM(model=a.modelo, revision=info.sha, dtype="bfloat16", max_model_len=MAX_MODELO,
              gpu_memory_utilization=0.88, seed=P.SEED)
    tok = llm.get_tokenizer()
    curta = SamplingParams(temperature=0.7, top_p=0.8, top_k=20, max_tokens=P.MAX_TOKENS_CURTA)
    longa = SamplingParams(temperature=0.7, top_p=0.8, top_k=20, max_tokens=P.MAX_TOKENS_LONGA)
    for i in faltam:
        t0 = time.time()
        lote, msgs, params, grande = [], [], [], 0
        for p in pedacos[i]:
            m = P.mensagens(p)
            sp = longa if P.longa(p) else curta
            n = len(tok.apply_chat_template(m, tokenize=True, add_generation_prompt=True, enable_thinking=False))
            if n + sp.max_tokens > MAX_MODELO:
                grande += 1
                continue
            lote.append(p); msgs.append(m); params.append(sp)
        outs = llm.chat(msgs, params, use_tqdm=False, chat_template_kwargs={"enable_thinking": False})
        arq = saida / f"bruto_{a.rotulo}_{i:03d}.jsonl.gz"
        tmp = arq.with_suffix(".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            for p, o in zip(lote, outs):
                c = o.outputs[0]
                f.write(json.dumps({"id": p["id"], "texto": c.text, "fim": c.finish_reason}, ensure_ascii=False) + "\n")
        tmp.rename(arq)   # pedaço só conta quando está inteiro
        print(f"pedaço {i + 1}/{len(pedacos)}: {len(lote)} respostas, {grande} longas demais, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    principal()
