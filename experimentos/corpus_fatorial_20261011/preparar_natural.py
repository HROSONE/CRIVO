"""Aplica português natural ao desenho fatorial antes de congelar o corpus.

Mantém a estrutura/contagens de preparar.py. Só substitui realizações textuais
por formas naturais com acentuação correta; o gate de gerabilidade decide se o
vocabulário fixo de 720 entradas consegue suportá-las sem realocação.
"""
from __future__ import annotations

import preparar as base

base.PREENCHIMENTOS_TREINO = [
    dict(nome="Lia", outro="Caio", objeto="caderno", atividade="leitura", lugar="casa"),
    dict(nome="Caio", outro="Nara", objeto="livro", atividade="escrita", lugar="sala"),
    dict(nome="Nara", outro="Davi", objeto="texto", atividade="fotografia", lugar="escola"),
    dict(nome="Davi", outro="Bia", objeto="desenho", atividade="desenho", lugar="biblioteca"),
    dict(nome="Bia", outro="Rui", objeto="rádio", atividade="pintura", lugar="oficina"),
    dict(nome="Rui", outro="Teo", objeto="vaso", atividade="jardinagem", lugar="cozinha"),
    dict(nome="Teo", outro="Mila", objeto="convite", atividade="revisão", lugar="praça"),
    dict(nome="Mila", outro="Lia", objeto="projeto", atividade="organização", lugar="quarto"),
]
base.PREENCHIMENTOS_DEV = [
    dict(nome="Iara", outro="Lino", objeto="caderno", atividade="escrita", lugar="sala"),
    dict(nome="Lino", outro="Noa", objeto="livro", atividade="leitura", lugar="casa"),
    dict(nome="Noa", outro="Sara", objeto="texto", atividade="desenho", lugar="escola"),
    dict(nome="Sara", outro="Iara", objeto="vaso", atividade="jardinagem", lugar="praça"),
]
base.PREENCHIMENTOS_FINAL = [
    dict(nome="Nubira-41", outro="Ocrélio-52", objeto="caderno", atividade="leitura", lugar="sala"),
    dict(nome="Ocrélio-52", outro="Velina-63", objeto="livro", atividade="escrita", lugar="casa"),
    dict(nome="Velina-63", outro="Darino-74", objeto="texto", atividade="fotografia", lugar="escola"),
    dict(nome="Darino-74", outro="Nubira-41", objeto="projeto", atividade="desenho", lugar="praça"),
]

base.MENSAGENS = {
    "recordar_pessoa": [
        "Quem ficou ligado a isso?",
        "Qual pessoa está combinada aqui?",
        "Me lembra quem é a pessoa.",
        "Quem é a pessoa nessa situação?",
    ],
    "recordar_objeto": [
        "Qual era o objeto mesmo?",
        "Do que eu estava falando?",
        "Me lembra qual é o objeto.",
        "Que objeto ficou nessa situação?",
    ],
    "corrigir_pessoa": [
        "Correção: agora é {outro}, não {atual}.",
        "Troque a pessoa: fica {outro} no lugar de {atual}.",
        "Mude isso: a pessoa correta é {outro}.",
        "Atualização: use {outro} como a pessoa.",
    ],
    "guardar_hipotese": [
        "Talvez eu faça {atividade} amanhã. Isso já está certo?",
        "Estou pensando em {atividade}, mas ainda não decidi. Posso tratar como fato?",
        "Se eu talvez fizer {atividade}, já posso dizer que aconteceu?",
        "Existe a possibilidade de eu fazer {atividade}. Isso está confirmado?",
    ],
    "mensagem_sem_horario": [
        "Escreva uma mensagem para {atual} sobre {atividade}, sem escolher horário.",
        "Quero convidar {atual} para {atividade}, mas não invente horário.",
        "Faça um convite para {atual} sobre {atividade}; não coloque horário.",
        "Escreva para {atual} sobre {atividade}, sem dizer quando.",
    ],
    "pedir_detalhe": [
        "Quero pedir uma coisa a {atual}, mas não disse o que.",
        "Preciso escrever um pedido para {atual}; ainda falta dizer o objeto.",
        "Quero fazer um pedido a {atual}, mas está faltando o que vou pedir.",
        "Vou pedir algo a {atual}; ainda não falei qual coisa.",
    ],
}

base.RESPOSTAS = {
    "recordar_pessoa": [
        "A pessoa é {atual}.",
        "{atual} é a pessoa combinada.",
    ],
    "recordar_objeto": [
        "O objeto é {objeto}.",
        "Você estava falando do {objeto}.",
    ],
    "corrigir_pessoa": [
        "Certo. Agora a pessoa é {outro}.",
        "Entendi a correção: fica {outro}.",
    ],
    "guardar_hipotese": [
        "Não. Isso ainda é uma possibilidade.",
        "Ainda não está confirmado.",
    ],
    "mensagem_sem_horario": [
        "{atual}, podemos combinar {atividade}?",
        "{atual}, você quer combinar {atividade} comigo?",
    ],
    "pedir_detalhe": [
        "O que você quer pedir a {atual}?",
        "Qual é o pedido para {atual}?",
    ],
}

# O histórico-semente também precisa ser natural; substituímos só a função de
# episódio para reaproveitar toda a auditoria/geração determinística da base.
_original = base.episodio

def episodio_natural(contexto, valores, contexto_i, preench_i, estilo_mensagem, estilo_resposta, split, episodio_id):
    saida = _original(contexto, valores, contexto_i, preench_i, estilo_mensagem, estilo_resposta, split, episodio_id)
    for ex in saida:
        for h in ex["historico"]:
            if h["papel"] == "assistente" and h["texto"].startswith("Entendi. A pessoa e "):
                h["texto"] = h["texto"].replace("Entendi. A pessoa e ", "Entendi. A pessoa é ", 1)
                h["texto"] = h["texto"].replace(", o objeto e ", ", o objeto é ", 1)
                h["texto"] = h["texto"].replace(" e a atividade e ", " e a atividade é ", 1)
    return saida

base.episodio = episodio_natural

if __name__ == "__main__":
    base.executar()
