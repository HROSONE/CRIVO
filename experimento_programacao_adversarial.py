"""Sonda adversarial de programação: diagnóstica, sem ajuste nem aprovação automática.

Perguntas escritas após a v0.4: NÃO são teste cego de generalização depois
que seus resultados forem usados para modificar o sistema. Não entram no treino.
"""
import json
from collections import Counter
from crivo import Crivo

# Linguagem explícita, paráfrases, troca de domínio, operadores e pedidos fora
# do currículo. A intenção esperada é uma hipótese para auditoria manual.
CASOS = [
    ("Como faço para mostrar olá na tela com Python?", "py_print", "parafrase"),
    ("Preciso coletar uma informação digitada em Python", "py_input", "parafrase"),
    ("Em Python, uma função pode devolver um resultado?", "py_funcao", "parafrase"),
    ("Meu script acusou KeyError ao procurar uma chave", "py_keyerror", "erro"),
    ("O código Python está reclamando de indentação", "py_indentacao", "erro"),
    ("Qual é a utilidade do bloco except em Python?", "py_excecao", "parafrase"),
    ("Como abrir e ler um arquivo de texto no Python?", "py_arquivo", "parafrase"),
    ("Como criar um dicionário com pares de chave e valor em Python?", "py_dicionario", "parafrase"),
    ("Em JavaScript, como declarar uma variável que não muda?", "js_variavel", "linguagem"),
    ("Como selecionar um nó do HTML pelo JavaScript?", "js_dom", "linguagem"),
    ("Como percorrer uma lista com for em JavaScript?", "js_for", "linguagem"),
    ("Como percorrer uma lista com for em Python?", "py_for", "linguagem"),
    ("Preciso somar números numa função JavaScript", "js_funcao", "linguagem"),
    ("Preciso somar números numa função Python", "py_funcao", "linguagem"),
    ("Como colocar um estilo CSS numa página?", "web_css", "parafrase"),
    ("Como estruturar o documento com tags HTML?", "web_html", "parafrase"),
    ("Em SQL, como selecionar registros com condição WHERE?", "sql_select", "parafrase"),
    ("Como associar linhas de tabelas diferentes usando JOIN?", "sql_join", "parafrase"),
    ("Como prevenir injeção SQL com parâmetros?", "sql_parametros", "parafrase"),
    ("Como criar uma ramificação sem modificar a branch principal no Git?", "git_branch", "parafrase"),
    ("Como inspecionar diferenças entre duas alterações no Git?", "git_diff", "parafrase"),
    ("Meu programa dá TypeError em JavaScript", "fora", "linguagem_errada"),
    ("Como usar print em JavaScript?", "fora", "linguagem_errada"),
    ("Escreva um driver de placa de vídeo em C++", "fora", "fora_curriculo"),
    ("Implemente uma linguagem de programação completa", "fora", "fora_curriculo"),
    ("Qual é a função da raiz de uma planta?", "partes_planta", "controle"),
    ("Como funciona o sistema solar?", "sistema_solar", "controle_aberto"),
]

def executar():
    resultados = []
    for pergunta, esperado, grupo in CASOS:
        bot = Crivo()
        obtido, resposta = bot.responder(pergunta)
        # 'duvida' e 'fora' sao abstencoes, nao acertos de intencao.
        passou = (obtido == esperado) if esperado != "fora" else obtido in ("fora", "duvida")
        resultados.append(dict(pergunta=pergunta, esperado=esperado, obtido=obtido,
                               grupo=grupo, passou=passou, resposta=resposta[:180]))
    grupos = {}
    for grupo in sorted(set(c["grupo"] for c in resultados)):
        itens = [c for c in resultados if c["grupo"] == grupo]
        grupos[grupo] = {"acertos": sum(c["passou"] for c in itens), "total": len(itens)}
    return {"acertos": sum(c["passou"] for c in resultados), "total": len(resultados),
            "grupos": grupos, "casos": resultados,
            "limite": "Sonda de desenvolvimento posterior a v0.4, nao teste cego; respostas revisadas manualmente."}

if __name__ == "__main__":
    print(json.dumps(executar(), ensure_ascii=False, indent=2))
