"""Treino isolado que altera somente a ponderação da perda de saída.

Mantém corpus, replay, vocabulário, inicialização, arquitetura e hiperparâmetros
do treino 1x. O holdout final conhecido do PR #137 não é importado nem lido.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ANT = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, FIM, fonte_dialogo, tokenizar
import treinar_dialogo_seq2seq as treinador


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


def verificar_entradas(p):
    caminhos = {
        "corpus": RAIZ / p["corpus"],
        "checkpoint_inicial": RAIZ / p["checkpoint_inicial"],
        "checkpoint_controle": RAIZ / p["checkpoint_controle"],
    }
    for nome, path in caminhos.items():
        obtido = sha256(path)
        if obtido != p["sha256"][nome]:
            raise ValueError(f"{nome} mudou: {obtido}")
    corpus = ler_json(caminhos["corpus"])
    treino = [e for e in corpus["exemplos"] if e.get("split") == "treino"]
    validacao = [e for e in corpus["exemplos"] if e.get("split") == "validacao"]
    nova = [e for e in validacao if e.get("grupo") == "sessao_completa"]
    antiga = [e for e in validacao if e.get("grupo") != "sessao_completa"]
    if (len(treino), len(antiga), len(nova)) != (3699, 334, 94):
        raise ValueError(f"Contagens mudaram: treino={len(treino)} antiga={len(antiga)} nova={len(nova)}")
    return caminhos, treino, antiga, nova


def instalar_perda_ponderada(p):
    """Monkey-patch local ao processo; validação continua com a perda original."""
    import numpy as np

    original = treinador.perda_gradientes
    cfg = p["perda_ponderada"]
    bonus_inicio = float(cfg["bonus_primeiros_tokens"])
    bonus_lex = float(cfg["bonus_geracao_lexical"])
    n_inicio = int(cfg["quantidade_primeiros_tokens"])
    auditoria = {"batches": 0, "tokens_base": 0.0, "tokens_inicio": 0, "tokens_lexicais": 0,
                 "tokens_inicio_e_lexicais": 0, "soma_pesos": 0.0}

    def ponderada(parametros, batch, gradientes=True, dropout=0.0, dropout_tokens=0.0,
                  amostragem=0.0, rng=None):
        if not gradientes:
            return original(parametros, batch, gradientes=False, dropout=dropout,
                            dropout_tokens=dropout_tokens, amostragem=amostragem, rng=rng)
        mascara = batch["mascara"]
        ativos = mascara > 0
        nao_eos = batch["y"] != FIM
        abertura = np.zeros_like(ativos, dtype=bool)
        abertura[:, :min(n_inicio, abertura.shape[1])] = True
        abertura &= ativos & nao_eos
        copiavel = batch["iguais"].sum(axis=2) > 0
        lexical = (batch["alvo_vocab"] > 0) & (~copiavel) & ativos & nao_eos
        pesos = np.ones_like(mascara, dtype=mascara.dtype)
        pesos += bonus_inicio * abertura.astype(mascara.dtype)
        pesos += bonus_lex * lexical.astype(mascara.dtype)
        if float(pesos.max()) > float(cfg["peso_maximo"]) + 1e-6:
            raise ValueError("Peso de loss excedeu protocolo")
        novo = dict(batch)
        novo["mascara"] = mascara * pesos
        auditoria["batches"] += 1
        auditoria["tokens_base"] += float(mascara.sum())
        auditoria["tokens_inicio"] += int(abertura.sum())
        auditoria["tokens_lexicais"] += int(lexical.sum())
        auditoria["tokens_inicio_e_lexicais"] += int((abertura & lexical).sum())
        auditoria["soma_pesos"] += float(novo["mascara"].sum())
        return original(parametros, novo, gradientes=True, dropout=dropout,
                        dropout_tokens=dropout_tokens, amostragem=amostragem, rng=rng)

    treinador.perda_gradientes = ponderada
    return original, auditoria


def treinar_candidato(p, caminhos):
    destino = OUT / "checkpoint_saida_lexical.json.gz"
    if destino.exists():
        dados = ler_json(destino)
        return destino, {"reutilizado": True, "epoca_selecionada": dados.get("treino", {}).get("epoca_selecionada")}

    tmp = OUT / ".checkpoint_saida_lexical.tmp.json"
    original, auditoria = instalar_perda_ponderada(p)
    inicio = time.monotonic()
    try:
        rel = treinador.treinar(
            caminhos["corpus"], tmp,
            checkpoint_inicial=caminhos["checkpoint_inicial"],
            **p["hiperparametros"],
        )
    finally:
        treinador.perda_gradientes = original

    dados = ler_json(tmp)
    if dados["treino"]["parametros"] != p["modelo"]["parametros"]:
        raise ValueError("Capacidade do modelo mudou")
    if len(dados["vocabulario"]) != p["modelo"]["vocabulario"]:
        raise ValueError("Tamanho do vocabulario mudou")
    inicial = ler_json(caminhos["checkpoint_inicial"])
    if dados["vocabulario"] != inicial["vocabulario"]:
        raise ValueError("Vocabulario ou IDs mudaram")
    dados.update(
        aprovado=False,
        ativo_no_chat=False,
        experimento="saida-lexical-20261010",
        perda_ponderada=p["perda_ponderada"],
    )
    gravar_gz(destino, dados)
    tmp.unlink()
    return destino, {
        "reutilizado": False,
        "segundos": round(time.monotonic() - inicio, 3),
        "epoca_selecionada": dados["treino"]["epoca_selecionada"],
        "validacao_nao_ponderada": rel["validacao"],
        "auditoria_loss": auditoria,
    }


def avaliar_checkpoint(path: Path, antiga, nova):
    dados = ler_json(path)
    modelo = DialogoSeq2Seq(dados)
    grupos = {
        "antiga": [texto(e) for e in antiga],
        "nova": [texto(e) for e in nova],
        "total": [texto(e) for e in antiga + nova],
    }
    saida = {}
    for nome, casos in grupos.items():
        perda = treinador.avaliar_perda(
            modelo.pesos, casos, modelo.indices, modelo.buckets,
            modelo.limite_fonte, 64, lote_tamanho=32,
        )
        livre = treinador.avaliar_geracao(dados, casos, limite_resposta=64, maximo=None, semente=179)
        saida[nome] = {
            "entropia_cruzada": perda["entropia_cruzada"],
            "perplexidade": perda["perplexidade"],
            "tokens": perda["tokens"],
            "exemplos": livre["exemplos"],
            "completas": livre["completas"],
            "iguais_ao_alvo": livre["iguais_ao_alvo"],
        }
    return saida


def diagnostico_saida(path: Path, nova):
    """Mesmo diagnóstico que motivou a intervenção, aplicado sem teacher-forcing ponderado."""
    from experimentos.diagnostico_transferencia_20261010.executar import nll_por_token, primeiro_erro

    dados = ler_json(path)
    modelo = DialogoSeq2Seq(dados)
    nll_lex = []
    erros_token0 = 0
    nao_exatas = 0
    erros_ate2 = 0
    primeiros = {}
    for ex in nova:
        d = nll_por_token(modelo.pesos, ex, modelo.indices, modelo.buckets, modelo.limite_fonte, 64)
        nll_lex.extend(x["nll"] for x in d if x["categoria"] == "geracao_lexical")
        ger = modelo.gerar(ex["mensagem"], ex.get("historico", []), max_tokens=64)
        alvo = [t.casefold() for t in tokenizar(ex["resposta"])]
        obtido = [t.casefold() for t in ger["tokens"]]
        if alvo != obtido:
            nao_exatas += 1
            i, _, _ = primeiro_erro(alvo, obtido)
            if i == 0:
                erros_token0 += 1
            if i is not None and i <= 2:
                erros_ate2 += 1
        primeiro = obtido[0] if obtido else "<vazio>"
        primeiros[primeiro] = primeiros.get(primeiro, 0) + 1
    return {
        "tokens_geracao_lexical": len(nll_lex),
        "nll_geracao_lexical": sum(nll_lex) / len(nll_lex),
        "nao_exatas": nao_exatas,
        "erros_token0": erros_token0,
        "erros_ate_token2": erros_ate2,
        "fracao_erros_ate_token2": erros_ate2 / max(1, nao_exatas),
        "primeiros_tokens_gerados": dict(sorted(primeiros.items(), key=lambda kv: (-kv[1], kv[0]))[:20]),
    }


def validar_controle(p, avaliacao, diag):
    ref = p["controle_desenvolvimento"]
    checks = {
        "antiga_exatas": avaliacao["antiga"]["iguais_ao_alvo"] == ref["antiga"]["exatas"],
        "nova_exatas": avaliacao["nova"]["iguais_ao_alvo"] == ref["nova"]["exatas"],
        "antiga_ce": abs(avaliacao["antiga"]["entropia_cruzada"] - ref["antiga"]["ce"]) < 1e-4,
        "nova_ce": abs(avaliacao["nova"]["entropia_cruzada"] - ref["nova"]["ce"]) < 1e-4,
        "erros_token0": diag["erros_token0"] == ref["nova"]["erros_token0"],
        "nll_lexical": abs(diag["nll_geracao_lexical"] - ref["nova"]["nll_geracao_lexical"]) < 0.01,
    }
    if not all(checks.values()):
        raise ValueError(f"Controle nao reproduziu o diagnostico congelado: {checks}")
    return checks


def relatorio(r):
    c = r["controle"]
    n = r["candidato"]
    cr = r["criterio"]
    def sim(x): return "sim" if x else "não"
    return "\n".join([
        "# Treino do mecanismo de saída lexical — 10/10/2026",
        "",
        "Um único candidato. Mesmos dados, replay 1×, vocabulário, inicialização, arquitetura e hiperparâmetros do controle. A única mudança é a ponderação da loss **somente durante treino**: +0,75 nos três primeiros alvos e +0,75 nos alvos lexicais que não estão disponíveis por cópia. Validação e avaliação permanecem não ponderadas.",
        "",
        "| Condição | CE antiga | Exatas antigas | CE nova | Exatas novas | NLL lexical | Erros token 0 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| controle 1× | {c['avaliacao']['antiga']['entropia_cruzada']:.6f} | {c['avaliacao']['antiga']['iguais_ao_alvo']}/334 | {c['avaliacao']['nova']['entropia_cruzada']:.6f} | {c['avaliacao']['nova']['iguais_ao_alvo']}/94 | {c['diagnostico']['nll_geracao_lexical']:.4f} | {c['diagnostico']['erros_token0']} |",
        f"| loss ponderada | {n['avaliacao']['antiga']['entropia_cruzada']:.6f} | {n['avaliacao']['antiga']['iguais_ao_alvo']}/334 | {n['avaliacao']['nova']['entropia_cruzada']:.6f} | {n['avaliacao']['nova']['iguais_ao_alvo']}/94 | {n['diagnostico']['nll_geracao_lexical']:.4f} | {n['diagnostico']['erros_token0']} |",
        "",
        "## Critério pré-congelado",
        "",
        f"- Reter antigo: **{sim(cr['reter_antigo'])}**.",
        f"- Melhorar novo: **{sim(cr['melhorar_novo'])}**.",
        f"- Melhorar saída lexical: **{sim(cr['melhorar_saida_lexical'])}**.",
        f"- Melhorar abertura: **{sim(cr['melhorar_abertura'])}**.",
        f"- Sucesso conjunto: **{sim(cr['sucesso_conjunto'])}**.",
        "",
        "## Integridade",
        "",
        "- Holdout final conhecido do PR #137: **não lido**.",
        "- Nenhum checkpoint público foi alterado.",
        "- Nenhuma regra de diálogo, memória, acervo, modelo externo, arquitetura ou parâmetro foi adicionado.",
        "- Este desenvolvimento é conhecido e não prova generalização; mesmo um candidato aprovado aqui não é promovido nesta fase.",
        "",
    ])


def executar():
    p = ler_json(OUT / "protocolo.json")
    caminhos, treino, antiga, nova = verificar_entradas(p)
    controle_eval = avaliar_checkpoint(caminhos["checkpoint_controle"], antiga, nova)
    controle_diag = diagnostico_saida(caminhos["checkpoint_controle"], nova)
    checks_controle = validar_controle(p, controle_eval, controle_diag)

    candidato_path, meta_treino = treinar_candidato(p, caminhos)
    candidato_eval = avaliar_checkpoint(candidato_path, antiga, nova)
    candidato_diag = diagnostico_saida(candidato_path, nova)

    cr = {
        "reter_antigo": (
            candidato_eval["antiga"]["entropia_cruzada"] <= controle_eval["antiga"]["entropia_cruzada"]
            and candidato_eval["antiga"]["iguais_ao_alvo"] >= controle_eval["antiga"]["iguais_ao_alvo"]
        ),
        "melhorar_novo": (
            candidato_eval["nova"]["entropia_cruzada"] < controle_eval["nova"]["entropia_cruzada"]
            and candidato_eval["nova"]["iguais_ao_alvo"] >= controle_eval["nova"]["iguais_ao_alvo"]
        ),
        "melhorar_saida_lexical": candidato_diag["nll_geracao_lexical"] < controle_diag["nll_geracao_lexical"],
        "melhorar_abertura": candidato_diag["erros_token0"] < controle_diag["erros_token0"],
    }
    cr["sucesso_conjunto"] = all(cr.values())

    resultado = {
        "base_commit": p["base_commit"],
        "aprovado": False,
        "ativo_no_chat": False,
        "holdout_final_lido": False,
        "controle": {"checkpoint": p["checkpoint_controle"], "avaliacao": controle_eval,
                     "diagnostico": controle_diag, "reproducao": checks_controle},
        "candidato": {"checkpoint": str(candidato_path.relative_to(RAIZ)),
                      "checkpoint_sha256": sha256(candidato_path), "avaliacao": candidato_eval,
                      "diagnostico": candidato_diag, "treino": meta_treino},
        "criterio": cr,
        "perda_ponderada": p["perda_ponderada"],
        "integridade": {
            "treino_exemplos": len(treino),
            "validacao_antiga": len(antiga),
            "validacao_nova": len(nova),
            "parametros": p["modelo"]["parametros"],
            "vocabulario": p["modelo"]["vocabulario"],
            "checkpoint_publico_alterado": False,
            "um_unico_candidato": True,
        },
    }
    gravar_json(OUT / "resultados.json", resultado)
    (OUT / "RELATORIO.md").write_text(relatorio(resultado), encoding="utf-8")
    print(json.dumps({"criterio": cr, "controle": {"old": controle_eval["antiga"], "new": controle_eval["nova"], "diag": controle_diag},
                      "candidato": {"old": candidato_eval["antiga"], "new": candidato_eval["nova"], "diag": candidato_diag},
                      "treino": meta_treino}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
