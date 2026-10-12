"""Congela as âncoras de preservação do v5 antes de qualquer treino.

As âncoras são mensagens de usuário do próprio CRIVO (split de treino de
curriculo_dialogo.json e curriculo_linguagem_neural.json). No notebook, a base
congelada gera a própria continuação para cada uma, e a cabeça é treinada para
reproduzir a distribuição da base nessas continuações (KL base → cabeça).
perguntas_externas.json não é usado: o arquivo proíbe uso em treino.
"""
import hashlib
import json
import random
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
SEED = 20261012
PRESERVACAO_FIXA = {  # as 12 perguntas da checagem final ficam fora das âncoras
    "Explique em uma frase o que é gravidade.", "Qual é a função de uma cadeira?",
    "O que significa memória?", "Diga uma característica da água.", "O que é uma estrela?",
    "Qual é a função de um recipiente?", "Explique o que é temperatura.",
    "O que significa aprender?", "Diga uma função de uma ferramenta.", "O que é uma hipótese?",
    "Explique o que é energia.", "Qual é a diferença entre fato e opinião?",
}


def main():
    textos = []
    for nome in ("curriculo_dialogo.json", "curriculo_linguagem_neural.json"):
        for ex in json.loads((RAIZ / nome).read_text(encoding="utf-8"))["exemplos"]:
            if ex.get("split") == "treino" and isinstance(ex.get("texto"), str):
                textos.append(ex["texto"].strip())
    vistos, pool = set(), []
    for t in textos:
        k = t.casefold()
        if k in vistos or not (8 <= len(t) <= 160) or t in PRESERVACAO_FIXA or "objeto inventado" in k:
            continue
        vistos.add(k)
        pool.append(t)
    rr = random.Random(SEED + 7007)
    rr.shuffle(pool)
    ancoras = {"descricao": __doc__.strip().splitlines()[0],
               "treino": pool[:800], "dev": pool[800:848]}
    caminho = AQUI / "ancoras_v5.json"
    caminho.write_text(json.dumps(ancoras, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("pool:", len(pool), "| treino:", len(ancoras["treino"]), "| dev:", len(ancoras["dev"]))
    print("sha256:", hashlib.sha256(caminho.read_bytes()).hexdigest())
    print("exemplos:", ancoras["treino"][:8])


if __name__ == "__main__":
    main()
