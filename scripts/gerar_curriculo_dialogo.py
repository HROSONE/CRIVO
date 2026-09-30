"""Currículo de atos de diálogo, com famílias e assuntos de validação separados.

Não usa saídas do bot, bases factuais ou benchmarks finais. Cada exemplo traz
o estado ANTERIOR à fala. Os alvos variam, mas o rótulo é uma ação de conversa.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from rede_sequencial import palavras


TREINO = {
    "relato": [
        "Eu estou {estado}", "Hoje estou {estado}", "Tô {estado} hoje",
        "Foi um dia {estado}", "Eu tive um problema com {tema}",
        "Meu nome é {nome}", "Pode me chamar de {nome}", "Me chamo {nome}",
        "Meu amigo falou sobre {tema}", "Minha irmã está {estado}",
        "Estou fazendo {tema}", "Eu tenho {tema}", "Meu chefe pediu {tema}",
        "Eu não consigo {acao}", "Não estou conseguindo {acao}",
        "Já tentei {acao}", "Tentei {acao} ontem", "O problema é {tema}",
        "Mas tenho {tema}", "Só tenho {numero} minutos por dia",
        "Tenho duas opções: {acao} ou {alternativa}", "Estou entre {acao} e {alternativa}",
        "Eu moro em {tema}", "Amanhã tenho {tema}", "Ele não me respondeu desde ontem",
        "Aconteceu uma coisa com {tema}", "Fiquei {estado} depois disso",
        "Na verdade, meu nome é {nome}", "Eu não gosto de {tema}",
        "Não quero mais {acao}", "Não tenho tempo para {acao}",
        "Tenho {numero} minutos para {acao}", "Estou cansado, mas preciso {acao}",
        "Acabei tendo um dia {estado}", "Fiquei {estado}", "Acabei de ficar {estado}",
        "Meu colega comentou {tema}", "Minha colega recebeu {tema}",
        "Não consegui terminar {tema}", "Hoje sobraram {numero} minutos para mim",
        "Agora pode me chamar de {nome}", "Eu sou {nome}",
    ],
    "preferencia": [
        "Eu gosto de {tema}", "Gosto muito de {tema}", "Curto {tema}",
        "Prefiro {tema}", "Adoro {tema}", "O que eu mais gosto é {tema}",
        "Minha coisa favorita é {tema}", "Eu gosto de {tema} e {alternativa}",
        "Eu sou fã de {tema}", "Sou bastante fã de {tema}",
        "O meu passatempo favorito é {tema}", "O que eu prefiro é {tema}",
        "Minha atividade preferida é {tema}", "Gosto mais de {tema}",
    ],
    "objetivo": [
        "Quero {acao}", "Eu quero {acao}", "Pretendo {acao}",
        "Meu objetivo é {acao}", "Estou pensando em {acao}",
        "Tenho vontade de {acao}", "Queria conseguir {acao}",
        "Gostaria de {acao}", "Eu queria {acao}",
        "Ando com vontade de {acao}", "Minha meta agora é {acao}",
        "A minha intenção é {acao}", "Ando pensando em {acao}",
        "Minha meta é {acao}", "Meu plano é {acao}",
    ],
    "ponto_de_vista": [
        "Acho que {proposicao}", "Eu acho que {proposicao}",
        "Na minha opinião {proposicao}", "Penso que {proposicao}",
        "Para mim {proposicao}", "Tenho a impressão de que {proposicao}",
        "Talvez {proposicao}", "Me parece que {proposicao}",
        "A minha opinião é que {proposicao}", "Minha impressão é que {proposicao}",
        "Pelo que eu vejo, {proposicao}", "Eu penso que {proposicao}",
    ],
    "refletir": [
        "O que você acha?", "Você concorda comigo?", "Concorda com isso?",
        "O que você faria no meu lugar?", "O que vale mais a pena?",
        "Como posso decidir?", "Qual das opções você escolheria?",
        "Me ajuda a pensar nisso", "Isso faz sentido para você?",
        "O que eu faço?", "E agora?", "O que você pensa disso?",
        "Será que ele está bravo comigo?", "Será que ela está me evitando?",
        "Como você vê essa situação?", "Como avaliar essas opções?",
        "Me ajude a avaliar as alternativas", "Vamos pesar as opções?",
        "Como você avaliaria a situação?", "Você pode me ajudar a escolher?",
        "Pode me ajudar a avaliar essas possibilidades?",
    ],
    "planejar": [
        "Por onde eu começo?", "Como posso organizar isso?",
        "Me ajuda a montar um plano", "Como eu posso começar?",
        "Qual seria o próximo passo?", "O que posso tentar primeiro?",
        "Me ajuda a planejar isso", "Dá para dividir em passos?",
        "Como faço para chegar nesse objetivo?", "Pode sugerir um começo?",
        "Qual o primeiro passo que você sugere?", "Quero organizar um plano",
        "Me ajude a planejar um caminho", "Como divido isso em etapas?",
    ],
    "ideias": [
        "Tem alguma ideia?", "Me dá uma ideia", "Pode sugerir alguma coisa?",
        "Vamos pensar em possibilidades", "Me ajuda a ter ideias",
        "Como deixo isso mais interessante?", "O que eu poderia mudar?",
        "Alguma sugestão?", "Como posso melhorar meu projeto?",
        "E se eu tentasse outro caminho?",
        "O que podemos inventar?", "Vamos explorar possibilidades?",
        "Que outras possibilidades você vê?", "O que dá para criar a partir disso?",
    ],
    "criterios": [
        "O que faz {tema} ser bom?", "O que faz {tema} ser interessante?",
        "Como posso avaliar {tema}?", "Como saber se {tema} vale a pena?",
        "O que torna {tema} útil?", "O que faz {tema} dar certo?",
        "Como sei se {tema} ficou bom?", "Quais critérios usar para {tema}?",
    ],
    "lembrar": [
        "Qual é meu nome?", "Como eu me chamo?", "Você lembra meu nome?",
        "O que eu disse que gosto?", "O que eu gosto de fazer?",
        "Lembra o que eu quero fazer?", "Qual é meu objetivo?",
        "O que eu contei para você?", "O que você lembra de mim?",
        "Quanto tempo eu disse que tenho?", "Quais são minhas opções?",
        "Como eu disse que queria ser chamado?", "Lembra como eu me chamo?",
        "Lembra quais coisas eu gosto?", "Quais coisas eu disse que curto?",
    ],
    "motivo": [
        "Por quê?", "Por que você acha isso?", "Por que isso acontece?",
        "Qual é o motivo?", "Por que você sugeriu isso?", "Como assim?",
        "Por que você diz isso?", "Pode justificar?",
        "Qual é a razão da sua sugestão?", "Qual a razão disso?",
        "Como chegou a essa conclusão?", "De onde veio sua conclusão?",
    ],
    "reparar": [
        "Não entendi direito", "Ainda não entendi", "Pode explicar mais fácil?",
        "Pode explicar de um jeito mais simples?", "Explica sem complicar",
        "Fiquei confuso com essa explicação", "Pode falar de um jeito mais claro?",
        "Não ficou claro para mim", "Consegue simplificar essa resposta?",
        "Não consegui entender a explicação", "Não acompanhei o que você disse",
        "Explica de uma maneira simples", "Explica de um modo mais fácil",
    ],
    "reciproco": [
        "E você?", "E tu?", "E vc?", "Você também?",
        "Qual é sua opinião?", "Você gosta disso?", "Você curte isso também?",
        "E você, o que acha?", "Você tem alguma coisa preferida?",
    ],
    "abrir": [
        "Queria trocar uma ideia contigo", "Quero bater papo com você",
        "Podemos conversar um pouco?", "Tô querendo conversar",
        "Queria só conversar", "Quero te contar uma coisa",
        "Posso falar uma coisa?", "Preciso conversar com alguém",
        "Queria puxar uma conversa", "Pode trocar uma ideia comigo?",
    ],
    "resposta": [
        "Sim", "Não", "Mais ou menos", "Um pouco", "Os dois", "Ainda não",
        "{tema}", "Sobre {tema}", "{estado}", "{numero} minutos",
        "Porque {proposicao}", "Só {tema}", "Principalmente {tema}",
        "Ainda não sei", "Não faço ideia", "Talvez {tema}", "Nenhuma",
        "Um {tema}", "Uma {tema}", "De {tema}",
        "Um {tema} com {alternativa}", "Uma {tema} sobre {alternativa}",
        "Sobre {tema} que aconteceu ontem", "A parte de {tema}",
        "{tema} com {alternativa}", "É {tema}",
    ],
    "outro": [
        "O que é {tema}?", "O que são {tema}?", "Como funciona {tema}?",
        "Para que serve {tema}?", "Você conhece {tema}?", "Quem inventou {tema}?",
        "Qual é a diferença entre {tema} e {alternativa}?", "Por que {proposicao}?",
        "Onde fica {tema}?", "Quando surgiu {tema}?", "Como usar {tema}?",
        "Escreva um texto sobre {tema}", "Faça um programa que leia {tema}",
        "Me explique o que é {tema}", "Você acha que {proposicao}?",
        "Não explique {tema}", "Não quero saber o que é {tema}",
        "Não sei se {proposicao}", "Qual é a fonte?", "Retome {tema}",
        "Mudar de assunto", "Recapitule nossa conversa", "Oi", "Obrigado",
        "Você é burro", "Isso está errado", "Você pensa?", "O que sabe fazer?",
        "Ele perguntou o que é {tema}", "Meu amigo perguntou o que é {tema}",
        'O texto diz "eu gosto de {tema}"', '`print("{tema}")`',
        "Se {proposicao}, o que acontece?", "{tema} não é {alternativa}?",
        "Liste {tema}", "Fale sobre {tema}", "Não conheço {tema}, o que é?",
        "Eu quero saber o que é {tema}", "Eu gosto de {tema}, mas o que é {alternativa}?",
        "Meu nome é {nome}. O que é {tema}?", "E {tema}?",
        "De onde veio essa informação?", "Você dorme?", "Você tem consciência?",
        "Qual é o seu nome?", "Como você foi criado?", "1", "2", "a primeira",
    ],
}

# Construções diferentes e valores fora do treino. Não são ajustadas a
# respostas do bot; o treino apenas produz um relatório sobre esta partição.
VALIDACAO = {
    "relato": ["Acabei ficando {estado}", "O dia de hoje foi {estado}",
               "Aqui pode me chamar de {nome}", "Meu colega trouxe {tema}",
               "Não consegui {acao} hoje", "Sobraram {numero} minutos no meu dia"],
    "preferencia": ["Sou fã de {tema}", "Meu passatempo preferido é {tema}"],
    "objetivo": ["Ando querendo {acao}", "A minha meta é {acao}"],
    "ponto_de_vista": ["A minha impressão é que {proposicao}", "Pelo que penso, {proposicao}"],
    "refletir": ["Pode me ajudar a pesar essas alternativas?", "Como você avaliaria isso?"],
    "planejar": ["Qual o primeiro passo para isso?", "Me ajude a organizar um caminho"],
    "ideias": ["Que possibilidades dá para explorar?", "O que dá para inventar aqui?"],
    "criterios": ["O que faz {tema} ser uma boa escolha?", "Qual a melhor forma de avaliar {tema}?"],
    "lembrar": ["Como foi que eu disse que me chamo?", "Quais coisas eu falei que curto?"],
    "motivo": ["Qual a razão desse conselho?", "De onde tirou essa conclusão?"],
    "reparar": ["Não consegui acompanhar a explicação", "Explica de uma maneira mais fácil"],
    "reciproco": ["E você, o que pensa?", "Você tem alguma preferência?"],
    "abrir": ["Podemos trocar uma ideia?", "Queria puxar um papo contigo"],
    "resposta": ["Por causa de {tema}", "A parte de {tema}", "Acho que {tema}"],
    "outro": ["Qual o significado de {tema}?", "Poderia definir {tema}?",
              "Esse {tema} tem relação com {alternativa}?", "Meu amigo quer saber como funciona {tema}",
              "O que é um nome?", "O que é preferência?", "O que é planejar?"],
}

VALORES = {
    "treino": dict(
        tema=["meu projeto", "fotografia", "uma apresentação", "um curso", "meus estudos", "uma viagem"],
        estado=["cansado", "animada", "difícil", "puxado", "frustrada", "feliz"],
        nome=["Ana", "Bruno", "Davi", "Iara", "Lucas", "Tainá"],
        acao=["aprender a cozinhar", "organizar meus estudos", "mudar de trabalho", "criar um projeto", "estudar hoje", "praticar desenho"],
        alternativa=["descansar", "ouvir música", "adiar para amanhã", "fazer uma pausa", "pedir ajuda", "conversar primeiro"],
        proposicao=["isso pode dar certo", "essa escolha é melhor", "aprender exige prática", "a tecnologia afasta as pessoas", "ele não gostou", "tudo tem dois lados"],
        numero=["10", "15", "30", "40", "50", "60"],
    ),
    "validacao": dict(
        tema=["restauração de violinos", "um clube de astronomia", "minha horta vertical"],
        estado=["esgotada", "aliviado", "complicado"], nome=["Cecília", "Hugo", "Maíra"],
        acao=["montar um observatório", "restaurar um instrumento", "cultivar temperos"],
        alternativa=["medir com calma", "testar uma maquete", "reservar o fim de semana"],
        proposicao=["construir junto é mais interessante", "a pressa atrapalha", "ele prefere ficar sozinho"],
        numero=["12", "25", "35"],
    ),
}


def gerar():
    exemplos, lexico = [], set()
    for split, familias in (("treino", TREINO), ("validacao", VALIDACAO)):
        valores = VALORES[split]
        for ato, formas in familias.items():
            for i, forma in enumerate(formas):
                if split == "treino":
                    lexico.update(t for t, _, _ in palavras(re.sub(r"\{\w+\}", "", forma)))
                estados = ["livre", "pessoal", "factual", "pendente"]
                if ato == "resposta":
                    estados = ["pendente"]
                for k in range(len(valores["tema"]) if "{" in forma else 1):
                    texto = forma.format(**{chave: vs[k % len(vs)] for chave, vs in valores.items()})
                    for estado in estados:
                        exemplos.append(dict(texto=texto, estado=estado, ato=ato,
                                             familia=split + ":" + ato + ":" + str(i), split=split))
    # Perguntas e pontuação têm representação estável, sem apagar o original.
    lexico.update("voce estou que por porque nao meu minha nome gosto quero com como sim entendi".split())
    return dict(versao=1, descricao=__doc__.strip(), lexico=sorted(lexico), exemplos=exemplos)


if __name__ == "__main__":
    destino = RAIZ / "curriculo_dialogo.json"
    dados = gerar()
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(destino), len(dados["exemplos"]), "falas com estado anterior")
