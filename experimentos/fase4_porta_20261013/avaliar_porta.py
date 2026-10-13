"""Porta conversacional (fase 4): o mesmo CRIVO com e sem a voz do realizador 17M.

python experimentos/fase4_porta_20261013/avaliar_porta.py --saida /tmp/porta [--realizador PASTA]

Cada conversa congelada roda duas vezes, do zero: com o motor atual e com o realizador
(`bot.realizador`). Os critérios de cada turno valem igual para os dois. Sem --realizador,
só o motor atual roda (útil para medir a cobertura do adaptador sem os pesos).

Gates (fixados antes da primeira execução com pesos):
  regressoes == 0            nenhum turno que passa no motor atual falha com o realizador;
  uso >= 60%                 dos turnos com quadro, a conferência aprova a frase do realizador;
  revisao_corrigiu == 0      a revisão não precisa corrigir nenhuma frase do realizador.
Mesmo passando, o opt-in só acontece depois que o criador do projeto ler o lado a lado.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))

CONJUNTOS = {
    # v1: escrito antes da primeira execução; depois dela, vale como regressão conhecida.
    "v1": ("conversas_congeladas.json", "84ffcece7880ea45586b38ead1e60ab0455ca1d6d8552b17e448340a4acd5782"),
    # v2: escrito depois de ler a v1 e antes de rodar os ajustes; é o teste novo.
    "v2": ("conversas_congeladas_v2.json", "5ff142e663678c0aa36d69635c1c515900da0fd495ee75700f49e9f944695acc"),
}


def conferir(turno, texto):
    baixo = texto.casefold()
    falhas = [c for c in turno.get("contem", ()) if c.casefold() not in baixo]
    algum = turno.get("contem_algum")
    if algum and not any(c.casefold() in baixo for c in algum):
        falhas.append("nenhum de: " + " / ".join(algum))
    falhas += ["contém: " + c for c in turno.get("nao_contem", ()) if c.casefold() in baixo]
    return not falhas, falhas


def rodar(conversas, realizador=None):
    from crivo import Crivo
    saida = []
    import random
    for k, conversa in enumerate(conversas):
        # Mesma semente nos dois lados: a variação de frases do CRIVO de hoje não
        # pode aparecer como diferença causada pelo realizador.
        random.seed(1000 + k)
        bot = Crivo()
        bot.conversacao.sorteio.seed(1000 + k)
        bot.realizador = realizador
        for j, turno in enumerate(conversa):
            ident, texto = bot.responder(turno["fala"])
            ok, falhas = conferir(turno, texto)
            reg = {"realizador": getattr(bot, "ultimo_realizador", None)}
            rev = getattr(bot.estado_interno, "revisao", None) or {}
            saida.append({"conversa": k, "turno": j, "fala": turno["fala"], "id": ident, "resposta": texto, "ok": ok,
                          "falhas": falhas, "realizador": reg.get("realizador"),
                          "revisao_corrigiu": bool(rev.get("corrections"))})
    return saida


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", required=True)
    ap.add_argument("--realizador", help="pasta com pesos.pt e tokenizer.json da fase 3 (SHA conferido)")
    ap.add_argument("--conjunto", choices=sorted(CONJUNTOS), default="v1")
    a = ap.parse_args()
    arquivo, SHA_CONVERSAS = CONJUNTOS[a.conjunto]
    texto = (AQUI / arquivo).read_text(encoding="utf-8")
    assert hashlib.sha256(texto.encode("utf-8")).hexdigest() == SHA_CONVERSAS, "conversas congeladas alteradas"
    conversas = json.loads(texto)["conversas"]
    destino = Path(a.saida)
    destino.mkdir(parents=True, exist_ok=True)

    atual = rodar(conversas)
    resultado = {"protocolo": "fase4_porta_conversacional", "conjunto": a.conjunto, "conversas_sha256": SHA_CONVERSAS,
                 "turnos": len(atual), "atual": {"ok": sum(t["ok"] for t in atual)}, "ativo_no_chat": False}
    if a.realizador:
        import realizador_17m
        voz = realizador_17m.Realizador(a.realizador)
        resultado["pesos_sha256"] = realizador_17m.PESOS_SHA256
        com = rodar(conversas, voz)
        com_quadro = [t for t in com if t["realizador"] and t["realizador"].get("quadro")]
        usados = [t for t in com_quadro if t["realizador"].get("usada")]
        regressoes = [(x, y) for x, y in zip(atual, com) if x["ok"] and not y["ok"]]
        melhoras = [(x, y) for x, y in zip(atual, com) if not x["ok"] and y["ok"]]
        por_ato = {}
        for t in com_quadro:
            ato = t["realizador"]["quadro"]["ato"]
            d = por_ato.setdefault(ato, {"com_quadro": 0, "usada": 0, "motivos": {}})
            d["com_quadro"] += 1
            d["usada"] += bool(t["realizador"].get("usada"))
            if not t["realizador"].get("usada"):
                d["motivos"][t["realizador"]["motivo"]] = d["motivos"].get(t["realizador"]["motivo"], 0) + 1
        resultado.update({
            "realizador": {"ok": sum(t["ok"] for t in com), "com_quadro": len(com_quadro), "usada": len(usados),
                           "uso": len(usados) / max(1, len(com_quadro)), "por_ato": por_ato,
                           "revisao_corrigiu": sum(t["revisao_corrigiu"] for t in usados)},
            "regressoes": [{"fala": y["fala"], "atual": x["resposta"], "realizador": y["resposta"], "falhas": y["falhas"]}
                           for x, y in regressoes],
            "melhoras": [{"fala": y["fala"], "atual": x["resposta"], "realizador": y["resposta"]} for x, y in melhoras],
        })
        resultado["gates"] = {"regressoes==0": not regressoes, "uso>=60%": resultado["realizador"]["uso"] >= 0.60,
                              "revisao_corrigiu==0": resultado["realizador"]["revisao_corrigiu"] == 0}
        resultado["gate_pass"] = all(resultado["gates"].values())
        linhas = ["# Porta conversacional — lado a lado", "",
                  "Cada turno: o que a pessoa disse, o CRIVO de hoje e o CRIVO com a voz do 17M.", ""]
        for x, y in zip(atual, com):
            if x["turno"] == 0:
                linhas += ["", "## Conversa %d" % (x["conversa"] + 1), ""]
            r = y["realizador"] or {}
            marca = "voz do 17M" if r.get("usada") else ("conferência recusou: " + str(r.get("motivo"))) if r.get("quadro") else "sem quadro"
            linhas += ["**Pessoa:** " + x["fala"], "", "- Hoje: " + x["resposta"].replace("\n", " "),
                       "- Com o 17M (%s): %s" % (marca, y["resposta"].replace("\n", " ")), ""]
        (destino / "lado_a_lado.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
        resultado["linhas_realizador"] = com
    resultado["linhas_atual"] = atual
    (destino / "resultado_porta.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    resumo = {k: v for k, v in resultado.items() if not k.startswith("linhas")}
    print(json.dumps(resumo, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    principal()
