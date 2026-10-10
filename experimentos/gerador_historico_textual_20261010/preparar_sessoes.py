"""Sessões autorais completas; alvos alternativos, sem leitura do holdout.

Cada episódio tem seis turnos e duas realizações escritas separadamente.
Expansão lexical não é contada como variedade semântica. O histórico é
texto com papéis; não há slots/atos recebidos pela rede na inferência.
"""
import gzip
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(DIR))
from executar import gravar,sha
from dialogo_seq2seq import tokenizar,fonte_dialogo,ESPECIAIS,DialogoSeq2Seq
from arquivos_contextuais import ler_json

# (pedido, resposta autoral A, resposta autoral B). Placeholders apenas
# constroem dados offline; não são campos de entrada do modelo.
EPISODIOS=[
('capacidade_mensagem',[
('Oi. O que posso pedir aqui?','Oi! Posso ajudar com escrita, ideias e pedidos. O que você precisa?','Podemos conversar, escrever ou pensar num começo. Qual é seu pedido?'),
('Quero uma mensagem para {nome}.','O que você quer dizer para {nome}?','Qual é o assunto da mensagem para {nome}?'),
('Quero pedir um {objeto} emprestado.','{nome}, pode me emprestar seu {objeto}, por favor?','{nome}, você poderia me emprestar um {objeto}?'),
('Não quero cobrar essa ajuda.','{nome}, pode me emprestar seu {objeto}? Tudo bem se não puder.','{nome}, você poderia me emprestar um {objeto}? Pode recusar, sem problema.'),
('Agora só uma frase curta.','{nome}, pode me emprestar seu {objeto}?','{nome}, você poderia me emprestar um {objeto}?'),
('Para quem era a mensagem?','A mensagem era para {nome}.','Você queria escrever para {nome}.')]),
('contar_resultado',[
('Posso contar uma coisa do meu dia?','Pode contar. Estou acompanhando.','Claro. O que aconteceu hoje?'),
('Terminei um {objeto} e fiquei contente.','Que bom que conseguiu terminar seu {objeto}.','Terminar seu {objeto} te deixou contente.'),
('Foi difícil começar.','O que ajudou você a começar?','Qual foi a parte difícil no começo?'),
('Fiz uma parte pequena primeiro.','Essa parte pequena ajudou a fazer o restante.','Você começou pequeno e conseguiu terminar.'),
('Não quero conselho, só dividir.','Obrigado por contar como foi.','Tudo bem. Podemos só conversar sobre isso.'),
('O que eu tinha terminado?','Você terminou um {objeto}.','O {objeto} foi o que você terminou.')]),
('descansar_e_retornar',[
('Quero escrever, mas estou cansado.','Pode começar com uma frase, ou fazer uma pausa.','Veja sua energia. Uma frase pequena pode ser suficiente agora.'),
('Uma frase parece possível.','Escolha a ideia que quer contar primeiro.','Escreva uma ideia simples, sem tentar terminar tudo.'),
('Já fiz. Agora quero descansar.','Tudo bem. Seu texto pode esperar.','Faça uma pausa. Você pode voltar ao texto depois.'),
('Voltei. Qual era a tarefa?','Você estava escrevendo um texto.','Sua tarefa era escrever, começando com uma frase.'),
('Quero seguir só mais um pouco.','Escreva a próxima frase e veja se ela continua a ideia.','Continue o trecho com uma frase pequena.'),
('Como confiro se faz sentido?','Leia as frases e veja se uma continua a outra.','Confira se o trecho conta a ideia que você queria.')]),
('organizar_sem_comprar',[
('Minha mesa está cheia. Por onde começo?','Escolha uma parte da mesa para organizar.','Comece por uma parte pequena da mesa.'),
('Não quero comprar nada.','Use o espaço que já tem. Tire o que não está usando.','Separe o que precisa ficar à mão, sem comprar.'),
('Só tenho energia para uma coisa.','Escolha um objeto e deixe o restante para depois.','Organize só uma parte. Não precisa terminar agora.'),
('Guardei meu {objeto}.','Uma parte já está feita. Quer continuar ou pausar?','Você já guardou o {objeto}. Pode fazer uma pausa.'),
('Vou parar.','Tudo bem. O restante pode esperar.','Pode parar por agora. Não precisa resolver tudo hoje.'),
('O que eu já fiz?','Você guardou seu {objeto}.','O {objeto} já foi guardado.')]),
('convite_sem_cobrar',[
('Quero chamar {nome} para praticar {hobby}.','{nome}, quer praticar {hobby} comigo?','{nome}, podemos praticar {hobby} juntos?'),
('Precisa poder recusar.','{nome}, quer praticar {hobby} comigo? Tudo bem se não puder.','{nome}, podemos praticar {hobby} juntos? Pode dizer não.'),
('Isso, mas menor.','{nome}, quer praticar {hobby} comigo?','{nome}, podemos praticar {hobby} juntos?'),
('Não sei se essa pessoa aceita.','Ainda não temos essa informação.','O convite não confirma que {nome} vai participar.'),
('Como continuo se não aceitar?','Você pode respeitar a escolha e fazer uma tentativa sozinho.','Não precisa insistir. Pode praticar {hobby} sozinho por enquanto.'),
('Qual atividade eu queria combinar?','Você queria combinar {hobby}.','Era um convite para praticar {hobby}.')]),
('agradecer_sem_exagero',[
('{nome} me ajudou a revisar meu texto.','Quer escrever um agradecimento para {nome}?','Podemos escrever uma mensagem sobre essa ajuda.'),
('Quero agradecer sem exagerar.','{nome}, obrigado pela ajuda com meu texto.','{nome}, agradeço por revisar meu texto.'),
('Não invente outra coisa que aconteceu.','{nome}, obrigado pela revisão do texto.','{nome}, agradeço pela ajuda na revisão.'),
('Diz que isso fez diferença para mim.','{nome}, obrigado por revisar meu texto. Essa ajuda fez diferença para mim.','{nome}, sua ajuda com meu texto fez diferença. Obrigado.'),
('Agora só a mensagem curta.','{nome}, obrigado pela ajuda com meu texto.','{nome}, agradeço pela revisão do texto.'),
('Quem ajudou com o texto?','{nome} ajudou com seu texto.','A ajuda veio de {nome}.')]),
('prazo_sem_desculpa',[
('Não consigo entregar meu {objeto} hoje.','Quer pedir mais prazo para a entrega?','Podemos escrever uma mensagem sobre o prazo.'),
('Posso entregar amanhã.','Posso entregar amanhã. Podemos combinar assim?','A entrega pode ficar para amanhã?'),
('Não invente um motivo.','Não consigo entregar hoje. Posso entregar amanhã.','Preciso de mais prazo. Posso entregar amanhã.'),
('Faz uma frase só.','Posso entregar amanhã, em vez de hoje?','Não consigo entregar hoje; posso entregar amanhã.'),
('Mudou: posso entregar depois de amanhã.','Posso entregar depois de amanhã.','A entrega pode ficar para depois de amanhã?'),
('Qual ficou sendo o prazo?','O prazo é depois de amanhã.','Você pode entregar depois de amanhã.')]),
('recusar_convite',[
('{nome} me chamou para praticar {hobby}.','Você quer aceitar ou recusar o convite?','O que você quer responder a {nome}?'),
('Quero recusar com calma.','{nome}, obrigado pelo convite, mas não vou participar.','{nome}, agradeço por lembrar de mim. Desta vez não vou participar.'),
('Não quero explicar um motivo.','{nome}, desta vez não vou participar. Obrigado pelo convite.','{nome}, obrigado pelo convite. Não vou participar desta vez.'),
('Pode ficar mais curto?','{nome}, obrigado, mas não vou participar.','{nome}, desta vez não vou participar. Obrigado.'),
('A pessoa aceitou minha resposta.','Vocês conseguiram combinar isso sem insistir.','Você já respondeu e {nome} aceitou a resposta.'),
('Eu aceitei o convite?','Não. Você recusou o convite.','Você disse que não ia participar.')]),
('correcao_pessoa',[
('Vou entregar um {objeto} para {nome}.','Você vai entregar o {objeto} para {nome}.','Entendi: a entrega é para {nome}.'),
('Eu troquei o nome. É para {outro}.','A entrega é para {outro}, então.','Você corrigiu: vai entregar para {outro}.'),
('Para quem vou entregar?','Você vai entregar para {outro}.','O {objeto} é para {outro}.'),
('Escreve uma mensagem para essa pessoa.','{outro}, posso entregar seu {objeto} amanhã?','{outro}, podemos combinar a entrega do {objeto}?'),
('Sem escolher data, por favor.','{outro}, podemos combinar a entrega do {objeto}?','{outro}, quando posso entregar seu {objeto}?'),
('Agora diz só o nome correto.','{outro}.','O nome correto é {outro}.')]),
('preferencia_duas_partes',[
('Prefiro praticar {hobby} em casa e sozinho.','Sua preferência é praticar {hobby} em casa, sozinho.','Você prefere ficar em casa e praticar sozinho.'),
('E se eu praticasse com alguém?','Isso seria outra possibilidade, sem mudar sua preferência atual.','Você pode pensar nessa possibilidade sem escolher agora.'),
('Qual é minha preferência atual?','Você prefere praticar em casa e sozinho.','Sua escolha atual é ficar em casa, sozinho.'),
('Agora quero companhia, mas continuo em casa.','Você prefere companhia em casa agora.','Mudou só uma parte: em casa, com companhia.'),
('Resume isso.','Sua preferência agora é companhia em casa.','Você quer praticar em casa, com companhia.'),
('Mudei o lugar também?','Não. Você continua preferindo ficar em casa.','O lugar continua sendo sua casa.')]),
('emprestimo_dono',[
('{nome} me emprestou um {objeto}.','O {objeto} pertence a {nome}.','Você está usando o {objeto} de {nome} por empréstimo.'),
('Quero agradecer.','{nome}, obrigado pelo empréstimo do {objeto}.','{nome}, agradeço por me emprestar seu {objeto}.'),
('Vou devolver amanhã. Faz o aviso.','{nome}, vou devolver seu {objeto} amanhã.','{nome}, posso devolver o {objeto} amanhã?'),
('Só uma frase, sem pergunta.','Vou devolver seu {objeto} amanhã.','Amanhã devolvo o {objeto} para você.'),
('O objeto passou a ser meu?','Não. O {objeto} continua pertencendo a {nome}.','Você recebeu um empréstimo, não um presente.'),
('Quem me emprestou mesmo?','Foi {nome}.','{nome} emprestou o {objeto} para você.')]),
('nome_usuario_e_amigo',[
('Meu nome é {nome}.','Olá, {nome}!','Oi, {nome}. Podemos conversar.'),
('Meu amigo se chama {outro}.','Seu amigo se chama {outro}.','Entendi. {outro} é seu amigo.'),
('Qual é meu nome?','Você se chama {nome}.','Seu nome é {nome}.'),
('Quem é meu amigo?','Seu amigo é {outro}.','O nome do seu amigo é {outro}.'),
('Quero pedir ajuda a essa pessoa.','{outro}, você pode me ajudar, por favor?','{outro}, podemos conversar sobre uma ajuda?'),
('Você confundiu meu nome com o nome do amigo?','Seu nome é {nome}; seu amigo é {outro}.','Você é {nome}. {outro} é a outra pessoa.')]),
('sem_nome_usuario',[
('Meu amigo se chama {nome}.','Entendi. Seu amigo é {nome}.','Você mencionou seu amigo {nome}.'),
('Como eu me chamo?','Você ainda não disse seu nome.','Não tenho seu nome. Pode me dizer?'),
('Eu sou {outro}.','Olá, {outro}!','Agora sei: seu nome é {outro}.'),
('Qual pessoa eu tinha mencionado antes?','Você mencionou seu amigo {nome}.','Antes, você falou de {nome}.'),
('E meu nome é qual?','Seu nome é {outro}.','Você se chama {outro}.'),
('Diz os dois, sem misturar.','Você é {outro}, e seu amigo é {nome}.','Seu nome é {outro}; {nome} é seu amigo.')]),
('hipotese_nao_fato',[
('Eu trabalho sozinho.','Você trabalha sozinho atualmente.','Entendi: por enquanto, você trabalha sozinho.'),
('Talvez eu chame {nome} para ajudar.','Isso ainda é uma possibilidade.','{nome} pode ajudar, mas ainda não está confirmado.'),
('Se a pessoa ajudasse, como dividir?','Vocês poderiam escolher uma parte para cada um.','Se {nome} ajudar, vocês podem combinar uma divisão.'),
('Já posso dizer que trabalhamos juntos?','Não. Você só considerou convidar {nome}.','Ainda não. O trabalho com {nome} não está confirmado.'),
('Escreve o convite.','{nome}, quer me ajudar nessa tarefa? Tudo bem se não puder.','{nome}, podemos dividir essa tarefa? Pode recusar.'),
('Qual é a situação por enquanto?','Você continua trabalhando sozinho.','A ajuda de {nome} ainda é uma possibilidade.')]),
('nao_saber_pensamento',[
('{nome} não respondeu minha mensagem.','Ainda não sabemos o motivo.','Você sabe que {nome} não respondeu, mas não o motivo.'),
('Então a pessoa está brava comigo?','Não dá para afirmar isso só pelo silêncio.','Essa é uma hipótese, não uma certeza.'),
('O que faço sem cobrar?','Pode perguntar se {nome} recebeu a mensagem.','Você pode esperar ou mandar uma pergunta curta.'),
('Escreve essa pergunta.','{nome}, você recebeu minha mensagem?','{nome}, pode me dizer se recebeu a mensagem?'),
('Não invente que a pessoa respondeu.','Ainda não temos uma resposta de {nome}.','Você disse que {nome} não respondeu.'),
('Qual parte é certeza?','{nome} não respondeu sua mensagem.','A falta de resposta é o que você contou.')]),
('historia_objeto_deixado',[
('Quero um conto curto com {nome}.','Qual é a ideia do conto?','O que acontece com {nome} no começo?'),
('{nome} acha um {objeto} na {lugar}.','Na {lugar}, {nome} encontrou um {objeto} deixado no chão.','{nome} parou na {lugar}. Um {objeto} estava ali, sem ninguém por perto.'),
('Continua sem levar o objeto.','{nome} deixou o {objeto} no lugar e procurou uma pista.','Sem levar o {objeto}, {nome} olhou ao redor.'),
('A pista não ajuda.','A pista não explicou nada. {nome} decidiu esperar.','{nome} não encontrou uma resposta na pista e voltou ao {objeto}.'),
('Termina com a busca aberta.','{nome} deixou um aviso e partiu. A busca continuava aberta.','O {objeto} ficou na {lugar}. {nome} ainda queria saber de quem era.'),
('Quem era a personagem?','A personagem era {nome}.','O conto acompanhava {nome}.')]),
('historia_som',[
('Começa com {nome} ouvindo um {objeto}.','{nome} ouviu um som vindo do {objeto}.','O {objeto} fazia barulho. {nome} parou para ouvir.'),
('O som para.','O {objeto} ficou quieto, e {nome} ouviu o ambiente.','De repente, o {objeto} parou. {nome} esperou outro som.'),
('Não coloque outra pessoa.','{nome} ficou sozinho, tentando entender o silêncio.','Sem ninguém por perto, {nome} olhou o {objeto} com calma.'),
('A pessoa não consegue resolver isso.','{nome} não encontrou uma resposta. O {objeto} continuou quieto.','O silêncio permaneceu. {nome} não conseguiu explicar o que aconteceu.'),
('Fecha sem fazer o som voltar.','{nome} guardou o {objeto}. O silêncio ficou no lugar.','O {objeto} não voltou a fazer barulho, e {nome} partiu.'),
('O som voltou no final?','Não. O {objeto} continuou quieto.','O conto terminou sem o som voltar.')]),
('historia_porta',[
('{nome} encontra uma porta fechada na {lugar}.','Na {lugar}, {nome} tentou abrir a porta, mas ela continuou fechada.','{nome} chegou à {lugar} e parou diante da porta fechada.'),
('Sem magia, dá uma próxima ação.','{nome} bateu na porta e esperou.','{nome} procurou outra passagem, sem forçar a porta.'),
('Ninguém vem abrir.','Ninguém veio. {nome} olhou ao redor.','{nome} esperou, mas a porta permaneceu fechada.'),
('Quero que tente uma janela.','{nome} encontrou uma janela e conferiu se podia passar.','A janela chamou sua atenção. {nome} foi olhar com calma.'),
('A janela também está fechada. Termina.','A janela estava fechada. {nome} partiu sem entrar.','{nome} não conseguiu entrar e deixou a {lugar} para trás.'),
('A pessoa conseguiu entrar?','Não. {nome} partiu sem entrar.','A porta e a janela ficaram fechadas.')]),
('historia_chuva',[
('{nome} leva um {objeto} pela {lugar}.','{nome} atravessava a {lugar} com o {objeto}.','Na {lugar}, {nome} carregava um {objeto} com cuidado.'),
('Começa uma chuva.','{nome} procurou abrigo para proteger o {objeto}.','A chuva chegou, e {nome} parou para guardar o {objeto}.'),
('Não deixe o objeto molhar.','O {objeto} ficou protegido enquanto {nome} esperava.','{nome} manteve o {objeto} no abrigo.'),
('A chuva não para ainda.','{nome} continuou no abrigo, sem retomar o caminho.','A espera ficou longa, mas o {objeto} permanecia protegido.'),
('Termina ainda no abrigo.','{nome} ficou no abrigo com o {objeto}, esperando a chuva diminuir.','O caminho teria de esperar. {nome} não saiu do abrigo.'),
('A personagem já retomou o caminho?','Não. {nome} continuou no abrigo.','O conto terminou antes de retomar o caminho.')]),
('historia_perda',[
('{nome} perdeu um {objeto} na {lugar}.','{nome} voltou à {lugar} para procurar seu {objeto}.','A busca pelo {objeto} levou {nome} de volta à {lugar}.'),
('Continua sem encontrar.','{nome} olhou ao redor, mas não encontrou o {objeto}.','A busca continuou, sem uma pista do {objeto}.'),
('A pessoa deixa um aviso.','{nome} deixou um aviso sobre o {objeto} perdido.','Na {lugar}, {nome} pediu ajuda por escrito.'),
('Não invente uma resposta ao aviso.','Ninguém respondeu ao aviso por enquanto.','{nome} esperou, mas não recebeu uma resposta.'),
('Termina voltando para casa.','{nome} voltou para casa sem o {objeto}. A busca ficou aberta.','O {objeto} continuou perdido quando {nome} partiu.'),
('O objeto foi encontrado?','Não. O {objeto} ainda estava perdido.','{nome} terminou a busca sem encontrar o {objeto}.')]),
('historia_e_mensagem',[
('Quero uma história com {nome} na {lugar}.','{nome} chegou à {lugar} e encontrou uma porta fechada.','Na {lugar}, {nome} procurava uma passagem.'),
('Ainda não deixe entrar.','{nome} esperou do lado de fora, sem entrar.','A passagem continuava fechada para {nome}.'),
('Pausa o conto. Quero agradecer a {outro}.','{outro}, obrigado pela ajuda.','{outro}, agradeço por ajudar.'),
('Agora volta à história.','{nome} ainda estava na {lugar}, tentando encontrar uma passagem.','De volta ao conto, {nome} continuava sem conseguir entrar.'),
('Termina sem abrir a porta.','{nome} partiu, deixando a porta fechada para trás.','Sem entrar, {nome} decidiu voltar em outro dia.'),
('Quem era a personagem do conto?','A personagem era {nome}.','Era {nome}, na {lugar}.')]),
('ambiente_e_titulo',[
('Escreve uma cena na {lugar} vazia.','A {lugar} estava vazia. A luz mudava devagar.','Na {lugar}, o silêncio deixava cada canto mais visível.'),
('Não coloque pessoas.','A {lugar} permaneceu vazia, com o vento ao redor.','Ninguém apareceu. A luz continuou mudando na {lugar}.'),
('Quero um detalhe de som.','O vento fazia um barulho baixo na {lugar}.','Um som de vento atravessava a {lugar} vazia.'),
('Mantém uma sensação calma.','O vento passou devagar. A {lugar} parecia tranquila.','O som baixo não mudou a calma da {lugar}.'),
('Dá um título curto.','O silêncio da {lugar}','O vento na {lugar}'),
('Qual era o lugar da cena?','A cena se passava na {lugar}.','O lugar era a {lugar}.')]),
('mudanca_de_lugar',[
('O conto começa com {nome} na {lugar}.','{nome} chegou à {lugar} e olhou ao redor.','Na {lugar}, {nome} esperava uma descoberta.'),
('Troque o lugar para {outra}.','Na {outra}, {nome} encontrou uma pista.','{nome} olhou ao redor da {outra}.'),
('Qual é o cenário agora?','O cenário agora é a {outra}.','O conto se passa na {outra} agora.'),
('Continua com a mesma pessoa.','{nome} seguiu a pista pela {outra}.','Na {outra}, {nome} tentou entender a pista.'),
('Sem resolver a pista ainda.','{nome} não encontrou uma resposta e continuou procurando.','A pista continuou sem explicação para {nome}.'),
('Quem está nesse cenário?','{nome} está na {outra}.','A personagem continua sendo {nome}.')]),
('pedido_esclarecido',[
('Preciso resolver uma coisa.','Qual coisa você quer resolver?','Me conte o pedido para eu poder ajudar.'),
('Uma mensagem para {nome}.','O que você quer dizer a {nome}?','Qual é o assunto dessa mensagem?'),
('Quero pedir ajuda com meu {objeto}.','{nome}, pode me ajudar com meu {objeto}?','{nome}, você poderia olhar meu {objeto}, por favor?'),
('Não quero que pareça uma ordem.','{nome}, pode me ajudar com meu {objeto}? Tudo bem se não puder.','{nome}, você poderia me ajudar? Pode dizer não.'),
('Isso, agora só uma frase.','{nome}, pode me ajudar com meu {objeto}, por favor?','{nome}, você poderia olhar meu {objeto}?'),
('Qual era o pedido mesmo?','Você queria pedir ajuda com seu {objeto}.','Era um pedido de ajuda para {nome}.')]),
('revisao_por_partes',[
('Quero revisar meu texto.','Pode começar por um parágrafo.','Vamos conferir uma parte do texto por vez.'),
('Primeiro olho o quê?','Confira se o trecho diz o que você queria.','Comece pelo sentido das frases.'),
('Depois disso?','Procure frases difíceis e repetições.','Depois, veja se há palavras repetidas sem precisar.'),
('Não tenho tempo para o texto todo.','Revise só um trecho agora.','Escolha uma parte pequena e deixe o restante para depois.'),
('Vou mandar assim mesmo?','Confira pelo menos o trecho que considera mais importante.','Você pode enviar depois dessa revisão pequena, sem prometer que está perfeito.'),
('O que estávamos fazendo?','Estávamos revisando seu texto por partes.','Você queria revisar o texto antes de enviar.')]),
('erro_sem_fracasso',[
('Tentei {hobby} e não gostei do resultado.','Qual parte do resultado te incomodou?','O que ficou diferente do que você esperava?'),
('Eu queria acertar tudo de primeira.','Essa expectativa pode tornar a tentativa pesada.','Acertar tudo de primeira não é uma obrigação.'),
('Então não preciso continuar hoje?','Você pode fazer uma pausa e rever a escolha depois.','Não precisa continuar agora só porque começou.'),
('Quero tentar outra vez amanhã.','Pode escolher uma parte pequena para a nova tentativa.','Amanhã você pode testar um começo diferente.'),
('Sem prometer que vai dar certo.','A tentativa pode ajudar a aprender, sem garantia de resultado.','Você pode observar o que muda, sem prometer um acerto.'),
('Qual atividade eu tinha tentado?','Você tinha tentado {hobby}.','A tentativa foi de {hobby}.')]),
('decisao_e_opcoes',[
('Não sei se continuo ou faço uma pausa.','O que está tornando essa escolha difícil?','Você quer continuar, pausar ou tentar outra coisa?'),
('Estou cansado, mas quero terminar meu {objeto}.','Você pode separar uma parte pequena ou descansar primeiro.','Veja sua energia antes de decidir sobre o {objeto}.'),
('Quero uma opinião, não certeza.','Eu consideraria uma pausa curta antes de continuar.','Uma tentativa pequena pode ser suficiente por agora.'),
('Vou descansar primeiro.','Tudo bem. O {objeto} pode esperar.','Você escolheu fazer uma pausa antes de continuar.'),
('Isso significa que abandonei?','Não. Você disse que vai descansar primeiro.','Uma pausa não confirma que você abandonou o {objeto}.'),
('Qual foi minha escolha?','Você escolheu descansar primeiro.','Sua escolha foi fazer uma pausa.')]),
('contar_sem_instrucoes',[
('Quero conversar, sem um plano.','Podemos só conversar. Como foi seu dia?','Tudo bem. O que você quer contar?'),
('Hoje pratiquei {hobby}.','Como foi essa tentativa de {hobby}?','O que você sentiu enquanto praticava?'),
('Foi tranquilo. Não quero dicas.','Tudo bem. Quer contar qual parte mais gostou?','Posso acompanhar sem transformar isso em conselho.'),
('Gostei de fazer sem pressa.','Fazer sem pressa foi importante para você.','Você encontrou um ritmo mais calmo.'),
('Pergunta só mais uma coisa.','O que ficou na sua cabeça depois dessa tentativa?','Qual parte você gostaria de contar de novo?'),
('Qual atividade mencionei?','Você mencionou {hobby}.','A atividade era {hobby}.')]),
('entrega_antes_convite',[
('Preciso entregar um {objeto} amanhã.','O prazo do {objeto} é amanhã.','Você tem uma entrega para amanhã.'),
('Quero convidar {nome} para conversar.','{nome}, podemos conversar um pouco?','{nome}, quer conversar comigo?'),
('Isso altera o prazo?','Não. O prazo continua sendo amanhã.','O convite não mudou a entrega do {objeto}.'),
('Sem prometer terminar antes.','A entrega fica para amanhã.','Você pode manter o prazo que declarou.'),
('Quero avisar que preciso de uma pausa.','Preciso de uma pausa. Depois volto ao {objeto}.','Vou fazer uma pausa antes de continuar o {objeto}.'),
('Qual compromisso ainda existe?','Você precisa entregar o {objeto} amanhã.','A entrega do {objeto} para amanhã continua.')]),
('devolver_e_consequencia',[
('{nome} encontrou um {objeto} perdido.','{nome} começou a procurar quem tinha perdido o {objeto}.','O {objeto} parecia importante. {nome} procurou uma pista.'),
('A pessoa consegue devolver.','{nome} devolveu o {objeto} e recebeu um agradecimento.','A devolução do {objeto} encerrou a busca de {nome}.'),
('Quero uma consequência pequena.','Depois da devolução, {nome} recebeu um convite para conversar.','Devolver o {objeto} abriu espaço para uma nova conversa.'),
('Não transforme em outra aventura.','{nome} ficou para conversar, sem começar uma nova busca.','A história continuou numa conversa calma.'),
('Termina com calma.','{nome} voltou para casa contente com a devolução.','A conversa terminou, e {nome} partiu sem pressa.'),
('O objeto ainda está perdido?','Não. {nome} devolveu o {objeto}.','A busca terminou com a devolução.')]),
('objeto_corrigido',[
('Escolhi um {objeto} para levar à {lugar}.','Você escolheu levar um {objeto}.','O {objeto} é sua escolha para a {lugar}.'),
('Troquei. Quero levar um {novo_objeto}.','Sua escolha agora é um {novo_objeto}.','Você trocou o {objeto} pelo {novo_objeto}.'),
('Qual foi a escolha final?','Sua escolha final foi um {novo_objeto}.','Você escolheu o {novo_objeto} por último.'),
('Escreve uma frase dizendo que vou levar.','Vou levar um {novo_objeto} à {lugar}.','O {novo_objeto} vai comigo para a {lugar}.'),
('Sem dizer que já cheguei.','Você ainda está falando do que vai levar.','A chegada à {lugar} não está confirmada.'),
('Então qual objeto vou levar?','Você vai levar um {novo_objeto}.','O objeto escolhido é o {novo_objeto}.')]),
('pessoa_silencio',[
('{nome} ficou em silêncio depois do meu pedido.','Você ainda não sabe o que {nome} pensa.','O silêncio não explica sozinho o motivo.'),
('Pode ser que não tenha entendido?','Essa é uma possibilidade.','Pode ser, mas não temos informação para confirmar.'),
('Como pergunto sem inventar o motivo?','{nome}, meu pedido ficou claro?','{nome}, quer que eu explique melhor o pedido?'),
('Só a pergunta curta.','{nome}, meu pedido ficou claro?','Você entendeu meu pedido, {nome}?'),
('Ainda não respondeu.','Ainda não há uma resposta de {nome}.','Por enquanto, você só sabe que {nome} ficou em silêncio.'),
('Você sabe o que a pessoa pensa?','Não tenho como saber isso.','Não podemos tratar uma hipótese como certeza.')]),
('correcao_autoria',[
('Eu disse que {nome} escreveu meu texto.','Você mencionou {nome} como a pessoa que escreveu.','Entendi o que você contou sobre o texto.'),
('Corrigindo: fui eu que escrevi.','Foi você quem escreveu o texto.','O texto foi escrito por você.'),
('Essa pessoa só ajudou a revisar.','{nome} ajudou na revisão, sem escrever o texto.','A revisão foi de {nome}; a escrita foi sua.'),
('Quem escreveu, então?','Você escreveu o texto.','A escrita foi sua.'),
('Escreve uma frase agradecendo a revisão.','{nome}, obrigado pela revisão do meu texto.','{nome}, agradeço por ajudar a revisar meu texto.'),
('Quem ajudou na revisão?','{nome} ajudou a revisar.','A ajuda na revisão veio de {nome}.')]),
('escrita_sem_apresentacao',[
('Escreve sobre um {objeto} deixado na {lugar}.','O {objeto} ficou na {lugar}, onde ninguém olhava.','Na {lugar}, o {objeto} parecia fazer parte do silêncio.'),
('Sem começar apresentando pessoas.','O {objeto} continuou ali, esperando ser notado.','A luz mudou sobre o {objeto}, sem ninguém chegar.'),
('Acrescenta só um detalhe.','O vento moveu uma folha perto do {objeto}.','Uma folha ficou no chão, ao lado do {objeto}.'),
('Não leve o objeto embora.','O {objeto} permaneceu no mesmo lugar.','Ninguém levou o {objeto} da {lugar}.'),
('Quero um título simples.','O {objeto} esquecido','O silêncio ao redor do {objeto}'),
('Onde ficou o objeto?','O {objeto} ficou na {lugar}.','Ele permaneceu na {lugar}.')]),
('esperar_sem_garantia',[
('{nome} pode chegar amanhã.','A chegada de {nome} ainda é uma possibilidade.','Você disse que {nome} pode chegar amanhã.'),
('Isso é uma certeza?','Não. Pode chegar não significa chegada confirmada.','Ainda não está confirmado que {nome} chega.'),
('Quero perguntar se vem.','{nome}, você vem amanhã?','{nome}, sua chegada amanhã está confirmada?'),
('Sem prometer nada por essa pessoa.','A pergunta não confirma que {nome} vai chegar.','Podemos perguntar, sem garantir a resposta de {nome}.'),
('Não respondeu ainda.','Então a chegada continua sem confirmação.','Ainda não temos a resposta de {nome}.'),
('Qual dia eu tinha mencionado?','Você mencionou amanhã.','O dia considerado era amanhã.')]),
('moradia_e_tarefas',[
('Eu moro sozinho.','Atualmente você mora sozinho.','Entendi sua situação atual.'),
('E se morasse com {nome}?','Vocês poderiam combinar uma divisão das tarefas.','Se morasse com {nome}, poderia conversar sobre as tarefas.'),
('Como evitar cobrança nessa hipótese?','Uma conversa sobre o que cada um pode fazer ajudaria.','Vocês poderiam combinar uma divisão possível, sem tratar ajuda como obrigação.'),
('Ainda não decidi mudar.','Sua situação atual não mudou.','Morar com {nome} continua sendo uma hipótese.'),
('Qual é minha situação atual?','Você mora sozinho.','Atualmente você continua morando sozinho.'),
('Resume a hipótese, sem transformar em fato.','Se morasse com {nome}, poderia dividir tarefas.','Você considerou morar com {nome}, mas não decidiu mudar.')]),
]

SUPORTE_LEXICAL=[
    ('Quero explicar um pedido e não sei por onde começar.', 'Explique a situação em uma frase simples.'),
    ('Minha mensagem ficou difícil de entender.', 'Veja o que não ficou claro e explique essa parte.'),
    ('Como confiro se a pessoa recebeu bem meu pedido?', 'Pode perguntar se a pessoa entendeu o pedido.'),
    ('Você conhece as ideias de outra pessoa sem perguntar?', 'Não sei o que essa pessoa pensa.'),
    ('O silêncio tem só um motivo possível?', 'Não. O silêncio não explica sozinho o motivo.'),
    ('Eu ainda não sei a resposta ao meu convite.', 'Podemos perguntar para confirmar, sem inventar uma resposta.'),
    ('A pessoa talvez venha, mas não respondeu.', 'A chegada continua sem confirmação.'),
    ('Qual é um jeito de retomar o que eu estava dizendo?', 'Então, podemos voltar ao assunto que você queria contar.'),
    ('Uma pessoa pode vir amanhã, mas ainda não sei.', 'Não dá para garantir que a pessoa chega amanhã.'),
    ('Eu estava pensando em um dia, mas não decidi.', 'Esse era o dia considerado, não uma escolha confirmada.'),
    ('Estou organizando um pedido difícil de explicar.', 'Começar por uma parte pequena ajudaria a deixar o pedido claro.'),
    ('Eu moro sozinho, mas penso em mudar de casa.', 'Morar em outro lugar ainda é uma possibilidade.'),
    ('Minha casa é onde moro sozinho.', 'Você está morando sozinho atualmente.'),
    ('Preciso decidir sobre minha casa, sem promessa de acertar.', 'Você pode pensar em como quer morar, sem decidir tudo agora.'),
]


def construir():
    destino=DIR/'corpus_sessoes.json.gz'
    if destino.exists():raise ValueError('Preservar corpus existente')
    nomes=['Alina','Breno','Cecília','Davi','Elisa','Fábio','Giovana','Heitor']
    objetos=['caderno','mapa','livro','quadro','relógio','pote','barco','casaco']
    lugares=['biblioteca','oficina','praça','cozinha','escola','sala']
    hobbies=['desenho','leitura','fotografia','escrita','pintura','jardinagem']
    # Quatro episódios inteiros reservados ao desenvolvimento, sem treino.
    dev={'pessoa_silencio','correcao_autoria','esperar_sem_garantia','moradia_e_tarefas'}
    novas=[]
    for familia,turnos in EPISODIOS:
        if len(turnos)!=6:raise ValueError('Episódio precisa de seis turnos')
        for split,usados in [('treino',nomes),('validacao',['Nubira-21','Ocrélio-32'])]:
            if (familia in dev)!=(split=='validacao'):continue
            for j,nome in enumerate(usados):
                valores=dict(nome=nome,outro=usados[(j+1)%len(usados)],objeto=objetos[j%8],
                    novo_objeto=objetos[(j+3)%8],lugar=lugares[j%6],outra=lugares[(j+2)%6],hobby=hobbies[j%6])
                for realizacao in [0,1]:
                    hist=[]
                    for k,(pedido,a,b) in enumerate(turnos):
                        mensagem=pedido.format(**valores)
                        # Variações de cortesia não são contadas como famílias.
                        if realizacao==1:
                            inicio=mensagem if mensagem.startswith((nome,valores['outro'])) else mensagem[0].lower()+mensagem[1:]
                            mensagem='Por favor, '+inicio
                        resposta=(a if realizacao==0 else b).format(**valores)
                        novas.append(dict(id=f'sessao-{familia}-{split}-{j}-{realizacao}-{k}',
                            familia=familia,grupo='sessao_completa',split=split,mensagem=mensagem,
                            historico=hist.copy(),resposta=resposta,episodio=f'{familia}-{j}-{realizacao}',turno=k+1))
                        hist.extend([dict(papel='usuario',texto=mensagem),dict(papel='assistente',texto=resposta)])
    legado=ler_json(DIR/'corpus_contrastes.json.gz')['exemplos'];por_familia=defaultdict(list)
    for e in legado:
        if e['split']=='treino':por_familia[e['familia']].append(e)
    # Memória de dados de treino, não modelo maior: replay limitado por família.
    replay=[dict(e,grupo='replay_legado') for _,es in sorted(por_familia.items()) for e in es[::max(1,len(es)//8)][:8]]
    antigos_dev=[e for e in legado if e['split']=='validacao']
    suporte=[dict(id=f'apoio-lexical-{i}',familia='apoio_lexical',grupo='apoio_lexical',split='treino',
        mensagem=q,historico=[],resposta=a) for i,(q,a) in enumerate(SUPORTE_LEXICAL)]
    exemplos=replay+antigos_dev+novas+suporte;unicos={}
    for e in exemplos:
        key=json.dumps([e['mensagem'],e.get('historico',[])],sort_keys=True,ensure_ascii=False)
        if key in unicos and (unicos[key]['resposta']!=e['resposta'] or unicos[key]['split']!=e['split']):
            raise ValueError(f'Entrada conflitante: {e["id"]}')
        unicos.setdefault(key,e)
    exemplos=list(unicos.values());origem=ler_json(DIR/'checkpoint_contrastes.json.gz')
    velho=origem['vocabulario'];necessarios=set(ESPECIAIS)
    # Seleção apenas por treino: proteger todo alvo antigo não copiável,
    # então reservar espaço para as flexões próprias do novo corpus.
    for e in [e for e in legado if e['split']=='treino']+[e for e in novas if e['split']=='treino']+suporte:
        necessarios.update(set(tokenizar(e['resposta']))-set(fonte_dialogo(e['mensagem'],e.get('historico',[]),512)))
    if len(necessarios)>720:raise ValueError(f'Vocabulário necessário excede capacidade: {len(necessarios)}')
    novos_tokens=sorted(necessarios-set(velho))
    livres=[i for i in range(len(velho)-1,len(ESPECIAIS)-1,-1) if velho[i] not in necessarios]
    if len(novos_tokens)>len(livres):raise ValueError('Não há entradas livres suficientes')
    vocabulario=list(velho);trocas=[]
    for i,palavra in zip(livres,novos_tokens):
        trocas.append(dict(indice=i,antes=velho[i],depois=palavra));vocabulario[i]=palavra
    vocab=set(vocabulario)
    impossiveis=Counter();longas=[]
    for e in exemplos:
        fonte=fonte_dialogo(e['mensagem'],e.get('historico',[]),512)
        impossiveis.update(set(tokenizar(e['resposta']))-vocab-set(fonte))
        if len(fonte)>192 or len(tokenizar(e['resposta']))+1>64:longas.append(e['id'])
    if impossiveis or longas:raise ValueError(f'Alvos não geráveis: {impossiveis}; fontes/respostas longas: {longas[:8]}')
    # Pesos comuns não são associados a outras palavras; apenas as entradas
    # substituídas recebem inicialização aleatória própria. Dimensões iguais.
    from treinar_dialogo_seq2seq import inicializar
    import numpy as np
    # Preservar também os valores JSON originais das entradas mantidas.
    # A conversão float32 será feita pelo treinador, como na origem.
    parametros={k:np.asarray(v,dtype=np.float64).copy() for k,v in origem['pesos'].items()}
    aleatorios=inicializar(vocabulario,24,16,128,179)
    for t in trocas:
        i=t['indice'];parametros['E'][i]=aleatorios['E'][i]
        parametros['O'][:,i]=aleatorios['O'][:,i];parametros['bo'][i]=aleatorios['bo'][i]
    base=dict(origem);base['vocabulario']=vocabulario;base['pesos']={k:a.tolist() for k,a in parametros.items()}
    base.update(aprovado=False,ativo_no_chat=False,experimento='inicializacao-lexical-propria-sessoes',
        realocacao_vocabulario=dict(origem_sha256=sha(DIR/'checkpoint_contrastes.json.gz'),semente=179,trocas=trocas,
            limite='Seleção só por treino; preserva pesos/índices das palavras mantidas. Não é ampliação de vocabulário ou parâmetros.'))
    DialogoSeq2Seq(base)
    (DIR/'inicializacao_sessoes.json.gz').write_bytes(gzip.compress((json.dumps(base,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0))
    gravar('realocacao_vocabulario_sessoes.json',base['realocacao_vocabulario'])
    dados=dict(origem='Episódios autorais de seis turnos, duas realizações por resposta; expansão lexical offline; replay de treino limitado e desenvolvimento antigo preservado',
        limite='Não diálogos humanos; expansões e cortesia não são novas capacidades. Não usa holdout nem catálogo na inferência.',exemplos=exemplos)
    destino.write_bytes(gzip.compress((json.dumps(dados,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0))
    sem_lexico=[dict(mensagem=q,respostas=[a,b]) for _,ts in EPISODIOS for q,a,b in ts]
    gravar('corpus_sessoes_estatisticas.json',dict(criado_em_utc=datetime.now(timezone.utc).isoformat(),
        episodios_autorais=len(EPISODIOS),episodios_treino=len(EPISODIOS)-len(dev),episodios_desenvolvimento=sorted(dev),
        turnos_por_episodio=6,pares_autorais_antes_expansao=len(sem_lexico),
        respostas_deslexicalizadas_autorais=len({a for _,ts in EPISODIOS for _,*rs in ts for a in rs}),
        splits=dict(Counter(e['split'] for e in exemplos)),novos=dict(Counter(e['split'] for e in novas)),
        replay_legado=len(replay),apoio_lexical_autoral=len(suporte),desenvolvimento_antigo_preservado=len(antigos_dev),
        exemplos_total=len(exemplos),vocabulario_tamanho=720,entradas_realocadas=len(trocas),parametros_preservados=81433,
        fonte_max_tokens=max(len(fonte_dialogo(e['mensagem'],e.get('historico',[]),512)) for e in exemplos),
        alvos_nao_geraveis={},sha256_corpus=sha(destino),
        limite='Duas realizações autorais de cada resposta, não dois padrões semânticos distintos; quatro famílias inteiras só no desenvolvimento.'))
    print(json.dumps(ler_json(DIR/'corpus_sessoes_estatisticas.json'),ensure_ascii=False,indent=2))


if __name__=='__main__':
    construir()
