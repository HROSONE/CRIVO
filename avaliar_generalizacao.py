"""Avaliação autoral com famílias separadas; não é avaliação externa cega.

Os rótulos descrevem o pedido e fatos existentes, não a saída do chatbot.
Treino, validação e teste final têm famílias disjuntas. O teste final é
executado explicitamente, depois da seleção pela validação. Não é carregado
pelo assistente nem pelos scripts de treinamento. Famílias são a unidade
de independência; dez temas por família não são dez avaliações independentes.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

CAMINHO = Path(__file__).with_name("benchmark_generalizacao.json")
ABSTENCOES = {"fora", "duvida", "vazio", "linguagem:negado", "social:nao_entendido"}


def carregar(caminho=CAMINHO):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if dados.get("versao") != 1:
        raise ValueError("Versão de benchmark inválida")
    vistos, familias = set(), {}
    for grupo in ("perguntas", "dialogos"):
        for caso in dados[grupo]:
            if caso["id"] in vistos or caso["split"] not in ("treino", "validacao", "teste"):
                raise ValueError("Caso duplicado ou partição inválida")
            vistos.add(caso["id"])
            familia = grupo + ":" + caso["familia"]
            anterior = familias.setdefault(familia, caso["split"])
            if anterior != caso["split"]:
                raise ValueError("Família vazou entre partições")
    textos = [c["texto"].casefold().strip() for c in dados["perguntas"]]
    if len(textos) != len(set(textos)):
        raise ValueError("Pergunta duplicada")
    return dados


def assinatura(dados):
    return hashlib.sha256(json.dumps(dados, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def confere(ident, resposta, esperado):
    if esperado.get("abster"):
        return ident in ABSTENCOES
    return (ident in esperado["ids"] and
            all(t.casefold() in resposta.casefold() for t in esperado.get("trechos", [])) and
            all(t.casefold() not in resposta.casefold() for t in esperado.get("proibidos", [])))


def avaliar(split="validacao", classe=None, caminho=CAMINHO):
    if split not in ("treino", "validacao", "teste"):
        raise ValueError("Partição inválida")
    if classe is None:
        from crivo import Crivo
        classe = Crivo
    dados = carregar(caminho)
    resultados, dialogos = [], []
    for caso in dados["perguntas"]:
        if caso["split"] != split:
            continue
        ident, resposta = classe().responder(caso["texto"])
        resultados.append(dict(id=caso["id"], familia=caso["familia"],
                               passou=confere(ident, resposta, caso["esperado"]),
                               absteve=ident in ABSTENCOES, resposta_id=ident))
    for caso in dados["dialogos"]:
        if caso["split"] != split:
            continue
        bot, turnos = classe(), []
        for turno in caso["turnos"]:
            ident, resposta = bot.responder(turno["texto"])
            turnos.append(confere(ident, resposta, turno["esperado"]))
        dialogos.append(dict(id=caso["id"], familia=caso["familia"],
                             passou=all(turnos), turnos_corretos=sum(turnos), total=len(turnos)))
    familias = {}
    for r in resultados:
        f = familias.setdefault(r["familia"], {"total": 0, "acertos": 0})
        f["total"] += 1
        f["acertos"] += r["passou"]
    return dict(split=split, assinatura=assinatura(dados),
                perguntas=dict(total=len(resultados), acertos=sum(r["passou"] for r in resultados),
                               abstencoes=sum(r["absteve"] for r in resultados), familias=familias,
                               falhas=[r for r in resultados if not r["passou"]]),
                dialogos=dict(total=len(dialogos), acertos=sum(r["passou"] for r in dialogos),
                              turnos=sum(r["total"] for r in dialogos),
                              turnos_corretos=sum(r["turnos_corretos"] for r in dialogos),
                              falhas=[r for r in dialogos if not r["passou"]]),
                limite=__doc__.strip())


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--split", choices=("treino", "validacao", "teste"), default="validacao")
    p.add_argument("--saida")
    args = p.parse_args()
    relatorio = avaliar(args.split)
    texto = json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n"
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
    print(texto)
