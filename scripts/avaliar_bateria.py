"""Bateria de medição do Crivo: astronomia e diálogos curtos.

Classifica cada resposta factual em:
  acerto          contém um dos trechos esperados;
  parcial         fala do assunto pedido, mas sem o trecho esperado;
  recusou         admitiu não saber, embora a base tenha a resposta;
  assunto_errado  respondeu com conteúdo que nem menciona o assunto (o erro grave).
Para perguntas fora da base (tipo "recusa"): acerto quando admite o limite,
"inventou" quando apresenta conteúdo como resposta.

Uso: python scripts/avaliar_bateria.py [dev|retido|todos] [--saida arquivo.json] [--detalhes]
"""
import json
import sys
import unicodedata
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA))

RECUSAS_ID = {"fora", "duvida", "vazio", "social:nao_entendido", "escrita:fim"}
RECUSAS_INICIO = ("não tenho", "ainda não", "reconheci o assunto", "não reconheci",
                  "não consegui", "não encontrei")


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.casefold())
    return " ".join("".join(c for c in texto if unicodedata.category(c) != "Mn").split())


def recusou(ident, resposta):
    return ident in RECUSAS_ID or resposta.strip().lower().startswith(RECUSAS_INICIO)


def classificar(caso, ident, resposta):
    r = normalizar(resposta)
    if caso.get("tipo") == "recusa":
        return "acerto" if recusou(ident, resposta) else "inventou"
    if any(normalizar(t) in r for t in caso["contem"]):
        return "acerto"
    if recusou(ident, resposta):
        return "recusou"
    if any(normalizar(a) in r for a in caso["assunto"]):
        return "parcial"
    return "assunto_errado"


def conferir_turno(esperado, ident, resposta):
    r = normalizar(resposta)
    if "id" in esperado and not any(ident.startswith(p) for p in esperado["id"]):
        return False
    if "contem" in esperado and not any(normalizar(t) in r for t in esperado["contem"]):
        return False
    if any(normalizar(t) in r for t in esperado.get("nao_contem", ())):
        return False
    return True


def avaliar(conjunto):
    from crivo import Crivo
    dados = json.loads((PASTA / "avaliacoes" / "bateria_v1" / (conjunto + ".json")).read_text(encoding="utf-8"))
    resultados, contagem = [], {}
    for caso in dados["casos"]:
        ident, resposta = Crivo().responder(caso["p"])
        classe = classificar(caso, ident, resposta)
        contagem[classe] = contagem.get(classe, 0) + 1
        resultados.append({"pergunta": caso["p"], "tipo": caso.get("tipo", "fato"),
                           "classe": classe, "id": ident, "resposta": resposta[:300]})
    dialogos_ok = 0
    falhas_dialogo = []
    for dialogo in dados["dialogos"]:
        bot = Crivo()
        ok = True
        for fala, esperado in dialogo["turnos"]:
            ident, resposta = bot.responder(fala)
            if not conferir_turno(esperado, ident, resposta):
                ok = False
                falhas_dialogo.append({"fala": fala, "id": ident, "resposta": resposta[:200]})
                break
        dialogos_ok += ok
    fatos = [r for r in resultados if r["tipo"] == "fato"]
    resumo = {
        "conjunto": conjunto,
        "fatos": len(fatos),
        "acertos_fato": sum(r["classe"] == "acerto" for r in fatos),
        "parcial": contagem.get("parcial", 0),
        "recusou": contagem.get("recusou", 0),
        "assunto_errado": contagem.get("assunto_errado", 0),
        "recusas_esperadas": len(resultados) - len(fatos),
        "recusas_corretas": sum(r["classe"] == "acerto" for r in resultados if r["tipo"] == "recusa"),
        "inventou": contagem.get("inventou", 0),
        "dialogos": len(dados["dialogos"]),
        "dialogos_ok": dialogos_ok,
    }
    return resumo, resultados, falhas_dialogo


def main():
    args = sys.argv[1:]
    detalhes = "--detalhes" in args
    saida = args[args.index("--saida") + 1] if "--saida" in args else None
    alvo = next((a for a in args if a in ("dev", "retido", "todos")), "dev")
    relatorio = {}
    for conjunto in (("dev", "retido") if alvo == "todos" else (alvo,)):
        resumo, resultados, falhas = avaliar(conjunto)
        relatorio[conjunto] = {"resumo": resumo, "resultados": resultados, "falhas_dialogo": falhas}
        print(json.dumps(resumo, ensure_ascii=False))
        if detalhes:
            for r in resultados:
                if r["classe"] != "acerto":
                    print("  [{}] {} -> {} | {}".format(r["classe"], r["pergunta"], r["id"],
                                                       r["resposta"][:110].replace("\n", " ")))
            for f in falhas:
                print("  [dialogo] {} -> {} | {}".format(f["fala"], f["id"], f["resposta"][:110].replace("\n", " ")))
    if saida:
        Path(saida).write_text(json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
