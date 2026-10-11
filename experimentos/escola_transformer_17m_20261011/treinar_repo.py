#!/usr/bin/env python3
"""Executa a Escola Cognitiva no Transformer 17M versionado no repositório.

O artefato de entrada é a cópia NumPy/FP16 que passou pelo ajuste experimental
do leitor (passo 1000), derivada da base própria de pré-treino de SHA
16102a72... . Ele NÃO é confundido com a base crua. O resultado nunca ativa
chat automaticamente: primeiro precisa vencer os gates prospectivos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import torch

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path[:0] = [str(RAIZ), str(AQUI)]

import treinar_escola as escola  # noqa: E402
from linguagem_profunda import Configuracao, LinguagemProfunda  # noqa: E402

ARTEFATO_SHA = "603ff3b6765d9fc82ff53517560ba3f1abca595e27f5a98c55911f1bb9a2b6dc"
TOKENIZER_SHA = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"
BASE_PRETREINO_SHA = "16102a72b21031b8bee2b4edfa633a359f7f08c5beab552b05f294e656b0cc67"
CONFIG = {"vocabulario":8192,"dimensao":384,"camadas":8,"cabecas":8,"contexto":256,"dropout":0.1}
PARAMETROS = 17_428_224


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def carregar_versionado(pasta: Path, dispositivo: torch.device):
    from tokenizers import Tokenizer

    npz = pasta / "pesos_numpy.npz"
    tok = pasta / "tokenizer.json"
    if sha(npz) != ARTEFATO_SHA:
        raise ValueError("pesos_numpy.npz não corresponde ao artefato 17M pré-comprometido")
    if sha(tok) != TOKENIZER_SHA:
        raise ValueError("tokenizer não corresponde ao artefato 17M pré-comprometido")

    dados = np.load(npz, allow_pickle=False)
    meta = json.loads(str(dados["meta"]))
    for chave, valor in CONFIG.items():
        if meta.get(chave) != valor:
            raise ValueError("configuração divergente em %s" % chave)
    if meta.get("passo") != 1000:
        raise ValueError("artefato esperado é o ajuste do leitor no passo 1000")

    modelo = LinguagemProfunda(Configuracao(**CONFIG))
    estado = modelo.state_dict()
    chaves = set(estado)
    disponiveis = {k for k in dados.files if k != "meta"}
    if chaves != disponiveis:
        raise ValueError("chaves do artefato não coincidem com o Transformer")
    convertido = {k: torch.from_numpy(dados[k].astype(np.float32, copy=False)) for k in estado}
    modelo.load_state_dict(convertido, strict=True)
    if sum(p.numel() for p in modelo.parameters()) != PARAMETROS:
        raise ValueError("contagem de parâmetros inesperada")
    modelo.to(dispositivo)

    tokenizer = Tokenizer.from_file(str(tok))
    tokenizer.encode_special_tokens = True
    if tokenizer.get_vocab_size() != CONFIG["vocabulario"]:
        raise ValueError("vocabulário incompatível")
    origem = {
        "config": CONFIG,
        "passo": 1000,
        "execucao": {
            "tokenizer_sha256": TOKENIZER_SHA,
            "pesos_externos": False,
            "base_pretreino_sha256": BASE_PRETREINO_SHA,
            "artefato_versionado_sha256": ARTEFATO_SHA,
            "origem": "ajuste experimental do leitor derivado da base própria 17M",
        },
    }
    return modelo, tokenizer, origem


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--dispositivo", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    dev = torch.device(args.dispositivo)
    pasta = Path(args.base)
    saida = Path(args.saida)

    # As funções pedagógicas e os gates são exatamente os congelados no #153.
    escola.TOK_SHA = TOKENIZER_SHA
    escola.BASE_SHA = ARTEFATO_SHA
    escola.PARAMETROS = PARAMETROS

    torch.manual_seed(escola.SEMENTE)
    if dev.type == "cuda":
        torch.cuda.manual_seed_all(escola.SEMENTE)

    modelo, tokenizer, origem = carregar_versionado(pasta, dev)
    treino = escola.treinar(modelo, tokenizer, dev)
    print("treino fixado; abrindo holdout prospectivo...", flush=True)
    holdout, manifesto = escola.abrir_holdout()
    textos = json.loads((AQUI / "preservacao_portugues.json").read_text(encoding="utf-8"))["textos"]

    base, tok_base, _ = carregar_versionado(pasta, dev)
    avaliacao_base = escola.avaliar(base, tok_base, holdout, dev)
    preservacao_base = escola.preservacao(base, tok_base, textos, dev)
    del base
    if dev.type == "cuda":
        torch.cuda.empty_cache()

    avaliacao = escola.avaliar(modelo, tokenizer, holdout, dev)
    preservacao = escola.preservacao(modelo, tokenizer, textos, dev)
    gates, derivados = escola.gates(avaliacao_base, avaliacao, preservacao_base, preservacao)
    elegivel = all(gates.values())
    simples = lambda x: {k:v for k,v in x.items() if k != "detalhes"}

    saida.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pasta / "tokenizer.json", saida / "tokenizer.json")
    checkpoint = {
        "versao": 1,
        "modelo": {k:v.detach().cpu() for k,v in modelo.state_dict().items()},
        "config": CONFIG,
        "passo": origem["passo"],
        "execucao": {
            "tokenizer_sha256": TOKENIZER_SHA,
            "semente": escola.SEMENTE,
            "pesos_externos": False,
            "base_pretreino_sha256": BASE_PRETREINO_SHA,
            "artefato_inicial_sha256": ARTEFATO_SHA,
            "escola_cognitiva": {
                "versao": 1,
                "passos": escola.PASSOS,
                "auxiliares_serializados": False,
                "ativo_no_chat": False,
            },
        },
    }
    torch.save(checkpoint, saida / "pesos.pt")
    checkpoint_sha = sha(saida / "pesos.pt")
    resultado = {
        "versao": 1,
        "origem": checkpoint["execucao"],
        "parametros": PARAMETROS,
        "treino": treino,
        "holdout": manifesto,
        "avaliacao_base": simples(avaliacao_base),
        "avaliacao_candidato": simples(avaliacao),
        "preservacao_base": preservacao_base,
        "preservacao_candidato": preservacao,
        "gates": gates,
        "derivados": derivados,
        "elegivel_promocao": elegivel,
        "ativo_no_chat": False,
        "checkpoint_sha256": checkpoint_sha,
        "detalhes_holdout": avaliacao["detalhes"],
    }
    (saida / "resultados.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (saida / "meta.json").write_text(json.dumps({
        "papel": "candidato de diálogo da Escola Cognitiva sobre Transformer próprio 17M",
        "base_pretreino_sha256": BASE_PRETREINO_SHA,
        "artefato_inicial_sha256": ARTEFATO_SHA,
        "checkpoint_sha256": checkpoint_sha,
        "elegivel_promocao": elegivel,
        "ativo_no_chat": False,
        "pesos_externos": False,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "elegivel_promocao": elegivel,
        "gates": gates,
        "base": simples(avaliacao_base),
        "candidato": simples(avaliacao),
        "preservacao_relativa": derivados["preservacao_ce_relativa"],
        "checkpoint_sha256": checkpoint_sha,
        "ativo_no_chat": False,
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
