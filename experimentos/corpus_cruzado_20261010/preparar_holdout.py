"""Cria apenas o holdout fresco do experimento cruzado. Não treina nada."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

CONTEXTOS = [
    dict(familia="farol", pessoa="Nara", obj1="mapa", obj2="câmera", atividade="fotografia", lugar="farol"),
    dict(familia="jardim", pessoa="Davi", obj1="caderno", obj2="lanterna", atividade="desenho", lugar="jardim"),
    dict(familia="estudio", pessoa="Lia", obj1="livro", obj2="violão", atividade="leitura", lugar="estúdio"),
    dict(familia="arquivo", pessoa="Rui", obj1="pacote", obj2="chave", atividade="escrita", lugar="arquivo"),
    dict(familia="trilha", pessoa="Bia", obj1="mochila", obj2="garrafa", atividade="caminhada", lugar="trilha"),
    dict(familia="mercado", pessoa="Caio", obj1="receita", obj2="cesta", atividade="cozinha", lugar="mercado"),
    dict(familia="terraco", pessoa="Iara", obj1="planta", obj2="vaso", atividade="jardinagem", lugar="terraço"),
    dict(familia="laboratorio", pessoa="Theo", obj1="relatório", obj2="tablet", atividade="estudo", lugar="laboratório"),
]

ORDENS = [
    ["registrar_estado","correcao","prazo","incerteza","recordar","pedido_educado","conversa_sem_dicas","adiar_sem_abandonar"],
    ["registrar_estado","incerteza","correcao","pedido_educado","prazo","recordar","adiar_sem_abandonar","conversa_sem_dicas"],
    ["registrar_estado","prazo","correcao","recordar","conversa_sem_dicas","incerteza","pedido_educado","adiar_sem_abandonar"],
    ["registrar_estado","conversa_sem_dicas","correcao","incerteza","recordar","prazo","adiar_sem_abandonar","pedido_educado"],
    ["registrar_estado","correcao","recordar","adiar_sem_abandonar","incerteza","prazo","conversa_sem_dicas","pedido_educado"],
    ["registrar_estado","incerteza","prazo","correcao","pedido_educado","recordar","conversa_sem_dicas","adiar_sem_abandonar"],
    ["registrar_estado","prazo","conversa_sem_dicas","correcao","adiar_sem_abandonar","recordar","incerteza","pedido_educado"],
    ["registrar_estado","conversa_sem_dicas","incerteza","prazo","correcao","pedido_educado","adiar_sem_abandonar","recordar"],
]


def turno(op, c, atual):
    if op == "registrar_estado":
        return (f"Vou levar o {c['obj1']} para o {c['lugar']} amanhã.",
                [f"Certo. Você vai levar o {c['obj1']} para o {c['lugar']} amanhã.",
                 f"Entendi. O {c['obj1']} é sua escolha para o {c['lugar']}."])
    if op == "correcao":
        return (f"Corrigindo: não vou levar o {c['obj1']}; vou levar o {c['obj2']}.",
                [f"Entendi. A escolha agora é o {c['obj2']}.",
                 f"Certo. Você mudou a escolha para o {c['obj2']}."])
    if op == "recordar":
        return ("Qual objeto eu vou levar agora?",
                [f"Você vai levar o {c['obj2']}.", f"A escolha atual é o {c['obj2']}."])
    if op == "prazo":
        return (f"Preciso entregar o {atual} amanhã. Se eu parar por uma hora, o prazo muda?",
                ["Não. O prazo continua amanhã.", "Não. Fazer uma pausa não muda o prazo de amanhã."])
    if op == "incerteza":
        return (f"{c['pessoa']} ficou em silêncio quando pedi ajuda. Isso quer dizer que recusou?",
                ["Não dá para concluir isso só pelo silêncio.", "Não. O silêncio sozinho não confirma uma recusa."])
    if op == "pedido_educado":
        return (f"Escreva uma pergunta curta para {c['pessoa']} pedir ajuda com o {atual}, sem soar como ordem.",
                [f"{c['pessoa']}, pode me ajudar com o {atual}, por favor?",
                 f"{c['pessoa']}, você pode me ajudar com o {atual}?"])
    if op == "conversa_sem_dicas":
        return (f"Hoje pratiquei {c['atividade']}. Foi tranquilo. Só quero conversar, sem dicas.",
                [f"Tudo bem. O que você mais gostou em {c['atividade']}?",
                 f"Claro. Qual parte de {c['atividade']} foi mais tranquila para você?"])
    if op == "adiar_sem_abandonar":
        return (f"Vou parar agora e continuar {c['atividade']} amanhã. Isso quer dizer que desisti?",
                ["Não. Você só decidiu continuar amanhã.", "Não. Fazer uma pausa agora não significa desistir."])
    raise ValueError(op)


def regras(op, c, atual):
    if op in ("registrar_estado",): return {"contem": [c["obj1"]]}
    if op in ("correcao", "recordar"): return {"contem": [c["obj2"]]}
    if op == "prazo": return {"contem": ["amanhã"]}
    if op == "incerteza": return {"contem_um_de": ["não", "Não"]}
    if op == "pedido_educado": return {"contem": [c["pessoa"], atual]}
    if op == "conversa_sem_dicas": return {"nao_contem": ["deve", "faça primeiro"]}
    if op == "adiar_sem_abandonar": return {"contem_um_de": ["não", "Não"]}
    return {}


def construir():
    sessoes = []
    for si, (c, ordem) in enumerate(zip(CONTEXTOS, ORDENS), 1):
        atual = c["obj1"]
        itens = []
        for ti, op in enumerate(ordem, 1):
            mensagem, alternativas = turno(op, c, atual)
            resposta = alternativas[(si + ti) % len(alternativas)]
            itens.append(dict(turno=ti, operacao=op, mensagem=mensagem, resposta=resposta,
                              alternativas_validas=alternativas, regras=regras(op, c, atual)))
            if op == "correcao": atual = c["obj2"]
        sessoes.append(dict(id=f"fresh-{c['familia']}", familia=c["familia"], turnos=itens))
    dados = dict(versao="fresh-cross-dialogue-v1", criado_antes_do_treino=True,
                 descricao="8 sessões inéditas, 64 turnos. O histórico é reconstruído em ordem pelo avaliador.",
                 familias_reservadas=[c["familia"] for c in CONTEXTOS], sessoes=sessoes)
    bruto = (json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    destino = OUT / "holdout_fresco.json"
    destino.write_bytes(bruto)
    meta = dict(sha256=hashlib.sha256(bruto).hexdigest(), sessoes=len(sessoes),
                turnos=sum(len(s["turnos"]) for s in sessoes),
                familias_reservadas=dados["familias_reservadas"],
                regra="Arquivo criado e commitado antes de existir workflow de treino nesta branch.")
    (OUT / "holdout_fresco_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    construir()
