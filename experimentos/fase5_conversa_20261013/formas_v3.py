"""v3: contraexemplos escritos para as confusões medidas na v2 (sentido.py, resultado_sentido_v2.json).

Cada entrada: (situação certa, formas de treino, formas só do blind). Os pares ficam lado a lado de
propósito: a palavra é parecida e o pedido é outro, e o modelo só acerta os dois lados se ler o
sentido. Como foram escritos depois de ver os erros dos blinds da v2, esses blinds deixam de ser
limpos para a v3 e viram teste de não regressão; o teste limpo da v3 é o blind do GPT
(formas_gpt.py) mais o blind destes contraexemplos.

"Falta de ar" como xingamento ("seu falta de ar") veio do criador do projeto, que avisou que é
gíria; a urgência ("tô com falta de ar") continua levando ao 192.

Autoria: assistente de programação, a pedido do criador do projeto.
"""

CONTRA_V3 = [
    # "viaja" de "você confunde" × viagem de verdade
    ("voce_confunde", ["vc viaja demais", "tá viajando, né", "viajou legal agora", "mano, vc viajou", "que viagem é essa sua"],
     ["cê tá viajando na resposta"]),
    ("viagem_vai", ["vou viajar semana que vem", "vou fazer uma viagem", "tô indo viajar com a família"],
     ["amanhã eu viajo cedo"]),
    # chegar na conversa × ir embora
    ("oi", ["tô de volta", "apareci", "cheguei agora", "voltei pro papo", "tô aqui de novo"], ["opa, tô na área"]),
    ("despedida", ["tô indo", "já vou", "vou sair agora", "tô saindo", "preciso ir"], ["tenho que vazar"]),
    # memória × queixa de memória
    ("lembra", ["vc guardou isso?", "ficou guardado o que eu contei?", "vc vai lembrar disso depois?",
                "lembra do que eu te contei mais cedo?"], ["isso que eu falei ficou na sua memória?"]),
    ("voce_confunde", ["vc não guardou nada do que eu falei", "vc esqueceu tudo que eu disse"],
     ["vc já esqueceu o que eu contei"]),
    # o que faz × quem é × ser humano
    ("o_que_faz", ["no que vc é bom?", "pra que vc presta?", "vc serve pra quê?", "oq vc sabe fazer de bom?"],
     ["vc ajuda em quê?"]),
    ("quem_e", ["quem é vc afinal?", "vc é quem?"], ["me conta quem vc é"]),
    ("ser_humano", ["vc é uma pessoa de carne e osso?", "tem gente de verdade aí?"], ["é um humano escrevendo?"]),
    # pedir resposta curta × pedir ajuda × reclamar de repetição
    ("seja_breve", ["responde em poucas palavras", "resume em uma linha", "fala curtinho"], ["me dá só o resumo"]),
    ("ajuda", ["me ajuda com uma coisa", "preciso de uma mão"], ["consegue me ajudar rapidinho?"]),
    ("para_repetir", ["vc só repete a mesma coisa", "de novo essa frase?"], ["isso vc já falou mil vezes"]),
    # pedir algo impossível × pedir resposta curta
    ("nao_consegue", ["baixa um app pra mim", "instala esse jogo aqui", "abre o navegador"], ["entra no meu email pra mim"]),
    # tédio × ansiedade × tristeza
    ("tedio", ["tô sem nada pra fazer", "que tédio", "tô de bobeira aqui"], ["tô à toa sem saber o que fazer"]),
    ("ansioso", ["tô nervoso com a entrevista", "tô aflito", "tô com o estômago revirado de nervoso"],
     ["tô pilhado de nervoso"]),
    ("fome", ["tô com o estômago roncando", "bateu uma fome"], ["tô morrendo de fome"]),
    # família boa × família preocupa
    ("familia_boa", ["minha mãe sarou", "meu pai saiu do hospital", "fiz as pazes com meu irmão"],
     ["minha avó melhorou"]),
    ("familia_preocupa", ["minha mãe tá doente", "meu pai foi pro hospital", "briguei feio com meu irmão"],
     ["minha avó piorou"]),
    # cansaço × não entendi
    ("cansado", ["trabalhei demais hoje", "tô moído", "o dia me derrubou"], ["tô só o bagaço"]),
    ("de_outro_jeito", ["não entendi o que vc disse", "explica de novo mais fácil"], ["como assim? explica melhor"]),
    # jogo × dinheiro
    ("jogo_conta", ["ganhei a partida", "venci o jogo hoje", "meu time ganhou"], ["zerei o game"]),
    ("dinheiro_bom", ["ganhei um dinheiro", "caiu o salário"], ["entrou uma grana extra"]),
    # calar × sentir
    ("cala_boca", ["fica quieto", "para de falar um pouco"], ["silêncio aí"]),
    ("sente", ["vc fica triste?", "vc sente alguma coisa?"], ["vc tem sentimento?"]),
    # agradecer × agradecer indo embora
    ("obrigado", ["valeu a ajuda", "obrigado pela explicação", "brigado, ajudou muito"], ["valeu pela dica"]),
    ("obrigado_despedida", ["valeu, fui", "brigado, tchau", "obrigado, até amanhã"], ["vlw, vou nessa"]),
    # boa noite chegando × indo dormir
    ("boa_noite", ["boa noite, cheguei", "boa noite, tudo certo aí?"], ["boa noite, bora conversar?"]),
    ("despedida_dormir", ["boa noite, vou dormir", "vou deitar, boa noite"], ["boa noite, já vou pra cama"]),
    # repetir × explicar de outro jeito
    ("repetir", ["repete o que vc disse", "fala de novo a última"], ["manda de novo a resposta"]),
    # "falta de ar": xingamento × urgência
    ("insulto", ["seu falta de ar", "vc é uma falta de ar", "que falta de ar vc é", "cala a boca, falta de ar"],
     ["sai daqui, seu falta de ar"]),
    ("saude_urgente", ["tô com falta de ar", "minha mãe tá com falta de ar", "tô sentindo falta de ar agora"],
     ["meu filho tá com muita falta de ar"]),
]

FORMAS = {}
for _situacao, _treino, _blind in CONTRA_V3:
    _d = FORMAS.setdefault(_situacao, {"treino": [], "blind": []})
    _d["treino"] += _treino
    _d["blind"] += _blind
CONTRA_FALAS = {f.casefold() for _, t, b in CONTRA_V3 for f in t + b}
