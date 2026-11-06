"""Enciclopédia de consulta do CRIVO: o começo de cada verbete da Wikipédia em português.

Quando o acervo (conhecimento*.json, escrito e conferido) não tem o assunto, o CRIVO procura o
verbete pelo título e diz a primeira frase dele, com a fonte (enciclopedia.py). O modelo recebe essa
frase como fato e só pode dizê-la sem alterar (a conferência confere).

Fonte: wikimedia/wikipedia, 20231101.pt (as 6 partes), revisão fixa, licença CC BY-SA. Este arquivo
derivado tem a mesma licença (ver NOTICE na pasta do artefato).

Fica de fora: desambiguação, listas e anexos, títulos que são só datas, verbete sem uma frase completa
de 40 a 230 caracteres no começo. Ficam os N verbetes mais longos (o tamanho do texto mede, de modo
grosseiro, quanto o assunto importa).

Arquivo (versão 3): enciclopedia_pt.v3.gz, texto UTF-8 em linhas: um cabeçalho JSON; n linhas
"título<TAB>começo do verbete"; e as chaves de busca ("título sem acento<TAB>índice") em ordem de bytes.
O CRIVO lê o arquivo aberto como um bloco só e acha a chave por busca binária (enciclopedia.py): 300 mil
verbetes cabem em uns 80 MB de memória, onde o JSON da versão 2 passava de 500 MB.

Uso: python scripts/construir_enciclopedia.py parte1.parquet ... --saida pasta [--n 300000]
"""
import argparse
import collections
import gzip
import hashlib
import heapq
import json
import re
import unicodedata
from pathlib import Path

VERSAO = 3
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


PARTICULAS = {"de", "da", "do", "dos", "das", "van", "von", "der", "del", "e", "y", "la", "le", "di", "du"}
PESSOA = re.compile(r"\(\s*[^()]*?\b\d{1,2} de [a-zç]+ de \d{3,4}|\bnascid[oa]\b|\b(?:foi|é) (?:um|uma) (?:[\w-]+ ){0,2}(?:"
                    r"matemátic|físic|químic|filósof|psicólog|psicanalist|psiquiatra|neurologista|médic|biólog|sociólog|"
                    r"antropólog|economista|historiador|escritor|poeta|romancista|dramaturgo|pintor|escultor|compositor|"
                    r"músic|cantor|ator|atriz|cineasta|político|política|presidente|rei|rainha|imperador|papa|santo|santa|"
                    r"cientista|inventor|engenheir|astrônom|jogador|futebolista|atleta|tenista|piloto|militar|general|"
                    r"teólog|jurista|advogad|jornalista|empresári|educador|pedagog|linguista|naturalista|explorador)")

OBRA = re.compile(r"\b(?:canção|álbum|single|filme|série|telenovela|episódio|livro|romance|banda|jogo|atropelamento|"
                  r"assassinato|caso|empresa|marca|clube|navio)\b", re.I)


def chaves_sobrenome(titulos, leads, chaves, limite=30_000):
    """"Freud" → "Sigmund Freud": o sobrenome de uma pessoa vira chave quando o verbete dela está entre os
    `limite` mais longos e é bem mais longo que o de qualquer outra pessoa com o mesmo sobrenome (3 vezes
    a posição). "Weber" (Max e Michel, perto um do outro) e "Lula" (o verbete é "Luiz Inácio Lula da Silva")
    ficam sem chave: o CRIVO diz que não sabe em vez de trazer a pessoa errada."""
    comuns = collections.Counter(w for f in leads for w in re.findall(r"\b[a-zà-ú]+\b", f))
    candidatos = collections.defaultdict(list)
    for i, (t, f) in enumerate(zip(titulos, leads)):
        partes = t.split()
        if "(" in t or not 2 <= len(partes) <= 5 or not all(p[:1].isupper() or p in PARTICULAS for p in partes):
            continue
        # "Instituto Lula", "Museu Freud"; canção, filme ou acontecimento com nome de gente
        if comuns[partes[0].lower()] >= 20 or not PESSOA.search(f) or OBRA.search(f[:120]):
            continue
        sobrenome = normalizar(partes[-1])
        if len(sobrenome) >= 4:
            candidatos[sobrenome].append(i)
    novas = {}
    for sobrenome, ids in candidatos.items():
        if sobrenome not in chaves and ids[0] < limite and (len(ids) == 1 or ids[1] >= 3 * ids[0] + 1000):
            novas[sobrenome] = ids[0]
    return novas


def construir(artigos, n=300_000):
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
    chaves.update(chaves_sobrenome(titulos, leads, chaves))
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
    cab = {k: enc[k] for k in ("versao", "fonte", "licenca", "n")}
    cab["chaves"] = len(enc["chaves"])
    linhas = [json.dumps(cab, ensure_ascii=False)]
    for t, f in zip(enc["titulos"], enc["leads"]):
        if any(c in t + f for c in "\t\n"):
            raise ValueError("verbete com tabulação ou quebra de linha: %r" % t)
        linhas.append(t + "\t" + f)
    chaves = sorted(enc["chaves"].items(), key=lambda kv: kv[0].encode("utf-8"))
    linhas += ["%s\t%d" % kv for kv in chaves]
    arquivo = saida / "enciclopedia_pt.v3.gz"
    with gzip.GzipFile(arquivo, "wb", mtime=0, compresslevel=9) as f:
        f.write("\n".join(linhas).encode("utf-8"))
    return hashlib.sha256(arquivo.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("parquets", nargs="+")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--n", type=int, default=300_000)
    a = ap.parse_args()
    enc = construir(ler_parquets(a.parquets), a.n)
    sha = salvar(enc, a.saida)
    print(json.dumps({"verbetes": enc["n"], "chaves": len(enc["chaves"]), "sha256": sha,
                      "exemplos": [[t, f] for t, f in zip(enc["titulos"][:5], enc["leads"][:5])]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
