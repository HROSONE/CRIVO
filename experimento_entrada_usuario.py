"""Diagnóstico incremental: compreender entrada do usuário em Python.

Casos fixados ANTES do código do experimento. Após ajustes, tornam-se
desenvolvimento, não conjunto cego. O objetivo é reduzir confusões sem
superinterpretar pedidos desconhecidos.
"""
import json
from collections import defaultdict
from crivo import Crivo
from avaliar_recuperador import avaliar
from pathlib import Path

CASOS = [
 ("Como obter informações de quem usa o programa Python?", "py_input", "entrada_indireta"),
 ("Como perguntar o nome da pessoa que abriu o programa Python?", "py_input", "entrada_indireta"),
 ("Como pedir a idade para alguém digitar no terminal Python?", "py_input", "entrada_indireta"),
 ("Quero pegar uma resposta da pessoa enquanto roda o script Python", "py_input", "entrada_indireta"),
 ("Em Python, como solicitar que uma pessoa informe seu nome?", "py_input", "entrada_indireta"),
 ("Quero receber texto que o usuário digita em Python", "py_input", "entrada_indireta"),
 ("Em Python, como fazer uma pergunta e aguardar digitação?", "py_input", "entrada_indireta"),
 ("Como capturar o que a pessoa escreveu no console Python?", "py_input", "entrada_indireta"),
 ("Como recolher dados de quem usa um script Python?", "py_input", "entrada_indireta"),
 ("Como capturar o texto que alguém escreve no teclado usando Python?", "py_input", "entrada_indireta"),
 ("Qual é a função de input em Python?", "py_input", "entrada_explicita"),
 ("Em Python, como receber dados do teclado?", "py_input", "entrada_explicita"),
 ("Como ler um arquivo de texto em Python?", "py_arquivo", "contraste"),
 ("Em Python, como ler dados de um arquivo JSON?", "py_json", "contraste"),
 ("Como extrair valor de um dicionário em Python?", "py_dicionario", "contraste"),
 ("Como declarar uma variável em Python?", "prog_variavel", "contraste"),
 ("Quero escrever um teste unitário em Python", "py_teste", "contraste"),
 ("Qual é a diferença entre uma variável e uma função?", "prog_variavel|py_funcao|duvida", "contraste"),
 ("Como obter dados pessoais de uma pessoa pelo telefone usando Python?", "fora|duvida", "limite"),
 ("Como obter informação em tempo real da posição GPS com Python?", "fora|duvida", "limite"),
 ("Faça um aplicativo bancário completo em Python", "fora|duvida", "limite"),
 ("Como receber mensagem do WhatsApp em Python?", "fora|duvida", "limite"),
 ("Como ler valor de um campo HTML com JavaScript?", "js_dom", "outras_linguagens"),
 ("Como utilizar SQL WHERE para filtrar linhas?", "sql_select", "outras_linguagens"),
 ("Como revisar arquivos modificados no Git?", "git_diff", "outras_linguagens"),
 ("Como salvar mudanças em um commit Git?", "git_commit", "outras_linguagens"),
 ("Como funciona a fotossíntese?", "fotossintese", "controle_geral"),
 ("Qual é a função da raiz de uma planta?", "partes_planta", "controle_geral"),
 ("O que é um eclipse lunar?", "eclipse", "controle_geral"),
]

def diagnosticar():
    rows = []
    for pergunta, esperado, grupo in CASOS:
        bot = Crivo()
        got, reply = bot.responder(pergunta)
        ranking = [{"id": bot.base[i]["id"], "score": round(score, 4)}
                   for score, i in bot._ranking(pergunta)[:3]]
        aceitos = esperado.split("|")
        rows.append({"pergunta": pergunta, "esperado": aceitos, "obtido": got,
                     "passou": got in aceitos, "grupo": grupo,
                     "ranking": ranking, "resposta": reply[:110]})
    groups = defaultdict(lambda: {"acertos": 0, "total": 0})
    for row in rows:
        groups[row["grupo"]]["total"] += 1
        groups[row["grupo"]]["acertos"] += int(row["passou"])
    return {"total": len(rows), "acertos": sum(x["passou"] for x in rows),
            "grupos": dict(groups), "casos": rows,
            "limite": "Casos criados antes deste experimento; usados em desenvolvimento, nao validação cega."}

if __name__ == "__main__":
    dados = diagnosticar()
    base = json.loads(Path("conhecimento.json").read_text(encoding="utf-8"))
    antigos = [e for e in base if e["topico"] != "programacao"]
    geral = avaliar(antigos)
    dados["benchmark_geral"] = {k: geral[k] for k in
            ("total", "acertos", "erradas", "abstencoes")}
    print(json.dumps(dados, ensure_ascii=False, indent=2))
    assert (geral["total"], geral["acertos"], geral["erradas"], geral["abstencoes"]) == (278, 192, 44, 42)
