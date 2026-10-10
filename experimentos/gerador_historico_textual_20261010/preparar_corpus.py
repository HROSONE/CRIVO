"""Diálogos autorais; expansão lexical offline, nunca consultada na inferência.

Famílias são operações discursivas diferentes, não só nomes diferentes.
Os 24 exemplos por família reutilizam padrões: reportar essa limitação.
Não importar nem ler a avaliação congelada para construir respostas.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

DIR = Path(__file__).resolve().parent
RAIZ = DIR.parents[1]
sys.path.insert(0, str(RAIZ))
from dialogo_seq2seq import fonte_dialogo, tokenizar, vocabulario_treino

# grupo, histórico alternado usuário/assistente, pedido, resposta autoral
PADROES = [
    ("conversa", [], "Oi, cheguei. Podemos conversar?", "Oi! Podemos conversar. O que você quer trazer hoje?"),
    ("conversa", [], "Nunca conversei com você. O que dá para fazer aqui?", "Posso ajudar a escrever, conversar sobre uma ideia ou organizar um pedido. Posso errar; me diga o que você precisa."),
    ("conversa", [], "Estou pensando em muita coisa e não sei por onde começar.", "Escolha uma coisa que está pesando agora. Podemos começar pequeno, sem resolver tudo de uma vez."),
    ("conversa", ["Hoje eu tentei {hobby}, mas não gostei do resultado.", "O que te incomodou no resultado?"], "Acho que eu só queria acertar de primeira.", "Querer acertar de primeira pode tornar a tentativa pesada. O que você mudaria numa segunda tentativa?"),
    ("conversa", ["Eu consegui terminar meu {objeto}.", "Como foi terminar?"], "Fiquei feliz, mas ninguém ligou muito.", "Terminar seu {objeto} foi importante para você, mesmo sem a reação que esperava. Quer contar como fez?"),
    ("conversa", [], "Você já sentiu saudade?", "Não tenho experiências pessoais. Posso conversar sobre saudade a partir do que você está sentindo."),
    ("conversa", [], "Me dá uma opinião, não uma certeza: vale tentar algo novo mesmo errando?", "Eu consideraria uma tentativa pequena, com espaço para errar e ajustar. Isso é uma sugestão, não uma garantia de resultado."),
    ("conversa", ["Eu queria praticar {hobby}, mas fiquei com medo.", "Medo de quê?"], "De parecer ridículo.", "Esse medo pode dificultar começar. Você poderia testar {hobby} num espaço onde se sinta menos exposto."),
    ("conversa", [], "Não quero solução agora. Só estou cansado.", "Tudo bem. Você pode contar o que aconteceu, e eu acompanho sem tentar transformar tudo em conselho."),
    ("conversa", ["Estou contente com minha tentativa de {hobby}.", "Quer contar o que deu certo?"], "Só queria dividir isso mesmo.", "Obrigado por dividir. Que bom que essa tentativa de {hobby} te deixou contente."),

    ("referencia", ["Meu nome é {nome}.", "Olá, {nome}!"], "Como eu me chamo?", "Você se chama {nome}."),
    ("referencia", ["O nome do meu amigo é {nome}.", "Entendi."], "Quem é meu amigo?", "Seu amigo é {nome}."),
    ("referencia", ["Eu levei um {objeto} para {nome}.", "Entendi o que você levou."], "O que eu levei?", "Você levou um {objeto} para {nome}."),
    ("referencia", ["{nome} está esperando na {lugar}.", "Certo."], "Onde essa pessoa está?", "{nome} está na {lugar}."),
    ("referencia", ["Quero praticar {hobby}.", "Podemos pensar num começo."], "O que eu queria praticar mesmo?", "Você queria praticar {hobby}."),
    ("referencia", ["Para mim, o melhor dia é {dia}.", "Entendi sua preferência."], "Qual dia eu prefiro?", "Você prefere {dia}."),
    ("referencia", ["Minha preferência é {cor1}.", "Certo."], "Qual é minha preferência?", "Sua preferência é {cor1}."),
    ("referencia", ["Eu tenho um {objeto}, mas {nome} não tem.", "Entendi."], "Quem tem o objeto?", "Você tem o {objeto}."),
    ("referencia", ["{nome} me emprestou um {objeto}.", "Certo."], "A quem pertence o que estou usando?", "O {objeto} pertence a {nome}; você está usando por empréstimo."),
    ("referencia", ["Preciso entregar meu {objeto} no {dia}.", "Esse é o prazo."], "Qual é o compromisso que mencionei?", "Você precisa entregar seu {objeto} no {dia}."),

    ("correcao", ["Meu amigo se chama {nome}.", "Certo.", "Não, me enganei. O nome é {outro}.", "Entendi a correção."], "Como meu amigo se chama agora?", "Seu amigo se chama {outro}."),
    ("correcao", ["Minha preferência é {cor1}.", "Certo.", "Corrigindo: minha preferência é {cor2}.", "Entendi."], "Qual é minha preferência agora?", "Sua preferência agora é {cor2}."),
    ("correcao", ["Escolhi um {objeto}.", "Certo.", "Troquei. Agora escolhi um {outro_objeto}.", "Entendi a troca."], "Qual foi minha escolha final?", "Sua escolha final foi um {outro_objeto}."),
    ("correcao", ["Vou encontrar {nome} no {dia}.", "Certo.", "Mudou: o encontro ficou para {outro_dia}.", "Entendi."], "Quando é o encontro?", "O encontro com {nome} é no {outro_dia}."),
    ("correcao", ["A história se passa na {lugar}.", "Entendi."], "Na verdade, quero que se passe na {outro_lugar}. Reescreva uma frase.", "Na {outro_lugar}, o silêncio deixou espaço para uma nova descoberta."),
    ("correcao", ["Eu prefiro ficar sozinho enquanto pratico {hobby}.", "Entendi."], "Mudei de ideia: quero companhia. O que eu prefiro agora?", "Agora você prefere ter companhia enquanto pratica {hobby}."),
    ("correcao", ["Meu {objeto} está quebrado.", "Entendi."], "Eu estava errado, ele só estava desmontado. Corrige o resumo.", "Seu {objeto} estava desmontado, não quebrado."),
    ("correcao", ["Eu disse que {nome} tinha feito isso.", "Certo."], "Fui eu, não essa pessoa. Quem fez?", "Foi você quem fez."),
    ("correcao", ["Quero uma cena triste com {nome}.", "Podemos começar pela despedida."], "Não quero triste. Quero uma cena alegre.", "{nome} voltou sorrindo, pronto para dividir a descoberta com quem estava por perto."),
    ("correcao", ["Vou praticar {hobby} no {dia}.", "Certo."], "Esquece esse plano. Não vou praticar por enquanto.", "Entendi: o plano de praticar {hobby} está cancelado por enquanto."),

    ("historia", [], "Escreve uma história curta: {nome} encontra um {objeto} na {lugar}.", "{nome} encontrou um {objeto} na {lugar}. Em vez de levá-lo, procurou uma pista de quem o havia deixado ali."),
    ("historia", ["{nome} encontrou um {objeto} na {lugar}.", "O objeto parecia esconder uma pista."], "Continua a história a partir dessa descoberta.", "{nome} examinou o {objeto} e encontrou uma marca. Decidiu seguir a pista antes de voltar para casa."),
    ("historia", ["{nome} tentou abrir uma porta, mas ela ficou presa.", "A passagem continuava fechada."], "O que acontece depois?", "{nome} parou de forçar a porta e procurou outra passagem. Ao olhar ao redor, viu uma janela aberta."),
    ("historia", ["{nome} perdeu um {objeto}.", "A busca começou na {lugar}."], "Dá um final sem encontrar o objeto.", "{nome} não encontrou o {objeto}, mas deixou um aviso na {lugar}. Voltou para casa com a busca ainda aberta."),
    ("historia", ["{nome} queria guardar um segredo.", "O segredo parecia difícil de carregar."], "Faz a pessoa mudar de ideia, mas sem briga.", "{nome} decidiu contar o segredo com calma. A conversa não resolveu tudo, mas abriu espaço para confiança."),
    ("historia", ["{nome} encontrou um {objeto} que fazia barulho.", "O som vinha do objeto."], "E se ele parasse de fazer barulho de repente? Continua.", "O {objeto} ficou quieto. {nome} ouviu o ambiente pela primeira vez e percebeu que havia alguém esperando do lado de fora."),
    ("historia", ["{nome} está carregando um {objeto} pela {lugar}.", "O caminho parecia tranquilo."], "Começa uma chuva e o objeto não pode molhar. Segue daí.", "{nome} procurou abrigo e protegeu o {objeto}. Esperou a chuva diminuir antes de seguir pelo caminho."),
    ("historia", ["{nome} acabou de devolver um {objeto}.", "A entrega encerrou a busca."], "Escreve uma continuação em que devolver isso tenha uma consequência.", "Ao devolver o {objeto}, {nome} recebeu um convite para voltar. A busca terminou, mas uma nova conversa estava começando."),
    ("historia", ["{nome} quer entrar na {lugar}.", "A porta estava fechada."], "Não abra a porta por magia. Faz uma solução comum.", "{nome} bateu na porta e esperou. Alguém ouviu o chamado e veio abrir."),
    ("historia", ["{nome} seguiu uma pista sobre um {objeto}.", "A pista apontava para a {lugar}."], "A pista estava errada. Continua sem fingir que acertou.", "Na {lugar}, {nome} percebeu que a pista estava errada. Voltou ao começo para conferir o que havia entendido."),

    ("reescrita", ["{nome} viu um {objeto} na {lugar}.", "A descoberta aconteceu no fim do dia."], "Conta essa mesma cena em uma frase menor.", "{nome} encontrou um {objeto} na {lugar}."),
    ("reescrita", [], "Troca o tom desta frase para mais gentil: devolva meu {objeto} agora.", "Você pode devolver meu {objeto}, por favor?"),
    ("reescrita", [], "Quero pedir a {nome} um {objeto} emprestado, sem parecer uma ordem.", "{nome}, você poderia me emprestar seu {objeto}? Tudo bem se não puder."),
    ("reescrita", [], "Escreve uma mensagem dizendo que só posso entregar no {dia}.", "Posso entregar no {dia}. Esse é o prazo que consigo cumprir; podemos combinar assim?"),
    ("reescrita", ["O texto diz: {nome} chegou na {lugar} e encontrou um {objeto}.", "Podemos ajustar o texto."], "Quero uma versão mais misteriosa, sem mudar a pessoa nem o objeto.", "Ao chegar na {lugar}, {nome} encontrou um {objeto} onde ninguém esperava. Uma pergunta ficou no ar."),
    ("reescrita", ["Eu quero recusar um convite de {nome}.", "Você pode ser direto e gentil."], "Escreve a mensagem sem inventar um motivo.", "{nome}, obrigado pelo convite. Desta vez não vou participar, mas agradeço por lembrar de mim."),
    ("reescrita", [], "Me ajuda a pedir mais prazo sem inventar doença ou emergência.", "Preciso de mais prazo para terminar. Podemos conversar sobre uma nova data de entrega?"),
    ("reescrita", [], "Transforma em pergunta: {nome} vai trazer um {objeto}.", "{nome} vai trazer um {objeto}?"),
    ("reescrita", [], "Quero um título para um texto sobre um {objeto} esquecido.", "O {objeto} que ficou para trás"),
    ("reescrita", ["{nome} escreveu uma despedida.", "A cena terminou com a partida."], "Muda só o final para deixar chance de uma volta.", "{nome} partiu, mas deixou aberta a possibilidade de voltar."),

    ("pratica", [], "Quero começar a praticar {hobby}, mas só tenho um tempo curto.", "Escolha uma tentativa pequena de {hobby}. Faça uma parte hoje e observe o que ficou difícil antes de aumentar o plano."),
    ("pratica", [], "Preciso arrumar minha mesa sem comprar nada.", "Tire da mesa o que não está usando, separe o que precisa ficar à mão e devolva cada coisa a um lugar possível."),
    ("pratica", ["Quero organizar meus materiais de {hobby}.", "Podemos começar pela separação."], "Tenho pouca energia hoje. Dá um primeiro passo pequeno.", "Separe só o material que vai usar primeiro em {hobby}. O restante pode esperar por outra etapa."),
    ("pratica", [], "Meu {objeto} caiu. Posso continuar usando sem olhar?", "Antes de continuar, veja se seu {objeto} sofreu algum dano. Se houver risco ou você não souber avaliar, peça ajuda."),
    ("pratica", ["Preciso levar meu {objeto} até a {lugar}.", "Como você vai transportar?"], "Vou a pé. Quero evitar que caia.", "Leve o {objeto} de forma firme e pare se precisar ajustar a posição. Evite carregar mais coisas ao mesmo tempo."),
    ("pratica", [], "Não consigo escolher entre praticar {hobby} e descansar.", "Veja como está sua energia. Você pode descansar primeiro ou fazer uma tentativa curta de {hobby}, sem se obrigar a continuar."),
    ("pratica", ["Tenho muitas coisas para resolver no {dia}.", "O que tem prazo?"], "Só uma tem prazo. Como começo?", "Comece pela tarefa com prazo e escolha uma parte que possa terminar. Depois veja o que ainda cabe no {dia}."),
    ("pratica", [], "Quero conversar com {nome} sobre dividir uma tarefa sem cobrar.", "{nome}, podemos combinar como dividir essa tarefa? Queria entender o que cada um consegue fazer."),
    ("pratica", ["Quero revisar meu texto antes de enviar.", "Podemos revisar por partes."], "O texto está grande e fico perdido.", "Revise um parágrafo por vez. Primeiro confira o sentido; depois procure repetições e frases que ficaram difíceis de entender."),
    ("pratica", [], "Preciso pedir ajuda, mas tenho medo de incomodar.", "Faça um pedido pequeno e dê espaço para a pessoa recusar. Você pode dizer o que precisa sem tratar a ajuda como obrigação."),

    ("hipotese", ["Eu moro sozinho.", "Entendi."], "E se eu morasse com {nome}? Como combinar tarefas?", "Se você morasse com {nome}, poderia conversar sobre as tarefas e combinar uma divisão. Isso ainda é uma possibilidade."),
    ("hipotese", ["Eu moro sozinho.", "Certo.", "Talvez eu more com {nome} no futuro.", "Essa é uma possibilidade."], "Qual é a minha situação atual?", "Atualmente você mora sozinho."),
    ("hipotese", ["No meu conto, um {objeto} pode falar.", "Essa é uma ideia de ficção."], "E se ele se recusasse a falar?", "O silêncio do {objeto} poderia criar um conflito: a personagem teria de buscar respostas de outra forma."),
    ("hipotese", [], "Se eu tentasse {hobby} e não gostasse, seria um fracasso?", "Não necessariamente. Experimentar {hobby} também pode ajudar você a descobrir o que prefere e ajustar a escolha."),
    ("hipotese", ["{nome} talvez traga um {objeto}.", "Ainda não está confirmado."], "Posso dizer que essa pessoa vai trazer com certeza?", "Não. Você disse que {nome} talvez traga um {objeto}; isso não confirma a entrega."),
    ("hipotese", [], "E se duas pessoas quisessem usar o mesmo {objeto}? Dá uma solução sem briga.", "Elas poderiam combinar uma ordem para usar o {objeto} ou procurar uma forma de compartilhar, se isso for possível."),
    ("hipotese", ["Meu texto se passa na {lugar}.", "Esse é o cenário."], "E se o lugar ficasse vazio? Continua sem inventar novas pessoas.", "A {lugar} ficou vazia. O silêncio tornou cada detalhe mais visível, e o caminho pareceu diferente."),
    ("hipotese", [], "É possível que alguém não responda sem estar bravo comigo?", "Sim, há outras possibilidades. Sem mais informação, não dá para afirmar o motivo do silêncio dessa pessoa."),
    ("hipotese", ["{nome} pode chegar no {dia}.", "É uma possibilidade."], "Então você garante que essa pessoa chega?", "Não posso garantir. Você disse que {nome} pode chegar no {dia}, não que a chegada está confirmada."),
    ("hipotese", [], "Se eu mudar de ideia sobre {hobby}, preciso continuar só porque comecei?", "Você pode rever a escolha. Vale pensar no que mudou e decidir se quer continuar, pausar ou tentar outra coisa."),

    ("esclarecimento", [], "Me ajuda com aquele negócio.", "Qual negócio você quer resolver? Me diga um pouco do pedido para eu poder ajudar."),
    ("esclarecimento", [], "Faz igual antes.", "Você quer repetir qual parte? Não tenho informação suficiente para saber o que significa antes aqui."),
    ("esclarecimento", ["Eu tenho um {objeto} e um {outro_objeto}.", "Certo."], "Aquele ficou ruim. Conserta.", "Você está falando do {objeto} ou do {outro_objeto}? E o que ficou ruim?"),
    ("esclarecimento", ["{nome} e {outro} estão na {lugar}.", "Entendi."], "Essa pessoa saiu. Quem ficou?", "Quem saiu, {nome} ou {outro}? Sem essa informação, não sei quem ficou."),
    ("esclarecimento", [], "Quero um texto melhor.", "Qual texto você quer melhorar? Pode enviar um trecho e dizer o que está te incomodando."),
    ("esclarecimento", [], "Preciso mandar um... esqueci. Uma coisa para {nome}.", "Você quer mandar uma mensagem ou algum objeto para {nome}? Podemos esclarecer primeiro."),
    ("esclarecimento", ["Eu pedi ajuda para escrever.", "Sobre qual assunto?"], "Uma mensagem. Mas não sei como começar.", "Para quem é a mensagem e o que você precisa dizer? Com isso podemos escolher um começo."),
    ("esclarecimento", [], "E aí, resolve para mim?", "O que você quer resolver? Preciso conhecer o pedido antes de sugerir um caminho."),
    ("esclarecimento", [], "Quanto falta?", "Quanto falta para quê? Você pode me dizer a tarefa ou o prazo que está acompanhando?"),
    ("esclarecimento", [], "Me diga o que {nome} está pensando.", "Não tenho como saber o que {nome} está pensando. Você pode contar o que aconteceu, sem tratar uma hipótese como certeza."),

    ("transicao", ["Quero planejar uma viagem.", "Podemos organizar o que você precisa."], "Esquece a viagem. Quero escrever uma mensagem para {nome}.", "Certo. O que você quer dizer para {nome} nessa mensagem?"),
    ("transicao", ["Estou tentando praticar {hobby}.", "Podemos pensar numa tentativa pequena."], "Agora quero falar de outra coisa: estou cansado.", "Podemos mudar de assunto. Quer contar o que está te deixando cansado?"),
    ("transicao", ["{nome} encontrou um {objeto}.", "A história começou com essa descoberta."], "Para a história. Quero uma mensagem para combinar um encontro.", "Podemos deixar a história de lado. Com quem você quer combinar o encontro e em qual dia?"),
    ("transicao", ["Preciso organizar minha mesa.", "Comece pelo que está usando."], "Não quero orientação. Quero só conversar um pouco.", "Tudo bem, podemos conversar. Como foi seu dia?"),
    ("transicao", ["Tenho um compromisso no {dia}.", "Certo."], "Não mudei o compromisso, só quero falar de {hobby} agora.", "Podemos falar de {hobby}. O compromisso no {dia} não foi alterado."),
    ("transicao", ["{nome} ficou preso na {lugar}.", "A história parou nesse problema."], "Podemos voltar à história?", "Podemos. {nome} ainda estava na {lugar}, tentando encontrar uma saída."),
    ("transicao", ["Estou sem vontade de praticar {hobby}.", "Você pode pausar."], "Só isso? Queria entender por que estou travando.", "Podemos olhar mais de perto. O que acontece quando você tenta começar a praticar {hobby}?"),
    ("transicao", ["Eu quero conversar sobre uma decisão.", "Qual decisão?"], "E aí? Você não vai perguntar nada?", "Vou tentar acompanhar melhor: quais são as opções e o que está tornando a escolha difícil?"),
    ("transicao", ["Preciso entregar meu {objeto} no {dia}.", "Esse é o prazo."], "Antes disso, me ajuda a pedir uma pausa.", "Você pode dizer: preciso de uma pausa antes de continuar. Depois volto ao {objeto} e ao prazo de {dia}."),
    ("transicao", ["Gosto de {cor1}.", "Entendi sua preferência."], "Mudando de assunto, quero agradecer a {nome}.", "{nome}, obrigado pela ajuda. Queria dizer que isso fez diferença para mim."),

    ("escrita_livre", [], "Descreve uma {lugar} vazia sem colocar pessoas.", "A {lugar} estava vazia. A luz mudava devagar, e o silêncio deixava cada canto mais visível."),
    ("escrita_livre", [], "Escreve sobre um {objeto} esquecido sem começar com uma apresentação.", "O {objeto} ficou onde ninguém olhava. Com o tempo, passou a fazer parte do lugar, esperando ser notado outra vez."),
    ("escrita_livre", [], "Quero um parágrafo tranquilo sobre chuva, sem história de aventura.", "A chuva tocava a janela num ritmo calmo. Dentro, o tempo parecia mais lento, e havia espaço para respirar sem pressa."),
    ("escrita_livre", [], "Dá uma frase de abertura sobre alguém voltando à {lugar}.", "Voltar à {lugar} foi reconhecer um caminho que já não parecia o mesmo."),
    ("escrita_livre", ["A {lugar} ficou vazia no fim da tarde.", "A luz ainda entrava pela janela."], "Continua sem colocar uma pessoa.", "O vento moveu uma folha no chão. Na {lugar}, nada precisava responder ao silêncio."),
    ("escrita_livre", [], "Cria um pequeno diálogo pedindo um {objeto} emprestado.", "Você pode me emprestar seu {objeto}? Posso, mas preciso dele de volta depois. Tudo bem, vamos combinar a devolução."),
    ("escrita_livre", [], "Não quero uma história. Quero uma ideia de conflito entre dois amigos.", "Um amigo empresta algo importante, e o outro perde. O conflito pode ser contar a verdade e tentar reparar a confiança."),
    ("escrita_livre", ["Meu texto começa na {lugar}.", "Esse é o cenário."], "Sugere um detalhe concreto para o ambiente.", "Você pode mostrar uma marca no chão da {lugar}, como pista de algo que aconteceu ali."),
    ("escrita_livre", [], "Escreve uma frase sobre mudar de ideia sem tratar isso como vergonha.", "Mudar de ideia pode ser uma forma de ouvir melhor o que a experiência mostrou."),
    ("escrita_livre", ["{nome} quer devolver um {objeto}.", "Esse é o objetivo da cena."], "Quero um acontecimento inesperado, sem perder o objetivo.", "{nome} encontrou a casa vazia ao tentar devolver o {objeto}. Precisou descobrir quando a pessoa voltaria."),
]

NOMES = ["Alina", "Breno", "Cecília", "Davi", "Elisa", "Fábio", "Giovana", "Heitor",
         "Isabel", "Jonas", "Karen", "Leandro", "Marta", "Nilo", "Olga", "Paulo",
         "Rita", "Sandro", "Teresa", "Ulisses", "Vera", "Walter", "Yara", "Zeca"]
OBJETOS = ["caderno", "mapa", "relógio", "livro", "barco", "casaco", "quadro", "pote"]
LUGARES = ["biblioteca", "praça", "oficina", "cozinha", "escola", "sala"]
CORES = ["azul", "verde", "amarelo", "vermelho", "roxo", "branco"]
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
HOBBIES = ["desenho", "fotografia", "leitura", "jardinagem", "escrita", "pintura"]


def construir():
    if (DIR / "corpus.json").exists():
        raise RuntimeError("Preservar corpus gerado; não reescrever silenciosamente")
    exemplos, por_familia = [], []
    for i, (grupo, hist, pedido, resposta) in enumerate(PADROES):
        # Família inteira sai do treino; avaliação interna não é um split lexical.
        split = "validacao" if i % 5 == 4 else "treino"
        quantidade = 12 if split == "validacao" else 24
        for j in range(quantidade):
            valores = dict(nome=NOMES[j], outro=NOMES[(j+7) % len(NOMES)],
                objeto=OBJETOS[j % len(OBJETOS)], outro_objeto=OBJETOS[(j+3) % len(OBJETOS)],
                lugar=LUGARES[j % len(LUGARES)], outro_lugar=LUGARES[(j+2) % len(LUGARES)],
                cor1=CORES[j % len(CORES)], cor2=CORES[(j+1) % len(CORES)],
                dia=DIAS[j % len(DIAS)], outro_dia=DIAS[(j+2) % len(DIAS)],
                hobby=HOBBIES[j % len(HOBBIES)])
            historico = [{"papel": "usuario" if k % 2 == 0 else "assistente", "texto": t.format(**valores)}
                         for k, t in enumerate(hist)]
            exemplos.append({"id": f"familia-{i:03d}-{j:02d}", "familia": f"familia-{i:03d}",
                "grupo": grupo, "split": split, "mensagem": pedido.format(**valores),
                "historico": historico, "resposta": resposta.format(**valores)})
        por_familia.append({"familia": f"familia-{i:03d}", "grupo": grupo, "split": split,
                           "historico_deslexicalizado": hist, "pedido_deslexicalizado": pedido,
                           "resposta_deslexicalizada": resposta, "exemplos": quantidade})
    treino = [e for e in exemplos if e["split"] == "treino"]
    vocab = vocabulario_treino(treino, 720)
    desconhecidos = Counter(t for e in treino for t in tokenizar(e["resposta"])
                           if t not in vocab and t not in fonte_dialogo(e["mensagem"], e["historico"]))
    fontes = [1+len(tokenizar(e["mensagem"]))+sum(1+len(tokenizar(h["texto"])) for h in e["historico"])
              for e in exemplos]
    alvos = [1+len(tokenizar(e["resposta"])) for e in exemplos]
    if max(fontes)>192 or max(alvos)>64 or desconhecidos:
        raise ValueError(f"Dados fora do orçamento: fonte={max(fontes)}, alvo={max(alvos)}, OOV={desconhecidos}")
    # Expansões lexicais podem repetir literalmente padrões sem variáveis. Deduplicar.
    distintos = {}
    for e in exemplos:
        chave = json.dumps({k: e[k] for k in ("mensagem", "historico", "resposta")}, sort_keys=True)
        if chave in distintos and distintos[chave]["split"] != e["split"]:
            raise ValueError("Sobreposição exata entre treino e validação")
        distintos.setdefault(chave, e)
    exemplos = list(distintos.values())
    conteudos = {"origem": "100 famílias escritas pelo agente; expansão lexical offline; sem modelo externo",
                "licenca": "mesma licença do repositório; conteúdo autoral novo", "exemplos": exemplos}
    corpus_path = DIR / "corpus.json"
    corpus_path.write_text(json.dumps(conteudos, ensure_ascii=False, indent=2)+"\n")
    (DIR / "familias.json").write_text(json.dumps(por_familia, ensure_ascii=False, indent=2)+"\n")
    estat = {"familias": len(PADROES), "familias_treino": len({e['familia'] for e in exemplos if e['split']=='treino'}),
        "familias_validacao": len({e['familia'] for e in exemplos if e['split']=='validacao'}),
        "exemplos_antes_deduplicacao": sum(f['exemplos'] for f in por_familia),
        "exemplos_unicos": len(exemplos), "splits": dict(Counter(e['split'] for e in exemplos)),
        "grupos": dict(Counter(e['grupo'] for e in exemplos)), "fonte_max_tokens": max(fontes),
        "alvo_max_tokens": max(alvos), "vocabulario_treino": len(vocab),
        "alvos_treino_desconhecidos_nao_copiaveis": dict(desconhecidos),
        "respostas_literais_distintas": len({e['resposta'] for e in exemplos}),
        "limite": "24 variações lexicais não são 24 novos padrões; famílias 4/9/... inteiras só na validação interna",
        "sha256_corpus": hashlib.sha256(corpus_path.read_bytes()).hexdigest()}
    (DIR / "corpus_estatisticas.json").write_text(json.dumps(estat, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(estat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    construir()
