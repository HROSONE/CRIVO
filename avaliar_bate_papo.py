"""Sonda autoral de diálogos completos, registrada para comparação antes/depois.

Os cenários são de desenvolvimento, não treino nem avaliação externa cega.
Uma recusa causal pertinente conta como compreensão do pedido, não como
conhecimento da causa. Os critérios incluem assunto, memória e limites.
"""
import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path


CASOS = [
    ("dia difícil", [
        ("Oi", "social:oi", []),
        ("Tô cansado hoje", "conversa:relato", ["cansado"]),
        ("Foi um dia puxado no trabalho", "conversa:relato", ["puxado"]),
        ("Meu chefe pediu muita coisa", "conversa:relato", ["chefe"]),
        ("O que você faria no meu lugar?", "conversa:reflexao", ["chefe", "opções"]),
    ]),
    ("projeto e fragmentos", [
        ("Quero conversar sobre meu projeto", "conversa:abertura", ["projeto"]),
        ("Estou fazendo um jogo", "conversa:relato", ["jogo"]),
        ("Um jogo de aventura com robôs", "conversa:relato", ["robôs"]),
        ("Quero que ele seja divertido", "conversa:relato", ["divertido"]),
        ("Tem alguma ideia?", "conversa:ideias", ["divertido", "testar"]),
    ]),
    ("nome e preferência", [
        ("Meu nome é Rafael", "conversa:relato", ["Rafael"]),
        ("Como eu me chamo?", "conversa:memoria", ["Rafael"]),
        ("Eu gosto de música e desenho", "conversa:relato", ["música e desenho"]),
        ("O que eu gosto de fazer?", "conversa:memoria", ["música e desenho"]),
    ]),
    ("plano com restrição", [
        ("Estou pensando em aprender Python", "conversa:relato", ["aprender Python"]),
        ("Por onde eu começo?", "conversa:planejamento", ["aprender Python", "tentativa"]),
        ("Mas tenho pouco tempo", "conversa:relato", ["pouco tempo"]),
        ("Só tenho 20 minutos por dia", "conversa:relato", ["20"]),
        ("Como posso organizar isso?", "conversa:planejamento", ["20 minutos", "4 min", "12 min"]),
        ("Por quê?", "conversa:justificativa", ["aprender Python", "20 minutos"]),
    ]),
    ("reparo factual e causa ausente", [
        ("O que é memória?", "conhecimento:mundo_memoria", ["registrar"]),
        ("Não entendi direito", "escrita:simples", ["recuperar"]),
        ("Pode explicar de um jeito mais simples?", "escrita:simples", ["recuperar"]),
        ("Por que isso acontece?", "fora", ["causal"]),
    ]),
    ("pedido informal e comparação", [
        ("Me fala uma coisa: pra que serve o DNA?", "escrita:explicacao", ["DNA", "genéticas"]),
        ("E o RNA, faz a mesma coisa?", "escrita:comparacao", ["DNA", "RNA", "informação genética"]),
    ]),
    ("opinião e argumento", [
        ("Acho que tecnologia deixa a gente mais sozinho", "conversa:relato", ["tecnologia"]),
        ("Você concorda comigo?", "conversa:reflexao", ["hipótese", "tecnologia"]),
        ("Por quê?", "conversa:justificativa", ["regra geral"]),
    ]),
    ("decisão com duas opções", [
        ("Tenho duas opções: estudar hoje ou descansar", "conversa:relato", ["estudar hoje", "descansar"]),
        ("Amanhã tenho prova e estou cansado", "conversa:relato", ["prova", "cansado"]),
        ("O que vale mais a pena?", "conversa:reflexao", ["estudar hoje", "descansar", "prazo"]),
    ]),
    ("cinema e perspectiva", [
        ("Vamos conversar sobre cinema", "conversa:abertura", ["cinema"]),
        ("Gosto de histórias com finais inesperados", "conversa:relato", ["finais inesperados"]),
        ("E você?", "conversa:perspectiva", ["Não tenho gostos", "finais inesperados"]),
        ("O que faz um final ser bom?", "conversa:criterios", ["finais inesperados", "critério"]),
    ]),
    ("premissas inéditas", [
        ("Se todo Lumo é um Tavi e todo Tavi é azul, um Lumo é azul?", "conversa:hipotese", ["Sim", "Lumo → Tavi → azul", "hipótese"]),
        ("Então um Tavi é um Lumo?", "conversa:hipotese", ["Não consigo concluir", "não prova"]),
    ]),
    ("conta com dados do usuário", [
        ("Comprei três livros por 20 reais cada. Quanto gastei?", "conversa:calculo", ["R$ 60", "3 × R$ 20"]),
    ]),
    ("relação com outra pessoa", [
        ("Queria trocar uma ideia contigo", "conversa:abertura", ["situação"]),
        ("Sobre um problema que tive com um amigo", "conversa:relato", ["amigo"]),
        ("Ele não me respondeu desde ontem", "conversa:relato", ["não me respondeu"]),
        ("Será que ele está bravo comigo?", "conversa:reflexao", ["não permite saber", "outra pessoa"]),
    ]),
    ("assunto fora do currículo factual", [
        ("Quero conversar sobre restauração de violinos", "conversa:abertura", ["violinos"]),
        ("Quero restaurar um instrumento", "conversa:relato", ["restaurar"]),
        ("Só tenho 25 minutos por dia", "conversa:relato", ["25"]),
        ("Me ajuda a montar um plano", "conversa:planejamento", ["restaurar", "25 minutos", "15 min"]),
    ]),
    ("correção, negação e esquecimento", [
        ("Meu nome é Cecília", "conversa:relato", ["Cecília"]),
        ("Na verdade, meu nome é Maíra", "conversa:relato", ["Maíra"]),
        ("Como eu me chamo?", "conversa:memoria", ["Maíra"]),
        ("Eu gosto de violinos", "conversa:relato", ["violinos"]),
        ("Eu não gosto de violinos", "conversa:relato", ["não gosta"]),
        ("O que eu gosto de fazer?", "conversa:memoria", ["não gosta"]),
        ("Mudar de assunto", "conversa:reinicio", ["começar"]),
        ("Como eu me chamo?", "conversa:memoria", ["ainda não me disse"]),
    ]),
    ("premissas em vários turnos", [
        ("Suponha que todo Kavor é um Névia", "conversa:hipotese", ["hipótese"]),
        ("E todo Névia é verde", "conversa:hipotese", ["hipótese"]),
        ("Então um Kavor é verde?", "conversa:hipotese", ["Kavor → Névia → verde"]),
    ]),
]


def avaliar(classe):
    casos = []
    for nome, turnos in CASOS:
        bot, resultados = classe(), []
        for pergunta, esperado, trechos in turnos:
            ident, texto = bot.responder(pergunta)
            resultados.append(dict(pergunta=pergunta, esperado=esperado, obtido=ident,
                                   passou=ident == esperado and all(t in texto for t in trechos), resposta=texto))
        casos.append(dict(nome=nome, passou=all(r["passou"] for r in resultados), turnos=resultados))
    return dict(dialogos=len(casos), dialogos_corretos=sum(c["passou"] for c in casos),
                turnos=sum(len(c["turnos"]) for c in casos),
                turnos_corretos=sum(r["passou"] for c in casos for r in c["turnos"]), casos=casos)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--referencia", help="Diretório com o código anterior para medir o mesmo conjunto")
    p.add_argument("--saida", default="avaliacao_bate_papo.json")
    a = p.parse_args()
    if a.referencia:
        sys.path.insert(0, str(Path(a.referencia).resolve()))
    classe = importlib.import_module("crivo").Crivo
    resultado = avaliar(classe)
    resultado.update(assinatura_casos=hashlib.sha256(json.dumps(CASOS, ensure_ascii=False).encode("utf-8")).hexdigest(), limite=__doc__.strip())
    Path(a.saida).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: resultado[k] for k in ("dialogos", "dialogos_corretos", "turnos", "turnos_corretos")}, ensure_ascii=False))
    for c in resultado["casos"]:
        for t in c["turnos"]:
            if not t["passou"]:
                print(c["nome"], t["pergunta"], "=>", t["obtido"])
    raise SystemExit(0 if a.referencia or resultado["dialogos"] == resultado["dialogos_corretos"] else 1)
