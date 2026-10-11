"""Constrói e audita corpus fatorial sem treinar o modelo.

O objetivo é remover o atalho familia+turno observado no PR #144:
- mesma quantidade total de treino (3699);
- mesmos 999 replay_legado e 14 apoios lexicais;
- 2686 exemplos de sessão substituídos por composição fatorial;
- nenhuma troca de vocabulário, arquitetura ou peso;
- desenvolvimento fatorial e avaliação final usam contextos não vistos no treino.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR = Path(__file__).resolve().parent
ANT = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, fonte_dialogo, tokenizar


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar_json(path: Path, dados) -> None:
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def gravar_gz(path: Path, dados) -> None:
    bruto = (json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    path.write_bytes(gzip.compress(bruto, mtime=0))


# O contexto muda; as operações se repetem e são permutadas dentro de cada
# família por preenchimento/realização, para familia+turno não identificar ato.
CONTEXTOS_TREINO = [
    ("entrega", "Estou organizando a entrega do {objeto} para {nome} em {lugar}."),
    ("emprestimo", "Estou usando o {objeto} que {nome} me emprestou em {lugar}."),
    ("convite", "Quero combinar {atividade} com {nome} em {lugar}."),
    ("revisao", "Estou revisando um {objeto} com {nome} em {lugar}."),
    ("organizacao", "Estou organizando o {objeto} com {nome} em {lugar}."),
    ("pratica", "Estou praticando {atividade} com {nome} em {lugar}."),
    ("mensagem", "Estou preparando uma mensagem sobre {objeto} para {nome}."),
    ("projeto", "Estou fazendo um projeto sobre {objeto} com {nome}."),
    ("estudo", "Estou estudando {objeto} com {nome} em {lugar}."),
    ("conserto", "Estou tentando consertar o {objeto} com {nome} em {lugar}."),
    ("cuidado", "Estou cuidando do {objeto} com {nome} em {lugar}."),
    ("planejamento", "Estou planejando {atividade} com {nome} em {lugar}."),
    ("leitura", "Estou lendo sobre {objeto} com {nome} em {lugar}."),
    ("desenho", "Estou desenhando um {objeto} com {nome} em {lugar}."),
    ("arrumacao", "Estou arrumando o {objeto} com {nome} em {lugar}."),
    ("aviso", "Estou preparando um aviso sobre {objeto} para {nome}."),
]
CONTEXTOS_DEV = [
    ("cozinha", "Estou preparando o {objeto} com {nome} na cozinha."),
    ("jardim", "Estou cuidando do {objeto} com {nome} no jardim."),
]
CONTEXTOS_FINAL = [
    ("biblioteca", "Estou preparando uma atividade sobre {objeto} com {nome} na biblioteca."),
    ("oficina", "Estou montando o {objeto} com {nome} na oficina."),
    ("visita", "Estou planejando uma visita com {nome} para ver {objeto}."),
    ("aula", "Estou preparando uma explicação sobre {objeto} para {nome}."),
]

PREENCHIMENTOS_TREINO = [
    dict(nome="Lia", outro="Caio", objeto="caderno", atividade="leitura", lugar="casa"),
    dict(nome="Caio", outro="Nara", objeto="livro", atividade="escrita", lugar="sala"),
    dict(nome="Nara", outro="Davi", objeto="texto", atividade="fotografia", lugar="escola"),
    dict(nome="Davi", outro="Bia", objeto="desenho", atividade="desenho", lugar="biblioteca"),
    dict(nome="Bia", outro="Rui", objeto="radio", atividade="pintura", lugar="oficina"),
    dict(nome="Rui", outro="Teo", objeto="vaso", atividade="jardinagem", lugar="cozinha"),
    dict(nome="Teo", outro="Mila", objeto="convite", atividade="revisao", lugar="praca"),
    dict(nome="Mila", outro="Lia", objeto="projeto", atividade="organizacao", lugar="quarto"),
]
PREENCHIMENTOS_DEV = [
    dict(nome="Iara", outro="Lino", objeto="caderno", atividade="escrita", lugar="sala"),
    dict(nome="Lino", outro="Noa", objeto="livro", atividade="leitura", lugar="casa"),
    dict(nome="Noa", outro="Sara", objeto="texto", atividade="desenho", lugar="escola"),
    dict(nome="Sara", outro="Iara", objeto="vaso", atividade="jardinagem", lugar="praca"),
]
PREENCHIMENTOS_FINAL = [
    dict(nome="Nubira-41", outro="Ocrelio-52", objeto="caderno", atividade="leitura", lugar="sala"),
    dict(nome="Ocrelio-52", outro="Velina-63", objeto="livro", atividade="escrita", lugar="casa"),
    dict(nome="Velina-63", outro="Darino-74", objeto="texto", atividade="fotografia", lugar="escola"),
    dict(nome="Darino-74", outro="Nubira-41", objeto="projeto", atividade="desenho", lugar="praca"),
]

OPERACOES = (
    "recordar_pessoa",
    "recordar_objeto",
    "corrigir_pessoa",
    "guardar_hipotese",
    "mensagem_sem_horario",
    "pedir_detalhe",
)

MENSAGENS = {
    "recordar_pessoa": [
        "Quem ficou ligado a isso?",
        "Qual pessoa esta combinada aqui?",
        "Me lembra quem e a pessoa.",
        "Quem e a pessoa nessa situacao?",
    ],
    "recordar_objeto": [
        "Qual era o objeto mesmo?",
        "Do que eu estava falando?",
        "Me lembra qual e o objeto.",
        "Que objeto ficou nessa situacao?",
    ],
    "corrigir_pessoa": [
        "Correcao: agora e {outro}, nao {atual}.",
        "Troque a pessoa: fica {outro} no lugar de {atual}.",
        "Mude isso: a pessoa correta e {outro}.",
        "Atualizacao: use {outro} como a pessoa.",
    ],
    "guardar_hipotese": [
        "Talvez eu faca {atividade} amanha. Isso ja esta certo?",
        "Estou pensando em {atividade}, mas ainda nao decidi. Posso tratar como fato?",
        "Se eu talvez fizer {atividade}, ja posso dizer que aconteceu?",
        "Existe a possibilidade de eu fazer {atividade}. Isso esta confirmado?",
    ],
    "mensagem_sem_horario": [
        "Escreva uma mensagem para {atual} sobre {atividade}, sem escolher horario.",
        "Quero convidar {atual} para {atividade}, mas nao invente horario.",
        "Faca um convite para {atual} sobre {atividade}; nao coloque horario.",
        "Escreva para {atual} sobre {atividade}, sem dizer quando.",
    ],
    "pedir_detalhe": [
        "Quero pedir uma coisa a {atual}, mas nao disse o que.",
        "Preciso escrever um pedido para {atual}; ainda falta dizer o objeto.",
        "Quero fazer um pedido a {atual}, mas esta faltando o que vou pedir.",
        "Vou pedir algo a {atual}; ainda nao falei qual coisa.",
    ],
}

RESPOSTAS = {
    "recordar_pessoa": [
        "A pessoa e {atual}.",
        "{atual} e a pessoa combinada.",
    ],
    "recordar_objeto": [
        "O objeto e {objeto}.",
        "Voce estava falando do {objeto}.",
    ],
    "corrigir_pessoa": [
        "Certo. Agora a pessoa e {outro}.",
        "Entendi a correcao: fica {outro}.",
    ],
    "guardar_hipotese": [
        "Nao. Isso ainda e uma possibilidade.",
        "Ainda nao esta confirmado.",
    ],
    "mensagem_sem_horario": [
        "{atual}, podemos combinar {atividade}?",
        "Podemos combinar {atividade}, {atual}?",
    ],
    "pedir_detalhe": [
        "O que voce quer pedir a {atual}?",
        "Qual e o pedido para {atual}?",
    ],
}


def ordem_operacoes(contexto_i: int, preench_i: int, estilo_mensagem: int) -> list[str]:
    base = list(OPERACOES)
    desloc = (contexto_i + 2 * preench_i + 3 * estilo_mensagem) % len(base)
    ordem = base[desloc:] + base[:desloc]
    if (contexto_i + preench_i + estilo_mensagem) % 2:
        ordem = list(reversed(ordem))
    return ordem


def episodio(contexto, valores, contexto_i, preench_i, estilo_mensagem, estilo_resposta, split, episodio_id):
    familia, seed_tpl = contexto
    seed_usuario = seed_tpl.format(**valores)
    seed_assistente = "Entendi. A pessoa e {nome}, o objeto e {objeto} e a atividade e {atividade}.".format(**valores)
    historico = [
        {"papel": "usuario", "texto": seed_usuario},
        {"papel": "assistente", "texto": seed_assistente},
    ]
    atual = valores["nome"]
    saida = []
    for turno, op in enumerate(ordem_operacoes(contexto_i, preench_i, estilo_mensagem), 1):
        fmt = dict(valores, atual=atual)
        mensagem = MENSAGENS[op][estilo_mensagem].format(**fmt)
        resposta = RESPOSTAS[op][estilo_resposta].format(**fmt)
        ex = {
            "id": f"fatorial-{split}-{episodio_id}-{turno}-{estilo_resposta}",
            "familia": familia,
            "grupo": "fatorial_cruzado",
            "split": split,
            "mensagem": mensagem,
            "historico": list(historico),
            "resposta": resposta,
            "episodio": episodio_id,
            "turno": turno,
            "operacao": op,
            "esperado_nome": valores["outro"] if op == "corrigir_pessoa" else atual,
            "nome_antes": atual,
            "objeto": valores["objeto"],
            "atividade": valores["atividade"],
        }
        saida.append(ex)
        historico.extend([
            {"papel": "usuario", "texto": mensagem},
            {"papel": "assistente", "texto": resposta},
        ])
        if op == "corrigir_pessoa":
            atual = valores["outro"]
    return saida


def gerar_treino():
    candidatos = []
    for ci, contexto in enumerate(CONTEXTOS_TREINO):
        for pi, valores in enumerate(PREENCHIMENTOS_TREINO):
            for em in (0, 1):
                for er in (0, 1):
                    eid = f"{contexto[0]}-{pi}-m{em}-r{er}"
                    candidatos.extend(episodio(contexto, valores, ci, pi, em, er, "treino", eid))
    # 3072 candidatos. Seleção por hash, não por família/turno/operação.
    candidatos.sort(key=lambda e: hashlib.sha256(e["id"].encode()).hexdigest())
    return candidatos[:2686], candidatos


def gerar_dev():
    saida = []
    for ci, contexto in enumerate(CONTEXTOS_DEV, start=len(CONTEXTOS_TREINO)):
        for pi, valores in enumerate(PREENCHIMENTOS_DEV):
            er = (ci + pi) % 2
            eid = f"{contexto[0]}-{pi}-dev"
            saida.extend(episodio(contexto, valores, ci, pi, 2, er, "validacao", eid))
    return saida  # 2*4*6 = 48


def gerar_final():
    saida = []
    for ci, contexto in enumerate(CONTEXTOS_FINAL, start=len(CONTEXTOS_TREINO) + len(CONTEXTOS_DEV)):
        for pi, valores in enumerate(PREENCHIMENTOS_FINAL):
            er = (ci + pi + 1) % 2
            eid = f"{contexto[0]}-{pi}-final"
            saida.extend(episodio(contexto, valores, ci, pi, 3, er, "avaliacao_final", eid))
    return saida  # 4*4*6 = 96


def entropia(cont):
    n = sum(cont.values())
    if not n:
        return 0.0
    return -sum((v/n) * math.log2(v/n) for v in cont.values() if v)


def nmi(exemplos, x_fn, y_fn):
    y = Counter(y_fn(e) for e in exemplos)
    hy = entropia(y)
    grupos = defaultdict(list)
    for e in exemplos:
        grupos[x_fn(e)].append(e)
    n = len(exemplos)
    hyx = 0.0
    for es in grupos.values():
        hyx += len(es)/n * entropia(Counter(y_fn(e) for e in es))
    return (hy - hyx) / hy if hy else 0.0


def prefixo(e, n):
    t = [x.casefold() for x in tokenizar(e["resposta"])]
    return tuple(t[:n])


def auditar_fatorial(treino):
    por_prefixo_familias = defaultdict(set)
    for e in treino:
        por_prefixo_familias[prefixo(e, 2)].add(e["familia"])
    pouco = sum(1 for e in treino if len(por_prefixo_familias[prefixo(e, 2)]) <= 2)
    pos = defaultdict(set)
    for e in treino:
        pos[e["operacao"]].add(int(e["turno"]))
    return {
        "nmi_abertura_familia_turno": nmi(treino, lambda e:(e["familia"],e["turno"]), lambda e:prefixo(e,1)),
        "nmi_prefixo2_familia_turno": nmi(treino, lambda e:(e["familia"],e["turno"]), lambda e:prefixo(e,2)),
        "fracao_prefixo2_em_ate_duas_familias": pouco/len(treino),
        "operacoes_posicoes": {k: sorted(v) for k,v in sorted(pos.items())},
        "todas_operacoes_em_todas_posicoes": all(v == set(range(1,7)) for v in pos.values()) and set(pos) == set(OPERACOES),
        "familias": len(set(e["familia"] for e in treino)),
        "operacoes": dict(Counter(e["operacao"] for e in treino)),
        "turnos": dict(Counter(e["turno"] for e in treino)),
    }


def alvos_nao_geraveis(exemplos, modelo):
    vocab = set(modelo.vocabulario)
    erros = []
    for e in exemplos:
        fonte = set(fonte_dialogo(e["mensagem"], e.get("historico", []), modelo.limite_fonte))
        for t in tokenizar(e["resposta"]):
            if t not in vocab and t not in fonte:
                erros.append({"id": e["id"], "token": t, "operacao": e.get("operacao")})
    return erros


def executar():
    protocolo = ler_json(DIR / "protocolo.json")
    origem = ANT / "corpus_sessoes.json.gz"
    inicial = ANT / "inicializacao_sessoes.json.gz"
    if sha256(origem) != protocolo["origem"]["corpus_sha256"]:
        raise ValueError("corpus original mudou")
    if sha256(inicial) != protocolo["origem"]["inicializacao_sha256"]:
        raise ValueError("inicializacao original mudou")

    antigo = ler_json(origem)
    replay = [e for e in antigo["exemplos"] if e.get("split") == "treino" and e.get("grupo") == "replay_legado"]
    apoio = [e for e in antigo["exemplos"] if e.get("split") == "treino" and e.get("grupo") == "apoio_lexical"]
    validacao_antiga = [e for e in antigo["exemplos"] if e.get("split") == "validacao" and e.get("grupo") != "sessao_completa"]
    if (len(replay), len(apoio), len(validacao_antiga)) != (999, 14, 334):
        raise ValueError(f"recortes originais mudaram: {(len(replay),len(apoio),len(validacao_antiga))}")

    treino_fatorial, candidatos = gerar_treino()
    dev_fatorial = gerar_dev()
    final = gerar_final()
    esperado = protocolo["contagens"]
    if len(treino_fatorial) != esperado["treino_fatorial"] or len(dev_fatorial) != esperado["validacao_fatorial"] or len(final) != esperado["avaliacao_final_fatorial"]:
        raise ValueError("contagens fatoriais inesperadas")

    modelo = DialogoSeq2Seq(ler_json(inicial))
    erros = alvos_nao_geraveis(treino_fatorial + dev_fatorial + final, modelo)
    auditoria = auditar_fatorial(treino_fatorial)
    auditoria["alvos_nao_geraveis"] = len(erros)
    auditoria["amostra_alvos_nao_geraveis"] = erros[:20]
    auditoria["candidatos_treino_antes_amostra"] = len(candidatos)

    gate = protocolo["portao_corpus_antes_treino"]
    checks = {
        "nmi_abertura": auditoria["nmi_abertura_familia_turno"] <= gate["nmi_abertura_familia_turno_max"],
        "nmi_prefixo2": auditoria["nmi_prefixo2_familia_turno"] <= gate["nmi_prefixo2_familia_turno_max"],
        "prefixos_cruzados": auditoria["fracao_prefixo2_em_ate_duas_familias"] <= gate["fracao_prefixo2_em_ate_duas_familias_max"],
        "operacoes_posicoes": auditoria["todas_operacoes_em_todas_posicoes"],
        "gerabilidade": len(erros) == gate["alvos_nao_geraveis"],
    }
    auditoria["portao"] = checks
    auditoria["aprovado_para_treino"] = all(checks.values())

    corpus = {
        "versao": "fatorial-20261011",
        "origem": "Substitui somente o bloco sessao_completa por composição fatorial; replay e apoio lexical são byte-semanticamente preservados.",
        "exemplos": replay + apoio + treino_fatorial + validacao_antiga + dev_fatorial,
    }
    splits = Counter(e["split"] for e in corpus["exemplos"])
    if splits["treino"] != esperado["treino_total"]:
        raise ValueError(f"treino deixou de ter 3699: {splits}")
    if len(corpus["exemplos"]) != esperado["treino_total"] + esperado["validacao_antiga"] + esperado["validacao_fatorial"]:
        raise ValueError("total do corpus inesperado")

    gravar_gz(DIR / "corpus_fatorial.json.gz", corpus)
    gravar_json(DIR / "avaliacao_final_fatorial.json", {
        "congelada_antes_treino": True,
        "contextos": [x[0] for x in CONTEXTOS_FINAL],
        "exemplos": final,
        "limite": "Contextos e formulações não usados em treino/desenvolvimento; autoral e sintético, não avaliação humana.",
    })
    gravar_json(DIR / "auditoria_corpus.json", auditoria)
    gravar_json(DIR / "manifesto_corpus.json", {
        "base_commit": protocolo["base_commit"],
        "sha256_corpus": sha256(DIR / "corpus_fatorial.json.gz"),
        "sha256_avaliacao_final": sha256(DIR / "avaliacao_final_fatorial.json"),
        "treino": splits["treino"],
        "validacao": splits["validacao"],
        "avaliacao_final": len(final),
        "parametros": protocolo["modelo"]["parametros"],
        "vocabulario": protocolo["modelo"]["vocabulario"],
        "nenhuma_realocacao_vocabulario": True,
        "aprovado_para_treino": auditoria["aprovado_para_treino"],
    })

    rel = [
        "# Corpus fatorial — auditoria antes do treino",
        "",
        "Nenhum treino foi executado nesta etapa. O bloco de sessão foi recomposto mantendo 3.699 exemplos de treino, 999 replays, 14 apoios lexicais, 81.433 parâmetros e vocabulário 720.",
        "",
        f"- NMI abertura | família+turno: **{auditoria['nmi_abertura_familia_turno']:.3f}** (antes: 0,650).",
        f"- NMI prefixo2 | família+turno: **{auditoria['nmi_prefixo2_familia_turno']:.3f}** (antes: 0,743).",
        f"- Prefixos de 2 tokens em ≤2 famílias: **{100*auditoria['fracao_prefixo2_em_ate_duas_familias']:.1f}%** (antes: 54,8%).",
        f"- Todas as 6 operações aparecem nas 6 posições: **{'sim' if auditoria['todas_operacoes_em_todas_posicoes'] else 'não'}**.",
        f"- Alvos não geráveis com o vocabulário fixo: **{len(erros)}**.",
        f"- Portão pré-treino: **{'PASSOU' if auditoria['aprovado_para_treino'] else 'FALHOU'}**.",
        "",
        "A avaliação final fatorial foi congelada agora e não será usada para selecionar época nem alterar o corpus após o treino.",
    ]
    (DIR / "RELATORIO_CORPUS.md").write_text("\n".join(rel) + "\n", encoding="utf-8")
    print(json.dumps({"auditoria": auditoria, "splits": dict(splits)}, ensure_ascii=False, indent=2))
    if not auditoria["aprovado_para_treino"]:
        raise SystemExit("Corpus fatorial não passou o portão pré-treino")


if __name__ == "__main__":
    executar()
