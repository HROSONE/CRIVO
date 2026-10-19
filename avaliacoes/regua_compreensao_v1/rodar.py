"""Régua de compreensão v1: roda os casos no chat (web_core) e confere a resposta.

Uso: python avaliacoes/regua_compreensao_v1/rodar.py [saida.json]
Não entra em nenhum dado de treino. Cada caso passa se:
- contem: todos os trechos aparecem na resposta;
- contem_algum: pelo menos um trecho aparece;
- nao_contem: nenhum trecho aparece.
Comparação sem acento e sem maiúsculas.
"""
import json
import sys
import time
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import web_core  # noqa: E402

import os  # noqa: E402
CASOS = Path(os.environ.get("REGUA_CASOS", Path(__file__).with_name("casos.json")))


def norm(texto):
    t = unicodedata.normalize("NFD", (texto or "").casefold())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def conferir(caso, resposta):
    r = norm(resposta)
    falhas = []
    for trecho in caso.get("contem", []):
        if norm(trecho) not in r:
            falhas.append(f"faltou '{trecho}'")
    algum = caso.get("contem_algum")
    if algum and not any(norm(t) in r for t in algum):
        falhas.append(f"faltou um de {algum}")
    for trecho in caso.get("nao_contem", []):
        if norm(trecho) in r:
            falhas.append(f"apareceu '{trecho}'")
    return not falhas, falhas


def principal(saida):
    casos = json.loads(CASOS.read_text(encoding="utf-8"))["casos"]
    resultados = []
    for c in casos:
        t = time.perf_counter()
        resp = web_core.responder_web({"message": c["pergunta"], "history": c.get("historico", [])},
                                      usar_geracao=True, voz_17m=True)["response"]
        ok, falhas = conferir(c, resp)
        resultados.append({"id": c["id"], "cat": c["cat"], "origem": c["origem"], "pergunta": c["pergunta"],
                           "resposta": resp, "passou": ok, "falhas": falhas, "segundos": round(time.perf_counter() - t, 2)})
        print(("OK  " if ok else "FALHA"), c["id"], c["pergunta"], "" if ok else falhas, flush=True)
    total = len(resultados)
    passou = sum(r["passou"] for r in resultados)
    por_cat = {}
    for r in resultados:
        p = por_cat.setdefault(r["cat"], [0, 0])
        p[0] += r["passou"]
        p[1] += 1
    resumo = {"total": total, "passou": passou, "por_categoria": {k: f"{a}/{b}" for k, (a, b) in por_cat.items()},
              "so_do_usuario": f"{sum(r['passou'] for r in resultados if r['origem']=='do_usuario')}/{sum(r['origem']=='do_usuario' for r in resultados)}"}
    print("RESUMO", json.dumps(resumo, ensure_ascii=False), flush=True)
    Path(saida).write_text(json.dumps({"resumo": resumo, "resultados": resultados}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("FIM", flush=True)


if __name__ == "__main__":
    principal(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).with_name("resultado_base.json")))
