"""Falas v7, grupo A: cumprimentos, despedidas, reações curtas e sim/não (20/10/2026).

Autoria: assistente de programação (Claude), com autorização do criador. NÃO são falas humanas.
"""
F = {}

F["oi"] = [
    "olá, tudo em paz?", "oi, cheguei por aqui", "salve salve", "opa, chegando", "e aí, meu chapa", "oi oi oi",
    "fala aí, crivo", "e aê", "alô, crivo", "oi, voltei pra conversar",
    "eita, oi", "oi gente", "oi, é a primeira vez que falo com você", "olá, prazer", "oi sumido", "oi de novo, crivo", "hey crivo", "e aí, parceiro", "fala, meu bom", "oi, bom te ver", "olá, amigo",
    "chegay", "oi, tô de volta", "salve, mano", "opa opa", "olar", "oi, apareci", "oie crivo", "eai mano",
]
F["oi_tudo_bem"] = [
    "como cê tá hoje?", "tudo certinho contigo?", "e a vida, como vai?", "como você vai indo?", "tá bem, crivo?",
    "como tá tudo por aí?", "e aí, tudo nos trinques?", "tudo bem contigo hoje?", "como andam as coisas, crivo?",
    "tudo joia com você?", "e aí, firme?", "como você tá se sentindo hoje?", "tá tudo certo aí?", "oi! tudo bom com você?",
    "como foi seu dia, crivo?", "e você, crivo, como vai?", "você tá bem?", "tudo tranquilo aí do seu lado?",
    "oi, tudo legal?", "tá de boa, crivo?", "como você está, meu amigo?", "e aí, como vai essa força?",
]
F["bom_dia"] = [
    "bom diaaa", "bom dia pra você, crivo", "dia!", "bom dia, flor do dia", "bom dia, acordei agora", "bom dia, tudo certo?",
    "bom dia, como foi a noite?", "acordei! bom dia", "bom dia, crivo querido", "bom dia, bora começar o dia",
    "bom dia, já tomei meu café", "bom dia pessoal", "bom dia, meu amigo", "bdia crivo", "um ótimo dia pra você",
    "bom dia, cedinho aqui", "bom dia, tô de pé", "bom dia bom dia",
]
F["boa_tarde"] = [
    "boa tardeee", "tarde, crivo", "boa tarde, meu amigo", "boa tarde, tudo certo?", "boa tarde, acabei de almoçar",
    "boa tarde pra você", "btarde", "boa tarde, crivo querido", "opa, boa tarde", "boa tarde, como vai a tarde aí?",
    "boa tarde! cheguei", "boa tarde, que calor né", "boa tarde, tô no intervalo", "boa tarde boa tarde",
]
F["boa_noite"] = [
    "boa noite, cheguei do trabalho", "opa, boa noite, tudo certo?", "boa noite, meu amigo", "boa noite! como vai?",
    "boa noite, crivo querido", "noite boa pra você", "boa noite, bora conversar?", "boa noite, acabei de jantar",
    "boa noite, tudo em paz aí?", "olá, boa noite",
]
F["despedida"] = [
    "vou indo nessa", "tenho que ir agora", "tô saindo, até", "até logo, crivo", "falou, até depois", "fui, valeu a conversa",
    "até a próxima, crivo", "vou nessa, beijos", "preciso ir, tchau tchau", "tchauzinho", "até outro dia", "vou sair agora, até",
    "a gente se vê", "até já", "té logo", "até breve, crivo", "tô indo, fica bem", "tchau, cuida de você", "fui, até amanhã",
    "vou ali e já volto", "tenho compromisso, tchau", "até mais ver", "flw crivo", "falou falou",
]
F["despedida_dormir"] = [
    "vou dormir que amanhã é cedo", "tô indo deitar, até amanhã", "sono bateu, vou dormir", "vou pra cama agora",
    "hora de dormir pra mim", "vou nanar", "me deitar agora, boa noite", "vou descansar, até amanhã", "partiu dormir",
    "já vou dormir, tchau", "tô caindo de sono, fui", "vou apagar a luz e dormir", "até amanhã, vou dormir",
    "dormir que eu ganho mais", "vou tirar um soninho",
]
F["obrigado"] = [
    "brigadão", "muito obrigado", "valeu demais", "obrigada mesmo", "agradeço muito", "valeu pela ajuda", "obg crivo",
    "muito obrigado pela explicação", "te agradeço", "gratidão", "valeuzão", "obrigado de coração", "thanks, crivo",
    "agradecido", "valeu, me ajudou muito", "obrigado pela paciência", "brigado mesmo", "foi muito útil, obrigado",
]
F["obrigado_despedida"] = [
    "valeu e tchau", "obrigado, até a próxima", "brigado, tchau tchau", "obrigada pela conversa, até mais",
    "valeu pela ajuda, fui", "agradeço, até depois", "muito obrigado e boa noite", "obrigado, vou indo",
    "valeu crivo, até amanhã", "obrigadão, tchau",
]
F["ok"] = [
    "tá bom", "ok, entendi", "beleza então", "certo, certo", "entendido", "tranquilo, entendi", "show", "joia",
    "tá certo", "ah tá", "ok ok", "fechado", "combinado", "anotado", "saquei", "hum, tá", "pode crer", "uhum, entendi",
    "beleza", "tá ok",
]
F["sim_continuar"] = [
    "sim, pode continuar", "quero saber, sim", "bora, pode falar", "claro, manda", "aham, continua", "sim, me conta",
    "pode ser, me fala", "uhum, quero", "com certeza, continua", "isso, segue", "sim, adoraria", "pode mandar ver",
    "sim, vamos", "claro que quero", "sim, estou ouvindo", "manda bala",
]
F["nao_obrigado"] = [
    "não, valeu", "não precisa não", "agora não, obrigado", "deixa pra depois", "não, tô bem assim", "dispenso, valeu",
    "não quero agora", "melhor outra hora", "nem precisa, obrigado", "não, obrigada", "por enquanto não",
    "não, pode deixar",
]
F["risada"] = [
    "kkkkkkkkkkk", "hahahahahaha", "kkkk boa", "rsrsrsrs", "hauhauhau", "kkkk que engraçado", "hahaha adorei",
    "rindo muito aqui", "kkk mano", "huehuehue", "kkkkk não aguento", "ahahaha", "kakakak",
    "kkkkk você é doido",
]
F["expressao_curta"] = [
    "nossa senhora", "credo", "aff maria", "uai", "eita nóis", "mds", "caramba, hein", "putz grila", "vish",
    "oxente", "vixi maria", "meu pai do céu", "jesus", "sério?! nossa",
]
F["grito"] = [
    "aaaaaaaaah", "aaargh", "ahhhhhhhh", "afff", "ugh", "argh", "aiaiai",
    "uuuuuuh", "hmmmpf", "grrrr", "aaaaff",
]
F["sem_sentido"] = [
    "asdasdasd", "lkjhgf", "qazwsx", "ççç", "zxcvb", "uiop", "ghjk", "trtrtr", "mnmnmn", "kjhkjh", "fdsfds", "xpto",
    "blublublu", "hjkl", "nnnn", "jdjdjd", "bnbnbn", "cvcvcv",
]
F["teste"] = [
    "testando 123", "teste teste", "só um teste", "1 2 3 testando", "check", "isso tá funcionando?", "tá me ouvindo?",
    "mensagem de teste", "testando aqui", "funcionou?", "tô testando o chat", "alô alô", "teste rápido",
]
F["cala_boca"] = [
    "fica quieto", "silêncio", "para de falar um pouco", "chega de falar", "quieto", "não fala nada", "me deixa em paz",
    "shhh", "para", "fica calado", "não quero conversa agora", "cala a boca, por favor", "dá um tempo",
]
F["ingles"] = [
    "hello there", "good morning", "what's up?", "can you speak english?", "how is it going?", "nice to meet you",
    "hey, how are you doing?", "do you understand english?", "good night", "thank you", "who are you?", "yes",
]
