"""Dados da fase 6b: o CRIVO aprende a conversar com conversas de pessoas, sem falas escritas por mim.

Decisão do criador (14/10/2026): "eu não quero que tu faça as falas dele, ele quem deve falar do
jeito que ele quiser". Nenhum alvo de treino aqui foi escrito pelo assistente nem por modelo de
linguagem:

1. OASST2 em português (Apache-2.0, revisão fixa, SHA conferido em scripts/baixar_fontes_linguagem.py):
   conversas inteiras escritas por voluntários, inclusive as respostas do "assistente". Mensagens
   marcadas como sintéticas, apagadas ou reprovadas na revisão ficam fora.
2. Legendas em português do Brasil (OpenSubtitles v2018, OPUS; uso não comercial, com crédito a
   opensubtitles.org): falas de filmes e séries, em janelas de 2 a 8 falas seguidas. Desligável
   (--sem-legendas).
3. Acervo do CRIVO: a pergunta "me fala sobre X" (lado da pessoa) e, como resposta, o próprio
   texto do acervo que o CRIVO entrega no contexto. Ensina a usar os fatos que recebe.

Contexto (formato_fase6.py):
- `quem`: o resumo do IDENTIDADE.md, em toda conversa de assistente (OASST2 e acervo). Decisão do
  criador: ele lê quem é e se apresenta do jeito dele.
- `lembrancas`: em conversas com 6 turnos ou mais, as primeiras falas da pessoa saem do histórico e
  entram como lembrança ("a pessoa disse: ..."). Ele aprende a usar o que foi dito antes.

Uso (no Colab): python gerar_fase6b.py --oasst oasst2.messages.jsonl.gz [--legendas URL_ou_arquivo] --saida pasta
"""
import argparse
import gzip
import hashlib
import io
import json
import random
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))

SEED = 20261014
LEGENDAS_URL = "https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/mono/pt_br.txt.gz"
PERGUNTAS_ACERVO = ["me fala sobre {a}", "o que é {a}?", "me explica {a}", "você sabe o que é {a}?",
                    "conta um pouco sobre {a}", "o que você sabe de {a}?", "{a}, o que é isso?"]
LIXO_LEGENDA = re.compile(r"(legenda|tradu[çc][ãa]o|sincroniza|www\.|http|\.com|♪|subtitle|revis[ãa]o:)", re.I)


def parte(chave):
    h = int(hashlib.sha256(chave.encode()).hexdigest()[:8], 16) % 100
    return "teste" if h < 3 else "val" if h < 6 else "treino"


def resumo_identidade():
    texto = (RAIZ / "IDENTIDADE.md").read_text(encoding="utf-8")
    m = re.search(r"## Em uma frase\s+(.+?)\n\n", texto, re.S)
    frase = " ".join(m.group(1).split()) if m else "O CRIVO é uma inteligência artificial feita do zero."
    return frase


def oasst(caminho):
    msgs = {}
    with gzip.open(caminho, "rt", encoding="utf-8") as f:
        for linha in f:
            m = json.loads(linha)
            msgs[m["message_id"]] = m
    filhos = defaultdict(list)
    for m in msgs.values():
        if m.get("parent_id"):
            filhos[m["parent_id"]].append(m["message_id"])
    rel = Counter()

    def boa(m):
        if not str(m.get("lang", "")).lower().startswith("pt"):
            return False
        if m.get("deleted") or m.get("synthetic") or m.get("review_result") is False:
            rel["fora_revisao_sintetica_apagada"] += 1
            return False
        return bool((m.get("text") or "").strip())

    def continua(m):
        """A conversa segue depois desta resposta (pessoa responde e alguém responde de novo)?"""
        return any(boa(msgs[f]) and any(boa(msgs[g]) for g in filhos[f]) for f in filhos[m["message_id"]])

    exemplos = []
    for m in msgs.values():
        # Só conversas que terminam aqui: os prefixos já entram com perda dentro das mais longas.
        if m.get("role") != "assistant" or not boa(m) or continua(m):
            continue
        cadeia, atual, ok = [], m, True
        while atual is not None:
            if not boa(atual):
                ok = False
                break
            cadeia.append(atual)
            atual = msgs.get(atual.get("parent_id")) if atual.get("parent_id") else None
        cadeia.reverse()
        if not ok or cadeia[0]["role"] != "prompter":
            continue
        papeis = [c["role"] for c in cadeia]
        if any(a == b for a, b in zip(papeis, papeis[1:])):
            rel["fora_papeis_fora_de_ordem"] += 1
            continue
        turnos = [{"papel": "usuario" if c["role"] == "prompter" else "assistente", "texto": c["text"].strip()}
                  for c in cadeia]
        exemplos.append({"origem": "oasst2", "chave": m["message_tree_id"], "turnos": turnos})
    rel["exemplos"] = len(exemplos)
    rel["arvores"] = len({e["chave"] for e in exemplos})
    return exemplos, dict(rel)


def _linhas_legenda(fonte, max_linhas):
    if str(fonte).startswith("http"):
        bruto = urllib.request.urlopen(fonte, timeout=120)
        arquivo = gzip.GzipFile(fileobj=bruto)
    else:
        arquivo = gzip.open(fonte, "rb")
    with io.TextIOWrapper(arquivo, encoding="utf-8", errors="replace") as f:
        for i, linha in enumerate(f):
            if i >= max_linhas:
                break
            yield linha.strip()


def legendas(fonte, max_linhas, rr):
    exemplos, janela, n_lixo = [], [], 0
    alvo = rr.randint(2, 8)
    for i, linha in enumerate(_linhas_legenda(fonte, max_linhas)):
        linha = re.sub(r"^[-–]\s*", "", linha)
        if not (2 <= len(linha) <= 200) or LIXO_LEGENDA.search(linha):
            n_lixo += 1
            janela, alvo = [], rr.randint(2, 8)   # quebra a sequência
            continue
        janela.append(linha)
        if len(janela) == alvo:
            n = len(janela)
            turnos = [{"papel": "assistente" if (n - 1 - j) % 2 == 0 else "usuario", "texto": t} for j, t in enumerate(janela)]
            if turnos[0]["papel"] == "assistente":
                turnos = turnos[1:]
            if len(turnos) >= 2:
                exemplos.append({"origem": "legendas", "chave": "leg:%d" % (i // 5000), "turnos": turnos})
            janela, alvo = [], rr.randint(2, 8)
    return exemplos, {"exemplos": len(exemplos), "linhas_descartadas": n_lixo}


def acervo(rr):
    from crivo import Crivo
    from curriculo_mundo import texto_fato
    exemplos = []
    for chave, item in sorted(Crivo().compositor.itens.items()):
        fs = [texto_fato(f) for f in item["fatos"] if f.get("natureza") != "religioso"]
        fs = [f for f in fs if 12 <= len(f) <= 260]
        if not fs or not (2 <= len(item["nome"]) <= 40):
            continue
        for _ in range(3):
            usados = fs[:rr.choice((1, 2))]
            pergunta = rr.choice(PERGUNTAS_ACERVO).format(a=item["nome"])
            exemplos.append({"origem": "acervo", "chave": "acervo:" + chave, "ctx": {"fatos": usados},
                             "turnos": [{"papel": "usuario", "texto": pergunta}, {"papel": "assistente", "texto": " ".join(usados)}]})
    return exemplos, {"exemplos": len(exemplos)}


def com_lembrancas(e, rr):
    """Conversa longa: as primeiras falas da pessoa viram lembrança no contexto."""
    turnos = e["turnos"]
    if len(turnos) < 6 or rr.random() < 0.3:
        return e
    k = 2 if len(turnos) >= 8 else 1
    tirar = turnos[:2 * k]
    lembr = ["a pessoa disse: " + t["texto"][:150] for t in tirar if t["papel"] == "usuario"]
    return {**e, "ctx": {**e.get("ctx", {}), "lembrancas": lembr}, "turnos": turnos[2 * k:]}


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oasst", required=True)
    ap.add_argument("--legendas", default=LEGENDAS_URL)
    ap.add_argument("--sem-legendas", action="store_true")
    ap.add_argument("--max-linhas-legenda", type=int, default=2_000_000)
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    rr = random.Random(SEED)
    quem = resumo_identidade()
    rel = {}
    ex_o, rel["oasst2"] = oasst(a.oasst)
    ex_a, rel["acervo"] = acervo(rr)
    ex_l = []
    if not a.sem_legendas:
        try:
            ex_l, rel["legendas"] = legendas(a.legendas, a.max_linhas_legenda, rr)
        except Exception as erro:  # sem rede ou fonte fora do ar: segue sem legendas
            rel["legendas"] = {"erro": "%s: %s" % (type(erro).__name__, erro)}
    dados = {"treino": [], "val": [], "teste": []}
    for e in ex_o + ex_a + ex_l:
        e = com_lembrancas(e, rr)
        if e["origem"] in ("oasst2", "acervo"):
            e = {**e, "ctx": {"quem": quem, **e.get("ctx", {})}}
        dados[parte(e["chave"])].append(e)
    for v in dados.values():
        rr.shuffle(v)
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    bruto = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
    with gzip.GzipFile(saida / "dados_fase6b.json.gz", "wb", mtime=0) as f:
        f.write(bruto)
    manifesto = {"protocolo": "fase6b", "seed": SEED, "dados_sha256": hashlib.sha256(bruto).hexdigest(), "quem": quem,
                 "tamanhos": {k: len(v) for k, v in dados.items()},
                 "por_origem": {k: dict(Counter(e["origem"] for e in v)) for k, v in dados.items()},
                 "com_lembrancas": sum(1 for v in dados.values() for e in v if e.get("ctx", {}).get("lembrancas")),
                 "relatorio": rel, "nenhuma_fala_escrita_pelo_assistente": True}
    (saida / "manifesto_fase6b.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(manifesto, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    principal()
