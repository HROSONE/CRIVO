"""Gera e audita a primeira prova prospectiva da Escola Cognitiva.

Este script NAO treina. Ele congela 144 casos novos e garante que nao ha
sobreposicao com o corpus fatorial nem com o holdout do PR #146. Cada caso
recebe rótulos treino-only de ACAO e FOCO.
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
sys.path.insert(0, str(DIR))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, fonte_dialogo, tokenizar
from escola import MAPA_OPERACOES, PROFESSORES, rotulos_da_operacao, validar_escola

FATORIAL = RAIZ / "experimentos" / "corpus_fatorial_20261011" / "corpus_fatorial.json.gz"
INICIAL = RAIZ / "experimentos" / "gerador_historico_textual_20261010" / "inicializacao_sessoes.json.gz"
HOLDOUT_146 = RAIZ / "experimentos" / "ato_auxiliar_dialogo_20261011" / "holdout_novo.json"

OPERACOES = tuple(MAPA_OPERACOES)
CONTEXTOS = [
    ("arquivo", "Estou revisando o {objeto} com {nome} antes da atividade de {atividade}."),
    ("jardim", "No jardim, eu e {nome} estamos cuidando do {objeto} enquanto planejamos {atividade}."),
    ("corredor", "No corredor, combinei com {nome} de levar o {objeto} para {atividade}."),
    ("patio", "No pátio, estou organizando o {objeto} com {nome} para uma atividade de {atividade}."),
    ("estudio", "No estúdio, estou separando o {objeto} com {nome} para fazer {atividade}."),
    ("terraco", "No terraço, estou preparando o {objeto} com {nome} antes de {atividade}."),
]
PREENCHIMENTOS = [
    dict(nome="Arina-81", outro="Belor-92", objeto="agenda", atividade="leitura"),
    dict(nome="Belor-92", outro="Célia-13", objeto="pasta", atividade="pintura"),
    dict(nome="Célia-13", outro="Dário-24", objeto="bilhete", atividade="revisão"),
    dict(nome="Dário-24", outro="Arina-81", objeto="chave", atividade="organização"),
]

MENSAGENS = {
    "recordar_pessoa": [
        "Qual pessoa eu tinha mencionado antes?",
        "Quem estava comigo nessa situação?",
        "Me recorde o nome da pessoa ligada a isso.",
        "Quem era a pessoa que ficou nesse contexto?",
    ],
    "recordar_objeto": [
        "Que objeto estava ligado a essa situação?",
        "Qual item eu tinha mencionado antes?",
        "Me recorde qual objeto ficou nesse contexto.",
        "Do que eu estava falando como objeto?",
    ],
    "corrigir_pessoa": [
        "Ajuste só a pessoa: troque {atual} por {outro}.",
        "Mude quem participa: agora é {outro}, não {atual}.",
        "Corrija apenas a pessoa; use {outro} no lugar de {atual}.",
        "Atualize o nome da pessoa de {atual} para {outro}.",
    ],
    "guardar_hipotese": [
        "Ainda estou pensando em {atividade}; isso já virou fato?",
        "Talvez eu faça {atividade}, mas não decidi. Está confirmado?",
        "Eu posso fazer {atividade}, só que ainda é uma ideia. Isso já é certeza?",
        "Existe a chance de eu fazer {atividade}. Posso tratar como confirmado?",
    ],
    "mensagem_sem_horario": [
        "Escreva para {atual} chamando para {atividade}, sem marcar hora.",
        "Faça um convite a {atual} para {atividade}, mas não escolha horário.",
        "Monte uma mensagem para {atual} sobre {atividade}, sem dizer quando.",
        "Quero convidar {atual} para {atividade}; escreva sem colocar horário.",
    ],
    "pedir_detalhe": [
        "Quero pedir alguma coisa a {atual}, mas não disse qual. O que falta?",
        "Vou fazer um pedido a {atual}, só que ainda não falei o que quero.",
        "Preciso pedir algo para {atual}; qual informação ainda está faltando?",
        "Quero mandar um pedido a {atual}, mas não informei o objeto do pedido.",
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
    bruto = json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(bruto).hexdigest()


def ordem(ci: int, pi: int):
    ops = list(OPERACOES)
    desloc = (ci + 2 * pi) % len(ops)
    ops = ops[desloc:] + ops[:desloc]
    return list(reversed(ops)) if (ci + pi) % 2 else ops


def gerar():
    exemplos = []
    for ci, (familia, seed_tpl) in enumerate(CONTEXTOS):
        for pi, valores in enumerate(PREENCHIMENTOS):
            hist = [
                {"papel": "usuario", "texto": seed_tpl.format(**valores)},
                {"papel": "assistente", "texto": "Entendi. A pessoa é {nome}, o objeto é {objeto} e a atividade é {atividade}.".format(**valores)},
            ]
            atual = valores["nome"]
            for turno, operacao in enumerate(ordem(ci, pi), 1):
                estilo = (2 * ci + pi + turno) % 4
                estilo_r = (ci + pi + 2 * turno) % 2
                fmt = dict(valores, atual=atual)
                mensagem = MENSAGENS[operacao][estilo].format(**fmt)
                resposta = RESPOSTAS[operacao][estilo_r].format(**fmt)
                ex = {
                    "id": f"escola-holdout-{familia}-{pi}-{turno}",
                    "split": "prospectivo_escola",
                    "familia": familia,
                    "turno": turno,
                    "operacao": operacao,
                    "professores": rotulos_da_operacao(operacao),
                    "mensagem": mensagem,
                    "historico": list(hist),
                    "resposta": resposta,
                }
                exemplos.append(ex)
                hist.extend([{"papel": "usuario", "texto": mensagem}, {"papel": "assistente", "texto": resposta}])
                if operacao == "corrigir_pessoa":
                    atual = valores["outro"]
    return exemplos


def exemplos_de(arquivo: Path):
    dados = ler_json(arquivo)
    if isinstance(dados, dict):
        return dados.get("exemplos", [])
    return dados


def main():
    validar_escola()
    protocolo = json.loads((DIR / "protocolo.json").read_text(encoding="utf-8"))
    if sha(FATORIAL) != protocolo["treino_futuro"]["corpus_sha256"]:
        raise SystemExit("Corpus fatorial mudou")
    if sha(INICIAL) != protocolo["treino_futuro"]["inicializacao_sha256"]:
        raise SystemExit("Inicialização mudou")

    novos = gerar()
    if len(novos) != 144:
        raise SystemExit(f"Holdout deveria ter 144 casos, tem {len(novos)}")
    cont_ops = Counter(e["operacao"] for e in novos)
    if cont_ops != Counter({op: 24 for op in OPERACOES}):
        raise SystemExit(f"Operações desbalanceadas: {cont_ops}")
    if len({assinatura(e) for e in novos}) != len(novos):
        raise SystemExit("Holdout contém duplicatas")

    conhecidos = exemplos_de(FATORIAL) + exemplos_de(HOLDOUT_146)
    sigs_conhecidos = {assinatura(e) for e in conhecidos}
    msgs_conhecidas = {e["mensagem"].casefold() for e in conhecidos if e.get("mensagem")}
    sobreposicao = sum(assinatura(e) in sigs_conhecidos for e in novos)
    mensagens_repetidas = sum(e["mensagem"].casefold() in msgs_conhecidas for e in novos)

    modelo = DialogoSeq2Seq(ler_json(INICIAL))
    vocab = set(modelo.vocabulario)
    nao_geraveis = []
    for e in novos:
        fonte = set(fonte_dialogo(e["mensagem"], e["historico"], modelo.limite_fonte))
        faltam = [t for t in tokenizar(e["resposta"]) + ["<fim>"] if t not in vocab and t not in fonte]
        if faltam:
            nao_geraveis.append({"id": e["id"], "tokens": faltam})

    cont_prof = {}
    for nome, professor in PROFESSORES.items():
        cont_prof[nome] = dict(sorted(Counter(e["professores"][nome] for e in novos).items()))
        if any(rot not in professor.ids for rot in cont_prof[nome]):
            raise SystemExit(f"Rótulo inválido no professor {nome}")

    auditoria = {
        "exemplos": len(novos),
        "contextos": len({e["familia"] for e in novos}),
        "por_operacao": dict(sorted(cont_ops.items())),
        "por_professor": cont_prof,
        "assinaturas_sobrepostas_com_fontes_conhecidas": sobreposicao,
        "mensagens_exatas_repetidas": mensagens_repetidas,
        "alvos_nao_geraveis": nao_geraveis,
        "aprovado": sobreposicao == 0 and mensagens_repetidas == 0 and not nao_geraveis,
    }
    saida = {
        "congelado_antes_do_treino": True,
        "escola": {nome: {"classes": list(p.classes), "peso": p.peso} for nome, p in PROFESSORES.items()},
        "auditoria": auditoria,
        "exemplos": novos,
    }
    caminho = DIR / "holdout_escola.json"
    caminho.write_text(json.dumps(saida, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifesto = {
        "aprovado": auditoria["aprovado"],
        "exemplos": len(novos),
        "holdout_sha256": sha(caminho),
        "gerador_sha256": sha(Path(__file__)),
        "protocolo_sha256": sha(DIR / "protocolo.json"),
        "escola_sha256": sha(DIR / "escola.py"),
    }
    (DIR / "manifesto_holdout.json").write_text(json.dumps(manifesto, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"auditoria": auditoria, "manifesto": manifesto}, ensure_ascii=False, indent=2))
    if not auditoria["aprovado"]:
        raise SystemExit("Prova da Escola Cognitiva não passou a auditoria")


if __name__ == "__main__":
    main()
