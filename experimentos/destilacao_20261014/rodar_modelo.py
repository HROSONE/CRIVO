"""Roda um modelo de terceiros (vLLM) sobre uma lista de pedidos de chat. Só no Colab (AGENTS.md).

Entrada (jsonl.gz): {"id", "mensagens", "max_tokens", "temperatura"}. Saída (jsonl.gz): {"id", "texto", "fim"}.
Os pesos ficam no disco do Colab (HF_HOME) e nunca vão para o Drive nem para o repositório.
O professor precisa de licença que permita treinar com as saídas (Apache 2.0 ou MIT); o juiz só dá nota.

Uso: python rodar_modelo.py --modelo Qwen/Qwen3-32B-AWQ --papel professor --entrada a.jsonl.gz --saida b.jsonl.gz
Código de saída 3: o modelo não existe, não tem a licença certa ou não coube na GPU (tente o próximo).
"""
import argparse
import gzip
import json
import sys
import time
from datetime import date
from pathlib import Path

LICENCAS_PROFESSOR = {"apache-2.0", "mit"}
MAX_MODELO = 4096
PEDACO = 3000


def licenca_de(info):
    return str(getattr(info.card_data, "license", None) or next(
        (t.split(":", 1)[1] for t in (info.tags or []) if t.startswith("license:")), "")).lower()


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--papel", choices=("professor", "juiz"), required=True)
    ap.add_argument("--entrada", required=True)
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    saida = Path(a.saida)
    if saida.is_file():
        print("já feito:", saida, flush=True)
        return
    from huggingface_hub import model_info
    try:
        info = model_info(a.modelo)
    except Exception as erro:
        print(f"{a.modelo}: não achei ({type(erro).__name__})", flush=True)
        sys.exit(3)
    licenca = licenca_de(info)
    if a.papel == "professor" and licenca not in LICENCAS_PROFESSOR:
        print(f"{a.modelo}: licença {licenca!r} não serve para professor (AGENTS.md)", flush=True)
        sys.exit(3)
    with gzip.open(a.entrada, "rt", encoding="utf-8") as f:
        pedidos = [json.loads(l) for l in f]
    pedacos = [pedidos[i:i + PEDACO] for i in range(0, len(pedidos), PEDACO)]
    parte = lambda k: saida.with_name(saida.name.replace(".jsonl.gz", "") + ".parte%03d.jsonl.gz" % k)
    faltam = [k for k in range(len(pedacos)) if not parte(k).is_file()]
    print(f"{a.modelo}: {len(pedidos)} pedidos, {len(pedacos)} pedaços, faltam {len(faltam)}", flush=True)
    if faltam:
        import vllm
        from vllm import LLM, SamplingParams
        try:
            llm = LLM(model=a.modelo, revision=info.sha, max_model_len=MAX_MODELO, gpu_memory_utilization=0.90, seed=20261015)
        except Exception as erro:
            print(f"{a.modelo}: não carregou ({type(erro).__name__}: {str(erro)[:200]})", flush=True)
            sys.exit(3)
        quem = {"papel": a.papel, "modelo": a.modelo, "revisao": info.sha, "licenca": licenca,
                "data": date.today().isoformat(), "vllm": vllm.__version__}
        saida.with_name(saida.name.replace(".jsonl.gz", "") + "_modelo.json").write_text(json.dumps(quem, indent=1))
        tok = llm.get_tokenizer()
        for k in faltam:
            t0, lote, msgs, params, grandes = time.time(), [], [], [], 0
            for p in pedacos[k]:
                n = len(tok.apply_chat_template(p["mensagens"], tokenize=True, add_generation_prompt=True, enable_thinking=False))
                if n + p["max_tokens"] > MAX_MODELO:
                    grandes += 1
                    continue
                lote.append(p)
                msgs.append(p["mensagens"])
                params.append(SamplingParams(temperature=p["temperatura"], top_p=0.8 if p["temperatura"] > 0 else 1.0,
                                             top_k=20 if p["temperatura"] > 0 else -1, max_tokens=p["max_tokens"]))
            print(f"  pedaço {k + 1}/{len(pedacos)}: gerando {len(lote)} respostas...", flush=True)
            outs = llm.chat(msgs, params, use_tqdm=True, chat_template_kwargs={"enable_thinking": False})
            tmp = parte(k).with_name(parte(k).name + ".tmp")
            with gzip.open(tmp, "wt", encoding="utf-8") as f:
                for p, o in zip(lote, outs):
                    c = o.outputs[0]
                    f.write(json.dumps({"id": p["id"], "texto": c.text, "fim": c.finish_reason}, ensure_ascii=False) + "\n")
            tmp.rename(parte(k))   # pedaço só conta quando está inteiro; se a sessão cair, recomeça do próximo
            print(f"  pedaço {k + 1}/{len(pedacos)}: {len(lote)} respostas, {grandes} longas demais, {time.time() - t0:.0f}s", flush=True)
    tmp = saida.with_name(saida.name + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        for k in range(len(pedacos)):
            with gzip.open(parte(k), "rt", encoding="utf-8") as g:
                f.write(g.read())
    tmp.rename(saida)
    for k in range(len(pedacos)):
        parte(k).unlink()


if __name__ == "__main__":
    principal()
