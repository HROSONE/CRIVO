"""Sonda pública de conversação: variações, contexto, escrita e limites.

Os cenários são verificações de desenvolvimento, não uma avaliação cega
nem evidência de entendimento de qualquer assunto ou linguagem irrestrita.
"""
import argparse
import json
from crivo import Crivo


CASOS = [
    ([], "Me explica direitinho o que seria uma sinapse", "conhecimento:mundo_sinapse", ["comunicação", "neurotransmissores"]),
    ([], "Queria entender um pouco melhor a memória", "conhecimento:mundo_memoria", ["recuperar", "podem melhorar"]),
    ([], "Cérebro é o quê?", "conhecimento:mundo_cerebro", ["órgão", "sistema nervoso"]),
    ([], "Me conta como funciona essa história de sono REM", "escrita:explicacao", ["sonhos", "normalmente"]),
    ([], "O que seria neuroplasticidade?", "conhecimento:mundo_neuroplasticidade", ["conexões", "experiências"]),
    ([], "Qual é o significado de biodiversidade?", "conhecimento:mundo_biodiversidade", ["espécies", "ecossistemas"]),
    ([], "Você poderia me explicar sobre ribossomos?", "conhecimento:mundo_ribossomo", ["proteínas", "RNA"]),
    ([], "Queria saber por que o sono ajuda a memória", "escrita:relacao", ["consolidação"]),
    ([], "Me explica para que serve clorofila", "escrita:explicacao", ["energia solar"]),
    ([], "Me diga a diferença entre ansiedade e estresse", "escrita:comparacao", ["externo", "ameaça"]),
    ([], "Gostaria de saber se Andrômeda é uma estrela", "logica:negacao_comprovada", ["disjunto", "estrela"]),
    ([], "Memória processual é o quê?", "conhecimento:mundo_memoria_procedural", ["habilidades", "bicicleta"]),
    (["O que é neurônio?"], "Fala a mesma coisa com outras palavras", "escrita:reformulacao", ["voltada a", "sinais"]),
    (["O que é memória?"], "Você pode me explicar de outro jeito?", "escrita:reformulacao", ["entende-se", "informações"]),
    (["O que é a Lua?"], "Reescreva essa explicação", "escrita:reformulacao", ["satélite natural", "29,5"]),
    (["O que é HTML e CSS?"], "Com outras palavras", "escrita:reformulacao", ["O que HTML descreve", "O que CSS define"]),
    (["O que é neurônio?"], "Pode explicar sem palavras difíceis?", "escrita:simples", ["receber e enviar", "axônio"]),
    (["O que é DNA?"], "Diga só o essencial", "escrita:resumo", ["molécula", "genéticas"]),
    (["O que é DNA?"], "Organize isso em uma lista", "escrita:topicos", ["- O DNA", "hélice"]),
    (["O que é memória procedural?"], "Me dá um exemplo na prática", "escrita:exemplo", ["bicicleta"]),
    (["O que é neurônio?"], "Pode desenvolver essa ideia?", "escrita:exploracao", ["sinapses", "Quer explorar"]),
    (["O que é DNA?", "Com outras palavras"], "De onde veio essa informação?", "escrita:fontes", ["genome.gov"]),
    (["O que é melatonina?"], "E como funciona?", "escrita:explicacao", ["luz", "escuridão"]),
    (["O que são DNA e RNA?", "Pode desenvolver essa ideia?", "sim"], "a segunda", "escrita:exploracao", ["RNA", "proteínas"]),
    (["O que é memória?", "O que é DNA?"], "Vamos voltar à memória", "escrita:retomada", ["recuperar", "experiências"]),
    (["O que é sinapse?", "Oi"], "Retome sinapse", "escrita:retomada", ["comunicação", "neurotransmissores"]),
    (["O que é memória?", "O que é DNA?"], "Voltar ao assunto anterior", "escrita:retomada", ["memória", "experiências"]),
    (["O que é memória?", "O que é DNA?"], "Recapitule nossa conversa", "escrita:recapitulacao", ["memória", "DNA"]),
    ([], "Quero conversar sobre trabalho", "conversa:abertura", ["trabalho", "situação"]),
    (["Quero conversar sobre trabalho"], "Eu quero mudar de trabalho", "conversa:relato", ["Você contou", "principal dificuldade"]),
    (["Quero conversar sobre trabalho", "Eu quero mudar de trabalho"], "Eu não consigo decidir", "conversa:relato", ["mudar de trabalho", "já tentou"]),
    (["Quero conversar sobre trabalho", "Eu quero mudar de trabalho", "Eu não consigo decidir"], "O que você acha?", "conversa:reflexao", ["opções", "critério"]),
    (["Quero conversar sobre trabalho", "Eu quero mudar de trabalho", "O que é DNA?"], "Vamos voltar ao trabalho", "conversa:retomada", ["mudar de trabalho", "O que mudou"]),
    (["O que é memória?"], "Esqueça essa conversa", "conversa:reinicio", ["começar outra conversa"]),
    (["O que é memória?", "Oi"], "Com outras palavras", "duvida", ["anterior"]),
    (["O que é memória?", "Mudar de assunto"], "Retome memória", "duvida", ["memória recente"]),
    ([], "Me explica por que o sono não ajuda a memória", "fora", ["evidência"]),
    ([], "Queria entender a memória alienígena", "fora", []),
    ([], "Me diga a diferença entre DNA e cristal quântico inventado", "fora", []),
    ([], "Me explique qual é a dose de melatonina para mim", "fora", ["dose", "pessoa"]),
]


def executar(caso):
    historico, pergunta, esperado, trechos = caso
    bot = Crivo()
    for anterior in historico:
        bot.responder(anterior)
    ident, resposta = bot.responder(pergunta)
    return dict(pergunta=pergunta, historico=historico, esperado=esperado, obtido=ident,
                passou=ident == esperado and all(t in resposta for t in trechos), resposta=resposta)


def avaliar():
    resultados = [executar(c) for c in CASOS]
    return dict(total=len(resultados), acertos=sum(r["passou"] for r in resultados),
                limite=__doc__.strip(), casos=resultados)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Exibe cenários e respostas completos")
    args = parser.parse_args()
    resultado = avaliar()
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        print("Conversação: {acertos}/{total} cenários de desenvolvimento.".format(**resultado))
        for caso in resultado["casos"]:
            if not caso["passou"]:
                print(json.dumps(caso, ensure_ascii=False))
    raise SystemExit(0 if resultado["acertos"] == resultado["total"] else 1)
