"""Mede dois erros encontrados conversando com o CRIVO:

  assunto  a resposta trata de outro tema porque uma palavra coincide
           ("Por que o céu é azul?" -> cores da reciclagem);
  tom      a reação a um relato tem o tom errado ou troca a pessoa
           ("Perdi minha avó" -> "Que chato").

Os controles são perguntas que devem continuar respondidas. Cada caso começa
numa conversa nova; "historico" são as falas anteriores do usuário.

Uso: python scripts/avaliar_assunto_tom.py [dev|retido|todos] [--detalhes]
(--detalhes só mostra os casos do dev; o retido fica só no agregado.)
"""
import json
import sys
from collections import Counter
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA))

from linguagem_conversa import normalizar  # noqa: E402


def conferir(caso, resposta):
    """Lista de motivos de falha (vazia se o caso passou)."""
    n = normalizar(resposta)
    motivos = []
    for t in caso.get("nao_contem", ()):
        if normalizar(t) in n:
            motivos.append("contém: " + t)
    if caso.get("contem_algum") and not any(normalizar(t) in n for t in caso["contem_algum"]):
        motivos.append("falta: " + " | ".join(caso["contem_algum"]))
    return motivos


def avaliar(conjunto):
    from crivo import Crivo
    dados = json.loads((PASTA / "avaliacoes" / "assunto_tom_v1" / (conjunto + ".json")).read_text(encoding="utf-8"))
    ok, por_tipo, detalhes = 0, Counter(), []
    falhas_tipo = Counter()
    for caso in dados["casos"]:
        bot = Crivo()
        bot.conversacao.sorteio.seed(20261004)
        for anterior in caso.get("historico", ()):
            bot.responder(anterior)
        _, resposta = bot.responder(caso["fala"])
        motivos = conferir(caso, resposta)
        ok += not motivos
        por_tipo[caso["tipo"]] += 1
        if motivos:
            falhas_tipo[caso["tipo"]] += 1
        detalhes.append((caso, resposta, motivos))
    acertos_tipo = {t: por_tipo[t] - falhas_tipo[t] for t in sorted(por_tipo)}
    return {"conjunto": conjunto, "casos": len(dados["casos"]), "acertos": ok,
            "acertos_por_tipo": {t: "%d/%d" % (acertos_tipo[t], por_tipo[t]) for t in acertos_tipo}}, detalhes


def main():
    args = sys.argv[1:]
    alvo = next((a for a in args if a in ("dev", "retido", "todos")), "dev")
    for conjunto in (("dev", "retido") if alvo == "todos" else (alvo,)):
        resumo, detalhes = avaliar(conjunto)
        print(json.dumps(resumo, ensure_ascii=False))
        if "--detalhes" in args and conjunto == "dev":
            for caso, resposta, motivos in detalhes:
                print(("  ok    " if not motivos else "  FALHA ") + "[" + caso["tipo"] + "] " + caso["fala"])
                print("        " + resposta.replace("\n", " / ")[:220])
                for m in motivos:
                    print("        - " + m)


if __name__ == "__main__":
    main()
