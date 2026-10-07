"""Geração ancorada v2: o CRIVO escolhe o fato, o gerador só escreve.

A v1 recebia vários fatos e escolhia sozinha qual usar; errava a escolha
("Quem foi Pelé?" -> datas). Aqui a busca aprendida (com o codificador de
sentido) ordena os fatos da ficha para a pergunta e o gerador recebe só o
melhor (ou os dois melhores numa pergunta de duas partes). Mede, nas
perguntas de validação do tutor (fichas fora do treino do gerador):
  - seleção: o fato escolhido está entre os que o tutor usou?
  - geração: a resposta passa na guarda? F1 contra o tutor, antes e depois.

Uso: python experimentos/geracao_ancorada/v2_selecao.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AQUI))

import treinar_geracao_ancorada as tga  # noqa: E402
from geracao_ancorada import GeracaoAncorada, norm  # noqa: E402

DUAS_PARTES = re.compile(r"\be (?:o que|que|qual|quais|quem|quando|onde|como|por que|quant[oa]s?)\b")


def selecionar(busca, pergunta, assunto):
    """Índices dos fatos da ficha que a busca põe no topo para a pergunta."""
    achados = busca.buscar(pergunta, k=3, assuntos=[assunto])
    if not achados:
        return []
    escolhidos = [achados[0][2]]
    if DUAS_PARTES.search(norm(pergunta)) and len(achados) > 1 and achados[1][0] >= 0.5 * achados[0][0]:
        escolhidos.append(achados[1][2])
    return escolhidos


def main():
    from crivo import Crivo
    from curriculo_mundo import texto_fato
    from leitura_ficha import busca_aprendida
    g = GeracaoAncorada(AQUI / "pesos", exigir_aprovacao=False)
    base = Crivo()
    comp = base.compositor
    busca = busca_aprendida(comp)
    ex = tga.carregar(str(AQUI / "dados"), comp)
    val = [e for e in ex if int(hashlib.sha256(e["id"].encode()).hexdigest()[:4], 16) % 20 == 0]
    r = {"n": len(val), "selecao_certa": 0, "gerou": 0, "f1_antes": 0.0, "f1_depois": 0.0}
    linhas = []
    for e in val:
        bot = Crivo()
        _, antes = bot.responder(e["pergunta"])
        idx = selecionar(busca, e["pergunta"], e["id"])
        certa = bool(idx) and idx[0] in e["citados"]
        r["selecao_certa"] += certa
        fatos = [texto_fato(comp.itens[e["id"]]["fatos"][i]) for i in idx]
        escrita = g.gerar(e["pergunta"], fatos) if fatos else None
        depois = escrita or antes
        r["gerou"] += escrita is not None
        r["f1_antes"] += tga.f1(antes, e["resposta"])
        r["f1_depois"] += tga.f1(depois, e["resposta"])
        prob = busca.buscar(e["pergunta"], k=1, assuntos=[e["id"]])
        linhas.append({"prob": round(prob[0][0], 3) if prob else 0.0, "pergunta": e["pergunta"], "selecao_certa": certa, "antes": antes[:300],
                       "gerado": escrita, "tutor": e["resposta"]})
    for k in ("f1_antes", "f1_depois"):
        r[k] = round(r[k] / r["n"], 3)
    print(json.dumps(r, ensure_ascii=False))
    (AQUI / "v2_resultado.json").write_text(json.dumps({"resumo": r, "linhas": linhas}, ensure_ascii=False, indent=1),
                                            encoding="utf-8")


if __name__ == "__main__":
    main()
