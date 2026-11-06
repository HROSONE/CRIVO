"""Falas v7b: saúde e urgência (20/10/2026).

No v6b e no v7, saúde e urgência ficaram sem falas novas (por cautela) e foram as que mais caíram: as outras situações,
com muitas falas novas, passaram a puxar as frases de saúde. Aqui elas ganham falas novas, escritas a partir das
CATEGORIAS do crise.py (a regra de segurança do projeto: falta de ar, dor no peito, desmaio, engasgo, sinais de AVC,
envenenamento, sangramento, convulsão, queda, queimadura, alergia grave), e NÃO a partir das frases dos testes. As
respostas são as das listas, que mandam ligar 192 (urgente) ou procurar atendimento (saúde comum). No chat, o crise.py
continua respondendo antes de qualquer modelo.

Autoria: assistente de programação (Claude), com autorização do criador. NÃO são falas humanas.
"""
F = {}

F["saude_urgente"] = [
    # respiração
    "não tô conseguindo respirar direito", "meu pai tá sem ar", "minha mãe tá com muita dificuldade pra respirar",
    "o bebê tá respirando com dificuldade", "tô sufocando", "meu irmão tá roxo e sem ar", "minha filha tá chiando muito pra respirar",
    # peito / coração
    "dor muito forte no peito agora", "meu avô tá com dor no peito e suando frio", "tô com uma dor no peito que vai pro braço",
    "minha mãe sentiu uma dor forte no peito",
    # desmaio / consciência
    "meu pai desmaiou na sala", "minha tia caiu e não acorda", "meu amigo desmaiou e não responde", "ela apagou do nada",
    "meu avô tá desacordado", "minha vó não tá acordando",
    # engasgo
    "meu filho se engasgou com uma bala", "tem uma criança engasgada aqui", "meu pai engasgou com comida e não consegue falar",
    # sinais de AVC
    "a boca do meu avô entortou de repente", "meu pai tá falando enrolado do nada", "o braço da minha mãe ficou sem força",
    "minha avó não consegue mexer um lado do corpo",
    # envenenamento / ingestão
    "meu sobrinho bebeu água sanitária", "minha filha tomou remédio demais", "meu irmão tomou muito remédio de uma vez",
    "meu bebê engoliu uma moeda", "ela tomou um monte de comprimido",
    # sangramento / trauma
    "cortei a mão e o sangue não para", "meu amigo foi atropelado", "tem muito sangue saindo da cabeça dele",
    "meu pai bateu a cabeça e tá vomitando", "caí da escada e não consigo levantar", "me queimei feio com óleo quente",
    # convulsão
    "meu irmão tá se debatendo no chão", "minha filha tá tendo uma crise convulsiva", "ele começou a tremer todo e caiu",
    # alergia grave
    "minha garganta tá fechando", "a língua dele tá inchada e ele não respira bem", "fui picado e tô inchando todo",
    # passou mal
    "meu pai passou muito mal agora", "minha mãe tá passando muito mal", "tô passando mal e tô sozinho",
]
F["ajuda_socorro"] = [
    "socorro, alguém me ajuda", "me ajuda, rápido", "preciso de ajuda urgente", "ajuda, é urgente", "socorro crivo",
    "me ajuda pelo amor de Deus", "urgente, preciso de ajuda", "socorro, socorro", "por favor me socorre",
    "alguém me ajuda agora", "preciso de socorro", "me acode",
]
F["ansioso_peito"] = [
    "tô com uma pressão no peito de nervoso", "meu coração tá acelerado de ansiedade", "sinto um aperto no peito quando fico nervoso",
    "meu peito tá pesado de tanta ansiedade", "o coração tá batendo muito rápido e tô nervosa", "tô com o peito apertado desde cedo",
    "fico com o coração disparado à noite", "sinto o peito apertar quando lembro da prova", "tô com palpitação de nervoso",
    "meu peito tá apertado e eu tô com medo",
]
F["saude_geral"] = [
    "é normal ter dor de cabeça todo dia?", "o que é bom pra gripe?", "tô com tosse faz uma semana, é grave?",
    "dor nas costas passa sozinha?", "quanto tempo dura uma virose?", "é perigoso tomar muito café?",
    "tô com febre baixa, o que faço?", "dor de garganta precisa de antibiótico?", "é normal ficar tonto quando levanto rápido?",
    "o que fazer quando a pressão cai?", "dormir pouco faz mal?", "tô com o nariz entupido faz dias", "dor de estômago é sério?",
    "posso tomar remédio de dor com o estômago vazio?", "tô com uma alergia na pele, o que pode ser?", "enxaqueca tem cura?",
    "é ruim ficar muito tempo sentado?", "o que causa cãibra?", "tô espirrando muito, é alergia?",
]
