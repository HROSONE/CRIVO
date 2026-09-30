"""Diálogos autorais para a primeira GRU generativa do Crivo.

Famílias e assuntos de validação diferem do treino. Os textos aqui são
exemplos de ensino, não respostas carregadas pelo servidor. Não usa
saídas do assistente, avaliações ou conhecimento científico como corpus.
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

TEMAS = {
    "treino": [("uma ponte", "um viajante"), ("uma biblioteca", "um gato"),
               ("um jardim", "uma carta"), ("um relógio", "uma nuvem"),
               ("uma estação", "uma bicicleta"), ("um barco", "uma estrela")],
    "validacao": [("uma oficina", "uma bússola"), ("uma torre", "uma raposa")],
}

PEDIDOS = {
    "historia": (["Invente uma história curta sobre {a} e {b}", "Crie um conto sobre {a} e {b}",
                  "Me conte uma história inventada com {a} e {b}"],
                 ["Imagine uma narrativa curta sobre {a} e {b}", "Pode inventar um conto envolvendo {a} e {b}?"]),
    "poema": (["Escreva um poema sobre {a} e {b}", "Crie versos sobre {a} e {b}",
               "Faça um poema curto com {a} e {b}"],
              ["Componha alguns versos sobre {a} e {b}", "Queria um poema que juntasse {a} e {b}"]),
    "final": (["Agora dê outro final", "Mude o final da história", "Invente outro desfecho"],
              ["Como essa história poderia terminar de outro jeito?", "Queria outro final para esse conto"]),
    "escuta": (["Você entendeu o que me incomodou?", "Você entendeu o que eu quis dizer?", "O que você entendeu do que contei?"],
               ["Como você entendeu a situação que eu trouxe?", "Me diga o que entendeu de mim"]),
    "alternativa": (["Faça uma sugestão diferente", "Me dê outra possibilidade", "Quero tentar outro caminho"],
                    ["Tem um jeito diferente de lidar com isso?", "Sugira outra abordagem para meu objetivo"]),
    "ajuste": (["Você já me perguntou isso", "Essa sugestão não me ajudou", "Você está repetindo a mesma pergunta"],
               ["Você continua fazendo a mesma pergunta", "O que disse não resolveu minha dificuldade"]),
    "apoio": (["Se uma tentativa não funcionou, sou incapaz?", "Errei uma vez, isso quer dizer que não consigo?",
               "Uma ideia deu errado e acho que sou incapaz"],
              ["Uma tentativa fracassou; isso define minha capacidade?", "Só porque errei, nunca vou conseguir?"]),
    "ideia": (["Me dê uma ideia concreta usando essas informações", "Crie uma ideia a partir do que contei",
               "Combine esses dois elementos numa ideia"],
              ["O que dá para criar juntando essas coisas?", "Proponha uma possibilidade com esses elementos"]),
}

# Ensinar variações completas de escrita. Estes trechos não são importados
# pelo runtime; o único artefato de inferência é o checkpoint de pesos.
INICIOS_HISTORIA = {
    "neutro": ["Num lugar distante,", "Num caminho esquecido,", "Certa manhã,", "Naquele lugar,"],
    "leve": ["Numa manhã tranquila,", "Durante uma festa,", "Entre risos,", "No jardim da imaginação,"],
    "aventura": ["Antes da última tempestade,", "No começo da viagem,", "Diante de um caminho desconhecido,", "Ao cruzar a passagem,"],
    "simples": ["Um dia,", "A história começa assim:", "No começo,", "Naquela manhã,"],
}
MIOLOS = ["encontrou uma pista inesperada", "percebeu que o caminho tinha mudado",
          "decidiu procurar uma saída", "recebeu uma mensagem sem assinatura"]
ENCONTROS = ["apareceu para ajudar", "trouxe uma ideia diferente", "mostrou outra possibilidade", "sugeriu um caminho novo"]
FINS = ["Juntos, descobriram que a resposta estava no que haviam deixado para trás.",
        "A viagem terminou com uma descoberta pequena e uma nova pergunta.",
        "O caminho ficou mais claro quando decidiram tentar uma coisa de cada vez.",
        "O que parecia um fim virou o começo de outra história."]


def resposta(acao, estilo, variante, slots, combinacao=0):
    i = variante % 4
    if acao == "historia":
        sujeito = "@tema1"
        segundo = (" Então @tema2 " + ENCONTROS[(combinacao//4)%4] + ".") if slots.get("tema2") else " Uma surpresa mostrou outra possibilidade."
        return INICIOS_HISTORIA[estilo][i] + " " + sujeito + " " + MIOLOS[combinacao%4] + "." + segundo + " " + FINS[(combinacao//16)%4]
    if acao == "poema":
        segundo = "e @tema2" if slots.get("tema2") else "e o que ainda vai chegar"
        versos = [
            "Entre @tema1 " + segundo + ",\nainda existe um caminho.\nUm passo encontra outro passo,\ne o silêncio ganha um sentido.",
            "@tema1 passa pelo tempo,\n" + segundo + " encontra o olhar.\nO que parecia distante\naos poucos aprende a chegar.",
            "Guardo @tema1 numa palavra,\n" + segundo + " num lugar.\nEntre o começo e a chegada,\nhá uma história para contar.",
            "Quando @tema1 encontra o vento,\n" + segundo + " descobre o chão,\no mundo cabe por um instante\ndentro de uma pequena canção.",
        ]
        linhas = versos[i].split("\n")[:2] + versos[combinacao%4].split("\n")[2:]
        return "\n".join(linhas)
    if acao == "final":
        if not slots.get("tema2"):
            return [
                "No fim, @tema1 encontrou uma pista diferente. Ela não levava a um tesouro: levava a uma conversa que havia ficado para depois.",
                "@tema1 decidiu voltar pelo mesmo caminho. A surpresa era simples: a resposta tinha mudado durante a viagem.",
                "@tema1 guardou a descoberta e seguiu em frente. Mais tarde, uma mensagem abriu o caminho para uma nova aventura.",
                "Quando @tema1 chegou, a história ganhou outra direção. Em vez de encerrar a viagem, uma nova pergunta levou até a próxima curva.",
            ][i]
        return [
            "No fim, @tema1 encontrou @tema2 novamente. A pista não levava a um tesouro: levava a uma conversa que os dois haviam adiado.",
            "@tema1 decidiu voltar com @tema2. A surpresa era simples: o caminho que procuravam estava sendo construído enquanto caminhavam.",
            "@tema1 e @tema2 guardaram a descoberta e seguiram caminhos diferentes. Mais tarde, uma mensagem reuniu os dois para uma nova aventura.",
            "Quando @tema1 encontrou @tema2, a história ganhou outra direção. Em vez de encerrar a viagem, decidiram descobrir o que havia depois da próxima curva.",
        ][i]
    if acao == "escuta":
        return [
            "O que entendi foi isto: você trouxe “@relato”. Estou partindo desse relato, sem supor detalhes que não contou. Qual parte você quer explorar agora?",
            "Você me contou “@relato”. Esse é o ponto que estou acompanhando. Se deixei alguma coisa importante de fora, pode me corrigir.",
            "Estou entendendo sua situação a partir de “@relato”. Podemos separar o que aconteceu do que você esperava que acontecesse. Qual dessas partes pesa mais?",
            "Pelo que você contou, o assunto é “@relato”. Quero acompanhar isso com você. Tem algum detalhe que mudaria a maneira de entender a situação?",
        ][i]
    if acao == "alternativa":
        objetivo = "@objetivo" if slots.get("objetivo") else "@relato"
        limite = " Você também trouxe a restrição “@restricao”." if slots.get("restricao") else ""
        return [
            "Para “"+objetivo+"”, outra possibilidade é testar só uma parte e observar o resultado."+limite+" Escolha uma tarefa que tenha um começo e um fim claros.",
            "Podemos olhar “"+objetivo+"” por outro caminho: trocar uma tentativa grande por um experimento pequeno."+limite+" O que seria possível testar primeiro?",
            "Uma alternativa para “"+objetivo+"” é mudar a ordem das etapas."+limite+" Comece pelo ponto mais fácil de verificar e use o resultado para escolher a próxima tentativa.",
            "Vamos criar outra possibilidade para “"+objetivo+"”: diminuir uma exigência e manter o que é essencial."+limite+" Qual parte você pode ajustar sem perder o objetivo?",
        ][i]
    if acao == "ajuste":
        return [
            "Entendi que minha resposta não ajudou. Vou mudar a abordagem. Você trouxe “@relato”; podemos escolher uma ação pequena em vez de repetir a mesma pergunta.",
            "Obrigado por apontar isso. Quero acompanhar “@relato” de outro jeito. Podemos comparar uma possibilidade concreta com o que você já tentou.",
            "Vou ajustar o caminho da conversa. Para “@relato”, podemos começar pelo que você já sabe e identificar só o detalhe que falta.",
            "Entendi o pedido de mudança. Estamos falando de “@relato”. Uma abordagem diferente é imaginar um próximo passo e ver se ele respeita suas prioridades.",
        ][i]
    if acao == "apoio":
        return [
            "Uma tentativa que não funcionou não basta para definir toda a sua capacidade. Você trouxe “@relato”. Podemos examinar o que aconteceu naquela tentativa e o que poderia mudar na próxima.",
            "O resultado de uma tentativa e sua capacidade inteira são coisas diferentes. Partindo de “@relato”, podemos procurar um detalhe que seja possível ajustar, sem transformar um erro numa conclusão sobre você.",
            "Não precisamos concluir que você é incapaz a partir de um único resultado. Você contou “@relato”. Vale separar a dificuldade daquela situação do que ainda pode ser aprendido ou testado.",
            "Você trouxe “@relato”. Uma experiência difícil pode mostrar um obstáculo, mas não determina sozinha o que você consegue fazer. Podemos pensar num teste menor e num critério para avaliar o resultado.",
        ][i]
    if acao == "ideia":
        return [
            "Uma possibilidade inventada é juntar @tema1 com @tema2 e mudar uma regra da combinação. Faça uma versão pequena, teste o que acontece e escolha o detalhe que ficou mais interessante.",
            "Podemos criar uma ideia em que @tema1 precisa de @tema2 para resolver um desafio. A surpresa aparece quando os dois trocam de papel. Que regra você gostaria de experimentar?",
            "Imagine @tema1 e @tema2 num mesmo projeto, cada um com uma função diferente. Depois inverta essas funções e observe que nova possibilidade aparece.",
            "Uma ideia é aproximar @tema1 e @tema2 por um objetivo comum. Crie uma limitação simples e procure uma maneira inesperada de trabalhar dentro dela.",
        ][i]
    raise ValueError("Ação sem exemplo autoral")


def gerar():
    exemplos = []
    for split,temas in TEMAS.items():
        for acao,(padroes_treino,padroes_validacao) in PEDIDOS.items():
            padroes = padroes_treino if split=="treino" else padroes_validacao
            estilos = list(INICIOS_HISTORIA) if acao in ("historia","poema") else ["neutro"]
            for familia,padrao in enumerate(padroes):
                for assunto,(a,b) in enumerate(temas):
                    for estilo in estilos:
                        for variante in range(4):
                            # Um diálogo inteiro pertence a uma partição.
                            ident = "{}:{}:{}:{}:{}:{}".format(split,acao,familia,assunto,estilo,variante)
                            slots = {"tema1":a,"tema2":b}
                            relato = "Gostei de "+a+", mas tive uma dificuldade com "+b
                            objetivo = "criar um projeto com "+a
                            restricao = "Só tenho "+str(10+5*assunto)+" minutos à noite"
                            historico = []
                            if acao in ("escuta","ajuste","apoio"):
                                slots={"relato":relato};historico=["Quero conversar sobre uma situação",relato]
                            elif acao=="alternativa":
                                slots={"relato":relato,"objetivo":objetivo,"restricao":restricao}
                                historico=["Quero "+objetivo,restricao]
                            elif acao=="final":
                                historico=["Invente uma história sobre "+a+" e "+b]
                            elif acao=="ideia":
                                historico=["Estou criando um projeto","Quero juntar "+a+" com "+b]
                            mensagem = padrao.format(a=a,b=b)
                            combinacao = ((familia*len(temas)+assunto+(20 if split=="validacao" else 0))*7)%64
                            ctx={"acao":acao,"estilo":estilo,"variante":variante,"slots":slots,
                                 "mensagem":mensagem,"historico":historico}
                            exemplos.append({"split":split,"familia":split+":"+acao+":"+str(familia),
                                             "dialogo":ident,"contexto":ctx,"resposta":resposta(acao,estilo,variante,slots,combinacao)})
                            if acao in ("historia","poema"):
                                sem_segundo=dict(ctx,slots={"tema1":a},mensagem=padrao.format(a=a,b="algo inesperado"))
                                exemplos.append({"split":split,"familia":split+":"+acao+":"+str(familia),
                                                 "dialogo":ident,"contexto":sem_segundo,
                                                 "resposta":resposta(acao,estilo,variante,sem_segundo["slots"],combinacao)})
                            elif acao=="final":
                                simples=dict(ctx,slots={"tema1":a},historico=["Invente uma história sobre "+a])
                                exemplos.append({"split":split,"familia":split+":"+acao+":"+str(familia),
                                                 "dialogo":ident,"contexto":simples,
                                                 "resposta":resposta(acao,estilo,variante,simples["slots"],combinacao)})
                            elif acao=="alternativa":
                                for tem_objetivo,tem_restricao in ((True,False),(False,True),(False,False)):
                                    argumentos={"relato":relato}
                                    if tem_objetivo: argumentos["objetivo"]=objetivo
                                    if tem_restricao: argumentos["restricao"]=restricao
                                    anterior=["Quero "+objetivo] if tem_objetivo else [relato]
                                    if tem_restricao: anterior.append(restricao)
                                    alternativo=dict(ctx,slots=argumentos,historico=anterior)
                                    exemplos.append({"split":split,"familia":split+":"+acao+":"+str(familia),
                                                     "dialogo":ident,"contexto":alternativo,
                                                     "resposta":resposta(acao,estilo,variante,argumentos,combinacao)})
    return {"versao":1,"autoria":"Exemplos escritos para ensinar escrita contextual; sem corpus externo ou respostas do modelo.",
            "limite":"Primeiro currículo pequeno e controlado; famílias de pedidos e temas separados não tornam a avaliação externa ou cega.",
            "exemplos":exemplos}


if __name__ == "__main__":
    dados=gerar()
    destino=RAIZ/"curriculo_geracao.json"
    destino.write_text(json.dumps(dados,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for split in ("treino","validacao"):
        casos=[c for c in dados["exemplos"] if c["split"]==split]
        print(split,len(casos),"exemplos",len({c['dialogo'] for c in casos}),"contextos de diálogo",
              len({c['resposta'] for c in casos}),"respostas deslexicalizadas")
