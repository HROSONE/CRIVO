"""Curva de replay 0x/1x/2x para o gerador textual próprio.

0x e 1x reutilizam checkpoints já congelados. Só 2x é treinado nesta fase.
O holdout final conhecido do PR #137 não é importado nem lido.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ANT = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
ABL = RAIZ / "experimentos" / "ablacao_lexico_replay_20261010"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq
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


def separar_corpus(protocolo):
    corpus_path = ANT / "corpus_sessoes.json.gz"
    init_path = ANT / "inicializacao_sessoes.json.gz"
    if sha256(corpus_path) != protocolo["sha256_congelados"]["corpus_sessoes"]:
        raise ValueError("corpus de sessoes mudou")
    if sha256(init_path) != protocolo["sha256_congelados"]["inicializacao_realocada"]:
        raise ValueError("inicializacao realocada mudou")

    corpus = ler_json(corpus_path)
    treino = [e for e in corpus["exemplos"] if e["split"] == "treino"]
    validacao = [e for e in corpus["exemplos"] if e["split"] == "validacao"]
    replay = [e for e in treino if e.get("grupo") == "replay_legado"]
    novo = [e for e in treino if e.get("grupo") != "replay_legado"]
    dev_nova = [e for e in validacao if e.get("grupo") == "sessao_completa"]
    dev_antiga = [e for e in validacao if e.get("grupo") != "sessao_completa"]

    obtido = {
        "treino_novo_sem_replay": len(novo),
        "replay_unico": len(replay),
        "treino_0x": len(novo),
        "treino_1x": len(novo) + len(replay),
        "treino_2x": len(novo) + 2 * len(replay),
        "validacao_antiga": len(dev_antiga),
        "validacao_nova": len(dev_nova),
        "validacao_total": len(validacao),
    }
    if obtido != protocolo["contagens_esperadas"]:
        raise ValueError(f"contagens mudaram: {obtido}")

    replay_2x = []
    for copia in (1, 2):
        for e in replay:
            duplicado = dict(e)
            duplicado["dose_replay_copia"] = copia
            replay_2x.append(duplicado)
    corpus_2x = dict(corpus)
    corpus_2x["origem"] = (
        "Curva de replay: preserva os 2700 exemplos novos e inclui duas copias "
        "deterministicas dos mesmos 999 exemplos replay_legado. Validacao identica."
    )
    corpus_2x["exemplos"] = novo + replay_2x + validacao
    path_2x = OUT / "corpus_replay_2x.json.gz"
    gravar_gz(path_2x, corpus_2x)
    return path_2x, dev_antiga, dev_nova


def avaliar_checkpoint(path: Path, dev_antiga, dev_nova):
    dados = ler_json(path)
    if len(dados["vocabulario"]) != 720:
        raise ValueError(f"{path.name}: vocabulario inesperado")
    modelo = DialogoSeq2Seq(dados)
    grupos = {
        "antiga": [texto(e) for e in dev_antiga],
        "nova": [texto(e) for e in dev_nova],
        "total": [texto(e) for e in dev_antiga + dev_nova],
    }
    saida = {}
    for nome, casos in grupos.items():
        perda = avaliar_perda(
            modelo.pesos, casos, modelo.indices, modelo.buckets,
            modelo.limite_fonte, 64, lote_tamanho=32,
        )
        livre = avaliar_geracao(dados, casos, limite_resposta=64, maximo=None, semente=179)
        saida[nome] = {
            "entropia_cruzada": perda["entropia_cruzada"],
            "perplexidade": perda["perplexidade"],
            "tokens": perda["tokens"],
            "exemplos": livre["exemplos"],
            "completas": livre["completas"],
            "iguais_ao_alvo": livre["iguais_ao_alvo"],
        }
    return saida


def treinar_2x(corpus_2x: Path, protocolo):
    destino = OUT / "checkpoint_replay_2x.json.gz"
    if destino.exists():
        dados = ler_json(destino)
        return destino, {"reutilizado": True, "epoca_selecionada": dados.get("treino", {}).get("epoca_selecionada")}
    tmp = OUT / ".checkpoint_replay_2x.tmp.json"
    inicio = time.monotonic()
    rel = treinar(
        corpus_2x,
        tmp,
        checkpoint_inicial=ANT / "inicializacao_sessoes.json.gz",
        **protocolo["hiperparametros"],
    )
    dados = ler_json(tmp)
    if dados["treino"]["parametros"] != protocolo["modelo"]["parametros"]:
        raise ValueError("capacidade do modelo mudou")
    dados.update(
        aprovado=False,
        ativo_no_chat=False,
        experimento="curva-replay-20261010",
        dose_replay=2,
    )
    gravar_gz(destino, dados)
    tmp.unlink()
    return destino, {
        "reutilizado": False,
        "segundos": round(time.monotonic() - inicio, 3),
        "epoca_selecionada": dados["treino"]["epoca_selecionada"],
        "validacao_treinador": rel["validacao"],
    }


def b(v):
    return "sim" if v else "não"


def relatorio(r):
    linhas = [
        "# Curva de replay — 10/10/2026",
        "",
        "Mesma rede, mesmo léxico realocado, mesmo corpus novo, mesma validação e mesmos hiperparâmetros. "
        "0× e 1× são checkpoints já congelados; **somente 2× foi treinado nesta fase**. "
        "O holdout final conhecido do PR #137 não foi lido.",
        "",
        "| Dose | Treino | CE antiga | Exatas antigas | CE nova | Exatas novas | CE total |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for dose in (0, 1, 2):
        c = r["doses"][str(dose)]
        linhas.append(
            f"| {dose}× | {c['treino_exemplos']} | {c['avaliacao']['antiga']['entropia_cruzada']:.6f} | "
            f"{c['avaliacao']['antiga']['iguais_ao_alvo']}/334 | {c['avaliacao']['nova']['entropia_cruzada']:.6f} | "
            f"{c['avaliacao']['nova']['iguais_ao_alvo']}/94 | {c['avaliacao']['total']['entropia_cruzada']:.6f} |"
        )
    cr = r["criterio_2x_vs_1x"]
    linhas += [
        "",
        "## Critério pré-congelado: 2× contra 1×",
        "",
        f"- Reter antigo: **{b(cr['reter_antigo'])}**.",
        f"- Não regredir novo: **{b(cr['nao_regredir_novo'])}**.",
        f"- Melhorar CE nova: **{b(cr['melhorar_novo'])}**.",
        f"- Sucesso conjunto: **{b(cr['sucesso_conjunto'])}**.",
        "",
        "## Limites",
        "",
        "- Oversampling também aumenta o número de atualizações por época; esta fase mede a dose efetiva no procedimento atual.",
        "- Correspondência literal é diagnóstico, não medida completa de naturalidade/compreensão.",
        "- O desenvolvimento é conhecido; nenhum destes checkpoints pode ser promovido por esta fase.",
        "- O holdout final de 10 sessões do PR #137 continua excluído e conhecido.",
    ]
    return "\n".join(linhas) + "\n"


def executar():
    protocolo = ler_json(OUT / "protocolo.json")
    corpus_2x, dev_antiga, dev_nova = separar_corpus(protocolo)

    caminhos = {
        "0": ABL / "checkpoint_realocado_sem_replay.json.gz",
        "1": ANT / "checkpoint_sessoes.json.gz",
    }
    chk2, meta2 = treinar_2x(corpus_2x, protocolo)
    caminhos["2"] = chk2

    init = ler_json(ANT / "inicializacao_sessoes.json.gz")
    vocab_init = init["vocabulario"]
    for dose, path in caminhos.items():
        dados = ler_json(path)
        if dados["vocabulario"] != vocab_init:
            raise ValueError(f"dose {dose} usa vocabulario diferente")

    contagens = protocolo["contagens_esperadas"]
    resultados = {
        "base_commit": protocolo["base_commit"],
        "holdout_final_lido": False,
        "aprovado": False,
        "ativo_no_chat": False,
        "doses": {},
    }
    for dose, path in caminhos.items():
        resultados["doses"][dose] = {
            "checkpoint": str(path.relative_to(RAIZ)),
            "checkpoint_sha256": sha256(path),
            "treino_exemplos": contagens[f"treino_{dose}x"],
            "avaliacao": avaliar_checkpoint(path, dev_antiga, dev_nova),
            "novo_treino_nesta_fase": dose == "2",
        }
    resultados["doses"]["2"]["treino"] = meta2

    d1 = resultados["doses"]["1"]["avaliacao"]
    d2 = resultados["doses"]["2"]["avaliacao"]
    criterio = {
        "reter_antigo": (
            d2["antiga"]["iguais_ao_alvo"] >= d1["antiga"]["iguais_ao_alvo"]
            and d2["antiga"]["entropia_cruzada"] <= d1["antiga"]["entropia_cruzada"]
        ),
        "nao_regredir_novo": d2["nova"]["iguais_ao_alvo"] >= d1["nova"]["iguais_ao_alvo"],
        "melhorar_novo": d2["nova"]["entropia_cruzada"] < d1["nova"]["entropia_cruzada"],
    }
    criterio["sucesso_conjunto"] = all(criterio.values())
    resultados["criterio_2x_vs_1x"] = criterio
    resultados["integridade"] = {
        "parametros": protocolo["modelo"]["parametros"],
        "vocabulario": protocolo["modelo"]["vocabulario"],
        "realocacoes_lexicais": protocolo["modelo"]["realocacoes_lexicais"],
        "mesmo_vocabulario_nas_tres_doses": True,
        "checkpoint_publico_alterado": False,
        "holdout_final_excluido": True,
    }
    gravar_json(OUT / "resultados.json", resultados)
    (OUT / "RELATORIO.md").write_text(relatorio(resultados), encoding="utf-8")
    print(json.dumps({"criterio": criterio, "doses": {d: {
        "antiga_ce": x["avaliacao"]["antiga"]["entropia_cruzada"],
        "antiga_exatas": x["avaliacao"]["antiga"]["iguais_ao_alvo"],
        "nova_ce": x["avaliacao"]["nova"]["entropia_cruzada"],
        "nova_exatas": x["avaliacao"]["nova"]["iguais_ao_alvo"],
    } for d, x in resultados["doses"].items()}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
