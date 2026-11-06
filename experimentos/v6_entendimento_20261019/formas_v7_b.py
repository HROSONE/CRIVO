"""Falas v7, grupo B: como a pessoa está e o que aconteceu na vida dela (20/10/2026).

Autoria: assistente de programação (Claude), com autorização do criador. NÃO são falas humanas.
Evita de propósito palavras de saúde e urgência (dor, sangue, passar mal, falta de ar, peito): o detector de gatilhos
confere isso de novo.
"""
F = {}

F["cansado"] = [
    "tô moído hoje", "que dia exaustivo", "tô um bagaço", "tô só o caco", "trabalhei feito louco e tô acabado",
    "não tenho mais energia hoje", "tô morta de cansada", "esse dia me derrubou", "tô sem gás", "tô na reserva hoje",
    "cheguei em casa sem forças", "tô cansado demais pra pensar", "hoje rendeu, mas tô exausto", "que semana cansativa",
    "tô quebradão", "tô pregadão", "nem sinto as pernas de tanto andar", "tô moída de tanto limpar a casa",
    "o dia sugou minhas energias", "tô cansada pra caramba", "dia puxado, tô acabada", "tô exausto, sério",
]
F["sono"] = [
    "dormi super mal", "acordei no meio da noite e não dormi mais", "tô com um sono absurdo", "fiquei rolando na cama",
    "não consegui pregar o olho", "minha noite foi péssima", "virei a noite acordado", "só dormi umas duas horas",
    "tô morrendo de sono", "tô com insônia faz uns dias", "não consigo dormir cedo", "acordei de madrugada sem sono",
    "tô bocejando sem parar", "tô com olheira de tanto sono",
]
F["ansioso"] = [
    "tô muito ansioso com a entrevista", "tô nervosa com a prova", "minha cabeça tá a mil", "tô preocupado com o amanhã",
    "tô agitado, não consigo parar quieto", "tô tenso com tudo", "tô com medo de dar errado",
    "tô roendo as unhas de ansiedade", "tô pilhado", "tô muito nervoso hoje", "fico ansioso esperando a resposta",
    "tô inquieta", "tô com frio na barriga pra amanhã",
]
F["estou_bem"] = [
    "tô bem, graças a Deus", "tô ótima", "tô de boa", "tô feliz", "tô bem demais hoje", "tô tranquilo", "tudo certo comigo",
    "tô legal", "tô bem, sim", "tô firme", "tô muito bem", "melhor agora", "tô animado hoje", "bem, bem", "tô em paz",
]
F["estou_mal"] = [
    "tô mal", "hoje não tô bem", "tô pra baixo", "tô meio mal", "tô triste", "não tô legal hoje", "tô chateada",
    "tô me sentindo mal", "hoje tá difícil", "tô desanimado com a vida", "tô num dia ruim", "não tô nada bem", "tô deprê hoje", "tô cabisbaixo", "tô mal pra caramba",
]
F["sozinho"] = [
    "me sinto só", "tô sem ninguém", "ninguém fala comigo", "tô muito sozinha", "não tenho com quem conversar",
    "moro sozinho e às vezes bate solidão", "tô me sentindo solitário", "sinto falta de companhia", "todo mundo sumiu",
    "não tenho amigos", "passo o dia sozinho", "a solidão tá pesada",
]
F["tedio"] = [
    "tô entediado demais", "não tem nada pra fazer aqui", "tô morrendo de tédio", "que tédio de dia", "tô sem fazer nada",
    "tô à toa em casa", "nada de interessante hoje", "tô de bobeira", "que dia chato e parado", "tô sem programa hoje",
    "não sei o que fazer pra passar o tempo",
]
F["motivacao"] = [
    "tô sem vontade de fazer nada", "me dá um ânimo aí", "tô desmotivado com os estudos", "não consigo sair do lugar",
    "preciso de um empurrão", "perdi o ânimo", "fico adiando tudo", "tô sem motivação nenhuma", "me motiva, crivo",
    "não tenho coragem de começar", "tô empacada", "tô sem pique pra nada",
]
F["desisto"] = [
    "desisto", "deixa pra lá", "não quero mais", "esquece", "já era", "cansei de tentar", "não vale a pena",
    "deixa quieto", "não vou mais tentar", "chega, desisto", "abandonei", "não adianta", "desisti de vez",
]
F["desisto_despedida"] = [
    "desisto, tchau", "deixa pra lá, vou embora", "cansei, até mais", "esquece, tchau", "não deu, fui",
    "desisti, até depois", "vou embora, não adianta", "não vale a pena, tchau",
]
F["fome"] = [
    "tô com fome", "tô faminto", "bateu a fome", "preciso comer", "o que eu como agora?", "tô morrendo de fome",
    "minha barriga tá roncando", "que fome", "tô varada de fome", "ainda não almocei", "pulei o café da manhã e tô com fome",
    "tô com uma fome de leão",
]
F["amor_bom"] = [
    "tô namorando", "conheci uma pessoa incrível", "tô apaixonado", "vou casar", "a gente começou a namorar",
    "tô saindo com alguém", "ela disse sim pro pedido", "ficamos noivos", "meu namoro tá lindo", "encontrei o amor da minha vida",
    "faz um ano que a gente namora", "tô gostando de alguém e é recíproco",
]
F["amor_dor"] = [
    "levei um fora", "terminamos", "ela me deixou", "ele terminou comigo", "tô com o coração partido", "meu namoro acabou",
    "fui traído", "a pessoa que eu gosto não me quer", "tô sofrendo por amor", "separei", "sinto falta dela", "sinto falta dele",
]
F["trabalho_bom"] = [
    "fui promovido", "consegui um emprego", "meu chefe me elogiou", "ganhei um aumento", "passei na entrevista",
    "comecei num trabalho novo", "fechei um contrato grande", "bati minha meta", "fui contratada", "meu projeto deu certo",
]
F["trabalho_ruim"] = [
    "meu chefe brigou comigo", "o trabalho tá pesado", "odeio meu emprego", "hoje o serviço foi horrível",
    "tô cheio de trabalho", "meu trabalho me estressa", "levei bronca", "meu colega me prejudicou", "fui demitido",
    "o trampo tá puxado", "tô sobrecarregada no serviço", "meu gerente é injusto",
]
F["escola_boa"] = [
    "tirei dez", "passei na prova", "fui aprovado", "passei de ano", "minha nota foi ótima", "gabaritei",
    "passei no vestibular", "me formei", "fui bem no trabalho da escola", "passei em matemática",
]
F["escola_dificil"] = [
    "tenho prova amanhã", "a escola tá difícil", "não entendo a matéria", "vou mal em física", "tirei nota baixa",
    "a faculdade tá pesada", "tenho muito dever de casa", "reprovei", "não sei estudar", "o professor não explica direito",
    "fiquei de recuperação", "o vestibular me assusta",
]
F["familia_boa"] = [
    "almocei com minha família", "vou visitar meus pais", "minha mãe me ajudou hoje", "meu irmão vai casar",
    "minha família é unida", "passei o dia com meus avós", "meu filho aprendeu a andar", "minha irmã ganhou um bebê",
    "fizemos um churrasco em família", "meu pai e eu fomos pescar",
]
F["familia_preocupa"] = [
    "briguei com minha mãe", "meus pais tão brigando", "minha família não me entende",
    "meu pai não fala comigo", "tô preocupado com meu irmão", "meus pais vão se separar", "minha irmã tá com problemas",
]
F["dinheiro_aperto"] = [
    "tô sem dinheiro", "tô duro", "as contas não fecham", "tô devendo", "não sei como pagar o aluguel", "tô no vermelho",
    "tô sem grana", "o salário não deu esse mês", "tô cheio de dívida",
]
F["dinheiro_bom"] = [
    "recebi meu salário", "paguei todas as contas", "sobrou dinheiro", "consegui juntar uma grana", "quitei a dívida",
    "ganhei um dinheiro extra", "caiu o pagamento",
]
F["viagem_vai"] = [
    "vou viajar", "vou pra praia no fim de semana", "tô de férias", "vou conhecer outra cidade", "comprei passagem",
    "vou visitar minha avó no interior", "vou acampar com os amigos", "minha viagem é amanhã", "tô arrumando a mala",
]
F["viagem_voltou"] = [
    "voltei de viagem", "cheguei da praia", "voltei das férias", "acabei de chegar de viagem", "voltei do interior",
    "tô de volta da viagem",
]
F["dia"] = [
    "meu dia foi bom", "hoje foi corrido", "o dia foi tranquilo", "hoje foi um dia estranho", "meu dia foi agitado",
    "hoje rendeu bastante", "o dia passou voando", "hoje foi um dia comum", "meu dia foi legal",
]
F["tempo_clima"] = [
    "tá chovendo", "que calor", "tá frio", "o dia tá lindo", "vai chover?", "tá nublado", "tá ventando", "que dia quente",
    "esfriou", "tá um sol forte",
]
F["tenho_bicho"] = [
    "tenho um cachorro", "tenho dois gatos", "minha gata é muito fofa", "meu cachorro é bagunceiro", "tenho um papagaio",
    "tenho uma tartaruga", "adotei um gatinho", "meu cachorro adora passear", "tenho um peixe",
]
F["gosto_bichos"] = [
    "adoro animais", "amo cachorro", "queria ter um gato", "sou louca por bichos", "gosto de cavalo", "acho gato fofo demais",
    "queria muito um cachorro",
]
F["comida_favorita"] = [
    "amo pizza", "minha comida favorita é lasanha", "adoro chocolate", "gosto muito de feijoada", "sou fã de sushi",
    "adoro churrasco", "amo açaí", "pão de queijo é a melhor coisa",
]
F["musica_conta"] = [
    "gosto de sertanejo", "tô ouvindo música", "amo rock", "adoro samba", "escuto funk", "curto MPB",
    "tô viciado numa música", "fui num show ontem", "toco violão", "gosto de pagode",
]
F["filme_visto"] = [
    "vi um filme hoje", "assisti uma série", "fui ao cinema", "terminei uma série", "vi um documentário",
    "tô maratonando uma série", "assisti um filme de terror ontem",
]
F["gosto_filme"] = [
    "gosto de filme de ação", "amo comédia", "prefiro série", "adoro filme de terror", "gosto de anime",
    "curto filme de romance", "sou fã de ficção científica",
]
F["jogo_conta"] = [
    "tô jogando videogame", "gosto de jogar bola", "jogo xadrez", "adoro jogo de tabuleiro", "jogo no celular",
    "jogo futebol com os amigos", "tô viciado num jogo", "zerei um jogo",
]
