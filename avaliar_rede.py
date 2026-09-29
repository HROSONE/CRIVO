"""Avaliação honesta: treino em frases conhecidas, teste em frases separadas."""
import argparse
import json
from pathlib import Path
from rede_neural import RedeCrivo


def avaliar(base, epocas=80, ocultos=24):
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
    rede = RedeCrivo(rotulos, ocultos=ocultos)
    rede.treinar(treino, epocas=epocas)
    acertos = sum(rede.prever(p)[0] == esperado for p, esperado in teste)
    from rede_neural import caracteristicas
    vetores = [(caracteristicas(p), rotulo) for p, rotulo in treino]
    def baseline(pergunta):
        v = caracteristicas(pergunta)
        return max(vetores, key=lambda item: sum(a*b for a, b in zip(v, item[0])))[1]
    acertos_baseline = sum(baseline(p) == esperado for p, esperado in teste)
    return {"epocas": epocas, "ocultos": ocultos, "acertos": acertos, "total": len(teste),
            "baseline_acertos": acertos_baseline,
            "baseline_precisao": round(acertos_baseline / len(teste), 4),
            "precisao": round(acertos / len(teste), 4),
            "metodo": "ultima pergunta de cada entrada reservada para teste",
            "aviso": "Exemplos da mesma intencao podem compartilhar palavras; nao mede compreensao geral."}


def validacao_cruzada(base, epocas=12, ocultos=24, dimensao=256, semente=42, modo="caracteres"):
    """Cada pergunta e testada uma vez, sempre fora do treino da rodada."""
    from rede_neural import caracteristicas
    rotulos = [e["id"] for e in base]
    n_dobras = max(len(e["perguntas"]) for e in base)
    resultados = []
    for dobra in range(n_dobras):
        treino, teste = [], []
        for e in base:
            perguntas = e["perguntas"]
            if len(perguntas) < 2:
                continue
            indice = dobra if dobra < len(perguntas) else None
            treino.extend((p, e["id"]) for i, p in enumerate(perguntas)
                          if i != indice)
            if indice is not None:
                teste.append((perguntas[indice], e["id"]))
        rede = RedeCrivo(rotulos, dimensao=dimensao, ocultos=ocultos, semente=semente, modo=modo)
        rede.treinar(treino, epocas=epocas, semente=semente)
        acertos = sum(rede.prever(p)[0] == esperado for p, esperado in teste)
        vetores = [(caracteristicas(p, dimensao, modo), rotulo) for p, rotulo in treino]
        def baseline(pergunta):
            v = caracteristicas(pergunta, dimensao, modo)
            return max(vetores, key=lambda item: sum(a*b for a, b in zip(v, item[0])))[1]
        acertos_baseline = sum(baseline(p) == esperado for p, esperado in teste)
        resultados.append({"dobra": dobra + 1, "acertos": acertos,
                           "baseline_acertos": acertos_baseline, "total": len(teste)})
    total = sum(x["total"] for x in resultados)
    acertos = sum(x["acertos"] for x in resultados)
    base_acertos = sum(x["baseline_acertos"] for x in resultados)
    return {"epocas": epocas, "ocultos": ocultos, "dimensao": dimensao, "modo": modo,
            "acertos": acertos, "total": total,
            "precisao": round(acertos / total, 4),
            "baseline_acertos": base_acertos,
            "baseline_precisao": round(base_acertos / total, 4),
            "dobras": resultados,
            "nota": "Rotacao por indice; frases similares entre intencoes ainda podem compartilhar vocabulario."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=str(Path(__file__).with_name("conhecimento.json")))
    parser.add_argument("--epocas", type=int, default=80)
    parser.add_argument("--ocultos", type=int, default=24)
    parser.add_argument("--cruzada", action="store_true")
    parser.add_argument("--dimensao", type=int, default=256)
    parser.add_argument("--modo", choices=("caracteres", "palavras", "misto", "portugues", "portugues_sem_filtro"), default="caracteres")
    args = parser.parse_args()
    dados = json.loads(Path(args.base).read_text(encoding="utf-8"))
    resultado = (validacao_cruzada(dados, args.epocas, args.ocultos, args.dimensao, modo=args.modo)
                 if args.cruzada else avaliar(dados, args.epocas, args.ocultos))
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
