"""Faz o 46M do CRIVO (v7c) crescer para ~290M sem trocar de modelo: o que ele sabe fica, e ele ganha largura e camadas.

Crescimento que preserva a função (o modelo crescido diz exatamente o mesmo que o v7c no começo):

- largura (384 → 768, 8 → 16 cabeças de 48): cada número do fluxo residual vira dois iguais, [x, x].
  A LayerNorm de [x, x] é [y, y] (mesma média, mesma variância); cada camada linear vira quatro cópias
  da original pela metade, então [y, y] dá [q, q]: as 16 cabeças são as 8 originais em dobro, com a mesma
  dimensão por cabeça, e a atenção é a mesma. O embedding é compartilhado com a saída: duplicado, ele
  dobraria os logits, então a norma final é multiplicada por 0,5;
- profundidade (24 → 40 camadas): entram 16 blocos novos, um depois de cada um dos blocos 0, 1, 3, 4, …
  (dois a cada três). Como em scripts/crescer_17m.py, cada bloco novo copia normas, atenção e a primeira
  camada do MLP do bloco anterior, e a projeção da atenção e a última camada do MLP começam em zero:
  pelo resíduo, é a identidade.

Depois da conferência, um ruído pequeno (`ruido`) separa as cópias, para elas aprenderem coisas diferentes;
com ruido=0 a saída é idêntica à do original.

Uso:
  python scripts/crescer_46m.py --origem pasta_do_v7c/ --destino crescido/
  python scripts/crescer_46m.py --conferir      # com os pesos do v7c no repositório: a saída não muda
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import torch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

import linguagem_profunda as lp  # noqa: E402

ZERADOS = ("projecao.weight", "mlp.2.weight", "mlp.2.bias")


def _dobrar_linear(w):
    """W (saída, entrada) → W' (2·saída, 2·entrada) que leva [y, y] a [W·y, W·y]."""
    meio = w / 2
    return torch.cat([torch.cat([meio, meio], 1), torch.cat([meio, meio], 1)], 0)


def _dobrar_qkv(w, d):
    """qkv (3d, d) → (6d, 2d): q, k e v dobrados cada um, na ordem que o chunk(3) do Bloco espera."""
    return torch.cat([_dobrar_linear(p) for p in w.split(d, 0)], 0)


def _dobrar(v):
    return torch.cat([v, v], -1)


def crescer_largura(estado, config):
    """(estado, config) com o dobro da largura e das cabeças; a mesma saída."""
    d = config["dimensao"]
    novo = {}
    for k, v in estado.items():
        if k in ("embedding.weight", "posicao.weight"):
            novo[k] = _dobrar(v)
        elif k == "norm.weight" or k == "norm.bias":
            novo[k] = _dobrar(v) * 0.5   # o embedding duplicado dobraria os logits
        elif k.endswith(("norm1.weight", "norm1.bias", "norm2.weight", "norm2.bias", "mlp.0.bias", "mlp.2.bias")):
            novo[k] = _dobrar(v)
        elif k.endswith("qkv.weight"):
            novo[k] = _dobrar_qkv(v, d)
        elif k.endswith(("projecao.weight", "mlp.0.weight", "mlp.2.weight")):
            novo[k] = _dobrar_linear(v)
        else:
            raise KeyError("parâmetro inesperado: " + k)
    return novo, dict(config, dimensao=2 * d, cabecas=2 * config["cabecas"])


def crescer_profundidade(estado, config, depois_de):
    """Um bloco novo (identidade pelo resíduo) depois de cada bloco em `depois_de`."""
    novo, destino = {}, 0
    for b in range(config["camadas"]):
        prefixo = f"blocos.{b}."
        bloco = {k[len(prefixo):]: v for k, v in estado.items() if k.startswith(prefixo)}
        for repeticao in range(2 if b in depois_de else 1):
            for nome, valor in bloco.items():
                valor = valor.clone()
                if repeticao and nome in ZERADOS:
                    valor.zero_()
                novo[f"blocos.{destino}.{nome}"] = valor
            destino += 1
    novo.update({k: v.clone() for k, v in estado.items() if not k.startswith("blocos.")})
    return novo, dict(config, camadas=destino)


def crescer_estado(estado, config, camadas=40, ruido=1e-4, semente=20261020):
    """(estado novo, config nova) do v7c crescido: largura dobrada e `camadas` blocos."""
    estado, config = crescer_largura(estado, config)
    extras = camadas - config["camadas"]
    if not 0 <= extras <= config["camadas"]:
        raise ValueError("só cabe até um bloco novo depois de cada bloco original")
    # Espalhados: dois a cada três blocos ganham um novo depois (16 de 24 → 40).
    depois_de = sorted(range(config["camadas"]), key=lambda b: (b % 3 == 2, b))[:extras]
    estado, config = crescer_profundidade(estado, config, set(depois_de))
    if ruido:
        g = torch.Generator().manual_seed(semente)
        for k, v in estado.items():
            if v.dim() == 2 and not k.endswith(ZERADOS):
                estado[k] = v + ruido * v.std() * torch.randn(v.shape, generator=g, dtype=v.dtype)
    return estado, config


def crescer(origem, destino, camadas=40, ruido=1e-4):
    origem, destino = Path(origem), Path(destino)
    salvo = torch.load(origem / "pesos.pt", map_location="cpu", weights_only=True)
    estado, cfg = crescer_estado(salvo["modelo"], salvo["config"], camadas, ruido)
    destino.mkdir(parents=True, exist_ok=True)
    execucao = dict(salvo.get("execucao", {}))
    execucao.update(crescido_de=hashlib.sha256((origem / "pesos.pt").read_bytes()).hexdigest(),
                    crescimento={"largura": cfg["dimensao"], "cabecas": cfg["cabecas"], "camadas": cfg["camadas"],
                                 "ruido": ruido, "script": "scripts/crescer_46m.py"})
    torch.save({"versao": salvo.get("versao", lp.VERSAO), "modelo": estado, "config": cfg, "passo": 0,
                "execucao": execucao}, destino / "pesos.pt")
    shutil.copyfile(origem / "tokenizer.json", destino / "tokenizer.json")
    print(f"crescido: {salvo['config']['dimensao']}×{salvo['config']['camadas']} → {cfg['dimensao']}×{cfg['camadas']}, "
          f"{sum(v.numel() for v in estado.values()) / 1e6:.1f}M parâmetros → {destino}")
    return cfg


def estado_do_npz(caminho):
    """O state_dict do v7c a partir do npz do site (int8 por linha → float32)."""
    import numpy as np
    z = np.load(caminho)
    meta = json.loads(str(z["meta"]))
    estado = {}
    for k in z.files:
        if k == "meta" or k.endswith(".escala"):
            continue
        if k.endswith(".q8"):
            base = k[:-3]
            estado[base] = torch.from_numpy(z[k].astype("float32") * z[base + ".escala"].astype("float32"))
        else:
            estado[k] = torch.from_numpy(z[k].astype("float32"))
    config = {"vocabulario": estado["embedding.weight"].shape[0], "dimensao": estado["embedding.weight"].shape[1],
              "camadas": meta["camadas"], "cabecas": meta["cabecas"], "contexto": meta["contexto"], "dropout": 0.0}
    return estado, config


def conferir(camadas=40):
    """Com o v7c do repositório: o crescido (sem ruído) dá os mesmos logits; com ruído, quase os mesmos."""
    estado, config = estado_do_npz(RAIZ / "artefatos" / "conversa46m_v7c_pt" / "pesos_numpy.npz")
    original = lp.LinguagemProfunda(lp.Configuracao(**config)).eval()
    original.load_state_dict(estado)
    ids = torch.randint(5, config["vocabulario"], (2, 160), generator=torch.Generator().manual_seed(1))
    with torch.no_grad():
        a = original(ids)[0]
        resultados = {}
        for ruido in (0.0, 1e-4):
            novo, cfg = crescer_estado(estado, config, camadas, ruido)
            crescido = lp.LinguagemProfunda(lp.Configuracao(**cfg)).eval()
            crescido.load_state_dict(novo)
            b = crescido(ids)[0]
            resultados[ruido] = (float((a - b).abs().max()), float((a.argmax(-1) == b.argmax(-1)).float().mean()))
    n = sum(v.numel() for v in novo.values())
    print(f"v7c {sum(v.numel() for v in estado.values()) / 1e6:.1f}M ({config['dimensao']}×{config['camadas']}) → "
          f"{n / 1e6:.1f}M ({cfg['dimensao']}×{cfg['camadas']}, {cfg['cabecas']} cabeças)")
    for ruido, (dif, top1) in resultados.items():
        print(f"  ruído {ruido:g}: maior diferença de logit {dif:.2e}, mesma palavra mais provável em {top1:.1%}")
    if resultados[0.0][0] > 1e-3:
        sys.exit("o crescimento mudou a saída")
    return resultados


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--origem")
    ap.add_argument("--destino")
    ap.add_argument("--camadas", type=int, default=40)
    ap.add_argument("--ruido", type=float, default=1e-4)
    ap.add_argument("--conferir", action="store_true")
    a = ap.parse_args()
    if a.conferir:
        conferir(a.camadas)
    else:
        crescer(a.origem, a.destino, a.camadas, a.ruido)


if __name__ == "__main__":
    main()
