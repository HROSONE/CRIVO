"""Diagnóstico sem treino da transferência do gerador 1x para famílias novas.

Usa somente o desenvolvimento conhecido de 94 exemplos. Não lê o holdout final
do PR #137, não altera pesos e não seleciona checkpoint.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, ESPECIAIS, FIM, fonte_dialogo, tokenizar
from treinar_dialogo_seq2seq import lote, perda_gradientes


def texto(ex):
    return {"mensagem": ex["mensagem"], "historico": ex.get("historico", []), "resposta": ex["resposta"]}


def media(xs):
    return sum(xs) / len(xs) if xs else None


def jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def toks(texto_):
    return [t.casefold() for t in tokenizar(texto_)]


def fonte_tokens(ex, limite):
    return [t.casefold() for t in fonte_dialogo(ex["mensagem"], ex.get("historico", []), limite)]


def primeiro_erro(alvo, gerada):
    n = max(len(alvo), len(gerada))
    for i in range(n):
        a = alvo[i] if i < len(alvo) else None
        g = gerada[i] if i < len(gerada) else None
        if a != g:
            return i, a, g
    return None, None, None


def ce_exemplo(pesos, ex, indices, buckets, limite_fonte, limite_resposta):
    b = lote([texto(ex)], indices, buckets, limite_fonte, limite_resposta)
    valor, _ = perda_gradientes(pesos, b, gradientes=False)
    return float(valor)


def nll_por_token(pesos, ex, indices, buckets, limite_fonte, limite_resposta):
    import numpy as np
    b = lote([texto(ex)], indices, buckets, limite_fonte, limite_resposta)
    mascara_original = b["mascara"].copy()
    alvo = tokenizar(ex["resposta"]) + [ESPECIAIS[FIM]]
    fonte = set(fonte_dialogo(ex["mensagem"], ex.get("historico", []), limite_fonte))
    vocab = set(indices)
    saida = []
    for j in range(int(mascara_original.shape[1])):
        if not mascara_original[0, j]:
            continue
        bb = dict(b)
        m = np.zeros_like(mascara_original)
        m[0, j] = 1.0
        bb["mascara"] = m
        valor, _ = perda_gradientes(pesos, bb, gradientes=False)
        token = alvo[j]
        if token == ESPECIAIS[FIM]:
            categoria = "eos"
        elif token in vocab and token in fonte:
            categoria = "vocab_e_fonte"
        elif token in vocab:
            categoria = "geracao_lexical"
        elif token in fonte:
            categoria = "copia_oov"
        else:
            categoria = "impossivel"
        saida.append({"indice": j, "token": token, "categoria": categoria, "nll": float(valor)})
    return saida


def vizinho_treino(ex, treino, limite):
    msg = toks(ex["mensagem"])
    src = fonte_tokens(ex, limite)
    melhor = None
    for t in treino:
        sm = jaccard(msg, toks(t["mensagem"]))
        sf = jaccard(src, fonte_tokens(t, limite))
        score = (sm + sf) / 2
        chave = (score, sf, sm)
        if melhor is None or chave > melhor[0]:
            melhor = (chave, t)
    (score, sf, sm), t = melhor
    return {
        "id": t.get("id"),
        "familia": t.get("familia"),
        "grupo": t.get("grupo"),
        "mensagem": t["mensagem"],
        "similaridade_media": score,
        "jaccard_fonte": sf,
        "jaccard_mensagem": sm,
    }


def resumir_grupo(linhas):
    exatas = sum(x["exata_full"] for x in linhas)
    divergencias = [x["primeiro_erro_indice"] for x in linhas if x["primeiro_erro_indice"] is not None]
    return {
        "exemplos": len(linhas),
        "ce_full": media([x["ce_full"] for x in linhas]),
        "ce_sem_historico": media([x["ce_sem_historico"] for x in linhas]),
        "delta_sem_hist_menos_full": media([x["ce_sem_historico"] - x["ce_full"] for x in linhas]),
        "exatas_full": exatas,
        "exatas_sem_historico": sum(x["exata_sem_historico"] for x in linhas),
        "primeiro_erro_medio": media(divergencias),
        "vizinho_similaridade_media": media([x["vizinho"]["similaridade_media"] for x in linhas]),
    }


def executar():
    import numpy as np

    protocolo = ler_json(DIR / "protocolo.json")
    checkpoint_path = RAIZ / protocolo["checkpoint"]
    corpus_path = RAIZ / protocolo["corpus"]
    dados = ler_json(checkpoint_path)
    corpus = ler_json(corpus_path)
    modelo = DialogoSeq2Seq(dados)
    pesos = {k: np.asarray(v, dtype=np.float32) for k, v in dados["pesos"].items()}
    limite_fonte = modelo.limite_fonte
    limite_resposta = 64

    treino = [e for e in corpus["exemplos"] if e.get("split") == "treino"]
    novos = [e for e in corpus["exemplos"] if e.get("split") == "validacao" and e.get("grupo") == "sessao_completa"]
    if len(novos) != protocolo["recorte"]["exemplos_esperados"]:
        raise ValueError(f"Esperava 94 exemplos novos; encontrei {len(novos)}")
    familias = sorted(set(e.get("familia") for e in novos))
    if familias != sorted(protocolo["recorte"]["familias_esperadas"]):
        raise ValueError(f"Famílias mudaram: {familias}")

    detalhes = []
    categorias = defaultdict(list)
    categorias_por_familia = defaultdict(lambda: defaultdict(list))

    for n, ex in enumerate(novos, 1):
        full = texto(ex)
        sem_hist = dict(full, historico=[])
        ce_full = ce_exemplo(pesos, full, modelo.indices, modelo.buckets, limite_fonte, limite_resposta)
        ce_sem = ce_exemplo(pesos, sem_hist, modelo.indices, modelo.buckets, limite_fonte, limite_resposta)

        gf = modelo.gerar(full["mensagem"], full["historico"], max_tokens=limite_resposta)
        gn = modelo.gerar(sem_hist["mensagem"], [], max_tokens=limite_resposta)
        alvo = [t.casefold() for t in tokenizar(full["resposta"])]
        ger_full = [t.casefold() for t in gf["tokens"]]
        ger_sem = [t.casefold() for t in gn["tokens"]]
        erro_i, erro_alvo, erro_gerado = primeiro_erro(alvo, ger_full)

        token_diag = nll_por_token(pesos, full, modelo.indices, modelo.buckets, limite_fonte, limite_resposta)
        for td in token_diag:
            categorias[td["categoria"]].append(td["nll"])
            categorias_por_familia[ex["familia"]][td["categoria"]].append(td["nll"])

        viz = vizinho_treino(full, treino, limite_fonte)
        detalhes.append({
            "id": ex.get("id"),
            "familia": ex.get("familia"),
            "turno": ex.get("turno"),
            "episodio": ex.get("episodio"),
            "mensagem": ex["mensagem"],
            "alvo": ex["resposta"],
            "ce_full": ce_full,
            "ce_sem_historico": ce_sem,
            "delta_sem_hist_menos_full": ce_sem - ce_full,
            "gerada_full": gf["texto"],
            "gerada_sem_historico": gn["texto"],
            "exata_full": alvo == ger_full,
            "exata_sem_historico": alvo == ger_sem,
            "primeiro_erro_indice": erro_i,
            "primeiro_erro_alvo": erro_alvo,
            "primeiro_erro_gerado": erro_gerado,
            "tokens_alvo": len(alvo),
            "tokens_gerados": len(ger_full),
            "token_diagnostico": token_diag,
            "vizinho": viz,
        })
        print(f"{n:02d}/{len(novos)} {ex['familia']} turno={ex.get('turno')} CE={ce_full:.3f}", flush=True)

    por_familia = {}
    for fam in familias:
        por_familia[fam] = resumir_grupo([x for x in detalhes if x["familia"] == fam])
        por_familia[fam]["por_categoria_token"] = {
            cat: {"tokens": len(vals), "nll_media": media(vals)}
            for cat, vals in sorted(categorias_por_familia[fam].items())
        }

    turnos = sorted(set(int(x["turno"]) for x in detalhes if x["turno"] is not None))
    por_turno = {str(t): resumir_grupo([x for x in detalhes if int(x["turno"]) == t]) for t in turnos}
    token_resumo = {
        cat: {"tokens": len(vals), "nll_media": media(vals), "nll_mediana": statistics.median(vals) if vals else None}
        for cat, vals in sorted(categorias.items())
    }

    posteriores = [x for x in detalhes if int(x["turno"]) >= 2]
    ce_full_post = media([x["ce_full"] for x in posteriores])
    ce_sem_post = media([x["ce_sem_historico"] for x in posteriores])
    fonte_vals = categorias.get("vocab_e_fonte", []) + categorias.get("copia_oov", [])
    lex_vals = categorias.get("geracao_lexical", [])
    nao_exatas = [x for x in detalhes if not x["exata_full"]]
    cedo = [x for x in nao_exatas if x["primeiro_erro_indice"] is not None and x["primeiro_erro_indice"] <= 2]
    inicio = [x for x in detalhes if int(x["turno"]) in (1, 2)]
    fim = [x for x in detalhes if int(x["turno"]) in (5, 6)]

    flags = {
        "historico_prejudica": (ce_full_post - ce_sem_post) >= 0.50,
        "historico_delta_ce_full_menos_sem": ce_full_post - ce_sem_post,
        "gap_geracao_vs_copia": bool(lex_vals and fonte_vals) and (media(lex_vals) - media(fonte_vals)) >= 0.75,
        "gap_nll_geracao_menos_fonte": (media(lex_vals) - media(fonte_vals)) if lex_vals and fonte_vals else None,
        "divergencia_muito_cedo": bool(nao_exatas) and len(cedo) / len(nao_exatas) >= 0.60,
        "fracao_divergencia_ate_token_2": len(cedo) / max(1, len(nao_exatas)),
        "erro_cresce_com_turno": (media([x["ce_full"] for x in fim]) - media([x["ce_full"] for x in inicio])) >= 0.75,
        "delta_ce_turnos_5_6_menos_1_2": media([x["ce_full"] for x in fim]) - media([x["ce_full"] for x in inicio]),
    }

    viz_scores = [x["vizinho"]["similaridade_media"] for x in detalhes]
    resumo = {
        "exemplos": len(detalhes),
        "familias": Counter(x["familia"] for x in detalhes),
        "ce_full_media": media([x["ce_full"] for x in detalhes]),
        "ce_sem_historico_media": media([x["ce_sem_historico"] for x in detalhes]),
        "exatas_full": sum(x["exata_full"] for x in detalhes),
        "exatas_sem_historico": sum(x["exata_sem_historico"] for x in detalhes),
        "com_primeiro_erro": sum(x["primeiro_erro_indice"] is not None for x in detalhes),
        "vizinho_similaridade_media": media(viz_scores),
        "vizinho_similaridade_min": min(viz_scores),
        "vizinho_similaridade_max": max(viz_scores),
    }

    resultado = {
        "base_commit": protocolo["base_commit"],
        "checkpoint": protocolo["checkpoint"],
        "nenhum_treino": True,
        "pesos_alterados": False,
        "holdout_final_lido": False,
        "resumo": resumo,
        "flags": flags,
        "por_familia": por_familia,
        "por_turno": por_turno,
        "por_categoria_token": token_resumo,
        "detalhes": detalhes,
        "limites": protocolo["limites"],
    }
    (DIR / "resultados.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    linhas = [
        "# Diagnóstico de transferência — 10/10/2026",
        "",
        "Sem treino e sem alteração de pesos. Usa o checkpoint 1× e somente os 94 exemplos novos de desenvolvimento já conhecidos; o holdout final do PR #137 não foi lido.",
        "",
        f"- CE média com histórico: **{resumo['ce_full_media']:.4f}**",
        f"- CE média sem histórico: **{resumo['ce_sem_historico_media']:.4f}**",
        f"- Exatas com histórico: **{resumo['exatas_full']}/94**",
        f"- Exatas sem histórico: **{resumo['exatas_sem_historico']}/94**",
        "",
        "## Por família",
        "",
        "| Família | N | CE full | CE sem hist | Δ sem-full | Exatas full | Vizinho treino |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for fam, r in por_familia.items():
        linhas.append(f"| {fam} | {r['exemplos']} | {r['ce_full']:.4f} | {r['ce_sem_historico']:.4f} | {r['delta_sem_hist_menos_full']:.4f} | {r['exatas_full']} | {r['vizinho_similaridade_media']:.3f} |")
    linhas += [
        "",
        "## Por posição do turno",
        "",
        "| Turno | N | CE full | CE sem hist | Δ sem-full | Exatas | Primeiro erro médio |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for t, r in por_turno.items():
        pe = "—" if r["primeiro_erro_medio"] is None else f"{r['primeiro_erro_medio']:.2f}"
        linhas.append(f"| {t} | {r['exemplos']} | {r['ce_full']:.4f} | {r['ce_sem_historico']:.4f} | {r['delta_sem_hist_menos_full']:.4f} | {r['exatas_full']} | {pe} |")
    linhas += [
        "",
        "## Por categoria de token",
        "",
        "| Categoria | Tokens | NLL média | NLL mediana |",
        "|---|---:|---:|---:|",
    ]
    for cat, r in token_resumo.items():
        linhas.append(f"| {cat} | {r['tokens']} | {r['nll_media']:.4f} | {r['nll_mediana']:.4f} |")
    linhas += [
        "",
        "## Flags pré-congeladas",
        "",
        f"- Histórico prejudica materialmente: **{'sim' if flags['historico_prejudica'] else 'não'}** (full − sem histórico = {flags['historico_delta_ce_full_menos_sem']:.4f} nos turnos 2–6).",
        f"- Gap geração lexical vs. tokens disponíveis na fonte: **{'sim' if flags['gap_geracao_vs_copia'] else 'não'}** (Δ NLL = {flags['gap_nll_geracao_menos_fonte']:.4f})." if flags['gap_nll_geracao_menos_fonte'] is not None else "- Gap geração lexical vs. fonte: indisponível.",
        f"- Divergência muito cedo: **{'sim' if flags['divergencia_muito_cedo'] else 'não'}** ({100*flags['fracao_divergencia_ate_token_2']:.1f}% das não-exatas divergem até índice 2).",
        f"- Erro cresce nos turnos finais: **{'sim' if flags['erro_cresce_com_turno'] else 'não'}** (Δ CE turnos 5–6 − 1–2 = {flags['delta_ce_turnos_5_6_menos_1_2']:.4f}).",
        "",
        "## Limites",
        "",
        "Desenvolvimento conhecido serve somente para diagnóstico. Jaccard usa apenas entradas, nunca o alvo. CE token a token usa teacher forcing. Nenhuma capacidade nova é alegada e nenhum checkpoint é promovido.",
    ]
    (DIR / "RELATORIO.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(json.dumps({"resumo": resumo, "flags": flags, "por_familia": por_familia, "por_turno": por_turno, "tokens": token_resumo}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
