"""Conversas reais de vários turnos: refaz cada conversa no chat (web_core), turno a turno.

Uso: python avaliacoes/conversas_reais_v1/rodar.py [saida.json] [--papel dev|teste]
Cada turno recebe o histórico das mensagens anteriores da pessoa, como o site manda.
Não entra em nenhum dado de treino. Um turno passa se cumpre todas as suas regras
(veja "regras" em conversas.json); um turno sem regra não conta.
"""
import json
import sys
import time
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import web_core  # noqa: E402

CASOS = Path(__file__).with_name("conversas.json")


def norm(texto):
    t = unicodedata.normalize("NFD", (texto or "").casefold())
    return " ".join("".join(c for c in t if unicodedata.category(c) != "Mn").split())


def conferir(turno, resposta):
    regras = ("contem", "contem_algum", "nao_contem", "comeca_com_algum")
    if not any(turno.get(r) for r in regras):
        return None, ["sem regra"]
    r = norm(resposta)
    falhas = [f"faltou '{t}'" for t in turno.get("contem", []) if norm(t) not in r]
    algum = turno.get("contem_algum")
    if algum and not any(norm(t) in r for t in algum):
        falhas.append(f"faltou um de {algum}")
    falhas += [f"apareceu '{t}'" for t in turno.get("nao_contem", []) if norm(t) in r]
    comeco = turno.get("comeca_com_algum")
    if comeco and not any(r.lstrip("\"'“ ").startswith(norm(t)) for t in comeco):
        falhas.append(f"não começou com um de {comeco}")
    return not falhas, falhas


def refazer(conversa):
    falas = [t["usuario"] for t in conversa["turnos"]]
    saida = []
    for k, turno in enumerate(conversa["turnos"]):
        t0 = time.perf_counter()
        r = web_core.responder_web({"message": falas[k], "history": falas[:k]}, usar_geracao=True, voz_17m=True)
        ok, falhas = conferir(turno, r["response"])
        voz = r.get("conversation_voice") or {}
        saida.append({"turno": k + 1, "usuario": falas[k], "resposta": r["response"], "passou": ok,
                      "falhas": falhas, "mecanismo": r.get("mechanism") or r.get("mecanismo"),
                      "id": r.get("id"), "voz_usada": voz.get("used"), "motivo_voz": voz.get("reason"),
                      "segundos": round(time.perf_counter() - t0, 2)})
        print("OK   " if ok else ("SEM  " if ok is None else "FALHA"), conversa["id"], k + 1, falas[k],
              "->", r["response"][:120].replace("\n", " "), "" if ok else falhas, flush=True)
    return saida


def principal(argv):
    papel = argv[argv.index("--papel") + 1] if "--papel" in argv else None
    args = [a for i, a in enumerate(argv) if a != "--papel" and (i == 0 or argv[i - 1] != "--papel")]
    destino = Path(args[0]) if args else Path(__file__).with_name("resultado_base.json")
    conversas = [c for c in json.loads(CASOS.read_text(encoding="utf-8"))["conversas"]
                 if papel is None or c["papel"] == papel]
    resultados, resumo = [], {}
    for c in conversas:
        turnos = refazer(c)
        com_regra = [t for t in turnos if t["passou"] is not None]
        passou = sum(t["passou"] for t in com_regra)
        resultados.append({"id": c["id"], "papel": c["papel"], "turnos": turnos})
        p = resumo.setdefault(c["papel"], {"turnos": 0, "passou": 0, "conversas": 0, "conversas_inteiras": 0})
        p["turnos"] += len(com_regra)
        p["passou"] += passou
        p["conversas"] += 1
        p["conversas_inteiras"] += passou == len(com_regra)
    print("RESUMO", json.dumps(resumo, ensure_ascii=False), flush=True)
    destino.write_text(json.dumps({"resumo": resumo, "conversas": resultados}, ensure_ascii=False, indent=1),
                       encoding="utf-8")


if __name__ == "__main__":
    principal(sys.argv[1:])
