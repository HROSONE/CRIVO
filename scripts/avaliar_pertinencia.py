"""Mede a pertinência da reação a um relato: o comentário de senso comum
combina com o que aconteceu, a pergunta vai para quem viveu o fato e o eco
está na voz de "você".

Cada caso é uma fala isolada numa conversa nova. Além das marcas de cada
caso ("nao_contem", "contem_algum"), confere em todos:
  pessoa_errada  o fato é de outra pessoa ("meu avô plantou…") e a pergunta
                 final pergunta sobre "você" (fora as de acolhimento);
  primeira_vazou um verbo ou possessivo de primeira pessoa da fala aparece
                 igual na resposta ("Que bom, comi pizza ontem!").

Uso: python scripts/avaliar_pertinencia.py [dev|retido|todos] [--detalhes]
(--detalhes só mostra os casos do dev; o retido fica só no agregado.)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA))

from linguagem_conversa import normalizar  # noqa: E402

# Fala sobre outra pessoa: "meu avô…", "minha prima…", "o vizinho…".
_OUTRA_PESSOA = re.compile(
    r"^(?:(?:meu|minha|o|a) )?(?:pai|mae|avo|avoa|irmao|irma|filho|filha|primo|prima|tio|tia|sobrinho|"
    r"sobrinha|vizinho|vizinha|chefe|amigo|amiga|namorado|namorada|marido|esposa|esposo)\b")
# Perguntas sobre "você" que continuam pertinentes quando o fato é de outra pessoa.
_ACOLHIMENTO = re.compile(r"\b(?:como voce esta|e voce, como|voce esta lidando|como voce ta|"
                          r"me conta como estao|voce esta em seguranca)\b")
_PRIMEIRA = re.compile(r"\b(?:eu|meu|minha|meus|minhas|\w{2,}ei|comi|bebi|fiz|fui|vi|perdi|dormi|corri|"
                       r"assisti|li|tive)\b")


def pergunta_final(resposta):
    perguntas = [f for f in re.split(r"(?<=[.!?])\s+", resposta.strip()) if f.endswith("?")]
    return perguntas[-1] if perguntas else ""


def conferir(caso, resposta):
    """Lista de motivos de falha (vazia se o caso passou)."""
    n = normalizar(resposta)
    motivos = []
    for t in caso.get("nao_contem", ()):
        if normalizar(t) in n:
            motivos.append("contém: " + t)
    if caso.get("contem_algum") and not any(normalizar(t) in n for t in caso["contem_algum"]):
        motivos.append("falta: " + " | ".join(caso["contem_algum"]))
    fala = normalizar(caso["fala"])
    if _OUTRA_PESSOA.match(fala):
        p = normalizar(pergunta_final(resposta))
        if re.search(r"\bvoce\b", p) and not _ACOLHIMENTO.search(p):
            motivos.append("pessoa_errada: " + pergunta_final(resposta))
    vazadas = {w for w in _PRIMEIRA.findall(fala)} & set(re.findall(r"[a-z]+", n))
    if vazadas:
        motivos.append("primeira_vazou: " + ", ".join(sorted(vazadas)))
    return motivos


def avaliar(conjunto):
    from crivo import Crivo
    dados = json.loads((PASTA / "avaliacoes" / "pertinencia_v1" / (conjunto + ".json")).read_text(encoding="utf-8"))
    ok, tipos, detalhes = 0, Counter(), []
    for caso in dados["casos"]:
        bot = Crivo()
        bot.conversacao.sorteio.seed(20261003)
        _, resposta = bot.responder(caso["fala"])
        motivos = conferir(caso, resposta)
        ok += not motivos
        for m in motivos:
            tipos[m.split(":")[0]] += 1
        detalhes.append((caso["fala"], resposta, motivos))
    return {"conjunto": conjunto, "casos": len(dados["casos"]), "acertos": ok,
            "falhas_por_tipo": dict(sorted(tipos.items()))}, detalhes


def main():
    args = sys.argv[1:]
    alvo = next((a for a in args if a in ("dev", "retido", "todos")), "dev")
    for conjunto in (("dev", "retido") if alvo == "todos" else (alvo,)):
        resumo, detalhes = avaliar(conjunto)
        print(json.dumps(resumo, ensure_ascii=False))
        if "--detalhes" in args and conjunto == "dev":
            for fala, resposta, motivos in detalhes:
                print(("  ok   " if not motivos else "  FALHA ") + fala)
                print("        " + resposta.replace("\n", " / "))
                for m in motivos:
                    print("        - " + m)


if __name__ == "__main__":
    main()
