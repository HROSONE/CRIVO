"""Currículo sintético fatorado da Escola Cognitiva do Transformer 17M.

Os termos e formulações de treino são deliberadamente diferentes dos cinco
domínios reservados em preparar_holdout.py.
"""
from __future__ import annotations
import random

SEMENTE = 20261011
OPERACOES = (
    "recordar_pessoa", "recordar_objeto", "corrigir_pessoa",
    "guardar_hipotese", "mensagem_sem_horario", "pedir_detalhe",
)
ROTULOS = {
    "recordar_pessoa": ("recordar", "pessoa"),
    "recordar_objeto": ("recordar", "objeto"),
    "corrigir_pessoa": ("atualizar", "pessoa"),
    "guardar_hipotese": ("epistemico", "nenhum"),
    "mensagem_sem_horario": ("compor", "pessoa"),
    "pedir_detalhe": ("esclarecer", "objeto"),
}
LUGARES = (
    "na biblioteca", "no laboratório", "na cozinha", "no escritório",
    "no galpão", "na sala de aula", "no cais", "no museu",
    "no arquivo", "no jardim", "no depósito", "no auditório",
    "na recepção", "no pátio", "na sala técnica", "no corredor",
)
OBJETOS = ("chave", "envelope", "lente", "martelo", "livro", "cabo", "frasco", "régua")
ATIVIDADES = ("revisão", "desenho", "inventário", "leitura", "teste", "organização", "pesquisa", "limpeza")
ORDENS = (
    OPERACOES,
    ("corrigir_pessoa", "recordar_pessoa", "recordar_objeto", "guardar_hipotese", "pedir_detalhe", "mensagem_sem_horario"),
    ("pedir_detalhe", "guardar_hipotese", "recordar_objeto", "corrigir_pessoa", "mensagem_sem_horario", "recordar_pessoa"),
    ("recordar_objeto", "corrigir_pessoa", "mensagem_sem_horario", "recordar_pessoa", "guardar_hipotese", "pedir_detalhe"),
    ("mensagem_sem_horario", "pedir_detalhe", "corrigir_pessoa", "recordar_pessoa", "recordar_objeto", "guardar_hipotese"),
    ("guardar_hipotese", "recordar_pessoa", "pedir_detalhe", "recordar_objeto", "corrigir_pessoa", "mensagem_sem_horario"),
    ("recordar_pessoa", "guardar_hipotese", "corrigir_pessoa", "pedir_detalhe", "recordar_objeto", "mensagem_sem_horario"),
    ("pedir_detalhe", "mensagem_sem_horario", "recordar_pessoa", "guardar_hipotese", "corrigir_pessoa", "recordar_objeto"),
)
PERGUNTAS = {
    "recordar_pessoa": (
        "Quem está ligado a esse contexto?", "Recupere o nome da pessoa.",
        "Quem ficou registrado nessa situação?", "Qual é a pessoa atual?",
        "Lembre quem participa desse caso.", "Diga quem é a pessoa associada.",
        "Qual nome humano está valendo?", "Quem devo considerar como pessoa desse contexto?",
    ),
    "recordar_objeto": (
        "Qual coisa foi registrada nesse contexto?", "Recupere o objeto citado.",
        "Que objeto pertence a essa situação?", "Qual é o item atual do caso?",
        "Lembre a coisa material mencionada.", "Diga qual objeto está associado.",
        "Qual item ficou no estado da conversa?", "Que objeto devo considerar aqui?",
    ),
    "corrigir_pessoa": (
        "Mude a pessoa de {pessoa} para {nova}.", "Correção: {nova} substitui {pessoa}.",
        "Atualize quem participa; sai {pessoa}, entra {nova}.", "Troque {pessoa} por {nova} como pessoa.",
        "A pessoa anterior era {pessoa}; a nova é {nova}.", "Faça a atualização de responsável: {nova} no lugar de {pessoa}.",
        "Não use mais {pessoa}; passe a usar {nova}.", "O nome correto agora é {nova}, não {pessoa}.",
    ),
    "guardar_hipotese": (
        "Posso fazer {atividade}, mas ainda é hipótese. Já está certo?", "Talvez aconteça {atividade}. Isso conta como confirmado?",
        "Estou só considerando {atividade}. É decisão final?", "{atividade} é apenas uma possibilidade. Já devo tratar como fato?",
        "Ainda estou pensando em {atividade}. Isso já foi confirmado?", "Cogitei {atividade}, sem decisão. Está fechado?",
        "Existe a ideia de {atividade}, mas não confirmação. É certo?", "Pode ser {atividade}, porém nada foi decidido. Está confirmado?",
    ),
    "mensagem_sem_horario": (
        "Redija um convite para {pessoa} sobre {atividade} sem escolher hora.", "Escreva para {pessoa} propondo {atividade}, sem horário.",
        "Crie uma mensagem curta chamando {pessoa} para {atividade}; não invente hora.", "Convide {pessoa} para {atividade} deixando o horário aberto.",
        "Faça um texto para {pessoa} sobre fazer {atividade}, sem marcar quando.", "Escreva uma mensagem a {pessoa} combinando {atividade}, mas sem hora.",
        "Quero convidar {pessoa} para {atividade}; formule sem acrescentar horário.", "Prepare um convite simples para {pessoa} fazer {atividade}, sem horário.",
    ),
    "pedir_detalhe": (
        "Quero pedir alguma coisa a {pessoa}, mas não disse o item.", "Há um pedido para {pessoa} e falta dizer o que será pedido.",
        "Vou fazer um pedido a {pessoa}; o objeto ainda está ausente.", "Preciso pedir algo a {pessoa}, só que a coisa não foi especificada.",
        "O destinatário é {pessoa}, mas não informei o que quero pedir.", "Falta o objeto do pedido que farei a {pessoa}.",
        "Pretendo pedir uma coisa a {pessoa}; ainda não disse qual.", "Tenho um pedido para {pessoa}, porém o item não foi fornecido.",
    ),
}
RESPOSTAS = {
    "recordar_pessoa": (
        "{pessoa} é a pessoa registrada.", "A pessoa atual é {pessoa}.",
        "A pessoa desse contexto é {pessoa}.", "O nome associado é {pessoa}.",
    ),
    "recordar_objeto": (
        "{objeto} é o objeto registrado.", "O objeto atual é {objeto}.",
        "O item desse contexto é {objeto}.", "O objeto associado é {objeto}.",
    ),
    "corrigir_pessoa": (
        "Certo. A pessoa passa a ser {nova}.", "Atualizado: agora a pessoa é {nova}.",
        "Correção registrada; vale {nova}.", "Entendido. Substituí por {nova}.",
    ),
    "guardar_hipotese": (
        "Não está confirmado; {atividade} segue como possibilidade.",
        "{atividade} ainda é apenas uma hipótese, não uma confirmação.",
        "Ainda não. {atividade} continua sem confirmação.",
        "Não. A ideia de {atividade} permanece provisória.",
    ),
    "mensagem_sem_horario": (
        "{pessoa}, você topa fazer {atividade} comigo?",
        "{pessoa}, quer fazer {atividade} comigo?",
        "{pessoa}, vamos combinar {atividade}?",
        "{pessoa}, gostaria de fazer {atividade} comigo?",
    ),
    "pedir_detalhe": (
        "Qual coisa você quer pedir a {pessoa}?",
        "O que exatamente você quer pedir a {pessoa}?",
        "Que item você pretende pedir a {pessoa}?",
        "Falta dizer o que será pedido a {pessoa}; qual é o item?",
    ),
}


def _nome(indice, rodada, novo=False):
    inicios = ("Areno", "Beli", "Caio", "Dorel", "Elian", "Fira", "Galen", "Helia",
               "Isen", "Jora", "Kalen", "Mira", "Noren", "Olia", "Peren", "Rina")
    desloc = 7 if novo else 0
    base = inicios[(indice + rodada * 3 + desloc) % len(inicios)]
    numero = 100 + ((indice * 37 + rodada * 53 + desloc * 11) % 800)
    return f"{base}-{numero}"


def _resposta(op, estilo, pessoa, nova, objeto, atividade):
    return RESPOSTAS[op][estilo % len(RESPOSTAS[op])].format(
        pessoa=pessoa, nova=nova, objeto=objeto, atividade=atividade)


def gerar_treino():
    exemplos = []
    # 16 lugares x 8 variantes x 4 rodadas x 6 atos = 3072 exemplos.
    for lidx, lugar in enumerate(LUGARES):
        for variante in range(8):
            objeto = OBJETOS[(variante + lidx) % len(OBJETOS)]
            atividade = ATIVIDADES[(2 * variante + lidx) % len(ATIVIDADES)]
            for rodada in range(4):
                pessoa = _nome(lidx + variante, rodada, False)
                nova = _nome(lidx + variante, rodada, True)
                estilo = (variante + rodada + lidx) % 8
                historico = [
                    {"papel": "usuario", "texto": f"Contexto: {pessoa} está {lugar} com {objeto} para uma atividade de {atividade}."},
                    {"papel": "assistente", "texto": f"Registrado. Pessoa {pessoa}; objeto {objeto}; atividade {atividade}."},
                ]
                ordem = ORDENS[(variante + rodada) % len(ORDENS)]
                for turno, op in enumerate(ordem, 1):
                    msg = PERGUNTAS[op][estilo].format(
                        pessoa=pessoa, nova=nova, objeto=objeto, atividade=atividade)
                    resp = _resposta(op, estilo, pessoa, nova, objeto, atividade)
                    acao, foco = ROTULOS[op]
                    exemplos.append({
                        "id": f"esc17m-tr-{lidx}-{variante}-{rodada}-{turno}",
                        "historico": [dict(x) for x in historico],
                        "mensagem": msg,
                        "resposta": resp,
                        "operacao": op,
                        "acao": acao,
                        "foco": foco,
                    })
                    historico.extend([
                        {"papel": "usuario", "texto": msg},
                        {"papel": "assistente", "texto": resp},
                    ])
                    if op == "corrigir_pessoa":
                        pessoa = nova
    assert len(exemplos) == 3072
    assert len({x["id"] for x in exemplos}) == len(exemplos)
    por_op = {op: sum(x["operacao"] == op for x in exemplos) for op in OPERACOES}
    assert set(por_op.values()) == {512}
    random.Random(SEMENTE).shuffle(exemplos)
    return exemplos


if __name__ == "__main__":
    xs = gerar_treino()
    from collections import Counter
    print(len(xs), Counter(x["operacao"] for x in xs))
