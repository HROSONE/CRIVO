"""Integra a expansão de psicologia cognitiva e neurociência ao currículo, só com fatos conferidos.

Lê o arquivo intermediário de scripts/preparar_expansao_psicologia.py e a revisão por afirmação
(docs/revisao_fontes_psicologia_20261020.jsonl). Cada linha da revisão diz se o fato está no texto
de uma fonte aberta (OpenStax ou Wikipédia em inglês), com a seção e um trecho literal:

    sustentado      o fato entra como está, com a seção como fonte;
    parcial         entra o texto corrigido da revisão (só o que a fonte diz);
    nao_encontrado  fica fora;
    incorreto       fica fora.

Um conceito só entra com uma afirmação conferida que o abra (o currículo exige começar por uma
definição; quando o lote não marcou nenhuma, a primeira afirmação conferida de detalhe ou causa abre a
ficha) e se o nome não colide com conceito que já existe. Nada é atribuído por conveniência: sem trecho, sem fato.

Uso: python scripts/integrar_expansao_psicologia.py [--intermediario arquivo.json]
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
REVISAO = RAIZ / "docs" / "revisao_fontes_psicologia_20261020.jsonl"
DESTINO = RAIZ / "conhecimento_psicologia_neurociencia.json"
VERIFICADO_EM = "2026-10-20"
LIVROS = {
    "openstax_psicologia_2e": ("Psychology 2e", "psychology-2e",
                               "OpenStax, Rice University; Rose M. Spielman, William J. Jenkins, Marilyn D. Lovett e outros"),
    "openstax_anat_fisio_2e": ("Anatomy and Physiology 2e", "anatomy-and-physiology-2e",
                               "OpenStax, Rice University; J. Gordon Betts, Kelly A. Young, James A. Wise e outros"),
}
# A Wikipédia em inglês entra como referência (CC BY-SA): o fato é síntese própria em português, sem
# reprodução do texto; o trecho literal fica só na revisão.
WIKIPEDIA = "wikipedia_en"
ESCOPO = ("Síntese própria em português, conferida afirmação por afirmação contra o texto desta seção "
          "(trecho e localizador em docs/revisao_fontes_psicologia_20261020.jsonl); sem reprodução de "
          "trechos, figuras ou exercícios.")


# Começos de nome que não dizem o assunto sozinhos ("Métodos e limites da neurociência").
GENERICOS = {"metodos", "reconstrucao", "consolidacao", "confianca", "receptores", "interacao entre sistema nervoso",
             "desenhos experimentais", "prática", "pratica", "variabilidade individual", "qualidade metodologica",
             "diferencas individuais", "perspectiva", "estatistica", "heuristicas", "transferencia de aprendizagem",
             "interacao entre emocao"}


def palavras_comuns(limite=20000):
    """As `limite` palavras mais frequentes das legendas (dados/lexico_pt): palavra comum sozinha não vira apelido."""
    caminho = RAIZ / "dados" / "lexico_pt" / "frequencia_legendas_pt_br_50k.txt"
    with caminho.open(encoding="utf-8") as f:
        return {_norm(linha.split()[0]) for _, linha in zip(range(limite), f) if linha.strip()}


def _norm(t):
    t = unicodedata.normalize("NFD", t.casefold())
    return " ".join("".join(c for c in t if unicodedata.category(c) != "Mn").split())


def _chave(fonte, localizador):
    return (fonte + "_" + re.sub(r"[^a-z0-9]+", "_", _norm(localizador)).strip("_"))[:80]


def _fonte(fonte, localizador):
    if fonte == WIKIPEDIA:
        artigo = localizador.replace(" ", "_")
        return {"titulo": "Wikipédia (inglês) — %s" % localizador.replace("_", " "),
                "url": "https://en.wikipedia.org/wiki/%s" % artigo, "tipo": "enciclopedia_aberta", "ano": 2026,
                "ano_tipo": "consulta", "credito": "Colaboradores da Wikipédia em inglês",
                "reutilizacao": "somente_referencia", "reproducao_autorizada": False,
                "direitos_url": "https://creativecommons.org/licenses/by-sa/4.0/", "verificado_em": VERIFICADO_EM,
                "escopo_uso": ESCOPO.replace("desta seção", "deste artigo")}
    titulo, livro, credito = LIVROS[fonte]
    secao = re.sub(r"^(\d+)-(\d+)-", r"\1.\2 ", localizador).replace("-", " ")
    return {"titulo": "%s — %s" % (titulo, secao), "url": "https://openstax.org/books/%s/pages/%s" % (livro, localizador),
            "tipo": "institucional_cientifica", "ano": 2026, "ano_tipo": "consulta", "credito": credito,
            "reutilizacao": "CC-BY-4.0", "direitos_url": "https://creativecommons.org/licenses/by/4.0/",
            "verificado_em": VERIFICADO_EM, "escopo_uso": ESCOPO}


def nomes_existentes():
    from curriculo_mundo import ler_curriculo
    dados = ler_curriculo(RAIZ / "conhecimento_mundo.json")
    # O próprio catálogo (de uma execução anterior) não conta como conceito que já existe.
    proprios = set()
    if DESTINO.is_file():
        proprios = {i["id"] for i in json.loads(DESTINO.read_text(encoding="utf-8"))["itens"]}
    itens = list(dados["itens"])
    # Todos os catálogos conhecimento_*.json, como scripts/verificar_acervo.py confere as colisões.
    for arquivo in sorted(RAIZ.glob("conhecimento_*.json")):
        d = json.loads(arquivo.read_text(encoding="utf-8"))
        if isinstance(d, dict) and arquivo != DESTINO:
            itens += [i for i in d.get("itens", []) if isinstance(i, dict) and isinstance(i.get("nome"), str)]
    return {_norm(n) for i in itens if i.get("id") not in proprios for n in [i["nome"]] + list(i.get("aliases", []))}


def integrar(intermediario, revisao=REVISAO):
    prep = json.loads(Path(intermediario).read_text(encoding="utf-8"))
    linhas = [json.loads(l) for l in Path(revisao).read_text(encoding="utf-8").splitlines() if l.strip()]
    rev = {(l["id"], l["n"]): l for l in linhas}
    existentes = nomes_existentes()
    fontes, itens, relatorio = {}, [], {"conceitos": 0, "fatos": 0, "fora": {}}
    for item in prep["itens"]:
        if _norm(item["nome"]) in existentes:
            relatorio["fora"].setdefault("conceito_ja_existe", []).append(item["id"])
            continue
        fatos = []
        for n, fato in enumerate(item["fatos"], start=1):
            r = rev.get((item["id"], n))
            if r is None or r["veredito"] not in ("sustentado", "parcial") or r.get("fonte") not in set(LIVROS) | {WIKIPEDIA}:
                motivo = "sem_revisao" if r is None else (r["veredito"] if r["veredito"] not in ("sustentado", "parcial")
                                                         else "fonte_fora_dos_livros_abertos")
                relatorio["fora"].setdefault(motivo, []).append("%s#%d" % (item["id"], n))
                continue
            texto = (r.get("texto_corrigido") or "").strip() if r["veredito"] == "parcial" else fato["texto"]
            if not texto or len(texto) > 400 or not r.get("trecho"):
                relatorio["fora"].setdefault("sem_trecho_ou_longo", []).append("%s#%d" % (item["id"], n))
                continue
            chave = _chave(r["fonte"], r["localizador"])
            fontes.setdefault(chave, _fonte(r["fonte"], r["localizador"]))
            fatos.append({"texto": texto, "fonte": chave, "papel": fato["papel"], "natureza": fato["natureza"]})
        definicoes = [f for f in fatos if f["papel"] == "definicao"]
        if not definicoes:
            # O lote nunca marcou uma definição: a primeira afirmação conferida que descreve o conceito
            # (detalhe ou causa, nunca ressalva ou exemplo) abre a ficha. Fica registrado no relatório.
            descreve = [f for f in fatos if f["papel"] in ("detalhe", "causa")]
            if not descreve:
                relatorio["fora"].setdefault("sem_definicao_conferida", []).append(item["id"])
                continue
            descreve[0]["papel"] = "definicao"
            definicoes = [descreve[0]]
            relatorio.setdefault("definicao_promovida", []).append(item["id"])
        fatos = [definicoes[0]] + [f for f in fatos if f is not definicoes[0]]
        fatos = [fatos[0]] + [dict(f, papel="detalhe") if f["papel"] == "definicao" else f for f in fatos[1:]][:11]
        itens.append({"id": item["id"], "nome": item["nome"], "area": item["area"], "aprofundamento": True,
                      "aliases": [a for a in item.get("aliases", []) if _norm(a) not in existentes], "fatos": fatos})
        existentes.add(_norm(item["nome"]))
        relatorio["conceitos"] += 1
        relatorio["fatos"] += len(fatos)
    # Nome composto ("Metacognição e calibração"): o termo de antes do "e", da vírgula ou dos dois-pontos
    # vira apelido, para "o que é metacognição?" achar a ficha; só se não for nome de outro conceito.
    # Uma palavra só, se for comum ("Linguagem", "Consciência"), pegaria perguntas de outros assuntos
    # ("Para que serve a linguagem SQL?" ia para "Linguagem, bilinguismo e contexto").
    comuns = palavras_comuns()
    for item in itens:
        cabeca = re.split(r"\s+e\s+|,|:|\s+—\s+", item["nome"])[0].strip()
        chave = _norm(cabeca)
        if (cabeca != item["nome"] and len(cabeca) >= 4 and chave not in existentes
                and chave.rstrip("s") not in existentes and chave not in GENERICOS
                and not (" " not in chave and chave in comuns)):
            item["aliases"].append(cabeca)
            existentes.add(chave)
    saida = {"versao": 1, "revisado_em": VERIFICADO_EM,
             "criterio": ("Psicologia cognitiva e neurociência (PR #175). Cada fato foi conferido contra o texto da seção "
                          "do OpenStax ou do artigo da Wikipédia em inglês indicado na fonte; fatos sem trecho que os sustente ficaram fora. "
                          "A conferência foi feita com ajuda de um modelo de terceiros como ferramenta de "
                          "desenvolvimento (Claude), com o trecho literal registrado para revisão humana."),
             "fontes": dict(sorted(fontes.items())), "itens": itens}
    return saida, relatorio


def principal():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--intermediario")
    args = ap.parse_args()
    intermediario = args.intermediario
    if intermediario is None:
        intermediario = Path(tempfile.mkdtemp()) / "preparado.json"
        subprocess.run([sys.executable, str(RAIZ / "scripts" / "preparar_expansao_psicologia.py"),
                        "--saida", str(intermediario)], check=True, stdout=subprocess.DEVNULL)
    saida, relatorio = integrar(intermediario)
    DESTINO.write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("conceitos:", relatorio["conceitos"], "| fatos:", relatorio["fatos"], "| fontes:", len(saida["fontes"]),
          "| definição tirada da primeira afirmação conferida:", len(relatorio.get("definicao_promovida", [])))
    for motivo, quais in sorted(relatorio["fora"].items()):
        print("fora (%s): %d" % (motivo, len(quais)))


if __name__ == "__main__":
    principal()
