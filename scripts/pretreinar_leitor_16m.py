"""Pré-treino do Transformer próprio (~17M) para ser a base do leitor do CRIVO.

Pesos aleatórios, vocabulário próprio: nenhum modelo pré-treinado é baixado.
Feito para o Colab com GPU (notebooks/treinar_transformer_leitor_colab.ipynb),
mas roda em qualquer máquina com PyTorch.

Etapas (--etapa):
  dados       baixa a Wikipédia em português inteira (6 partes, SHA-256
              conferido) e os diálogos humanos em português do OpenAssistant;
              limpa (corta Referências/Ligações externas, tira duplicatas e
              textos curtos) e junta os fatos do acervo do CRIVO;
  tokenizador BPE de bytes próprio (8.192 tokens) aprendido só com o treino;
  tokenizar   grava os ids em uint16 (treino e validação) no disco local;
  treinar     modelo de linguagem causal; AdamW, aquecimento e cosseno,
              precisão mista na GPU; validação a cada --avaliar-a-cada passos;
  exportar    grava a base no formato que o leitor espera
              (pesos.pt + tokenizer.json), a partir do melhor da validação.

Checkpoint: um único arquivo, sobrescrito (gravação atômica), a cada
--checkpoint-a-cada passos (padrão 10.000) e ao fim do orçamento de tempo.
Nada se acumula: o Drive guarda no máximo um checkpoint e a base final.
"""
import argparse
import dataclasses
import hashlib
import json
import math
import random
import re
import shutil
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

SEMENTE = 20261007
VOCABULARIO = 8192
REVISAO_WIKI = "b04c8d1ceb2f5cd4588862100d08de323dccfbaa"
WIKIPEDIA = [  # wikimedia/wikipedia 20231101.pt (CC-BY-SA-3.0/GFDL), SHA-256 do LFS
    ("train-00000-of-00006.parquet", "059136d457150f9c033a4bdfb7fbea2eef2b6e58e03e2c0cb8275144ce99fb34"),
    ("train-00001-of-00006.parquet", "5e9b4476c0d69b0bffdcf76529de424dfda9510e3a6867676e5d482e6c70f1be"),
    ("train-00002-of-00006.parquet", "d136dc9359e96408ed739bedc3c7da0bb4ee4481597299eb5d4170b36d1fca9c"),
    ("train-00003-of-00006.parquet", "786f1ee2e400298e4b0889de8eef4d8bc465629cf773970a84adb520ae900e4f"),
    ("train-00004-of-00006.parquet", "181d7004d5cedf4704ec5baa5c1c549520634234e3bdf7ea9aa8cfeb0f505cbc"),
    ("train-00005-of-00006.parquet", "5d60245e7e8c8176e2b9f7f0ed5ba5dcf4eb748bb94f852582ccac01d7ec72fd"),
]
MODELO = {"vocabulario": VOCABULARIO, "dimensao": 384, "camadas": 8, "cabecas": 8, "contexto": 256, "dropout": 0.1}
# Seções do fim dos artigos sem conteúdo corrido.
CORTES = re.compile(r"\n(?:Referências|Ligações externas|Bibliografia|Ver também|Notas|Leitura adicional|"
                    r"Fontes|Notas e referências)\s*\n")


def _sha(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _baixar(url, destino, sha):
    destino = Path(destino)
    if destino.exists() and _sha(destino) == sha:
        return destino
    tmp = destino.with_suffix(destino.suffix + ".parcial")
    for tentativa in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as src, tmp.open("wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
            break
        except OSError:
            if tentativa == 3:
                raise
            time.sleep(2 ** (tentativa + 1))
    if _sha(tmp) != sha:
        tmp.unlink()
        raise ValueError("SHA-256 diverge: " + url)
    tmp.replace(destino)
    return destino


def particao(texto):
    """Validação: 0,5% dos documentos, pelo hash do texto (estável)."""
    return "validacao" if int(hashlib.sha256(texto.encode()).hexdigest()[:8], 16) % 200 == 0 else "treino"


def limpar_artigo(texto):
    m = CORTES.search(texto)
    if m:
        texto = texto[:m.start()]
    linhas = [l.strip() for l in texto.split("\n")]
    # Linhas muito curtas que não terminam frase são títulos de seção ou restos de tabela.
    linhas = [l for l in linhas if len(l) >= 40 or (l and l[-1] in ".!?:")]
    return "\n".join(linhas).strip()


def textos_acervo():
    """Fatos do acervo do CRIVO e respostas da base antiga (sem dados de teste)."""
    from crivo import Crivo
    bot = Crivo()
    for it in bot.compositor.itens.values():
        fatos = [f["texto"] if isinstance(f, dict) else str(f) for f in it["fatos"]]
        yield it["nome"] + ". " + " ".join(fatos)
    for e in bot.base:
        if e.get("resposta"):
            yield e["resposta"]


def etapa_dados(args):
    import pyarrow.parquet as pq
    fontes, saida = Path(args.fontes), Path(args.dados)
    fontes.mkdir(parents=True, exist_ok=True)
    saida.mkdir(parents=True, exist_ok=True)
    vistos, contagem = set(), {"wikipedia": 0, "oasst2": 0, "acervo": 0, "recusados": 0, "duplicados": 0}
    arquivos = {p: (saida / ("%s.txt" % p)).open("w", encoding="utf-8") for p in ("treino", "validacao")}

    def gravar(texto, fonte):
        chave = hashlib.sha256(texto.encode()).hexdigest()
        if chave in vistos:
            contagem["duplicados"] += 1
            return
        vistos.add(chave)
        # Um documento por linha; quebras internas viram o separador  .
        arquivos[particao(texto)].write(texto.replace("\n", " ") + "\n")
        contagem[fonte] += 1

    for nome, sha in WIKIPEDIA:
        url = "https://huggingface.co/datasets/wikimedia/wikipedia/resolve/%s/20231101.pt/%s" % (REVISAO_WIKI, nome)
        caminho = _baixar(url, fontes / nome, sha)
        print("lendo", nome, flush=True)
        for lote in pq.ParquetFile(caminho).iter_batches(batch_size=2048, columns=["title", "text"]):
            for titulo, texto in zip(lote.column("title").to_pylist(), lote.column("text").to_pylist()):
                texto = limpar_artigo(texto or "")
                if len(texto) < 300:
                    contagem["recusados"] += 1
                    continue
                gravar(titulo + "\n" + texto, "wikipedia")
        print(contagem, flush=True)
    # Diálogos humanos em português (OpenAssistant oasst2, Apache-2.0).
    from scripts.baixar_fontes_linguagem import baixar
    baixar("oasst2", fontes)
    import gzip
    with gzip.open(fontes / "oasst2.messages.jsonl.gz", "rt", encoding="utf-8") as f:
        for linha in f:
            m = json.loads(linha)
            if m.get("lang") == "pt-BR" and len(m.get("text", "")) >= 80 and not m.get("deleted"):
                gravar(m["text"].strip(), "oasst2")
    # Fatos do acervo, duas vezes: são poucos e são o que o leitor vai ler.
    for _ in range(2):
        for texto in textos_acervo():
            chave = hashlib.sha256(texto.encode()).hexdigest()
            vistos.discard(chave)
            gravar(texto, "acervo")
    for f in arquivos.values():
        f.close()
    (saida / "manifesto.json").write_text(json.dumps({
        "wikipedia": {"dataset": "wikimedia/wikipedia", "revisao": REVISAO_WIKI, "arquivos": WIKIPEDIA,
                      "licenca": "CC-BY-SA-3.0/GFDL"},
        "oasst2": "OpenAssistant/oasst2 (Apache-2.0), mensagens pt-BR", "acervo": "fatos do CRIVO",
        "contagem": contagem, "pesos_pre_treinados": False}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("dados:", contagem, flush=True)


def _documentos(caminho, limite=None):
    with open(caminho, encoding="utf-8") as f:
        for i, linha in enumerate(f):
            if limite is not None and i >= limite:
                return
            yield linha.rstrip("\n").replace(" ", "\n")


def etapa_tokenizador(args):
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
    from linguagem_profunda import ESPECIAIS
    dados = Path(args.dados)
    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    treinador = trainers.BpeTrainer(vocab_size=VOCABULARIO, min_frequency=2, special_tokens=ESPECIAIS,
                                    initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
    # 300 mil documentos de treino bastam para as frequências; nada da validação.
    tok.train_from_iterator(_documentos(dados / "treino.txt", 300000), treinador)
    tok.encode_special_tokens = True
    tok.save(str(dados / "tokenizer.json"))
    print("tokenizador:", tok.get_vocab_size(), "tokens", flush=True)


def etapa_tokenizar(args):
    import numpy as np
    from tokenizers import Tokenizer
    dados = Path(args.dados)
    tok = Tokenizer.from_file(str(dados / "tokenizer.json"))
    doc, fim = tok.token_to_id("<documento>"), tok.token_to_id("<fim>")
    for parte in ("treino", "validacao"):
        total = 0
        with (dados / ("%s.bin" % parte)).open("wb") as out:
            lote = []
            for texto in _documentos(dados / ("%s.txt" % parte)):
                lote.append(texto)
                if len(lote) == 2000:
                    total += _gravar_ids(out, tok, lote, doc, fim, np)
                    lote = []
            if lote:
                total += _gravar_ids(out, tok, lote, doc, fim, np)
        print(parte, total, "tokens", flush=True)


def _gravar_ids(out, tok, textos, doc, fim, np):
    total = 0
    for enc in tok.encode_batch(textos, add_special_tokens=False):
        ids = np.asarray([doc] + enc.ids + [fim], dtype=np.uint16)
        out.write(ids.tobytes())
        total += len(ids)
    return total


def _lote(dados, contexto, tamanho, gerador, np, torch, dispositivo):
    inicio = gerador.integers(0, len(dados) - contexto - 1, size=tamanho)
    x = np.stack([dados[i:i + contexto] for i in inicio]).astype(np.int64)
    y = np.stack([dados[i + 1:i + 1 + contexto] for i in inicio]).astype(np.int64)
    return torch.from_numpy(x).to(dispositivo, non_blocking=True), torch.from_numpy(y).to(dispositivo, non_blocking=True)


def salvar_atomico(estado, caminho):
    import torch
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(".tmp")
    torch.save(estado, tmp)
    tmp.replace(caminho)  # sobrescreve: nunca há mais de um checkpoint


def etapa_treinar(args):
    import numpy as np
    import torch
    from linguagem_profunda import Configuracao, LinguagemProfunda
    dados = Path(args.dados)
    dispositivo = args.dispositivo
    treino = np.memmap(dados / "treino.bin", dtype=np.uint16, mode="r")
    valid = np.memmap(dados / "validacao.bin", dtype=np.uint16, mode="r")
    config = Configuracao(**MODELO)
    torch.manual_seed(SEMENTE)
    modelo = LinguagemProfunda(config).to(dispositivo)
    parametros = sum(p.numel() for p in modelo.parameters())
    decai = [p for n, p in modelo.named_parameters() if p.dim() >= 2]
    sem_decai = [p for n, p in modelo.named_parameters() if p.dim() < 2]
    opt = torch.optim.AdamW([{"params": decai, "weight_decay": 0.1}, {"params": sem_decai, "weight_decay": 0.0}],
                            lr=args.lr, betas=(0.9, 0.95), fused=dispositivo == "cuda")
    bf16 = dispositivo == "cuda" and torch.cuda.is_bf16_supported()
    tipo = torch.bfloat16 if bf16 else torch.float16
    escala = torch.cuda.amp.GradScaler(enabled=dispositivo == "cuda" and not bf16)
    ckpt = Path(args.checkpoint)
    passo, melhor, melhor_estado = 0, float("inf"), None
    gerador = np.random.default_rng(SEMENTE)
    if ckpt.exists():
        estado = torch.load(ckpt, map_location="cpu", weights_only=False)
        modelo.load_state_dict(estado["modelo"])
        opt.load_state_dict(estado["opt"])
        escala.load_state_dict(estado["escala"])
        passo, melhor, melhor_estado = estado["passo"], estado["melhor"], estado["melhor_estado"]
        gerador = np.random.default_rng(SEMENTE + passo)
        print("retomando do passo", passo, "| melhor validação", melhor, flush=True)
    print("parâmetros:", parametros, "| tokens de treino:", len(treino), "| dispositivo:", dispositivo,
          "| precisão:", "bf16" if bf16 else "fp16" if dispositivo == "cuda" else "fp32", flush=True)

    def taxa(p):
        if p < args.aquecimento:
            return args.lr * (p + 1) / args.aquecimento
        progresso = min(1.0, (p - args.aquecimento) / max(1, args.passos - args.aquecimento))
        return args.lr * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * progresso)))

    @torch.no_grad()
    def validar():
        modelo.eval()
        g = np.random.default_rng(SEMENTE)
        perdas = []
        for _ in range(args.lotes_validacao):
            x, y = _lote(valid, config.contexto, args.lote, g, np, torch, dispositivo)
            with torch.autocast(device_type="cuda", dtype=tipo, enabled=dispositivo == "cuda"):
                perdas.append(modelo(x, y)[1].item())
        modelo.train()
        return sum(perdas) / len(perdas)

    def checkpoint():
        salvar_atomico({"modelo": modelo.state_dict(), "opt": opt.state_dict(), "escala": escala.state_dict(),
                        "passo": passo, "melhor": melhor, "melhor_estado": melhor_estado,
                        "config": dataclasses.asdict(config)}, ckpt)
        print("checkpoint gravado no passo", passo, "->", ckpt, flush=True)

    inicio, ultimo = time.time(), time.time()
    modelo.train()
    while passo < args.passos:
        for g in opt.param_groups:
            g["lr"] = taxa(passo)
        x, y = _lote(treino, config.contexto, args.lote, gerador, np, torch, dispositivo)
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
            print("passo %d/%d perda %.3f lr %.2e | %.0f tokens/s" % (
                passo, args.passos, perda.item(), taxa(passo),
                100 * args.lote * config.contexto / (agora - ultimo)), flush=True)
            ultimo = agora
        if passo % args.avaliar_a_cada == 0 or passo == args.passos:
            v = validar()
            print("passo %d | validação %.4f (melhor %.4f)" % (passo, v, melhor), flush=True)
            if v < melhor:
                melhor = v
                melhor_estado = {k: t.detach().to("cpu", copy=True) for k, t in modelo.state_dict().items()}
        fim_tempo = args.max_horas and time.time() - inicio > args.max_horas * 3600
        if passo % args.checkpoint_a_cada == 0 or passo == args.passos or fim_tempo:
            checkpoint()
        if fim_tempo:
            print("Orçamento de tempo atingido no passo", passo, "- rode de novo para continuar.", flush=True)
            return
    print("pré-treino concluído:", passo, "passos | melhor validação", melhor, flush=True)


def etapa_exportar(args):
    import torch
    dados, saida = Path(args.dados), Path(args.base)
    estado = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if estado["passo"] < args.passos:
        raise SystemExit("Pré-treino incompleto (%d de %d passos)." % (estado["passo"], args.passos))
    saida.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(dados / "tokenizer.json", saida / "tokenizer.json")
    sha = _sha(saida / "tokenizer.json")
    pesos = estado["melhor_estado"] or estado["modelo"]
    torch.save({"modelo": pesos, "config": estado["config"], "passo": estado["passo"],
                "execucao": {"tokenizer_sha256": sha, "semente": SEMENTE, "pesos_externos": False}},
               saida / "pesos.pt")
    manifesto = json.loads((dados / "manifesto.json").read_text(encoding="utf-8"))
    (saida / "relatorio.json").write_text(json.dumps({
        "papel": "base própria do leitor do CRIVO (modelo de linguagem causal)",
        "config": estado["config"], "passos": estado["passo"], "melhor_validacao": estado["melhor"],
        "perplexidade_validacao": math.exp(estado["melhor"]), "dados": manifesto,
        "pesos_externos": False}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("base exportada em", saida, "| validação", estado["melhor"], flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--etapa", required=True, choices=("dados", "tokenizador", "tokenizar", "treinar", "exportar"))
    ap.add_argument("--fontes", default="/content/crivo-fontes")
    ap.add_argument("--dados", default="/content/crivo-dados")
    ap.add_argument("--checkpoint", default="/content/drive/MyDrive/CRIVO/transformer-leitor/checkpoint.pt")
    ap.add_argument("--base", default="/content/drive/MyDrive/CRIVO/transformer-leitor/base")
    ap.add_argument("--passos", type=int, default=40000)
    ap.add_argument("--lote", type=int, default=64)
    ap.add_argument("--lr", type=float, default=6e-4)
    ap.add_argument("--aquecimento", type=int, default=1000)
    ap.add_argument("--avaliar-a-cada", type=int, default=1000)
    ap.add_argument("--lotes-validacao", type=int, default=50)
    ap.add_argument("--checkpoint-a-cada", type=int, default=10000)
    ap.add_argument("--max-horas", type=float, default=0, help="pausa com checkpoint depois desse tempo")
    ap.add_argument("--dispositivo", default=None)
    args = ap.parse_args()
    if args.etapa == "treinar" and "/drive/" in args.checkpoint and args.checkpoint_a_cada < 10000:
        raise SystemExit("Checkpoint no Drive a cada menos de 10.000 passos enche o Drive; use 10.000 ou mais.")
    if args.dispositivo is None:
        import torch
        args.dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    random.seed(SEMENTE)
    {"dados": etapa_dados, "tokenizador": etapa_tokenizador, "tokenizar": etapa_tokenizar,
     "treinar": etapa_treinar, "exportar": etapa_exportar}[args.etapa](args)


if __name__ == "__main__":
    main()
