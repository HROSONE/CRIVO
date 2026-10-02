"""Mede a memória do que a pessoa conta: perguntas sobre relatos anteriores.

Cada diálogo passa se todos os turnos cumprirem: "contem" (ao menos um),
"nao_contem" (nenhum) e "nao_fora" (não cair em "não entendi").

Uso: python scripts/avaliar_memoria_relatos.py [dev|retido|todos] [--detalhes]
"""
import json
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA))

from linguagem_conversa import normalizar  # noqa: E402


def conferir(esperado, ident, resposta):
    n = normalizar(resposta)
    if esperado.get("nao_fora") and (ident in ("fora", "duvida") or "Ainda não consegui entender" in resposta):
        return False
    if "contem" in esperado and not any(normalizar(t) in n for t in esperado["contem"]):
        return False
    if any(normalizar(t) in n for t in esperado.get("nao_contem", ())):
        return False
    return True


def avaliar(conjunto):
    from crivo import Crivo
    dados = json.loads((PASTA / "avaliacoes" / "memoria_relatos_v1" / (conjunto + ".json")).read_text(encoding="utf-8"))
    ok, falhas = 0, []
    for d in dados["dialogos"]:
        bot, passou = Crivo(), True
        bot.conversacao.sorteio.seed(20261002)
        for fala, esperado in d["turnos"]:
            ident, resposta = bot.responder(fala)
            if not conferir(esperado, ident, resposta):
                passou = False
                falhas.append({"dialogo": d["nome"], "fala": fala, "id": ident, "resposta": resposta[:200]})
                break
        ok += passou
    return {"conjunto": conjunto, "dialogos": len(dados["dialogos"]), "dialogos_ok": ok}, falhas


def main():
    args = sys.argv[1:]
    alvo = next((a for a in args if a in ("dev", "retido", "retido2", "todos")), "dev")
    for conjunto in (("dev", "retido", "retido2") if alvo == "todos" else (alvo,)):
        resumo, falhas = avaliar(conjunto)
        print(json.dumps(resumo, ensure_ascii=False))
        if "--detalhes" in args:
            for f in falhas:
                print("  [{}] {} -> {} | {}".format(f["dialogo"], f["fala"], f["id"], f["resposta"][:120].replace("\n", " ")))


if __name__ == "__main__":
    main()
