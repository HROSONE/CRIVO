"""Currículo sintético autoral para a GRU generativa contextual do Crivo.

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


# Ampliação v2: repertório de diálogo e escrita, ainda sem corpus externo.
# Os contextos pessoais são declarações autorais, não fatos aprendidos.
import sys
sys.path.insert(0, str(RAIZ))
from linguagem_gerativa import VARIANTES, ESTILOS, slots_requeridos

_RESPOSTA_V1 = resposta
TEMAS = {
    'treino': [('uma ponte', 'um viajante'), ('uma biblioteca', 'um gato'),
               ('um jardim', 'uma carta'), ('um relógio', 'uma nuvem'),
               ('uma estação', 'uma bicicleta'), ('um barco', 'uma estrela'),
               ('uma praça', 'uma mala'), ('um teatro', 'uma chave'),
               ('uma janela', 'um desenho'), ('um moinho', 'uma fita'),
               ('uma trilha', 'um espelho'), ('uma cabana', 'um violino')],
    'validacao': [('uma oficina', 'uma bússola'), ('uma torre', 'uma raposa'),
                  ('uma varanda', 'um envelope'), ('um corredor', 'uma lanterna')],
}
INICIOS_HISTORIA.update({
    'carinhoso': ['Numa tarde acolhedora,', 'Com um gesto de cuidado,', 'Perto de um lugar querido,', 'Na companhia de uma lembrança boa,'],
    'formal': ['No início daquela jornada,', 'Ao observar a passagem,', 'Durante uma visita inesperada,', 'Diante daquela descoberta,'],
    'divertido': ['No dia em que tudo saiu do avesso,', 'Depois de uma confusão engraçada,', 'Entre uma risada e um tropeço,', 'Quando a surpresa chegou sem avisar,'],
    'misterioso': ['Quando o último sinal desapareceu,', 'Atrás de uma porta esquecida,', 'Naquela noite silenciosa,', 'Depois de ouvir passos na passagem,'],
})

EXTRAS_PEDIDOS = {
 'historia': ['Quero uma história sobre {a} e {b}', 'Por favor, escreva um conto com {a} e {b}', 'Faça uma narrativa inventada envolvendo {a} e {b}'],
 'poema': ['Quero um poema para falar de {a} e {b}', 'Pode criar poesia com {a} e {b}?', 'Escreva alguns versos juntando {a} e {b}'],
 'final': ['Essa história precisa de um final diferente', 'Troque o desfecho por outra possibilidade', 'Faça o conto terminar de outra maneira'],
 'escuta': ['Me mostre se acompanhou o que relatei', 'Qual parte da minha situação você compreendeu?', 'Você consegue dizer o que eu estava tentando explicar?'],
 'alternativa': ['Quero outra proposta que respeite o que falei', 'Pense em um caminho diferente para eu experimentar', 'Dê uma opção que ainda não tentamos'],
 'ajuste': ['Você está voltando para a mesma resposta', 'Isso que sugeriu não combina com o que eu preciso', 'Mude a abordagem porque a anterior não me serviu'],
 'apoio': ['Uma coisa deu errado e acho que nunca vou conseguir', 'Estou concluindo que sou incapaz porque falhei', 'Não deu certo uma vez; minha capacidade é tão pequena assim?'],
 'ideia': ['Quero uma proposta criativa combinando esses elementos', 'Imagine um projeto juntando as duas coisas que mencionei', 'Sugira uma combinação nova a partir desses temas'],
}
VALIDACAO_EXTRA = {
 'historia': 'Queria ler uma ficção com {a} e {b}',
 'poema': 'Gostaria de uma poesia que aproximasse {a} de {b}',
 'final': 'Como fecharia esse conto sem repetir o desfecho anterior?',
 'escuta': 'Você captou a parte que me afetou?',
 'alternativa': 'Que possibilidade ainda posso experimentar sem repetir a anterior?',
 'ajuste': 'Tente responder de outra maneira, essa não me serviu',
 'apoio': 'Uma tentativa fracassada prova que sou incapaz?',
 'ideia': 'Como poderíamos misturar os dois temas num projeto inventado?',
}
for _acao, _extras in EXTRAS_PEDIDOS.items():
    _antigos, _validacao = PEDIDOS[_acao]
    PEDIDOS[_acao] = (_antigos + _extras, _validacao + [VALIDACAO_EXTRA[_acao]])
PEDIDOS.update({
 'mensagem': (
  ['Escreva uma mensagem para {p} sobre {r}', 'Quero mandar uma mensagem a {p} para falar de {r}',
   'Me ajude a escrever para {p}: o assunto é {r}', 'Faça um recado dirigido a {p} sobre {r}',
   'Como posso escrever a {p} para conversar sobre {r}?', 'Prepare um texto pessoal para {p} a respeito de {r}'],
  ['Pode redigir um recado para {p} com o assunto {r}?', 'Queria dizer a {p} algo sobre {r}; escreva a mensagem',
   'Transforme {r} numa mensagem que eu possa mandar a {p}']),
 'dialogo': (
  ['Escreva um diálogo entre {a} e {b}', 'Crie uma conversa fictícia com {a} e {b}',
   'Imagine duas falas para {a} e {b}', 'Faça uma cena de diálogo envolvendo {a} e {b}',
   'Quero uma troca de falas entre {a} e {b}', 'Conte uma conversa inventada sobre {a} e {b}'],
  ['Pode inventar um diálogo que reúna {a} e {b}?', 'Mostre {a} e {b} conversando numa cena',
   'Queria ler uma conversa imaginária com {a} e {b}']),
 'continuacao': (
  ['Continue a história a partir desse ponto', 'Conte o que aconteceu depois', 'Prossiga com essa cena',
   'Quero a continuação desse conto', 'Faça a história seguir adiante', 'Escreva mais uma parte dessa narrativa'],
  ['O que aconteceu em seguida nessa história?', 'Pode continuar de onde o conto parou?', 'Como a cena segue depois disso?']),
 'resumo': (
  ['Resuma o que eu contei', 'Faça um resumo da minha situação', 'Junte os pontos do meu relato',
   'O que eu disse em poucas palavras?', 'Retome de forma curta o que relatei', 'Organize o que eu trouxe num resumo'],
  ['Pode reunir o essencial da situação que descrevi?', 'Queria ver um resumo das coisas que falei', 'Relembre brevemente meu relato']),
 'reformulacao': (
  ['Reescreva meu relato de forma mais clara', 'Reformule o que eu disse', 'Diga minha situação de outro jeito',
   'Me ajude a apresentar isso com outras palavras', 'Organize melhor a forma de contar meu relato', 'Deixe mais direta a apresentação da minha situação'],
  ['Como posso colocar em palavras a situação que trouxe?', 'Pode mudar a forma de apresentar meu relato?', 'Queria uma versão mais organizada do que falei']),
 'exploracao': (
  ['Me faça uma pergunta sobre isso', 'Ajude-me a explorar essa situação', 'Quero pensar melhor no que contei',
   'Que pergunta ajudaria a entender meu relato?', 'Puxe a conversa sobre o que eu trouxe', 'Vamos conversar mais sobre essa dificuldade'],
  ['Que parte da situação vale investigar comigo?', 'Pode aprofundar a conversa a partir do meu relato?', 'Queria continuar pensando sobre isso com você']),
 'plano': (
  ['Organize um plano para meu objetivo', 'Me dê próximos passos respeitando meu limite', 'Como posso começar o que quero fazer?',
   'Faça uma organização prática do meu objetivo', 'Quero dividir meu objetivo em etapas', 'Ajude a planejar um primeiro teste possível'],
  ['Como organizo um começo para o que pretendo?', 'Sugira etapas que caibam na minha restrição', 'Pode propor uma sequência para eu tentar?']),
 'reflexao': (
  ['Essa conclusão decorre dessa premissa?', 'Me ajude a refletir sobre esse raciocínio', 'Como avaliar essa conclusão?',
   'O que falta para essa premissa sustentar a conclusão?', 'Quero examinar o argumento que formulei', 'Separe minha premissa da conclusão'],
  ['O que precisaria verificar para aceitar essa conclusão?', 'Pode analisar a ligação entre essas duas afirmações?', 'Queria pensar melhor se meu argumento se sustenta']),
})

DESTINATARIOS = {'treino': ['Lia', 'Caio', 'Rui', 'Bia', 'Davi', 'Nina', 'Ivo', 'Eva', 'Luca', 'Joana', 'Leo', 'Mara'],
                'validacao': ['Elisa', 'Tomás', 'Yara', 'Noemi']}
SITUACOES = {
 'treino': [
  ('Eu gostei da ideia, mas não sei por onde começar', 'Quero criar um projeto pequeno', 'Tenho quinze minutos à noite', 'Já tentei juntar todas as tarefas de uma vez', 'animado e confuso'),
  ('Comecei uma história, mas fiquei preso no meio', 'Quero terminar minha primeira história', 'Só posso escrever no fim de semana', 'O começo já está pronto', 'inseguro'),
  ('Eu queria ajudar, mas minha mensagem ficou confusa', 'Quero conversar melhor com uma pessoa próxima', 'Prefiro uma mensagem curta', 'Ainda não mandei a mensagem', 'preocupado'),
  ('Fiquei cansado depois de tentar tudo de uma vez', 'Quero organizar meu próximo passo', 'Preciso de uma tarefa que caiba em dez minutos', 'Ontem tentei várias coisas ao mesmo tempo', 'cansado'),
  ('Gostei da conversa, mas um detalhe me incomodou', 'Quero explicar com clareza o que me incomodou', 'Não quero decidir tudo agora', 'O detalhe apareceu perto do final', 'dividido'),
  ('Eu mudei de ideia durante o projeto', 'Quero testar uma possibilidade diferente', 'Só tenho os materiais que já separei', 'A primeira ideia parecia grande demais', 'curioso'),
  ('Fiz uma tentativa e o resultado não foi o esperado', 'Quero entender o que posso ajustar', 'Quero testar uma mudança de cada vez', 'Consegui concluir só a primeira parte', 'frustrado'),
  ('Eu tenho duas ideias e estou indeciso', 'Quero comparar opções sem abandonar meu objetivo', 'Não posso dedicar o dia inteiro', 'Uma das ideias já tem um começo', 'indeciso'),
  ('Queria conversar sobre uma decisão pequena', 'Quero escolher um começo possível', 'Preciso de algo simples para hoje', 'Ainda não escolhi um critério', 'apreensivo'),
  ('Minha primeira versão não ficou clara', 'Quero apresentar minha ideia de forma organizada', 'Tenho pouco espaço para explicar', 'A versão anterior misturava vários assuntos', 'confuso'),
  ('Eu avancei um pouco e parei numa dificuldade', 'Quero retomar meu projeto aos poucos', 'Tenho vinte minutos antes de dormir', 'A etapa anterior funcionou', 'esperançoso'),
  ('Eu quero tentar de novo, mas mudar a abordagem', 'Quero observar um resultado pequeno', 'Não quero repetir a mesma tentativa', 'A abordagem anterior não ajudou', 'desanimado'),
 ],
 'validacao': [
  ('Estou planejando algo e perdi a ordem das etapas', 'Quero reorganizar um pequeno projeto', 'Tenho apenas um intervalo curto', 'Já concluí uma parte antes de parar', 'desorientado'),
  ('Eu gostei do começo, mas esperava outro caminho', 'Quero experimentar outra possibilidade', 'Prefiro testar sem gastar dinheiro', 'A tentativa anterior ficou pela metade', 'insatisfeito'),
  ('Quero escrever para alguém e não encontro um começo', 'Quero apresentar meu pedido com clareza', 'A mensagem precisa caber num parágrafo', 'Já separei os pontos que quero contar', 'hesitante'),
  ('Comecei a organizar as ideias e apareceu uma dúvida', 'Quero verificar um detalhe antes de seguir', 'Só consigo revisar uma etapa por dia', 'Já tenho uma primeira versão pronta', 'atento'),
 ],
}


def resposta(acao, estilo, variante, slots, combinacao=0):
    i, j = variante % 4, variante // 4
    if acao in ('historia', 'poema', 'final', 'escuta', 'alternativa', 'ajuste', 'apoio', 'ideia'):
        base = _RESPOSTA_V1(acao, estilo, i, slots, combinacao)
        if not j:
            return base
        if acao == 'historia':
            adicionais = ['Uma marca no chão indicou uma passagem nova.', 'A primeira escolha abriu espaço para outra pergunta.',
                          'Um encontro mudou o rumo da busca.', 'Uma lembrança ajudou a perceber o que faltava.']
            partes = base.rsplit('. ', 1)
            return partes[0] + '. ' + adicionais[combinacao%4] + ' ' + partes[1]
        if acao == 'poema':
            começos = ['No espaço entre @tema1 e a lembrança,', 'De @tema1 nasce uma pergunta,',
                       'O caminho de @tema1 guarda um nome,', '@tema1 desenha uma passagem,']
            segundo = '@tema2' if slots.get('tema2') else 'uma nova possibilidade'
            linhas = [começos[i], 'e '+segundo+' aprende a ouvir.',
                      ['um instante encontra outro instante,', 'a palavra atravessa o silêncio,', 'uma curva revela o começo,', 'a distância procura um abrigo,'][combinacao%4],
                      ['há outro jeito de seguir.', 'sem decidir aonde ir.', 'ainda existe o que descobrir.', 'e um pequeno lugar para existir.'][i]]
            return '\n'.join(linhas)
        objetivo = '@objetivo' if slots.get('objetivo') else '@relato'
        limite = ' O limite que você trouxe é “@restricao”.' if slots.get('restricao') else ''
        extras = {
         'escuta': [
          'Estou acompanhando “@relato”. Não quero reduzir isso a uma palavra só. Podemos olhar primeiro para o ponto que você considera mais importante.',
          'O ponto que você trouxe é “@relato”. Minha leitura começa pelo que você declarou. Como você gostaria de continuar essa conversa?',
          'Entendi que “@relato” é o assunto que precisa de atenção. Se minha leitura não combinar com o que quis dizer, podemos ajustar juntos.',
          'Você colocou em palavras “@relato”. Posso acompanhar esse ponto com você e perguntar antes de supor uma explicação. O que falta compreender melhor?',
         ],
         'alternativa': [
          'Outra maneira de trabalhar com “'+objetivo+'” é escolher um resultado pequeno e observável.'+limite+' Depois compare o que esperava com o que aconteceu.',
          'Para “'+objetivo+'”, você pode experimentar uma ordem diferente.'+limite+' Separe o que depende de você e escolha só uma ação para começar.',
          'Uma possibilidade para “'+objetivo+'” é criar duas versões pequenas e comparar.'+limite+' Use um critério que combine com o que você quer alcançar.',
          'Podemos tratar “'+objetivo+'” como uma tentativa aberta.'+limite+' Escolha o que manter, mude uma parte e observe antes de decidir o próximo passo.',
         ],
         'ajuste': [
          'Vou mudar a forma de acompanhar “@relato”. Em vez de insistir no mesmo caminho, podemos revisar o objetivo e escolher uma ação concreta.',
          'Você sinalizou que minha resposta não serviu. Retomo “@relato” com outra abordagem: separar o que já tentou do que ainda pode testar.',
          'Entendi a necessidade de ajuste. Partindo de “@relato”, podemos trocar uma pergunta repetida por uma comparação entre duas possibilidades pequenas.',
          'Quero corrigir a abordagem da conversa sobre “@relato”. Vamos usar o que você já contou para escolher um começo, sem exigir que repita tudo.',
         ],
         'apoio': [
          'Você contou “@relato”. Esse resultado merece atenção, mas não resume toda a sua capacidade. Um próximo teste pode verificar uma parte menor do problema.',
          'A partir de “@relato”, podemos analisar uma tentativa específica. Isso ajuda mais do que tratar um resultado isolado como uma definição de quem você é.',
          'Não precisamos transformar “@relato” numa sentença sobre sua capacidade. Vale verificar o que estava sob seu controle e o que poderia ser ajustado.',
          'Você trouxe “@relato”. Podemos reconhecer a dificuldade e, ao mesmo tempo, deixar aberta a possibilidade de aprender com uma tentativa diferente.',
         ],
         'ideia': [
          'Imagine um projeto em que @tema1 guarda uma pergunta e @tema2 oferece uma pista. A regra é que cada parte precisa mudar antes de encontrar uma resposta.',
          'Uma ideia inventada é criar um encontro entre @tema1 e @tema2 em que a solução habitual não funciona. Escolha uma regra pequena para tornar a combinação surpreendente.',
          'Podemos usar @tema1 como ponto de partida e @tema2 como uma mudança de direção. Crie uma primeira versão curta e observe qual detalhe desperta mais curiosidade.',
          'Uma proposta é fazer @tema1 e @tema2 compartilharem um desafio. Cada parte só pode ajudar de uma maneira, e a combinação precisa encontrar um terceiro caminho.',
         ],
        }
        if acao == 'final':
            sujeito = '@tema1 e @tema2' if slots.get('tema2') else '@tema1'
            verbos = ('chegaram', 'perceberam', 'deixaram', 'escolheram') if slots.get('tema2') else ('chegou', 'percebeu', 'deixou', 'escolheu')
            encontro = 'encontraram' if slots.get('tema2') else 'encontrou'
            return [sujeito+' '+verbos[0]+' ao fim do caminho e '+encontro+' uma porta aberta. A descoberta não encerrou a viagem: deu um novo sentido ao começo.',
                    sujeito+' '+verbos[1]+' que a última pista estava numa escolha pequena. Depois disso, o lugar conhecido pareceu diferente, como se a história tivesse recomeçado.',
                    sujeito+' '+verbos[2]+' a resposta guardada para outro dia. O fim trouxe uma despedida tranquila e a promessa de procurar uma nova passagem.',
                    sujeito+' '+verbos[3]+' continuar a busca sem resolver tudo naquela noite. A primeira luz abriu outra possibilidade, e o conto terminou com uma pergunta.'][i]
        return extras[acao][i]
    if acao == 'mensagem':
        saudacao = 'Oi, @destinatario.' if slots.get('destinatario') else 'Oi.'
        if estilo == 'formal':
            saudacao = 'Olá, @destinatario.' if slots.get('destinatario') else 'Olá.'
        if estilo == 'carinhoso':
            saudacao += ' Queria te escrever com carinho.'
        textos = [
         'Queria conversar sobre “@relato”. Para mim, esse assunto merece uma atenção tranquila. Quando puder, gostaria de saber como você vê essa situação.',
         'Estou escrevendo porque quero falar de “@relato”. Ainda estou organizando o que penso e prefiro começar com uma conversa simples. Você pode me ouvir sobre isso?',
         'Gostaria de compartilhar “@relato”. Quero apresentar esse ponto com clareza e entender também o seu lado. Podemos escolher um momento para conversar?',
         'Quero retomar o assunto “@relato”. Não preciso resolver tudo nesta mensagem, mas gostaria de abrir espaço para uma conversa. Quando for possível, me diga o que pensa.',
         'Pensei em te escrever sobre “@relato”. Esse é o ponto que quero trazer agora. Gostaria de conversar aos poucos e ouvir o que você tem a dizer.',
         'Minha mensagem é sobre “@relato”. Quero que a conversa comece com calma e tenha espaço para nós dois. Podemos retomar esse assunto quando você puder?',
         'Quero colocar em palavras “@relato”. Estou tentando falar de um jeito simples e aberto. Se alguma parte não ficar clara, podemos ajustar na conversa.',
         'Escrevo para conversar a respeito de “@relato”. Gostaria de trocar ideias sem apressar uma decisão. Podemos começar por esse ponto e ouvir um ao outro.',
        ]
        if estilo == 'simples':
            curtas = [
             'Queria conversar sobre “@relato”. Podemos falar disso com calma?',
             'Meu assunto é “@relato”. Quando puder, gostaria de te ouvir.',
             'Quero compartilhar “@relato”. Podemos começar uma conversa por esse ponto?',
             'Gostaria de falar de “@relato”. Me diga quando podemos conversar.',
             'Escrevo sobre “@relato”. Gostaria de saber o que você pensa.',
             'Quero retomar “@relato”. Podemos conversar sem apressar uma decisão?',
             'Queria colocar em palavras “@relato”. Posso te contar melhor?',
             'O ponto que quero trazer é “@relato”. Podemos falar aos poucos?',
            ]
            return saudacao+' '+curtas[variante%8]
        return saudacao+' '+textos[variante%8]
    if acao == 'dialogo':
        outro = '@tema2' if slots.get('tema2') else 'Uma voz'
        falas = [
         ('Encontrei uma pista no caminho.', 'Então vamos olhar antes de seguir.'),
         ('Eu pensava que a porta estava fechada.', 'Talvez a pergunta tenha mudado.'),
         ('O caminho parece diferente hoje.', 'Podemos descobrir uma curva de cada vez.'),
         ('Guardei uma pergunta para esse encontro.', 'Estou aqui para ouvir o começo.'),
         ('A última tentativa não levou aonde eu esperava.', 'Vamos experimentar um caminho menor.'),
         ('Achei uma marca onde antes não havia nada.', 'Pode ser o começo de outra descoberta.'),
         ('Precisamos decidir o que levar daqui.', 'Eu levaria a pergunta que ainda está aberta.'),
         ('Não sei como terminar esta conversa.', 'Talvez ela possa virar o começo de outra cena.'),
        ]
        primeira, segunda = falas[variante%8]
        fim = ['A conversa abriu uma passagem inesperada.', 'Depois das falas, surgiu uma nova escolha.',
               'Os dois deixaram uma pergunta para o próximo encontro.', 'A cena terminou com uma pequena descoberta.'][combinacao%4]
        return '@tema1: '+primeira+'\n'+outro+': '+segunda+'\n'+fim
    if acao == 'continuacao':
        ponto = 'Depois da cena “@detalhe”, ' if slots.get('detalhe') else 'Na parte seguinte, '
        segundo = ' @tema2 apareceu com uma pista inesperada.' if slots.get('tema2') else ' Uma pista diferente surgiu no caminho.'
        passos = ['percebeu uma marca que não estava ali antes', 'decidiu procurar a origem de um som distante',
                  'encontrou uma passagem atrás da última curva', 'guardou a pergunta e seguiu por outro caminho',
                  'voltou até o ponto em que tudo tinha mudado', 'encontrou um sinal perto da porta esquecida',
                  'recebeu uma pista que parecia incompleta', 'notou que a escolha anterior tinha aberto outra passagem']
        fins = ['A busca continuou, agora com uma pergunta diferente.', ('Antes de escolher, observaram o que havia mudado.' if slots.get('tema2') else 'Antes de escolher, observou o que havia mudado.'),
                'O próximo passo revelou uma surpresa pequena.', 'A continuação deixou aberta uma nova possibilidade.']
        return ponto+'@tema1 '+passos[variante%8]+'.'+segundo+' '+fins[combinacao%4]
    if acao in ('resumo', 'reformulacao'):
        detalhe = ' Você também acrescentou “@detalhe”.' if slots.get('detalhe') else ''
        objetivo = ' Seu objetivo declarado é “@objetivo”.' if slots.get('objetivo') else ''
        limite = ' O limite que mencionou é “@restricao”.' if slots.get('restricao') else ''
        entradas = {
         'resumo': ['O resumo do seu relato é: “@relato”.', 'O ponto principal que você contou foi “@relato”.',
                    'Retomando o que declarou: “@relato”.', 'Você trouxe como situação “@relato”.',
                    'Em poucas palavras, seu relato começa com “@relato”.', 'O assunto que você apresentou é “@relato”.',
                    'Os pontos do relato partem de “@relato”.', 'Reunindo o que contou: “@relato”.'],
         'reformulacao': ['Uma apresentação mais organizada começa assim: “@relato”.', 'Podemos colocar seu relato desta forma: “@relato”.',
                         'Para apresentar a situação com clareza: “@relato”.', 'Uma forma direta de abrir o relato é: “@relato”.',
                         'Você pode começar a explicar a situação com “@relato”.', 'Para separar as partes, comece pelo ponto “@relato”.',
                         'Uma maneira de organizar a apresentação é partir de “@relato”.', 'Para retomar a ideia de modo simples: “@relato”.'],
        }
        return entradas[acao][variante%8]+detalhe+objetivo+limite+' Esses são os pontos que você declarou, sem acrescentar detalhes.'
    if acao == 'exploracao':
        detalhe = ' Você também trouxe “@detalhe”.' if slots.get('detalhe') else ''
        sentimento = ' Você descreveu como se sente: “@sentimento”.' if slots.get('sentimento') else ''
        perguntas = ['O que você esperava que acontecesse nessa situação?', 'Qual parte você gostaria de compreender melhor primeiro?',
                     'O que mudou entre o que esperava e o que aconteceu?', 'Que detalhe ajudaria a escolher um próximo passo?',
                     'Qual ponto você considera mais importante manter?', 'O que já tentou e gostaria de fazer de outro jeito?',
                     'Como você perceberia que a conversa está ajudando?', 'O que seria útil explorar agora, antes de decidir?']
        return 'Você contou “@relato”.'+detalhe+sentimento+' '+perguntas[variante%8]
    if acao == 'plano':
        limite = ' O limite é “@restricao”.' if slots.get('restricao') else ''
        passos = [
         'Primeiro, escolha uma parte pequena. Depois, faça uma tentativa que caiba no limite. Por fim, observe o resultado antes de escolher a próxima etapa.',
         'Comece definindo o que seria um primeiro resultado observável. Faça só uma tentativa. Depois compare o resultado com o que esperava.',
         'Separe o que já está pronto do que falta. Escolha uma tarefa curta para o próximo passo. Ao terminar, anote o que funcionou e o que precisa mudar.',
         'Divida a ideia em começo, tentativa e revisão. Escolha um começo simples. Depois use a revisão para decidir como continuar.',
         'Escolha uma ação possível hoje. Defina onde ela começa e termina. Depois verifique se respeitou sua prioridade e ajuste só uma parte.',
         'Organize duas etapas pequenas: preparar e experimentar. Reserve uma pausa para observar o resultado. Só então escolha a etapa seguinte.',
         'Comece por uma parte fácil de verificar. Teste essa parte sem tentar resolver tudo. Use o que observar para reorganizar o restante.',
         'Defina um teste pequeno e um critério de resultado. Faça o teste dentro do limite. Depois decida se mantém a abordagem ou muda uma etapa.',
        ]
        return 'Seu objetivo é “@objetivo”.'+limite+' '+passos[variante%8]
    if acao == 'reflexao':
        entradas = ['Vamos separar as duas afirmações.', 'Podemos examinar a ligação entre essas ideias.',
                    'Vale distinguir o ponto de partida da conclusão.', 'O argumento pode ser analisado em partes.',
                    'Para refletir, vamos começar pelo que foi declarado.', 'Podemos verificar o raciocínio sem aceitar tudo de uma vez.',
                    'A relação entre as afirmações precisa de uma verificação.', 'Vamos olhar para a passagem de uma afirmação à outra.']
        fins = ['A premissa sozinha não demonstra automaticamente a conclusão. O que precisaria ser verificado para ligar as duas?',
                'Precisamos ver se a conclusão realmente segue da premissa e se há alguma hipótese faltando. Você tem um exemplo que ajude a verificar?',
                'Essas afirmações têm papéis diferentes no argumento. Qual informação sustentaria a passagem de uma para a outra?',
                'Antes de aceitar a conclusão, podemos procurar uma condição ou um exemplo que confirme ou limite essa ligação. O que seria possível testar?']
        return entradas[variante%8]+' A premissa é “@premissa”. A conclusão é “@conclusao”. '+fins[combinacao%4]
    raise ValueError('Ação sem resposta autoral')


def _estilos(acao):
    if acao in ('historia', 'poema'):
        return ESTILOS
    if acao == 'mensagem':
        return ('neutro', 'carinhoso', 'formal', 'simples')
    if acao == 'dialogo':
        return ('neutro', 'divertido')
    if acao == 'continuacao':
        return ('neutro', 'misterioso')
    if acao == 'reformulacao':
        return ('neutro', 'simples')
    return ('neutro',)


def _contextos(acao, a, b, pessoa, situacao, mensagem, estilo, variante, combinacao):
    relato, objetivo, restricao, detalhe, sentimento = situacao
    temas = {'tema1': a, 'tema2': b}
    hist = []
    if acao in ('historia', 'poema', 'dialogo', 'ideia'):
        perfis = [temas, {'tema1': a}] if acao != 'ideia' else [temas]
        hist = ['Quero criar um projeto', 'Quero juntar '+a+' com '+b] if acao == 'ideia' else []
    elif acao == 'final':
        perfis = [temas, {'tema1': a}]
        hist = ['Invente uma história sobre '+a+' e '+b]
    elif acao == 'continuacao':
        perfis = [dict(temas, detalhe='Uma porta se abriu perto do final'), temas,
                  {'tema1': a, 'detalhe': 'A descoberta abriu uma nova pergunta'}]
        hist = ['Invente uma história sobre '+a+' e '+b, 'Agora dê outro final']
    elif acao == 'alternativa':
        perfis = [{'relato': relato, 'objetivo': objetivo, 'restricao': restricao},
                  {'relato': relato, 'objetivo': objetivo}, {'relato': relato, 'restricao': restricao}, {'relato': relato}]
        hist = ['Quero '+objetivo, restricao]
    elif acao == 'mensagem':
        perfis = [{'relato': 'a situação que envolve '+a, 'destinatario': pessoa}, {'relato': 'a situação que envolve '+a}]
        hist = [relato]
    elif acao in ('resumo', 'reformulacao'):
        perfis = [{'relato': relato}, {'relato': relato, 'detalhe': detalhe},
                  {'relato': relato, 'detalhe': detalhe, 'objetivo': objetivo, 'restricao': restricao}]
        hist = [relato, detalhe, 'Quero '+objetivo]
    elif acao == 'exploracao':
        perfis = [{'relato': relato}, {'relato': relato, 'detalhe': detalhe, 'sentimento': sentimento}]
        hist = [relato, detalhe]
    elif acao == 'plano':
        perfis = [{'objetivo': objetivo}, {'objetivo': objetivo, 'restricao': restricao}]
        hist = ['Quero '+objetivo, restricao]
    elif acao == 'reflexao':
        perfis = [{'premissa': 'uma tentativa não funcionou', 'conclusao': 'nenhuma tentativa pode funcionar'},
                  {'premissa': 'uma parte da ideia foi testada', 'conclusao': 'a ideia inteira está comprovada'}]
        hist = ['Quero pensar sobre uma conclusão', 'Se uma parte falhou, a ideia toda falhou?']
    else:
        perfis = [{'relato': relato}]
        hist = ['Quero conversar sobre uma situação', relato]
    for slots in perfis:
        anterior = ''
        if acao in ('continuacao', 'final'):
            anterior = resposta('historia', estilo, variante, {k:v for k,v in slots.items() if k in ('tema1','tema2')}, combinacao)
        elif acao in ('ajuste', 'alternativa'):
            anterior = resposta('escuta', 'neutro', (variante+1)%VARIANTES, {'relato': relato}, combinacao)
        elif acao == 'reformulacao':
            anterior = resposta('resumo', 'neutro', variante, slots, combinacao)
        ctx = {'acao': acao, 'estilo': estilo, 'variante': variante, 'slots': slots,
               'mensagem': mensagem, 'historico': hist[-3:], 'resposta_anterior': anterior}
        yield ctx


def gerar():
    exemplos = []
    for split, temas in TEMAS.items():
        for acao, (pedidos_treino, pedidos_validacao) in PEDIDOS.items():
            padroes = pedidos_treino if split == 'treino' else pedidos_validacao
            for familia, padrao in enumerate(padroes):
                for assunto, (a,b) in enumerate(temas):
                    situacao = SITUACOES[split][assunto]
                    pessoa = DESTINATARIOS[split][assunto]
                    for estilo in _estilos(acao):
                        # Duas variantes por combinação; ao longo das famílias
                        # cada assunto ensina todas as oito variantes.
                        for k in range(2):
                            variante = (2*familia+assunto+k)%VARIANTES
                            combinacao = ((familia*len(temas)+assunto+(37 if split=='validacao' else 0))*7)%64
                            mensagem = padrao.format(a=a,b=b,p=pessoa,r='a situação que envolve '+a)
                            ident = '{}:{}:{}:{}:{}:{}'.format(split,acao,familia,assunto,estilo,variante)
                            for ctx in _contextos(acao,a,b,pessoa,situacao,mensagem,estilo,variante,combinacao):
                                r = resposta(acao,estilo,variante,ctx['slots'],combinacao)
                                if not all('@'+s in r for s in slots_requeridos(acao,ctx['slots'])):
                                    raise ValueError('Currículo perdeu um argumento: '+acao)
                                exemplos.append({'split': split, 'familia': split+':'+acao+':'+str(familia),
                                                 'tema': a+' | '+b, 'dialogo': ident,
                                                 'contexto': ctx, 'resposta': r})
        # Episódios autorais com estados e saídas anteriores efetivos.
        for assunto, (a,b) in enumerate(temas):
            for variante in range(VARIANTES):
                id_dialogo = '{}:episodio:{}:{}'.format(split,assunto,variante)
                historia_ctx = {'acao':'historia','estilo':'neutro','variante':variante,
                                'slots':{'tema1':a,'tema2':b},'mensagem':(('Invente uma história sobre ' if split=='treino' else 'Imagine uma narrativa breve que junte ')+a+' e '+b),'historico':[]}
                roteiro = [historia_ctx]
                anterior = resposta('historia','neutro',variante,historia_ctx['slots'],assunto)
                detalhe = anterior.rsplit('. ',1)[-1]
                roteiro.append({'acao':'continuacao','estilo':'neutro','variante':variante,
                                'slots':{'tema1':a,'tema2':b,'detalhe':detalhe},
                                'mensagem':('Continue a história a partir desse ponto' if split=='treino' else 'Siga adiante a partir da última cena inventada'),'historico':[historia_ctx['mensagem']],
                                'resposta_anterior':anterior})
                continua = resposta('continuacao','neutro',variante,roteiro[-1]['slots'],assunto)
                roteiro.append({'acao':'final','estilo':'neutro','variante':variante,
                                'slots':historia_ctx['slots'],'mensagem':('Agora dê outro final' if split=='treino' else 'Escreva um desfecho diferente para essa narrativa'),
                                'historico':[historia_ctx['mensagem'],roteiro[-1]['mensagem']], 'resposta_anterior':continua})
                for ctx in roteiro:
                    exemplos.append({'split':split,'familia':split+':episodio-criacao','tema':a+' | '+b,
                                     'dialogo':id_dialogo,'contexto':ctx,
                                     'resposta':resposta(ctx['acao'],ctx['estilo'],variante,ctx['slots'],assunto)})
    return {'versao':1,'autoria':'Currículo sintético autoral v2: exemplos de escrita e conversa contextual, sem corpus externo ou saídas de modelos.',
            'limite':'Famílias de pedidos, temas e grupos de diálogo separados entre treino e validação. As respostas autorais compartilham estruturas: esta validação é interna e não mede conversa irrestrita ou inteligência geral.',
            'exemplos':exemplos}


if __name__ == '__main__':
    dados = gerar()
    destino = RAIZ/'curriculo_geracao.json'
    cabecalho = json.dumps({k:v for k,v in dados.items() if k!='exemplos'},ensure_ascii=False,indent=2)
    linhas = [json.dumps(c,ensure_ascii=False,separators=(',',':')) for c in dados['exemplos']]
    conteudo = cabecalho[:-2]+',\n  "exemplos": [\n'+',\n'.join('    '+l for l in linhas)+'\n  ]\n}\n'
    temporario = destino.with_suffix('.tmp')
    temporario.write_text(conteudo,encoding='utf-8')
    temporario.replace(destino)
    for split in ('treino','validacao'):
        casos = [c for c in dados['exemplos'] if c['split']==split]
        print(split,len(casos),'exemplos',len({c['dialogo'] for c in casos}),'contextos de diálogo',
              len({c['resposta'] for c in casos}),'respostas deslexicalizadas')
