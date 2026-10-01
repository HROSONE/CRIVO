"""Treino neural reproduzível sem usar a prova independente como treino.

Executar: python scripts/treinar_astronomia.py --saida rede_astronomia_experimental.json
O checkpoint gerado e experimental; não substitui o modelo de produção.
"""
import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from curriculo_mundo import carregar_base
from rede_neural import treinar_base, assinatura_base, assinatura_regras, RedeCrivo


def treinar(saida, epocas=100):
    base = carregar_base(RAIZ / "conhecimento.json")
    destino = Path(saida).resolve()
    if destino == (RAIZ / "rede_crivo.json").resolve():
        raise ValueError("Não substituir o checkpoint de produção sem avaliação independente")
    prova = RAIZ / "avaliacoes" / "astronomia_independente_v1.json"
    if prova.exists():
        perguntas = {q.casefold().strip(" .!?") for item in base for q in item["perguntas"]}
        reservadas = json.loads(prova.read_text(encoding="utf-8"))["casos"]
        colisoes = [c["id"] for c in reservadas if c["pergunta"].casefold().strip(" .!?") in perguntas]
        if colisoes:
            raise ValueError("Contaminação de treino detectada: " + ", ".join(colisoes))
    rede = treinar_base(str(RAIZ / "conhecimento.json"), str(destino),
                        epocas=epocas, ocultos=48, dimensao=512, modo="portugues")
    carregada = RedeCrivo.carregar(destino)
    assert carregada.assinatura_base == assinatura_base(base)
    assert carregada.assinatura_regras == assinatura_regras("portugues")
    return {"arquivo": str(destino), "classes": len(rede.rotulos),
            "epocas": epocas, "dimensao": rede.dimensao,
            "neuronios_ocultos": rede.ocultos, "prova_usada_no_treino": False,
            "estado": "checkpoint experimental, não certificado"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", default="rede_astronomia_experimental.json")
    parser.add_argument("--epocas", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(treinar(args.saida, args.epocas), ensure_ascii=False, indent=2))
