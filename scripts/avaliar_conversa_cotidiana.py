"""Mede a conversa do dia a dia: observações, noções e “não sei”.

Classes por caso:
  observacao: acerto | nao_entendeu | palestra (respondeu com explicação
              em vez de conversar) | sem_tema | sem_pergunta
  nocao:      acerto | nao_entendeu | sem_marca (afirmou sem dizer que é
              noção) | errado
  nao_sei:    acerto | nao_entendeu | sem_admitir (explicou sem dizer o limite)
  fato:       acerto | errado (o conhecimento com fonte não pode piorar)

Uso: python scripts/avaliar_conversa_cotidiana.py [dev|retido|todos] [--detalhes]
"""
import json
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA))

from linguagem_conversa import normalizar  # noqa: E402

CONVERSA = ("nocao:", "conversa:", "social:")
MARCAS = ("em geral", "pelo que eu sei", "nocao", "costuma")


def nao_entendeu(ident, resposta):
    return ident in ("fora", "duvida", "social:nao_entendido") or "Ainda não consegui entender" in resposta


def contem(resposta, termos):
    n = normalizar(resposta)
    return any(normalizar(t) in n for t in termos)


def classificar(caso, ident, resposta):
    tipo = caso["tipo"]
    n = normalizar(resposta)
    if tipo == "fato":
        if "id" in caso:
            return "acerto" if ident == caso["id"] else "errado"
        return "acerto" if contem(resposta, caso["contem"]) else "errado"
    if nao_entendeu(ident, resposta):
        return "nao_entendeu"
    if tipo == "observacao":
        if not ident.startswith(CONVERSA):
            return "palestra"
        if not contem(resposta, caso["tema"]):
            return "sem_tema"
        return "acerto" if "?" in resposta else "sem_pergunta"
    if tipo == "nocao":
        if not contem(resposta, caso["contem"]):
            return "errado"
        return "acerto" if any(m in n for m in MARCAS) else "sem_marca"
    if tipo == "nao_sei":
        return "acerto" if "nao sei" in n and contem(resposta, caso["contem"]) else "sem_admitir"
    raise ValueError(tipo)


def conferir_turno(esperado, ident, resposta):
    if esperado.get("nao_fora") and nao_entendeu(ident, resposta):
        return False
    if "contem_algum" in esperado and not contem(resposta, esperado["contem_algum"]):
        return False
    return True


def avaliar(conjunto):
    from crivo import Crivo
    dados = json.loads((PASTA / "avaliacoes" / "conversa_cotidiana_v1" / (conjunto + ".json"))
                       .read_text(encoding="utf-8"))
    resultados, contagem = [], {}
    for caso in dados["casos"]:
        ident, resposta = Crivo().responder(caso["fala"])
        classe = classificar(caso, ident, resposta)
        contagem.setdefault(caso["tipo"], {}).setdefault(classe, 0)
        contagem[caso["tipo"]][classe] += 1
        resultados.append({"fala": caso["fala"], "tipo": caso["tipo"], "classe": classe,
                           "id": ident, "resposta": resposta[:300]})
    dialogos_ok, falhas = 0, []
    for dialogo in dados["dialogos"]:
        bot, ok = Crivo(), True
        bot.conversacao.sorteio.seed(20261002)
        for fala, esperado in dialogo["turnos"]:
            ident, resposta = bot.responder(fala)
            if not conferir_turno(esperado, ident, resposta):
                ok = False
                falhas.append({"fala": fala, "id": ident, "resposta": resposta[:200]})
                break
        dialogos_ok += ok
    resumo = {"conjunto": conjunto, "casos": len(resultados),
              "acertos": sum(r["classe"] == "acerto" for r in resultados),
              "por_tipo": {t: dict(sorted(c.items())) for t, c in sorted(contagem.items())},
              "fatos_errados": contagem.get("fato", {}).get("errado", 0),
              "dialogos": len(dados["dialogos"]), "dialogos_ok": dialogos_ok}
    return resumo, resultados, falhas


def main():
    args = sys.argv[1:]
    alvo = next((a for a in args if a in ("dev", "retido", "retido2", "todos")), "dev")
    for conjunto in (("dev", "retido", "retido2") if alvo == "todos" else (alvo,)):
        resumo, resultados, falhas = avaliar(conjunto)
        print(json.dumps(resumo, ensure_ascii=False))
        if "--detalhes" in args:
            for r in resultados:
                if r["classe"] != "acerto":
                    print("  [{}] {} -> {} | {}".format(r["classe"], r["fala"], r["id"],
                                                       r["resposta"][:110].replace("\n", " ")))
            for f in falhas:
                print("  [dialogo] {} -> {} | {}".format(f["fala"], f["id"], f["resposta"][:110].replace("\n", " ")))


if __name__ == "__main__":
    main()
