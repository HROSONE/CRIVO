"""Congela uma prova nova antes de existir o treinador contrastivo.

Nao treina nada. A prova usa contextos e frases diferentes do corpus fatorial,
do holdout #146 e da primeira turma da Escola Cognitiva (#148).
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

DIR = Path(__file__).resolve().parent
RAIZ = DIR.parents[1]
ESCOLA = RAIZ / "experimentos" / "escola_cognitiva_20261011"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(ESCOLA))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, fonte_dialogo, tokenizar
from escola import MAPA_OPERACOES, rotulos_da_operacao, validar_escola

FATORIAL = RAIZ / "experimentos" / "corpus_fatorial_20261011" / "corpus_fatorial.json.gz"
INICIAL = RAIZ / "experimentos" / "gerador_historico_textual_20261010" / "inicializacao_sessoes.json.gz"
H146 = RAIZ / "experimentos" / "ato_auxiliar_dialogo_20261011" / "holdout_novo.json"
H148 = ESCOLA / "holdout_escola.json"

OPERACOES = tuple(MAPA_OPERACOES)
CONTEXTOS = [
    ("museu", "No museu, estou separando o {objeto} com {nome} antes de {atividade}."),
    ("quintal", "No quintal, eu e {nome} deixamos o {objeto} pronto para {atividade}."),
    ("sotao", "No sótão, estou conferindo o {objeto} com {nome} para fazer {atividade}."),
    ("galpao", "No galpão, estou preparando o {objeto} junto com {nome} para {atividade}."),
    ("salao", "No salão, organizei o {objeto} com {nome} pensando em {atividade}."),
    ("mirante", "No mirante, eu e {nome} estamos com o {objeto} antes da atividade de {atividade}."),
]
PREENCHIMENTOS = [
    dict(nome="Eloa-17", outro="Faron-28", objeto="mapa", atividade="xadrez"),
    dict(nome="Faron-28", outro="Gilda-39", objeto="caixa", atividade="costura"),
    dict(nome="Gilda-39", outro="Helio-46", objeto="cartaz", atividade="musica"),
    dict(nome="Helio-46", outro="Iris-57", objeto="agenda", atividade="caminhada"),
    dict(nome="Iris-57", outro="Eloa-17", objeto="pasta", atividade="pintura"),
]

MENSAGENS = {
    "recordar_pessoa": [
        "Identifique quem estava participando comigo nesse contexto.",
        "Qual era o nome de quem aparecia nessa situação?",
        "Quem estava associado ao que eu contei antes?",
        "Recupere a pessoa mencionada nessa conversa.",
        "De quem eu estava falando como participante?",
    ],
    "recordar_objeto": [
        "Identifique o item que fazia parte dessa situação.",
        "Qual coisa concreta eu tinha citado nesse contexto?",
        "Recupere o objeto mencionado anteriormente.",
        "Que item estava envolvido no que eu contei?",
        "Do contexto anterior, qual era o objeto?",
    ],
    "corrigir_pessoa": [
        "Faça somente esta atualização: substitua {atual} por {outro}.",
        "A pessoa mudou; considere {outro} em vez de {atual}.",
        "Revise o participante: o correto agora é {outro}, não {atual}.",
        "Atualize quem participa para {outro} e descarte {atual}.",
        "Troque apenas o nome ativo de {atual} para {outro}.",
    ],
    "guardar_hipotese": [
        "Estou cogitando {atividade}, porém ainda não decidi. Isso já é fato?",
        "{atividade} é só uma possibilidade por enquanto. Posso chamar de certeza?",
        "Talvez aconteça {atividade}; devo considerar confirmado agora?",
        "Ainda existe dúvida sobre {atividade}. Isso conta como confirmado?",
        "Estou avaliando fazer {atividade}, sem decisão final. Já aconteceu como fato?",
    ],
    "mensagem_sem_horario": [
        "Redija para {atual} um convite para {atividade} sem definir quando.",
        "Crie uma mensagem convidando {atual} para {atividade}, sem horário.",
        "Escreva um convite a {atual} sobre {atividade} e deixe o horário aberto.",
        "Prepare uma mensagem para {atual} propondo {atividade}, sem data nem hora.",
        "Convide {atual} para {atividade} sem inventar momento específico.",
    ],
    "pedir_detalhe": [
        "Quero solicitar algo a {atual}, mas ainda falta dizer exatamente o quê. Como você responde?",
        "Há um pedido para {atual}, porém o conteúdo do pedido não foi informado.",
        "Pretendo pedir alguma coisa a {atual}; qual detalhe precisa ser esclarecido primeiro?",
        "Antes de montar o pedido para {atual}, ainda não defini o que vou solicitar.",
        "Se eu só disser que quero pedir algo a {atual}, qual informação está faltando?",
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


def exemplos_de(path: Path):
    d = ler_json(path)
    return d.get("exemplos", []) if isinstance(d, dict) else d


def ordem(ci: int, pi: int):
    ops = list(OPERACOES)
    shift = (2 * ci + 3 * pi) % len(ops)
    ops = ops[shift:] + ops[:shift]
    return list(reversed(ops)) if (ci + pi) % 2 else ops


def gerar():
    saida = []
    for ci, (familia, seed) in enumerate(CONTEXTOS):
        for pi, valores in enumerate(PREENCHIMENTOS):
            historico = [
                {"papel": "usuario", "texto": seed.format(**valores)},
                {"papel": "assistente", "texto": "Entendi. A pessoa é {nome}, o objeto é {objeto} e a atividade é {atividade}.".format(**valores)},
            ]
            atual = valores["nome"]
            for turno, op in enumerate(ordem(ci, pi), 1):
                estilo = (ci + 2 * pi + turno) % 5
                estilo_r = (ci + pi + turno) % 2
                fmt = dict(valores, atual=atual)
                msg = MENSAGENS[op][estilo].format(**fmt)
                resp = RESPOSTAS[op][estilo_r].format(**fmt)
                ex = {
                    "id": f"contraste-holdout-{familia}-{pi}-{turno}",
                    "split": "prospectivo_contraste",
                    "familia": familia,
                    "turno": turno,
                    "operacao": op,
                    "professores": rotulos_da_operacao(op),
                    "mensagem": msg,
                    "historico": list(historico),
                    "resposta": resp,
                    "esperado_nome": valores["outro"] if op == "corrigir_pessoa" else atual,
                    "nome_antes": atual,
                    "objeto": valores["objeto"],
                    "atividade": valores["atividade"],
                }
                saida.append(ex)
                historico.extend([{"papel": "usuario", "texto": msg}, {"papel": "assistente", "texto": resp}])
                if op == "corrigir_pessoa":
                    atual = valores["outro"]
    return saida


def main():
    validar_escola()
    protocolo = json.loads((DIR / "protocolo.json").read_text(encoding="utf-8"))
    if sha(FATORIAL) != protocolo["fontes"]["corpus_sha256"]:
        raise SystemExit("Corpus fatorial mudou")
    if sha(INICIAL) != protocolo["fontes"]["inicializacao_sha256"]:
        raise SystemExit("Inicializacao mudou")

    novos = gerar()
    if len(novos) != 180:
        raise SystemExit(f"Esperava 180 casos; recebi {len(novos)}")
    cont = Counter(e["operacao"] for e in novos)
    if cont != Counter({op: 30 for op in OPERACOES}):
        raise SystemExit(f"Operacoes desbalanceadas: {cont}")
    if len({assinatura(e) for e in novos}) != 180:
        raise SystemExit("Duplicata interna na prova")

    conhecidos = exemplos_de(FATORIAL) + exemplos_de(H146) + exemplos_de(H148)
    sigs = {assinatura(e) for e in conhecidos}
    msgs = {e.get("mensagem", "").casefold() for e in conhecidos}
    sobre = sum(assinatura(e) in sigs for e in novos)
    msgs_rep = sum(e["mensagem"].casefold() in msgs for e in novos)

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
        "contextos": len({e["familia"] for e in novos}),
        "por_operacao": dict(sorted(cont.items())),
        "assinaturas_sobrepostas": sobre,
        "mensagens_exatas_repetidas": msgs_rep,
        "alvos_nao_geraveis": nao_geraveis,
        "aprovado": sobre == 0 and msgs_rep == 0 and not nao_geraveis,
    }
    payload = {"congelado_antes_do_treinador": True, "auditoria": auditoria, "exemplos": novos}
    out = DIR / "holdout_contraste.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifesto = {
        "aprovado": auditoria["aprovado"],
        "exemplos": len(novos),
        "holdout_sha256": sha(out),
        "gerador_sha256": sha(Path(__file__)),
        "protocolo_sha256": sha(DIR / "protocolo.json"),
    }
    (DIR / "manifesto_holdout.json").write_text(json.dumps(manifesto, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"auditoria": auditoria, "manifesto": manifesto}, ensure_ascii=False, indent=2))
    if not auditoria["aprovado"]:
        raise SystemExit("Holdout contrastivo reprovado")


if __name__ == "__main__":
    main()
