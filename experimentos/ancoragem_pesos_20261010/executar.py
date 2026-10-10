"""Experimento de ancoragem L2-SP dos pesos preservados do gerador.

Treina um único candidato a partir da mesma inicialização/corpus 1x do PR #137.
A força da âncora é calibrada exclusivamente com treino e a trajetória do
controle 1x. O holdout final conhecido do PR #137 não é importado.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR = Path(__file__).resolve().parent
BASE = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, tokenizar
from treinar_dialogo_seq2seq import (
    assinatura,
    avaliar_geracao,
    avaliar_perda,
    checkpoint,
    ler_corpus,
    lote,
    perda_gradientes,
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar_json(path: Path, dados) -> None:
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def gravar_gz(path: Path, dados) -> None:
    bruto = (json.dumps(dados, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    path.write_bytes(gzip.compress(bruto, mtime=0))


def texto(ex):
    return {"mensagem": ex["mensagem"], "historico": ex.get("historico", []), "resposta": ex["resposta"]}


def carregar_arrays(path: Path):
    import numpy as np
    dados = ler_json(path)
    return dados, {k: np.asarray(v, dtype=np.float32).copy() for k, v in dados["pesos"].items()}


def construir_mascara(pesos, indices_livres):
    import numpy as np
    mascara = {k: np.ones_like(v, dtype=np.float32) for k, v in pesos.items()}
    livres = np.asarray(sorted(indices_livres), dtype=np.int64)
    mascara["E"][livres, :] = 0
    mascara["O"][:, livres] = 0
    mascara["bo"][livres] = 0
    return mascara


def norma_mascarada(valores, mascara):
    return math.sqrt(sum(float(((valores[k] * mascara[k]) ** 2).sum()) for k in valores))


def distancia(pesos, ancora, mascara):
    return math.sqrt(sum(float((((pesos[k] - ancora[k]) * mascara[k]) ** 2).sum()) for k in pesos))


def calibrar_lambda(treino, controle, ancora, mascara, indices, protocolo):
    import numpy as np
    cfg = protocolo["ancoragem"]["calibracao"]
    rng = np.random.default_rng(cfg["semente"])
    ordem = rng.permutation(len(treino)).tolist()
    lote_tamanho = protocolo["hiperparametros"]["lote_tamanho"]
    normas = []
    for b in range(cfg["batches"]):
        pos = ordem[b * lote_tamanho:(b + 1) * lote_tamanho]
        if not pos:
            break
        batch = lote(
            [treino[i] for i in pos], indices,
            protocolo["hiperparametros"]["buckets"],
            protocolo["hiperparametros"]["limite_fonte"],
            protocolo["hiperparametros"]["limite_resposta"],
        )
        _, grad = perda_gradientes(controle, batch)
        normas.append(norma_mascarada(grad, mascara))
    if len(normas) != cfg["batches"]:
        raise ValueError("Batches insuficientes para calibrar a ancoragem")
    deslocamento = distancia(controle, ancora, mascara)
    if deslocamento <= 0:
        raise ValueError("Controle não se afastou da âncora")
    mediana = float(np.median(np.asarray(normas, dtype=np.float64)))
    forca = float(cfg["alvo_razao_normas"] * mediana / deslocamento)
    if not math.isfinite(forca) or forca <= 0:
        raise ValueError("Força de ancoragem inválida")
    return {
        "lambda": forca,
        "norma_gradiente_tarefa_mediana": mediana,
        "normas_gradiente_tarefa": normas,
        "norma_deslocamento_controle": deslocamento,
        "alvo_razao_normas": cfg["alvo_razao_normas"],
    }


def validar_mascara(mascara, indices_livres, vocabulario):
    import numpy as np
    livres = set(indices_livres)
    if len(livres) != 151 or len(vocabulario) != 720:
        raise ValueError("Realocação/vocabulário inesperados")
    for i in range(len(vocabulario)):
        esperado = 0.0 if i in livres else 1.0
        if not np.all(mascara["E"][i] == esperado):
            raise ValueError("Máscara E incorreta")
        if not np.all(mascara["O"][:, i] == esperado):
            raise ValueError("Máscara O incorreta")
        if float(mascara["bo"][i]) != esperado:
            raise ValueError("Máscara bo incorreta")
    for k, m in mascara.items():
        if k not in ("E", "O", "bo") and not np.all(m == 1):
            raise ValueError(f"Peso preservado não totalmente ancorado: {k}")
    return True


def treinar_ancorado(corpus_path: Path, destino: Path, protocolo):
    import numpy as np
    hp = protocolo["hiperparametros"]
    treino, validacao = ler_corpus(
        corpus_path,
        limite_fonte=hp["limite_fonte"],
        limite_resposta=hp["limite_resposta"],
    )
    if len(treino) != protocolo["treino"]["exemplos"] or len(validacao) != protocolo["treino"]["validacao_total"]:
        raise ValueError("Contagens do corpus mudaram")

    init_path = RAIZ / protocolo["treino"]["checkpoint_inicial_e_ancora"]
    controle_path = RAIZ / protocolo["controle"]["checkpoint"]
    realoc_path = RAIZ / protocolo["treino"]["realocacoes"]
    init_dados, ancora = carregar_arrays(init_path)
    controle_dados, controle = carregar_arrays(controle_path)
    if init_dados["vocabulario"] != controle_dados["vocabulario"]:
        raise ValueError("Controle e âncora usam vocabulários diferentes")
    vocabulario = list(init_dados["vocabulario"])
    if len(vocabulario) != hp["vocab_max"]:
        raise ValueError("Vocabulário inesperado")
    p = {k: v.copy() for k, v in ancora.items()}
    indices = {t: i for i, t in enumerate(vocabulario)}

    realoc = ler_json(realoc_path)
    indices_livres = [int(t["indice"]) for t in realoc["trocas"]]
    mascara_ancora = construir_mascara(p, indices_livres)
    validar_mascara(mascara_ancora, indices_livres, vocabulario)
    calibracao = calibrar_lambda(treino, controle, ancora, mascara_ancora, indices, protocolo)
    lam = calibracao["lambda"]

    momentos = {k: np.zeros_like(a) for k, a in p.items()}
    quadrados = {k: np.zeros_like(a) for k, a in p.items()}
    rng = np.random.default_rng(hp["semente"])
    passo = 0
    entropias = []
    validacoes = []
    distancias = []
    melhor = None
    melhor_valor = float("inf")
    melhor_epoca = 0
    sem_melhoria = 0
    inicio = time.monotonic()

    print("Parâmetros", sum(a.size for a in p.values()), "vocabulário", len(vocabulario),
          "exemplos", len(treino), "lambda", lam, flush=True)

    for epoca in range(hp["epocas"]):
        taxa_amostragem = min(
            hp["amostragem"],
            hp["amostragem"] * max(0, epoca - hp["aquecimento"] + 1) / 3,
        )
        ordem = rng.permutation(len(treino)).tolist()
        tokens_total = 0
        perda_total = 0.0
        grupos = [ordem[j:j + hp["lote_tamanho"] * 8] for j in range(0, len(ordem), hp["lote_tamanho"] * 8)]
        batches = []
        for grupo in grupos:
            grupo.sort(key=lambda i: len(tokenizar(treino[i]["mensagem"])) +
                       sum(len(tokenizar(h["texto"])) for h in treino[i].get("historico", [])))
            batches += [grupo[j:j + hp["lote_tamanho"]] for j in range(0, len(grupo), hp["lote_tamanho"])]
        rng.shuffle(batches)

        for pos in batches:
            batch = lote([treino[i] for i in pos], indices, hp["buckets"], hp["limite_fonte"], hp["limite_resposta"])
            perda, g = perda_gradientes(
                p, batch,
                dropout=hp["dropout"],
                dropout_tokens=hp["dropout_tokens"],
                amostragem=taxa_amostragem,
                rng=rng,
            )
            n = int(batch["mascara"].sum())
            if not math.isfinite(perda) or any(not np.isfinite(a).all() for a in g.values()):
                raise ValueError("Treinamento produziu perda ou gradiente não finito")
            for k in g:
                g[k] += lam * mascara_ancora[k] * (p[k] - ancora[k])
            if any(not np.isfinite(a).all() for a in g.values()):
                raise ValueError("Ancoragem produziu gradiente não finito")
            tokens_total += n
            perda_total += perda * n
            norma = math.sqrt(sum(float((a * a).sum()) for a in g.values()))
            escala = min(1.0, 5 / max(norma, 1e-12))
            passo += 1
            for k in p:
                dg = g[k] * escala
                momentos[k] = .9 * momentos[k] + .1 * dg
                quadrados[k] = .999 * quadrados[k] + .001 * dg * dg
                p[k] -= hp["taxa"] * (momentos[k] / (1 - .9 ** passo)) / (
                    np.sqrt(quadrados[k] / (1 - .999 ** passo)) + 1e-8
                )
                if p[k].ndim == 2:
                    p[k] *= 1 - hp["taxa"] * hp["decaimento"]

        media = perda_total / max(1, tokens_total)
        entropias.append(media)
        dist = distancia(p, ancora, mascara_ancora)
        distancias.append(dist)
        print("Época", epoca + 1, "CE treino", round(media, 4), "distância", round(dist, 4),
              "segundos", round(time.monotonic() - inicio, 1), flush=True)

        if (epoca + 1) % hp["validar_cada"] == 0 or epoca + 1 == hp["epocas"]:
            medicao = avaliar_perda(
                p, validacao, indices, hp["buckets"], hp["limite_fonte"], hp["limite_resposta"], hp["lote_tamanho"]
            )
            validacoes.append(dict(epoca=epoca + 1, distancia_ancora_preservada=dist, **medicao))
            valor = medicao["entropia_cruzada"]
            print("Validação", epoca + 1, "CE", round(valor, 4), flush=True)
            if valor < melhor_valor - 1e-5:
                melhor_valor = valor
                melhor_epoca = epoca + 1
                melhor = {k: a.copy() for k, a in p.items()}
                sem_melhoria = 0
            else:
                sem_melhoria += hp["validar_cada"]
            if sem_melhoria >= hp["paciencia"]:
                print("Parada por validação; melhor época", melhor_epoca, flush=True)
                break

    if melhor is not None:
        p = melhor

    meta = {
        "arquitetura": "BiGRU encoder + GRU decoder + atenção e pointer-generator",
        "assinatura_treino": assinatura(treino),
        "assinatura_validacao": assinatura(validacao),
        "treino": {
            "epocas_solicitadas": hp["epocas"],
            "epocas": len(entropias),
            "epoca_selecionada": melhor_epoca,
            "validar_cada": hp["validar_cada"],
            "paciencia": hp["paciencia"],
            "dropout_locked": hp["dropout"],
            "dropout_lexical_fonte": hp["dropout_tokens"],
            "scheduled_sampling_max": hp["amostragem"],
            "scheduled_sampling_aquecimento": hp["aquecimento"],
            "lote": hp["lote_tamanho"],
            "semente": hp["semente"],
            "taxa": hp["taxa"],
            "decaimento": hp["decaimento"],
            "exemplos": len(treino),
            "parametros": sum(a.size for a in p.values()),
            "entropias": entropias,
            "validacoes": validacoes,
            "distancias_ancora_preservada": distancias,
            "segundos": round(time.monotonic() - inicio, 2),
            "regularizacao": "L2-SP somente nos pesos preservados; E/O/bo dos 151 índices realocados ficam livres.",
        },
        "checkpoint_inicial": {
            "arquivo": str(init_path.relative_to(RAIZ)),
            "sha256_arquivo": sha256(init_path),
            "vocabulario_preservado": True,
            "otimizador": "Adam novo; não é retomada exata",
        },
        "ancoragem": {
            **calibracao,
            "indices_lexicais_livres": indices_livres,
            "pesos_ancorados": [k for k in p],
            "mascara": "Todos os pesos preservados; E/O/bo dos 151 índices realocados excluídos.",
        },
        "limites": {"fonte_tokens": hp["limite_fonte"], "resposta_tokens": hp["limite_resposta"]},
        "limite": "Experimento de desenvolvimento conhecido; não demonstra conversa geral e não autoriza promoção.",
    }
    dados = checkpoint(p, vocabulario, hp["ocultos"], hp["embeddings"], hp["buckets"], hp["limite_fonte"], **meta)
    dados.update(aprovado=False, ativo_no_chat=False, experimento="ancoragem-pesos-20261010")
    gravar_gz(destino, dados)
    return dados, meta


def avaliar_checkpoint(dados, grupos, hp):
    modelo = DialogoSeq2Seq(dados)
    saida = {}
    for nome, casos in grupos.items():
        perda = avaliar_perda(
            {k: __import__("numpy").asarray(v, dtype="float32") for k, v in dados["pesos"].items()},
            casos, modelo.indices, modelo.buckets, modelo.limite_fonte, hp["limite_resposta"], hp["lote_tamanho"]
        )
        ger = avaliar_geracao(dados, casos, hp["limite_resposta"], maximo=None, semente=hp["semente"])
        saida[nome] = {
            "entropia_cruzada": perda["entropia_cruzada"],
            "perplexidade": perda["perplexidade"],
            "exemplos": ger["exemplos"],
            "completas": ger["completas"],
            "iguais_ao_alvo": ger["iguais_ao_alvo"],
        }
    return saida


def relatorio(resultado):
    c = resultado["controle"]
    a = resultado["ancorado"]
    k = resultado["criterio"]
    sim = lambda x: "sim" if x else "não"
    return f"""# Ancoragem dos pesos — 10/10/2026

Controle 1× e candidato ancorado usam o mesmo corpus, vocabulário realocado, arquitetura e hiperparâmetros. A única mudança do candidato é a regularização L2-SP dos pesos preservados. Os 151 índices lexicais realocados ficam livres em `E`, `O` e `bo`.

A força foi calibrada **sem validação**: 16 batches do treino no checkpoint controle, alvo de 25% da norma do gradiente de tarefa antes do Adam. `lambda = {resultado['calibracao']['lambda']:.10g}`.

| Condição | CE antiga | Exatas antigas | CE nova | Exatas novas | CE total |
|---|---:|---:|---:|---:|---:|
| controle 1× | {c['antiga']['entropia_cruzada']:.6f} | {c['antiga']['iguais_ao_alvo']}/334 | {c['nova']['entropia_cruzada']:.6f} | {c['nova']['iguais_ao_alvo']}/94 | {c['total']['entropia_cruzada']:.6f} |
| 1× + âncora | {a['antiga']['entropia_cruzada']:.6f} | {a['antiga']['iguais_ao_alvo']}/334 | {a['nova']['entropia_cruzada']:.6f} | {a['nova']['iguais_ao_alvo']}/94 | {a['total']['entropia_cruzada']:.6f} |

## Critério pré-congelado

- Reter antigo: **{sim(k['reter_antigo'])}**.
- Melhorar CE nova: **{sim(k['melhorar_novo'])}**.
- Não regredir exatas novas: **{sim(k['nao_regredir_novo'])}**.
- Sucesso conjunto: **{sim(k['sucesso_conjunto'])}**.

## Integridade

- Holdout final conhecido do PR #137 lido: **não**.
- Promoção permitida nesta fase: **não**.
- Runtime/checkpoint público alterado: **não**.
- Arquitetura/parâmetros/modelos externos: **inalterados**.

## Limites

A avaliação usa desenvolvimento conhecido e autoral. Correspondência literal não mede naturalidade/compreensão. A calibração da âncora usa normas antes do Adam; o otimizador é adaptativo, portanto 25% é uma escala de gradiente, não uma razão garantida de deslocamento.
"""


def executar():
    protocolo = ler_json(DIR / "protocolo.json")
    hp = protocolo["hiperparametros"]
    corpus_path = RAIZ / protocolo["treino"]["corpus"]
    bruto = ler_json(corpus_path)
    validacao_bruta = [e for e in bruto["exemplos"] if e.get("split") == "validacao"]
    dev_nova = [texto(e) for e in validacao_bruta if e.get("grupo") == "sessao_completa"]
    dev_antiga = [texto(e) for e in validacao_bruta if e.get("grupo") != "sessao_completa"]
    if len(dev_antiga) != 334 or len(dev_nova) != 94:
        raise ValueError("Partição antiga/nova mudou")
    grupos = {"antiga": dev_antiga, "nova": dev_nova, "total": dev_antiga + dev_nova}

    controle_dados = ler_json(RAIZ / protocolo["controle"]["checkpoint"])
    controle_eval = avaliar_checkpoint(controle_dados, grupos, hp)

    destino = DIR / "checkpoint_ancorado.json.gz"
    candidato, meta = treinar_ancorado(corpus_path, destino, protocolo)
    candidato_eval = avaliar_checkpoint(candidato, grupos, hp)

    criterio = {
        "reter_antigo": (
            candidato_eval["antiga"]["entropia_cruzada"] <= controle_eval["antiga"]["entropia_cruzada"]
            and candidato_eval["antiga"]["iguais_ao_alvo"] >= controle_eval["antiga"]["iguais_ao_alvo"]
        ),
        "melhorar_novo": candidato_eval["nova"]["entropia_cruzada"] < controle_eval["nova"]["entropia_cruzada"],
        "nao_regredir_novo": candidato_eval["nova"]["iguais_ao_alvo"] >= controle_eval["nova"]["iguais_ao_alvo"],
    }
    criterio["sucesso_conjunto"] = all(criterio.values())
    resultado = {
        "base_commit": protocolo["base_commit"],
        "controle": controle_eval,
        "ancorado": candidato_eval,
        "calibracao": meta["ancoragem"],
        "criterio": criterio,
        "holdout_final_lido": False,
        "aprovado": False,
        "ativo_no_chat": False,
        "checkpoint_ancorado_sha256": sha256(destino),
        "integridade": {
            "parametros": sum(__import__("numpy").asarray(v).size for v in candidato["pesos"].values()),
            "vocabulario": len(candidato["vocabulario"]),
            "indices_realocados_livres": len(meta["ancoragem"]["indices_lexicais_livres"]),
            "checkpoint_publico_alterado": False,
        },
    }
    gravar_json(DIR / "resultados.json", resultado)
    (DIR / "RELATORIO.md").write_text(relatorio(resultado), encoding="utf-8")
    print(json.dumps({
        "lambda": resultado["calibracao"]["lambda"],
        "criterio": criterio,
        "controle": {g: {"ce": controle_eval[g]["entropia_cruzada"], "exatas": controle_eval[g]["iguais_ao_alvo"]} for g in grupos},
        "ancorado": {g: {"ce": candidato_eval[g]["entropia_cruzada"], "exatas": candidato_eval[g]["iguais_ao_alvo"]} for g in grupos},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
