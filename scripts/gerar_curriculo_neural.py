"""Exemplos autorais de operações e spans; não usa conhecimento factual.

Não importa nem lê o benchmark final. Nomes aqui são argumentos variáveis,
inclusive nomes fictícios. As famílias de validação não entram no gradiente.
"""
import json
from pathlib import Path

TREINO = {
    "definir": ["O que é {alvo}?", "Defina {alvo}.", "Me explica o que é {alvo}.",
        "Eu quero entender {alvo}.", "O que significa {alvo}?", "{alvo} é o quê?",
        "Por favor, me diga o que seria {alvo}.", "Eu queria saber o que é {alvo}.",
        "Fale sobre {alvo}.", "Não sei o que é {alvo}.", "Não entendi o significado de {alvo}.",
        "Tenho uma dúvida: o que é {alvo}?", "Minha pergunta é: o que significa {alvo}?",
        "Gostaria de uma explicação sobre {alvo}.", "Você sabe o significado de {alvo}?",
        "Quero conhecer o significado de {alvo}.", "Você me conta sobre {alvo}?",
        "Estou tentando entender {alvo}.", "{alvo}: eu queria saber o significado.",
        "Explique este termo: {alvo}.", "Quero uma definição para {alvo}.",
        "Nunca ouvi falar de {alvo}, pode explicar?", "Pode me esclarecer o que é {alvo}?",
        "{alvo}, qual o significado desse termo?", "Pode dizer o significado de {alvo}?",
        "Ajude a compreender este nome: {alvo}.", "Pode me ajudar com uma definição de {alvo}?",
        "Sobre {alvo}, não faço ideia e quero saber a definição.",
        "Me dê uma ideia do significado de {alvo}.", "Não tenho ideia sobre {alvo}; explique.",
        "Eu ainda quero compreender {alvo}.",
        "Explique esse nome para mim: {alvo}.", "Preciso de ajuda com a definição de {alvo}."],
    "funcionamento": ["Como funciona {alvo}?", "Me conta como age {alvo}.",
        "Queria saber o funcionamento de {alvo}.", "Explique como funciona {alvo}.",
        "{alvo}: qual o funcionamento?"],
    "funcao": ["Para que serve {alvo}?", "Qual é a função de {alvo}?",
        "Queria entender a utilidade de {alvo}.", "Explique a função de {alvo}.",
        "{alvo}: serve para quê?"],
    "comparar": ["Compare {alvo} com {outro}.", "Qual a diferença entre {alvo} e {outro}?",
        "O que diferencia {alvo} de {outro}?", "{alvo} e {outro} são iguais?",
        "Me diga a diferença de {alvo} e {outro}.",
        "Mostre a diferença de {alvo} para {outro}.",
        "Quero uma comparação de {alvo} com {outro}."],
    "reformular": ["Fale a mesma coisa com outras palavras.", "Fala de outro jeito.",
        "Diga isso de outra maneira.", "Reformule a resposta.", "Reescreva essa explicação.",
        "Pode explicar de outro jeito?", "Eu quero a mesma ideia em outras palavras."],
    "simplificar": ["Explique sem palavras difíceis.", "Pode explicar sem palavras difíceis?",
        "Fale mais simples.", "Simplifique a explicação.", "Deixe isso mais fácil de entender.",
        "Quero uma explicação simples."],
    "resumir": ["Resuma isso.", "Mais curto.", "Pode resumir a resposta?",
        "Diga só o essencial.", "Faça um resumo dessa explicação.", "Quero uma versão curta."],
    "topicos": ["Organize em tópicos.", "Coloque isso em tópicos.", "Faça uma lista da resposta.",
        "Divida a explicação em tópicos.", "Apresente a mesma ideia em uma lista."],
    "fontes": ["Qual é a fonte?", "De onde veio essa informação?", "Quais são suas fontes?",
        "Mostre a origem da informação.", "Quero conferir as referências.", "Pode citar a fonte?"],
    "retomar": ["Retome {alvo}.", "Volte ao assunto {alvo}.", "Vamos voltar a {alvo}.",
        "Quero retomar {alvo}.", "Vamos falar novamente sobre {alvo}.",
        "Posso voltar a falar de {alvo}?",
        "Eu gostaria de voltar ao tema {alvo}.",
        "Consegue voltar a conversar sobre {alvo}?",
        "Você consegue retomar a conversa sobre {alvo}?",
        "A gente queria voltar a falar de {alvo}.",
        "Eu queria que você voltasse a falar de {alvo}."],
    "negado": ["Não me explique {alvo}.", "Sobre {alvo}, não quero uma explicação.",
        "Não quero saber o que é {alvo}.", "Não defina {alvo}.",
        "Não pedi uma explicação sobre {alvo}.", "Explicar {alvo} não é meu pedido.",
        "Eu não quero que você fale sobre {alvo}.", "Não explique o significado de {alvo}.",
        "Não é para definir {alvo}.", "Eu não solicitei a definição de {alvo}.",
        "Explicar {alvo} não foi minha solicitação.", "A explicação de {alvo} não foi meu pedido.",
        "Definir {alvo} não é o meu pedido."],
    "outro": ["{alvo} é uma palavra nesse texto.", "Será que {alvo} cura todas as doenças?",
        "Quero comprar {alvo}.", "Você dorme?", "Ele perguntou o que é {alvo} ontem.",
        "A pessoa disse: defina {alvo}.", "O cachorro perseguiu o gato.",
        "Faça meu diagnóstico.", "Qual dose devo tomar?", "Abra o aplicativo de {alvo}.",
        "Onde posso comprar {alvo}?", "Calcule 12 vezes 7.", "Isso é impossível.",
        "Eu acho que {alvo} não funciona.", "O que é o dobro de 18?"],
}

VALIDACAO = {
    "definir": ["Você me ajuda a saber o significado de {alvo}?",
        "Ainda não compreendo o que seria {alvo}.", "{alvo}, me diga uma definição."],
    "funcionamento": ["Eu gostaria de saber como age {alvo}."],
    "funcao": ["Você me conta para que serve {alvo}?"],
    "comparar": ["Me explique a diferença de {alvo} para {outro}."],
    "reformular": ["Apresente a mesma explicação de outra forma."],
    "simplificar": ["Dê uma explicação mais fácil."],
    "resumir": ["Encurte a explicação anterior."],
    "topicos": ["Queria ver a explicação organizada numa lista."],
    "fontes": ["Diga a referência dessa informação."],
    "retomar": ["Podemos retomar o assunto {alvo}?"],
    "negado": ["Definir {alvo} não foi o que solicitei."],
    "outro": ["Se {alvo} existisse em outra dimensão, qual seria sua massa?"],
}

NOMES_TREINO = ["neurônio", "sinapse", "memória", "hipocampo", "DNA", "RNA", "Andrômeda",
    "gravidade", "internet", "neuroplasticidade", "API", "Xenofluxo", "campo de luminância",
    "rede de sinais", "módulo de QZX", "grande esfera opaca", "energia hipotética rara",
    "memória alienígena", "memória se tiver capacidade infinita", "partícula sem nome",
    "célula muito pequena", "grande objeto desconhecido", "SQL", "HTML e CSS",
    "campo com outra função", "explicação de sinais", "mapa antes da ponte",
    "rede não circular", "módulo === raro"]
NOMES_VALIDACAO = ["enzima", "Flaron", "campo magnético oblíquo", "sequência de qubit",
    "proteína desconhecida", "dispositivo de segurança", "vento solar", "campo alienígena inventado"]


def instanciar(modelo, alvo, outro):
    # Os marcadores registram spans antes da formação do texto final.
    bruto = modelo.replace("{alvo}", "\x01" + alvo + "\x02").replace("{outro}", "\x03" + outro + "\x04")
    texto, spans, aberto = "", {}, {}
    for c in bruto:
        if c in "\x01\x03":
            aberto["alvo" if c == "\x01" else "outro"] = len(texto)
        elif c in "\x02\x04":
            chave = "alvo" if c == "\x02" else "outro"
            spans[chave] = [aberto[chave], len(texto)]
        else:
            texto += c
    return texto, spans


def gerar():
    dados = []
    for split, familias, nomes in (("treino", TREINO, NOMES_TREINO),
                                   ("validacao", VALIDACAO, NOMES_VALIDACAO)):
        for ato, modelos in familias.items():
            for k, modelo in enumerate(modelos):
                alvos = nomes if "{alvo}" in modelo else nomes[:1]
                for j, alvo in enumerate(alvos):
                    texto, spans = instanciar(modelo, alvo, nomes[(j+3) % len(nomes)])
                    if ato == "outro":
                        spans = {}
                    dados.append(dict(texto=texto, ato=ato, spans=spans, split=split,
                                      familia=split + ":" + ato + ":" + str(k)))
    return dict(versao=1, origem="Autoral; nomes variáveis sem respostas factuais.", exemplos=dados)


if __name__ == "__main__":
    caminho = Path(__file__).resolve().parents[1] / "curriculo_linguagem_neural.json"
    caminho.write_text(json.dumps(gerar(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
