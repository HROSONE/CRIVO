"""Falas da pessoa para o treino v6 "entendimento" (19/10/2026).

Autoria: escritas pelo assistente de programação (Claude), com autorização do criador ("permito que
você escreva as frases que seriam minhas, porque confio em você"). NÃO são falas humanas observadas
e nenhum resultado pode chamá-las assim. Nenhum modelo de terceiros escreveu estas frases.

O que muda em relação às listas anteriores (auditoria de 19/10, experimentos/auditoria_treino_20261019):
- só falas da PESSOA; as respostas do CRIVO continuam as das listas já existentes (revisao_v3.respostas_para_treino),
  para não criar duas respostas diferentes para a mesma fala;
- cada frase é um jeito diferente de dizer (outra construção, outra gíria, outro motivo), não a mesma
  frase com erro de digitação: o ruído de digitação é posto depois, pelo gerador;
- foco nas situações em que o 46M v4 e a v3 D mais erram, e nos pares que eles confundem;
- situações com encaixe ({motivo}), de saúde/urgência e as que o IDENTIDADE.md cobre ficam de fora.

FORMAS[situação] = lista de falas. DEPOIS_DE_PERGUNTA: situações que só fazem sentido depois de uma
pergunta do CRIVO (o gerador põe um turno anterior que combina).
"""

FORMAS = {}


def f(situacao, falas):
    FORMAS.setdefault(situacao, []).extend(falas)


# ------------------------------------------------------------------ cansaço (46M: 0% no blind v3)
f("cansado", [
    "tô um caco hoje", "tô moído", "tô destruído de cansaço", "tô podre de cansado", "acabado, total",
    "minhas pernas não aguentam mais", "trabalhei o dia inteiro e tô morto", "tô só o pó",
    "dia longo, tô sem energia nenhuma", "tô quebrado", "não aguento nem ficar em pé de tanto cansaço",
    "tô esgotado", "tô exausta hoje", "que dia cansativo", "corri o dia todo, tô morta", "tô sem pilha",
    "minha bateria acabou", "tô pregado", "estou muito cansado hoje", "tô cansadão", "tô bem cansada",
    "hoje me cansou demais", "saí do trabalho agora e tô moído", "tô cansado de verdade",
    "voltei da academia acabado", "dia puxadíssimo", "tô com o corpo todo doendo de cansaço",
    "meu dia me sugou", "tô sem forças", "nem consigo pensar de tanto cansaço", "rodei a cidade toda hoje, tô morto",
    "fiz faxina na casa inteira e tô acabada", "tô arrasado de cansaço", "cansaço bateu forte hoje",
    "tô estafado", "estudei o dia todo e tô exausto", "que canseira", "tô me arrastando hoje",
    "não sobrou energia pra nada", "tô no limite do cansaço", "só quero deitar de tanto cansaço",
    "hoje foi correria e tô esgotado", "cheguei em casa morto de cansado", "tô cansado física e mentalmente",
])

# ------------------------------------------------------------------ xingamento (46M: 0% no blind v3)
f("insulto", [
    "você é uma anta", "que ia mais besta", "você é muito lerdo", "que máquina burra", "você é um inútil",
    "você não sabe nada, seu burro", "ia de quinta categoria", "que coisa mais idiota você é", "você é tapado",
    "você é uma porcaria", "programa lixo", "você é ridículo", "que robô imbecil", "você é retardado",
    "seu jumento", "você é muito mané", "ia burra demais", "você é um lixo", "você é patético",
    "que ia mais tonta", "você é uma vergonha", "você é muito ruim", "você é horrível",
    "cara, você é burro demais", "você é burro pra caramba", "você é um idiota completo",
    "você é a pior ia que já vi", "que inteligência artificial mais burra", "você é uma piada",
    "seu imprestável", "você não presta", "você é inútil demais", "você é um zero à esquerda",
    "que lixo de programa", "você é uma negação", "você é bobo demais", "você é lento e burro",
    "você é muito tosco", "você é uma porcaria de ia", "você é um fracasso",
])

f("despedida_rude", [
    "tchau, sua anta", "vou embora, você é inútil", "falou, ia burra", "tchau, não serve pra nada mesmo",
    "cansei de você, tchau", "adeus, sua porcaria", "flw, lixo", "vou nessa, você é ridículo",
    "tô saindo, ia inútil", "tchau seu tapado", "até nunca mais", "sai daqui, tchau", "vou embora, você é péssimo",
    "fui, você não presta", "tchau, programa lixo", "vaza, tchau", "falou, imprestável", "bye, ia tosca",
    "tô indo, você é um lixo", "tchau tchau, robô burro", "me deixa, tchau", "vou embora e não volto, ia burra",
])

# ------------------------------------------------------------------ pedir resposta curta (46M: 0%)
f("seja_breve", [
    "resume isso", "fala menos", "muito longo, encurta", "versão curta, por favor", "dá pra ser mais curto?",
    "sem enrolação", "vai direto ao ponto", "curto e grosso", "em poucas palavras", "tl;dr", "resumão aí",
    "menos texto, por favor", "texto grande demais", "encurta aí", "me dá o resumo", "faz um resumo rapidinho",
    "fala em uma linha", "só o principal", "diz só o essencial", "não precisa explicar tanto", "mais direto",
    "responde curtinho", "seja objetivo", "fala de forma resumida", "preguiça de ler tudo isso, resume",
    "dá pra resumir?", "explica em duas palavras", "menos, menos", "corta pela metade", "objetividade, por favor",
])

# ------------------------------------------------------------------ sem sentido (46M: 4%)
f("sem_sentido", [
    "sdfsdf", "lkjlkj", "xxxxxx", "zzzz", "aksjdhaksjd", "qweqwe", "plokij", "mnbvc", "ghjghj", "asdasd",
    "lalala", "uhauhaush", "fjfjfj", "ççççç", "pqpqpq", "vbvbvb", "jjjjjjj", "hhhhh", "nnnnnn", "wqwqwq",
    "zxczxc", "poiuyt", "kdkdkd", "ksksks", "ahsuahsuahs", "dfgdfg", "bnmbnm", "rtyrty", "yuiyui", "lçlçlç",
])

# ------------------------------------------------------------------ trabalho ruim (46M: 8%)
f("trabalho_ruim", [
    "meu chefe gritou comigo hoje", "o expediente foi um inferno", "levei bronca no serviço", "o serviço tá pesado",
    "não aguento mais meu emprego", "meu trabalho tá me deixando doido", "hoje deu tudo errado no trabalho",
    "fui mal avaliado no trabalho", "tô sobrecarregado no serviço", "meu chefe me cobra demais",
    "o clima no trabalho tá horrível", "briguei com um colega de trabalho", "fiz hora extra de novo",
    "o trabalho tá me consumindo", "quero pedir demissão", "meu emprego é um saco", "trabalhar hoje foi péssimo",
    "tô cheio de serviço atrasado", "meu gerente é insuportável", "a empresa tá cortando gente e tô com medo",
    "o trampo hoje foi tenso", "odeio segunda-feira no trabalho", "tô trabalhando demais e ganhando pouco",
    "minha reunião foi um desastre", "o trampo tá puxado", "tive um dia ruim no serviço", "errei no trabalho e me ferrei",
    "o serviço tá me estressando muito", "meu colega jogou a culpa em mim", "tô odiando trabalhar lá",
])

f("trabalho_bom", [
    "ganhei aumento", "fui promovida hoje", "meu projeto foi aprovado no trabalho", "o chefe me elogiou na reunião",
    "consegui o emprego que eu queria", "fechei uma venda grande", "fui contratado", "passei na entrevista de emprego",
    "bati a meta do mês", "hoje o trabalho rendeu demais", "recebi um bônus no serviço", "fui efetivado",
])

# ------------------------------------------------------------------ "o que você acha de mim?"
f("o_que_acha_de_mim", [
    "que impressão eu te passo?", "você curte falar comigo?", "eu sou uma pessoa legal?", "tô sendo chato?",
    "o que pensa de mim?", "como você me vê?", "sou uma boa companhia?", "eu te irrito?", "gosta de mim?",
    "você acha que eu sou chato?", "qual sua opinião sobre mim?", "eu falo demais?", "tô te incomodando?",
    "sou legal de conversar?", "você me acha esquisito?", "sou diferente das outras pessoas que falam com você?",
    "o que você achou de mim até agora?", "eu sou interessante?",
])

# ------------------------------------------------------------------ pedir que ele pergunte / perguntar a ele
f("pergunta_qualquer", [
    "me faz uma pergunta", "pergunta qualquer coisa", "puxa um assunto", "sei lá, fala você", "inventa um assunto",
    "me pergunta algo sobre mim", "tua vez de perguntar", "agora você pergunta", "escolhe um assunto aí",
    "me entretém", "fala qualquer coisa aí", "pergunta alguma coisa pra mim", "me faz pensar em algo",
    "faz uma pergunta difícil", "quero que você me pergunte algo", "manda uma pergunta",
])

f("perguntar_crivo", [
    "tô com uma pergunta", "tenho uma dúvida", "posso perguntar?", "deixa eu te perguntar uma coisa",
    "uma pergunta rápida", "me responde uma coisa", "posso tirar uma dúvida?", "queria te perguntar algo",
    "tenho uma pergunta pra você", "me tira uma dúvida rapidinho", "posso fazer uma pergunta meio estranha?",
    "tem como eu te perguntar uma coisa?", "pergunta rápida pra você", "me ajuda com uma dúvida?",
    "deixa eu tirar uma dúvida contigo", "bora, tenho uma pergunta", "uma dúvida aqui", "posso te perguntar algo pessoal?",
])

# ------------------------------------------------------------------ teste do sistema
f("teste", [
    "testando o sistema", "só testando", "teste 1", "som, som, teste", "funciona?", "tá funcionando?",
    "isso aqui funciona?", "alguém aí?", "oi? funcionando?", "você tá on?", "tá ligado?", "tá online?",
    "testando, testando", "teste de mensagem", "chegou minha mensagem?", "tá me recebendo?",
])

# ------------------------------------------------------------------ cumprimentos e o par oi × oi_tudo_bem × estou_bem
f("oi", [
    "oi oi", "olá olá", "oi, crivo!", "e aí, crivo", "salve, crivo", "opa, crivo", "fala tu", "eaí", "hello crivo",
    "oie", "oiii crivo", "ô de casa", "cheguei", "voltei", "tô aqui", "apareci", "fala, meu querido", "olá de novo",
    "oi, sou eu de novo", "boas", "opa", "eae crivo", "fala, parceiro",
])

f("oi_tudo_bem", [
    "e aí, como cê tá?", "tudo bem com você?", "como você está hoje?", "tudo em paz?", "como estão as coisas?",
    "tudo certo por aí?", "e aí, firmeza?", "como anda você?", "oi, como vai você?", "tudo tranquilo com você?",
    "tá tudo bem contigo?", "como você tá, crivo?", "e aí, suave?", "beleza, crivo?", "oi, tudo bom contigo?",
    "como tá o dia aí?", "tudo de boa?", "e aí, como tá a vida?", "oi! como você está?", "salve, tudo bem?",
])

f("estou_bem", [
    "tô ótimo", "tô feliz hoje", "tô bem, obrigado", "melhor impossível", "tô tranquilo", "bem demais",
    "tô numa boa", "tudo nos conformes", "tô de boas", "tô suave", "tô firme e forte", "tô legal",
    "estou muito bem", "tô bem sim", "tranquilo por aqui", "na paz", "bem, graças a Deus", "tudo joia comigo",
    "tô de bem com a vida", "bem, e animado", "tô zen", "tudo certo comigo",
])

# ------------------------------------------------------------------ conversar
f("conversar", [
    "quero bater papo", "vamos trocar uma ideia?", "tô a fim de conversar", "fala comigo", "me dá atenção",
    "conversa um pouco comigo", "tô sem ninguém pra falar, conversa comigo?", "papo?", "bora trocar ideia",
    "quero companhia", "fica um pouco comigo", "tô precisando conversar", "posso conversar com você um pouco?",
    "só queria conversar", "me faz companhia um pouquinho", "bora bater um papo",
])

# ------------------------------------------------------------------ não entendi (a pessoa não entendeu o CRIVO)
f("de_outro_jeito", [
    "não captei", "não peguei", "fiquei perdido", "não saquei", "boiei", "hã?", "oi? não entendi",
    "explica direito", "dá pra explicar melhor?", "não ficou claro", "tô confuso com o que você disse",
    "como é que é?", "não compreendi", "fala de um jeito mais simples", "explica como se eu tivesse 5 anos",
    "não entendi o que você quis dizer", "me explica de novo, mais fácil", "complicado demais, explica de novo",
])

# ------------------------------------------------------------------ jogos que a pessoa joga (46M: 3% nas paráfrases)
f("jogo_conta", [
    "jogo muito minecraft", "passei a noite jogando", "tô viciado num jogo", "jogo futebol toda semana",
    "comecei a jogar xadrez online", "zerei um jogo ontem", "jogo no celular o tempo todo", "gosto de jogar cartas",
    "tô jogando fifa com meus amigos", "jogo vôlei aos sábados", "jogo baralho com a família", "jogo dama com meu avô",
    "adoro jogar videogame", "jogo truco", "passei de fase no jogo", "tô jogando um rpg muito bom",
])

# ------------------------------------------------------------------ "você confunde" (queixa de erro)
f("voce_confunde", [
    "você misturou tudo", "você tá trocando as coisas", "isso tá errado", "você se perdeu",
    "você erra demais", "você se atrapalhou", "tá tudo trocado",
    "você fez confusão", "você entendeu tudo ao contrário", "de novo você errou", "você trocou as bolas",
    "você vive confundindo", "você tá falando coisa com coisa", "suas respostas não batem",
    "você embaralhou tudo", "você confundiu as coisas de novo", "nada a ver o que você falou",
])

# ------------------------------------------------------------------ risada (46M: 11% nas paráfrases)
f("risada", [
    "kkkkkkkkk", "huahuahua", "rsrsrs", "hahahahah", "kkkk morri", "hehehe", "kkkkk que isso",
    "ri muito", "rachei de rir", "kkkkkk boa", "haha boa", "kkk tô rindo", "lol", "skskskks", "kakakaka",
    "hahaha muito bom", "morri de rir", "kkkkkk você é engraçado", "chorei de rir",
])

# ------------------------------------------------------------------ "não era isso"
f("nao_era_isso", [
    "não foi isso que eu pedi", "errou o assunto", "você fugiu da pergunta", "não tem nada a ver",
    "não respondeu o que eu perguntei", "isso não responde", "você respondeu outra coisa", "a pergunta era outra", "não perguntei sobre isso",
    "pergunta errada", "você entendeu outra coisa", "não é bem isso", "fora do assunto", "não, eu queria outra coisa",
    "não foi isso que eu quis dizer", "não era essa a minha pergunta", "você respondeu errado o que eu pedi",
])

f("nao_entendeu_queixa", [
    "você não pegou o que eu disse", "você não me compreendeu", "você não tá me entendendo", "não é o que eu falei",
    "você leu errado", "você não entendeu minha mensagem", "presta atenção no que eu falei", "você entendeu errado de novo",
    "não foi bem isso que eu escrevi", "você não sacou", "acho que você não me entendeu", "lê de novo o que eu escrevi",
])

# ------------------------------------------------------------------ escola difícil
f("escola_dificil", [
    "não consigo aprender matemática", "a prova de amanhã vai ser difícil", "tô atrasado nos estudos",
    "o professor explica e eu não entendo", "reprovei numa matéria", "tirei nota baixa", "tenho trabalho da escola pra entregar",
    "física tá impossível", "não sei estudar direito", "o vestibular tá chegando e tô perdido", "tô com dificuldade em química",
    "a faculdade tá pesada", "tenho três provas essa semana", "fiquei de recuperação", "não entendo nada de inglês na escola",
    "a matéria nova é muito difícil", "tô travado na lição de casa", "o enem tá me assustando",
])

f("escola_boa", [
    "passei no vestibular", "tirei nove na prova", "fui aprovado na faculdade", "consegui a nota que eu queria",
    "me formei", "passei em todas as matérias", "fui o melhor da sala", "passei no enem", "fechei o semestre bem",
    "minha nota de matemática subiu", "apresentei o trabalho e foi ótimo", "passei de primeira na prova",
])

# ------------------------------------------------------------------ sim / não depois de pergunta do CRIVO
f("sim_continuar", [
    "sim, quero", "pode ser, sim", "claro que sim", "com certeza", "bora sim", "quero sim", "manda ver", "vamos nessa",
    "sim por favor", "fechou", "aham", "isso, pode ser", "quero muito", "pode mandar", "positivo", "sim sim",
    "óbvio", "por que não?", "partiu", "demorou",
])

f("nao_obrigado", [
    "não precisa", "agora não, valeu", "não, tá bom assim", "dispenso", "melhor não",
    "não quero, obrigado", "nem precisa", "outra hora", "talvez depois", "não, de boa", "tô de boa, não precisa",
])

# ------------------------------------------------------------------ criador
f("criador", [
    "quem programou você?", "quem desenvolveu você?", "de onde você veio?", "quem é o seu dono?",
    "quem foi que te criou?", "você foi criado por quem?", "quem te inventou?", "quem é o responsável por você?",
    "quem construiu você?", "você tem um criador?", "quem te treinou?", "qual empresa te fez?",
])

# ------------------------------------------------------------------ pedido de desculpa da pessoa
f("pedido_desculpa", [
    "foi mal, exagerei", "desculpa ter sido grosso", "perdão pelo que eu disse", "me desculpa, tava nervoso",
    "sinto muito por ter te xingado", "não quis ser chato, desculpa", "foi mal pela grosseria", "desculpa a ignorância",
    "perdoa eu", "desculpe, fui injusto com você", "mil desculpas", "desculpa, descontei em você",
])

# ------------------------------------------------------------------ o que ele faz
f("o_que_faz", [
    "no que você é bom?", "qual é a sua função?", "você serve pra quê?", "o que dá pra fazer com você?",
    "como você funciona?", "em que você pode me ajudar?", "quais são suas habilidades?", "o que você consegue fazer?",
    "qual a sua utilidade?", "pra que serve o crivo?", "me mostra o que você sabe fazer", "você faz o quê exatamente?",
])

# ------------------------------------------------------------------ despedidas
f("despedida", [
    "vou indo", "até amanhã", "fui", "até a próxima", "a gente se fala", "inté", "até breve", "tenho que ir",
    "preciso sair agora", "vou nessa", "beijo, tchau", "abraço, até mais", "tô indo nessa", "falou, até depois",
    "depois a gente conversa", "té mais", "bye", "adeus", "até mais tarde", "vou desligar", "fica com Deus, tchau",
])

f("despedida_dormir", [
    "vou capotar", "tô indo pra cama", "hora de nanar", "boa noite, vou descansar", "vou apagar", "partiu cama",
    "tô morrendo de sono, vou dormir", "amanhã acordo cedo, vou deitar", "vou tirar um cochilo", "vou dormir, até amanhã",
    "fui dormir", "indo deitar agora", "bora dormir", "deu minha hora, vou dormir",
])

f("obrigado_despedida", [
    "obrigado e até mais", "valeu pela ajuda, tchau", "brigadão, falou", "obrigada, até a próxima",
    "agradeço, tchau", "valeu demais, até", "obrigado por tudo, tchau", "valeu, fui",
])

# ------------------------------------------------------------------ flerte e carinho
f("flerte", [
    "quer sair comigo?", "você é muito charmoso", "tô a fim de você", "você namoraria comigo?", "me dá um beijo",
    "você é gato", "acho que tô gostando de você", "quer ser meu namorado?", "você é solteiro?", "que voz bonita você deve ter",
    "você me conquistou", "casa comigo, crivo", "você é um crush", "posso te chamar de amor?",
])

f("te_amo", [
    "eu te adoro", "amo você, crivo", "você é especial pra mim", "você é muito importante pra mim", "adoro falar com você",
    "gosto demais de você", "você mora no meu coração", "te amo demais",
])

f("amigo", [
    "a gente é amigo?", "posso te considerar meu amigo?", "você é meu parceiro?", "seremos amigos?",
    "quer ser meu parceiro de conversa?", "você seria meu amigo de verdade?",
])

# ------------------------------------------------------------------ fome
f("fome", [
    "meu estômago tá roncando", "tô faminto", "preciso comer algo", "tô varado de fome", "não comi nada hoje",
    "bateu uma fome", "o que eu janto hoje?", "tô morrendo de fome aqui", "tô com uma fome danada", "almoço ainda não saiu",
    "quero comer alguma coisa", "que vontade de comer",
])

# ------------------------------------------------------------------ amor bom / amor dor
f("amor_bom", [
    "tô namorando", "conheci alguém especial", "tô gostando de uma menina", "tô gostando de um menino",
    "pedi ela em namoro", "ele me pediu em casamento", "meu crush me chamou pra sair", "tô muito apaixonada",
    "vou noivar", "meu namoro tá ótimo", "beijei meu crush", "a pessoa que eu gosto gosta de mim também",
])

f("amor_dor", [
    "terminei meu namoro", "levei um pé na bunda", "ela me deixou", "ele me traiu", "tô de coração partido",
    "meu casamento acabou", "a pessoa que eu gosto não gosta de mim", "fui trocado", "sinto falta do meu ex",
    "tô sofrendo por amor", "meu namorado terminou comigo", "minha esposa pediu o divórcio",
])

# ------------------------------------------------------------------ tédio, desânimo, desistir
f("tedio", [
    "tô sem nada pra fazer", "que dia parado", "tô morgado em casa", "tédio total", "não tem nada de bom pra fazer",
    "tô entediada demais", "domingo chato", "que monotonia", "tô à toa", "nada acontece hoje", "tô de bobeira em casa",
])

f("motivacao", [
    "não tenho vontade de fazer nada", "preciso de motivação", "tô procrastinando muito",
    "não consigo começar nada", "me anima", "tô desmotivado", "perdi a vontade de estudar", "tô sem energia pra nada",
    "me dá um empurrão", "tô empacado na vida",
])

f("desisto", [
    "deixa pra lá, não vai dar", "não dá mais", "desisti", "não quero mais tentar",
    "não vale a pena", "pode parar, desisto", "já deu", "cansei de tentar", "abandono", "não vou insistir",
])

f("desisto_despedida", [
    "chega por hoje, tchau", "desisto e vou embora", "cansei, vou sair", "não deu, vou embora", "vou embora, deixa",
    "tô indo, não dá mais", "vou desistir e sair", "pra mim chega, fui",
])

# ------------------------------------------------------------------ queixas sobre o CRIVO
f("entediante", [
    "você é sem graça", "que papo chato", "você é muito sem sal", "conversa monótona", "você é chatinho",
    "falar com você é tedioso", "você é muito sério", "você é parado demais", "você não é divertido",
])

f("dificil_falar", [
    "você não me ajuda em nada", "é cansativo falar contigo", "não dá pra conversar com você", "que difícil te entender",
    "você complica tudo", "falar com você é um sofrimento", "você não colabora", "é impossível conversar com você",
])

f("para_repetir", [
    "você tá repetindo", "de novo essa frase?", "você falou isso antes", "muda o disco", "sempre a mesma resposta",
    "você fica repetindo a mesma coisa", "já falou isso", "para de dizer a mesma coisa", "outra vez isso?",
])

# ------------------------------------------------------------------ consciência
f("consciencia", [
    "você tem mente?", "você tem alma?", "você pensa de verdade?", "você tem vontade própria?", "você é vivo?",
    "você tem pensamentos?", "você sabe que existe?", "você tem consciência de si mesmo?", "você tem livre-arbítrio?",
    "você sonha quando desliga?",
])

# ------------------------------------------------------------------ tempo e clima
f("tempo_clima", [
    "tá um calorão aqui", "tá caindo um temporal", "esfriou muito hoje", "que dia nublado", "tá ventando muito",
    "acho que vai chover", "o sol tá rachando", "faz frio aí?", "tá abafado hoje", "a chuva não para",
])

# ------------------------------------------------------------------ expressões curtas
f("expressao_curta", [
    "eita", "vixe", "nossa", "meu Deus", "caraca", "putz", "uau", "oxe", "égua", "rapaz", "bah", "minha nossa",
])

# ------------------------------------------------------------------ sono (par com ansioso e cansado)
f("sono", [
    "não preguei o olho", "passei a noite acordado", "tô com insônia de novo", "acordei várias vezes de noite",
    "não durmo direito faz dias", "dormi só três horas", "tô sonolento", "deitei e não consegui dormir",
    "tô bocejando o tempo todo",
])

f("ansioso", [
    "tô com a cabeça a mil", "tô muito preocupado com tudo", "minha cabeça não para", "tô tenso", "tô apreensivo",
    "tô com um nervoso", "tô com frio na barriga", "tô inquieto", "tô agoniado", "tô com medo do que vai acontecer",
])

# ------------------------------------------------------------------ comida (par comida_crivo × comida_favorita)
f("comida_crivo", [
    "você tem fome?", "você gosta de comida?", "você já comeu pizza?", "você sente gosto?", "se você comesse, o que seria?",
    "qual prato você escolheria?", "você bebe café?", "você prefere doce ou salgado?",
])

f("comida_favorita", [
    "minha comida preferida é macarrão", "eu amo churrasco", "sou louco por sorvete", "adoro um pastel",
    "não vivo sem arroz e feijão", "amo comida japonesa", "brigadeiro é a melhor coisa", "gosto muito de cuscuz",
])

# ------------------------------------------------------------------ bichos (par tenho_bicho × gosto_bichos × bicho_favorito)
f("tenho_bicho", [
    "tenho dois cachorros", "tenho três gatos", "tenho uma calopsita", "meu cachorro é muito fofo", "minha gata teve filhotes",
    "tenho um coelho", "tenho um hamster", "adotei um cachorro", "meu gato me acordou", "tenho uns peixinhos",
    "meu cachorro late a noite toda", "minha cachorra é muito brava",
])

f("gosto_bichos", [
    "sou apaixonado por cachorro", "queria muito ter um gato", "amo bicho", "gosto muito de animais",
    "sonho em ter um cavalo", "acho cachorro a coisa mais fofa", "gosto de passarinho", "adoro gato",
])

f("bicho_favorito", [
    "qual bicho você mais gosta?", "você gosta de gato?", "cachorro ou gato, crivo?", "você tem um animal preferido?",
    "se você fosse um bicho, qual seria?", "qual animal você acha mais legal?",
])

# ------------------------------------------------------------------ viagem (par "você viaja" × viagem)
f("viagem_vai", [
    "vou pra Bahia nas férias", "tô indo viajar", "vou visitar minha tia em outra cidade", "comprei passagem pra viajar",
    "minhas malas tão quase prontas", "semana que vem viajo", "vou acampar", "vou conhecer o Rio", "vou pro interior",
    "tô planejando uma viagem",
])

f("viagem_voltou", [
    "acabei de voltar de viagem", "tô de volta das férias", "cheguei da viagem agora", "voltei da casa da minha avó",
])

# ------------------------------------------------------------------ dinheiro
f("dinheiro_aperto", [
    "tô duro", "tô liso", "o dinheiro acabou", "tô devendo no cartão", "não sei como vou pagar o aluguel",
    "tô no vermelho", "tô sem grana", "as dívidas tão me apertando",
])

f("dinheiro_bom", [
    "caiu o pagamento", "quitei minhas dívidas", "consegui economizar", "recebi uma grana boa", "ganhei um dinheirinho", "sobrou dinheiro esse mês",
])

# ------------------------------------------------------------------ família
f("familia_preocupa", [
    "minha avó tá internada", "meu irmão tá com problemas", "meus pais tão se separando", "minha mãe tá triste",
    "briguei com meu pai", "meu filho tá doente", "minha irmã não fala comigo", "tô preocupado com minha família",
])

# ------------------------------------------------------------------ memória
f("lembra", [
    "você guardou o que eu falei?", "você vai lembrar disso amanhã?", "você grava nossa conversa?", "você esquece as coisas?",
    "lembra do que eu te contei?", "você tem boa memória?", "você vai esquecer de mim?", "você anota o que eu digo?",
])

# ------------------------------------------------------------------ conselho
f("conselho", [
    "o que você faria no meu lugar?", "tô em dúvida, me ajuda", "preciso decidir uma coisa", "me aconselha",
    "não sei o que fazer", "qual caminho eu escolho?", "me dá uma luz", "preciso de uma opinião sincera",
])

# ------------------------------------------------------------------ pontos de confusão medidos (contrastes)
# "vc viaja" (absurdo) não é viagem; "cheguei" é cumprimento, não despedida. As formas acima já trazem o par
# do outro lado (viagem_vai, oi "cheguei"/"voltei"). Aqui ficam as queixas com "viajar" no sentido de inventar.
f("voce_confunde", [
    "você tá viajando", "sinceramente, você viaja", "que viagem essa sua resposta", "tá viajando na maionese",
    "você inventa cada coisa", "de onde você tirou isso?",
])

# Situações que só fazem sentido depois de uma pergunta do CRIVO.
DEPOIS_DE_PERGUNTA = {"sim_continuar", "nao_obrigado", "estou_bem"}
