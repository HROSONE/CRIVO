"""Enciclopédia de consulta do CRIVO: o começo de cada verbete da Wikipédia em português.

Quando o acervo (conhecimento*.json, escrito e conferido) não tem o assunto, o CRIVO procura o
verbete pelo título e diz a primeira frase dele, com a fonte (enciclopedia.py). O modelo recebe essa
frase como fato e só pode dizê-la sem alterar (a conferência confere).

Fonte: wikimedia/wikipedia, 20231101.pt (as 6 partes), revisão fixa, licença CC BY-SA. Este arquivo
derivado tem a mesma licença (ver NOTICE na pasta do artefato).

Fica de fora: desambiguação, listas e anexos, títulos que são só datas, verbete sem uma frase completa
de 40 a 230 caracteres no começo. Ficam os N verbetes mais longos (o tamanho do texto mede, de modo
grosseiro, quanto o assunto importa).

Uso (no Colab): python scripts/construir_enciclopedia.py parte1.parquet ... --saida pasta [--n 120000]
"""
import argparse
import gzip
import hashlib
import heapq
import json
import re
import unicodedata
from pathlib import Path

VERSAO = 2
MIN_LEAD, MAX_LEAD = 40, 300
CURTA = 230   # cabe no contexto do modelo; mais longa, o CRIVO mostra o texto sem o modelo reescrever
FORA_TITULO = re.compile(r"^(?:lista|anexo|predefinição|categoria|portal|wikipédia|ajuda|ficheiro|arquivo)\b|desambiguação"
                         r"|^\d{1,4}(?: a\.c\.)?$|^\d{1,2} de \w+$|^(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto"
                         r"|setembro|outubro|novembro|dezembro) de \d{4}$", re.I)
DESAMBIGUACAO = re.compile(r"pode (?:se )?referir|pode ser:|pode significar|refere-se a:|desambigua", re.I)
# Parênteses de pronúncia, etimologia e grafias: atrapalham a frase e não são o fato.
PARENTESE_RUIDO = re.compile(r"\s*\((?:[^()]*?(?:pronúncia|IPA|AFI|em [a-zà-ú]+:|lit\.|grego|latim|ouça|escute|"
                             r"\[|/)[^()]*)\)", re.I)
# Verbete de obra ou mídia ("DNA (canção)") não responde pelo título sozinho ("o que é DNA?").
MIDIA = re.compile(r"\((?:[^)]*\b(?:canção|álbum|single|filme|série|telenovela|banda|grupo|jogo|livro|romance|"
                   r"personagem|episódio|programa|revista|jornal|peça|ópera|EP|DVD|turnê|clube|navio|cantor|cantora|"
                   r"rapper|ator|atriz|desambiguação)\b[^)]*)\)$", re.I)
ABREVIACOES = re.compile(r"\b(?:a\.C|d\.C|Sr|Sra|Dr|Dra|St|Sto|Sta|séc|aprox|ca|n\.º|nº|pág|vol|etc|Jr|Mr|Mrs|E\.U\.A|EUA|"
                         r"[A-Z])\.$")


def normalizar(t):
    t = unicodedata.normalize("NFD", t.casefold())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^\w\s-]", " ", t)
    return " ".join(t.split())


def frases(paragrafo):
    """Divide em frases sem quebrar em abreviações ("a.C.", "Dr.", iniciais)."""
    partes, atual = [], ""
    for pedaco in re.split(r"(?<=[.!?])\s+", paragrafo):
        atual = (atual + " " + pedaco).strip() if atual else pedaco
        if ABREVIACOES.search(atual):
            continue
        partes.append(atual)
        atual = ""
    if atual:
        partes.append(atual)
    return partes


def lead(titulo, texto):
    """A primeira frase (ou as duas primeiras, se couberem) do verbete, ou None."""
    if not titulo or not texto or FORA_TITULO.search(titulo.strip()):
        return None
    paragrafo = next((p.strip() for p in texto.split("\n") if len(p.strip()) >= MIN_LEAD), "")
    if not paragrafo or DESAMBIGUACAO.search(paragrafo[:300]):
        return None
    paragrafo = " ".join(PARENTESE_RUIDO.sub("", paragrafo).split())
    paragrafo = re.sub(r"\(\s*\)|\s+([,.;])", r"\1", paragrafo)
    fs = frases(paragrafo)
    if not fs or not fs[0].endswith((".", "!", "?")):
        return None
    saida = fs[0]
    if len(saida) > MAX_LEAD:   # verbete grande: sem os parênteses (datas, locais, grafias) costuma caber
        saida = " ".join(re.sub(r"\s*\([^()]*\)", "", saida).split())
        saida = re.sub(r"\s+([,.;])", r"\1", saida)
    if len(fs) > 1 and len(saida) + 1 + len(fs[1]) <= CURTA and fs[1].endswith("."):
        saida = saida + " " + fs[1]
    if not (MIN_LEAD <= len(saida) <= MAX_LEAD):
        return None
    # A frase tem que falar do título (o começo de verbete típico: "X é ...").
    base = normalizar(re.sub(r"\s*\(.*\)$", "", titulo))
    if not base or base.split()[0] not in normalizar(saida):
        return None
    return saida


def construir(artigos, n=120_000):
    """artigos: iterável de (titulo, texto). Devolve o dicionário da enciclopédia."""
    melhores, k = [], 0
    for titulo, texto in artigos:
        frase = lead(titulo, texto)
        if frase is None:
            continue
        item = (len(texto), k, titulo.strip(), frase)
        k += 1
        if len(melhores) < n:
            heapq.heappush(melhores, item)
        elif item[0] > melhores[0][0]:
            heapq.heapreplace(melhores, item)
    melhores.sort(key=lambda x: (-x[0], x[1]))
    titulos = [t for _, _, t, _ in melhores]
    leads = [f for _, _, _, f in melhores]
    chaves = {}
    for i, t in enumerate(titulos):   # do mais longo para o mais curto: o título exato vence; depois, o sem parênteses
        chaves.setdefault(normalizar(t), i)
    for i, t in enumerate(titulos):
        base = re.sub(r"\s*\(.*\)$", "", t)
        if base != t and not MIDIA.search(t):
            chaves.setdefault(normalizar(base), i)
    return {"versao": VERSAO, "fonte": "Wikipédia em português (wikimedia/wikipedia 20231101.pt)",
            "licenca": "CC BY-SA 3.0/4.0", "n": len(titulos), "titulos": titulos, "leads": leads, "chaves": chaves}


def ler_parquets(caminhos):
    import pyarrow.parquet as pq
    for c in caminhos:
        for lote in pq.ParquetFile(c).iter_batches(batch_size=5000, columns=["title", "text"]):
            yield from zip(lote.column(0).to_pylist(), lote.column(1).to_pylist())


def salvar(enc, saida):
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    bruto = json.dumps(enc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with gzip.GzipFile(saida / "enciclopedia_pt.json.gz", "wb", mtime=0, compresslevel=9) as f:
        f.write(bruto)
    return hashlib.sha256((saida / "enciclopedia_pt.json.gz").read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("parquets", nargs="+")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--n", type=int, default=120_000)
    a = ap.parse_args()
    enc = construir(ler_parquets(a.parquets), a.n)
    sha = salvar(enc, a.saida)
    print(json.dumps({"verbetes": enc["n"], "chaves": len(enc["chaves"]), "sha256": sha,
                      "exemplos": [[t, f] for t, f in zip(enc["titulos"][:5], enc["leads"][:5])]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
