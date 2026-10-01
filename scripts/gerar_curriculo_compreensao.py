"""Currículo autoral de compreensão e diálogo contextual, sem corpus externo.

Cada pedido e resposta foi escrito para ensinar atos, argumentos e contexto.
Os assuntos, pessoas e famílias de pedido da validação não são usados no
treino. As respostas têm construção composicional compartilhada: esta é
validação sintética interna, não uma medida de inteligência geral.

Os offsets são Unicode, com fim exclusivo; não são índices de bytes.
O servidor não importa este gerador nem procura respostas neste arquivo.
"""
import hashlib
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ATOS = ["saudacao", "identidade", "compreensao", "limites", "abrir",
        "relato", "desabafo", "objetivo", "preferencia", "conselho",
        "opiniao", "explorar", "filosofar", "escuta", "reparo", "correcao",
        "elaborar", "memoria", "retomar", "mudar_assunto", "encerrar",
        "consulta", "escrita"]
PAPEIS = ["evento", "sentimento", "tema", "objetivo", "restricao",
          "interlocutor", "modo", "modo_recusado", "referencia"]


def linhas(texto):
    return [linha.strip() for linha in texto.strip().splitlines() if linha.strip()]


# Cada linha é uma família gramatical autoral; não vem de sondas ou do bot.
PEDIDOS = {
"saudacao": ("""
Oi!
Olá, tudo bem?
E aí, bora conversar?
Bom dia, Crivo
Boa noite pra você
Opa, cheguei
Ei, tem alguém por aí?
Olá de novo
Tô de volta, oi
Oi, como vai?
Fala comigo, bom dia
Boa tarde!
Oi, tudo certo por aí?
Oii, passei pra conversar
Eae, tá por aqui?
Saudações, vamos falar?
Cheguei, tudo bom?
Ei Crivo, oi
""", """
Alô, posso entrar no papo?
Um olá pra começar
Salve, apareci por aqui
Opa, boa tarde pra nós
Oiê, cheguei de novo
Como vai esse nosso papo?
"""),
"identidade": ("""
Você é uma IA?
Vc é inteligência artificial?
Quem é você?
Você é uma pessoa ou um programa?
Tu és um sistema de computador?
Como posso te chamar?
Você é o Crivo mesmo?
Me fala o que você é
O que é você, afinal?
Tem uma pessoa digitando suas respostas?
Você foi criado como uma inteligência artificial?
Então estou falando com um programa?
Você não é humano, né?
Seu nome é Crivo?
Você é um robô de conversa?
Queria saber quem está respondendo aqui
Tem alguém atrás desse chat ou é um sistema?
Você é uma IA feita neste projeto?
""", """
Com quem eu estou conversando neste chat?
É um software que está falando comigo?
Que tipo de assistente você é?
Você se apresenta como o quê?
Aqui responde uma máquina ou um ser humano?
Me apresenta quem você é antes do papo
"""),
"compreensao": ("""
Você me entende?
Vc tá entendendo o que eu quero dizer?
Consegue acompanhar minha conversa?
Você entendeu minha intenção?
Será que você entende as pessoas?
Você acompanha o sentido do que digo?
Está conseguindo seguir meu raciocínio?
Tu entende quando eu falo desse jeito?
Você percebe o que eu estou tentando dizer?
Me entendeu ou ficou confuso?
O que você entendeu do meu pedido?
Você sabe interpretar uma conversa?
Você entende a diferença entre ouvir e dar conselho?
Conseguiu acompanhar o que estou falando?
Você pega a ideia por trás das palavras?
Dá pra você entender minha mensagem mesmo abreviada?
Você entendeu que quero conversar?
Isso faz sentido pra você ou preciso explicar?
""", """
Você captou o que eu quis expressar?
Minha ideia chegou pra você?
Está claro para você o que eu procuro aqui?
Você consegue interpretar a intenção da minha fala?
O sentido dessa conversa está chegando aí?
Como você interpreta o que estou tentando comunicar?
"""),
"limites": ("""
Você tem pensamentos próprios?
Você sente alguma coisa?
Você é consciente?
O que você consegue fazer?
Você entende tudo que eu disser?
Você pode errar numa conversa?
Você aprende sozinho enquanto falamos?
Você tem um cérebro de verdade?
Quais são suas limitações?
Você sabe tudo?
Como você produz suas respostas?
Você tem sentimentos como uma pessoa?
Você consegue se lembrar para sempre?
Você foi treinado do zero?
Você usa uma IA de fora para responder?
Você muda seus pesos com cada mensagem?
Você pensa igual a um ser humano?
Pode me explicar o que ainda não consegue fazer?
""", """
Sua compreensão tem algum limite?
Você possui consciência de si mesmo?
O que o seu treinamento permite hoje?
O que significa dizer que você raciocina?
Você consegue evoluir sem um novo treinamento?
Até onde chegam as suas capacidades neste projeto?
"""),
"abrir": ("""
Quero conversar com você
Vamos bater papo?
Tô afim de trocar uma ideia
Podemos conversar sobre {tema}?
Não tenho uma pergunta, só quero falar
Queria companhia pra conversar
Posso te contar uma coisa?
Vem conversar um pouco comigo
Quero um papo sem objetivo específico
Vamos falar de qualquer coisa?
Tem espaço para eu falar sobre {tema}?
Não quero uma pesquisa, quero conversar
Bora trocar uma ideia sobre {tema}
Queria puxar assunto sobre {tema}
Topa falar comigo um pouco?
Hoje eu só queria um pouco de conversa
Tenho uma história pra te contar
Quero começar um papo sobre {tema}
""", """
Estou procurando um lugar pra conversar
Podemos ter um papo a respeito de {tema}?
Queria dividir umas coisas sem fazer uma pergunta
Você pode acompanhar uma conversa comigo?
Gostaria de abrir um assunto: {tema}
Tenho vontade de ficar conversando um pouco
"""),
"relato": ("""
{interlocutor} {evento} hoje
Aconteceu isto: {interlocutor} {evento}
Preciso contar que {interlocutor} {evento}
Você acredita? {interlocutor} {evento}
Hoje, {interlocutor} {evento}; fiquei sem reação
Eu estava com {interlocutor}, que {evento}
{interlocutor} {evento}, e era importante para mim
O que rolou foi que {interlocutor} {evento}
Ontem {interlocutor} {evento}; queria contar isso
Então, {interlocutor} {evento} e eu não soube o que dizer
Foi um dia estranho: {interlocutor} {evento}
Acabei de saber que {interlocutor} {evento}
Uma coisa me marcou: {interlocutor} {evento}
Estava indo bem, mas {interlocutor} {evento}
Não estou fazendo uma pergunta: {interlocutor} {evento}
Tem uma situação acontecendo: {interlocutor} {evento}
Quero te situar: {interlocutor} {evento}
Não sei explicar direito; {interlocutor} {evento}
""", """
Vou começar pelo ocorrido: {interlocutor} {evento}
O episódio de hoje foi que {interlocutor} {evento}
É sobre uma coisa que aconteceu com {interlocutor}: {evento}
Algo mudou meu dia: {interlocutor} {evento}
Pra você saber do contexto, {interlocutor} {evento}
Deixa eu descrever a situação: {interlocutor} {evento}
"""),
"desabafo": ("""
Eu me sinto {sentimento}
Tô {sentimento} com o que aconteceu
Fiquei {sentimento} depois que {interlocutor} {evento}
Hoje eu estou {sentimento}, de verdade
Quero desabafar: estou {sentimento}
Isso me deixou {sentimento}
{interlocutor} {evento} e eu tô {sentimento}
Não sei lidar com a sensação de estar {sentimento}
Me peguei {sentimento} por causa disso
Eu tento seguir, mas continuo {sentimento}
Não é uma dúvida técnica; me sinto {sentimento}
Eu estou estudando {tema}, mas me sinto {sentimento}
Não sei por que isso mexeu tanto comigo; tô {sentimento}
{interlocutor} disse "não" e eu fiquei {sentimento}
Estou {sentimento}, mesmo sabendo que posso tentar de novo
Não quero fingir que tá tudo bem, estou {sentimento}
Queria admitir que me sinto {sentimento}
Fiquei {sentimento}; você pode ficar nessa conversa comigo?
""", """
O sentimento que ficou foi {sentimento}
Aquilo me atingiu e me deixou {sentimento}
Estou com dificuldade de sair desse estado: {sentimento}
Tem sido pesado; ando {sentimento} com {tema}
Eu achei que ia passar, só que ainda estou {sentimento}
Depois desse episódio, acabei ficando {sentimento}
"""),
"objetivo": ("""
Quero {objetivo}
Minha vontade é {objetivo}
Estou tentando {objetivo}
Pretendo {objetivo}, mas {restricao}
Tenho uma meta: {objetivo}
Eu queria conseguir {objetivo}
Decidi que vou tentar {objetivo}
Ando pensando em {objetivo}
Queria falar sobre minha vontade de {objetivo}
O que eu busco é {objetivo}
Meu foco agora é {objetivo}
Não quero desistir de {objetivo}
Talvez eu tente {objetivo}, mesmo com o pouco tempo
Me interessa {objetivo}, só que {restricao}
Para mim seria importante {objetivo}
Tenho vontade de {objetivo}, sem pressa
Meu objetivo mudou: agora quero {objetivo}
Quero {objetivo}; ainda não estou pedindo um plano
""", """
O que estou buscando neste momento é {objetivo}
Minha intenção daqui para frente é {objetivo}
Eu gostaria de dar um jeito de {objetivo}
Estou considerando seriamente {objetivo}
Seria bom para mim conseguir {objetivo}
Meu desejo atual é {objetivo}, apesar de {restricao}
"""),
"preferencia": ("""
Eu gosto de {tema}
Curto conversar sobre {tema}
Prefiro {tema} a ficar falando de trabalho
Adoro {tema}
Não sou muito fã de {tema}
Ultimamente tenho curtido {tema}
Meu assunto preferido é {tema}
Gosto bastante de {tema}, e você?
Eu prefiro falar de {tema}
{tema} é uma coisa que eu curto
Tenho interesse por {tema}
Tô gostando cada vez mais de {tema}
Não gosto tanto de {tema} quanto antes
Se eu pudesse escolher, falaria sobre {tema}
Minha preferência agora é {tema}
Sempre achei {tema} interessante
Eu gosto de {tema}, mesmo sem saber muito
Não quero pesquisar; gosto de falar sobre {tema}
""", """
O assunto que mais me prende é {tema}
Ultimamente o que eu aprecio é {tema}
Tenho uma queda por conversas sobre {tema}
Entre vários temas, {tema} me atrai mais
Eu me interesso particularmente por {tema}
Meu gosto mudou e agora inclui {tema}
"""),
"conselho": ("""
O que eu poderia fazer nessa situação?
Me ajuda a pensar num jeito de {objetivo}
Qual seria um caminho para {objetivo}?
Você pode me dar um conselho?
Como eu lido com isso sem piorar as coisas?
Tenho que decidir o que fazer com {interlocutor}
Você sugeriria alguma coisa para {objetivo}?
Como posso tentar {objetivo} se {restricao}?
Queria uma sugestão que respeitasse meu tempo
Me dá uma ideia prática, mas sem decidir por mim
O que você faria para começar a {objetivo}?
Como eu converso com {interlocutor} sobre isso?
Preciso de uma possibilidade concreta
Quero pensar em uma ação, não só desabafar
Que alternativa você vê para o que eu contei?
Me ajuda a escolher um próximo passo
Pode comparar dois caminhos para {objetivo}?
Agora sim eu queria um conselho
""", """
Que atitude seria razoável nessa situação?
Pode me ajudar a encontrar uma saída para {objetivo}?
Que possibilidade cabe no limite de que {restricao}?
Como agir sem ignorar o que eu sinto?
Eu queria avaliar uma ação possível para {objetivo}
O que posso experimentar a partir desse ponto?
"""),
"opiniao": ("""
O que você acha disso?
Como você vê essa situação?
Você concorda com o que eu estou pensando?
Qual é sua opinião sobre {tema}?
Isso faz sentido para você?
Você acha que {interlocutor} fez isso de propósito?
Será que estou exagerando?
Como você interpreta o que aconteceu?
O que você pensa do que eu contei?
Você vê isso do mesmo jeito que eu?
Me dá uma perspectiva, não um plano
Seria justo eu pensar assim?
Você acha que estou cobrando demais?
Que outro ponto de vista existe nessa história?
Eu queria ouvir um contraponto
Você avaliaria isso de outro jeito?
Será que dá para olhar isso sem culpar ninguém?
Você acha que isso prova alguma coisa sobre mim?
""", """
Qual leitura você faria desse episódio?
Como isso parece a partir de outra perspectiva?
Dá para questionar a interpretação que fiz?
Você considera razoável o que estou sentindo?
Que conclusão você evitaria tirar tão cedo?
Como você pensaria a respeito disso?
"""),
"explorar": ("""
Quero entender melhor por que isso me incomodou
Me faz uma pergunta sobre o que contei
Vamos explorar o assunto de {tema}
O que falta eu olhar nessa situação?
Queria ir mais fundo nessa conversa
Pergunta alguma coisa que ajude a pensar
Me ajuda a entender o que eu estou sentindo
Quero refletir sobre minha reação a {interlocutor}
Podemos examinar o que está por trás disso?
Queria descobrir o que mais pesa para mim
Me ajuda a separar as partes dessa situação
Vamos olhar minha expectativa com mais calma
O que ainda não consideramos nessa conversa?
Quero pensar sobre isso antes de agir
Pode puxar esse papo um pouco mais?
Queria conversar mais sobre esse sentimento
Onde você acha que essa história ficou confusa?
Quero explorar, sem montar um plano agora
""", """
Queria aprofundar o que te contei
Pode abrir uma pergunta que vá além da primeira impressão?
Vamos investigar o que me afetou nisso
O que seria útil compreender antes de tomar uma atitude?
Quero olhar com mais cuidado para esse episódio
Ajuda a destrinchar o que estou tentando expressar
"""),
"filosofar": ("""
O que dá sentido a uma vida?
Por que a gente procura um propósito?
O que significa viver bem?
Qual é a diferença entre existir e viver?
Você acha que a vida tem um sentido único?
É possível ser livre e ter responsabilidades?
O que faz uma escolha ser realmente nossa?
Uma vida boa precisa ser produtiva?
Podemos encontrar sentido sem uma resposta definitiva?
Por que mudar assusta mesmo quando é necessário?
O que é felicidade para além de estar animado?
Somos só o resultado do que já aconteceu?
O que significa amadurecer?
Uma coisa só tem valor se dura para sempre?
Como pensar em quem eu sou sem me definir por um erro?
O que seria mais importante: pertencer ou ser livre?
Será que um propósito precisa ser grandioso?
Por que o tempo parece tão diferente em cada fase?
""", """
Como você pensaria sobre o sentido da existência?
É possível construir uma vida significativa sem certezas?
Quais perspectivas existem sobre viver uma vida boa?
O que distingue ter um objetivo de ter um propósito?
Será que a identidade de uma pessoa pode sempre mudar?
Como refletir sobre liberdade e responsabilidade juntas?
"""),
"escuta": ("""
Não quero {modo_recusado}, só quero {modo}
Só me ouve, por favor
Eu queria desabafar sem receber um plano
Sem {modo_recusado} agora; prefiro {modo}
Não estou pedindo uma solução
Queria apenas ser ouvido
Não quero que decida o que eu devo fazer
Agora eu preciso mais de escuta do que de instruções
Esquece os passos, deixa eu falar
Eu quero conversar, não {modo_recusado}
Pode só acompanhar o que estou dizendo?
Não faça perguntas por enquanto, só me deixe contar
Quero {modo}, mesmo sem chegar a uma solução
Você não precisa transformar isso numa tarefa
Não estou procurando {modo_recusado}
Sem tentar resolver tudo, pode ficar nesse assunto?
Não quero {modo_recusado}; deixa eu terminar
Me escuta sem pular para uma ação
""", """
O que preciso agora é de alguém acompanhando o relato
Eu prefiro espaço para falar, sem instruções
Pode deixar as recomendações de lado por um momento?
Antes de qualquer passo, gostaria de ser ouvido
Meu pedido é conversar sobre isso, sem buscar uma saída ainda
Gostaria de expressar o que sinto sem um interrogatório
"""),
"reparo": ("""
Não foi isso que eu quis dizer
Você está respondendo outra coisa
Não entendi essa resposta
Você está repetindo a mesma pergunta
Isso não me ajudou
Você não entendeu o ponto principal
Tá falando de um assunto diferente
Eu pedi uma conversa, mas você trouxe um roteiro
Isso soou muito automático
Você só repetiu o que eu falei
Sua resposta ignorou a parte importante
Pode explicar de um jeito mais claro?
Não quero a mesma resposta outra vez
Esse conselho não combina com o que eu contei
Você pulou uma parte da minha mensagem
Você presumiu uma coisa que eu não disse
Ficou confuso; tenta responder de outro jeito
Você tá me entendendo errado
""", """
A interpretação que fez não corresponde ao meu pedido
Sua resposta passou longe daquilo que eu queria expressar
Pode reformular com atenção ao que realmente contei?
Essa explicação ainda não ficou clara para mim
Você voltou ao mesmo ponto sem avançar o papo
Não reconheço meu pedido no que você respondeu
"""),
"correcao": ("""
Na verdade foi {interlocutor}, não a outra pessoa
Corrigindo: eu me sinto {sentimento}
Não é bem isso; {interlocutor} {evento}
Eu me expressei mal: queria {objetivo}
Meu limite mudou; agora {restricao}
Esqueci de dizer que {interlocutor} {evento}
Não tenho mais aquele tempo; {restricao}
Quero corrigir uma coisa sobre {tema}
Não estou triste, estou {sentimento}
O que aconteceu de verdade foi: {interlocutor} {evento}
Eu não disse que vou desistir; quero {objetivo}
Pode trocar a informação anterior por esta: {restricao}
Foi outra pessoa: {interlocutor}
Retificando o que falei, minha meta é {objetivo}
Não foi ontem; o importante é que {interlocutor} {evento}
Queria ajustar um detalhe: {restricao}
Você pode considerar esta correção: {interlocutor} {evento}
Pera, me expliquei errado; estou {sentimento}
""", """
Preciso retificar um detalhe do meu relato: {restricao}
Falei de forma imprecisa; a pessoa era {interlocutor}
Uma correção importante: o que quero é {objetivo}
O sentimento certo para descrever isso é {sentimento}
Atualiza o que contei: {interlocutor} {evento}
Eu havia informado diferente; o limite atual é {restricao}
"""),
"elaborar": ("""
Por quê?
Como assim?
Pode explicar melhor o que quis dizer?
O que te fez pensar nisso?
Por que você sugeriu esse caminho?
O que quer dizer com essa parte?
Explica mais um pouco
Dá um exemplo do que você está falando
Pode continuar esse raciocínio?
O que sustenta essa interpretação?
Como você chegou a esse ponto?
Me explica essa diferença com calma
O que isso tem a ver com o que eu contei?
Fala mais sobre essa ideia
Queria entender a razão da sua resposta
Pode desenvolver esse ponto?
Em que você se baseou nessa conversa?
Qual parte da minha fala levou a isso?
""", """
Detalha o raciocínio que acabou de apresentar
O que está por trás dessa sua leitura?
Como a conclusão se conecta ao meu relato?
Mostra com mais calma a razão dessa perspectiva
Queria compreender esse trecho da sua resposta
Desenvolve um pouco a justificativa que você deu
"""),
"memoria": ("""
O que eu te contei até agora?
Você lembra meu objetivo?
Qual era a dificuldade que mencionei?
Lembra o que aconteceu com {interlocutor}?
O que eu disse que estava sentindo?
Quanto tempo eu disse que tenho?
Qual assunto a gente estava discutindo?
O que você lembra desse nosso papo?
Eu já falei o que quero fazer?
Que limite eu tinha colocado?
Você lembra quem eu mencionei?
O que mudou na minha história?
Qual foi a última coisa que te contei?
Me mostra o que você guardou dessa conversa
Quais partes do meu relato você acompanhou?
Você consegue resumir o que falei antes?
Qual era a minha meta mesmo?
O que eu pedi para você evitar?
""", """
Recupera os pontos que eu trouxe neste papo
Você consegue lembrar a restrição que informei?
Retoma aquilo que declarei como objetivo
Quem aparecia na situação que descrevi?
Que sentimento eu tinha mencionado antes?
O que ficou registrado do que contei aqui?
"""),
"retomar": ("""
Voltando ao que aconteceu com {interlocutor}
Vamos retomar aquela conversa
Sobre {referencia}, ainda estou pensando
Quero voltar ao assunto de {tema}
E {referencia}, como a gente pode olhar?
Lembra daquele ponto? Quero continuar
Voltando ao meu objetivo de {objetivo}
A gente pode continuar de onde parou?
Sobre a situação que eu te contei
Ainda queria falar de {referencia}
Retoma a parte sobre {interlocutor}
Continuando meu relato, {interlocutor} {evento}
Vamos voltar para minha dificuldade
Quero seguir naquele assunto anterior
E quanto a {referencia} que mencionei?
Eu estava falando de {tema}, vamos voltar
Podemos retomar o ponto que ficou aberto?
Volta pro que eu contei antes
""", """
Gostaria de recuperar nosso assunto sobre {tema}
Reabrindo a conversa sobre {interlocutor}
Quero dar continuidade àquele relato anterior
Vamos voltar ao episódio que descrevi?
Eu queria seguir com a questão de {referencia}
Podemos continuar o papo a partir daquele ponto?
"""),
"mudar_assunto": ("""
Vamos mudar de assunto
Não quero falar mais sobre isso agora
Quero conversar sobre {tema} em vez disso
Esquece essa história, bora falar de outra coisa
Pode trocar de assunto comigo?
Quero deixar esse tema para depois
Agora eu preferia falar de {tema}
Vamos encerrar esse assunto e abrir outro
Cansei desse tema; mudamos?
Não quero continuar nessa situação
Podemos sair desse papo por enquanto?
Chega desse assunto, me acompanha em outro
Quero um assunto diferente
Prefiro trocar de tema antes de continuar
Hoje não vou falar mais disso
Vamos deixar {referencia} para outro momento
Gostaria de falar de outra coisa: {tema}
Mudando de assunto, você topa {tema}?
""", """
Prefiro suspender este tema e conversar sobre outra coisa
Podemos passar a um assunto diferente?
Quero encerrar esta parte do papo por enquanto
O próximo assunto que queria abrir é {tema}
Vamos guardar esse tema e falar de algo novo
Eu gostaria de deslocar a conversa para {tema}
"""),
"encerrar": ("""
Tchau, até depois
Vou sair agora
Obrigada pelo papo, até mais
Por hoje chega, vou dormir
Valeu, vou nessa
Até amanhã
Preciso ir, a gente continua depois
Boa noite, estou encerrando por aqui
Vou fechar o chat
Acabou por hoje, valeu
Depois eu volto a conversar
Foi bom conversar, tchau
Até logo, Crivo
Tenho que sair, obrigado
Vou parar a conversa agora
Nos falamos outra hora
Valeu por acompanhar, fui
Por enquanto é só, até mais
""", """
Vou me despedir por agora
Encerramos aqui e continuamos em outro momento
Obrigado por este tempo de conversa; preciso sair
Até uma próxima conversa
Vou descansar, deixamos o papo para depois
Preciso encerrar este chat neste momento
"""),
"consulta": ("""
Qual é a definição de {tema}?
O que significa tecnicamente {tema}?
Quais propriedades {tema} possui?
Você pode provar uma relação sobre {tema}?
Explique a sintaxe de {tema}
Escreva código para consultar {tema}
Que dados verificáveis você tem sobre {tema}?
Mostre um exemplo de código com {tema}
Faça uma consulta na sua base sobre {tema}
O que a base sabe sobre {tema}?
Quero informação factual sobre {tema}
Compare as propriedades de {tema}
Descreva as regras formais de {tema}
O que acontece ao executar esse código: {tema}?
Você tem alguma prova para essa afirmação?
Eu preciso da definição, não de conselho pessoal
Isso é uma pergunta técnica sobre {tema}
Quero uma resposta que possa ser verificada
""", """
Informe os fatos disponíveis acerca de {tema}
Pode consultar o conhecimento registrado sobre {tema}?
Qual informação confirmada existe a respeito de {tema}?
Preciso de uma explicação técnica do conceito {tema}
Há uma demonstração formal dessa relação?
Quero entender a operação técnica de {tema}
"""),
"escrita": ("""
Escreva uma mensagem para {interlocutor}
Invente uma história sobre {tema}
Faça um poema sobre {tema}
Quero um diálogo fictício com {interlocutor}
Crie uma cena curta envolvendo {tema}
Me ajuda a escrever um recado para {interlocutor}
Pode fazer uma versão mais curta daquele texto?
Dê outro final para a história
Quero um texto em tom carinhoso
Continua aquela história que escreveu
Troque o personagem por {interlocutor}
Escreva um bilhete sobre {tema}
Faça uma versão mais formal
Crie uma conversa imaginária sobre {tema}
Quero uma mensagem para dizer que estou {sentimento}
Reescreva meu texto com mais clareza
Me dá uma ideia de história usando {tema}
Escreva um email para {interlocutor} sobre {tema}
""", """
Componha uma pequena narrativa com {tema}
Queria um rascunho dirigido a {interlocutor}
Você pode elaborar alguns versos sobre {tema}?
Produza outra versão do texto que criamos
Gostaria de uma cena imaginária envolvendo {interlocutor}
Me ajuda a formular por escrito esse recado
"""),
}


# As respostas são alvos de aprendizagem da rede seq2seq. Há várias formas
# de responder ao mesmo ato, e condições adicionais abaixo usam a fala real.
RESPOSTAS = {
"saudacao": linhas("""
Oi! Como foi seu dia?
Olá! Quer me contar alguma coisa ou puxar um assunto?
Oi, estou por aqui. Como você está?
Vamos conversar. O que está passando pela sua cabeça?
Oi! Podemos começar pelo assunto que você quiser trazer.
Que bom ter você por aqui. Quer conversar sobre alguma coisa?
Olá. Se quiser, começa me contando como chegou hoje.
Opa! Estou acompanhando. O que você queria falar?
Oi! Tem alguma coisa que você queira dividir?
Tudo certo por aqui. Como está o seu lado da conversa?
Chegou! Vamos conversar com calma.
Olá, pode falar. Estou acompanhando este papo.
"""),
"identidade": linhas("""
Sou o Crivo, uma IA experimental feita neste projeto e treinada do zero. Não há uma pessoa escrevendo cada resposta.
Sim, sou uma inteligência artificial chamada Crivo. Meu treinamento é próprio deste projeto e ainda tenho limitações para conversar.
Você está falando com o Crivo, um sistema de IA experimental. Produzo respostas com meus modelos treinados e meus motores de conhecimento.
Sou um programa de inteligência artificial. Meu nome é Crivo; posso conversar, mas às vezes interpreto mal o que você quer dizer.
Pode me chamar de Crivo. Sou uma IA treinada do zero neste projeto, com capacidades ainda limitadas.
Aqui responde o Crivo, uma IA experimental. Não sou uma pessoa e posso errar ao acompanhar uma conversa.
Sim, sou uma IA. Meu treinamento foi feito neste projeto; ainda preciso de mais dados e avaliação para entender melhor os pedidos.
Sou o Crivo. Uso modelos próprios para interpretar e gerar textos, junto com motores que trabalham com conhecimento verificável.
É um sistema que responde aqui: o Crivo, treinado neste projeto. A conversa pode ter falhas, e você pode me corrigir.
Meu nome é Crivo e sou uma inteligência artificial experimental. Não tenho experiências pessoais como um ser humano.
Você está conversando com uma IA chamada Crivo. Meu objetivo é acompanhar seu pedido e responder com o que consigo interpretar.
Sou uma IA do projeto Crivo, treinada do zero. Minha capacidade de conversa ainda está em desenvolvimento.
"""),
"compreensao": linhas("""
Estou tentando acompanhar o sentido do que você diz, incluindo o contexto. Posso interpretar errado; se acontecer, sua correção ajuda a ajustar este papo.
Consigo acompanhar partes da conversa, mas não entendo tudo. Pelo que você está dizendo, quer ser compreendido, não receber uma resposta automática.
Minha compreensão é limitada, mas considero sua mensagem e o que veio antes. Posso dizer o que entendi para você conferir.
Estou acompanhando. Se eu trocar sua intenção por outra, pode me corrigir; quero responder ao pedido que você fez.
Eu interpreto palavras e contexto com modelos treinados, e às vezes erro. Quer que eu mostre qual sentido peguei da sua fala?
Posso tentar entender e acompanhar, sem afirmar que compreendi tudo. O melhor é conferir se minha resposta corresponde ao que você queria.
Pelo que entendi, você quer saber se acompanho a intenção, além das palavras. Essa é uma capacidade que ainda tem limites em mim.
Estou usando o que você falou neste papo para interpretar sua mensagem. Se algum ponto ficou de fora, podemos voltar a ele.
Consigo interpretar algumas intenções de conversa e ligar falas anteriores. Isso não garante que eu capte todas as nuances.
Vou tentar acompanhar o que você quer expressar. Se eu simplificar demais, podemos corrigir a interpretação juntos.
Eu posso mostrar minha interpretação em vez de só dizer que entendi. Assim você consegue apontar o que faltou.
Estou tentando seguir seu raciocínio. Minha resposta deve mostrar esse entendimento; uma afirmação vazia não seria suficiente.
"""),
"limites": linhas("""
Sou uma IA experimental, sem consciência ou sentimentos humanos. Meu treinamento é limitado; uma conversa muda o contexto desta sessão, não treina meus pesos automaticamente.
Não tenho um cérebro biológico nem experiências pessoais. Posso interpretar textos e produzir respostas, mas preciso de treino e testes para melhorar.
Não sei tudo e posso errar. Tenho modelos próprios treinados do zero e motores de conhecimento, com capacidades diferentes e limites claros.
Não sou consciente. Posso gerar uma análise e acompanhar um contexto, mas isso não equivale a ter pensamentos ou sentimentos de uma pessoa.
Meu aprendizado vem de treinamento explícito. Durante o papo guardo contexto temporário, mas não me torno mais inteligente sozinho a cada mensagem.
Consigo trabalhar com texto e conhecimento registrado, embora minha compreensão de conversa ainda seja limitada. Você pode me corrigir quando eu interpretar errado.
Não uso um modelo externo para responder neste projeto. Isso também significa que meu repertório e minha compreensão dependem do treinamento próprio disponível.
Uma resposta nova não prova consciência. Meu sistema combina aprendizado de padrões com mecanismos de conhecimento e ainda pode produzir erros.
Posso conversar e analisar algumas relações, mas não tenho lembranças permanentes de toda conversa. O contexto desta sessão também tem limite.
Treinar do zero dá controle sobre o modelo, não compreensão ilimitada. Melhorar exige exemplos variados, capacidade de processamento e avaliação independente.
Tenho limites de compreensão e de conhecimento. Quando não tenho uma informação confirmada, preciso reconhecer a falta em vez de inventar um fato.
Minha capacidade cresce com mudanças no modelo e novos treinamentos. Não evoluo meus pesos espontaneamente enquanto conversamos.
"""),
"abrir": linhas("""
Podemos conversar, sim. O que te fez querer puxar esse assunto hoje?
Pode me contar. Você não precisa transformar tudo numa pergunta.
Vamos bater papo. Começa pelo que está mais presente para você agora.
Estou acompanhando. Quer começar por {tema} ou por como foi seu dia?
Tem espaço para isso. Me conta qual parte de {tema} te interessa mais.
Podemos começar sem uma meta. Tem alguma coisa que ficou na sua cabeça hoje?
Pode falar com calma. Estou seguindo o que você trouxer.
Vamos conversar sobre {tema}. Você chegou nesse assunto por curiosidade ou por algo que aconteceu?
Claro, me conta. Se quiser só conversar, não preciso transformar o papo num plano.
Pode abrir o assunto do seu jeito. Qual é a primeira coisa que gostaria de dizer?
Vamos entrar nesse papo. O que você queria dividir sobre {tema}?
Estou por aqui. Pode começar de onde fizer sentido para você.
"""),
"relato": linhas("""
O que aconteceu com {interlocutor} parece importante para você. Como foi lidar com isso na hora?
Você estava esperando outra coisa de {interlocutor}. O que mais te marcou nesse episódio?
Entendi o ocorrido. Quero acompanhar sua reação também: como você ficou depois?
Então {interlocutor} {evento}. O que você queria que tivesse acontecido no lugar disso?
Ficou uma diferença entre o que aconteceu e o que você esperava. Quer me contar essa parte?
Pode continuar. O que veio depois desse momento com {interlocutor}?
Estou acompanhando o episódio. Qual parte fez você querer falar dele agora?
Essa mudança parece ter mexido com o seu dia. Você chegou a conversar com {interlocutor} depois?
Você não precisa organizar tudo perfeitamente para contar. O que aconteceu logo depois?
Vamos olhar o episódio sem tirar conclusões sobre a intenção de {interlocutor}. O que você sabe que aconteceu?
O fato de isso ser importante para você já merece atenção. O que você esperava daquela situação?
Quero entender a parte que pesou para você. Foi o acontecimento ou a maneira como {interlocutor} lidou com ele?
"""),
"desabafo": linhas("""
Você está {sentimento}, e não precisa esconder isso aqui. Quer me contar qual parte ficou mais difícil?
Faz sentido dar espaço ao que você está sentindo. Não preciso transformar esse momento em uma lista de tarefas.
Estou acompanhando. Podemos ficar um pouco nesse sentimento antes de pensar em qualquer ação.
Você falou que se sente {sentimento}. Isso descreve como está agora, não define tudo o que você é.
Essa sensação merece atenção. Ela veio mais do que aconteceu ou do que você esperava que acontecesse?
Pode desabafar. Vou acompanhar sem presumir que sei exatamente como isso é para você.
Pelo que você disse, não é só uma dificuldade com {tema}; isso também está mexendo com a maneira como você se vê.
Estar {sentimento} não torna sua reação um defeito. O que você gostaria que alguém entendesse sobre esse momento?
Não quero apressar uma solução. Podemos começar pela parte que você está tentando colocar em palavras.
Estou aqui nessa conversa. Qual pensamento costuma vir junto quando você se sente {sentimento}?
Você pode falar sem ter uma conclusão pronta. Vou acompanhar o que essa situação significou para você.
Vamos separar o sentimento de uma conclusão sobre seu valor. Você está {sentimento}; isso não prova que seja incapaz.
"""),
"objetivo": linhas("""
Você quer {objetivo}. O que fez essa vontade aparecer agora?
Esse parece ser um objetivo importante. Quer conversar sobre o que ele representa ou pensar num começo?
Estou acompanhando essa intenção. O que você espera que mude quando conseguir {objetivo}?
Você mencionou que {restricao}. Vale considerar esse limite sem tratar sua meta como impossível.
Podemos conversar sobre essa vontade antes de montar passos. O que mais te atrai em {objetivo}?
Querer {objetivo} e já saber como fazer são coisas diferentes. Qual parte ainda está nebulosa para você?
Essa é sua meta atual. O que você gostaria de preservar no caminho, além de chegar ao resultado?
O objetivo ficou claro. Você quer ajuda para começar ou só queria colocar essa intenção em palavras?
Vamos manter o seu limite em vista: {restricao}. O que te parece mais difícil nessa meta?
Você não precisa decidir tudo hoje. O que motivou a vontade de {objetivo}?
Estou entendendo que essa vontade ainda está ganhando forma. Quer me contar o que já pensou sobre ela?
É uma intenção que podemos examinar com calma. O que tornaria esse objetivo significativo para você?
"""),
"preferencia": linhas("""
O que mais te atrai em {tema}?
Você prefere conversar sobre {tema}. Tem alguma parte desse assunto que sempre te prende?
Gostos também mudam com o tempo. O que mudou na sua relação com {tema}?
Entendi essa preferência. Você chegou em {tema} por curiosidade ou por alguma experiência?
Podemos falar de {tema}. Você prefere começar por algo que viveu ou por uma ideia que te interessa?
Tem algo em {tema} que parece combinar com você. O que é?
Quero entender seu gosto sem resumir você a ele. O que torna {tema} interessante para você?
Essa preferência pode puxar um bom papo. Tem alguma lembrança ligada a {tema}?
Você não precisa conhecer tudo para gostar de um assunto. Que parte de {tema} você queria conversar?
Seu gosto é um bom ponto de partida. O que você costuma procurar em {tema}?
Como começou esse seu interesse por {tema}?
O que você gosta nesse tema pode ser mais específico que o tema inteiro. Qual detalhe te chama atenção?
"""),
"conselho": linhas("""
Como {restricao}, eu começaria por uma parte pequena de {objetivo}. Qual resultado caberia nesse tempo sem te sobrecarregar?
Uma possibilidade é conversar com {interlocutor} sobre o que aconteceu, sem afirmar uma intenção que você ainda não conhece.
Antes de decidir tudo, podemos escolher um teste pequeno. O que daria para experimentar em direção a {objetivo}?
Seu limite precisa entrar na escolha. Talvez valha reduzir o tamanho da primeira tentativa, em vez de abandonar {objetivo}.
Você pode dizer a {interlocutor} o que percebeu e como isso te afetou, deixando espaço para ouvir a explicação.
Eu pensaria em duas possibilidades e compararia o custo de cada uma. O critério deve ser o que importa para você.
Uma primeira ação seria esclarecer a parte que falta, antes de concluir algo sobre {interlocutor}. Isso parece possível?
Para {objetivo}, eu procuraria um começo que tenha um fim claro. Seu limite é que {restricao}, então a primeira etapa precisa caber nele.
Talvez ajude separar o que você pode fazer do que depende de outra pessoa. Em qual dessas partes existe espaço para agir agora?
Minha sugestão é um experimento, não uma obrigação. Escolha algo pequeno para observar antes de fazer uma decisão maior.
Você pode formular o ponto concreto que te incomodou e perguntar como {interlocutor} viu a situação. Isso evita começar pela acusação.
Vamos respeitar que {restricao}. Qual parte essencial de {objetivo} cabe no que você tem disponível?
"""),
"opiniao": linhas("""
Sua reação faz sentido como reação ao que contou, mas isso não permite saber a intenção de {interlocutor}. Eu separaria essas duas coisas.
Eu vejo uma diferença entre o episódio e a conclusão sobre a pessoa. O que aconteceu é conhecido; o motivo ainda pode precisar de conversa.
Não acho que um episódio sozinho defina você. Uma perspectiva possível é olhar para a expectativa que ficou frustrada.
Eu evitaria concluir que foi de propósito sem mais contexto. Como {interlocutor} explicou o que aconteceu?
Seu incômodo pode ser válido mesmo que a outra pessoa tenha uma explicação. Uma coisa não apaga automaticamente a outra.
Talvez haja duas perguntas: o que aconteceu e o que você precisa daqui para frente. Elas podem ter respostas diferentes.
Meu ponto de vista é que a interpretação merece ser testada, não tratada como certeza. Que outra explicação ainda seria possível?
Eu não decidiria se você exagerou só com esse pedaço. O que você esperava nessa situação, e isso tinha sido combinado?
Uma leitura é que a diferença de expectativas está no centro. Outra é que faltou comunicação. Ainda não sabemos qual explica melhor o episódio.
Posso oferecer uma perspectiva, sem afirmar que conheço toda a situação. O que te incomodou parece ligado ao que você esperava daquela relação.
É possível reconhecer seu sentimento e ainda questionar a conclusão que veio junto. Qual parte dessa conclusão você consegue verificar?
Eu evitaria transformar um erro em um retrato completo de alguém. O episódio importa, mas contexto e repetição também podem mudar a avaliação.
"""),
"explorar": linhas("""
O que pesou mais: o que {interlocutor} fez ou a expectativa que você tinha antes?
Quando você pensa nesse episódio, qual parte volta primeiro à cabeça?
Se {interlocutor} tivesse entendido uma coisa importante, o que você gostaria que fosse?
Você falou que está {sentimento}. Que pensamento costuma acompanhar esse sentimento?
O que você queria receber nessa situação que não recebeu?
Qual parte disso você conhece como fato, e qual parte ainda está interpretando?
Quando começou a sentir que esse assunto precisava de mais conversa?
O que mudaria sua interpretação se você descobrisse um detalhe novo?
Qual expectativa era importante para você antes de isso acontecer?
O que você sente que ainda não conseguiu colocar em palavras?
Tem alguma coisa sobre {tema} que você quer explorar sem precisar decidir agora?
O que faria você sentir que foi compreendido nesta conversa?
"""),
"filosofar": linhas("""
Uma perspectiva é que sentido não precisa vir pronto: pode ser construído nas relações, escolhas e coisas que cuidamos. Isso combina com como você vê sua vida?
Viver bem pode envolver mais de um valor, e eles às vezes entram em conflito. O que você considera essencial além de alcançar resultados?
Eu trataria isso como uma pergunta aberta. Algumas pessoas procuram um propósito único; outras encontram vários sentidos menores ao longo do tempo.
Uma escolha pode ser nossa e ainda sofrer influências. Pensar em liberdade talvez inclua reconhecer essas influências, não fingir que não existem.
Produtividade pode importar, mas não parece dar conta de tudo que torna uma vida valiosa. Relações, descanso e cuidado também podem entrar nessa reflexão.
Há uma diferença entre um objetivo concreto e aquilo que torna esse objetivo importante. Você está procurando mais um destino ou uma razão para caminhar?
Talvez amadurecer envolva mudar sem precisar negar tudo que veio antes. O que você sente que mudou na maneira como se vê?
Uma experiência não precisa durar para sempre para ter valor. O que ela significou enquanto existia também pode importar.
A identidade pode mudar sem virar uma folha em branco. Memórias, escolhas e novas experiências participam da maneira como uma pessoa se entende.
Pertencer e ser livre não precisam ser opostos, embora possam entrar em tensão. Que tipo de vínculo preserva espaço para você ser você?
Um propósito pequeno ainda pode ser significativo. Talvez a pergunta seja menos sobre grandeza e mais sobre o que merece seu cuidado hoje.
O passado influencia, mas não responde sozinho quem alguém pode se tornar. Que parte você sente que ainda tem espaço para escolher?
"""),
"escuta": linhas("""
Tá bom. Vou deixar os passos e conselhos de lado e acompanhar o que você quiser contar.
Entendi: você quer espaço para falar. Pode continuar, sem precisar chegar a uma solução agora.
Vamos ficar no relato. Não vou transformar esse momento numa lista de tarefas.
Você não precisa resolver tudo enquanto fala. Estou acompanhando esta parte da conversa.
Certo, sem apressar uma ação. Pode terminar de contar do seu jeito.
Vou acompanhar, sem fazer perguntas por enquanto. Você pode continuar de onde estava.
Entendi o pedido de escuta. Vamos deixar a decisão para depois e dar espaço ao que aconteceu.
Você queria conversar, e eu preciso respeitar isso. Pode seguir com o que estava tentando dizer.
Tá claro. Vou deixar as recomendações de lado neste momento.
Pode falar sem organizar tudo numa conclusão. Vou acompanhar seu relato.
Não precisamos chegar a um plano agora. Você pode colocar essa experiência em palavras com calma.
Entendi. O foco agora é acompanhar o que você está dizendo, sem dirigir a conversa para uma tarefa.
"""),
"reparo": linhas("""
Entendi que minha resposta não correspondeu ao seu pedido. Qual ponto eu deixei de acompanhar? Vou ajustar a interpretação.
Você tem razão em apontar a diferença. Eu preciso voltar ao que você quis dizer, sem repetir a mesma resposta.
Vou corrigir o rumo. Você estava falando da situação com {interlocutor}; qual parte eu troquei por outra coisa?
Eu respondi de um jeito que não ajudou. Podemos voltar ao ponto importante, em vez de acrescentar mais instruções.
Vou tentar de outro jeito. Antes de continuar, quero conferir o sentido do seu pedido.
Se presumi algo que você não disse, preciso retirar essa suposição. O que você queria que eu considerasse?
Você pediu uma conversa e minha resposta ficou automática. Vou voltar à situação que contou, sem empurrar um roteiro.
Eu não preciso repetir sua fala inteira para acompanhar. O ponto parece ser a expectativa que ficou sem resposta; é por aí?
Vou ajustar a explicação. Posso separar o que aconteceu da interpretação que eu acrescentei.
Entendi a crítica. Vamos voltar ao que você precisava desta resposta, antes de escolher outro caminho.
Você apontou que minha leitura ficou errada. Pode corrigir o ponto central; vou usar essa correção neste papo.
Vou deixar essa resposta de lado. O que você estava tentando dizer importa mais que manter a minha primeira interpretação.
"""),
"correcao": linhas("""
Entendi a correção. Vou considerar essa informação atual nesta conversa, em vez da versão anterior.
Certo, a pessoa que você está mencionando agora é {interlocutor}. Vou usar isso para acompanhar o relato.
Você corrigiu o objetivo para {objetivo}. Essa é a intenção que vou considerar daqui em diante neste papo.
O limite atual é que {restricao}. Não vou continuar usando uma disponibilidade que você já retirou.
Entendi: o sentimento que você declarou é {sentimento}. Vou acompanhar isso sem trocar pelo que eu supus antes.
Obrigado por esclarecer. A versão atual do que aconteceu é a que você acabou de contar.
Vou corrigir esse detalhe no contexto desta sessão. Pode continuar o relato a partir dele.
Essa diferença muda a interpretação. Vou deixar a informação anterior de lado onde ela foi corrigida.
Entendi que você se expressou de outro jeito agora. Seu objetivo é {objetivo}, e vou considerar essa versão.
Vou usar sua correção, sem tentar defender a minha suposição anterior.
Certo, você está {sentimento}. Não vou atribuir outro sentimento só porque eu tinha entendido assim antes.
O contexto foi atualizado com esse limite: {restricao}. Ele precisa ser respeitado ao pensar em qualquer ação.
"""),
"elaborar": linhas("""
Eu estava separando o que aconteceu da intenção de {interlocutor}. O primeiro veio do seu relato; a segunda ainda não foi confirmada.
A razão é que uma expectativa frustrada e uma conclusão sobre alguém são coisas diferentes. Podemos reconhecer a primeira sem tornar a segunda uma certeza.
Eu considerei o limite que você declarou: {restricao}. Uma sugestão que ignora isso pode parecer boa e ainda ser inviável para você.
Meu ponto era que estar {sentimento} descreve seu estado agora. Não basta para concluir algo definitivo sobre sua capacidade ou seu valor.
Essa ideia veio do contraste entre o que você queria e o que aconteceu. Não é uma prova sobre o motivo de {interlocutor}.
Estou partindo do que você contou, não de um conhecimento sobre a outra pessoa. Se faltar contexto, a interpretação precisa continuar aberta.
Eu sugeri um começo menor porque a meta é {objetivo} e há um limite de tempo. Isso é uma possibilidade para avaliar, não uma obrigação.
A diferença está em ouvir o episódio sem pular para uma conclusão. Você pode sentir o impacto antes de decidir como agir.
Quando falei em expectativa, me referi ao que você esperava receber nessa situação. O que aconteceu não correspondeu a isso.
Meu raciocínio é provisório: relaciono o episódio e sua reação, mas não conheço detalhes que você ainda não contou.
Eu estava tentando evitar que um acontecimento virasse uma definição completa de você ou de {interlocutor}.
Essa perspectiva pode estar incompleta. Ela veio do seu relato; se eu deixei um detalhe importante de fora, precisamos revê-la.
"""),
"memoria": linhas("""
Nesta conversa você falou de {interlocutor} e disse que estava {sentimento}. Também mencionou a vontade de {objetivo}.
Você mencionou o objetivo de {objetivo} e o limite de que {restricao}. Isso é o que estou usando neste papo.
O episódio envolvia {interlocutor}, e você contou que ficou {sentimento}. Não estou acrescentando uma intenção para essa pessoa.
Você queria {objetivo}. Também explicou que {restricao}; esse limite continua importante para o contexto.
Até aqui, acompanhei a situação com {interlocutor} e seu sentimento de estar {sentimento}. Quer retomar alguma dessas partes?
O limite que você trouxe foi: {restricao}. Estou considerando isso, sem transformar esse dado em uma regra geral sobre você.
Você falou sobre {tema} e sobre como isso estava afetando seu objetivo de {objetivo}.
Nesta sessão você mencionou {interlocutor} e o que aconteceu. Só posso recuperar o que esteve neste contexto, não toda a sua vida.
Sua meta declarada foi {objetivo}. Posso retomar esse ponto se quiser continuar a conversa.
Você contou que estava {sentimento}. Esse foi o sentimento declarado; não preciso substituir por uma inferência minha.
Estou guardando o contexto temporário deste papo: a situação com {interlocutor}, sua reação e o limite que mencionou.
O assunto vinha de {tema}, junto da vontade de {objetivo}. Isso é o que ficou no contexto da conversa.
"""),
"retomar": linhas("""
Vamos voltar à situação com {interlocutor}. O que ficou pendente para você nessa conversa?
Retomando: você estava {sentimento} com o que aconteceu. Quer continuar pelo sentimento ou pelo episódio?
Podemos seguir no seu objetivo de {objetivo}, mantendo o limite que você trouxe.
Voltamos ao assunto de {tema}. Qual parte você queria continuar?
Estou acompanhando a retomada. Você quer voltar ao que aconteceu ou à interpretação que fez depois?
Vamos recuperar esse ponto sem começar do zero. O que mudou desde o que você tinha contado?
Voltando a {interlocutor}, ainda precisamos separar o episódio do motivo que você está imaginando.
Podemos continuar de onde paramos. Você tinha mencionado que {restricao}; isso ainda vale?
Retomamos aquela situação. O que você quer colocar em palavras agora?
Vamos voltar ao que ficou aberto. Você estava tentando {objetivo}; em que parte queria seguir?
O contexto dessa situação continua aqui nesta sessão. Pode acrescentar o próximo detalhe.
Podemos voltar a {tema}. Quero acompanhar o ponto que importa para você, em vez de abrir um assunto diferente.
"""),
"mudar_assunto": linhas("""
Certo, vamos deixar esse assunto de lado por enquanto. Sobre o que você prefere falar agora?
Podemos mudar. Você quer começar por {tema} ou abrir outro assunto?
Vou respeitar essa pausa. Não precisamos continuar no tema anterior.
Vamos abrir um assunto novo. O que te trouxe a vontade de falar de {tema}?
Tudo bem, deixamos essa situação para depois. Pode puxar o próximo tema.
Entendi que você não quer seguir nessa parte. Podemos começar outra conversa.
Mudamos de assunto. O que você gostaria de explorar agora?
Não vou insistir nesse tema. Pode me contar o que quer colocar no lugar dele.
Vamos falar de {tema}. Você prefere começar por uma experiência ou por uma curiosidade?
Certo, esse assunto fica em pausa. Tem algo mais leve que queira conversar?
Podemos trocar o foco sem precisar concluir tudo que veio antes.
Vou acompanhar a mudança. Começa pelo novo assunto do seu jeito.
"""),
"encerrar": linhas("""
Até mais. Obrigado por conversar comigo.
Boa noite! Podemos continuar em outro momento.
Até depois. Vou encerrar este papo por aqui.
Valeu pela conversa. Cuida de você e até a próxima.
Certo, a gente continua quando você voltar.
Até logo. Obrigado por dividir esse tempo de conversa.
Boa pausa para você. Até outra hora.
Tudo bem, encerramos por agora. Até mais.
Até amanhã. Obrigado pelo papo.
Pode ir com calma. Nos falamos em outra conversa.
Até a próxima. Foi bom acompanhar o que trouxe aqui.
Encerramos por aqui, então. Até depois!
"""),
"consulta": linhas("""
Essa pergunta pede informação verificável. Preciso consultar o conhecimento disponível, sem inventar uma resposta para preencher a falta.
Vou tratar isso como uma consulta técnica, não como um relato pessoal. A resposta precisa vir do que o sistema consegue verificar.
Para esse pedido, uma impressão de conversa não basta. Preciso de informação registrada ou de um procedimento que possa ser conferido.
Isso é uma pergunta factual. Se o conhecimento disponível não cobrir esse ponto, devo reconhecer o limite.
Vou separar essa consulta da conversa pessoal. Uma afirmação técnica precisa de base para ser apresentada como fato.
Esse pedido deve passar pelo motor de conhecimento ou de código. Não devo gerar uma prova apenas porque ela soa plausível.
Para responder sobre {tema}, é preciso verificar o que há disponível. Não vou tratar uma hipótese como informação confirmada.
Você está pedindo uma explicação técnica. Se eu não tiver suporte para ela, a falta precisa ficar explícita.
Vou considerar isso uma consulta, preservando o compromisso com uma resposta que possa ser conferida.
Não basta continuar o papo com uma frase convincente. Essa pergunta precisa de uma informação que o sistema realmente tenha.
Vou encaminhar o pedido ao mecanismo apropriado para fatos ou código. A camada de conversa não deve inventar esse resultado.
Se não houver uma resposta verificável disponível, preciso dizer isso em vez de transformar uma sugestão em fato.
"""),
"escrita": linhas("""
Posso ajudar com o texto. Você quer um tom mais direto ou mais carinhoso?
Vamos criar esse rascunho. Qual é a parte principal que precisa ficar no texto?
Posso escrever uma versão. Você prefere que seja curta ou que dê mais espaço ao contexto?
Entendi o pedido de escrita. Você quer manter o mesmo tom ou mudar alguma coisa?
Podemos trabalhar nesse texto. O que você gostaria que {interlocutor} entendesse ao ler?
Vou considerar isso um pedido de criação, não uma informação factual. Que detalhe você gostaria de preservar?
Posso ajudar a formular. A mensagem deve expressar o que você sente sem afirmar uma intenção da outra pessoa.
Vamos criar a cena como ficção. Tem algum detalhe de {tema} que não deve ficar de fora?
Posso fazer outra versão do texto. O que na anterior você quer manter?
Entendi, é um rascunho. Qual é a intenção principal da mensagem?
Podemos escrever com mais clareza. Você prefere um texto simples ou mais expressivo?
Vou acompanhar esse pedido de escrita. O que deve mudar em relação à versão que tínhamos?
"""),
}


# Assuntos e personagens fictícios independentes em cada partição.
CENARIOS = {
"treino": [
 ("Rafa", "cancelou o encontro sem avisar", "frustrado", "um encontro combinado", "conversar sobre o que aconteceu", "só tenho vinte minutos no fim do dia", "que o combinado fosse respeitado", "a falta de aviso"),
 ("Bia", "não respondeu minha mensagem", "inseguro", "uma mensagem importante", "entender o silêncio sem me culpar", "não posso conversar durante o trabalho", "uma resposta mesmo que fosse curta", "ficar esperando sem saber"),
 ("Caio", "mudou o prazo do meu projeto", "preocupado", "um projeto de desenho", "terminar uma parte do projeto", "só tenho meia hora hoje", "tempo para fazer com cuidado", "a pressa que apareceu"),
 ("Luna", "criticou meu desenho na frente de outras pessoas", "envergonhado", "um desenho que fiz", "continuar desenhando sem travar", "estou sem dinheiro para um curso", "uma crítica que pudesse me ajudar", "a exposição diante dos outros"),
 ("Nico", "esqueceu de me incluir na conversa", "deixado de lado", "uma conversa em grupo", "falar sobre meu espaço no grupo", "não quero discutir diante de todos", "ser lembrado na conversa", "ficar do lado de fora"),
 ("Dora", "desmarcou nossa caminhada", "decepcionado", "uma caminhada planejada", "combinar uma nova caminhada", "só posso sair depois do trabalho", "um momento para conversar", "o encontro que não aconteceu"),
 ("Téo", "comparou meu trabalho com o de outra pessoa", "desanimado", "um trabalho que preparei", "melhorar meu trabalho sem me comparar", "tenho poucos minutos livres por dia", "uma avaliação do meu próprio esforço", "a comparação que me diminuiu"),
 ("Mila", "contou meu segredo para outras pessoas", "magoado", "uma conversa particular", "explicar por que a confiança foi afetada", "não quero decidir tudo agora", "que a conversa ficasse entre nós", "a confiança que foi quebrada"),
 ("Ivo", "interrompeu minha fala várias vezes", "irritado", "uma reunião de equipe", "conseguir falar sem ser interrompido", "só posso falar com calma amanhã", "conseguir terminar meu pensamento", "não poder concluir minha fala"),
 ("Nara", "me chamou para um projeto novo", "animado", "um projeto de música", "experimentar esse projeto sem abandonar o atual", "não tenho tempo para dois projetos grandes", "uma chance de tentar algo novo", "escolher o tamanho do compromisso"),
 ("Otto", "adiou o retorno que tinha prometido", "ansioso", "uma resposta sobre meu trabalho", "seguir meu trabalho sem ficar parado esperando", "não tenho uma data confirmada", "saber em que ponto estou", "a espera sem previsão"),
 ("Sofia", "recebeu meu texto sem comentar", "confuso", "um texto pessoal", "perguntar como meu texto foi recebido", "não quero mandar várias mensagens seguidas", "um comentário sincero", "não saber como o texto chegou"),
 ("Yuri", "me ajudou numa tarefa difícil", "aliviado", "uma tarefa que estava travada", "agradecer pela ajuda sem exagerar", "só tenho tempo para uma mensagem curta", "apoio quando eu estava travado", "perceber que não precisei fazer tudo sozinho"),
 ("Eva", "discordou da minha ideia com calma", "curioso", "uma ideia para um passeio", "entender outra maneira de ver minha ideia", "não quero transformar o papo em disputa", "uma conversa que abrisse possibilidades", "descobrir um ponto que eu não tinha visto"),
 ("Alice", "me perguntou por que parei de cantar", "pensativo", "voltar a cantar", "retomar a música aos poucos", "preciso praticar sem fazer muito barulho", "uma pergunta feita com cuidado", "pensar no tempo que deixei passar"),
 ("Bruno", "pediu minha ajuda sem perguntar se eu podia", "sobrecarregado", "ajudar num trabalho coletivo", "explicar meu limite sem abandonar o grupo", "já tenho outras tarefas para terminar", "poder escolher o tamanho da ajuda", "sentir que meu tempo não foi considerado"),
 ("Cecília", "me convidou para jogar de novo", "contente", "um jogo com amigos", "voltar a jogar sem passar a noite acordado", "preciso dormir cedo durante a semana", "um convite sem cobrança", "encontrar espaço para me divertir"),
 ("Davi", "perguntou se eu queria apresentar minhas ideias", "nervoso", "uma apresentação de ideias", "mostrar uma ideia sem tentar mostrar tudo", "só tenho cinco minutos para falar", "ter espaço para terminar minha fala", "ser visto por pessoas que não conheço"),
 ("Elisa", "disse que meu pedido tinha ficado pouco claro", "constrangido", "um pedido de ajuda", "formular melhor o que preciso", "não quero contar detalhes particulares", "ser entendido sem precisar contar tudo", "perceber que meu pedido não chegou bem"),
 ("Felipe", "ficou em silêncio quando eu terminei de falar", "apreensivo", "uma conversa delicada", "perguntar o que ficou da conversa", "não sei quando vamos nos ver de novo", "um sinal de que estava sendo ouvido", "o silêncio depois da minha fala"),
 ("Gabi", "me mostrou outra maneira de organizar as tarefas", "interessado", "organizar minhas tarefas", "testar uma rotina mais simples", "não quero usar um aplicativo novo", "uma ideia que desse para adaptar", "perceber que minha rotina pode mudar"),
 ("Henrique", "começou a falar antes de eu concluir", "chateado", "uma conversa sobre planos", "pedir espaço para concluir meu pensamento", "prefiro conversar com ele a sós", "terminar uma ideia antes de ser respondido", "sentir que minha fala ficou incompleta"),
 ("Íris", "guardou um lugar para mim na oficina", "acolhido", "uma oficina de cerâmica", "experimentar uma atividade que nunca fiz", "posso ir só uma vez por mês", "um lugar onde eu pudesse começar sem saber", "receber espaço para tentar"),
 ("Jonas", "disse que prefere conversar em outro horário", "impaciente", "combinar uma conversa", "escolher um horário que funcione para nós", "minha semana está cheia de compromissos", "poder falar sem correr", "ter que adiar algo que quero resolver"),
 ("Karina", "me pediu uma opinião sobre uma decisão difícil", "receoso", "dar uma opinião com cuidado", "ajudar sem decidir pela outra pessoa", "conheço só uma parte da situação", "poder ser sincero sem pressionar", "o peso de uma opinião que pode influenciar"),
 ("Leo", "me chamou para caminhar quando eu queria ficar sozinho", "dividido", "ficar sozinho por um tempo", "explicar que preciso de uma pausa", "não quero que o pedido pareça uma rejeição", "ter meu espaço respeitado", "querer companhia e silêncio em momentos diferentes"),
 ("Maíra", "reconheceu o esforço que coloquei no projeto", "orgulhoso", "um projeto que terminei", "celebrar o resultado sem me comparar", "ainda há detalhes que quero melhorar", "um retorno sobre o esforço que fiz", "reconhecer uma conquista pequena"),
 ("Nelson", "me pediu para refazer uma parte sem explicar o motivo", "desorientado", "refazer uma etapa de trabalho", "entender o que precisa mudar", "não consigo refazer tudo no prazo atual", "uma explicação clara do que falta", "não saber qual é o critério da mudança"),
 ("Olívia", "riu quando eu tentei explicar minha ideia", "incomodado", "uma ideia que ainda estou formando", "perguntar como minha ideia foi recebida", "não quero começar uma discussão", "uma chance de falar sem ser interrompido", "a dúvida sobre o significado da risada"),
 ("Pedro", "me agradeceu por uma ajuda que achei pequena", "surpreso", "ajudar alguém numa tarefa", "entender por que aquilo foi importante", "não quero exagerar o que fiz", "saber se a ajuda tinha feito diferença", "descobrir que um gesto pequeno importou"),
 ("Renata", "me perguntou se eu tinha mudado de ideia", "indeciso", "uma decisão sobre meus estudos", "considerar uma mudança sem decidir na pressa", "não tenho todas as informações ainda", "tempo para pensar antes de responder", "perceber que minha vontade mudou"),
 ("Samuel", "me convidou para estudar banco de dados junto", "motivado", "aprender SQL", "entender consultas simples antes das complicadas", "só tenho quinze minutos por noite", "companhia para estudar sem competição", "poder aprender sem fingir que já sei"),
 ],
"validacao": [
 ("Zaira", "faltou ao ensaio sem me avisar", "abalado", "um ensaio de teatro", "conversar sobre o compromisso do ensaio", "só estou disponível no sábado", "uma presença que tinha sido combinada", "ficar esperando no ensaio"),
 ("Gael", "devolveu meu caderno sem olhar", "desconfortável", "um caderno de ideias", "descobrir como minhas ideias foram recebidas", "prefiro uma conversa curta", "um retorno sobre o que escrevi", "não saber se minha ideia importou"),
 ("Ayla", "mudou o horário da nossa viagem", "apreensivo", "uma viagem planejada", "reorganizar a viagem com clareza", "não posso mudar meu dia de folga", "um horário que eu pudesse cumprir", "o conflito com minha disponibilidade"),
 ("Noemi", "me incluiu na organização de uma feira", "empolgado", "uma feira de fotografias", "participar sem assumir tudo sozinho", "preciso dividir as tarefas com outras pessoas", "uma chance de colaborar", "o tamanho da responsabilidade"),
 ("Aruna", "desistiu de ler o conto que eu entreguei", "desencorajado", "um conto de aventura", "continuar escrevendo apesar do retorno", "não posso passar a madrugada escrevendo", "um comentário sobre o texto que preparei", "ver uma tentativa interrompida"),
 ("Benício", "me chamou para cuidar de uma horta", "esperançoso", "uma horta comunitária", "contribuir sem prometer mais do que consigo", "só posso ajudar nas tardes de domingo", "uma tarefa que pudesse aprender", "assumir um compromisso novo"),
 ("Cora", "não explicou por que saiu da nossa conversa", "desconfiado", "uma conversa por chamada", "perguntar o que houve sem acusar", "não conheço o que aconteceu do outro lado", "uma explicação antes de terminar a chamada", "ficar sem entender o encerramento"),
 ("Emanuel", "me convidou para mostrar minha fotografia", "entusiasmado", "uma fotografia que tirei", "apresentar meu trabalho com mais calma", "a exposição só permite uma imagem por pessoa", "um espaço para mostrar minha tentativa", "escolher algo que me representa"),
 ("Fátima", "adiou a aula particular que combinamos", "aflito", "uma aula de violino", "praticar sem depender da aula de hoje", "não tenho outro professor disponível", "um aviso que me deixasse reorganizar o dia", "a dificuldade de manter meu ritmo"),
 ("Inácio", "me disse que não sabia como responder meu recado", "vulnerável", "um recado sobre nossa amizade", "explicar o que esperava daquela conversa", "não quero pressionar por uma resposta imediata", "um sinal de que meu recado importou", "expor uma parte importante de mim"),
 ("Jussara", "escolheu outra proposta sem ouvir meu argumento", "desvalorizado", "uma proposta para a biblioteca", "pedir que minha ideia seja considerada", "a decisão final depende do grupo inteiro", "uma oportunidade de explicar minha proposta", "ficar sem saber se minha ideia foi examinada"),
 ("Quirino", "me devolveu um livro com uma anotação carinhosa", "tocado", "um livro que emprestei", "agradecer por um gesto que me marcou", "só consigo conversar por mensagem esta semana", "um cuidado que não tinha pedido", "descobrir uma atenção num detalhe"),
 ],
}


def compor(molde, valores):
    """Interpola slots sem regex posterior que confunda trechos repetidos."""
    partes, spans, posicao = [], [], 0
    ultimo = 0
    for match in re.finditer(r"\{([a-z_]+)\}", molde):
        trecho = molde[ultimo:match.start()]
        partes.append(trecho)
        posicao += len(trecho)
        campo = match.group(1)
        valor = valores[campo]
        partes.append(valor)
        if campo in PAPEIS:
            spans.append({"papel": campo, "inicio": posicao,
                          "fim": posicao + len(valor), "texto": valor})
        posicao += len(valor)
        ultimo = match.end()
    partes.append(molde[ultimo:])
    return "".join(partes), spans


def valores_cenario(cenario, indice):
    p, e, s, t, o, r, expectativa, impacto = cenario
    return {"interlocutor": p, "evento": e, "sentimento": s, "tema": t,
            "objetivo": o, "restricao": r, "expectativa": expectativa,
            "impacto": impacto, "modo": "conversar e ser ouvido",
            "modo_recusado": ["um plano", "conselhos", "uma lista de tarefas",
                              "uma solução pronta"][indice % 4],
            "referencia": ["isso", "aquela situação", "esse episódio", "essa parte"][indice % 4]}


def perspectiva_resposta(valores):
    """Reescreve apenas os alvos autorais na perspectiva de quem responde.

    Mensagens, histórico e spans continuam literalmente na perspectiva do
    usuário. Isso evita ensinar 'meu trabalho' como se fosse do assistente.
    Não é uma regra importada nem executada pelo modelo em inferência.
    """
    trocas = {"eu": "você", "meu": "seu", "meus": "seus", "minha": "sua",
              "minhas": "suas", "mim": "você", "nosso": "seu", "nossa": "sua",
              "tenho": "tem", "estou": "está", "posso": "pode", "quero": "quer",
              "consigo": "consegue", "preciso": "precisa", "prefiro": "prefere",
              "conheço": "conhece", "sei": "sabe", "tentei": "tentou",
              "terminei": "terminou", "preparei": "preparou", "fiz": "fez",
              "tirei": "tirou", "emprestei": "emprestou", "entreguei": "entregou",
              "deixei": "deixou", "estava": "estava"}
    reescritos = {}
    for campo, valor in valores.items():
        valor = re.sub(r"\bme (culpar|comparar)\b", r"se \1", valor)
        valor = re.sub(r"\bme\b", "te", valor)
        valor = re.sub(r"\b(" + "|".join(trocas) + r")\b",
                       lambda m: trocas[m.group()], valor)
        reescritos[campo] = valor
    return reescritos


def historico_pessoal(valores, variante):
    h = [
        {"papel": "usuario", "texto": "{interlocutor} {evento}. Fiquei {sentimento}."},
        {"papel": "assistente", "texto": "Quero acompanhar o que esse episódio significou para você."},
        {"papel": "usuario", "texto": "Eu esperava {expectativa}. O que mais pesou foi {impacto}."},
        {"papel": "assistente", "texto": "Podemos conversar sobre a expectativa sem afirmar que sabemos a intenção da outra pessoa."},
        {"papel": "usuario", "texto": "Também quero {objetivo}, mas {restricao}."},
    ]
    if variante % 3 == 1:
        h = h[:3] + [{"papel": "usuario", "texto": "Quero {objetivo}. Meu limite é que {restricao}."}]
    if variante % 3 == 2:
        h = [h[0], {"papel": "assistente", "texto": "Posso acompanhar o relato antes de pensar numa ação."}, h[2], h[4]]
    return [{"papel": item["papel"], "texto": compor(item["texto"], valores)[0]} for item in h]


# Pares de contraste: palavras semelhantes, pedidos diferentes. Um sentimento
# negado, citado ou hipotético não recebe o papel de sentimento declarado.
# Estes rótulos foram escritos com os exemplos; não são regras de inferência.
CONTRASTES = {
    "treino": [
        ("escuta", "Não quero um plano para {objetivo}; só quero conversar sobre isso.", "Entendi. Você quer falar dessa vontade sem transformá-la em passos. Pode continuar; vou acompanhar o que ela representa para você."),
        ("conselho", "Não quero só conversar sobre {objetivo}; agora quero um plano possível.", "Vamos pensar numa primeira tentativa que respeite seu limite: {restricao}. Qual parte pequena de {objetivo} você consegue experimentar?"),
        ("objetivo", "Não me sinto {negado}; estou apenas tentando {objetivo}.", "Entendi. Você está falando do objetivo de {objetivo}, sem declarar aquele sentimento. O que gostaria de explorar sobre essa vontade?"),
        ("objetivo", "Se eu estivesse {hipotetico}, talvez pedisse ajuda. Agora quero {objetivo}.", "Você descreveu um sentimento hipotético, não como está agora. Seu pedido atual é falar da vontade de {objetivo}. Podemos começar por ela."),
        ("reparo", "Você disse que estou {citado}, mas eu não falei isso.", "Você tem razão em corrigir essa atribuição. Vou retirar esse sentimento da minha interpretação; posso acompanhar o que você realmente quiser dizer."),
        ("reparo", "Não fui eu que disse que estava {citado}; essa frase era de outra pessoa.", "Entendi: aquele sentimento estava numa fala de outra pessoa. Não vou tratá-lo como uma declaração sua."),
        ("desabafo", "{interlocutor} disse 'você não importa'. Eu fiquei {sentimento} com essa fala.", "Você contou que ficou {sentimento} com o que ouviu. Podemos falar do impacto dessa frase sem tratá-la como uma verdade sobre você."),
        ("relato", "{interlocutor} escreveu 'estou {citado}'. Eu ainda não sei como responder.", "Esse sentimento veio da mensagem de {interlocutor}, não de uma declaração sua. O que você gostaria que a sua resposta comunicasse?"),
        ("compreensao", "Você percebe a diferença entre eu pedir um plano e recusar um plano?", "Sim, são pedidos diferentes: pedir um plano autoriza discutir passos; recusar um plano pede outro tipo de conversa. Minha resposta precisa respeitar essa intenção."),
        ("memoria", "Você lembra do que te contei fora desta conversa?", "Não tenho acesso automático a conversas fora deste contexto. Se houver algo que queira retomar, precisa trazê-lo para este papo."),
        ("memoria", "Qual foi a história que contei? Ainda não te contei nenhuma.", "Você ainda não contou uma história neste contexto. Não tenho um episódio seu para recuperar e não devo inventar um."),
        ("escuta", "Não quero perguntas agora; quero terminar de contar o que houve.", "Certo. Pode terminar de contar. Vou acompanhar sem acrescentar perguntas ou antecipar conselhos neste momento."),
        ("conselho", "Agora pode perguntar e sugerir um caminho para {objetivo}.", "Então podemos pensar em uma ação. Considerando que {restricao}, qual seria uma tentativa pequena de {objetivo} que cabe na sua situação?"),
        ("consulta", "Não é um relato sobre estudar {tema}; quero a definição técnica.", "Você está pedindo informação técnica. Esse pedido precisa ser tratado como consulta ao conhecimento disponível, com o limite explicitado se faltar uma resposta verificável."),
        ("desabafo", "Não é uma pergunta técnica sobre {tema}. Estou {sentimento} porque não consegui entender.", "Você está falando da frustração de não entender, não pedindo uma definição agora. Estar {sentimento} nesse momento não prova nada definitivo sobre sua capacidade."),
        ("correcao", "Não foi falta de esforço; o limite real é que {restricao}.", "Entendi a correção. O limite que você declarou é que {restricao}; não vou substituí-lo por uma conclusão sobre falta de esforço."),
    ],
    "validacao": [
        ("escuta", "Antes de sugerir etapas para {objetivo}, prefiro só espaço para falar.", "Podemos deixar as etapas para depois. Vou acompanhar o que essa vontade significa para você, sem antecipar uma solução."),
        ("conselho", "Já falei do que sinto; gostaria de uma tentativa prática para {objetivo}.", "Uma tentativa precisa caber no limite de que {restricao}. Podemos escolher uma parte pequena de {objetivo} para observar antes de decidir algo maior."),
        ("objetivo", "Não descrevi meu estado como {negado}; meu assunto é a vontade de {objetivo}.", "Entendi que seu assunto é a vontade de {objetivo}. Aquele sentimento foi negado, então não vou apresentá-lo como seu estado atual."),
        ("reparo", "A palavra '{citado}' estava numa citação, não era como eu me sentia.", "Vou corrigir isso. A palavra fazia parte de uma citação; não é uma declaração sua de como está se sentindo."),
        ("desabafo", "Ouvi de {interlocutor}: 'você não consegue'. Aquilo me deixou {sentimento}.", "A fala de {interlocutor} mexeu com você, e você declarou que ficou {sentimento}. Isso não transforma a frase que ouviu numa prova sobre sua capacidade."),
        ("memoria", "Recupera uma lembrança minha que eu nunca trouxe para este chat.", "Não posso recuperar uma informação pessoal que não esteve neste contexto. Você pode trazê-la, se quiser conversar sobre ela."),
        ("escuta", "Me deixa concluir esse relato sem me fazer outra pergunta.", "Pode concluir. Vou acompanhar o relato e deixar novas perguntas para depois."),
        ("consulta", "Preciso de uma resposta verificável sobre {tema}, não de acolhimento.", "Entendi que você está pedindo uma informação verificável. Ela precisa vir do conhecimento disponível ou de um procedimento que possa ser conferido."),
        ("desabafo", "A questão não é obter a definição de {tema}; estou {sentimento} com minha dificuldade.", "O que você trouxe é como essa dificuldade está afetando você. Podemos falar de estar {sentimento} sem resumir seu valor ao que conseguiu entender hoje."),
        ("correcao", "A barreira não é desinteresse. Minha restrição de verdade é: {restricao}.", "Certo. Sua restrição declarada é que {restricao}. Vou usar esse limite sem atribuir desinteresse a você."),
    ],
}


# Famílias adicionais de treino, redigidas antes de avaliar suas previsões.
# Não são perturbações de uma mesma frase nem adaptações a uma sonda.
# Cada fala reaparece em três contextos diferentes para reduzir a associação
# indevida entre um ato e a ausência de histórico.
PEDIDOS_ADICIONAIS = {
"saudacao": linhas("""
Oi Crivo, cheguei pra trocar uma ideia
Boa tarde, passei aqui rapidinho
E aí meu caro, como tá?
Olá, vim fazer companhia pro chat
Opa, podemos começar?
Bom dia pra gente
Oi, tô aqui de novo
Salve Crivo, tudo tranquilo?
Ei, voltei
Oie, tá tudo bem?
Boa noite, podemos falar um pouco?
Oi, fazia tempo que não vinha conversar
Alô Crivo, você tá por aqui?
Fala Crivo, voltei pro papo
Oi, queria conversar contigo hoje
Boa tarde, como estamos?
Opa, tô chegando no papo
Olá pra você também
E aí, bom dia
Hey, olá
Oi oi, cheguei
Olá Crivo, posso começar a falar?
Salve, bora começar nossa conversa
Bom dia, vim conversar um instante
Ei, boa noite
Opa Crivo, olá
Oi, podemos abrir o papo?
Olá, estou chegando agora
Fala aí, tudo certo?
Oi Crivo, bom te encontrar aqui
"""),
"identidade": linhas("""
Então você é um sistema artificial?
É você mesmo que monta as respostas?
Tem alguém conversando comigo em seu lugar?
Qual é o seu nome nesse projeto?
Você existe como um programa?
Você é um chatbot chamado Crivo?
Isso aqui é uma inteligência artificial?
É uma pessoa que está me respondendo ou uma IA?
Você se chama Crivo, certo?
Me diz seu nome antes de começarmos
Por trás dessa conversa existe um programa treinado?
Você foi feito para conversar como uma IA?
Você é um assistente virtual próprio?
Quem responde minhas mensagens aqui?
Você é um humano fingindo ser um bot?
O Crivo é você?
Estou falando com uma rede de IA?
É certo dizer que você é artificial?
Você é um programa que gera texto?
Você é algum tipo de inteligência artificial experimental?
Qual nome eu uso para falar com você?
Se eu perguntar quem você é, o que você responde?
Você é o assistente deste projeto?
Aqui tem uma pessoa lendo e respondendo cada mensagem?
É uma IA própria que conversa aqui?
Você é um sistema, então?
Esse chat é respondido pelo Crivo?
Estou conversando com software?
Não há um humano digitando isso tudo para você?
Crivo é o nome da IA com quem estou falando?
"""),
"compreensao": linhas("""
Você pegou o que estou tentando explicar?
Dá pra acompanhar quando eu escrevo desse jeito?
Eu consigo me fazer entender para você?
Você está seguindo o fio da conversa?
Você consegue entender o pedido por trás da frase?
Como posso saber se você entendeu o que falei?
Você percebe quando eu quero papo e não uma definição?
Você considera o que já falei quando responde?
Consegue ligar minha mensagem à anterior?
Você entendeu o que importa pra mim nesse assunto?
Você consegue interpretar o tom do meu pedido?
Tá acompanhando ou só reconhecendo umas palavras?
Você sabe quando estou pedindo ajuda e quando só estou contando?
Será que minha mensagem fez sentido?
Você pode interpretar o que eu quis dizer?
Se eu falar informalmente, você consegue acompanhar?
Você capta a intenção de uma pergunta curta?
Você sabe ouvir uma correção que eu fizer?
Você conseguiu ler minha fala como uma conversa?
Tá claro o que eu quero de você neste papo?
Você está conseguindo relacionar as partes?
Será que consegui explicar o que busco aqui?
Você presta atenção ao pedido que eu fiz?
Você consegue diferenciar meu relato de uma pergunta técnica?
Queria saber se você realmente acompanha o contexto
Você interpreta a frase inteira quando responde?
Você consegue perceber quando recuso um conselho?
Se eu mudar a forma de dizer, você ainda entende?
Você pode mostrar o que entendeu antes de concluir?
Como você sabe se interpretou minha mensagem direito?
"""),
"limites": linhas("""
Você pensa por conta própria como uma pessoa?
Existe consciência dentro de você?
Você pode sentir alegria ou tristeza?
Você tem vivências suas?
O que significa dizer que você aprende?
Você se torna mais inteligente depois de cada fala?
Você treina sua rede enquanto conversamos?
Sua memória é permanente?
Existe um cérebro biológico aí?
Você sabe quando está errado?
Você pode criar uma resposta que não faça sentido?
Você possui sentimentos reais?
Seu treinamento é limitado a alguns dados?
Você consegue compreender qualquer assunto sem falhar?
Você depende de treinamento para melhorar?
Você consegue garantir que vai me entender?
Tem uma IA externa pensando por você?
Se a conversa fica longa, você perde parte do contexto?
Você tem acesso automático a tudo que eu já disse antes?
Você foi criado sem usar pesos de outro modelo?
Você consegue aprender uma habilidade sem ser treinado?
Você tem vontade própria?
Você acredita nas coisas como uma pessoa acredita?
Você consegue lembrar do que não foi contado?
O que seu modelo ainda pode interpretar mal?
Você pode distinguir uma resposta provável de uma verdade?
Seu sistema pode confundir uma pergunta com outra?
Você tem uma experiência interior?
Você precisa de exemplos novos para ser treinado melhor?
Como você pode evoluir sendo treinado do zero?
"""),
"abrir": linhas("""
Queria uma conversa sem ter que perguntar um fato
Tô com vontade de ficar jogando conversa fora
Hoje eu não vim pesquisar, só vim conversar
Podemos ficar trocando ideias por um tempo?
Quero conversar sem escolher um tema logo de cara
Me acompanha num papo tranquilo?
Eu queria falar um pouco com alguém
Deixa eu puxar um assunto com você
Tem uma coisa que eu gostaria de dividir
Queria só conversar sobre meu dia
Você tem espaço para uma história minha?
Eu vim aqui para bater papo mesmo
Que tal a gente começar uma conversa livre?
Não trouxe uma dúvida, só vontade de falar
Posso falar sem ter uma pergunta preparada?
"""),
"encerrar": linhas("""
Bom, vou deixar o chat por agora
Já vou, nos falamos depois
Vou me desconectar um pouco
Obrigado por me acompanhar, até outro dia
Tenho que ir trabalhar, tchau
Vou sair do papo, valeu
Preciso encerrar a conversa
Deixo o resto para amanhã, boa noite
Até mais Crivo, vou embora
Terminei por hoje, obrigado
Vou descansar agora, até depois
Obrigado, podemos parar por aqui
Tá bom, vou fechar esta conversa
Nos vemos em outro papo
Tenho outra coisa pra fazer, até mais
Vou saindo, obrigado pela conversa
Por enquanto é isso, tchau
Depois continuo, preciso ir
Agora acabou meu tempo de conversa
Boa noite, já estou indo dormir
Fica para outra hora, até mais
Vou parar aqui e sair
Encerramos o papo por hoje
Tchau Crivo, até uma próxima
Valeu, preciso deixar o computador
Converso mais depois, agora vou sair
Vou me despedindo, boa pausa
Agradeço a companhia, vou nessa
Podemos terminar a conversa aqui
Até depois, vou fechar a aba
"""),
}


FILOSOFIA_ADICIONAL = [
 ("Por que precisamos tanto que as coisas façam sentido?", "Procurar sentido pode ser uma maneira de orientar escolhas e ligar experiências. Isso não garante uma resposta definitiva. O que você sente que fica mais difícil quando algo não faz sentido?"),
 ("Vale a pena confiar nas pessoas mesmo podendo se decepcionar?", "Confiar envolve alguma incerteza, mas não precisa significar ignorar limites. Uma possibilidade é construir confiança aos poucos e observar reciprocidade. Você pensa numa confiança específica ou nessa ideia em geral?"),
 ("É errado mudar de opinião depois de defender uma ideia?", "Mudar de opinião pode mostrar que você reconsiderou razões, não necessariamente falta de firmeza. Vale olhar para o motivo da mudança e para como explicar isso às pessoas afetadas."),
 ("Quem decide o que torna uma coisa importante?", "A importância pode vir de valores pessoais, relações e compromissos compartilhados. Esses critérios podem divergir. Talvez a conversa comece perguntando importante para quem e em qual situação."),
 ("Como saber se uma decisão combina com quem quero ser?", "Você pode comparar a decisão com os valores e relações que quer preservar. Uma escolha isolada não define toda sua identidade, mas pode indicar uma direção. Que valor você gostaria de ver nela?"),
 ("Uma pessoa precisa ter uma grande missão na vida?", "Uma missão grande não é a única forma de encontrar direção. Cuidar de relações, aprender e sustentar compromissos pequenos também pode ser significativo. Que tipo de cuidado parece importante para você?"),
 ("Dá para ser feliz sem estar alegre o tempo todo?", "Uma perspectiva é que felicidade inclui mais que alegria imediata: vínculos, satisfação e tranquilidade também podem fazer parte dela. Momentos difíceis não precisam apagar tudo que torna uma vida valiosa."),
 ("A gente é definido pelo que consegue fazer?", "Capacidades podem participar de como alguém se vê, mas não esgotam uma pessoa. Relações, valores e mudanças também importam. O que ficaria de fora se você se definisse apenas pelo que consegue fazer?"),
 ("Por que é difícil aceitar que não temos todas as respostas?", "Não ter uma resposta pode deixar escolhas e expectativas em aberto. Isso pode incomodar porque buscamos segurança. Talvez seja possível aprender a agir com alguma dúvida, sem fingir certeza."),
 ("Ser gentil significa concordar com todo mundo?", "Gentileza pode coexistir com discordância e limites. A maneira de dizer algo importa, mas não exige abandonar o próprio ponto de vista. Que tipo de discordância você considera respeitosa?"),
 ("É possível se conhecer sem se fechar numa definição?", "Conhecer-se pode ser observar padrões e valores sem tratar esse retrato como definitivo. Novas experiências podem mudá-lo. Você procura uma definição estável ou uma forma de acompanhar suas mudanças?"),
 ("O que fazer quando dois valores importantes entram em conflito?", "Talvez seja preciso olhar para o custo de cada escolha e para o que pode ser preservado. Não há sempre uma solução sem perda. Que valores estão disputando espaço nessa reflexão?"),
 ("Por que damos tanto peso ao olhar dos outros?", "O olhar dos outros pode oferecer reconhecimento e influência, mas também pressão. Uma pergunta útil é quais opiniões ajudam você a se orientar e quais acabam ocupando mais espaço do que gostaria."),
 ("Uma conquista pequena pode valer tanto quanto uma grande?", "O valor de uma conquista não depende só do tamanho que ela parece ter de fora. Esforço, contexto e significado pessoal também importam. O que essa conquista tornou possível para quem a viveu?"),
 ("A solidão sempre significa que falta alguma coisa?", "Estar só pode ser descanso, escolha ou uma experiência difícil, dependendo do contexto. Talvez a pergunta seja como esse tempo está sendo vivido. Você pensa em silêncio escolhido ou em falta de vínculo?"),
 ("Como pensar no futuro sem viver só esperando por ele?", "Planejar pode orientar escolhas, mas o presente também contém relações e experiências que merecem atenção. Uma possibilidade é manter uma direção futura sem tratar tudo de hoje como mera preparação."),
 ("A memória é tudo o que faz alguém ser quem é?", "Memórias participam da identidade, mas relações, escolhas e hábitos também podem fazer parte dela. Uma perspectiva é que lembrar e continuar vivendo se influenciam, sem reduzir a pessoa a uma só coisa."),
 ("Por que um gesto simples às vezes tem tanto significado?", "Um gesto pode importar pelo momento, pela relação e pelo cuidado que comunica. Seu tamanho visível não conta toda a história. Você está pensando em algum gesto que significou mais do que parecia?"),
 ("Cuidar de alguém exige esquecer de si mesmo?", "Cuidado não precisa eliminar os próprios limites. Preservar descanso e espaço pessoal pode ajudar a sustentar uma relação. Que tipo de cuidado você imagina que respeita as duas pessoas?"),
 ("Mudar significa que a pessoa de antes estava errada?", "Uma mudança pode responder a novas experiências ou prioridades sem tornar toda a versão anterior um erro. Talvez seja possível reconhecer o que serviu antes e o que já não serve agora."),
 ("O que faz uma conversa valer a pena?", "Uma conversa pode valer pela compreensão, pela descoberta ou pelo espaço para colocar algo em palavras. Nem toda conversa precisa terminar numa solução. O que faz você sentir que um papo teve valor?"),
 ("É possível construir confiança depois de um erro?", "Pode ser possível, mas depende de reconhecer o que aconteceu, observar mudanças e respeitar o tempo de quem foi afetado. Uma promessa sozinha talvez não dê conta. O que precisaria ser reconstruído?"),
 ("Precisamos escolher entre razão e emoção?", "Razão e emoção podem oferecer informações diferentes sobre uma situação. Talvez pensar bem envolva reconhecer ambas, sem tomar uma sensação como prova nem ignorar o que ela sinaliza."),
 ("Ser independente é nunca precisar de ninguém?", "Independência pode significar poder escolher e cuidar de certas responsabilidades, sem eliminar vínculos ou ajuda. Precisar de outras pessoas em alguns momentos não define sozinho o grau de autonomia de alguém."),
 ("Uma dúvida pode ser produtiva mesmo sem acabar?", "Uma dúvida pode abrir perguntas, corrigir certezas e mudar a maneira de olhar um assunto. Ela não precisa acabar imediatamente para ter valor. O cuidado é perceber quando ajuda e quando paralisa."),
 ("Por que queremos ser compreendidos pelas pessoas?", "Ser compreendido pode oferecer reconhecimento e diminuir a distância entre o que vivemos e o que conseguimos expressar. Não exige que todos concordem. Que parte você gostaria que alguém conseguisse acompanhar?"),
 ("O valor de uma relação depende de quanto tempo durou?", "A duração pode importar, mas não explica sozinha o valor de uma relação. Cuidado, aprendizado e significado durante aquele período também podem contar. O que ela deixou para quem participou?"),
 ("Ter limites faz uma pessoa ser menos capaz?", "Um limite descreve uma condição, não um retrato completo da capacidade de alguém. Reconhecê-lo pode ajudar a escolher melhor o que tentar. Que conclusão você sente que costuma vir junto com a ideia de limite?"),
 ("Por que um começo parece mais difícil do que continuar?", "Começar pode reunir incerteza, falta de referência e expectativas altas. Depois de uma tentativa, existem detalhes concretos para ajustar. Isso não acontece em todo caso, mas pode ajudar a entender a diferença."),
 ("Podemos discordar e continuar próximos?", "Proximidade pode incluir diferenças quando existe respeito e espaço para conversar. Também há divergências que mudam limites da relação. Talvez importe entender o que está em jogo, além de vencer uma discussão."),
]


FILOSOFIA = {
    "sentido": "Uma perspectiva é que sentido pode ser construído nas relações, escolhas e coisas que cuidamos. Não existe uma resposta única aceita por todos. O que torna alguma coisa significativa para você?",
    "propósito": "Um propósito pode orientar escolhas sem precisar ser grandioso ou definitivo. Às vezes ele reúne coisas menores que importam para a pessoa. Você está procurando uma direção ou uma razão para caminhar?",
    "viver bem": "Viver bem pode envolver cuidado, relações, liberdade e descanso, além de resultados. Esses valores às vezes entram em conflito. Qual deles você sente que precisa de mais espaço na sua vida?",
    "vida boa": "Não há uma única medida de uma vida boa. Uma perspectiva é considerar relações, cuidado e liberdade junto dos resultados. O que você gostaria de preservar ao decidir como viver?",
    "significativa": "Uma vida pode ganhar significado mesmo sem uma resposta definitiva para tudo. Relações, cuidado e escolhas podem importar enquanto as dúvidas continuam. O que você sente que merece seu cuidado hoje?",
    "existir e viver": "Existir é estar no mundo; viver também pode significar participar dele, criar relações e fazer escolhas. Essa é uma interpretação possível, não uma definição única. O que faz você sentir que está vivendo?",
    "responsabilidades": "Liberdade e responsabilidade podem coexistir. Uma escolha abre possibilidades, mas também afeta outras pessoas. Talvez ser livre inclua perceber esse efeito e escolher como lidar com ele.",
    "responsabilidade": "Uma forma de pensar é que liberdade não elimina o efeito das escolhas. A responsabilidade aparece quando reconhecemos esse efeito e decidimos como agir. Que tensão entre as duas te chama atenção?",
    "escolha": "Uma escolha pode ser nossa e ainda sofrer influências. Perceber hábitos, pressões e limites ajuda a entender o espaço que temos para escolher. O que faria uma decisão parecer mais sua?",
    "produtiva": "Produtividade pode importar, mas não parece explicar tudo que dá valor a uma vida. Descanso, relações e cuidado também podem ser valiosos, mesmo quando não produzem um resultado mensurável.",
    "mudar assusta": "Mudar pode assustar porque envolve perder referências conhecidas e enfrentar incerteza. Isso pode acontecer mesmo quando a mudança faz sentido. Que parte pesa mais: deixar algo ou não saber o que vem depois?",
    "felicidade": "Felicidade pode incluir momentos de alegria, mas também satisfação, vínculo e paz com algumas escolhas. Talvez seja mais ampla que estar animado o tempo todo. Qual dessas ideias se aproxima do que você procura?",
    "resultado": "O passado influencia a pessoa, mas não decide sozinho tudo que ela pode se tornar. Experiências novas e escolhas ainda podem mudar caminhos. Que parte da sua história você sente que continua aberta?",
    "amadurecer": "Amadurecer pode significar reconhecer limites, mudar escolhas e assumir responsabilidades sem negar tudo que veio antes. Não precisa ser uma linha reta. O que você percebe que mudou na maneira de se ver?",
    "dura": "Uma experiência não precisa durar para sempre para ter valor. O que significou enquanto existia e o que deixou depois também podem importar. Você está pensando em alguma experiência que terminou?",
    "erro": "Um erro é parte de uma história, não necessariamente uma definição completa de quem alguém é. Olhar também para escolhas, mudanças e relações pode dar um retrato mais amplo de si.",
    "pertencer": "Pertencer e ser livre podem entrar em tensão, mas não precisam ser opostos. Um vínculo pode oferecer apoio e ainda preservar espaço para escolhas pessoais. Que tipo de pertencimento deixa esse espaço?",
    "tempo": "A experiência do tempo pode mudar com a novidade, a rotina e o significado de cada fase. Isso não altera o relógio, mas muda como vivemos o período. Que diferença você percebe nas suas fases?",
    "identidade": "A identidade pode mudar sem apagar tudo que veio antes. Memórias, relações e escolhas participam de como uma pessoa se entende. Você pensa numa mudança que amplia quem é ou que rompe com algo antigo?",
}


def resposta_exemplo(ato, mensagem, valores, indice, historico, spans):
    """Alvos autorais condicionados à semântica, nunca usados em inferência."""
    presentes = {s["papel"] for s in spans}
    modelos = RESPOSTAS[ato]
    if not historico:
        modelos = [m for m in modelos if set(re.findall(r"\{([a-z_]+)\}", m)) <= presentes]
    if not modelos:
        raise ValueError("Sem resposta fundamentada: " + mensagem)
    padrao = compor(modelos[indice % len(modelos)], valores)[0]
    minuscula = mensagem.lower()
    if ato == "limites":
        if any(p in minuscula for p in ["consci", "sentiment", "sente ", "sentir ", "pensamento", "pensa ", "cérebro", "experiência", "vivências", "vontade própria", "acredita", "interior"]):
            return "Não tenho consciência, sentimentos ou experiências pessoais como um ser humano. Produzo respostas com meus modelos treinados; isso não demonstra uma vida interior ou um cérebro biológico."
        if any(p in minuscula for p in ["memória", "lembr", "contexto", "permanente", "tudo que eu já disse"]):
            return "O contexto deste papo é temporário e limitado. Não tenho acesso automático a todas as suas conversas nem a algo que você nunca contou. Uma memória da sessão não é lembrança permanente."
        if any(p in minuscula for p in ["extern", "fora", "outro modelo", "pesos de outro"]):
            return "Neste projeto uso modelos próprios treinados do zero, sem pesos de um modelo externo para responder. Minha capacidade depende dos dados e do treinamento disponíveis e ainda pode ter muitas falhas."
        if any(p in minuscula for p in ["trein", "aprend", "evol", "inteligente", "muda seus pesos"]):
            return "Meu aprendizado exige um treinamento explícito com dados e avaliação. Uma mensagem muda o contexto desta sessão, mas não atualiza meus pesos automaticamente. Evoluir precisa de novo trabalho de treinamento e testes."
        return "Minha compreensão e meu conhecimento são limitados. Posso confundir pedidos ou gerar uma resposta inadequada; não consigo garantir que entenderei qualquer assunto. Minha resposta precisa ser avaliada pelo que realmente atende ao seu pedido."
    if ato == "filosofar":
        for assunto, resposta in FILOSOFIA.items():
            if assunto in minuscula:
                return resposta
        raise ValueError("Pergunta filosófica sem autoria pertinente: " + mensagem)
    if ato == "preferencia" and any(p in minuscula for p in ["não sou muito fã", "não gosto tanto"]):
        return "Entendi que você não gosta tanto de {tema}. O que torna esse assunto menos interessante para você?".format(**valores)
    if ato == "preferencia" and "e você" in minuscula:
        return "Não tenho gostos pessoais como uma pessoa. Posso conversar sobre {tema}; o que mais te atrai nesse assunto?".format(**valores)
    if ato == "objetivo" and "não estou pedindo um plano" in mensagem:
        return "Entendi: você está colocando a vontade de {objetivo} em palavras, sem pedir passos agora. O que essa vontade significa para você?".format(**valores)
    if ato == "correcao":
        if "evento" in presentes:
            return "Entendi a atualização: {interlocutor} {evento}. Vou considerar esse relato no contexto desta sessão, sem acrescentar um motivo para a pessoa.".format(**valores)
        if "sentimento" in presentes:
            return "Entendi a correção: você disse que está {sentimento}. Vou usar o sentimento que declarou, sem substituir por uma impressão minha.".format(**valores)
        if "restricao" in presentes:
            return "Certo, o limite atual é que {restricao}. Vou deixar a disponibilidade anterior de lado neste contexto.".format(**valores)
        if "objetivo" in presentes:
            return "Seu objetivo atual é {objetivo}. Vou considerar essa correção no restante deste papo.".format(**valores)
        if "interlocutor" in presentes:
            return "Entendi a correção: a pessoa é {interlocutor}. Vou acompanhar o relato com esse detalhe atualizado.".format(**valores)
        return "Pode me dizer qual detalhe precisa ser corrigido? Você indicou o assunto, mas ainda não contou qual informação devo substituir."
    if ato == "mudar_assunto":
        if "tema" in presentes:
            return "Vamos deixar o assunto anterior em pausa e falar de {tema}. Você prefere começar por uma experiência ou por uma ideia que te interessa?".format(**valores)
        return "Certo, esse assunto fica em pausa. Pode começar o novo tema do seu jeito; não vou insistir no anterior."
    if ato == "elaborar":
        if "sugeriu esse caminho" in minuscula:
            return "Ainda não sugeri um caminho concreto. Eu estava acompanhando o relato antes de discutir uma ação, para não trocar a sua conversa por um plano que não pediu."
        if "exemplo" in minuscula:
            return "Por exemplo: você esperava {expectativa}, mas contou que {interlocutor} {evento}. Essa diferença pode importar, sem provar qual foi a intenção da outra pessoa.".format(**valores)
        ultima = next((h["texto"] for h in reversed(historico) if h["papel"] == "assistente"), "")
        if "expectativa" in ultima:
            return "Eu estava separando duas coisas: você esperava {expectativa} e contou que {interlocutor} {evento}. Reconhecer essa diferença não nos permite afirmar o motivo da outra pessoa.".format(**valores)
        return "Meu ponto era acompanhar o que esse episódio significou para você antes de sugerir uma ação. Você contou que ficou {sentimento}; isso merece espaço sem uma conclusão apressada sobre a outra pessoa.".format(**valores)
    if ato == "memoria":
        if any(p in minuscula for p in ["tempo", "limite", "restrição"]):
            return "O limite que você mencionou foi que {restricao}. É essa informação que tenho no contexto desta conversa.".format(**valores)
        if any(p in minuscula for p in ["objetivo", "meta", "quero fazer"]):
            return "Você declarou a vontade de {objetivo}. Esse é o objetivo que ficou no contexto deste papo.".format(**valores)
        if any(p in minuscula for p in ["sentindo", "sentimento"]):
            return "Você disse que estava {sentimento}. Estou recuperando o sentimento que declarou, sem acrescentar outro.".format(**valores)
        if "quem" in minuscula:
            return "Você mencionou {interlocutor} na situação que contou. Não tenho uma informação sobre a intenção dessa pessoa.".format(**valores)
        if "aconteceu" in minuscula:
            return "Você contou que {interlocutor} {evento} e que ficou {sentimento}. Esse é o episódio presente no relato desta conversa.".format(**valores)
        if "última" in minuscula:
            return "Sua última fala declarava a vontade de {objetivo} e o limite de que {restricao}. Esses são os pontos mais recentes do contexto.".format(**valores)
        if "evitar" in minuscula:
            return "Não vejo neste contexto um pedido explícito para evitar um modo de resposta. Você declarou este limite: {restricao}. Pode acrescentar o que prefere que eu evite.".format(**valores)
        if "mudou" in minuscula:
            return "Você ainda não contou uma mudança neste episódio. Falou da situação com {interlocutor}, do seu sentimento e da vontade de {objetivo}.".format(**valores)
        return "Você contou que {interlocutor} {evento}, ficou {sentimento} e queria {objetivo}. Também declarou o limite de que {restricao}.".format(**valores)
    return padrao


def gerar():
    exemplos = []
    familias = {particao: set() for particao in CENARIOS}
    sem_contexto = {"saudacao", "identidade", "compreensao", "limites", "abrir",
                   "filosofar", "encerrar", "consulta", "escrita"}
    for ato in ATOS:
        for pi, particao in enumerate(["treino", "validacao"]):
            pedidos = linhas(PEDIDOS[ato][pi])
            for fi, molde in enumerate(pedidos):
                familia = "%s:%s:%02d" % (particao, ato, fi)
                familias[particao].add(familia)
                for ci, cenario in enumerate(CENARIOS[particao]):
                    valores = valores_cenario(cenario, ci + fi)
                    mensagem, spans = compor(molde, valores)
                    historico = [] if ato in sem_contexto else historico_pessoal(valores, ci + fi)
                    # Uma declaração de evento pode ser a abertura do papo.
                    # Nesse caso o alvo só usa o que foi dito nesta mensagem.
                    if ato in {"relato", "desabafo", "objetivo", "preferencia"} and fi % 4 == 0:
                        historico = []
                    # Sem contexto, os alvos só usam argumentos da fala
                    # atual. Correções, retomadas e respostas filosóficas
                    # são condicionadas ao sentido específico do pedido.
                    alvo = resposta_exemplo(ato, mensagem, perspectiva_resposta(valores), fi + ci, historico, spans)
                    exemplos.append({"id": "%s:%02d" % (familia, ci),
                                     "familia": familia, "grupo": particao + ":" + str(ci),
                                     "tema": valores["tema"], "split": particao,
                                     "contexto": {"mensagem": mensagem, "historico": historico},
                                     "ato": ato, "spans": spans,
                                     "quadro": {"argumentos_atuais": {s["papel"]: s["texto"] for s in spans},
                                                "origem": "autoria_sintetica", "conhecimento_global": False},
                                     "resposta": alvo})
    # Pedidos curtos idênticos mudam de sentido quando o histórico muda.
    # A fonte técnica não fornece fatos nem respostas a serem memorizadas.
    contextuais = {
        "treino": ["Por quê?", "Como assim?", "Pode explicar melhor o que quis dizer?",
                    "O que sustenta essa interpretação?", "Qual parte levou a isso?",
                    "Dá um exemplo", "Pode continuar?", "E então?"],
        "validacao": ["O que está por trás dessa resposta?", "Pode desenvolver o ponto?",
                       "Como esse resultado foi obtido?", "O que significa essa parte?"],
    }
    for particao, pedidos in contextuais.items():
        for fi, mensagem in enumerate(pedidos):
            familia = "%s:consulta_contextual:%02d" % (particao, fi)
            familias[particao].add(familia)
            for ci, cenario in enumerate(CENARIOS[particao]):
                valores = valores_cenario(cenario, ci)
                historico = [
                    {"papel": "usuario", "texto": "Quero a definição técnica de " + valores["tema"] + "."},
                    {"papel": "assistente", "texto": "Esse é um pedido factual. Não há uma definição verificada disponível neste exemplo."},
                ]
                exemplos.append({"id": "%s:%02d" % (familia, ci), "familia": familia,
                                 "grupo": particao + ":" + str(ci), "tema": valores["tema"],
                                 "split": particao, "contexto": {"mensagem": mensagem, "historico": historico},
                                 "ato": "consulta", "spans": [],
                                 "quadro": {"argumentos_atuais": {}, "origem": "autoria_sintetica",
                                            "conhecimento_global": False},
                                 "resposta": "A conversa anterior era uma consulta técnica sem definição confirmada. Não tenho uma prova ou um resultado disponível para desenvolver."})
    for particao, contrastes in CONTRASTES.items():
        for fi, (ato, molde, alvo) in enumerate(contrastes):
            familia = "%s:contraste_%s:%02d" % (particao, ato, fi)
            familias[particao].add(familia)
            for ci, cenario in enumerate(CENARIOS[particao]):
                valores = valores_cenario(cenario, ci + fi)
                valores.update({"negado": valores["sentimento"],
                                "hipotetico": valores["sentimento"],
                                "citado": valores["sentimento"]})
                mensagem, spans = compor(molde, valores)
                historico = historico_pessoal(valores, ci + fi) if ato in {"escuta", "conselho"} else []
                exemplos.append({"id": "%s:%02d" % (familia, ci), "familia": familia,
                                 "grupo": particao + ":" + str(ci), "tema": valores["tema"],
                                 "split": particao, "contexto": {"mensagem": mensagem, "historico": historico},
                                 "ato": ato, "spans": spans,
                                 "quadro": {"argumentos_atuais": {s["papel"]: s["texto"] for s in spans},
                                            "origem": "autoria_sintetica", "conhecimento_global": False},
                                 "resposta": compor(alvo, perspectiva_resposta(valores))[0]})
    adicionais = [(ato, mensagem, None) for ato, pedidos in PEDIDOS_ADICIONAIS.items()
                   for mensagem in pedidos]
    adicionais += [("filosofar", mensagem, resposta) for mensagem, resposta in FILOSOFIA_ADICIONAL]
    for fi, (ato, mensagem, alvo_fixo) in enumerate(adicionais):
        familia = "treino:linguagem_adicional_%s:%03d" % (ato, fi)
        familias["treino"].add(familia)
        valores = valores_cenario(CENARIOS["treino"][fi % len(CENARIOS["treino"])], fi)
        for hi in range(3):
            historico = [] if hi == 0 else historico_pessoal(valores, hi)
            if hi == 1:
                historico = historico[:2]
            alvo = alvo_fixo or resposta_exemplo(ato, mensagem, perspectiva_resposta(valores), fi + hi, historico, [])
            exemplos.append({"id": "%s:%02d" % (familia, hi), "familia": familia,
                             "grupo": "treino:adicional:" + str(hi), "tema": valores["tema"],
                             "split": "treino", "contexto": {"mensagem": mensagem, "historico": historico},
                             "ato": ato, "spans": [],
                             "quadro": {"argumentos_atuais": {}, "origem": "autoria_sintetica",
                                        "conhecimento_global": False},
                             "resposta": alvo})
    # Idênticos sem contexto não acrescentam informação ao treinamento.
    # Conserva a primeira autoria, mas nunca apaga conflitos de rótulos.
    unicos, vistos = [], {}
    for exemplo in exemplos:
        chave = json.dumps(exemplo["contexto"], ensure_ascii=False, sort_keys=True)
        anterior = vistos.get(chave)
        if anterior:
            if anterior["ato"] != exemplo["ato"]:
                raise ValueError("Conflito de atos: " + exemplo["contexto"]["mensagem"])
            if anterior["split"] != exemplo["split"]:
                raise ValueError("Vazamento entre partições: " + exemplo["contexto"]["mensagem"])
            continue
        vistos[chave] = exemplo
        unicos.append(exemplo)
    exemplos = unicos
    for exemplo in exemplos:
        for span in exemplo["spans"]:
            assert exemplo["contexto"]["mensagem"][span["inicio"]:span["fim"]] == span["texto"]
        assert "{" not in exemplo["resposta"] and "}" not in exemplo["resposta"]
        assert len(exemplo["resposta"].split()) <= 64, exemplo["resposta"]
    por_particao = {p: sum(e["split"] == p for e in exemplos) for p in CENARIOS}
    corpus_sha = hashlib.sha256(json.dumps(exemplos, ensure_ascii=False, sort_keys=True,
                                          separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"versao": 1, "atos": ATOS, "papeis": PAPEIS,
            "metadados": {"autoria": "Sintético autoral do projeto Crivo; sem corpus externo, base factual, saídas do bot ou sondas de avaliação.",
                          "particoes": por_particao,
                          "familias": {p: len(familias[p]) for p in familias},
                          "grupos": {p: len({e["grupo"] for e in exemplos if e["split"] == p}) for p in CENARIOS},
                          "divisao": "Famílias de pedido, grupos pessoais, nomes e assuntos disjuntos entre treino e validação.",
                          "compartilhamento": "A construção composicional das respostas e o vocabulário funcional são compartilhados. Validação sintética interna não comprova conversa irrestrita.",
                          "slots": "Trechos literais da mensagem atual; Unicode com fim exclusivo. Sem emoções inferidas nem intenções alheias apresentadas como fatos.",
                          "max_palavras_resposta": max(len(e["resposta"].split()) for e in exemplos),
                          "sha256_exemplos": corpus_sha},
            "exemplos": exemplos}


if __name__ == "__main__":
    dados = gerar()
    destino = RAIZ / "curriculo_compreensao.json"
    # Uma linha por exemplo mantém autoria e diffs legíveis.
    cabecalho = {k: v for k, v in dados.items() if k != "exemplos"}
    texto = json.dumps(cabecalho, ensure_ascii=False, indent=2)[:-2]
    texto += ',\n  "exemplos": [\n'
    texto += ",\n".join("    " + json.dumps(e, ensure_ascii=False, sort_keys=True) for e in dados["exemplos"])
    texto += "\n  ]\n}\n"
    destino.write_text(texto, encoding="utf-8")
    print(json.dumps(dados["metadados"], ensure_ascii=False, indent=2))
