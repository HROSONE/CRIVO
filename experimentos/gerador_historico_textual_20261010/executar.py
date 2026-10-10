"""Treino e avaliação textual isolados: nenhuma alteração no motor/site."""
import argparse
import gzip
import hashlib
import json
import os
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

DIR = Path(__file__).resolve().parent
RAIZ = DIR.parents[1]
sys.path.insert(0, str(RAIZ))
from dialogo_seq2seq import DialogoSeq2Seq, fonte_dialogo, tokenizar, vocabulario_treino
from arquivos_contextuais import ler_json
from treinar_dialogo_seq2seq import checkpoint, inicializar, ler_corpus, treinar


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gravar(nome, dados):
    (DIR / nome).write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False)+"\n")


def protocolo():
    p = json.loads((DIR / "protocolo.json").read_text())
    if sha(DIR / "avaliacao_congelada.json") != p["sha256_avaliacao"]:
        raise ValueError("Avaliação modificada após congelamento")
    return p


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.casefold()) if not unicodedata.combining(c))


def triagem(saida, turno):
    texto = normalizar(saida["texto"])
    grupos = turno["exige_qualquer_por_grupo"]
    ausentes = [g for g in grupos if not any(normalizar(t) in texto for t in g)]
    proibidos = [t for t in turno["proibidos"] if normalizar(t) in texto]
    tokens = saida["tokens"]
    repeticoes = len(tokens)-len(set(tokens))
    return {"passou_triagem": bool(texto.strip()) and saida["completa"] and not ausentes and not proibidos,
            "grupos_ausentes": ausentes, "proibidos_presentes": proibidos,
            "repeticoes_tokens": repeticoes,
            "limite": "presença lexical não prova sentido correto nem detecta toda invenção; revisão obrigatória"}


def avaliar(modelo, modo="com_historico"):
    p = protocolo()
    avaliacao = json.loads((DIR / "avaliacao_congelada.json").read_text())
    sessoes = []
    for sessao in avaliacao["sessoes"]:
        historico, turnos = [], []
        for turno in sessao["turnos"]:
            usado = [] if modo == "sem_historico" else list(reversed(historico)) if modo == "ordem_inversa" else historico
            bruto = 1+len(tokenizar(turno["mensagem"]))+sum(1+len(tokenizar(h["texto"])) for h in usado)
            saida = modelo.gerar(turno["mensagem"], usado, **p["decodificacao"])
            turnos.append({"mensagem": turno["mensagem"], "historico_fornecido": usado.copy(),
                "saida": saida, "triagem": triagem(saida, turno),
                "tokens_fonte_sem_truncamento": bruto, "truncou_fonte": bruto>modelo.limite_fonte})
            # Rollout REAL: nunca inserir resposta-alvo/correção pelo juiz.
            historico += [{"papel": "usuario", "texto": turno["mensagem"]},
                          {"papel": "assistente", "texto": saida["texto"]}]
        sessoes.append({"id": sessao["id"], "turnos": turnos,
                        "passou_triagem_todos_turnos": all(t["triagem"]["passou_triagem"] for t in turnos)})
    dono = avaliacao["pedido_do_dono"]
    resposta_dono = modelo.gerar(dono["mensagem"], [], **p["decodificacao"])
    turnos = [t for s in sessoes for t in s["turnos"]]
    return {"modo": modo, "avaliacao_sha256": p["sha256_avaliacao"],
        "juiz_sha256": sha(__file__), "sessoes_triagem": sum(s["passou_triagem_todos_turnos"] for s in sessoes),
        "sessoes_total": len(sessoes), "turnos_triagem": sum(t["triagem"]["passou_triagem"] for t in turnos),
        "turnos_total": len(turnos), "completas": sum(t["saida"]["completa"] for t in turnos),
        "turnos_com_proibidos": sum(bool(t["triagem"]["proibidos_presentes"]) for t in turnos),
        "fontes_truncadas": sum(t["truncou_fonte"] for t in turnos),
        "respostas_distintas": len({t["saida"]["texto"] for t in turnos}),
        "sessoes": sessoes, "pedido_do_dono": {"mensagem": dono["mensagem"], "saida": resposta_dono,
            "avaliacao": "revisão qualitativa; pedido reservado, sem treino"},
        "aprovado": False, "ativo_no_chat": False}


def controles():
    p = protocolo(); h = p["hiperparametros"]
    treino, _ = ler_corpus(DIR / "corpus.json")
    vocab = vocabulario_treino(treino, h["vocab_max"])
    pesos = inicializar(vocab, h["ocultos"], h["embeddings"], h["buckets"], h["semente"])
    n = sum(a.size for a in pesos.values())
    if n>p["limite_parametros"]:
        raise ValueError("Orçamento de parâmetros excedido")
    dados = checkpoint(pesos, vocab, h["ocultos"], h["embeddings"], h["buckets"], h["limite_fonte"],
                       aprovado=False, ativo_no_chat=False)
    gravar("antes_aleatorio.json", avaliar(DialogoSeq2Seq(dados)))
    gravar("antes_seq2seq_existente.json", avaliar(DialogoSeq2Seq(ler_json(RAIZ / "rede_dialogo_seq2seq.json.gz"))))
    print(json.dumps({"parametros": n, "vocabulario": len(vocab), "controles": "concluídos"}))


def treinamento():
    p = protocolo(); h = p["hiperparametros"]
    if (DIR / "checkpoint.json.gz").exists():
        raise ValueError("Preservar checkpoint já treinado; usar outro experimento para novo treino")
    corpus_sha = sha(DIR / "corpus.json")
    destino = DIR / "checkpoint_treino.json"
    inicio = time.monotonic()
    resultado = treinar(DIR / "corpus.json", destino, **h)
    dados = json.loads(destino.read_text())
    dados.update(aprovado=False, ativo_no_chat=False,
                 experimento="gerador_historico_textual_20261010", sha256_corpus=corpus_sha,
                 sha256_avaliacao_reservada=p["sha256_avaliacao"])
    if dados["treino"]["parametros"]>p["limite_parametros"] or sha(DIR / "corpus.json")!=corpus_sha:
        raise ValueError("Modelo excedeu orçamento ou corpus mudou durante treino")
    serializado = (json.dumps(dados, ensure_ascii=False, separators=(",", ":"), allow_nan=False)+"\n").encode()
    (DIR / "checkpoint.json.gz").write_bytes(gzip.compress(serializado, mtime=0))
    destino.unlink()  # arquivo temporário de serialização; pesos finais acima
    resultado["manifesto"] = {"checkpoint_sha256": sha(DIR / "checkpoint.json.gz"),
        "corpus_sha256": corpus_sha, "avaliacao_sha256": p["sha256_avaliacao"],
        "protocolo_sha256": sha(DIR / "protocolo.json"),
        "treinador_sha256": sha(RAIZ / "treinar_dialogo_seq2seq.py"),
        "arquitetura_sha256": sha(RAIZ / "dialogo_seq2seq.py"),
        "script_sha256": sha(__file__), "numpy": __import__("numpy").__version__,
        "segundos_total": round(time.monotonic()-inicio, 2),
        "pesos_iniciais": "aleatórios próprios, seed 173; nenhum checkpoint externo",
        "threads": {k: os.environ.get(k) for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")},
        "aprovado": False, "ativo_no_chat": False}
    gravar("treino.json", resultado)
    print(json.dumps(resultado["manifesto"], ensure_ascii=False), flush=True)


def depois():
    modelo = DialogoSeq2Seq(ler_json(DIR / "checkpoint.json.gz"))
    resumos = {}
    for modo in ("com_historico", "sem_historico", "ordem_inversa"):
        resultado = avaliar(modelo, modo)
        gravar("depois_"+modo+".json", resultado)
        resumos[modo] = {k: resultado[k] for k in ("sessoes_triagem", "turnos_triagem", "turnos_total", "fontes_truncadas")}
    gravar("resumo_automatico.json", resumos)
    print(json.dumps(resumos, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=("antes", "treinar", "depois"))
    args = ap.parse_args()
    {"antes": controles, "treinar": treinamento, "depois": depois}[args.etapa]()
