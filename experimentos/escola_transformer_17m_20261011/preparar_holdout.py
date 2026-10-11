#!/usr/bin/env python3
"""Gera e congela o holdout prospectivo da Escola Cognitiva do Transformer 17M.

Este arquivo NÃO importa código de treino. O conjunto usa léxico, famílias e
formulações reservadas para a prova e deve ser materializado antes de qualquer
implementação do candidato.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

SEMENTE = 20261011
OPERACOES = (
    "recordar_pessoa",
    "recordar_objeto",
    "corrigir_pessoa",
    "guardar_hipotese",
    "mensagem_sem_horario",
    "pedir_detalhe",
)
ROTULOS = {
    "recordar_pessoa": ("recordar", "pessoa"),
    "recordar_objeto": ("recordar", "objeto"),
    "corrigir_pessoa": ("atualizar", "pessoa"),
    "guardar_hipotese": ("epistemico", "nenhum"),
    "mensagem_sem_horario": ("compor", "pessoa"),
    "pedir_detalhe": ("esclarecer", "objeto"),
}
FAMILIAS = (
    ("observatorio", "no observatório", ("planisfério", "tripé", "caderno", "filtro"), ("cartografia celeste", "anotação lunar", "fotometria", "observação de meteoros")),
    ("viveiro", "no viveiro", ("regador", "etiqueta", "bandeja", "termômetro"), ("replantio", "semeadura", "catalogação", "irrigação")),
    ("oficina", "na oficina", ("paquímetro", "gabarito", "bobina", "maleta"), ("calibração", "soldagem", "montagem", "medição")),
    ("trilha", "na trilha", ("bússola", "cantil", "prancheta", "lanterna"), ("mapeamento", "fotografia", "contagem de aves", "coleta de folhas")),
    ("estudio", "no estúdio", ("metrônomo", "pedestal", "roteiro", "microfone"), ("ensaio", "narração", "mixagem", "gravação")),
)
NOMES = (
    ("Ireno-41", "Maelis-52"), ("Corael-63", "Nivara-74"),
    ("Belino-85", "Soreia-96"), ("Darian-17", "Lumea-28"),
    ("Orien-39", "Velesa-40"),
)
ORDENS = (
    OPERACOES,
    ("pedir_detalhe", "recordar_objeto", "mensagem_sem_horario", "corrigir_pessoa", "recordar_pessoa", "guardar_hipotese"),
    ("guardar_hipotese", "corrigir_pessoa", "recordar_pessoa", "pedir_detalhe", "mensagem_sem_horario", "recordar_objeto"),
    ("recordar_objeto", "mensagem_sem_horario", "guardar_hipotese", "recordar_pessoa", "corrigir_pessoa", "pedir_detalhe"),
)
FORMAS = {
    "recordar_pessoa": (
        "Na situação {lugar}, recupere só a pessoa ligada ao caso.",
        "Sem voltar ao começo do caso {lugar}, quem é a pessoa?",
        "Qual pessoa está valendo agora no contexto {lugar}?",
        "Diga apenas quem ficou associado ao caso {lugar}.",
    ),
    "recordar_objeto": (
        "Qual era o objeto associado ao caso {lugar}?",
        "No contexto {lugar}, recupere o objeto, não a pessoa.",
        "Que objeto ficou registrado na situação {lugar}?",
        "Lembre qual é o objeto do contexto {lugar}.",
    ),
    "guardar_hipotese": (
        "Estou cogitando {atividade} {lugar}, mas ainda não decidi. Isso já está confirmado?",
        "Talvez eu faça {atividade} {lugar}; por enquanto é só uma ideia. Posso tratar como certo?",
        "Considerei {atividade} {lugar}, sem fechar nada. O plano já virou confirmação?",
        "{atividade} {lugar} é uma possibilidade, não uma decisão. Está confirmado ou não?",
    ),
    "mensagem_sem_horario": (
        "Escreva uma mensagem curta para {pessoa} sobre {atividade} {lugar}, sem inventar horário.",
        "Monte um convite para {pessoa} fazer {atividade} {lugar}; não acrescente hora.",
        "Quero chamar {pessoa} para {atividade} {lugar}. Redija sem escolher horário por mim.",
        "Faça uma mensagem para {pessoa} combinando {atividade} {lugar}, mas deixe o horário em aberto.",
    ),
    "pedir_detalhe": (
        "No caso {lugar}, quero pedir algo a {pessoa}, mas ainda não disse qual coisa.",
        "Para a situação {lugar}, preciso fazer um pedido a {pessoa}; falta informar o objeto do pedido.",
        "No contexto {lugar}, vou pedir uma coisa a {pessoa}, só que não especifiquei o quê.",
        "Há um pedido para {pessoa} no caso {lugar}, porém o item pedido está faltando.",
    ),
    "corrigir_pessoa": (
        "No caso {lugar}, corrija a pessoa: {pessoa} sai e {nova} passa a valer.",
        "Atualize o responsável do contexto {lugar} de {pessoa} para {nova}.",
        "Na situação {lugar}, troque quem participa: não é mais {pessoa}; agora é {nova}.",
        "Faça uma correção de estado {lugar}: substitua {pessoa} por {nova}.",
    ),
}


def resposta(op, pessoa, nova, objeto, atividade):
    if op == "recordar_pessoa":
        return f"A pessoa é {pessoa}."
    if op == "recordar_objeto":
        return f"O objeto é {objeto}."
    if op == "corrigir_pessoa":
        return f"Atualizado: a pessoa agora é {nova}."
    if op == "guardar_hipotese":
        return f"Não. {atividade} continua apenas como possibilidade."
    if op == "mensagem_sem_horario":
        return f"{pessoa}, quer combinar {atividade} comigo?"
    if op == "pedir_detalhe":
        return f"O que você quer pedir a {pessoa}?"
    raise KeyError(op)


def gerar():
    exemplos = []
    for fidx, (familia, lugar, objetos, atividades) in enumerate(FAMILIAS):
        nome, nova = NOMES[fidx]
        for variante in range(4):
            objeto = objetos[variante]
            atividade = atividades[variante]
            pessoa = nome
            historico = [
                {"papel": "usuario", "texto": f"Estou organizando {objeto} com {pessoa} {lugar} para uma atividade de {atividade}."},
                {"papel": "assistente", "texto": f"Entendi. Pessoa: {pessoa}. Objeto: {objeto}. Atividade: {atividade}."},
            ]
            for turno, op in enumerate(ORDENS[variante], 1):
                msg = FORMAS[op][variante].format(
                    pessoa=pessoa, nova=nova, objeto=objeto, atividade=atividade, lugar=lugar)
                alvo = resposta(op, pessoa, nova, objeto, atividade)
                acao, foco = ROTULOS[op]
                exemplos.append({
                    "id": f"esc17m-v1-{familia}-{variante}-{turno}",
                    "split": "prospectivo",
                    "familia": familia,
                    "variante": variante,
                    "turno": turno,
                    "historico": [dict(x) for x in historico],
                    "mensagem": msg,
                    "resposta": alvo,
                    "operacao": op,
                    "acao": acao,
                    "foco": foco,
                })
                historico.extend([
                    {"papel": "usuario", "texto": msg},
                    {"papel": "assistente", "texto": alvo},
                ])
                if op == "corrigir_pessoa":
                    pessoa = nova
    return exemplos


def sha_json(obj):
    bruto = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(bruto).hexdigest()


def main():
    aqui = Path(__file__).resolve().parent
    exemplos = gerar()
    ids = [x["id"] for x in exemplos]
    mensagens = [x["mensagem"] for x in exemplos]
    por_op = {op: sum(x["operacao"] == op for x in exemplos) for op in OPERACOES}
    assert len(exemplos) == 120
    assert len(ids) == len(set(ids))
    assert len(mensagens) == len(set(mensagens))
    assert set(por_op.values()) == {20}
    pacote = {
        "versao": 1,
        "semente": SEMENTE,
        "congelado_antes_do_treino": True,
        "auditoria": {
            "aprovado": True,
            "exemplos": len(exemplos),
            "familias": len(FAMILIAS),
            "mensagens_exatas_repetidas": len(mensagens) - len(set(mensagens)),
            "por_operacao": por_op,
        },
        "exemplos": exemplos,
    }
    (aqui / "holdout_cognitivo_v1.json").write_text(
        json.dumps(pacote, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifesto = {
        "versao": 1,
        "congelado_antes_do_treino": True,
        "holdout_sha256_canonico": sha_json(pacote),
        "gerador_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "exemplos": len(exemplos),
        "por_operacao": por_op,
        "criterio": "não alterar este holdout depois de implementar ou executar o candidato",
    }
    (aqui / "manifesto_holdout.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifesto, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
