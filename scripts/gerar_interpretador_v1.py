"""Gera avaliacoes/interpretador_v1/{dev,retido}.json: conceitos x formas de
perguntar. Dev e retido usam FORMAS e CONCEITOS diferentes; o retido mede se o
interpretador generaliza para jeitos de perguntar que não guiaram o ajuste."""
import json
import random
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

DEV_CONCEITOS = ["entropia", "seleção natural", "anomia", "utilitarismo", "ansiedade", "fotossíntese",
                 "luto", "relatividade geral", "epigenética", "habitus", "existencialismo", "matéria escura",
                 "supernova", "meiose", "imperativo categórico", "estresse", "neuroplasticidade", "cogito",
                 "CRISPR", "falseabilidade"]
RETIDO_CONCEITOS = ["fusão nuclear", "deriva genética", "hegemonia", "fenomenologia", "melatonina",
                    "energia escura", "mitocôndria", "capital cultural", "estoicismo", "spin",
                    "procrastinação", "biodiversidade"]

DEV_FORMAS = ["oq é {x}", "o q e {x}", "explica {x} pra mim", "fala um pouco de {x}", "qual o conceito de {x}?",
              "tenho uma dúvida sobre {x}", "me dá um resumo sobre {x}", "como funciona {x}?",
              "to estudando {x}, me ajuda", "o que é {t}?", "O que é {x}?", "me explica {x}",
              "{x}?", "queria saber sobre {x}", "o que significa {x}?", "definição de {x}"]
RETIDO_FORMAS = ["vc sabe me dizer o que é {x}?", "explica ai {x}", "nao entendi nada de {x}, socorro",
                 "alguém me explica {x} de um jeito simples", "o que é isso de {x}?", "me fala sobre {x}",
                 "qual é a ideia de {x}?", "preciso entender {x} pra prova", "{x} é o quê exatamente?",
                 "pode explicar {t}?", "como assim {x}?", "o que quer dizer {x}?"]

CONTROLES = [  # não são pedidos de explicação: não podem virar aula
    {"fala": "estou com ansiedade hoje", "nao_e_definicao": True},
    {"fala": "to muito estressado com o trabalho", "nao_e_definicao": True},
    {"fala": "perdi minha avó, estou de luto", "nao_e_definicao": True},
    {"fala": "não consigo parar de procrastinar", "nao_e_definicao": True},
    {"fala": "oi, tudo bem?", "nao_e_definicao": True},
    {"fala": "meu gato derrubou um copo", "nao_e_definicao": True},
    {"fala": "hoje estudei fotossíntese e gostei muito", "nao_e_definicao": True},
    {"fala": "Morcego é ave?", "nao_e_definicao": True},
]


def erro_digitacao(nome):
    letras = [i for i, c in enumerate(nome) if c.isalpha()]
    if len(letras) < 6:
        return nome
    i = letras[len(letras) // 2]
    return nome[:i] + nome[i + 1:]


def casos(conceitos, formas):
    saida = []
    for nome in conceitos:
        for forma in formas:
            saida.append({"conceito": nome, "fala": forma.format(x=nome, t=erro_digitacao(nome))})
    return saida


def main():
    pasta = RAIZ / "avaliacoes" / "interpretador_v1"
    pasta.mkdir(parents=True, exist_ok=True)
    dev = {"descricao": "Desenvolvimento: guia o ajuste. Cada caso exige a definição do conceito na resposta; "
                        "controles não podem receber definição.",
           "casos": casos(DEV_CONCEITOS, DEV_FORMAS) + CONTROLES[:5]}
    retido = {"descricao": "Retido: formas e conceitos fora do dev. Só o agregado é mostrado.",
              "casos": casos(RETIDO_CONCEITOS, RETIDO_FORMAS) + CONTROLES[5:]}
    for nome, dados in (("dev", dev), ("retido", retido)):
        (pasta / (nome + ".json")).write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(nome, len(dados["casos"]))


if __name__ == "__main__":
    main()
