"""Léxico curado de sinônimos e antônimos do português (autoria do projeto).

Usado pela busca factual para aceitar UMA palavra da pergunta escrita com
outro termo de mesmo sentido ("ventos fortes" / "ventos intensos") e para
nunca aproximar termos opostos ("quente" / "frio"). Relações só existem
quando listadas; nada é inferido por semelhança.
"""
import json
from pathlib import Path

CAMINHO = Path(__file__).resolve().parent / "dados" / "lexico_sinonimos_antonimos_pt.json"


def flexoes(classe, palavra):
    formas = {palavra}
    if classe == "adj":
        if palavra.endswith("o"):
            formas |= {palavra[:-1] + "a", palavra + "s", palavra[:-1] + "as"}
        elif palavra.endswith(("e", "a")):
            formas.add(palavra + "s")
        elif palavra.endswith(("z", "r")):
            formas.add(palavra + "es")
        elif palavra.endswith("l"):
            formas.add(palavra[:-1] + "is")
    elif classe == "nome":
        if palavra.endswith(("a", "e", "o")):
            formas.add(palavra + "s")
        elif palavra.endswith(("r", "z")):
            formas.add(palavra + "es")
    elif classe == "verbo" and palavra.endswith(("ar", "er", "ir")):
        raiz, vogal = palavra[:-2], palavra[-2]
        terceira = raiz + ("a" if vogal == "a" else "e")
        formas |= {terceira, terceira + "m", raiz + ("ado" if vogal == "a" else "ido")}
    return formas


class LexicoPT:
    def __init__(self, caminho=CAMINHO):
        self.sinonimos, self.antonimos = {}, {}
        try:
            dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        for parte in ("treino", "reservados"):
            for chave, destino in (("sinonimos", self.sinonimos), ("antonimos", self.antonimos)):
                for classe, a, b in dados.get(parte, {}).get(chave, []):
                    fa, fb = flexoes(classe, a), flexoes(classe, b)
                    for x in fa:
                        destino.setdefault(x, set()).update(fb)
                    for y in fb:
                        destino.setdefault(y, set()).update(fa)

    def sinonimo(self, a, b):
        return b in self.sinonimos.get(a, ())

    def antonimo(self, a, b):
        return b in self.antonimos.get(a, ())
