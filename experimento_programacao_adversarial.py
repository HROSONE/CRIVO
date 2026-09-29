"""Sonda adversarial de programação: diagnóstica, sem ajuste nem aprovação automática.

Perguntas escritas após a v0.4: NÃO são teste cego de generalização depois
que seus resultados forem usados para modificar o sistema. Não entram no treino.
"""
import json
from pathlib import Path
from avaliar_recuperador import avaliar
from crivo import Crivo, PASTA

# Linguagem explícita, paráfrases, troca de domínio, operadores e pedidos fora
# do currículo. A intenção esperada é uma hipótese para auditoria manual.
# A pergunta ampla sobre sistema solar não corresponde a um ID na base;
# o comportamento seguro é oferecer esclarecimento entre assuntos cadastrados.
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
    ("Como funciona o sistema solar?", "duvida", "controle_aberto"),
]

# Segunda sonda escrita depois das correções: serve como diagnóstico extra,
# não como validação estatística independente nem conjunto de treino.
CONTROLES_POS_AJUSTE = [
    ("Como faço para receber caracteres digitados no terminal com Python?", "py_input", "entrada"),
    ("Como obter informações de quem usa o programa Python?", "py_input", "entrada"),
    ("Como usar JavaScript para alterar o texto de uma tag HTML?", "js_dom", "dom"),
    ("Qual é a diferença entre JavaScript e CSS?", "js_intro", "linguagens"),
    ("Como comparar dois arquivos modificados no Git?", "git_diff", "git"),
    ("No Git, como revisar alterações do arquivo?", "git_diff", "git"),
    ("Qual a diferença entre um commit e um push no Git?", "git_commit", "git"),
    ("Como registrar as mudanças em um commit Git?", "git_commit", "git"),
    ("Qual planeta não tem anéis?", "duvida", "negacao"),
    ("Em Ruby, como declarar variáveis?", "fora", "fora"),
    ("Em Python, como tratar um KeyError?", "py_keyerror", "erro"),
    ("Como evitar SQL injection?", "sql_parametros", "sql"),
]

def executar(casos=CASOS):
    resultados = []
    for pergunta, esperado, grupo in casos:
        bot = Crivo()
        obtido, resposta = bot.responder(pergunta)
        rank = bot._ranking(pergunta)
        candidatos = [{"id": bot.base[i]["id"], "score": round(score, 4)}
                      for score, i in rank[:3]]
        # 'duvida' e 'fora' sao abstencoes, nao acertos de intencao.
        passou = (obtido == esperado) if esperado != "fora" else obtido in ("fora", "duvida")
        resultados.append(dict(pergunta=pergunta, esperado=esperado, obtido=obtido,
                               grupo=grupo, passou=passou, candidatos=candidatos,
                               resposta=resposta[:180]))
    grupos = {}
    for grupo in sorted(set(c["grupo"] for c in resultados)):
        itens = [c for c in resultados if c["grupo"] == grupo]
        grupos[grupo] = {"acertos": sum(c["passou"] for c in itens), "total": len(itens)}
    return {"acertos": sum(c["passou"] for c in resultados), "total": len(resultados),
            "grupos": grupos, "casos": resultados,
            "limite": "Sonda de desenvolvimento posterior a v0.4, nao teste cego; respostas revisadas manualmente."}

if __name__ == "__main__":
    relatorio = executar()
    relatorio["controles_pos_ajuste"] = executar(CONTROLES_POS_AJUSTE)
    base = json.loads((PASTA / "conhecimento.json").read_text(encoding="utf-8"))
    antigos = [e for e in base if e["topico"] != "programacao"]
    # Mede novamente o recuperador nos 278 exemplos gerais, retirando a
    # pergunta avaliada do indice (nao compara so o corpus completo).
    comparacao = avaliar(antigos)
    relatorio["benchmark_geral"] = {chave: comparacao[chave] for chave in
        ("total", "acertos", "erradas", "abstencoes", "ranking_acertos")}
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    if (comparacao["total"] != 278 or comparacao["acertos"] < 192 or
            comparacao["erradas"] > 44):
        raise SystemExit("Regressão no benchmark anterior de assuntos gerais")
