"""Compara o CRIVO completo com/sem geração; congelados só em agregados.

Os classificadores originais continuam intactos, inclusive os que exigem
cópia literal. Uma reescrita pode falhar nesse critério; a contagem não é
convertida automaticamente em acerto pelo fato de a fonte ter sido selecionada.

OPENBLAS_NUM_THREADS=1 python scripts/avaliar_geracao_ancorada.py --saida resultado.json
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ), str(RAIZ / "scripts")]


def tarefas():
    import avaliar_busca_sem_nome as sem_nome
    import avaliar_leitura_ficha as leitura
    import avaliar_bateria as bateria
    import avaliar_lacunas as lacunas
    def medir_lacunas(conjunto):
        r = lacunas.avaliar(conjunto, detalhes=True)
        return {k: r[k] for k in ("casos", "certo", "recusou", "errado", "por_area")}
    return (
        [("sem_nome_" + c, lambda c=c: sem_nome.avaliar(c)) for c in ("dev", "teste")]
        + [("leitura_" + c, lambda c=c: leitura.avaliar(c)[0]) for c in ("teste", "teste_v2")]
        + [("bateria_" + c, lambda c=c: bateria.avaliar(c)[0]) for c in ("dev", "retido")]
        + [("lacunas_" + c, lambda c=c: medir_lacunas(c)) for c in ("dev", "teste")]
    )


def medir(ligada, alvos=None, publicar=None):
    import crivo
    original = crivo.Crivo
    usos, motivos, rejeicoes, modos = Counter(), Counter(), Counter(), Counter()

    class Medido(original):
        def __init__(self, *args, **kwargs):
            kwargs["usar_geracao"] = ligada
            super().__init__(*args, **kwargs)

        def responder(self, texto):
            ident, resposta = super().responder(texto)
            trace = self.ultima_geracao or {}
            usos["turnos"] += 1
            usos["gerados"] += bool(trace.get("usada"))
            usos["tentativas"] += trace.get("tentativas", 0)
            usos["alterados"] += bool(trace.get("texto_alterado"))
            usos["copias_literais"] += bool(trace.get("copia_literal"))
            motivos[trace.get("motivo", "sem_diagnostico")] += 1
            rejeicoes.update(trace.get("rejeicoes", ()))
            if trace.get("usada"):
                modos[trace.get("modo", "factual")] += 1
            return ident, resposta

    crivo.Crivo = Medido
    resultado = {}
    try:
        for nome, avaliar in tarefas():
            if alvos and nome not in alvos:
                continue
            for c in (usos, motivos, rejeicoes, modos):
                c.clear()
            inicio = time.monotonic()
            qualidade = avaliar()
            resultado[nome] = {"qualidade": qualidade, "uso": dict(usos),
                               "motivos": dict(motivos), "rejeicoes": dict(rejeicoes),
                               "modos": dict(modos), "segundos": round(time.monotonic() - inicio, 2)}
            if publicar is not None:
                publicar(resultado)
            print(json.dumps({"modo": "com" if ligada else "sem", "avaliacao": nome,
                              **resultado[nome]}, ensure_ascii=False), flush=True)
    finally:
        crivo.Crivo = original
    return resultado


BONS = {"certo", "afirmou_certo", "aproximou_certo", "acertos_fato", "recusas_corretas",
        "dialogos_ok", "calou_bem"}
RUINS = {"errado", "afirmou_errado", "afirmou", "inventou", "assunto_errado"}


def regressoes(antes, depois):
    """Compara classes/áreas, nunca perguntas dos conjuntos congelados."""
    saida = []

    def comparar(nome, a, b, prefixo=""):
        for k in a.keys() | b.keys():
            x, y = a.get(k, 0), b.get(k, 0)
            if isinstance(x, dict) and isinstance(y, dict):
                comparar(nome, x, y, prefixo + k + ".")
            elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
                if (k in BONS and y < x) or (k in RUINS and y > x):
                    saida.append({"avaliacao": nome, "classe": prefixo + k, "sem": x, "com": y})
    for nome in antes.keys() & depois.keys():
        comparar(nome, antes[nome]["qualidade"], depois[nome]["qualidade"])
    return saida


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modo", choices=("com", "sem", "ambos"), default="ambos")
    parser.add_argument("--avaliacoes", nargs="+", help="Nomes dos agregados a medir")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    resultado = {"versao": 1, "classificadores": "originais", "congelados": "somente agregados"}
    args.saida.parent.mkdir(parents=True, exist_ok=True)

    def salvar():
        args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    for modo in (("sem", "com") if args.modo == "ambos" else (args.modo,)):
        def publicar(parcial):
            resultado[modo] = parcial
            salvar()
        resultado[modo] = medir(modo == "com", args.avaliacoes, publicar)
        salvar()
    if "sem" in resultado and "com" in resultado:
        resultado["regressoes"] = regressoes(resultado["sem"], resultado["com"])
        resultado["aprovado"] = not resultado["regressoes"]
        salvar()
        if not resultado["aprovado"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
