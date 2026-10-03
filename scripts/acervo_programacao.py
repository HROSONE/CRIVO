#!/usr/bin/env python3
"""Curadoria, busca e exportação do acervo. Não altera runtime/treino do CRIVO."""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/pesquisa_conhecimento/programacao"
CATALOG=BASE/"catalogo-avancado.json"
FIELDS=("id","dominio","conceito","definicao","mecanismo","falhas_comuns","criterio_de_escolha","verificacao")
LEGACY={"01-algoritmos-estruturas-dados.md","02-sistemas-memoria-concorrencia.md"}
STOP={"o","a","os","as","um","uma","de","do","da","dos","das","e","em","no","na","como","que","qual","quais","para","por","me","explique","the","and","of","in"}
ALIASES={"js":"javascript","ts":"typescript","nodejs":"node"}

class InvalidCorpus(ValueError): pass
def require(condition,message):
    if not condition: raise InvalidCorpus(message)
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def normalized(text):
    return "".join(c for c in unicodedata.normalize("NFKD",text.casefold()) if not unicodedata.combining(c))
def tokens(text):
    raw=re.findall(r"[a-z0-9]+(?:\+\+|#)?|===|!==|==|!=|=>|\?\?|\?\.",normalized(text))
    return {ALIASES.get(t,t) for t in raw if t not in STOP}
def safe_path(relative,root=None):
    root=ROOT if root is None else root
    require(isinstance(relative,str) and bool(relative),"Path inválido")
    path=Path(relative)
    require(not path.is_absolute() and ".." not in path.parts,"Path fora do escopo: "+relative)
    resolved=(root/path).resolve()
    require(resolved.is_relative_to(root.resolve()),"Symlink fora do escopo: "+relative)
    return resolved

def check_catalog(catalog):
    require(catalog.get("schema_versao")=="1.0","Schema incompatível")
    require(catalog.get("integrado_runtime") is False,"Acervo não é integração")
    require(catalog.get("treinamento_realizado") is False,"Acervo não é treino")
    units=catalog.get("unidades");sources=catalog.get("fontes")
    require(isinstance(units,list) and bool(units),"Unidades ausentes")
    require(isinstance(sources,dict) and bool(sources),"Fontes ausentes")
    ids=set()
    for unit in units:
        require(isinstance(unit,dict),"Unidade inválida")
        for field in FIELDS:
            require(isinstance(unit.get(field),str) and bool(unit[field].strip()),"Campo inválido: "+field)
        for field in ("id","dominio"):
            # IDs legados têm acentos; preservar identidade, bloquear separadores.
            require(re.fullmatch(r"[\w-]+",unit[field]) is not None,"Identificador inválido: "+field)
        require(unit["id"] not in ids,"ID duplicado: "+unit["id"]);ids.add(unit["id"])
    for key,source in sources.items():
        require(isinstance(source,dict),"Fonte inválida: "+key)
        url=urlsplit(source.get("url",""))
        require(url.scheme=="https" and bool(url.netloc),"URL inválida: "+key)
        require(bool(source.get("titulo")) and bool(source.get("escopo")),"Fonte incompleta: "+key)
    for unit in units:
        refs=unit.get("fontes")
        require(isinstance(refs,list) and bool(refs) and all(s in sources for s in refs),"Fonte inexistente: "+unit["id"])
        for field in ("relacoes","pre_requisitos"):
            links=unit.get(field,[])
            require(isinstance(links,list) and len(links)==len(set(links)) and all(i in ids and i!=unit["id"] for i in links),"Relação inválida: "+unit["id"])
        if "exemplo" in unit:
            require(safe_path(unit["exemplo"].split("#")[0],BASE).is_file(),"Exemplo inexistente: "+unit["id"])
    graph={u["id"]:u.get("pre_requisitos",[]) for u in units};visiting=set();done=set()
    def visit(node):
        require(node not in visiting,"Ciclo de pré-requisitos: "+node)
        if node in done:return
        visiting.add(node)
        for dep in graph[node]:visit(dep)
        visiting.remove(node);done.add(node)
    for node in graph:visit(node)
    return units,sources

def markdown(domain,units,sources):
    text="# Fichas avançadas: "+domain+"\n\nExportação determinística de `catalogo-avancado.json`. Síntese autoral; referências remotas precisam de conferência editorial. Acervo não integrado ao runtime.\n\n"
    for unit in units:
        text+="## "+unit["id"]+" — "+unit["conceito"]+"\n\n"
        for label,key in [("Definição","definicao"),("Mecanismo","mecanismo"),("Falhas comuns","falhas_comuns"),("Escolha","criterio_de_escolha"),("Verificação proposta","verificacao")]:
            text+="**"+label+":** "+unit[key]+"\n\n"
        for label,key in [("Invariantes","invariantes"),("Complexidade","complexidade"),("Modelo formal","modelo_formal"),("Pré-requisitos","pre_requisitos"),("Relações","relacoes"),("Exemplo local","exemplo"),("Conferência pontual (ver conferencia-fontes-2.json)","conferencia_parcial")]:
            if key in unit:
                value=unit[key]
                if isinstance(value,list):value="; ".join(value)
                text+="**"+label+":** "+value+"\n\n"
        refs=["["+sources[s]["titulo"]+"]("+sources[s]["url"]+")" for s in unit["fontes"]]
        text+="**Referências recomendadas:** "+"; ".join(refs)+"\n\n"
    return text

def managed_files():
    paths=[p for p in BASE.rglob("*") if p.is_file() and p.suffix in {".md",".json",".mjs",".ts"} and p.name not in LEGACY|{"manifesto.json"}]
    paths.extend(p for p in (ROOT/"scripts/acervo_programacao.py",ROOT/"scripts/test_acervo_programacao.py") if p.is_file())
    return sorted(paths)
def make_manifest(catalog,tasks):
    entries=[]
    for path in managed_files():
        relative=str(path.relative_to(ROOT))
        require(safe_path(relative).is_file(),"Arquivo inseguro: "+relative)
        data=path.read_bytes();entries.append({"path":relative,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    counts=dict(sorted(Counter(u["dominio"] for u in catalog["unidades"]).items()))
    return {"schema_versao":"1.0","acervo":catalog["id"],"revisao":catalog.get("revisao","1"),"unidades":len(catalog["unidades"]),"dominios":len(counts),"fontes":len(catalog["fontes"]),"desafios":len(tasks),"contagem_por_dominio":counts,"bytes_acervo":sum(e["bytes"] for e in entries),"nota":"Manifesto exclui a si e os dois capítulos legados; Markdown duplica JSON. Não mede competência.","paths":[e["path"] for e in entries],"arquivos":entries}
def check_tasks(tasks,ids):
    require(isinstance(tasks,list) and bool(tasks),"Desafios ausentes");seen=set()
    for task in tasks:
        require(isinstance(task,dict) and isinstance(task.get("id"),str),"Desafio inválido")
        require(task["id"] not in seen,"Desafio duplicado");seen.add(task["id"])
        require(task.get("holdout") is False,"Desafio público não é holdout")
        require(isinstance(task.get("conceitos"),list) and bool(task["conceitos"]) and all(i in ids for i in task["conceitos"]),"Referência inválida em desafio")
        for key in ("titulo","requisito","cenarios_adversariais"):
            require(isinstance(task.get(key),str) and bool(task[key].strip()),"Desafio incompleto: "+key)
def read_checked():
    catalog=load(CATALOG);units,sources=check_catalog(catalog)
    tasks=load(BASE/"desafios-projetos.json")["desafios"]
    check_tasks(tasks,{u["id"] for u in units})
    report=BASE/"conferencia-fontes-2.json"
    checks=load(report)["consultas"] if report.is_file() else []
    check_ids={c["id"] for c in checks}
    require(len(check_ids)==len(checks),"Conferência duplicada")
    for unit in units:
        require(all(i in check_ids for i in unit.get("conferencia_parcial",[])),
                "Conferência inexistente: "+unit["id"])
    return catalog,units,sources,tasks
def rebuild():
    catalog,units,sources,tasks=read_checked();(BASE/"fichas").mkdir(exist_ok=True)
    for domain in sorted({u["dominio"] for u in units}):
        (BASE/"fichas"/(domain+".md")).write_text(markdown(domain,[u for u in units if u["dominio"]==domain],sources),encoding="utf-8")
    (BASE/"manifesto.json").write_text(json.dumps(make_manifest(catalog,tasks),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return validate()
def validate():
    catalog,units,sources,tasks=read_checked()
    for domain in sorted({u["dominio"] for u in units}):
        expected=markdown(domain,[u for u in units if u["dominio"]==domain],sources)
        require((BASE/"fichas"/(domain+".md")).read_text(encoding="utf-8")==expected,"Markdown divergente: "+domain)
    actual=load(BASE/"manifesto.json")
    for entry in actual.get("arquivos",[]):
        require(safe_path(entry["path"]).is_file(),"Arquivo ausente: "+entry["path"])
    require(actual==make_manifest(catalog,tasks),"Manifesto divergente: revisar e reconstruir")
    return {"unidades":len(units),"dominios":len(actual["contagem_por_dominio"]),"fontes":len(sources),"desafios":len(tasks),"arquivos_verificados":len(actual["arquivos"]),"status":"ok"}
def search(query,limit,domain=None):
    wanted=tokens(query)
    if not wanted:return []
    ranked=[]
    for unit in load(CATALOG)["unidades"]:
        if domain and unit["dominio"]!=domain:continue
        title=tokens(" ".join(unit[k] for k in ("id","conceito","dominio")))
        body=tokens(" ".join(unit[k] for k in FIELDS));score=4*len(wanted&title)+len(wanted&body)
        if score:ranked.append((score,unit))
    ranked.sort(key=lambda pair:(-pair[0],pair[1]["id"]))
    return [{"score":score,**unit} for score,unit in ranked[:limit]]
def related(unit_id,depth):
    units={u["id"]:u for u in load(CATALOG)["unidades"]};require(unit_id in units,"ID inexistente: "+unit_id)
    seen=set();frontier=[unit_id];result=[]
    for level in range(depth+1):
        next_level=[]
        for key in frontier:
            if key in seen:continue
            seen.add(key);unit=units[key];result.append({"distancia":level,**unit})
            next_level.extend(unit.get("pre_requisitos",[])+unit.get("relacoes",[]))
        frontier=next_level
    return result
def main():
    parser=argparse.ArgumentParser(description=__doc__);actions=parser.add_mutually_exclusive_group()
    actions.add_argument("--validar",action="store_true");actions.add_argument("--reconstruir",action="store_true")
    actions.add_argument("--buscar");actions.add_argument("--relacoes")
    actions.add_argument("--jsonl",action="store_true",help="Unidades com referências para stdout")
    parser.add_argument("--dominio");parser.add_argument("--profundidade",type=int,default=1);parser.add_argument("--limite",type=int,default=5)
    args=parser.parse_args()
    if not 1<=args.limite<=100:parser.error("--limite precisa estar entre 1 e 100")
    if not 0<=args.profundidade<=5:parser.error("--profundidade precisa estar entre 0 e 5")
    if args.validar:result=validate()
    elif args.reconstruir:result=rebuild()
    elif args.buscar is not None:result=search(args.buscar,args.limite,args.dominio)
    elif args.relacoes is not None:result=related(args.relacoes,args.profundidade)
    elif args.jsonl:
        _,units,sources,_=read_checked()
        for unit in units:
            if args.dominio and args.dominio!=unit["dominio"]:continue
            print(json.dumps({**unit,"referencias":[sources[s] for s in unit["fontes"]]},ensure_ascii=False,sort_keys=True))
        return
    else:parser.print_help();return
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":
    try:main()
    except (InvalidCorpus,KeyError,ValueError,OSError,TypeError) as error:
        print("Acervo inválido: "+str(error),file=sys.stderr);raise SystemExit(1)
