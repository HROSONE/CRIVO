"""Congela os dados do Pointer/Copy Causal v3 antes de qualquer treino.

Uso: python preparar_v3.py
Gera, nesta pasta:
- blind_regressao_v2.json: as 100 entidades do blind do v2, reproduzidas pelo
  próprio código do notebook v2, com os 600 casos no formato antigo (IDs colados,
  só para regressão) e os mesmos 600 casos no formato real do runtime;
- blind_novo_v3.json: 100 entidades novas, disjuntas de tudo que o v2 usou,
  com os 600 casos no formato real do runtime;
- treino_dev_v3.json: entidades de treino (480) e dev (80), disjuntas dos dois blinds;
- manifesto.json: SHA-256 de cada arquivo e estatísticas de copiabilidade.
"""
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AQUI))

import linguagem_profunda as lp  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402
import dados_v3 as d  # noqa: E402

TOKENIZER = RAIZ / "artefatos" / "sentido_pt" / "tokenizer.json"
TOKENIZER_SHA = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"
NOTEBOOK_V2 = RAIZ / "notebooks" / "pointer_copy_causal_v2_colab.ipynb"
SEED = 20261012
CONTEXTO = 256
VOCAB = 8192


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gravar(nome, obj):
    caminho = AQUI / nome
    caminho.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n",
                       encoding="utf-8")
    return sha(caminho)


def reproduzir_v2(tokenizer):
    """Executa as células 5 e 6 do notebook v2 (splits e tarefas) sem alteração."""
    nb = json.loads(NOTEBOOK_V2.read_text(encoding="utf-8"))
    codigo = [''.join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    ids = {s: tokenizer.token_to_id(s) for s in lp.ESPECIAIS}
    cfg = type("Cfg", (), {"vocabulario": VOCAB, "contexto": CONTEXTO})()
    ns = {
        "random": random, "re": re, "json": json, "Counter": Counter,
        "defaultdict": defaultdict, "SEED": SEED, "tokenizer": tokenizer,
        "cfg": cfg, "lp": lp, "ESPECIAIS_SET": set(ids.values()),
        "ID_PAD": ids["<pad>"], "ID_USUARIO": ids["<usuario>"],
        "ID_ASSISTENTE": ids["<assistente>"], "ID_FIM": ids["<fim>"],
    }
    exec(compile(codigo[5], "v2_celula5", "exec"), ns)
    exec(compile(codigo[6], "v2_celula6", "exec"), ns)
    return ns


def balancear(pool, total, rr):
    """Metade close / metade distant; cota igual por comprimento dentro do grupo."""
    buckets = defaultdict(list)
    for e in pool:
        buckets[(e["grupo"], e["n_tokens"])].append(e)
    for k in sorted(buckets):
        rr.shuffle(buckets[k])
    escolhidos = []
    metade = {"close": total // 2, "distant": total - total // 2}
    for g in ("close", "distant"):
        chaves = sorted(((g, L) for L in (1, 2, 3, 4)), key=lambda k: (len(buckets[k]), k))
        restante = metade[g]
        for idx, k in enumerate(chaves):
            faltam = len(chaves) - idx
            parte = restante if faltam == 1 else restante // faltam
            q = min(len(buckets[k]), parte)
            escolhidos += buckets[k][:q]
            restante -= q
        if restante:
            raise SystemExit(f"oferta insuficiente no grupo {g}")
    rr.shuffle(escolhidos)
    return escolhidos


def completar(entidades, offset):
    out = []
    for i, e in enumerate(entidades):
        z = {"nome": e["nome"], "grupo": e["grupo"], "n_tokens": e["n_tokens"]}
        z["categoria"] = d.CATEGORIAS[(i + offset) % len(d.CATEGORIAS)]
        z["material_a"] = ["madeira", "metal", "vidro", "tecido", "argila", "bambu"][(2 * i + offset) % 6]
        z["material_b"] = ["madeira", "metal", "vidro", "tecido", "argila", "bambu"][(2 * i + offset + 1) % 6]
        out.append(z)
    return out


def casos_naturais(tokenizer, entidades):
    casos = []
    for i, ent in enumerate(entidades):
        for j, tarefa in enumerate(d.TAREFAS):
            casos.append(d.montar_caso(lp, tokenizer, ent, tarefa, d.POSICOES[(i + j) % 3], CONTEXTO))
    return casos


def estat_copiabilidade(casos):
    por = {}
    for t in d.TAREFAS:
        xs = [c for c in casos if c["tarefa"] == t]
        tok = sum(sum(c["nome_resp"]) for c in xs)
        cop = sum(sum(c["copy_resp"]) for c in xs)
        primeiro = sum(c["copy_resp"][c["nome_resp"].index(True)] for c in xs)
        por[t] = {
            "tokens_do_nome_copiaveis": cop / tok,
            "primeiro_token_copiavel": primeiro / len(xs),
            "nome_inteiro_copiavel": sum(c["nome_todo_copiavel"] for c in xs) / len(xs),
        }
    return por


def main():
    if sha(TOKENIZER) != TOKENIZER_SHA:
        raise SystemExit("tokenizer diferente do usado pela base")
    tokenizer = Tokenizer.from_file(str(TOKENIZER))
    tokenizer.encode_special_tokens = True

    v2 = reproduzir_v2(tokenizer)
    blind_v2 = v2["BLIND_CONGELADO"]
    nomes_amostra = [blind_v2[i]["nome"] for i in range(4)]
    if nomes_amostra != ["entemente", "jkvx", "zedi", "anteriores"]:
        raise SystemExit(f"reprodução do blind v2 divergiu das amostras publicadas: {nomes_amostra}")
    usados_v2 = {e["nome"].casefold() for e in v2["TRAIN_ENT"] + v2["DEV_ENT"] + blind_v2}

    # Pool novo: mesmo universo de candidatos do v2, validado com a tokenização do runtime.
    proibidas = d.palavras_dos_modelos()
    especiais = {tokenizer.token_to_id(s) for s in lp.ESPECIAIS}
    vistos, pool = set(), []
    for nome, grupo in v2["universo_candidatos"]():
        k = nome.casefold()
        if k in vistos or k in proibidas:
            continue
        vistos.add(k)
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{2,19}", nome):
            continue
        meio = lp.codificar_texto(tokenizer, " " + nome)
        inicio = lp.codificar_texto(tokenizer, nome)
        if not (1 <= len(meio) <= 4 and 1 <= len(inicio) <= 4):
            continue
        if any(t in especiais for t in meio + inicio):
            continue
        if tokenizer.decode(meio).strip() != nome or tokenizer.decode(inicio).strip() != nome:
            continue
        pool.append({"nome": nome, "grupo": grupo, "n_tokens": len(meio)})

    rr = random.Random(SEED + 5005)
    candidatos_blind = [e for e in pool if e["nome"].casefold() not in usados_v2]
    blind_novo = completar(balancear(candidatos_blind, 100, rr), 2)
    casos_blind_novo = casos_naturais(tokenizer, blind_novo)

    excluir = {e["nome"].casefold() for e in blind_v2} | {e["nome"].casefold() for e in blind_novo}
    restantes = [e for e in pool if e["nome"].casefold() not in excluir]
    escolhidos = balancear(restantes, 560, random.Random(SEED + 6006))
    dev = completar(escolhidos[:80], 1)
    treino = completar(escolhidos[80:], 0)
    for ent in treino + dev:  # falha cedo se algum caso de treino/dev não montar
        for t in d.TAREFAS:
            for p in d.POSICOES:
                d.montar_caso(lp, tokenizer, ent, t, p, CONTEXTO)

    blind_v2_ent = [{k: e[k] for k in ("nome", "grupo", "n_tokens", "categoria", "material_a", "material_b")}
                    for e in blind_v2]
    for e in blind_v2_ent:  # comprimento no formato do runtime, para as métricas novas
        e["n_tokens_v2"] = e["n_tokens"]
        e["n_tokens"] = len(lp.codificar_texto(tokenizer, " " + e["nome"]))
    casos_legado = [{k: c[k] for k in ("nome", "nome_ids", "grupo", "n_tokens", "categoria", "cat_ids",
                                       "fun_ids", "tarefa", "posicao", "prompt_ids", "resp_ids", "copy_resp")}
                    for c in v2["BLIND_EX"]]
    casos_regressao_natural = casos_naturais(tokenizer, blind_v2_ent)

    nomes = lambda xs: {e["nome"].casefold() for e in xs}
    conjuntos = {"treino": treino, "dev": dev, "blind_v2": blind_v2_ent, "blind_novo": blind_novo}
    for a in conjuntos:
        for b in conjuntos:
            if a < b and nomes(conjuntos[a]) & nomes(conjuntos[b]):
                raise SystemExit(f"interseção entre {a} e {b}")
    if nomes(blind_novo) & usados_v2:
        raise SystemExit("blind novo reutiliza nome do v2")

    resumo = lambda xs: {"n": len(xs), "grupo": dict(Counter(e["grupo"] for e in xs)),
                         "tokens_runtime": dict(sorted(Counter(e["n_tokens"] for e in xs).items()))}
    shas = {
        "blind_novo_v3.json": gravar("blind_novo_v3.json", {
            "descricao": "Blind novo v3, formato real do runtime; congelado antes do treino.",
            "entidades": blind_novo, "casos": casos_blind_novo}),
        "blind_regressao_v2.json": gravar("blind_regressao_v2.json", {
            "descricao": "As 100 entidades do blind v2 (regressão conhecida).",
            "entidades": blind_v2_ent, "casos_legado_v2": casos_legado,
            "casos_formato_real": casos_regressao_natural}),
        "treino_dev_v3.json": gravar("treino_dev_v3.json", {"treino": treino, "dev": dev}),
    }
    manifesto = {
        "protocolo": "pointer_copy_causal_v3",
        "tokenizer_sha256": TOKENIZER_SHA,
        "base_pesos_sha256_esperado": "c0a56b1546495efafde5df99feebfa084fef414d512076d888b40c9828e4eb4e",
        "base_fingerprint_esperado": "257a4eb41406b9aeeee8f9cf0471c1d8423f769685643200d03c6886a1ea1566",
        "arquivos_sha256": shas,
        "dados_v3_py_sha256": sha(AQUI / "dados_v3.py"),
        "pool_runtime_valido": len(pool),
        "splits": {k: resumo(v) for k, v in conjuntos.items()},
        "copiabilidade_blind_novo": estat_copiabilidade(casos_blind_novo),
        "copiabilidade_blind_v2_formato_real": estat_copiabilidade(casos_regressao_natural),
    }
    (AQUI / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    print(json.dumps(manifesto, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
