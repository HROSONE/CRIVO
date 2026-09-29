"""Avaliação honesta: treino em frases conhecidas, teste em frases separadas."""
import argparse
import json
from pathlib import Path
from rede_neural import RedeCrivo


def avaliar(base, epocas=80):
    rotulos = [e["id"] for e in base]
    treino, teste = [], []
    for entrada in base:
        perguntas = entrada["perguntas"]
        if len(perguntas) < 2:
            continue
        treino.extend((p, entrada["id"]) for p in perguntas[:-1])
        teste.append((perguntas[-1], entrada["id"]))
    if not teste:
        raise ValueError("Nao ha exemplos suficientes para avaliacao")
    rede = RedeCrivo(rotulos)
    rede.treinar(treino, epocas=epocas)
    acertos = sum(rede.prever(p)[0] == esperado for p, esperado in teste)
    return {"acertos": acertos, "total": len(teste),
            "precisao": round(acertos / len(teste), 4),
            "metodo": "ultima pergunta de cada entrada reservada para teste",
            "aviso": "Exemplos da mesma intencao podem compartilhar palavras; nao mede compreensao geral."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=str(Path(__file__).with_name("conhecimento.json")))
    parser.add_argument("--epocas", type=int, default=80)
    args = parser.parse_args()
    dados = json.loads(Path(args.base).read_text(encoding="utf-8"))
    print(json.dumps(avaliar(dados, args.epocas), ensure_ascii=False, indent=2))
