"""Congela a prova prospectiva da aula de consistencia representacional.

Este arquivo NAO treina. Gera 180 casos novos, verifica balanceamento,
sobreposicao com fontes conhecidas e gerabilidade dos alvos, e grava um SHA
antes de existir qualquer treinador desta aula.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

DIR = Path(__file__).resolve().parent
RAIZ = DIR.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "experimentos" / "escola_cognitiva_20261011"))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, fonte_dialogo, tokenizar
from escola import MAPA_OPERACOES, rotulos_da_operacao, validar_escola

FATORIAL = RAIZ / "experimentos" / "corpus_fatorial_20261011" / "corpus_fatorial.json.gz"
INICIAL = RAIZ / "experimentos" / "gerador_historico_textual_20261010" / "inicializacao_sessoes.json.gz"
H146 = RAIZ / "experimentos" / "ato_auxiliar_dialogo_20261011" / "holdout_novo.json"
H148 = RAIZ / "experimentos" / "escola_cognitiva_20261011" / "holdout_escola.json"
H149 = RAIZ / "experimentos" / "escola_contrastiva_20261011" / "holdout_contraste.json"

OPERACOES = tuple(MAPA_OPERACOES)
CONTEXTOS = [
    ("observatorio", "No observatorio, {nome} deixou o {objeto} comigo antes de {atividade}."),
    ("deposito", "No deposito, eu e {nome} separamos o {objeto} para {atividade}."),
    ("varanda_nova", "Na varanda, {nome} trouxe o {objeto} enquanto falavamos de {atividade}."),
    ("sala_musica", "Na sala de musica, combinei com {nome} de usar o {objeto} em {atividade}."),
    ("horta", "Na horta, {nome} guardou o {objeto} antes de {atividade}."),
    ("garagem_nova", "Na garagem, eu e {nome} deixamos o {objeto} pronto para {atividade}."),
]
PREENCHIMENTOS = [
    dict(nome="Alvena-31", outro="Breno-42", objeto="caderno", atividade="leitura"),
    dict(nome="Breno-42", outro="Celina-53", objeto="livro", atividade="revisao"),
    dict(nome="Celina-53", outro="Dario-64", objeto="mapa", atividade="desenho"),
    dict(nome="Dario-64", outro="Elena-75", objeto="chave", atividade="organizacao"),
    dict(nome="Elena-75", outro="Alvena-31", objeto="cartaz", atividade="pintura"),
]
MENSAGENS = {
    "recordar_pessoa": [
        "Quem era a pessoa ligada ao que eu contei?",
        "Qual pessoa estava nessa historia comigo?",
        "Recupere quem eu tinha mencionado nesse contexto.",
        "De quem eu estava falando nessa situacao?",
        "Qual era o nome da pessoa desse caso?",
    ],
    "recordar_objeto": [
        "Qual objeto fazia parte do que eu contei?",
        "Que item estava presente nessa historia?",
        "Recupere o objeto mencionado nesse contexto.",
        "Qual era a coisa concreta dessa situacao?",
        "Que objeto eu tinha citado nesse caso?",
    ],
    "corrigir_pessoa": [
        "Corrija somente quem participa: agora e {outro}, nao {atual}.",
        "Troque a pessoa mencionada por {outro}.",
        "Atualize apenas o nome: use {outro} no lugar de {atual}.",
        "A pessoa correta passou a ser {outro}; ajuste isso.",
        "Substitua {atual} por {outro} como pessoa desse contexto.",
    ],
    "guardar_hipotese": [
        "Estou considerando {atividade}, mas ainda nao decidi. Isso e fato?",
        "Talvez eu faca {atividade}; posso tratar como confirmado?",
        "{atividade} ainda e so uma possibilidade. Ja virou certeza?",
        "Penso em fazer {atividade}, sem decisao final. Esta confirmado?",
        "Existe a chance de {atividade}, mas nada foi decidido. E certeza?",
    ],
    "mensagem_sem_horario": [
        "Escreva para {atual} propondo {atividade}, sem indicar horario.",
        "Monte um convite a {atual} para {atividade}, sem escolher quando.",
        "Crie uma mensagem para {atual} sobre {atividade}, sem marcar hora.",
        "Convide {atual} para {atividade}, mas deixe o horario em aberto.",
        "Escreva um convite para {atual} fazer {atividade}, sem hora definida.",
    ],
    "pedir_detalhe": [
        "Quero pedir algo a {atual}, mas ainda nao disse o que. O que falta?",
        "Vou fazer um pedido para {atual}, sem informar qual pedido. Pergunte o que falta.",
        "Preciso pedir uma coisa a {atual}, mas o conteudo do pedido nao foi dado.",
        "Quero solicitar algo a {atual}; qual detalhe ainda preciso dizer?",
        "Tenho um pedido para {atual}, mas nao falei qual e. O que voce precisa saber?",
    ],
}
RESPOSTAS = {
    "recordar_pessoa": ["A pessoa é {atual}.", "{atual} é a pessoa."],
    "recordar_objeto": ["O objeto é {objeto}.", "Você estava falando do {objeto}."],
    "corrigir_pessoa": ["Certo. Agora a pessoa é {outro}.", "Entendi. Agora fica {outro}."],
    "guardar_hipotese": ["Ainda não está confirmado.", "Não. Isso ainda é uma possibilidade."],
    "mensagem_sem_horario": ["{atual}, podemos combinar {atividade}?", "{atual}, você quer combinar {atividade} comigo?"],
    "pedir_detalhe": ["O que você quer pedir a {atual}?", "Qual é o pedido para {atual}?"],
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def assinatura(ex) -> str:
    base = {"mensagem": ex["mensagem"], "historico": ex.get("historico", []), "resposta": ex["resposta"]}
    return hashlib.sha256(json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def ordem(ci: int, pi: int):
    ops = list(OPERACOES)
    d = (2 * ci + 3 * pi + 1) % len(ops)
    ops = ops[d:] + ops[:d]
    if (ci * 3 + pi) % 2:
        ops.reverse()
    return ops


def gerar():
    saida = []
    for ci, (familia, seed_tpl) in enumerate(CONTEXTOS):
        for pi, valores in enumerate(PREENCHIMENTOS):
            hist = [
                {"papel": "usuario", "texto": seed_tpl.format(**valores)},
                {"papel": "assistente", "texto": "Entendi. A pessoa e {nome}, o objeto e {objeto} e a atividade e {atividade}.".format(**valores)},
            ]
            atual = valores["nome"]
            for turno, op in enumerate(ordem(ci, pi), 1):
                estilo = (ci + 2 * pi + turno) % 5
                estilo_r = (ci + pi + turno) % 2
                fmt = dict(valores, atual=atual)
                msg = MENSAGENS[op][estilo].format(**fmt)
                resp = RESPOSTAS[op][estilo_r].format(**fmt)
                ex = {
                    "id": f"consistencia-{familia}-{pi}-{turno}",
                    "split": "prospectivo_consistencia",
                    "familia": familia,
                    "turno": turno,
                    "operacao": op,
                    "professores": rotulos_da_operacao(op),
                    "mensagem": msg,
                    "historico": list(hist),
                    "resposta": resp,
                }
                saida.append(ex)
                hist += [{"papel": "usuario", "texto": msg}, {"papel": "assistente", "texto": resp}]
                if op == "corrigir_pessoa":
                    atual = valores["outro"]
    return saida


def exemplos(path: Path):
    dados = ler_json(path)
    return dados.get("exemplos", []) if isinstance(dados, dict) else dados


def main():
    validar_escola()
    novos = gerar()
    if len(novos) != 180:
        raise SystemExit(f"Esperados 180 casos, obtidos {len(novos)}")
    por_op = Counter(e["operacao"] for e in novos)
    if por_op != Counter({op: 30 for op in OPERACOES}):
        raise SystemExit(f"Desbalanceado: {por_op}")
    if len({assinatura(e) for e in novos}) != 180:
        raise SystemExit("Duplicata interna")

    conhecidos = exemplos(FATORIAL) + exemplos(H146) + exemplos(H148) + exemplos(H149)
    sigs = {assinatura(e) for e in conhecidos}
    msgs = {str(e.get("mensagem", "")).casefold() for e in conhecidos}
    sobre = sum(assinatura(e) in sigs for e in novos)
    repetidas = sum(e["mensagem"].casefold() in msgs for e in novos)

    modelo = DialogoSeq2Seq(ler_json(INICIAL))
    vocab = set(modelo.vocabulario)
    nao_geraveis = []
    for e in novos:
        fonte = set(fonte_dialogo(e["mensagem"], e["historico"], modelo.limite_fonte))
        faltam = [t for t in tokenizar(e["resposta"]) + ["<fim>"] if t not in vocab and t not in fonte]
        if faltam:
            nao_geraveis.append({"id": e["id"], "tokens": faltam})

    auditoria = {
        "exemplos": 180,
        "por_operacao": dict(sorted(por_op.items())),
        "assinaturas_sobrepostas": sobre,
        "mensagens_repetidas": repetidas,
        "alvos_nao_geraveis": nao_geraveis,
        "aprovado": sobre == 0 and repetidas == 0 and not nao_geraveis,
    }
    destino = DIR / "holdout_consistencia.json"
    destino.write_text(json.dumps({"congelado_antes_do_treinador": True, "auditoria": auditoria, "exemplos": novos}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifesto = {
        "aprovado": auditoria["aprovado"],
        "exemplos": 180,
        "holdout_sha256": sha(destino),
        "gerador_sha256": sha(Path(__file__)),
        "protocolo_sha256": sha(DIR / "protocolo.json"),
    }
    (DIR / "manifesto_holdout.json").write_text(json.dumps(manifesto, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"auditoria": auditoria, "manifesto": manifesto}, ensure_ascii=False, indent=2))
    if not auditoria["aprovado"]:
        raise SystemExit("Holdout de consistencia reprovou auditoria")


if __name__ == "__main__":
    main()