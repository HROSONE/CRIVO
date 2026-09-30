"""Treina pesos próprios em operações e spans; nunca lê o benchmark final."""
import argparse
import json
from collections import Counter
from pathlib import Path

from rede_sequencial import (RedeSequencial, atributos_frase, atributos_token,
                            palavras, assinatura, VERSAO_ATRIBUTOS, token_estrutura, FLEXOES, assinatura_atributos)
from linguagem_neural import LinguagemNeural


def exemplos_tags(caso, dimensao, estruturais):
    ts = palavras(caso["texto"])
    nomes = [token_estrutura(t, estruturais) for t, _, _ in ts]
    resultado = []
    for i, (_, a, b) in enumerate(ts):
        tag = "O"
        for nome, (inicio, fim) in caso["spans"].items():
            if inicio <= a and b <= fim:
                tag = ("B" if a == inicio else "I") + ("1" if nome == "alvo" else "2")
        resultado.append((atributos_token(nomes, i, dimensao), tag))
    return resultado


def avaliar_quadros(rede, casos):
    corretos = atos = spans = negacoes = 0
    por_ato = {}
    for c in casos:
        q = rede.analisar(c["texto"])
        ato_ok = q is not None and q.ato == c["ato"]
        spans_ok = q is not None and {n: [a, b] for n, a, b in q.spans} == c["spans"]
        neg_ok = q is not None and q.negacao_pedido == (c["ato"] == "negado")
        atos += ato_ok
        spans += spans_ok
        negacoes += neg_ok
        corretos += ato_ok and spans_ok and neg_ok
        p = por_ato.setdefault(c["ato"], {"total": 0, "atos": 0, "quadros": 0})
        p["total"] += 1; p["atos"] += ato_ok; p["quadros"] += ato_ok and spans_ok and neg_ok
    return dict(total=len(casos), atos_corretos=atos, spans_corretos=spans,
                negacoes_corretas=negacoes, quadros_corretos=corretos, por_ato=por_ato)


def treinar(caminho, destino, epocas=70, semente=42, acelerar=False):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    treino = [c for c in dados["exemplos"] if c["split"] == "treino"]
    validacao = [c for c in dados["exemplos"] if c["split"] == "validacao"]
    if {c["familia"] for c in treino} & {c["familia"] for c in validacao}:
        raise ValueError("Famílias misturadas")
    if any(c["split"] not in ("treino", "validacao") for c in dados["exemplos"]):
        raise ValueError("Treino não pode receber teste final")
    rotulos = sorted({c["ato"] for c in treino})
    estruturais = {t for c in treino if c["ato"] != "outro"
                  for t, a, b in palavras(c["texto"])
                  if not any(inicio <= a and b <= fim for inicio, fim in c["spans"].values())}
    estruturais.update(FLEXOES)
    estruturais = frozenset(estruturais)
    ordem = RedeSequencial(rotulos, semente=semente)
    ordem.treinar([(atributos_frase(c["texto"], estruturais=estruturais), c["ato"]) for c in treino],
                 epocas=epocas, semente=semente, acelerar=acelerar)
    sem_ordem = RedeSequencial(rotulos, semente=semente)
    sem_ordem.treinar([(atributos_frase(c["texto"], ordem=False, estruturais=estruturais), c["ato"]) for c in treino],
                     epocas=epocas, semente=semente, acelerar=acelerar)
    tags = RedeSequencial(["O", "B1", "I1", "B2", "I2"], semente=semente)
    tags.treinar([e for c in treino for e in exemplos_tags(c, tags.dimensao, estruturais)],
                 epocas=max(25, epocas//2), semente=semente, acelerar=acelerar)
    checkpoint = dict(versao=1, atributos=VERSAO_ATRIBUTOS, assinatura_atributos=assinatura_atributos(),
                      atos=ordem.dados(), tags=tags.dados(),
                      estruturais=sorted(estruturais), limiar=.80, assinatura_treino=assinatura(treino),
                      metodo="Pesos próprios; MLP com atributos de sequência local e tagger por posição.",
                      treino=dict(semente=semente, epocas=epocas, exemplos=len(treino),
                                  familias=len({c["familia"] for c in treino}),
                                  acelerador="numpy" if acelerar else "python"))
    rede = LinguagemNeural(checkpoint)
    relatorio = dict(semente=semente, epocas=epocas, assinatura_treino=assinatura(treino),
                     treino=avaliar_quadros(rede, treino), validacao=avaliar_quadros(rede, validacao),
                     comparacao_ato_sem_ordem=dict(total=len(validacao), acertos=sum(
                         sem_ordem.prever(atributos_frase(c["texto"], ordem=False, estruturais=estruturais))[0] == c["ato"]
                         for c in validacao)),
                     limite="Validação autoral por famílias e alvos diferentes; não comprova compreensão universal. A comparação sem ordem usa as mesmas famílias, rótulos, arquitetura, épocas e semente.")
    Path(destino).write_text(json.dumps(checkpoint, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return relatorio


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dados", default="curriculo_linguagem_neural.json")
    p.add_argument("--saida", default="rede_linguagem.json")
    p.add_argument("--relatorio", default="avaliacao_linguagem_neural.json")
    p.add_argument("--epocas", type=int, default=70)
    p.add_argument("--semente", type=int, default=42)
    p.add_argument("--numpy", action="store_true")
    a = p.parse_args()
    resultado = treinar(a.dados, a.saida, a.epocas, a.semente, a.numpy)
    Path(a.relatorio).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
