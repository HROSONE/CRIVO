"""Sonda de desenvolvimento de conhecimento, composição e diálogo.

Fixada antes do compositor; não é teste cego nem avaliação de escrita
arbitrária. Usa o caminho público Crivo.responder, sem inspecionar o motor.
"""
import json
from crivo import Crivo

CASOS = [
    ([], "O que é Andrômeda?", "conhecimento:andromeda", ["galáxia", "2,5"]),
    ([], "O que é DNA?", "conhecimento:dna", ["genética", "hélice"]),
    ([], "O que é RNA?", "conhecimento:rna", ["RNA", "fita"]),
    ([], "O que é um gene?", "conhecimento:gene", ["hereditária", "proteínas"]),
    ([], "O que é um vírus?", "conhecimento:virus", ["genético", "hospedeira"]),
    ([], "O que é aprendizado de máquina?", "conhecimento:aprendizado_maquina", ["dados", "supervisionado"]),
    ([], "O que é rede neural?", "conhecimento:rede_neural", ["modelo", "pesos"]),
    ([], "O que é uma nebulosa?", "conhecimento:nebulosa", ["poeira", "estrelas"]),
    ([], "O que é ano-luz?", "conhecimento:ano_luz", ["distância", "9,46"]),
    ([], "O que é um exoplaneta?", "conhecimento:exoplaneta", ["fora", "estrelas"]),
    ([], "Fale sobre buracos negros", "escrita:explicacao", ["horizonte de eventos", "luz"]),
    ([], "Qual é a distância de Andrômeda?", "conhecimento:andromeda", ["2,5 milhões"]),
    ([], "Escreva um texto sobre o Sol e a Lua", "escrita:texto", ["Sol", "Lua"]),
    ([], "Crie um resumo sobre DNA e RNA", "escrita:resumo", ["DNA", "RNA"]),
    ([], "Faça um roteiro curto sobre fotossíntese", "escrita:roteiro", ["fotossíntese", "luz"]),
    ([], "Escreva um texto sobre HTML, CSS e JavaScript", "escrita:texto", ["HTML", "CSS", "JavaScript"]),
    ([], "Escreva um texto sobre Andrômeda em duas frases", "escrita:texto", ["Andrômeda", "2,5 milhões"]),
    (["O que é Andrômeda?"], "Mais curto", "escrita:resumo", ["Andrômeda"]),
    (["O que é o Sol?"], "Em tópicos", "escrita:topicos", ["- ", "Sol"]),
    (["O que é DNA?"], "Explique melhor", "escrita:explicacao", ["bases", "DNA"]),
    (["O que é DNA?"], "Não entendi", "escrita:simples", ["DNA"]),
    (["O que é Andrômeda?"], "Continue", "escrita:continuacao", ["constelação"]),
    (["O que é Andrômeda?"], "Qual é a fonte?", "escrita:fontes", ["science.nasa.gov"]),
    (["O que é Andrômeda?"], "Qual a distância dela?", "conhecimento:andromeda", ["2,5 milhões"]),
    (["O que é Via Láctea?"], "Qual é o nome desse braço que você falou?", "conhecimento:braco_orion", ["Órion"]),
    (["O que é Via Láctea?"], "Onde fica esse braço?", "conhecimento:braco_orion", ["Sagitário", "Perseu"]),
    (["O que é DNA?", "Oi!"], "Mais curto", "duvida", ["anterior"]),
    ([], "Mais curto", "duvida", ["anterior"]),
    ([], "Escreva um texto sobre HTML e cristal quântico inventado", "fora", ["cristal"]),
    ([], "Escreva um texto sobre uma árvore binária", "escrita:texto", ["cada nó", "dois filhos"]),
    ([], "Escreva um texto sobre um grafo cristalônico inventado", "fora", ["grafo"]),
    ([], "Escreva um texto sobre gravidade com cinco citações inventadas", "fora", ["citações"]),
    (["O que é o Sol?"], "Por quê?", "fora", ["causal"]),
]

def executar(caso):
    historico, pergunta, esperado, trechos = caso
    bot = Crivo()
    for q in historico:
        bot.responder(q)
    ident, resposta = bot.responder(pergunta)
    return {"pergunta": pergunta, "historico": historico,
            "esperado": esperado, "obtido": ident,
            "passou": ident == esperado and all(t in resposta for t in trechos),
            "resposta": resposta}

def avaliar():
    casos = [executar(c) for c in CASOS]
    return {"total": len(casos), "acertos": sum(c["passou"] for c in casos),
            "limite": "Sonda de desenvolvimento usada durante a implementação, não teste cego.",
            "casos": casos}

if __name__ == "__main__":
    print(json.dumps(avaliar(), ensure_ascii=False, indent=2))
