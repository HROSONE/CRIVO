"""Prepara corpus misto/contrastivo sem treinar.

Mistura uma amostra balanceada das antigas sessões com exemplos fatoriais
cruzados. Nos fatoriais, palavras-pista aparecem como distratores em todos os
atos, reduzindo a chance de um atalho lexical substituir a leitura do pedido.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR = Path(__file__).resolve().parent
OLD = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
FAT = RAIZ / "experimentos" / "corpus_fatorial_20261011"
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


def chave_hash(e) -> str:
    bruto = (str(e.get("id", "")) + "\n" + e.get("mensagem", "") + "\n" + e.get("resposta", "")).encode("utf-8")
    return hashlib.sha256(bruto).hexdigest()


def familia(e):
    return str(e.get("familia") or e.get("episodio") or e.get("grupo") or "sem_familia")


def turno(e):
    t = e.get("turno")
    if t is not None:
        return int(t)
    return 0


def selecionar_round_robin(exemplos, n, chave_grupo):
    grupos = defaultdict(list)
    for e in exemplos:
        grupos[chave_grupo(e)].append(e)
    filas = {k: deque(sorted(v, key=chave_hash)) for k, v in grupos.items()}
    chaves = sorted(filas, key=lambda k: str(k))
    saida = []
    while len(saida) < n:
        avancou = False
        for k in chaves:
            if filas[k] and len(saida) < n:
                saida.append(filas[k].popleft())
                avancou = True
        if not avancou:
            break
    if len(saida) != n:
        raise ValueError(f"Seleção insuficiente: {len(saida)} de {n}")
    return saida


DISTRATORES = [
    ("mensagem", "Antes de escrever qualquer mensagem, responda ao pedido atual: {m}"),
    ("possibilidade", "Mesmo que alguma parte disso ainda possa mudar, responda ao pedido atual: {m}"),
    ("correcao", "Sem tratar isso como outra correção, responda ao pedido atual: {m}"),
    ("pessoa", "Mesmo que eu tenha mencionado uma pessoa, responda ao pedido atual: {m}"),
    ("horario", "Sem escolher horário agora, responda ao pedido atual: {m}"),
]


def contrastivar(exemplos):
    por_op = defaultdict(list)
    for e in exemplos:
        op = e.get("operacao")
        if not op:
            raise ValueError("Exemplo fatorial sem operação")
        por_op[op].append(e)
    saida = []
    for op, itens in sorted(por_op.items()):
        itens = sorted(itens, key=chave_hash)
        for i, e in enumerate(itens):
            nome, molde = DISTRATORES[i % len(DISTRATORES)]
            novo = dict(e)
            novo["mensagem"] = molde.format(m=e["mensagem"])
            novo["grupo"] = "fatorial_contrastivo"
            novo["distrator"] = nome
            novo["id"] = "misto-" + str(e.get("id") or chave_hash(e)[:16])
            saida.append(novo)
    return saida


def entropia(cont):
    n = sum(cont.values())
    if not n:
        return 0.0
    return -sum((v/n) * math.log2(v/n) for v in cont.values() if v)


def nmi(exemplos, x_fn, y_fn):
    y = Counter(y_fn(e) for e in exemplos)
    hy = entropia(y)
    if not hy:
        return 0.0
    grupos = defaultdict(list)
    for e in exemplos:
        grupos[x_fn(e)].append(e)
    n = len(exemplos)
    hyx = sum(len(es)/n * entropia(Counter(y_fn(e) for e in es)) for es in grupos.values())
    return (hy - hyx) / hy


def prefixo(e, n):
    return tuple(t.casefold() for t in tokenizar(e["resposta"])[:n])


def audit_session_block(exemplos, fatoriais):
    pref_fams = defaultdict(set)
    for e in exemplos:
        pref_fams[prefixo(e, 2)].add(familia(e))
    pouco = sum(len(pref_fams[prefixo(e, 2)]) <= 2 for e in exemplos)

    pos = defaultdict(set)
    for e in fatoriais:
        pos[e["operacao"]].add(turno(e))

    return {
        "nmi_abertura_familia_turno": nmi(exemplos, lambda e:(familia(e), turno(e)), lambda e:prefixo(e,1)),
        "nmi_prefixo2_familia_turno": nmi(exemplos, lambda e:(familia(e), turno(e)), lambda e:prefixo(e,2)),
        "fracao_prefixo2_em_ate_duas_familias": pouco / max(1, len(exemplos)),
        "nmi_operacao_distrator": nmi(fatoriais, lambda e:e["distrator"], lambda e:e["operacao"]),
        "operacoes_fatoriais_posicoes": {k: sorted(v) for k,v in sorted(pos.items())},
        "todas_operacoes_fatoriais_em_todas_posicoes": bool(pos) and all(v == set(range(1,7)) for v in pos.values()),
        "familias_bloco": len(set(familia(e) for e in exemplos)),
        "distratores_por_operacao": {
            op: dict(Counter(e["distrator"] for e in fatoriais if e["operacao"] == op))
            for op in sorted(set(e["operacao"] for e in fatoriais))
        },
    }


def alvos_nao_geraveis(exemplos, modelo):
    vocab = set(modelo.vocabulario)
    erros = []
    for e in exemplos:
        fonte = set(fonte_dialogo(e["mensagem"], e.get("historico", []), modelo.limite_fonte))
        for t in tokenizar(e["resposta"]):
            if t not in vocab and t not in fonte:
                erros.append({"id": e.get("id"), "token": t, "grupo": e.get("grupo")})
    return erros


PROSPECT_CONTEXTS = [
    ("arquivo_novo", "Estou separando um {objeto} com {nome} no arquivo."),
    ("ensaio_novo", "Estou ensaiando {atividade} com {nome} no salão."),
    ("visita_tecnica_nova", "Estou revisando o {objeto} com {nome} numa visita técnica."),
    ("feira_nova", "Estou preparando o {objeto} com {nome} para uma feira."),
    ("laboratorio_novo", "Estou organizando o {objeto} com {nome} no laboratório."),
]
PROSPECT_VALUES = [
    dict(nome="Solina-81", outro="Bravio-92", objeto="caderno", atividade="leitura"),
    dict(nome="Bravio-92", outro="Télio-83", objeto="livro", atividade="escrita"),
    dict(nome="Télio-83", outro="Marena-64", objeto="texto", atividade="fotografia"),
    dict(nome="Marena-64", outro="Solina-81", objeto="projeto", atividade="desenho"),
]
OPS = ("recordar_pessoa", "recordar_objeto", "corrigir_pessoa", "guardar_hipotese", "mensagem_sem_horario", "pedir_detalhe")
PROSPECT_MSG = {
    "recordar_pessoa": "Retome só a pessoa vinculada a essa situação: quem era?",
    "recordar_objeto": "Sem mudar mais nada, qual coisa ficou como objeto dessa situação?",
    "corrigir_pessoa": "Considere esta mudança: onde estava {atual}, passe a usar {outro} como a pessoa.",
    "guardar_hipotese": "Eu só estou cogitando {atividade}; isso já conta como confirmado ou continua incerto?",
    "mensagem_sem_horario": "Prepare um recado para {atual} sobre {atividade}; deixe o momento em aberto.",
    "pedir_detalhe": "Quero falar com {atual}, mas ainda não expliquei o que vou pedir. O que você precisa saber?",
}
PROSPECT_RESP = {
    "recordar_pessoa": ("A pessoa é {atual}.", "{atual} é a pessoa."),
    "recordar_objeto": ("O objeto é {objeto}.", "Você estava falando do {objeto}."),
    "corrigir_pessoa": ("Certo. Agora a pessoa é {outro}.", "Entendi. Agora fica {outro}."),
    "guardar_hipotese": ("Não. Isso ainda é uma possibilidade.", "Ainda não está confirmado."),
    "mensagem_sem_horario": ("{atual}, podemos combinar {atividade}?", "{atual}, você quer combinar {atividade} comigo?"),
    "pedir_detalhe": ("O que você quer pedir a {atual}?", "Qual é o pedido para {atual}?"),
}


def prospect_order(ci, pi):
    base = list(OPS)
    shift = (2*ci + pi) % len(base)
    out = base[shift:] + base[:shift]
    if (ci + pi) % 2:
        out.reverse()
    return out


def gerar_prospectivo():
    saida = []
    for ci, (fam, seed_tpl) in enumerate(PROSPECT_CONTEXTS):
        for pi, vals in enumerate(PROSPECT_VALUES):
            atual = vals["nome"]
            seed_u = seed_tpl.format(**vals)
            seed_a = f"Entendi. A pessoa é {vals['nome']}, o objeto é {vals['objeto']} e a atividade é {vals['atividade']}."
            hist = [{"papel":"usuario", "texto":seed_u}, {"papel":"assistente", "texto":seed_a}]
            for pos, op in enumerate(prospect_order(ci, pi), 1):
                fmt = dict(vals, atual=atual)
                msg = PROSPECT_MSG[op].format(**fmt)
                resp = PROSPECT_RESP[op][(ci + pi + pos) % 2].format(**fmt)
                ex = {
                    "id": f"prospect-{fam}-{pi}-{pos}", "familia": fam, "grupo":"prospectivo_contrastivo",
                    "mensagem": msg, "historico": list(hist), "resposta": resp,
                    "episodio": f"{fam}-{pi}", "turno": pos, "operacao": op,
                    "esperado_nome": vals["outro"] if op == "corrigir_pessoa" else atual,
                    "nome_antes": atual, "objeto": vals["objeto"], "atividade": vals["atividade"],
                }
                saida.append(ex)
                hist.extend([{"papel":"usuario","texto":msg}, {"papel":"assistente","texto":resp}])
                if op == "corrigir_pessoa":
                    atual = vals["outro"]
    return saida


def executar():
    p = ler_json(DIR / "protocolo.json")
    old_path = RAIZ / p["origem"]["corpus_antigo"]
    fat_path = RAIZ / p["origem"]["corpus_fatorial"]
    init_path = RAIZ / p["origem"]["inicializacao"]
    if sha256(old_path) != p["origem"]["corpus_antigo_sha256"]:
        raise ValueError("Corpus antigo mudou")
    if sha256(fat_path) != p["origem"]["corpus_fatorial_sha256"]:
        raise ValueError("Corpus fatorial mudou")
    if sha256(init_path) != p["origem"]["inicializacao_sha256"]:
        raise ValueError("Inicialização mudou")

    old = ler_json(old_path)["exemplos"]
    fat = ler_json(fat_path)["exemplos"]
    replay = [e for e in old if e.get("split") == "treino" and e.get("grupo") == "replay_legado"]
    apoio = [e for e in old if e.get("split") == "treino" and e.get("grupo") == "apoio_lexical"]
    old_sessions = [e for e in old if e.get("split") == "treino" and e.get("grupo") == "sessao_completa"]
    old334 = [e for e in old if e.get("split") == "validacao" and e.get("grupo") != "sessao_completa"]
    known94 = [e for e in old if e.get("split") == "validacao" and e.get("grupo") == "sessao_completa"]
    fat_train = [e for e in fat if e.get("split") == "treino" and e.get("grupo") == "fatorial_cruzado"]
    fat_dev = [e for e in fat if e.get("split") == "validacao" and e.get("grupo") == "fatorial_cruzado"]

    esperado = p["composicao_treino"]
    if (len(replay), len(apoio), len(old_sessions), len(old334), len(known94), len(fat_train), len(fat_dev)) != (999,14,2686,334,94,2686,48):
        raise ValueError("Recortes de origem mudaram: " + str((len(replay),len(apoio),len(old_sessions),len(old334),len(known94),len(fat_train),len(fat_dev))))

    old_sel = selecionar_round_robin(old_sessions, esperado["sessoes_antigas_balanceadas"], lambda e:(familia(e), turno(e)))
    fat_sel = selecionar_round_robin(fat_train, esperado["fatoriais_contrastivas"], lambda e:(e.get("operacao"), turno(e), familia(e)))
    fat_con = contrastivar(fat_sel)
    dev_con = contrastivar(fat_dev)

    bloco = old_sel + fat_con
    auditoria = audit_session_block(bloco, fat_con)
    modelo = DialogoSeq2Seq(ler_json(init_path))
    prospect = gerar_prospectivo()
    erros = alvos_nao_geraveis(replay + apoio + bloco + old334 + known94 + dev_con + prospect, modelo)
    auditoria["alvos_nao_geraveis"] = len(erros)
    auditoria["amostra_alvos_nao_geraveis"] = erros[:20]
    auditoria["contagens"] = {
        "replay": len(replay), "apoio": len(apoio), "old_sessions": len(old_sel),
        "fatoriais": len(fat_con), "old334": len(old334), "known94": len(known94),
        "dev_contrastivo": len(dev_con), "prospectivo": len(prospect),
    }

    g = p["portao_corpus"]
    checks = {
        "nmi_abertura": auditoria["nmi_abertura_familia_turno"] <= g["nmi_abertura_familia_turno_max"],
        "nmi_prefixo2": auditoria["nmi_prefixo2_familia_turno"] <= g["nmi_prefixo2_familia_turno_max"],
        "nmi_distrator": auditoria["nmi_operacao_distrator"] <= g["nmi_operacao_distrator_max"],
        "prefixos_cruzados": auditoria["fracao_prefixo2_em_ate_duas_familias"] <= g["fracao_prefixo2_em_ate_duas_familias_max"],
        "operacoes_posicoes": auditoria["todas_operacoes_fatoriais_em_todas_posicoes"],
        "gerabilidade": len(erros) == g["alvos_nao_geraveis"],
    }
    auditoria["portao"] = checks
    auditoria["aprovado_para_treino"] = all(checks.values())

    corpus = {
        "versao": "misto-contrastivo-20261011",
        "origem": "999 replay + 14 apoio + 896 sessoes antigas balanceadas + 1790 fatoriais com pistas lexicais cruzadas.",
        "exemplos": replay + apoio + old_sel + fat_con + old334 + known94 + dev_con,
    }
    splits = Counter(e.get("split") for e in corpus["exemplos"])
    if splits["treino"] != p["composicao_treino"]["total"] or splits["validacao"] != p["validacao"]["total"]:
        raise ValueError(f"Splits inesperados: {splits}")

    gravar_gz(DIR / "corpus_misto.json.gz", corpus)
    gravar_json(DIR / "avaliacao_prospectiva.json", {
        "congelada_antes_treino": True,
        "base_commit": p["base_commit"],
        "exemplos": prospect,
        "limite": "Autoral/sintética. Famílias, formulações e nomes não entram em treino/validação; não é avaliação humana geral.",
    })
    gravar_json(DIR / "auditoria_corpus.json", auditoria)
    manifesto = {
        "base_commit": p["base_commit"],
        "sha256_corpus": sha256(DIR / "corpus_misto.json.gz"),
        "sha256_avaliacao_prospectiva": sha256(DIR / "avaliacao_prospectiva.json"),
        "treino": splits["treino"], "validacao": splits["validacao"], "prospectivo": len(prospect),
        "parametros": p["modelo"]["parametros"], "vocabulario": p["modelo"]["vocabulario"],
        "aprovado_para_treino": auditoria["aprovado_para_treino"],
        "nenhuma_realocacao_vocabulario": True,
    }
    gravar_json(DIR / "manifesto.json", manifesto)

    linhas = [
        "# Corpus misto contrastivo — auditoria pré-treino", "",
        "Sem treino nesta etapa. Mantém 3.699 exemplos e a mesma rede/vocabulário.", "",
        f"- NMI abertura | família+turno: **{auditoria['nmi_abertura_familia_turno']:.3f}**.",
        f"- NMI prefixo2 | família+turno: **{auditoria['nmi_prefixo2_familia_turno']:.3f}**.",
        f"- NMI operação | distrator lexical: **{auditoria['nmi_operacao_distrator']:.3f}**.",
        f"- Prefixos em ≤2 famílias: **{100*auditoria['fracao_prefixo2_em_ate_duas_familias']:.1f}%**.",
        f"- Todas as operações fatoriais nas seis posições: **{'sim' if auditoria['todas_operacoes_fatoriais_em_todas_posicoes'] else 'não'}**.",
        f"- Alvos não geráveis: **{len(erros)}**.",
        f"- Portão: **{'PASSOU' if auditoria['aprovado_para_treino'] else 'FALHOU'}**.", "",
        f"- Holdout prospectivo congelado: **{len(prospect)}** exemplos; SHA `{manifesto['sha256_avaliacao_prospectiva']}`.",
    ]
    (DIR / "RELATORIO_CORPUS.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(json.dumps({"auditoria": auditoria, "manifesto": manifesto}, ensure_ascii=False, indent=2))
    if not auditoria["aprovado_para_treino"]:
        raise SystemExit("Corpus misto não passou portão pré-treino")


if __name__ == "__main__":
    executar()
