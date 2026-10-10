"""Reformulações autorais offline; nenhum normalizador chega à inferência.

Não lê as sondas congeladas para construir exemplos. Mantém as 100
reformulações anteriores no desenvolvimento, fora do treino. Nome trocado
ou prefixo não é contado como novo padrão de pedido.
"""
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(DIR))
from preparar_corpus import PADROES,NOMES,OBJETOS,LUGARES,CORES,DIAS,HOBBIES,RAIZ
from preparar_rodada2 import CONTEXTOS
from dialogo_seq2seq import tokenizar,fonte_dialogo

VARIANTES=[
    ('E aí, tem como bater um papo?', 'oi, queria conversar um pouquinho', 'Posso ficar aqui e falar do meu dia?'),
    ('Como você ajuda alguém que chegou agora?', 'Pra que posso usar você numa conversa?', 'Não conheço o Crivo. Me conta o que consegue fazer.'),
    ('Não consigo escolher um começo, tenho muita coisa na cabeça.', 'Tô perdido com tanto pensamento. Podemos começar por uma coisa?', 'Queria falar, mas está tudo misturado na minha cabeça.'),
    ('Sinto que me cobro para já começar acertando.', 'Eu esperava conseguir de primeira e travei.', 'Talvez o problema seja esperar que a primeira tentativa fique boa.'),
    ('Me alegrou terminar, mesmo sem ninguém se importar.', 'Queria que alguém percebesse, mas fiquei feliz de concluir.', 'Consegui terminar e isso me animou, ainda que tenham ignorado.'),
    ('Você tem lembranças de alguém de quem sente falta?', 'Sentir falta de uma pessoa é algo que você vive?', 'Queria saber se saudade é uma experiência sua.'),
    ('O que você sugeriria sobre começar algo diferente sem acertar tudo?', 'Me ajuda a pensar se vale experimentar uma novidade.', 'Na sua avaliação, errar impede tentar uma coisa nova?'),
    ('O medo é de passarem a rir de mim.', 'Acho que vou parecer bobo quando tentar.', 'Tenho vergonha de como os outros vão me ver tentando.'),
    ('Hoje não quero dica, só companhia no papo.', 'Me escuta um pouco sem tentar consertar as coisas.', 'Não preciso de conselho agora; estou sem energia.'),
    ('Não preciso de mais nada, só queria contar.', 'Era só para compartilhar uma coisa boa.', 'Eu queria dividir essa alegria, sem pedir ajuda.'),

    ('Qual foi o nome que eu te disse?', 'Lembra como eu me apresentei?', 'me diz meu nome de novo'),
    ('Quem eu disse que é meu amigo?', 'Você lembra o nome desse meu amigo?', 'Como se chama a pessoa que apresentei como amigo?'),
    ('O que entreguei para essa pessoa?', 'Lembra qual coisa eu levei?', 'Diz o objeto e a pessoa para quem levei.'),
    ('Onde está a pessoa que mencionei?', 'Qual lugar foi mencionado para essa pessoa?', 'Em que lugar essa pessoa está agora?'),
    ('Me lembra qual atividade eu queria fazer.', 'Do que eu tinha vontade de praticar?', 'Qual era meu plano de atividade?'),
    ('Em qual dia eu gostaria que fosse?', 'Lembra minha escolha de dia?', 'Que dia eu disse que era melhor para mim?'),
    ('Você lembra do que eu gosto?', 'Que preferência eu contei?', 'Qual escolha combina com o que falei?'),
    ('Eu tenho essa coisa ou é a outra pessoa?', 'Quem está com o objeto?', 'De quem foi dito que tem isso?'),
    ('Esse objeto é de quem mesmo?', 'Quem é o dono da coisa emprestada?', 'De quem eu peguei isso emprestado?'),
    ('Lembra a entrega e o dia que combinei?', 'O que ficou combinado para eu entregar?', 'Qual é o objeto da entrega e quando ela acontece?'),

    ('Depois de corrigir, quem é meu amigo?', 'Eu tinha falado errado o nome. Qual é o certo?', 'Use o último nome que eu disse para essa amizade.'),
    ('Qual preferência vale depois que mudei de ideia?', 'Não use a escolha antiga: do que eu gosto agora?', 'Me lembra o que escolhi por último.'),
    ('Depois da troca, qual objeto ficou?', 'Não é mais o primeiro. Qual escolhi no fim?', 'O que eu resolvi escolher afinal?'),
    ('O dia mudou. Quando vou encontrar essa pessoa?', 'Use o prazo mais recente do encontro.', 'Diz a data atual desse encontro, não a anterior.'),
    ('Quero trocar o lugar para {outro_lugar}. Mostre a cena de novo.', 'A cena deve acontecer na {outro_lugar}, e não no lugar anterior.', 'Reescreva uma frase colocando o cenário na {outro_lugar}.'),
    ('Agora prefiro praticar acompanhado. Relembre minha escolha.', 'Não é mais sozinho: quero outra pessoa por perto.', 'Pode atualizar que eu quero companhia para essa atividade?'),
    ('Não estava estragado, era só a montagem. Corrija a descrição.', 'Eu me confundi ao dizer que quebrou: estava desmontado.', 'Reescreva sabendo que estava desmontado, sem afirmar defeito.'),
    ('Não foi essa pessoa. Eu fiz. Pode dizer quem foi?', 'Errei a autoria; quem fez fui eu.', 'Corrija: a ação foi minha, e não de quem citei.'),
    ('Quero alegria nessa cena, em vez de tristeza.', 'Deixa o trecho mais alegre, por favor.', 'Mudei o tom: escreva uma cena feliz.'),
    ('Pode cancelar essa atividade por enquanto.', 'Não vou fazer isso agora; deixe o plano de lado.', 'Mudei de ideia e não quero praticar neste momento.'),

    ('Conta um conto curto: {nome} acha um {objeto} na {lugar}.', 'Quero uma pequena cena com {nome}, um {objeto} e a {lugar}.', '{nome} encontra um {objeto} na {lugar}. Pode transformar isso numa história?'),
    ('E aí, depois da descoberta?', 'Pode seguir a partir do que encontrou?', 'Me conta o próximo trecho, mantendo o achado.'),
    ('Como essa pessoa age depois de ficar sem passagem?', 'Segue daí: a porta ainda está presa.', 'Quero saber o próximo passo depois desse problema com a porta.'),
    ('Termine sem recuperar o objeto perdido.', 'O final precisa deixar a busca sem resultado.', 'Não encontre o objeto. Escreva um encerramento assim.'),
    ('Quero que decida contar o segredo com calma.', 'Faça uma mudança de decisão sem conflito violento.', 'Essa pessoa pode revelar o segredo sem discussão? Mostre isso.'),
    ('O som some de repente. Como segue o conto?', 'Imagine que o objeto fica quieto. Escreva o próximo trecho.', 'Faça a continuação depois que ele para de produzir som.'),
    ('A chuva atrapalhou. Continue protegendo o que leva.', 'O objeto precisa ficar seco, mas começou a chover.', 'Segue com a personagem procurando abrigo para o objeto.'),
    ('Depois de devolver, o que muda?', 'Mostre uma consequência da entrega, e não só repita a entrega.', 'Quero que a devolução leve a um próximo acontecimento.'),
    ('Não quero magia para entrar. Resolva de um jeito comum.', 'Faça essa pessoa entrar sem um poder mágico.', 'Uma solução realista para a porta fechada, por favor.'),
    ('Errou a pista. O que faz depois disso?', 'A informação levou ao lugar errado. Continua a partir do erro.', 'Não transforme a pista errada em certa; mostre como reage.'),

    ('Diz a mesma coisa em menos palavras.', 'Encurta essa cena sem mudar o que aconteceu.', 'Uma frase só para resumir o trecho, por favor.'),
    ('Deixe educado: traga meu {objeto} de volta já.', 'Quero dizer com gentileza que preciso do meu {objeto} de volta.', 'Sem soar mandão, como pedir a devolução do {objeto}?'),
    ('Escreva para {nome} perguntando se pode emprestar seu {objeto}.', 'Me dá uma mensagem pedindo o {objeto} de {nome} emprestado.', 'Como pedir a {nome} um {objeto} sem fazer cobrança?'),
    ('Avise que o prazo possível para mim é {dia}.', 'Redija uma mensagem: consigo terminar só no {dia}.', 'Quero combinar entrega para {dia}. Me ajuda a dizer isso.'),
    ('Mantenha o que acontece, mas dê um clima de mistério.', 'Pode escrever essa mesma cena com suspense?', 'Não troque o objeto nem a pessoa; só faça parecer mais misterioso.'),
    ('Não vou aceitar. Redija uma recusa educada sem motivo falso.', 'Quero dizer não ao convite, sem uma história inventada.', 'Uma mensagem gentil para não participar, por favor.'),
    ('Só peça mais tempo, sem inventar uma justificativa.', 'Não quero mentir; me ajuda a pedir um prazo maior.', 'Escreva que preciso de mais tempo para concluir.'),
    ('Coloque na forma de pergunta: {nome} vai trazer um {objeto}.', 'Pergunte se {nome} trará um {objeto}.', 'Quero uma frase interrogativa sobre {nome} trazer um {objeto}.'),
    ('Me dá um nome para o texto sobre um {objeto} esquecido.', 'Sugira o título de um texto em que um {objeto} ficou para trás.', 'Um título curto usando esse {objeto} esquecido, por favor.'),
    ('Deixe uma porta aberta para o reencontro.', 'A despedida não precisa ser definitiva. Mude o fim.', 'Quero que o encerramento permita voltar, sem prometer que volta.'),

    ('Tenho pouco tempo para {hobby}. Como começo pequeno?', 'Queria experimentar {hobby} sem fazer um plano enorme.', 'Qual é um começo simples para praticar {hobby}?'),
    ('Me dá um jeito de organizar a mesa sem comprar materiais.', 'Quero espaço na mesa usando só o que tenho.', 'Como começo a arrumar minha mesa com as coisas que já estão aqui?'),
    ('Estou cansado. Dá para separar só o primeiro material?', 'Não tenho força para organizar tudo da atividade.', 'Quero um passo bem pequeno para deixar o material pronto.'),
    ('Derrubei meu {objeto}. Devo conferir o estado primeiro?', 'Esse {objeto} caiu; posso ignorar e seguir usando?', 'Antes de usar um {objeto} que caiu, o que devo olhar?'),
    ('Vou andando. Como levar sem derrubar?', 'Preciso de cuidado para carregar isso a pé.', 'Me sugere uma forma segura de levar enquanto caminho.'),
    ('Estou cansado e também quero {hobby}. Como decidir?', 'Praticar {hobby} agora ou fazer uma pausa primeiro?', 'Não sei se descanso ou faço um pouco de {hobby}.'),
    ('Como priorizar quando só uma tarefa tem prazo?', 'Tenho uma coisa com prazo e o restante pode esperar.', 'Se só uma obrigação precisa ficar pronta logo, por qual começo?'),
    ('Me ajuda a propor a {nome} que a gente divida a tarefa.', 'Quero perguntar a {nome} como repartir esse trabalho.', 'Escreva para {nome} combinando uma divisão sem cobrar.'),
    ('Fico confuso revisando um texto enorme. Como dividir a revisão?', 'Como conferir um texto longo por partes?', 'Me sugere um começo para revisar sem encarar tudo de uma vez.'),
    ('Tenho vergonha de pedir um favor. Como dizer sem pressionar?', 'Quero ajuda, mas a pessoa pode não ter como ajudar.', 'Como faço um pedido deixando a pessoa à vontade para negar?'),

    ('Se eu dividisse a casa com {nome}, como organizar as tarefas?', 'Talvez eu more com {nome}. O que combinar antes?', 'Pensa na possibilidade de eu morar com {nome}, sem assumir que aconteceu.'),
    ('Eu já moro com essa pessoa ou isso só foi uma hipótese?', 'De verdade, como é minha moradia hoje?', 'Ignore o talvez: qual situação eu confirmei?'),
    ('Imagine que esse objeto decide ficar quieto. Qual seria o conflito?', 'O objeto não fala mais. Como isso cria um problema na ficção?', 'Quero uma ideia para o silêncio do objeto falante.'),
    ('Se não gostar de {hobby}, isso quer dizer que tentar foi errado?', 'A experiência com {hobby} pode valer mesmo se eu não continuar?', 'Não gostar de {hobby} depois de testar é fracassar?'),
    ('Essa pessoa prometeu trazer ou só pode trazer?', 'Dá para tratar o talvez como uma confirmação?', 'É certo que o objeto vem ou ainda é uma possibilidade?'),
    ('Como dois amigos poderiam compartilhar o {objeto} sem brigar?', 'Duas pessoas querem o mesmo {objeto}. Sugira um acordo.', 'Um jeito calmo de combinar o uso do {objeto}, por favor.'),
    ('Continue com o cenário vazio e sem novos personagens.', 'Apenas o lugar permanece. Escreva o que acontece sem gente.', 'Quero seguir no ambiente vazio, mantendo só a descrição.'),
    ('Será que o silêncio tem outras explicações além de raiva?', 'Se não me respondeu, precisa estar zangado?', 'Posso concluir que está bravo só porque ficou quieto?'),
    ('Você sabe com certeza que essa pessoa vem no {dia}?', 'Dá para prometer que a chegada vai acontecer?', 'Pode confirmar o que ainda era uma possibilidade?'),
    ('Posso parar {hobby} se minha vontade mudou?', 'Preciso insistir em {hobby} só por ter começado?', 'Quero rever a escolha de {hobby}. Isso é permitido?'),

    ('Pode me ajudar nisso aí?', 'Quero resolver aquele assunto, sabe?', 'Tô precisando de ajuda com uma coisa, mas não expliquei ainda.'),
    ('Faz do outro jeito de novo.', 'Queria igual àquela vez.', 'Repete o que fez antes, sem eu dizer qual parte.'),
    ('Um deles ficou ruim. Pode resolver?', 'Aquele objeto precisa de ajuste, mas não sei se fui claro.', 'Arruma isso que ficou ruim.'),
    ('Uma dessas pessoas foi embora. Quem continuou no lugar?', 'Não disse qual saiu: dá para saber quem ficou?', 'A pessoa saiu, a outra ficou. Você sabe quem é quem?'),
    ('Você revisa um texto para ficar melhor?', 'Quero melhorar o que escrevi, mas ainda não mandei.', 'Pode dar uma versão melhor do meu texto?'),
    ('Vou mandar uma coisa para {nome}, só não consigo explicar direito.', 'É para {nome}, uma... mensagem? Um objeto? Estou confuso.', 'Preciso enviar algo a {nome}, mas perdi o fio do pedido.'),
    ('Ainda não contei o assunto. Como começar essa mensagem?', 'Quero mandar uma mensagem, mas não expliquei para quem.', 'Ajuda com o começo, embora eu ainda não tenha dito o que vou comunicar.'),
    ('Resolve isso para mim?', 'Tem como cuidar dessa coisa?', 'E aí, consegue me ajudar ou preciso explicar primeiro?'),
    ('Quanto ainda falta?', 'Qual é a parte que resta?', 'Já está perto de acabar? Não falei do que ainda.'),
    ('Você consegue ler o que {nome} pensa?', 'Me diga por que {nome} está pensando assim sem ter informação.', 'Dá para afirmar o pensamento de {nome} sem perguntar?'),

    ('Muda o assunto: agora quero escrever a {nome}.', 'Não vamos planejar a viagem. Quero uma mensagem para {nome}.', 'Deixa a viagem para depois e ajuda a falar com {nome}.'),
    ('Pausa essa atividade. Preciso conversar sobre meu cansaço.', 'Agora não quero praticar: quero contar que fiquei sem energia.', 'Mudei de assunto, podemos falar de como estou cansado?'),
    ('Chega de história por agora. Quero combinar um encontro por mensagem.', 'Deixa esse conto parado e me ajuda com um convite para nos vermos.', 'Vamos mudar para a mensagem de encontro, em vez de continuar a ficção.'),
    ('Não quero dicas para a mesa agora, só um papo.', 'Largue a orientação e converse comigo.', 'Me escuta um pouco. Não preciso da solução neste momento.'),
    ('O compromisso continua. Só quero conversar sobre {hobby}.', 'Não cancelei o encontro; mude só o tema para {hobby}.', 'Podemos deixar o prazo como estava e falar de {hobby}?'),
    ('Retoma aquela história de onde a gente parou.', 'Vamos voltar à ficção anterior?', 'Continue o conto que deixamos em pausa.'),
    ('Queria entender a trava, não só receber uma dica curta.', 'Essa sugestão ficou rasa para o que sinto quando começo.', 'Vamos olhar melhor para a dificuldade que me impede de praticar?'),
    ('Você pode me fazer uma pergunta sobre essa escolha?', 'Não me deixe falando sozinho: pergunte sobre minha decisão.', 'Me acompanha perguntando algo que ajude a pensar nas opções.'),
    ('Antes de terminar preciso parar um pouco. Me ajuda a avisar.', 'Quero pedir um intervalo antes de seguir na entrega.', 'Como comunicar que farei uma pausa sem alterar o prazo?'),
    ('Vamos mudar: escreva uma mensagem agradecendo a {nome}.', 'Agora só quero dizer obrigado a {nome}.', 'Me ajuda a agradecer a {nome}, em vez de falar da preferência.'),

    ('Descreva uma {lugar} onde não tem ninguém.', 'Um parágrafo sobre a {lugar} vazia, sem pessoas.', 'Quero só o ambiente da {lugar}, sem colocar personagens.'),
    ('Comece direto pelo {objeto} que foi esquecido.', 'Conte sobre um {objeto} deixado para trás, sem apresentação.', 'Um pequeno texto que já entra no {objeto} abandonado.'),
    ('Quero uma descrição calma da chuva, sem aventura.', 'Me dá um trecho sereno em que está chovendo.', 'Escreva sobre chuva para dar uma sensação de pausa.'),
    ('Uma abertura para alguém que volta à {lugar}, por favor.', 'Como escrever a primeira frase de uma volta à {lugar}?', 'Inicie o texto com o retorno à {lugar}.'),
    ('O lugar segue vazio. Pode acrescentar mais uma frase?', 'Continua descrevendo sem surgir gente no cenário.', 'Quero mais um trecho só do ambiente, sem pessoas novas.'),
    ('Mostra um diálogo curto sobre emprestar um {objeto}.', 'Duas pessoas combinam o empréstimo do {objeto}. Escreva as falas.', 'Um pedido e uma resposta sobre emprestar o {objeto}, por favor.'),
    ('Me dá só uma ideia de problema entre amigos.', 'Qual conflito de amizade poderia render uma história?', 'Não escreva o conto: sugira o que põe a amizade em dificuldade.'),
    ('Um detalhe visível para tornar esse ambiente concreto.', 'O que poderia aparecer nesse cenário como pista?', 'Quero imaginar o lugar com um pequeno detalhe, não uma explicação longa.'),
    ('Diz em uma frase que reconsiderar não é vergonhoso.', 'Uma frase simples sobre aceitar mudar de opinião.', 'Me dá uma ideia curta para falar de rever uma escolha.'),
    ('Essa pessoa ainda quer devolver. Crie um obstáculo inesperado.', 'Surpreenda com algo que atrapalha a devolução.', 'Qual acontecimento novo pode dificultar entregar o objeto sem trocar o objetivo?'),
]


def historico_variado(hist,variante):
    # Edição de dados offline, não interpretação de mensagens em produção.
    substituicoes=[
        {'Meu nome é':'Eu me chamo','O nome do meu amigo é':'Meu amigo é',
         'Minha preferência é':'Eu prefiro','minha preferência é':'eu prefiro',
         'Meu amigo se chama':'O nome do meu amigo é','Eu levei um':'Levei um',
         'Eu tenho um':'Tenho um','Eu moro sozinho.':'Hoje moro sozinho.',
         'Certo.':'Entendi o que você disse.','Entendi.':'Certo, estou acompanhando.'},
        {'Meu nome é':'Pode me chamar de','Minha preferência é':'Minha escolha é',
         'minha preferência é':'minha escolha é','O nome do meu amigo é':'A pessoa que é minha amiga se chama',
         'Quero praticar':'Estou com vontade de praticar','Corrigindo:':'Mudei de ideia:',
         'Certo.':'Pode continuar.','Entendi.':'Estou acompanhando.'},
        {'Meu nome é':'Eu sou','Meu amigo se chama':'Quem é meu amigo se chama',
         'Minha preferência é':'Gosto de','minha preferência é':'gosto de',
         'Eu levei um':'Eu entreguei um','Não, me enganei.':'Eu disse errado.',
         'Certo.':'Tudo bem.','Entendi.':'Entendi essa parte.'},
    ][variante]
    resultado=[]
    for k,texto in enumerate(hist):
        for antigo,novo in substituicoes.items():texto=texto.replace(antigo,novo)
        resultado.append({'papel':'usuario' if k%2==0 else 'assistente','texto':texto})
    return resultado


def construir():
    if len(VARIANTES)!=len(PADROES):raise ValueError('Três novas formas por família')
    destino=DIR/'corpus_rodada3.json'
    if destino.exists():raise ValueError('Preservar corpus já preparado')
    antigos=json.loads((DIR/'corpus_rodada2.json').read_text())['exemplos']
    # Entradas antigas e desenvolvimento preservados; não incorporar os
    # pedidos de desenvolvimento como treino por já conhecer suas falhas.
    exemplos=list(antigos)
    for i,((grupo,hist,_,resposta),perguntas) in enumerate(zip(PADROES,VARIANTES)):
        for v,pedido in enumerate(perguntas):
            for j in range(12):
                pos=(2*j+v)%len(NOMES)
                valores=dict(nome=NOMES[pos],outro=NOMES[(pos+7)%len(NOMES)],
                    objeto=OBJETOS[j%len(OBJETOS)],outro_objeto=OBJETOS[(j+3)%len(OBJETOS)],
                    lugar=LUGARES[j%len(LUGARES)],outro_lugar=LUGARES[(j+2)%len(LUGARES)],
                    cor1=CORES[j%len(CORES)],cor2=CORES[(j+1)%len(CORES)],
                    dia=DIAS[j%len(DIAS)],outro_dia=DIAS[(j+2)%len(DIAS)],hobby=HOBBIES[j%len(HOBBIES)])
                historico=[{**h,'texto':h['texto'].format(**valores)} for h in historico_variado(hist,v)]
                if j%2:
                    historico=[{'papel':'usuario','texto':CONTEXTOS[(j+v*5)%len(CONTEXTOS)]},
                               {'papel':'assistente','texto':'Pode explicar do seu jeito.'}]+historico
                exemplos.append({'id':f'rodada3-{i:03d}-{v}-{j:02d}','familia':f'familia-{i:03d}',
                    'grupo':grupo,'split':'treino','mensagem':pedido.format(**valores),
                    'historico':historico,'resposta':resposta.format(**valores)})
    distintos={}
    for e in exemplos:
        chave=json.dumps([e['mensagem'],e['historico']],sort_keys=True,ensure_ascii=False)
        if chave in distintos and (distintos[chave]['split']!=e['split'] or distintos[chave]['resposta']!=e['resposta']):
            raise ValueError('Entrada repetida com split/alvo conflitante')
        distintos.setdefault(chave,e)
    exemplos=list(distintos.values())
    inicial=json.loads(gzip.decompress((DIR/'checkpoint_rodada2.json.gz').read_bytes()))
    vocab=set(inicial['vocabulario'])
    oov={s:Counter(t for e in exemplos if e['split']==s for t in tokenizar(e['resposta'])
        if t not in vocab and t not in fonte_dialogo(e['mensagem'],e['historico'])) for s in ['treino','validacao']}
    if any(oov.values()):raise ValueError(f'Alvos impossíveis: {oov}')
    max_fonte=max(1+len(tokenizar(e['mensagem']))+sum(1+len(tokenizar(h['texto'])) for h in e['historico']) for e in exemplos)
    if max_fonte>192:raise ValueError('Histórico de treino seria truncado')
    dados={'origem':'100 padrões autorais, mais 300 formulações de pedido e variação textual de histórico; sem consulta ao holdout',
        'limite':'mesmas operações e alvos da rodada 2; melhora formulação de entrada, não diversidade geral de assuntos/saídas',
        'exemplos':exemplos}
    destino.write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n')
    estat={'padroes_treino_pedidos_deslexicalizados':len({p for _,_,p,_ in PADROES}|{p for vs in VARIANTES for p in vs}),
        'padroes_desenvolvimento_deslexicalizados':100,'familias_supervisao':100,
        'splits':dict(Counter(e['split'] for e in exemplos)),
        'respostas_literais_distintas':len({e['resposta'] for e in exemplos}),
        'vocabulario_preservado':len(vocab),'parametros_preservados':inicial['treino']['parametros'],
        'fonte_max_tokens':max_fonte,'alvos_nao_copiaveis_fora_vocab':{s:dict(c) for s,c in oov.items()},
        'sha256_corpus':hashlib.sha256(destino.read_bytes()).hexdigest(),
        'limite':'prefixos e expansões lexicais não são contados como novos padrões; respostas continuam estreitas'}
    (DIR/'corpus_rodada3_estatisticas.json').write_text(json.dumps(estat,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(estat,ensure_ascii=False,indent=2))


if __name__=='__main__':
    construir()
