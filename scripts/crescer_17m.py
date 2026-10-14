"""Faz o Transformer do CRIVO crescer sem trocar de modelo: os pesos aprendidos ficam e ganham camadas.

Crescimento que preserva a função (o modelo crescido diz exatamente o mesmo que o original no
começo, e as partes novas aprendem com o treino):

- profundidade: depois de cada bloco original entram `novos_por_bloco` blocos novos. Eles copiam
  normas, atenção e a primeira camada do MLP do bloco anterior (para começar com gradiente útil),
  mas a projeção da atenção e a última camada do MLP começam em zero. Pelo resíduo, cada bloco
  novo é a identidade;
- contexto: as posições aprendidas (0..255) ficam iguais; as novas começam como a última posição
  aprendida, com um ruído pequeno. Sequências de até 256 tokens não mudam nada.

Uso:
  python scripts/crescer_17m.py --origem base/ --destino crescido/ --novos-por-bloco 2 --contexto 1024
  python scripts/crescer_17m.py --conferir      # prova, com pesos do repositório, que a saída não muda
"""
import argparse
import dataclasses
import hashlib
import json
import shutil
import sys
from pathlib import Path

import torch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import linguagem_profunda as lp  # noqa: E402

ZERADOS = ("projecao.weight", "mlp.2.weight", "mlp.2.bias")


def crescer_estado(estado, config, novos_por_bloco=2, contexto=1024, semente=20261014):
    """(estado novo, config nova). `estado` é o state_dict de LinguagemProfunda."""
    g = torch.Generator().manual_seed(semente)
    novo = {}
    destino = 0
    for b in range(config["camadas"]):
        prefixo = f"blocos.{b}."
        bloco = {k[len(prefixo):]: v for k, v in estado.items() if k.startswith(prefixo)}
        for repeticao in range(1 + novos_por_bloco):
            for nome, valor in bloco.items():
                valor = valor.clone()
                if repeticao > 0 and nome in ZERADOS:
                    valor.zero_()
                novo[f"blocos.{destino}.{nome}"] = valor
            destino += 1
    for k, v in estado.items():
        if not k.startswith("blocos."):
            novo[k] = v.clone()
    pos = estado["posicao.weight"]
    if contexto > pos.shape[0]:
        extra = pos[-1:].repeat(contexto - pos.shape[0], 1)
        extra = extra + 0.01 * torch.randn(extra.shape, generator=g, dtype=extra.dtype)
        novo["posicao.weight"] = torch.cat([pos, extra], 0)
    cfg = dict(config, camadas=destino, contexto=max(contexto, pos.shape[0]))
    return novo, cfg


def crescer(origem, destino, novos_por_bloco=2, contexto=1024):
    origem, destino = Path(origem), Path(destino)
    salvo = torch.load(origem / "pesos.pt", map_location="cpu", weights_only=True)
    estado, cfg = crescer_estado(salvo["modelo"], salvo["config"], novos_por_bloco, contexto)
    destino.mkdir(parents=True, exist_ok=True)
    execucao = dict(salvo.get("execucao", {}))
    execucao.update(crescido_de=hashlib.sha256((origem / "pesos.pt").read_bytes()).hexdigest(),
                    crescimento={"novos_por_bloco": novos_por_bloco, "contexto": cfg["contexto"]})
    torch.save({"versao": salvo.get("versao", lp.VERSAO), "modelo": estado, "config": cfg, "passo": 0,
                "execucao": execucao}, destino / "pesos.pt")
    shutil.copyfile(origem / "tokenizer.json", destino / "tokenizer.json")
    n = sum(v.numel() for v in estado.values())
    print(f"crescido: {salvo['config']['camadas']} → {cfg['camadas']} camadas, contexto {cfg['contexto']}, "
          f"{n / 1e6:.1f}M parâmetros → {destino}")
    return cfg


def conferir():
    """Com os pesos NumPy do realizador (17M, no repositório): o crescido dá os mesmos logits."""
    import numpy as np
    npz = np.load(RAIZ / "artefatos" / "realizador_pt" / "pesos_numpy.npz")
    meta = json.loads(str(npz["meta"]))
    config = {k: meta[k] for k in ("vocabulario", "dimensao", "camadas", "cabecas", "contexto", "dropout")}
    estado = {k: torch.from_numpy(npz[k].astype("float32")) for k in npz.files if k != "meta"}
    original = lp.LinguagemProfunda(lp.Configuracao(**config)).eval()
    original.load_state_dict(estado)
    novo_estado, cfg = crescer_estado(estado, config, 2, 1024)
    crescido = lp.LinguagemProfunda(lp.Configuracao(**cfg)).eval()
    crescido.load_state_dict(novo_estado)
    ids = torch.randint(5, config["vocabulario"], (3, 200), generator=torch.Generator().manual_seed(1))
    with torch.no_grad():
        a, b = original(ids)[0], crescido(ids)[0]
        longo = crescido(torch.randint(5, config["vocabulario"], (1, 900)))[0]
    dif = float((a - b).abs().max())
    print(f"original {sum(v.numel() for v in estado.values()) / 1e6:.1f}M, {config['camadas']} camadas | "
          f"crescido {sum(v.numel() for v in novo_estado.values()) / 1e6:.1f}M, {cfg['camadas']} camadas, contexto "
          f"{cfg['contexto']} | maior diferença de logit: {dif:.2e} | 900 tokens ok: {tuple(longo.shape)}")
    if dif > 1e-4:
        sys.exit("o crescimento mudou a saída")
    return dif


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--origem")
    ap.add_argument("--destino")
    ap.add_argument("--novos-por-bloco", type=int, default=2)
    ap.add_argument("--contexto", type=int, default=1024)
    ap.add_argument("--conferir", action="store_true")
    a = ap.parse_args()
    if a.conferir:
        conferir()
    else:
        crescer(a.origem, a.destino, a.novos_por_bloco, a.contexto)


if __name__ == "__main__":
    main()
