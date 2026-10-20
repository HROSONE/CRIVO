"""Régua de compreensão: roda os casos no chat (web_core) e confere a resposta.

Uso: python avaliacoes/regua_compreensao_v1/rodar.py [saida.json]
Variável REGUA_CASOS escolhe outro arquivo de casos.
Não entra em nenhum dado de treino. Cada caso passa se:
- contem: todos os trechos aparecem na resposta;
- contem_algum: pelo menos um trecho aparece;
- nao_contem: nenhum trecho aparece.
Comparação sem acento e sem maiúsculas.
Um caso sem nenhuma regra aparece como "sem regra" e não conta como aprovado.
"""
import json
import os
import sys
import time
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import web_core  # noqa: E402

CASOS = Path(os.environ.get("REGUA_CASOS", Path(__file__).with_name("casos.json")))


def norm(texto):
    t = unicodedata.normalize("NFD", (texto or "").casefold())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def tem_regra(caso):
    return bool(caso.get("contem") or caso.get("contem_algum") or caso.get("nao_contem"))


def conferir(caso, resposta):
    if not tem_regra(caso):
        return None, ["sem regra"]
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
        estado = "SEM " if ok is None else ("OK  " if ok else "FALHA")
        print(estado, c["id"], c["pergunta"], "" if ok else falhas, flush=True)
    com_regra = [r for r in resultados if r["passou"] is not None]
    por_cat = {}
    for r in com_regra:
        p = por_cat.setdefault(r["cat"], [0, 0])
        p[0] += r["passou"]
        p[1] += 1
    resumo = {"total": len(resultados), "com_regra": len(com_regra), "passou": sum(r["passou"] for r in com_regra),
              "por_categoria": {k: f"{a}/{b}" for k, (a, b) in por_cat.items()}}
    print("RESUMO", json.dumps(resumo, ensure_ascii=False), flush=True)
    Path(saida).write_text(json.dumps({"resumo": resumo, "resultados": resultados}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("FIM", flush=True)


if __name__ == "__main__":
    principal(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).with_name("resultado_base.json")))
