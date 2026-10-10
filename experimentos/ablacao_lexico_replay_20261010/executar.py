"""Ablação 2x2: realocação lexical × replay, sem tocar no holdout final.

Compara o mesmo gerador e a mesma validação do experimento de sessões.
A avaliação final de 10 sessões, agora conhecida, não é lida aqui.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import time
from collections import Counter
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
ANT = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
OUT = Path(__file__).resolve().parent

import sys
sys.path.insert(0, str(RAIZ))
from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, fonte_dialogo, tokenizar
from treinar_dialogo_seq2seq import avaliar_geracao, avaliar_perda, treinar


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar_json(nome: str, dados) -> None:
    (OUT / nome).write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def gravar_gz(path: Path, dados) -> None:
    bruto = (json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    path.write_bytes(gzip.compress(bruto, mtime=0))


def somente_texto(ex):
    return {"mensagem": ex["mensagem"], "historico": ex.get("historico", []), "resposta": ex["resposta"]}


def representavel(ex, vocabulario):
    vocab = set(vocabulario)
    fonte = set(fonte_dialogo(ex["mensagem"], ex.get("historico", []), 192))
    return all(tok in vocab or tok in fonte for tok in tokenizar(ex["resposta"]) + ["<fim>"])


def cobertura(exemplos, vocabulario):
    vocab = set(vocabulario); nao_copiaveis = Counter(); copiaveis = Counter(); tokens_alvo = 0; exemplos_com_nao_copiavel = 0
    for ex in exemplos:
        fonte = set(fonte_dialogo(ex["mensagem"], ex.get("historico", []), 192)); faltantes = []
        for tok in tokenizar(ex["resposta"]) + ["<fim>"]:
            tokens_alvo += 1
            if tok in vocab: continue
            if tok in fonte: copiaveis[tok] += 1
            else: nao_copiaveis[tok] += 1; faltantes.append(tok)
        exemplos_com_nao_copiavel += bool(faltantes)
    return {"exemplos": len(exemplos), "tokens_alvo": tokens_alvo,
        "ocorrencias_oov_copiaveis": sum(copiaveis.values()), "ocorrencias_oov_nao_copiaveis": sum(nao_copiaveis.values()),
        "tipos_oov_copiaveis": len(copiaveis), "tipos_oov_nao_copiaveis": len(nao_copiaveis),
        "exemplos_com_oov_nao_copiavel": exemplos_com_nao_copiavel,
        "oov_nao_copiaveis_mais_frequentes": nao_copiaveis.most_common(30)}


def avaliar(path: Path, grupos):
    dados = ler_json(path); modelo = DialogoSeq2Seq(dados); resultado = {}
    for nome, exemplos in grupos.items():
        casos = [somente_texto(e) for e in exemplos]
        perda = avaliar_perda(modelo.pesos, casos, modelo.indices, modelo.buckets, modelo.limite_fonte, 64, lote_tamanho=32)
        livre = avaliar_geracao(dados, casos, limite_resposta=64, maximo=None, semente=179)
        resultado[nome] = {"perda": perda, "geracao_livre": {"exemplos": livre["exemplos"], "completas": livre["completas"],
            "iguais_ao_alvo": livre["iguais_ao_alvo"], "segundos": livre["segundos"]}}
    return resultado


def preparar_corpora(protocolo):
    corpus = ler_json(ANT / "corpus_sessoes.json.gz"); exemplos = corpus["exemplos"]
    treino = [e for e in exemplos if e["split"] == "treino"]; validacao = [e for e in exemplos if e["split"] == "validacao"]
    replay = [e for e in treino if e.get("grupo") == "replay_legado"]
    sem_replay_treino = [e for e in treino if e.get("grupo") != "replay_legado"]
    validacao_nova = [e for e in validacao if e.get("grupo") == "sessao_completa"]
    validacao_antiga = [e for e in validacao if e.get("grupo") != "sessao_completa"]
    esperados = protocolo["contagens_esperadas"]
    obtidos = {"treino_com_replay": len(treino), "replay": len(replay), "treino_sem_replay": len(sem_replay_treino),
        "validacao_antiga": len(validacao_antiga), "validacao_nova": len(validacao_nova), "validacao_total": len(validacao)}
    if obtidos != esperados: raise ValueError(f"Contagens mudaram: {obtidos} != {esperados}")
    filtrado = dict(corpus); filtrado["origem"] = "Derivado byte-logicamente do corpus de sessões: remove apenas exemplos de treino com grupo=replay_legado; validação permanece idêntica."
    filtrado["exemplos"] = sem_replay_treino + validacao; gravar_gz(OUT / "corpus_sem_replay.json.gz", filtrado)
    return treino, sem_replay_treino, validacao_antiga, validacao_nova


def treinar_condicao(nome, corpus_path, checkpoint_inicial, hiper, esperado_parametros):
    destino = OUT / f"checkpoint_{nome}.json.gz"; temporario = OUT / f".{nome}.tmp.json"
    if destino.exists():
        dados = ler_json(destino)
        return destino, {"reutilizado_local": True, "epoca_selecionada": dados.get("treino", {}).get("epoca_selecionada"), "segundos_originais": dados.get("treino", {}).get("segundos")}
    inicio = time.monotonic(); relatorio = treinar(corpus_path, temporario, checkpoint_inicial=checkpoint_inicial, **hiper); dados = ler_json(temporario)
    if dados["treino"]["parametros"] != esperado_parametros: raise ValueError(f"{nome}: capacidade mudou")
    dados.update(aprovado=False, ativo_no_chat=False, experimento="ablacao-lexico-replay-20261010", condicao=nome)
    gravar_gz(destino, dados); temporario.unlink()
    return destino, {"reutilizado_local": False, "segundos": round(time.monotonic() - inicio, 3), "epoca_selecionada": dados["treino"]["epoca_selecionada"], "validacao_treinador": relatorio["validacao"]}


def markdown(resultados):
    ordem = ["original_sem_replay", "original_com_replay", "realocado_sem_replay", "realocado_com_replay"]; comum = resultados["suporte_comum"]
    linhas = ["# Ablação: realocação lexical × replay — 10/10/2026", "",
        "Esta fase isola duas variáveis que mudaram juntas no PR #137. **O holdout final de 10 sessões não foi lido nem usado para selecionar nada.**", "",
        "A entropia cruzada do desenvolvimento completo só deve ser comparada **dentro do mesmo léxico**. No léxico original, alvos não geráveis são colapsados em `<desconhecido>` pelo treinador, o que torna uma comparação direta de CE entre vocabulários enviesada. Para comparar os dois léxicos, o relatório usa também o subconjunto em que o alvo inteiro é gerável por ambos.", "",
        f"Suporte comum: **{comum['antiga']}** exemplos antigos + **{comum['nova']}** novos = **{comum['total']}** exemplos.", "",
        "| Condição | Replay | Léxico | CE dev completo* | CE suporte comum | Exatas antiga | Exatas nova | OOV não copiável treino |",
        "|---|---:|---|---:|---:|---:|---:|---:|"]
    for nome in ordem:
        r = resultados["condicoes"][nome]; ce_total = r["avaliacao"]["total"]["perda"]["entropia_cruzada"]; ce_comum = r["avaliacao"]["comum_total"]["perda"]["entropia_cruzada"]
        a = r["avaliacao"]["antiga"]["geracao_livre"]["iguais_ao_alvo"]; n = r["avaliacao"]["nova"]["geracao_livre"]["iguais_ao_alvo"]; cov = r["cobertura_treino"]["ocorrencias_oov_nao_copiaveis"]
        linhas.append(f"| `{nome}` | {'sim' if r['replay'] else 'não'} | {r['lexico']} | {ce_total:.6f} | {ce_comum:.6f} | {a}/{r['avaliacao']['antiga']['geracao_livre']['exemplos']} | {n}/{r['avaliacao']['nova']['geracao_livre']['exemplos']} | {cov} |")
    e = resultados["efeitos"]
    linhas += ["", "\* CE completa é comparável apenas entre as duas linhas do mesmo léxico.", "", "## Efeitos pareados válidos", "", "Valores negativos em ΔCE são melhora; positivos são piora.", "",
        f"- **Realocação sem replay, no suporte comum:** ΔCE = {e['realocacao_sem_replay_delta_ce_comum']:+.6f}.",
        f"- **Realocação com replay, no suporte comum:** ΔCE = {e['realocacao_com_replay_delta_ce_comum']:+.6f}.",
        f"- **Replay com léxico original, desenvolvimento completo:** ΔCE = {e['replay_lexico_original_delta_ce_total']:+.6f}.",
        f"- **Replay com léxico realocado, desenvolvimento completo:** ΔCE = {e['replay_lexico_realocado_delta_ce_total']:+.6f}.", "", "## Leitura", "",
        "- O replay pode ser avaliado diretamente porque cada comparação mantém o mesmo vocabulário.",
        "- A realocação deve ser julgada pelo suporte comum, cobertura e geração livre; não pela CE total cruzada entre léxicos.",
        "- A realocação remove alvos não copiáveis do treino, mas reinicializa 151 entradas e suas colunas de saída; os dois efeitos competem.", "", "## Limites", "",
        "- A comparação usa apenas desenvolvimento conhecido; não reabre o holdout final.",
        "- Correspondência literal mede reprodução do alvo, não pertinência semântica.",
        "- Nenhum checkpoint desta ablação é promovido ao chat; todos permanecem `aprovado: false` e `ativo_no_chat: false`."]
    return "\n".join(linhas) + "\n"


def executar():
    protocolo = ler_json(OUT / "protocolo.json")
    arquivos = {"corpus": ANT / "corpus_sessoes.json.gz", "checkpoint_original": ANT / "checkpoint_contrastes.json.gz", "checkpoint_realocado": ANT / "inicializacao_sessoes.json.gz", "checkpoint_reuso": ANT / "checkpoint_sessoes.json.gz"}
    for chave, path in arquivos.items():
        esperado = protocolo["sha256"][chave]; atual = sha(path)
        if atual != esperado: raise ValueError(f"{chave} mudou: {atual} != {esperado}")
    treino_com, treino_sem, dev_antiga, dev_nova = preparar_corpora(protocolo); hiper = protocolo["hiperparametros"]
    orig = arquivos["checkpoint_original"]; real = arquivos["checkpoint_realocado"]; dados_orig = ler_json(orig); dados_real = ler_json(real)
    comum_antiga = [e for e in dev_antiga if representavel(e, dados_orig["vocabulario"]) and representavel(e, dados_real["vocabulario"])]
    comum_nova = [e for e in dev_nova if representavel(e, dados_orig["vocabulario"]) and representavel(e, dados_real["vocabulario"])]
    grupos = {"antiga": dev_antiga, "nova": dev_nova, "total": dev_antiga + dev_nova, "comum_antiga": comum_antiga, "comum_nova": comum_nova, "comum_total": comum_antiga + comum_nova}
    if not comum_antiga or not comum_nova: raise ValueError("Suporte comum vazio; desenho não permite comparação lexical")
    condicoes = {"original_sem_replay": (False, "original", OUT / "corpus_sem_replay.json.gz", orig), "original_com_replay": (True, "original", arquivos["corpus"], orig), "realocado_sem_replay": (False, "realocado", OUT / "corpus_sem_replay.json.gz", real)}
    resultados = {"protocolo_sha256": sha(OUT / "protocolo.json"), "numpy": np.__version__, "threads": {k: os.environ.get(k) for k in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"]}, "holdout_final_lido": False,
        "suporte_comum": {"antiga": len(comum_antiga), "nova": len(comum_nova), "total": len(comum_antiga) + len(comum_nova), "criterio": "Todo token-alvo precisa estar no vocabulario ou ser copiavel da fonte em ambos os lexicos."}, "condicoes": {}}
    for nome, (replay, lexico, corpus_path, inicial) in condicoes.items():
        checkpoint, treino_meta = treinar_condicao(nome, corpus_path, inicial, hiper, protocolo["parametros"]); dados_init = ler_json(inicial); train_set = treino_com if replay else treino_sem
        resultados["condicoes"][nome] = {"replay": replay, "lexico": lexico, "checkpoint_inicial": str(inicial.relative_to(RAIZ)), "checkpoint_inicial_sha256": sha(inicial), "corpus_sha256": sha(corpus_path), "checkpoint_sha256": sha(checkpoint), "treino": treino_meta,
            "cobertura_treino": cobertura(train_set, dados_init["vocabulario"]), "cobertura_dev_antiga": cobertura(dev_antiga, dados_init["vocabulario"]), "cobertura_dev_nova": cobertura(dev_nova, dados_init["vocabulario"]), "avaliacao": avaliar(checkpoint, grupos), "aprovado": False, "ativo_no_chat": False}
    nome = "realocado_com_replay"
    resultados["condicoes"][nome] = {"replay": True, "lexico": "realocado", "checkpoint_inicial": str(real.relative_to(RAIZ)), "checkpoint_inicial_sha256": sha(real), "corpus_sha256": sha(arquivos["corpus"]), "checkpoint_sha256": sha(arquivos["checkpoint_reuso"]),
        "treino": {"reutilizado_pr137": True, "motivo": "Mesmos corpus, inicialização e hiperparâmetros; evita retraining desnecessário."},
        "cobertura_treino": cobertura(treino_com, dados_real["vocabulario"]), "cobertura_dev_antiga": cobertura(dev_antiga, dados_real["vocabulario"]), "cobertura_dev_nova": cobertura(dev_nova, dados_real["vocabulario"]), "avaliacao": avaliar(arquivos["checkpoint_reuso"], grupos), "aprovado": False, "ativo_no_chat": False}
    def ce(nome, grupo): return resultados["condicoes"][nome]["avaliacao"][grupo]["perda"]["entropia_cruzada"]
    resultados["efeitos"] = {"realocacao_sem_replay_delta_ce_comum": ce("realocado_sem_replay", "comum_total") - ce("original_sem_replay", "comum_total"),
        "realocacao_com_replay_delta_ce_comum": ce("realocado_com_replay", "comum_total") - ce("original_com_replay", "comum_total"),
        "replay_lexico_original_delta_ce_total": ce("original_com_replay", "total") - ce("original_sem_replay", "total"),
        "replay_lexico_realocado_delta_ce_total": ce("realocado_com_replay", "total") - ce("realocado_sem_replay", "total")}
    resultados["integridade"] = {"contagens": protocolo["contagens_esperadas"], "parametros": protocolo["parametros"], "vocabulario": protocolo["vocabulario"], "avaliacao_final_conhecida_excluida": True, "pesos_promovidos": False, "ce_entre_lexicos_restrita_ao_suporte_comum": True}
    gravar_json("resultados.json", resultados); (OUT / "RELATORIO.md").write_text(markdown(resultados), encoding="utf-8")
    print(json.dumps({"suporte_comum": resultados["suporte_comum"], "efeitos": resultados["efeitos"], "condicoes": {k: {"ce_total": v["avaliacao"]["total"]["perda"]["entropia_cruzada"], "ce_comum": v["avaliacao"]["comum_total"]["perda"]["entropia_cruzada"], "exatas_antiga": v["avaliacao"]["antiga"]["geracao_livre"]["iguais_ao_alvo"], "exatas_nova": v["avaliacao"]["nova"]["geracao_livre"]["iguais_ao_alvo"], "oov_nao_copiavel_treino": v["cobertura_treino"]["ocorrencias_oov_nao_copiaveis"]} for k, v in resultados["condicoes"].items()}}, ensure_ascii=False, indent=2))


if __name__ == "__main__": executar()
