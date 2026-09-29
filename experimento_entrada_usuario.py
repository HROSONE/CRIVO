"""Diagnóstico incremental: compreender entrada do usuário em Python.

Casos fixados ANTES do código do experimento. Após ajustes, tornam-se
desenvolvimento, não conjunto cego. O objetivo é reduzir confusões sem
superinterpretar pedidos desconhecidos.
"""
import json
from collections import defaultdict
from crivo import Crivo
from avaliar_recuperador import avaliar
from coorte_geral import selecionar_coorte
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

# Controles adicionais formulados DEPOIS da primeira alteração.
# Não são teste cego; destacam extrapolações para meios de entrada
# que a base não ensina (web, câmera, rede).
CONTROLES_POS_AJUSTE = [
 ("Como solicitar o nome de alguém no Python?", "py_input", "entrada"),
 ("Quero obter resposta digitada pelo usuário em Python", "py_input", "entrada"),
 ("Como pegar o que foi digitado no terminal Python?", "py_input", "entrada"),
 ("Como perguntar um número para uma pessoa em Python?", "py_input", "entrada"),
 ("Quero usar input no código Python", "py_input", "entrada"),
 ("Qual é seu nome?", "social:quem", "social"),
 ("Qual é o seu nome?", "social:quem", "social"),
 ("Me diga seu nome", "social:quem", "social"),
 ("Em Python, como solicitar que uma pessoa informe seu nome?", "py_input", "social"),
 ("Como solicitar documento de usuário por formulário web em Python?", "fora|duvida", "limite"),
 ("Como capturar dados de pessoa pela câmera usando Python?", "fora|duvida", "limite"),
 ("Como solicitar dados de uma pessoa pelo WhatsApp usando Python?", "fora|duvida", "limite"),
 ("Como obter um endereço IP pelo Python?", "fora|duvida", "limite"),
 ("Como consultar uma API de cadastro por Python?", "fora|duvida", "limite"),
 ("Como não salvar os dados de entrada em Python?", "duvida", "negacao"),
 ("Posso não regar minha planta?", "duvida", "negacao"),
 ("Qual planeta não tem anéis?", "duvida", "negacao"),
 ("Como alterar o texto de um elemento HTML com JavaScript?", "js_dom", "dom"),
 ("Como selecionar uma tag HTML usando JavaScript?", "js_dom", "dom"),
 ("Como funciona a Lua?", "lua", "generico"),
 ("Como funciona uma usina nuclear?", "fora|duvida", "generico"),
 ("Como comparar arquivos alterados no Git?", "git_diff", "git"),
 ("Qual a diferença entre commit e push no Git?", "git_commit", "git"),
]

def diagnosticar(casos=CASOS):
    rows = []
    for pergunta, esperado, grupo in casos:
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
    dados['controles_pos_ajuste'] = diagnosticar(CONTROLES_POS_AJUSTE)
    base = json.loads(Path("conhecimento.json").read_text(encoding="utf-8"))
    antigos = selecionar_coorte(base)
    geral = avaliar(antigos)
    dados["benchmark_geral"] = {k: geral[k] for k in
            ("total", "acertos", "erradas", "abstencoes")}
    print(json.dumps(dados, ensure_ascii=False, indent=2))
    assert (geral["total"], geral["acertos"], geral["erradas"], geral["abstencoes"]) == (278, 192, 44, 42)
