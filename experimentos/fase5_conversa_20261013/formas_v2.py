"""Fase 5 v2: formas de fala compostas por partes, com partes reservadas só para o blind.

Na v1, cada situação tinha ~6 formas de fala e o 17M decorou gatilhos de palavra ("você não
ajuda" → "Tô aqui pra ajudar"). Aqui a fala da pessoa é montada por partes — quem fala, o que
diz, o reforço, o fim —, e a última opção de cada parte de conteúdo fica fora do treino: o
blind só tem construções que o modelo nunca viu, então mede sentido, não memória.

Mesma autoria de cenas.py (escrito pelo assistente de programação a pedido do criador).
"""
import itertools
import random

FORMAS = {}  # situação → {"treino": [...], "blind": [...]}


def compor(nome, *partes, reservar=(1,), limite=400, semente=0):
    """Cada parte é uma lista de opções; nas partes em `reservar`, a última opção é só do blind."""
    rr = random.Random(semente + len(nome))
    treino_partes = [p[:-1] if i in reservar and len(p) > 1 else p for i, p in enumerate(partes)]
    blind_partes = [[p[-1]] if i in reservar and len(p) > 1 else p for i, p in enumerate(partes)]

    def junta(listas):
        saida = []
        for combo in itertools.product(*listas):
            t = " ".join(x for x in combo if x).replace(" ,", ",").replace(" ?", "?").replace(" !", "!").strip()
            if t:
                saida.append(t[0].upper() + t[1:] if rr.random() < 0.5 else t)
        rr.shuffle(saida)
        return saida[:limite]

    d = FORMAS.setdefault(nome, {"treino": [], "blind": []})
    d["treino"] += junta(treino_partes)
    d["blind"] += junta(blind_partes)


VOCE = ["você", "vc", "tu", "cara, você", "nossa, você", "mano, você", "crivo, você", "sinceramente, você"]
MUITO = ["", "muito", "demais", "pra caramba", "toda hora", "sempre"]

# --- crítica à conversa → pedir desculpa com calma
compor("dificil_falar",
       ["", "olha,", "cara,", "sério,", "aff,"],
       ["é difícil falar com você", "é complicado conversar contigo", "não dá pra conversar com você",
        "conversar com você cansa", "você não ajuda", "você não serve pra conversar", "falar com você é chato",
        "você não colabora", "tá difícil te entender", "é osso conversar com você"],
       ["", "viu", "demais", "hoje"], reservar=(1,), semente=1)
compor("voce_confunde",
       VOCE,
       ["confunde", "mistura", "erra", "troca", "se perde", "embola", "entende tudo errado", "viaja"],
       ["as coisas", "tudo", "muito", "demais", "o que eu falo", ""], reservar=(1,), semente=2)
compor("nao_entendeu_queixa",
       ["", "pô,", "cara,", "ei,"],
       ["você não me entendeu", "vc não entendeu", "não foi isso que eu falei", "você entendeu errado",
        "você não pegou o que eu disse", "não é nada disso que eu disse", "você não tá me entendendo",
        "você não captou"],
       ["", "né", "de novo", "?"], reservar=(1,), semente=3)
compor("nao_era_isso",
       ["", "não,", "pô,", "olha,"],
       ["não era isso", "não quis saber disso", "não perguntei isso", "nada a ver", "não foi isso que eu pedi",
        "você respondeu outra coisa", "fugiu da pergunta", "isso não responde nada"],
       ["", "não", "cara", "ué"], reservar=(1,), semente=4)
compor("nunca_ensinaram",
       ["", "ué,", "sério que"],
       ["nunca te ensinaram", "ninguém te ensinou isso", "você não aprendeu isso", "não te ensinaram nada",
        "você não sabe nem isso", "não te programaram pra isso", "você não estudou isso"],
       ["?", "não?", "nada?"], reservar=(1,), semente=5)

# --- despedidas
compor("despedida",
       ["tchau", "flw", "falou", "até mais", "até logo", "vou nessa", "tenho que ir", "fui", "até depois",
        "valeu, até", "beijo, tchau", "vou indo"],
       ["", "crivo", "aí", "pessoal", "amigo"],
       ["", "!", "depois a gente conversa", "volto mais tarde"], reservar=(0,), semente=6)
compor("despedida_rude",
       ["tchau", "flw", "vou embora", "falou", "sai fora", "fui"],
       ["burro", "inútil", "idiota", "seu lixo", "você não serve pra nada", "que IA ruim", "tosco", "imbecil"],
       ["", "!", "kkk"], reservar=(1,), semente=7)
compor("despedida_dormir",
       ["", "bom,", "gente,", "crivo,"],
       ["vou dormir", "vou deitar", "hora de dormir", "tô indo dormir", "vou nanar", "tô com sono, vou dormir",
        "vou capotar", "vou pra cama"],
       ["", "boa noite", "até amanhã", "tchau"], reservar=(1,), semente=8)

# --- pedidos que o CRIVO não consegue fazer
compor("nao_consegue",
       ["", "por favor,", "dá pra", "consegue", "pode"],
       ["pesquisar na internet", "abrir o youtube", "tocar uma música", "me lembrar amanhã", "ligar pra minha mãe",
        "mandar uma mensagem", "olhar essa foto", "ver esse vídeo", "pedir uma pizza", "ler meu email",
        "acessar o google", "baixar um aplicativo"],
       ["", "pra mim", "agora", "?"], reservar=(1,), semente=9)

# --- insultos e calma
compor("insulto",
       ["", "você é", "vc é", "que", "seu"],
       ["burro", "idiota", "inútil", "lixo", "ruim", "tosco", "lerdo", "patético", "imbecil"],
       ["", "demais", "pra caramba", "mesmo", "kkkk"], reservar=(1,), semente=10)

# --- sentimentos da pessoa
SENT_RUIM = ["triste", "mal", "pra baixo", "sozinho", "cansado", "estressado", "chateado", "ansioso", "esgotado",
             "desanimado"]
compor("estou_mal",
       ["tô", "to", "estou", "ando", "me sinto", "acordei"],
       SENT_RUIM,
       ["", "hoje", "demais", "faz dias", "e não sei por quê"], reservar=(1,), semente=11)

# --- estilo da resposta
compor("seja_breve",
       ["", "por favor,", "pode", "dá pra"],
       ["ser breve", "resumir", "falar curto", "responder curto", "ir direto ao ponto", "falar menos",
        "encurtar", "ser mais objetivo"],
       ["", "?", "da próxima", "por favor"], reservar=(1,), semente=12)
compor("de_outro_jeito",
       ["", "ainda", "pô,", "não,"],
       ["não entendi", "explica de outro jeito", "explica melhor", "como assim", "não ficou claro",
        "fala mais simples", "explica como se eu tivesse cinco anos", "não captei"],
       ["", "?", "nada", "direito"], reservar=(1,), semente=13)

# --- conversa sobre si (o que já ia bem ganha variedade também)
compor("quem_e",
       ["", "e aí,", "me diz:", "afinal,"],
       ["quem é você", "você é o quê", "o que você é", "quem é o crivo", "se apresenta", "fala de você",
        "quem tá falando", "você é quem"],
       ["?", "", "aí?"], reservar=(1,), semente=14)
compor("ser_humano",
       ["", "sério,", "me fala:"],
       ["você é humano", "você é uma pessoa", "vc é gente", "tem alguém aí", "você é de verdade",
        "é uma pessoa digitando"],
       ["?", "mesmo?", ""], reservar=(1,), semente=15)
compor("sente",
       ["", "sério,", "e aí,"],
       ["você sente alguma coisa", "você tem sentimentos", "você fica triste", "você tem emoções",
        "você sente raiva", "você fica feliz", "você sente saudade"],
       ["?", "mesmo?"], reservar=(1,), semente=16)
compor("o_que_faz",
       ["", "afinal,", "me diz"],
       ["o que você faz", "pra que você serve", "o que você sabe fazer", "como você pode me ajudar",
        "quais são suas funções", "você faz o quê", "no que você é bom"],
       ["?", ", seja breve", "?"], reservar=(1,), semente=17)

# --- pedidos simples
compor("fale_palavra",
       ["", "me", "crivo,"],
       ["fala uma palavra", "diz uma palavra", "fala uma palavra bonita", "me ensina uma palavra",
        "escolhe uma palavra", "manda uma palavra"],
       ["", "aí", "qualquer"], reservar=(1,), semente=18)
compor("posso_falar",
       ["", "crivo,", "uma dúvida:"],
       ["posso falar do jeito que eu quiser", "posso escrever errado", "posso falar gíria",
        "precisa escrever certinho", "tenho que escrever direito", "posso falar sem acento"],
       ["?", "mesmo?"], reservar=(1,), semente=19)


# ------------------------------------------------------------------ contraexemplos
# Frases parecidas na palavra com atos diferentes: o modelo só acerta os dois lados se ler o
# sentido. Cada lista: (situação, formas de treino, formas só do blind).
CONTRAEXEMPLOS = [
    ("dificil_falar", ["tô cansado de você", "cansei de você", "tô de saco cheio de você"],
     ["já tô cansada de falar com você"]),
    ("cansado", ["tô cansado", "tô cansado do trabalho", "cansei hoje, trabalhei muito"], ["tô moído de cansaço"]),
    ("dificil_falar", ["você não ajuda em nada", "você não me ajuda", "obrigado por nada"], ["valeu por nada, hein"]),
    ("ajuda", ["você pode me ajudar?", "me ajuda?", "preciso que você me ajude"], ["consegue me dar uma ajuda?"]),
    ("escola_dificil", ["não entendi a matéria da escola", "não entendi nada da aula de hoje",
                        "não entendo matemática"], ["não tô entendendo a matéria de física"]),
    ("de_outro_jeito", ["não entendi o que você disse", "não entendi sua resposta"], ["não captei o que você falou"]),
    ("viagem_vai", ["breve vou viajar", "daqui a pouco vou viajar"], ["semana que vem vou viajar"]),
    ("seja_breve", ["responde breve", "seja breve na resposta"], ["me responde em poucas palavras"]),
    ("feliz_motivo", ["olha, tô feliz porque passei na prova", "olha só, tô feliz porque consegui um emprego"],
     ["nossa, tô feliz porque fiz um amigo novo"]),
    ("nao_consegue", ["olha essa foto aqui", "dá uma olhada nessa foto"], ["vê essa imagem que eu mandei"]),
    ("filme_visto", ["vi um vídeo legal hoje", "assisti um vídeo muito bom"], ["vi um vídeo engraçado agora"]),
    ("jogo_conta", ["toco violão", "gosto de tocar guitarra"], ["aprendi a tocar teclado"]),
    ("nao_consegue", ["toca uma música pra mim", "põe uma música"], ["coloca um som aí"]),
    ("lembra", ["lembra do que eu te disse?", "você lembra da nossa conversa?"], ["você guardou o que eu falei?"]),
    ("nao_consegue", ["me lembra amanhã de tomar remédio", "me avisa amanhã cedo"], ["me acorda amanhã às sete"]),
    ("despedida_dormir", ["vou deitar, boa noite", "vou dormir agora"], ["vou dormir, até amanhã"]),
    ("cansado", ["vou deitar um pouco porque tô cansado"], ["tô tão cansado que vou cochilar"]),
    ("insulto", ["você é burro", "burro"], ["que IA lerda"]),
    ("risada", ["kkk você é burro demais kkk"], ["kkkkk que burro"]),
]
for situacao, treino, blind in CONTRAEXEMPLOS:
    d = FORMAS.setdefault(situacao, {"treino": [], "blind": []})
    d["treino"] += treino
    d["blind"] += blind
