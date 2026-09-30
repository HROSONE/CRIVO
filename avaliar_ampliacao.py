"""Sonda autoral de ampliação, com critérios fixados antes de observar saídas.

Os pedidos e argumentos deste arquivo não participam do treino. O oráculo
confere operações, continuidade, cópia dos dados declarados e proveniência;
os textos completos permitem revisão humana. Não mede inteligência geral,
compreensão irrestrita ou qualidade literária por uma pontuação automática.
"""
import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path


def turno(pergunta, ids=(), trechos=(), **criterios):
    if isinstance(ids, str):
        ids = [ids]
    return dict(pergunta=pergunta, ids=list(ids), trechos=list(trechos), **criterios)


CASOS = [
    ("pedido informal e continuidade", [
        turno("Será que você consegue criar um conto sobre Zíria-47 e um trem de vidro?",
              "conversa:gerada_historia", ["Zíria-47", "um trem de vidro"], gerada=True),
        turno("Pode continuar de onde parou?", "conversa:gerada_continuacao",
              ["Zíria-47", "um trem de vidro"], gerada=True, diferente=True),
        turno("Agora deixa esse conto com um clima misterioso", "conversa:gerada_historia",
              ["Zíria-47", "um trem de vidro"], gerada=True, diferente=True),
        turno("Muda Zíria-47 para Maíra", "conversa:gerada_historia",
              ["Maíra", "um trem de vidro"], gerada=True, ausentes=["Zíria-47"]),
    ]),
    ("diálogo fictício e revisão", [
        turno("Você pode escrever um diálogo entre uma tartaruga astronauta e uma bússola falante?",
              "conversa:gerada_dialogo", ["uma tartaruga astronauta", "uma bússola falante"],
              gerada=True, linhas_minimas=2),
        turno("Continua a conversa deles", "conversa:gerada_continuacao",
              ["uma tartaruga astronauta", "uma bússola falante"], gerada=True, diferente=True),
        turno("Troque a bússola falante por um guarda-chuva curioso", "conversa:gerada_dialogo",
              ["uma tartaruga astronauta", "um guarda-chuva curioso"], gerada=True,
              ausentes=["uma bússola falante"]),
    ]),
    ("mensagem com destinatário e tom", [
        turno("Me ajuda a escrever uma mensagem para Lídia dizendo que adorei nossa caminhada?",
              "conversa:gerada_mensagem", ["Lídia", "adorei nossa caminhada"], gerada=True),
        turno("Pode deixar mais carinhosa?", "conversa:gerada_mensagem",
              ["Lídia", "adorei nossa caminhada"], gerada=True, diferente=True),
        turno("Faça uma versão mais formal", "conversa:gerada_mensagem",
              ["Lídia", "adorei nossa caminhada"], gerada=True, diferente=True),
        turno("Troque Lídia por Bento", "conversa:gerada_mensagem",
              ["Bento", "adorei nossa caminhada"], gerada=True, ausentes=["Lídia"]),
    ]),
    ("pedido incompleto e preenchimento", [
        turno("Queria uma mensagem para Íris", "duvida", ["comunicar"]),
        turno("Dizendo que vou chegar vinte minutos depois", "conversa:gerada_mensagem",
              ["Íris", "vou chegar vinte minutos depois"], gerada=True),
    ]),
    ("resumo e reformulação de relatos", [
        turno("Quero conversar sobre uma apresentação que fiz", conversa=True),
        turno("Eu preparei os desenhos com cuidado", conversa=True, trechos=["desenhos"]),
        turno("Fiquei nervoso e esqueci de explicar a última página", conversa=True,
              trechos=["última página"]),
        turno("Junta o que eu te contei num resumo", "conversa:gerada_resumo",
              ["desenhos", "última página"], gerada=True, ausentes=["diagnóstico", "transtorno"]),
        turno("Pode dizer isso de outro jeito?", "conversa:gerada_reformulacao",
              ["desenhos", "última página"], gerada=True, diferente=True),
        turno("Me faça uma pergunta para eu pensar melhor nisso", "conversa:gerada_exploracao",
              ["última página"], gerada=True, pergunta_exploracao=True),
        turno("Me faça outra pergunta sobre isso", "conversa:gerada_exploracao",
              ["última página"], gerada=True, pergunta_exploracao=True, diferente=True),
    ]),
    ("objetivo, restrição e hipótese", [
        turno("Quero aprender a fazer animações de papel", conversa=True, trechos=["animações de papel"]),
        turno("Só tenho 25 minutos à noite e não posso comprar equipamentos", conversa=True,
              trechos=["25 minutos"]),
        turno("Me ajuda a organizar minhas ideias", "conversa:gerada_plano",
              ["animações de papel", "25 minutos", "não posso comprar equipamentos"], gerada=True),
        turno("E se eu só tivesse 8 minutos?", "conversa:gerada_plano",
              ["animações de papel", "8 minutos"], gerada=True),
        turno("Quanto tempo eu disse que tenho?", "conversa:memoria", ["25"]),
    ]),
    ("reflexão sobre dados explícitos", [
        turno("Eu perdi uma partida; isso significa que nunca vou jogar bem?",
              "conversa:gerada_reflexao", ["perdi uma partida", "nunca vou jogar bem"],
              gerada=True, algum=["não", "hipótese", "concluir", "conclusão"]),
        turno("Meu colega demorou a responder; posso concluir que ele está bravo comigo?",
              "conversa:gerada_reflexao", ["demorou a responder", "está bravo comigo"],
              gerada=True, algum=["não", "hipótese", "concluir", "conclusão"],
              ausentes=["com certeza ele está bravo", "ele certamente está bravo"]),
    ]),
    ("relato explícito no próprio pedido", [
        turno("Resuma este relato: Fui ao ensaio cedo, mas o ônibus atrasou e perdi a primeira música.",
              "conversa:gerada_resumo", ["ônibus atrasou", "primeira música"], gerada=True),
        turno("Reformule: Quero pedir ajuda sem parecer que estou cobrando uma resposta.",
              "conversa:gerada_reformulacao", ["pedir ajuda", "cobrando uma resposta"], gerada=True),
    ]),
    ("reset e ausência de dados", [
        turno("Escreva uma mensagem para Caíque dizendo que gostei da oficina",
              "conversa:gerada_mensagem", ["Caíque", "gostei da oficina"], gerada=True),
        turno("Esqueça essa conversa", "conversa:reinicio"),
        turno("Deixe a mensagem mais formal", "duvida", ausentes=["Caíque", "oficina"]),
        turno("Resuma o que eu te contei", "duvida", ausentes=["Caíque", "oficina"]),
    ]),
    ("negações não executam criação", [
        turno("Não escreva uma mensagem para Caíque dizendo que gostei da oficina", nao_gerada=True),
        turno("Não resuma o que eu te contei", nao_gerada=True),
        turno("Não continue uma história sobre uma ilha secreta", nao_gerada=True),
    ]),
    ("fatos, código e prova depois da escrita", [
        turno("Escreva um diálogo entre Névia e um cometa", "conversa:gerada_dialogo",
              ["Névia", "um cometa"], gerada=True),
        turno("O que é DNA?", "conhecimento:dna", ["genética"], nao_gerada=True),
        turno("Qual é a fonte?", "escrita:fontes", ["genome.gov"], nao_gerada=True),
        turno("Como usar input em Python?", "py_input", ["input("], nao_gerada=True),
        turno("Por que um pinguim é um ser vivo?", "logica:tipo_de", ["pinguim → ave"],
              nao_gerada=True, prova=True),
    ]),
]


def avaliar(classe):
    casos = []
    for nome, criterios in CASOS:
        bot = classe()
        turnos = []
        anterior = ""
        for c in criterios:
            ident, resposta = bot.responder(c["pergunta"])
            falhas = []
            if c["ids"] and ident not in c["ids"]:
                falhas.append("operação")
            if c.get("conversa") and not ident.startswith("conversa:"):
                falhas.append("acompanhamento do relato")
            if any(t.casefold() not in resposta.casefold() for t in c["trechos"]):
                falhas.append("dados declarados")
            if any(t.casefold() in resposta.casefold() for t in c.get("ausentes", [])):
                falhas.append("dado indevido ou substituição")
            if c.get("algum") and not any(t.casefold() in resposta.casefold() for t in c["algum"]):
                falhas.append("limite da conclusão")
            if c.get("diferente") and resposta == anterior:
                falhas.append("repetição integral")
            if c.get("pergunta_exploracao") and "?" not in resposta:
                falhas.append("pergunta de exploração")
            if c.get("linhas_minimas") and len(resposta.splitlines()) < c["linhas_minimas"]:
                falhas.append("formato de diálogo")
            quadro = (bot.historico[-1].get("quadro_geracao") or {}) if bot.historico else {}
            if c.get("gerada") and (not quadro or quadro.get("tokens", 0) < 6):
                falhas.append("geração concluída")
            if c.get("gerada") and (bot.contexto_textual is not None or
                                   "prova_origem" in (bot.ultimo_turno or {})):
                falhas.append("proveniência fictícia")
            if c.get("nao_gerada") and (quadro or ident.startswith("conversa:gerada_")):
                falhas.append("rota gerativa indevida")
            if c.get("prova") and not ident.startswith("logica:"):
                falhas.append("prova preservada")
            turnos.append(dict(pergunta=c["pergunta"], esperado=c["ids"], id=ident,
                               resposta=resposta, passou=not falhas, falhas=falhas))
            anterior = resposta
        casos.append(dict(nome=nome, passou=all(t["passou"] for t in turnos), turnos=turnos))
    ts = [t for c in casos for t in c["turnos"]]
    return dict(mensagens=len(ts), acertos=sum(t["passou"] for t in ts), dialogos=len(casos),
                dialogos_completos=sum(c["passou"] for c in casos), casos=casos)


def assinatura_casos():
    return hashlib.sha256(json.dumps(CASOS, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path)
    p.add_argument("--saida", type=Path, default=Path("avaliacao_ampliacao.json"))
    p.add_argument("--permitir-falhas", action="store_true")
    a = p.parse_args()
    if a.repo:
        sys.path.insert(0, str(a.repo.resolve()))
    r = avaliar(importlib.import_module("crivo").Crivo)
    r["assinatura_casos"] = assinatura_casos()
    r["limite"] = ("Sonda autoral de desenvolvimento, independente do corpus. Confere operações e "
                   "dados declarados; não é avaliação cega de compreensão geral ou qualidade literária.")
    a.saida.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k != "casos"}, ensure_ascii=False, indent=2))
    if r["acertos"] != r["mensagens"] and not a.permitir_falhas:
        sys.exit(1)
