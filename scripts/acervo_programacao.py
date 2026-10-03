#!/usr/bin/env python3
"""Busca e validação do acervo; não conecta nem altera o runtime do CRIVO."""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/pesquisa_conhecimento/programacao"
CATALOG = BASE / "catalogo-avancado.json"

def normalized(text):
    return re.sub(r"[^a-z0-9]+", " ", "".join(
        c for c in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(c))).strip()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    units = catalog["unidades"]
    assert catalog["schema_versao"] == "1.0"
    assert catalog["integrado_runtime"] is False
    assert catalog["treinamento_realizado"] is False
    ids = {u["id"] for u in units}
    assert len(ids) == len(units), "IDs repetidos"
    assert len(units) >= 200, "Cobertura incompleta"
    fields = ("id", "dominio", "conceito", "definicao", "mecanismo",
              "falhas_comuns", "criterio_de_escolha", "verificacao")
    sources = catalog["fontes"]
    for key, source in sources.items():
        assert source["url"].startswith("https://"), key
        assert source["titulo"] and source["escopo"], key
    for unit in units:
        for field in fields:
            assert isinstance(unit[field], str) and unit[field].strip(), (unit["id"],field)
        assert unit["fontes"], unit["id"]
        assert all(s in sources for s in unit["fontes"]), unit["id"]
        for field in ("relacoes", "pre_requisitos"):
            assert all(i in ids and i != unit["id"] for i in unit.get(field,[])), unit["id"]
        if "exemplo" in unit:
            assert (BASE / unit["exemplo"].split("#")[0]).is_file(), unit["id"]
    # Pré-requisitos não podem conter ciclos.
    graph = {u["id"]:u.get("pre_requisitos",[]) for u in units}
    visiting, done = set(), set()
    def visit(node):
        assert node not in visiting, "Ciclo de pré-requisitos: " + node
        if node in done: return
        visiting.add(node)
        for dep in graph[node]: visit(dep)
        visiting.remove(node); done.add(node)
    for node in graph: visit(node)
    tasks = json.loads((BASE/"desafios-projetos.json").read_text(encoding="utf-8"))["desafios"]
    assert len({t["id"] for t in tasks}) == len(tasks)
    assert len(tasks) == 40
    for task in tasks:
        assert task["holdout"] is False
        assert all(i in ids for i in task["conceitos"]), task["id"]
    # Exportações Markdown são reproduzidas pelo catálogo de origem.
    for domain in {u["dominio"] for u in units}:
        text=(BASE/"fichas"/(domain+".md")).read_text(encoding="utf-8")
        for unit in (u for u in units if u["dominio"]==domain):
            assert "## "+unit["id"]+" — " in text, unit["id"]
            for field in ("definicao","mecanismo","falhas_comuns","criterio_de_escolha","verificacao"):
                assert unit[field] in text, (unit["id"],field)
    manifest=json.loads((BASE/"manifesto.json").read_text(encoding="utf-8"))
    assert manifest["unidades"] == len(units)
    assert manifest["desafios"] == len(tasks)
    assert manifest["fontes"] == len(sources)
    assert manifest["dominios"] == len({u["dominio"] for u in units})
    assert manifest["bytes_acervo"] == sum(item["bytes"] for item in manifest["arquivos"])
    expected = set(manifest["paths"])
    actual = {entry["path"] for entry in manifest["arquivos"]}
    assert expected == actual and len(actual)==len(manifest["arquivos"])
    for item in manifest["arquivos"]:
        path=ROOT/item["path"]
        assert path.is_file(), item["path"]
        assert path.stat().st_size == item["bytes"], item["path"]
        assert digest(path) == item["sha256"], item["path"]
    return {"unidades":len(units),"dominios":len(manifest["contagem_por_dominio"]),
            "fontes":len(sources),"desafios":len(tasks),
            "arquivos_verificados":len(manifest["arquivos"]),"status":"ok"}

def search(query, limit):
    units=json.loads(CATALOG.read_text(encoding="utf-8"))["unidades"]
    tokens=set(normalized(query).split())
    if not tokens: return []
    ranked=[]
    for unit in units:
        title=set(normalized(unit["id"]+" "+unit["conceito"]+" "+unit["dominio"]).split())
        body=set(normalized(" ".join(unit[f] for f in (
            "definicao","mecanismo","falhas_comuns","criterio_de_escolha","verificacao"))).split())
        score=4*len(tokens & title)+len(tokens & body)
        if score:
            ranked.append((score,unit))
    ranked.sort(key=lambda pair:(-pair[0],pair[1]["id"]))
    return [{"score":score,**unit} for score,unit in ranked[:limit]]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validar",action="store_true")
    parser.add_argument("--buscar")
    parser.add_argument("--limite",type=int,default=5)
    args=parser.parse_args()
    if args.limite<1 or args.limite>100:
        parser.error("--limite precisa estar entre 1 e 100")
    if args.validar:
        print(json.dumps(validate(),ensure_ascii=False,indent=2))
    elif args.buscar is not None:
        print(json.dumps(search(args.buscar,args.limite),ensure_ascii=False,indent=2))
    else: parser.print_help()
if __name__=="__main__":
    try: main()
    except (AssertionError, KeyError, ValueError, OSError) as error:
        print("Acervo inválido: "+repr(error),file=sys.stderr)
        raise SystemExit(1)

