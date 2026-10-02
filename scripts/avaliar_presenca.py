"""Mede presença na conversa: resposta específica, sem repetição, sem
"não entendi" de robô, lembrando o que foi dito.

Por turno: "contem" (algum), "nao_contem" (nenhum), "especifico" (a
resposta retoma ao menos uma palavra de conteúdo da fala da pessoa).
Por conversa: respostas genéricas (não entendi/menu) e repetições
(mesma frase de abertura ou mesmo texto já dito na conversa).

Uso: python scripts/avaliar_presenca.py [dev|retido|todos] [--detalhes] [--transcricao]
"""
import json
import re
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA))

from linguagem_conversa import normalizar  # noqa: E402

VAZIAS = set("""a o as os um uma uns umas de do da dos das em no na nos nas ao aos que e é eu tu ele ela
    eles elas meu minha meus minhas seu sua seus suas pra para por com sem mas hoje ontem foi era
    muito muita mais ainda ja porque quando como isso esse essa este esta ta to tô tá vai vou estou
    estava fiz fui tem tenho sim nao não né ne pois sei la lá""".split())
GENERICAS = ("ainda nao consegui entender", "digite 'ajuda'", "digite ajuda", "pode indicar o assunto",
             "nao reconheci essa pergunta")


def raizes(texto):
    return {w[:5] for w in re.findall(r"[a-z0-9]+", normalizar(texto)) if len(w) >= 4 and w not in VAZIAS}


def generica(ident, resposta):
    n = normalizar(resposta)
    return ident in ("fora", "duvida") or any(g in n for g in GENERICAS)


def primeira_frase(resposta):
    return normalizar(re.split(r"(?<=[.!?])\s", resposta.strip())[0])


def conferir(esperado, fala, resposta):
    n = normalizar(resposta)
    if "contem" in esperado and not any(normalizar(t) in n for t in esperado["contem"]):
        return False
    if any(normalizar(t) in n for t in esperado.get("nao_contem", ())):
        return False
    if esperado.get("especifico") and not (raizes(fala) & raizes(resposta)):
        return False
    return True


def avaliar(conjunto, transcrever=False):
    from crivo import Crivo
    dados = json.loads((PASTA / "avaliacoes" / "presenca_v1" / (conjunto + ".json")).read_text(encoding="utf-8"))
    turnos = ok = genericas = repeticoes = 0
    falhas, transcricao = [], []
    for c in dados["conversas"]:
        bot = Crivo()
        bot.conversacao.sorteio.seed(20261002)
        ditas, aberturas = set(), []
        transcricao.append("== " + c["nome"])
        for fala, esperado in c["turnos"]:
            ident, resposta = bot.responder(fala)
            transcricao.append("  VOCÊ: %s\n  CRIVO [%s]: %s" % (fala, ident, resposta.replace("\n", " / ")))
            turnos += 1
            passou = conferir(esperado, fala, resposta)
            ok += passou
            if not passou:
                falhas.append({"conversa": c["nome"], "fala": fala, "id": ident, "resposta": resposta[:200]})
            if generica(ident, resposta):
                genericas += 1
            chave = normalizar(resposta)
            frase1 = primeira_frase(resposta)
            if chave in ditas or (len(frase1) > 25 and frase1 in aberturas):
                repeticoes += 1
            ditas.add(chave)
            aberturas.append(frase1)
    resumo = {"conjunto": conjunto, "turnos": turnos, "turnos_ok": ok, "genericas": genericas,
              "repeticoes": repeticoes}
    return resumo, falhas, transcricao


def main():
    args = sys.argv[1:]
    alvo = next((a for a in args if a in ("dev", "retido", "todos")), "dev")
    for conjunto in (("dev", "retido") if alvo == "todos" else (alvo,)):
        resumo, falhas, transcricao = avaliar(conjunto)
        print(json.dumps(resumo, ensure_ascii=False))
        if "--detalhes" in args:
            for f in falhas:
                print("  [{}] {} -> {} | {}".format(f["conversa"], f["fala"], f["id"], f["resposta"][:140].replace("\n", " ")))
        if "--transcricao" in args:
            print("\n".join(transcricao))


if __name__ == "__main__":
    main()
