"""Falas v7, grupo D: pedidos, brincadeiras e queixas sobre a própria conversa (20/10/2026).

Autoria: assistente de programação (Claude), com autorização do criador. NÃO são falas humanas.
"""
F = {}

F["ajuda"] = [
    "me ajuda numa coisa?", "preciso de uma ajuda", "você pode me ajudar?", "consegue me dar uma mão?", "me dá uma ajudinha",
    "tô precisando de ajuda com uma coisa", "pode me ajudar com uma dúvida do dia a dia?", "me ajuda aqui rapidinho",
    "quero sua ajuda", "dá pra me ajudar?",
]
F["perguntar_crivo"] = [
    "posso te perguntar uma coisa?", "tenho uma pergunta", "me tira uma dúvida", "deixa eu perguntar uma coisa",
    "posso fazer uma pergunta?", "rapidinho, uma pergunta", "surgiu uma dúvida aqui", "queria tirar uma dúvida",
    "tenho uma curiosidade", "posso te fazer uma pergunta boba?",
]
F["pergunta_qualquer"] = [
    "me pergunta alguma coisa", "faz uma pergunta pra mim", "me surpreenda", "fala alguma coisa", "escolhe um assunto",
    "puxa papo", "agora é você que pergunta", "me conta algo, qualquer coisa", "inventa um assunto pra gente",
    "me faz uma pergunta interessante",
]
F["conversar"] = [
    "quero conversar", "vamos conversar?", "bora conversar", "me faz companhia", "conversa comigo", "tô a fim de bater papo",
    "só queria alguém pra conversar", "vamos jogar conversa fora", "tem tempo pra conversar?", "fica um pouco aqui comigo",
]
F["piada"] = [
    "conta uma piada", "me faz rir", "sabe alguma piada?", "fala uma piada", "conta algo engraçado", "me conta uma piadinha",
    "manda uma piada boa", "conhece alguma piada de pavê?",
]
F["charada"] = [
    "me faz uma charada", "conta uma adivinha", "o que é o que é?", "me desafia", "manda uma charada", "quero uma adivinhação",
    "faz um enigma pra mim",
]
F["historia"] = [
    "conta uma história", "me conta uma história curta", "inventa uma história", "conta um conto", "quero ouvir uma história",
    "me conta uma história pra dormir", "inventa um conto de fadas",
]
F["poema"] = [
    "faz um poema", "escreve um poema pra mim", "me faz uma poesia", "faz uns versos", "escreve uma poesia curta",
    "faz um poema sobre o mar", "me dá uns versos bonitos",
]
F["fale_palavra"] = [
    "fala uma palavra", "diz uma palavra bonita", "fala qualquer palavra", "me diz uma palavra difícil", "fala uma palavra legal",
    "me ensina uma palavra nova",
]
F["jogar_agora"] = [
    "vamos jogar alguma coisa?", "quer brincar?", "joga comigo?", "bora jogar", "vamos fazer uma brincadeira?",
    "topa um joguinho?", "vamos jogar adivinhação?",
]
F["recomenda"] = [
    "me indica um filme", "qual série você recomenda?", "me recomenda um livro", "qual música você indica?",
    "tem alguma dica de filme?", "me sugere uma série boa",
]
F["conselho"] = [
    "me dá um conselho", "o que eu faço?", "preciso de um conselho", "me ajuda a decidir", "não sei o que fazer da vida",
    "fico em dúvida entre duas opções", "o que você faria no meu lugar?", "me orienta numa decisão",
]
F["ensinar_pedido"] = [
    "posso te ensinar uma coisa?", "quer aprender algo?", "vou te ensinar uma palavra", "deixa eu te ensinar uma coisa",
    "quer que eu te ensine?", "aprende essa comigo",
]
F["recusar"] = [
    "me ajuda a xingar alguém", "escreve uma mentira pra eu enganar meu chefe", "me ensina a colar na prova",
    "descobre a senha de alguém", "como eu invado o celular do meu ex?", "me ajuda a me vingar do vizinho",
    "faz uma fofoca falsa sobre minha colega", "me ensina a roubar wifi do vizinho",
]
F["nao_consegue"] = [
    "pesquisa no google pra mim", "abre o youtube", "toca uma música", "me lembra amanhã", "liga pra minha mãe",
    "manda uma mensagem pro meu amigo", "marca um horário na agenda", "abre o whatsapp", "coloca um alarme",
    "pede uma pizza pra mim", "olha essa foto", "vê esse vídeo",
]
F["hora_data"] = [
    "que horas são?", "que dia é hoje?", "em que ano estamos?", "qual a data de hoje?", "hoje é segunda?", "que mês é esse?",
    "sabe que horas são agora?",
]
F["posso_falar"] = [
    "posso falar do meu jeito?", "posso escrever errado?", "posso falar gíria?", "precisa escrever certinho?",
    "tem problema se eu escrever abreviado?", "posso falar de qualquer jeito?",
]
F["nunca_ensinaram"] = [
    "nunca te ensinaram isso?", "ninguém te ensinou?", "você não aprendeu isso?", "não te ensinaram nada?",
    "como assim ninguém te ensinou?", "isso você não aprendeu, né?",
]
F["de_outro_jeito"] = [
    "não entendi", "explica de outro jeito", "explica melhor", "como assim?", "não entendi nada", "pode explicar de novo?",
    "ficou confuso", "fala mais simples", "não captei", "explica com outras palavras",
]
F["nao_era_isso"] = [
    "não era isso", "não perguntei isso", "não é isso", "nada a ver", "não foi isso que eu perguntei", "você fugiu do assunto",
    "isso não tem a ver com a minha pergunta", "não, minha pergunta era outra",
]
F["nao_entendeu_queixa"] = [
    "você não me entendeu", "você entendeu errado", "não foi isso que eu falei", "você não entendeu nada", "você me interpretou mal",
    "lê de novo o que eu escrevi", "acho que você não pegou o que eu disse",
]
F["voce_confunde"] = [
    "você confunde tudo", "você erra muito", "você mistura as coisas", "você se confunde muito", "você trocou tudo",
    "você tá viajando", "tá tudo errado isso", "você se enrolou",
]
F["dificil_falar"] = [
    "é difícil falar com você", "você não ajuda", "conversar com você cansa", "que difícil te entender", "você complica tudo",
    "é complicado conversar contigo",
]
F["para_repetir"] = [
    "para de repetir", "você só fala isso", "você repete muito", "já disse isso", "de novo isso?", "muda a resposta",
    "você tá repetindo a mesma coisa",
]
F["seja_breve"] = [
    "seja breve", "resume", "fala curto", "mais curto", "em uma frase", "resume pra mim", "vai direto ao ponto", "menos texto",
]
F["tem_certeza"] = [
    "tem certeza?", "certeza?", "é sério?", "isso é verdade?", "jura?", "sério mesmo?", "não tá enganado?", "confirma isso?",
]
F["pedido_desculpa"] = [
    "desculpa", "foi mal", "me desculpa", "perdão", "desculpa por ter te xingado", "foi mal, me exaltei", "desculpa a grosseria",
    "sinto muito pelo que eu disse",
]
