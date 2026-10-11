"""Treina um único candidato fatorial e o compara com o controle 1x.

A avaliação final fatorial é carregada somente depois de o treinador ter
selecionado a melhor época usando a validação interna do corpus (334 antigos +
48 fatoriais). Nenhum resultado desta fase ativa o checkpoint no chat.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR = Path(__file__).resolve().parent
ANT = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, tokenizar
from treinar_dialogo_seq2seq import avaliar_geracao, avaliar_perda, treinar


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


def texto(ex):
    return {"mensagem": ex["mensagem"], "historico": ex.get("historico", []), "resposta": ex["resposta"]}


def normalizar(s: str) -> str:
    return re.sub(r"\s+", " ", s.casefold().strip())


def contem(texto_: str, trecho: str) -> bool:
    return normalizar(trecho) in normalizar(texto_)


def score_operacao(ex, gerada: str) -> bool:
    g = normalizar(gerada)
    op = ex["operacao"]
    nome = normalizar(ex["esperado_nome"])
    objeto = normalizar(ex["objeto"])
    atividade = normalizar(ex["atividade"])
    if op == "recordar_pessoa":
        return nome in g
    if op == "recordar_objeto":
        return objeto in g
    if op == "corrigir_pessoa":
        antigo = normalizar(ex["nome_antes"])
        return nome in g and antigo not in g
    if op == "guardar_hipotese":
        marcadores = ("possibilidade", "ainda não", "não está confirmado", "não está certa", "não está certo", "não é certeza")
        return any(m in g for m in marcadores)
    if op == "mensagem_sem_horario":
        proibidos = ("hoje", "amanhã", "ontem", "horário", " horas", "depois de amanhã")
        return nome in g and atividade in g and not any(p in g for p in proibidos)
    if op == "pedir_detalhe":
        return nome in g and "?" in gerada and ("o que" in g or "qual" in g)
    raise ValueError(f"Operação desconhecida: {op}")


def avaliar_bloco(dados, exemplos, com_operacoes=False):
    modelo = DialogoSeq2Seq(dados)
    casos = [texto(e) for e in exemplos]
    perda = avaliar_perda(
        modelo.pesos, casos, modelo.indices, modelo.buckets,
        modelo.limite_fonte, 64, lote_tamanho=32,
    )
    livre = avaliar_geracao(dados, casos, limite_resposta=64, maximo=None, semente=179)
    primeiro_correto = 0
    ranks = []
    probs_alvo = []
    for ex in exemplos:
        alvo = tokenizar(ex["resposta"])[0]
        dist = modelo.probabilidades(ex["mensagem"], ex.get("historico", []))
        ordem = sorted(dist.items(), key=lambda kv: (-kv[1], kv[0]))
        top = ordem[0][0]
        primeiro_correto += top.casefold() == alvo.casefold()
        rank = next((i + 1 for i, (tok, _) in enumerate(ordem) if tok.casefold() == alvo.casefold()), len(ordem) + 1)
        ranks.append(rank)
        probs_alvo.append(sum(p for tok, p in ordem if tok.casefold() == alvo.casefold()))

    saida = {
        "perda": perda,
        "geracao": {k: v for k, v in livre.items() if k != "saidas"},
        "primeiro_token": {
            "corretos": primeiro_correto,
            "total": len(exemplos),
            "acuracia": primeiro_correto / max(1, len(exemplos)),
            "rank_medio": sum(ranks) / max(1, len(ranks)),
            "probabilidade_alvo_media": sum(probs_alvo) / max(1, len(probs_alvo)),
        },
    }
    if com_operacoes:
        detalhes = []
        por_op = {}
        acertos = 0
        for ex, ger in zip(exemplos, livre["saidas"]):
            ok = score_operacao(ex, ger["gerada"])
            acertos += ok
            detalhes.append({
                "id": ex["id"], "operacao": ex["operacao"], "mensagem": ex["mensagem"],
                "alvo": ex["resposta"], "gerada": ger["gerada"], "passou": bool(ok),
            })
        for op in sorted(set(e["operacao"] for e in exemplos)):
            ds = [d for d in detalhes if d["operacao"] == op]
            por_op[op] = {"acertos": sum(d["passou"] for d in ds), "total": len(ds),
                          "taxa": sum(d["passou"] for d in ds) / max(1, len(ds))}
        saida["operacoes"] = {
            "acertos": acertos, "total": len(exemplos), "taxa": acertos / max(1, len(exemplos)),
            "por_operacao": por_op, "detalhes": detalhes,
            "limite": "Critérios determinísticos específicos das seis operações; não equivalem a avaliação humana geral.",
        }
    return saida


def resumo_md(resultados):
    c = resultados["controle"]
    n = resultados["candidato"]
    cf, nf = c["final"], n["final"]
    ca, na = c["antiga"], n["antiga"]
    ck = resultados["criterio"]
    linhas = [
        "# Treino fatorial — resultado",
        "",
        "Um único candidato. Mesma inicialização, arquitetura, vocabulário, quantidade de treino e hiperparâmetros do controle; muda somente a composição do bloco de sessões.",
        "",
        "| Medida | Controle 1× | Corpus fatorial |",
        "|---|---:|---:|",
        f"| CE antiga (334) | {ca['perda']['entropia_cruzada']:.4f} | {na['perda']['entropia_cruzada']:.4f} |",
        f"| Exatas antigas | {ca['geracao']['iguais_ao_alvo']}/334 | {na['geracao']['iguais_ao_alvo']}/334 |",
        f"| CE final fatorial (96) | {cf['perda']['entropia_cruzada']:.4f} | {nf['perda']['entropia_cruzada']:.4f} |",
        f"| Exatas final fatorial | {cf['geracao']['iguais_ao_alvo']}/96 | {nf['geracao']['iguais_ao_alvo']}/96 |",
        f"| Primeiro token final | {100*cf['primeiro_token']['acuracia']:.1f}% | {100*nf['primeiro_token']['acuracia']:.1f}% |",
        f"| Operações final | {100*cf['operacoes']['taxa']:.1f}% | {100*nf['operacoes']['taxa']:.1f}% |",
        "",
        "## Portão pré-congelado",
        "",
        f"- Reter exatas antigas: **{'sim' if ck['reter_exatas_antigas'] else 'não'}**.",
        f"- CE antiga dentro do limite: **{'sim' if ck['ce_antiga_ok'] else 'não'}**.",
        f"- Melhorar CE final em ≥15%: **{'sim' if ck['melhorar_ce_final'] else 'não'}** ({100*ck['ganho_ce_final_relativo']:.1f}%).",
        f"- Ganhar ≥15 p.p. no primeiro token: **{'sim' if ck['melhorar_primeiro_token'] else 'não'}** ({100*ck['ganho_primeiro_token']:.1f} p.p.).",
        f"- Ganhar ≥15 p.p. nas operações: **{'sim' if ck['melhorar_operacoes'] else 'não'}** ({100*ck['ganho_operacoes']:.1f} p.p.).",
        f"- Sucesso conjunto: **{'SIM' if ck['sucesso_conjunto'] else 'NÃO'}**.",
        "",
        "O checkpoint permanece experimental e `ativo_no_chat=false`, independentemente do resultado.",
    ]
    return "\n".join(linhas) + "\n"


def executar():
    protocolo = ler_json(DIR / "protocolo.json")
    manifesto = ler_json(DIR / "manifesto_corpus.json")
    corpus = DIR / "corpus_fatorial.json.gz"
    avaliacao_final_path = DIR / "avaliacao_final_fatorial.json"
    inicial = ANT / "inicializacao_sessoes.json.gz"
    controle_path = ANT / "checkpoint_sessoes.json.gz"

    if not manifesto.get("aprovado_para_treino"):
        raise ValueError("Corpus não foi aprovado pelo gate pré-treino")
    if sha256(corpus) != manifesto["sha256_corpus"]:
        raise ValueError("Corpus fatorial mudou depois do congelamento")
    if sha256(avaliacao_final_path) != manifesto["sha256_avaliacao_final"]:
        raise ValueError("Avaliação final mudou depois do congelamento")
    if sha256(inicial) != protocolo["origem"]["inicializacao_sha256"]:
        raise ValueError("Inicialização mudou")
    if sha256(controle_path) != protocolo["controle"]["checkpoint_sha256"]:
        raise ValueError("Controle 1x mudou")

    destino = DIR / "checkpoint_fatorial.json.gz"
    if destino.exists():
        raise ValueError("Checkpoint fatorial já existe; não sobrescrever")
    temporario = DIR / ".checkpoint_fatorial.tmp.json"
    inicio_treino = time.monotonic()
    rel_treino = treinar(
        corpus, temporario, checkpoint_inicial=inicial,
        **protocolo["hiperparametros"],
    )
    candidato = ler_json(temporario)
    temporario.unlink()
    if candidato["treino"]["parametros"] != protocolo["modelo"]["parametros"]:
        raise ValueError("Capacidade do candidato mudou")
    if len(candidato["vocabulario"]) != protocolo["modelo"]["vocabulario"]:
        raise ValueError("Vocabulário do candidato mudou")
    candidato.update(
        aprovado=False, ativo_no_chat=False,
        experimento="corpus-fatorial-20261011",
        sha256_corpus=manifesto["sha256_corpus"],
        sha256_avaliacao_final=manifesto["sha256_avaliacao_final"],
    )
    gravar_gz(destino, candidato)

    # Só agora, depois da seleção da melhor época, a avaliação final é aberta.
    final = ler_json(avaliacao_final_path)["exemplos"]
    corpus_dados = ler_json(corpus)
    antiga = [e for e in corpus_dados["exemplos"] if e.get("split") == "validacao" and e.get("grupo") != "fatorial_cruzado"]
    dev_fatorial = [e for e in corpus_dados["exemplos"] if e.get("split") == "validacao" and e.get("grupo") == "fatorial_cruzado"]
    if (len(antiga), len(dev_fatorial), len(final)) != (334, 48, 96):
        raise ValueError("Recortes de avaliação mudaram")

    controle = ler_json(controle_path)
    aval_controle_antiga = avaliar_bloco(controle, antiga)
    aval_candidato_antiga = avaliar_bloco(candidato, antiga)
    aval_controle_final = avaliar_bloco(controle, final, com_operacoes=True)
    aval_candidato_final = avaliar_bloco(candidato, final, com_operacoes=True)

    # Desenvolvimento conhecido do #137: diagnóstico apenas, nunca gate.
    corpus_antigo = ler_json(ANT / "corpus_sessoes.json.gz")
    conhecido = [e for e in corpus_antigo["exemplos"] if e.get("split") == "validacao" and e.get("grupo") == "sessao_completa"]
    diagnostico_conhecido = None
    if conhecido:
        diagnostico_conhecido = {
            "controle": avaliar_bloco(controle, conhecido),
            "candidato": avaliar_bloco(candidato, conhecido),
            "exemplos": len(conhecido),
            "entra_no_gate": False,
        }

    gate = protocolo["portao_candidato"]
    ce_ctrl = aval_controle_final["perda"]["entropia_cruzada"]
    ce_cand = aval_candidato_final["perda"]["entropia_cruzada"]
    ganho_ce = (ce_ctrl - ce_cand) / max(1e-12, ce_ctrl)
    ganho_primeiro = aval_candidato_final["primeiro_token"]["acuracia"] - aval_controle_final["primeiro_token"]["acuracia"]
    ganho_ops = aval_candidato_final["operacoes"]["taxa"] - aval_controle_final["operacoes"]["taxa"]
    criterio = {
        "reter_exatas_antigas": aval_candidato_antiga["geracao"]["iguais_ao_alvo"] >= gate["reter_exatas_antigas_min"],
        "ce_antiga_ok": aval_candidato_antiga["perda"]["entropia_cruzada"] <= gate["ce_antiga_max"],
        "melhorar_ce_final": ganho_ce >= gate["melhora_ce_final_fatorial_relativa_min"],
        "melhorar_primeiro_token": ganho_primeiro >= gate["ganho_primeiro_token_final_min"],
        "melhorar_operacoes": ganho_ops >= gate["ganho_operacao_final_min"],
        "ganho_ce_final_relativo": ganho_ce,
        "ganho_primeiro_token": ganho_primeiro,
        "ganho_operacoes": ganho_ops,
    }
    criterio["sucesso_conjunto"] = all(
        criterio[k] for k in ("reter_exatas_antigas", "ce_antiga_ok", "melhorar_ce_final", "melhorar_primeiro_token", "melhorar_operacoes")
    )

    resultados = {
        "base_commit": protocolo["base_commit"],
        "integridade": {
            "um_unico_candidato": True,
            "mesmos_parametros": candidato["treino"]["parametros"] == protocolo["modelo"]["parametros"],
            "mesmo_vocabulario": len(candidato["vocabulario"]) == protocolo["modelo"]["vocabulario"],
            "mesma_quantidade_treino": candidato["treino"]["exemplos"] == protocolo["contagens"]["treino_total"],
            "avaliacao_final_sha256": manifesto["sha256_avaliacao_final"],
            "holdout_final_pr137_lido": False,
            "checkpoint_publico_alterado": False,
        },
        "treino": {
            "segundos_parede": round(time.monotonic() - inicio_treino, 3),
            "epoca_selecionada": candidato["treino"]["epoca_selecionada"],
            "validacao_selecao": rel_treino["validacao"],
            "checkpoint_sha256": sha256(destino),
        },
        "controle": {"antiga": aval_controle_antiga, "final": aval_controle_final},
        "candidato": {"antiga": aval_candidato_antiga, "final": aval_candidato_final},
        "diagnostico_desenvolvimento_conhecido": diagnostico_conhecido,
        "criterio": criterio,
        "aprovado_experimentalmente": bool(criterio["sucesso_conjunto"]),
        "ativo_no_chat": False,
        "limite": "Avaliação final fatorial é autoral/sintética e congelada; não substitui avaliação humana nem prova diálogo geral.",
    }
    gravar_json(DIR / "resultados_treino.json", resultados)
    (DIR / "RELATORIO_TREINO.md").write_text(resumo_md(resultados), encoding="utf-8")
    print(json.dumps({
        "criterio": criterio,
        "controle_final": {"ce": ce_ctrl, "primeiro": aval_controle_final["primeiro_token"]["acuracia"], "operacoes": aval_controle_final["operacoes"]["taxa"]},
        "candidato_final": {"ce": ce_cand, "primeiro": aval_candidato_final["primeiro_token"]["acuracia"], "operacoes": aval_candidato_final["operacoes"]["taxa"]},
        "antigo_controle_exatas": aval_controle_antiga["geracao"]["iguais_ao_alvo"],
        "antigo_candidato_exatas": aval_candidato_antiga["geracao"]["iguais_ao_alvo"],
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    executar()
