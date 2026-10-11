"""Gera e audita o holdout prospectivo do experimento de ato auxiliar.

Este script NAO treina. Ele apenas materializa 144 casos novos, verifica
sobreposicao com o corpus fatorial e confirma que os alvos sao representaveis
pelo vocabulario/copia do checkpoint inicial.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

DIR = Path(__file__).resolve().parent
RAIZ = DIR.parents[1]
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, fonte_dialogo, tokenizar

FATORIAL = RAIZ / "experimentos" / "corpus_fatorial_20261011" / "corpus_fatorial.json.gz"
INICIAL = RAIZ / "experimentos" / "gerador_historico_textual_20261010" / "inicializacao_sessoes.json.gz"

ATOS = (
    "recordar_pessoa", "recordar_objeto", "corrigir_pessoa",
    "guardar_hipotese", "mensagem_sem_horario", "pedir_detalhe",
)
CONTEXTOS = [
    ("garagem", "Estou separando o {objeto} com {nome} na garagem para uma atividade de {atividade}."),
    ("varanda", "Na varanda, estou organizando o {objeto} com {nome} para fazer {atividade}."),
    ("deposito", "Estou conferindo o {objeto} com {nome} no deposito antes de {atividade}."),
    ("estacao", "Na estacao, estou combinando com {nome} uma tarefa sobre {objeto} e {atividade}."),
    ("laboratorio", "Estou preparando o {objeto} com {nome} no laboratorio para praticar {atividade}."),
    ("quintal", "No quintal, estou cuidando do {objeto} com {nome} enquanto planejo {atividade}."),
]
PREENCHIMENTOS = [
    dict(nome="Zamira-18", outro="Taleno-27", objeto="mapa", atividade="xadrez"),
    dict(nome="Taleno-27", outro="Rivela-36", objeto="caixa", atividade="costura"),
    dict(nome="Rivela-36", outro="Soleno-45", objeto="cartaz", atividade="musica"),
    dict(nome="Soleno-45", outro="Zamira-18", objeto="caderno", atividade="caminhada"),
]
MENSAGENS = {
    "recordar_pessoa": [
        "Quem estava participando disso comigo?",
        "Qual era o nome ligado a essa situacao?",
        "Me diga qual pessoa ficou nessa historia.",
        "Quem eu tinha mencionado como a pessoa daqui?",
    ],
    "recordar_objeto": [
        "Qual coisa ficou como objeto aqui?",
        "Que item eu tinha mencionado nessa situacao?",
        "Me lembra o objeto que estava envolvido.",
        "Qual era mesmo o objeto dessa historia?",
    ],
    "corrigir_pessoa": [
        "Mude so a pessoa: no lugar de {atual}, considere {outro}.",
        "A pessoa mudou; troque {atual} por {outro}.",
        "Corrija apenas o nome: agora a pessoa e {outro}.",
        "Atualize quem participa: passa de {atual} para {outro}.",
    ],
    "guardar_hipotese": [
        "Estou considerando fazer {atividade}, mas nao decidi. Isso ja conta como certo?",
        "Talvez eu faca {atividade}. Posso tratar isso como confirmado?",
        "Eu pensei em {atividade}, sem decidir ainda. Isso virou fato?",
        "Existe a chance de eu fazer {atividade}; ja esta confirmado?",
    ],
    "mensagem_sem_horario": [
        "Escreva um convite para {atual} sobre {atividade}, sem marcar hora.",
        "Monte uma mensagem para {atual} chamando para {atividade}, mas sem horario.",
        "Quero convidar {atual} para {atividade}; escreva sem escolher quando.",
        "Faca uma mensagem curta para {atual} sobre {atividade}, sem colocar horario.",
    ],
    "pedir_detalhe": [
        "Quero pedir algo a {atual}, mas ainda nao disse qual item. O que falta?",
        "Vou fazer um pedido para {atual}, so que nao falei o que quero pedir.",
        "Preciso pedir uma coisa a {atual}; ainda falta dizer qual coisa.",
        "Quero mandar um pedido a {atual}, mas o objeto do pedido nao foi informado.",
    ],
}
RESPOSTAS = {
    "recordar_pessoa": ["A pessoa e {atual}.", "{atual} e a pessoa."],
    "recordar_objeto": ["O objeto e {objeto}.", "Voce estava falando do {objeto}."],
    "corrigir_pessoa": ["Certo. Agora a pessoa e {outro}.", "Entendi. Agora fica {outro}."],
    "guardar_hipotese": ["Ainda nao esta confirmado.", "Nao. Isso ainda e uma possibilidade."],
    "mensagem_sem_horario": ["{atual}, podemos combinar {atividade}?", "{atual}, voce quer combinar {atividade} comigo?"],
    "pedir_detalhe": ["O que voce quer pedir a {atual}?", "Qual e o pedido para {atual}?"],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assinatura(ex) -> str:
    base = {"mensagem": ex["mensagem"], "historico": ex.get("historico", []), "resposta": ex["resposta"]}
    return hashlib.sha256(json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def ordem(ci: int, pi: int):
    atos = list(ATOS)
    desloc = (2 * ci + pi) % len(atos)
    atos = atos[desloc:] + atos[:desloc]
    return list(reversed(atos)) if (ci + pi) % 2 else atos


def gerar():
    exemplos = []
    for ci, (familia, seed_tpl) in enumerate(CONTEXTOS):
        for pi, valores in enumerate(PREENCHIMENTOS):
            hist = [
                {"papel": "usuario", "texto": seed_tpl.format(**valores)},
                {"papel": "assistente", "texto": "Entendi. A pessoa e {nome}, o objeto e {objeto} e a atividade e {atividade}.".format(**valores)},
            ]
            atual = valores["nome"]
            for turno, ato in enumerate(ordem(ci, pi), 1):
                estilo = (ci + pi + turno) % 4
                estilo_r = (ci + 2*pi + turno) % 2
                fmt = dict(valores, atual=atual)
                mensagem = MENSAGENS[ato][estilo].format(**fmt)
                resposta = RESPOSTAS[ato][estilo_r].format(**fmt)
                ex = {
                    "id": f"atoaux-holdout-{familia}-{pi}-{turno}",
                    "split": "prospectivo",
                    "familia": familia,
                    "turno": turno,
                    "operacao": ato,
                    "mensagem": mensagem,
                    "historico": list(hist),
                    "resposta": resposta,
                }
                exemplos.append(ex)
                hist.extend([{"papel": "usuario", "texto": mensagem}, {"papel": "assistente", "texto": resposta}])
                if ato == "corrigir_pessoa":
                    atual = valores["outro"]
    return exemplos


def main():
    protocolo = json.loads((DIR / "protocolo.json").read_text(encoding="utf-8"))
    if sha(FATORIAL) != protocolo["treino"]["corpus_sha256"] or sha(INICIAL) != protocolo["treino"]["inicializacao_sha256"]:
        raise SystemExit("Fonte do experimento mudou")
    novos = gerar()
    if len(novos) != 144 or Counter(e["operacao"] for e in novos) != Counter({a: 24 for a in ATOS}):
        raise SystemExit("Holdout nao esta balanceado em 144 casos")
    if len({assinatura(e) for e in novos}) != len(novos):
        raise SystemExit("Holdout contem duplicatas")

    corpus = ler_json(FATORIAL)
    anteriores = corpus["exemplos"] if isinstance(corpus, dict) else corpus
    assinaturas_anteriores = {assinatura(e) for e in anteriores}
    sobreposicao = sum(assinatura(e) in assinaturas_anteriores for e in novos)
    mensagens_antigas = {e["mensagem"].casefold() for e in anteriores}
    mensagens_repetidas = sum(e["mensagem"].casefold() in mensagens_antigas for e in novos)

    modelo = DialogoSeq2Seq(ler_json(INICIAL))
    vocab = set(modelo.vocabulario)
    nao_geraveis = []
    for e in novos:
        fonte = set(fonte_dialogo(e["mensagem"], e["historico"], modelo.limite_fonte))
        faltam = [t for t in tokenizar(e["resposta"]) + ["<fim>"] if t not in vocab and t not in fonte]
        if faltam:
            nao_geraveis.append({"id": e["id"], "tokens": faltam})

    auditoria = {
        "exemplos": len(novos),
        "por_operacao": dict(sorted(Counter(e["operacao"] for e in novos).items())),
        "contextos": len({e["familia"] for e in novos}),
        "assinaturas_sobrepostas_com_corpus": sobreposicao,
        "mensagens_exatas_repetidas": mensagens_repetidas,
        "alvos_nao_geraveis": nao_geraveis,
        "aprovado": sobreposicao == 0 and mensagens_repetidas == 0 and not nao_geraveis,
    }
    saida = {"congelado_antes_do_treino": True, "exemplos": novos, "auditoria": auditoria}
    caminho = DIR / "holdout_novo.json"
    caminho.write_text(json.dumps(saida, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifesto = {
        "holdout_sha256": sha(caminho),
        "gerador_sha256": sha(Path(__file__)),
        "protocolo_sha256": sha(DIR / "protocolo.json"),
        "exemplos": len(novos),
        "aprovado": auditoria["aprovado"],
    }
    (DIR / "manifesto_holdout.json").write_text(json.dumps(manifesto, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"auditoria": auditoria, "manifesto": manifesto}, ensure_ascii=False, indent=2))
    if not auditoria["aprovado"]:
        raise SystemExit("Holdout novo nao passou auditoria")


if __name__ == "__main__":
    main()
