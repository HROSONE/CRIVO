"""Treina as decisões da voz própria com as respostas do tutor.

Para cada resposta de dados/voz_tutor.json:
  1. pergunta ao CRIVO quais fatos ele mostra para aquela pergunta;
  2. monta todas as combinações de abertura, conectivos e fecho da voz;
  3. a combinação mais próxima do tutor (chrF) vira o “oráculo”;
  4. cada ponto de decisão do oráculo vira um exemplo de treino.
Um softmax linear por tipo de decisão aprende a reproduzir as escolhas a
partir de características do texto. 20% dos assuntos ficam para validação.
Aprovação: chrF de validação acima do texto atual e fidelidade total.

Uso: python scripts/treinar_voz.py [--saida artefatos/voz_pt]
"""
import argparse
import itertools
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import voz  # noqa: E402
from scripts.avaliar_voz import chrf  # noqa: E402

DIMENSAO = 4096


def preparar(casos):
    from crivo import Crivo
    exemplos = []
    for caso in casos:
        bot = Crivo()
        bot.usar_voz = False
        _, atual = bot.responder(caso["pergunta"])
        ctx = bot.contexto_textual
        assunto = caso["assuntos"][0]
        if ctx is None or not ctx.exibidos or any(e != assunto for e, _ in ctx.exibidos):
            continue
        item = bot.compositor.itens[assunto]
        mostrados = [i for _, i in ctx.exibidos]
        pontos, _ = voz.pontos_de_decisao(caso["pergunta"], item, mostrados)
        melhor, valor = None, -1
        for escolhas in itertools.product(*[opcoes for _, _, opcoes in pontos]):
            s = chrf(voz.montar(caso["pergunta"], item, mostrados, escolhas), caso["tutor"])
            if s > valor:
                melhor, valor = escolhas, s
        exemplos.append({"caso": caso, "item": item, "mostrados": mostrados, "atual": atual,
                         "pontos": pontos, "oraculo": melhor, "chrf_oraculo": valor})
    return exemplos


def treinar(exemplos, epocas=30, taxa=0.3, l2=1e-4, semente=42):
    rng = random.Random(semente)
    pesos = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    amostras = [(tipo, ctx, opcoes, escolha) for ex in exemplos
                for (tipo, ctx, opcoes), escolha in zip(ex["pontos"], ex["oraculo"]) if len(opcoes) > 1]
    import math
    for _ in range(epocas):
        rng.shuffle(amostras)
        for tipo, ctx, opcoes, escolha in amostras:
            idx = [str(voz._hash(f, DIMENSAO)) for f in voz.caracteristicas(tipo, ctx)] + ["b"]
            pont = [sum(pesos[tipo][o][i] for i in idx) for o in opcoes]
            m = max(pont)
            ex = [math.exp(p - m) for p in pont]
            z = sum(ex)
            for o, e in zip(opcoes, ex):
                grad = e / z - (1.0 if o == escolha else 0.0)
                for i in idx:
                    w = pesos[tipo][o]
                    w[i] -= taxa * (grad + l2 * w[i])
    return {t: {o: {i: round(v, 5) for i, v in w.items() if abs(v) > 1e-5} for o, w in d.items()}
            for t, d in pesos.items()}


class _Decisor:
    def __init__(self, pesos):
        self.ativo = True
        self.dimensao = DIMENSAO
        self.pesos = pesos

    pontuar = voz.ModeloDecisoes.pontuar
    escolher = voz.ModeloDecisoes.escolher


def medir(exemplos, pesos):
    d = _Decisor(pesos)
    soma_voz = soma_atual = acertos = total = fieis = 0
    for ex in exemplos:
        caso = ex["caso"]
        resposta = voz.realizar(caso["pergunta"], ex["item"], ex["mostrados"], decisor=d)
        fieis += resposta is not None
        resposta = resposta or ex["atual"]
        soma_voz += chrf(resposta, caso["tutor"])
        soma_atual += chrf(ex["atual"], caso["tutor"])
        for (tipo, ctx, opcoes), escolha in zip(ex["pontos"], ex["oraculo"]):
            if len(opcoes) > 1:
                total += 1
                acertos += d.escolher(tipo, ctx, opcoes) == escolha
    n = len(exemplos)
    return {"casos": n, "chrf_voz": round(soma_voz / n, 2), "chrf_atual": round(soma_atual / n, 2),
            "chrf_oraculo": round(sum(ex["chrf_oraculo"] for ex in exemplos) / n, 2),
            "decisoes_certas": "%d/%d" % (acertos, total), "fieis": "%d/%d" % (fieis, n)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default=str(RAIZ / "artefatos" / "voz_pt"))
    args = parser.parse_args()
    casos = json.loads((RAIZ / "dados" / "voz_tutor.json").read_text(encoding="utf-8"))["casos"]
    teste = json.loads((RAIZ / "avaliacoes" / "voz_v1" / "teste.json").read_text(encoding="utf-8"))
    proibidos = {a for c in teste["casos"] for a in c["assuntos"]}
    assert not proibidos & {a for c in casos for a in c["assuntos"]}, "tutor e teste congelado se sobrepõem"
    exemplos = preparar(casos)
    rng = random.Random(1005)
    assuntos = sorted({ex["caso"]["assuntos"][0] for ex in exemplos})
    rng.shuffle(assuntos)
    validacao = set(assuntos[:len(assuntos) // 5])
    treino = [ex for ex in exemplos if ex["caso"]["assuntos"][0] not in validacao]
    valid = [ex for ex in exemplos if ex["caso"]["assuntos"][0] in validacao]
    pesos = treinar(treino)
    controle = {"treino": medir(treino, pesos), "validacao": medir(valid, pesos)}
    v = controle["validacao"]
    controle["aprovado"] = v["chrf_voz"] > v["chrf_atual"] and v["fieis"].split("/")[0] == v["fieis"].split("/")[1]
    print(json.dumps(controle, ensure_ascii=False, indent=1))
    # Pesos finais com todos os exemplos do tutor; o controle acima vem da validação separada.
    pesos = treinar(exemplos)
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    meta = {"versao": voz.VERSAO, "dimensao": DIMENSAO, "pesos": pesos, "controle": controle,
            "dados": "dados/voz_tutor.json (%d respostas do tutor)" % len(exemplos)}
    (saida / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
