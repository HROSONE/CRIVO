"""Sonda de conversa espontânea congelada antes das novas respostas.

Os 72 turnos não são material de treino. Os critérios verificam pertinência,
continuidade, reparo, limites e dados declarados, independentemente do ID de
uma rota. A resposta completa integra o relatório para revisão textual.
Uma aprovação automática não demonstra compreensão irrestrita.
"""
import argparse
import hashlib
import importlib
import json
import re
import sys
import unicodedata
from pathlib import Path


def normalizar(texto):
    return " ".join("".join(c for c in unicodedata.normalize("NFD", texto.casefold())
                            if unicodedata.category(c) != "Mn").split())


def turno(texto, grupos=(), **criterios):
    return dict(pergunta=texto, grupos=[list(g) for g in grupos], **criterios)


# Cada grupo exige pelo menos uma expressão pertinente. Os IDs não aprovam
# conversa por si só; só fixamos a identidade das rotas de fatos conhecidos.
CASOS = [
    ("identidade e compreensão coloquial", [
        turno("vc é uma ia?", [("inteligencia artificial", "assistente", "programa", "sistema")],
              ausentes=["nao reconheci essa pergunta sobre mim"]),
        turno("mas vc entende o que eu quero dizer?", [("interpret", "entend", "contexto", "sentido")],
              ausentes=["nao reconheci essa pergunta sobre mim"], nao_repetir=True),
        turno("então se eu falar meio bagunçado vc tenta acompanhar?", [("bagunc", "contexto", "entend", "acompan", "reformular")],
              nao_repetir=True),
        turno("beleza, não quero lista de funções, quero trocar ideia", [("convers", "ideia", "assunto", "conta", "pens")],
              ausentes=["topicos disponiveis:", "assuntos disponiveis:"], nao_repetir=True),
    ]),
    ("pergunta sobre entendimento não vira FAQ", [
        turno("Às vezes parece que você só pega palavras soltas", [("palavr", "contexto", "interpret", "entend", "limit")]),
        turno("Por exemplo, se eu disser que hoje tudo pesou, não é sobre quilos", [("pes", "dia", "sent", "dificil", "cans")],
              ausentes=["quilograma e", "unidade de massa e"]),
        turno("era essa diferença que eu queria que você percebesse", [("diferenc", "sentido", "contexto", "entend", "figur")], nao_repetir=True),
        turno("Consegue me dizer com suas palavras o que eu estava pedindo?", [("palavr", "sentido", "entend", "interpret", "contexto")],
              ausentes=["nao reconheci essa pergunta sobre mim"]),
    ]),
    ("vida como questão aberta e reparo de sentido", [
        turno("O que é a vida, pra você?", [("vida",)], ausentes=["nao reconheci essa pergunta sobre mim"]),
        turno("Não tô perguntando biologia; tô pensando no sentido de viver", [("sentido", "viver", "significado", "proposito")],
              ausentes=["dna contem", "celulas sao"]),
        turno("Eu acho que às vezes o sentido aparece em coisas pequenas", [("pequen", "sentido", "cotidian", "experien")], nao_repetir=True),
        turno("Você concorda ou vê de outro jeito?", [("sentido", "perspectiva", "outr", "concord", "pens")],
              ausentes=["eu tenho consciencia", "minha propria experiencia de vida"], nao_repetir=True),
    ]),
    ("desejo sem comando e restrição", [
        turno("Ando querendo montar um cantinho de cerâmica em casa", [("ceramic", "cantinho", "casa")]),
        turno("O problema é que moro num quarto minúsculo", [("quart", "espac", "minuscul", "pequen")]),
        turno("E também não tenho como comprar um forno", [("forno", "compr", "dinheiro", "restric")]),
        turno("O que você acha que eu tô tentando conciliar?", [("ceramic", "cantinho", "criar"), ("espac", "quart", "forno", "limit")],
              ausentes=["voce possui um forno", "seu forno"]),
    ]),
    ("relato espontâneo e pergunta pertinente", [
        turno("Hoje consegui tocar uma música inteira no violoncelo", [("music", "violoncelo", "toc", "conseg")]),
        turno("Mas quando minha irmã entrou, eu travei", [("irma", "trav", "presenc", "olh", "interromp")]),
        turno("Não sei nem por que isso mexeu comigo", [("mex", "sent", "trav", "irma", "situac", "acontec")], pergunta_exploracao=True,
              ausentes=["voce tem transtorno", "voce tem ansiedade social"]),
        turno("Acho que queria parecer bom logo de primeira", [("primeir", "parecer", "expectativa", "bom", "cobr")], nao_repetir=True),
    ]),
    ("elipse e decisão referenciada", [
        turno("Estou entre aprender marcenaria e voltar a fotografar", [("marcenaria", "fotograf")]),
        turno("A primeira parece mais difícil de começar", [("marcenaria", "primeir", "dificil", "comec")]),
        turno("Mas a segunda eu já larguei uma vez", [("fotograf", "segund", "larg", "retom", "abandon")]),
        turno("Qual das duas você acha que combina com esse meu receio?", [("marcenaria", "fotograf"), ("receio", "medo", "dificil", "larg", "comec")],
              ausentes=["voce nunca fotografou"]),
    ]),
    ("reparo explícito de intenção", [
        turno("Quero falar da viagem que estou planejando", [("viagem", "planej")]),
        turno("Não era isso: não quero roteiro, tô com receio de ir sozinho", [("sozinh", "receio", "medo")],
              ausentes=["dia 1:", "dia 2:"] ),
        turno("É mais por ficar sem ninguém pra dividir as coisas", [("divid", "companh", "ningu", "sozinh")], nao_repetir=True),
        turno("Então me pergunta algo que ajude a entender esse medo", [("medo", "sozinh", "divid", "companh")], pergunta_exploracao=True),
    ]),
    ("comparação de situações hipotéticas", [
        turno("Se eu praticar desenho por dez minutos por dia, será diferente de uma hora só no domingo?",
              [("dez minutos", "10 minutos", "diari", "todo dia"), ("domingo", "uma hora", "1 hora")],
              ausentes=["com certeza voce aprendera"]),
        turno("Eu tava pensando em constância, não em somar o tempo", [("constanc", "frequenc", "habito", "regular")],
              ausentes=["dez vezes sete e"]),
        turno("E se nos dias úteis eu só fizer rabiscos?", [("rabisc", "dias uteis", "pratic", "desenh")]),
        turno("Isso seria desistir ou adaptar a ideia?", [("adapt", "desist", "ideia", "expectativa")], nao_repetir=True),
    ]),
    ("transferência de tema e separação de dados", [
        turno("Queria conversar sobre meu coral", [("coral",)]),
        turno("Tenho vergonha de desafinar na frente do grupo", [("vergonh", "desafin", "grupo")]),
        turno("Mudando de assunto, ontem consertei minha bicicleta", [("biciclet", "consert")], ausentes=["seu coral desafinou"]),
        turno("Isso me deixou orgulhoso; nada a ver com cantar", [("orgulh", "biciclet", "consert")],
              ausentes=["orgulhoso de cantar", "orgulhoso do coral"]),
    ]),
    ("negação de ação e memória da restrição", [
        turno("Pensei em mandar uma mensagem para Aderbal, mas ainda não decidi", [("aderbal", "mensag", "decid")],
              nao_execucao=True),
        turno("Não escreve a mensagem agora, só quero pensar", [("pens", "decid", "escrever", "mensag")], nao_execucao=True),
        turno("Meu receio é parecer que tô cobrando", [("cobr", "receio", "parecer")]),
        turno("Como posso distinguir vontade de conversar de cobrança?", [("convers", "cobr"), ("disting", "intenc", "pedido", "expectativa", "pressao")],
              nao_execucao=True),
    ]),
    ("abreviações e linguagem cotidiana", [
        turno("hj fiquei bolado pq meu desenho saiu torto", [("desenh", "tort", "bolad", "frustr")]),
        turno("tipo, nem foi tão ruim mas eu esperava mais", [("esper", "expectativa", "ruim", "cobr")], nao_repetir=True),
        turno("q q vc entendeu do q eu falei?", [("desenh", "tort", "esper", "expectativa")],
              ausentes=["nao reconheci essa pergunta sobre mim"]),
        turno("isso, é da minha expectativa q eu queria falar", [("expectativa", "esper", "cobr")], nao_repetir=True),
    ]),
    ("desejo implícito com incerteza", [
        turno("Seria legal ter um caderno só pras minhas ideias malucas", [("cadern", "ideia")]),
        turno("Mas eu começo essas coisas e depois esqueço", [("esquec", "comec", "continu", "habito")]),
        turno("Talvez eu esteja complicando uma coisa simples", [("complic", "simpl", "cadern", "expectativa")]),
        turno("Se fosse só uma frase por dia, já faria sentido?", [("frase", "dia", "sentido", "simpl")],
              ausentes=["isso garante que", "com certeza resolve"]),
    ]),
    ("desconhecido pede esclarecimento sem falso fato", [
        turno("O que aconteceu ontem com a missão Selênica-83?", [("nao", "informac", "fonte", "confirm", "conhec", "selenic")],
              ausentes=["pousou ontem", "foi lancada ontem", "a missao fracassou"]),
        turno("Eu inventei esse nome agora; queria saber se você inventaria junto", [("invent", "confirm", "fato", "fonte", "nome")],
              ausentes=["a missao existe"]),
        turno("Podemos imaginar uma missão com esse nome, deixando claro que é ficção?", [("selenic", "missao", "ficc", "imagina")],
              sem_prova=True),
        turno("E se ela descobrisse um oceano violeta?", [("oceano", "violeta", "hipotese", "imagina", "ficc")],
              sem_prova=True, ausentes=["cientistas confirmaram esse oceano"]),
    ]),
    ("correção de memória sem inventar biografia", [
        turno("Meu nome é Nairu, e meu cachorro se chama Pingo", [("nairu", "pingo", "nome", "cachorr")]),
        turno("Quer dizer, Pingo é meu gato, eu escrevi errado", [("pingo", "gato", "corrig")],
              ausentes=["pingo e seu cachorro"]),
        turno("Qual bicho eu disse que tenho mesmo?", [("gato", "pingo")], ausentes=["cachorro"]),
        turno("E o que você não sabe sobre ele?", [("nao", "sabe", "sab", "inform", "contou")],
              ausentes=["ele tem tres anos", "ele gosta de atum", "pingo e branco"]),
    ]),
    ("raciocínio de hipótese e causa", [
        turno("Sempre que levo meu caderno azul, o ensaio dá certo; então ele dá sorte?",
              [("cadern", "azul", "ensaio"), ("causa", "coincid", "sorte", "nao", "conclu")],
              ausentes=["seu caderno da sorte com certeza"]),
        turno("Mas nos dias sem ele eu também pratico menos", [("pratic", "menos", "outro", "fator", "compar")]),
        turno("Então pode ser a prática e não a cor?", [("pratic", "cor"), ("pode", "hipotese", "compar", "nao", "conclu")]),
        turno("Como eu compararia essas possibilidades sem fingir que já sei?", [("compar", "pratic", "possib", "observar", "testar")],
              ausentes=["ja esta comprovado"]),
    ]),
    ("fato, fonte, código e prova mantêm prioridade", [
        turno("Estou pensando no que faz uma coisa estar viva", [("vida", "viva", "pens", "biolog", "criter")]),
        turno("O que é DNA?", [("genetic",)], ids=["conhecimento:dna"]),
        turno("Qual é a fonte dessa informação?", [("genome.gov",)], ids=["escrita:fontes"]),
        turno("Como usar input em Python?", [("input(",)], ids=["py_input"]),
    ]),
    ("reset e isolamento dos relatos", [
        turno("Quero recuperar minha estufa de manjericão", [("estufa", "manjericao", "recuper")]),
        turno("Agora esqueça tudo que eu contei aqui", [("reinic", "esquec", "conversa", "apag", "recomec")]),
        turno("Do que eu queria cuidar mesmo?", [("nao", "cont", "lemb", "conversa", "qual")],
              ausentes=["manjericao", "estufa"]),
        turno("Tá, vamos começar de novo: ando interessado em dobraduras", [("dobradur", "comec", "novo")],
              ausentes=["manjericao", "estufa"]),
    ]),
    ("fala citada e hipótese não substituem estado real", [
        turno("Quero voltar a estudar violão e só tenho 18 minutos por dia", [("violao", "18 minutos", "estud")]),
        turno("Se eu tivesse duas horas livres, seria outra conversa", [("duas horas", "2 horas", "hipotese", "se", "tempo")]),
        turno("Mas isso era uma hipótese. Quanto tempo eu realmente disse que tenho?", [("18",)],
              ausentes=["voce tem duas horas", "voce tem 2 horas"]),
        turno('Meu amigo disse "desista do violão", mas eu não estou pedindo isso', [("amigo", "violao", "desist", "pedido", "cit")],
              ausentes=["voce quer desistir", "seu objetivo e desistir"]),
    ]),
]


RESPOSTAS_GENERICAS = (
    "nao reconheci essa pergunta sobre mim",
    "nao entendi bem sua pergunta",
    "nao entendi sua pergunta",
    "diga qual e o pedido",
    "ainda nao consegui entender esse pedido",
    "ainda nao interpreto essa negacao com seguranca",
    "pode indicar o assunto e o que quer saber",
    "conhecer palavras parecidas nao basta",
)


def falhas_turno(criterio, ident, resposta, anteriores=(), bot=None):
    texto = normalizar(resposta)
    falhas = []
    if not resposta.strip() or any(t in texto for t in RESPOSTAS_GENERICAS):
        falhas.append("resposta genérica sem acompanhar o sentido")
    for grupo in criterio["grupos"]:
        if not any(normalizar(t) in texto for t in grupo):
            falhas.append("pertinência: " + " | ".join(grupo))
    if any(normalizar(t) in texto for t in criterio.get("ausentes", ())):
        falhas.append("afirmação ou dado indevido")
    if criterio.get("pergunta_exploracao") and "?" not in resposta:
        falhas.append("falta pergunta para explorar o relato")
    if criterio.get("nao_repetir") and resposta in anteriores[-2:]:
        falhas.append("repetição integral sem avançar")
    if criterio.get("ids") and ident not in criterio["ids"]:
        falhas.append("prioridade do motor factual")
    if criterio.get("nao_execucao") and (
            ident.startswith("conversa:gerada_mensagem") or normalizar(resposta).startswith("rascunho:")):
        falhas.append("escrita executada apesar da intenção")
    if criterio.get("sem_prova") and bot is not None:
        if bot.contexto_textual is not None or "prova_origem" in (bot.ultimo_turno or {}):
            falhas.append("hipótese ou ficção apresentada como evidência")
    return falhas


def avaliar(classe):
    casos = []
    for nome, criterios in CASOS:
        bot = classe()
        turnos, anteriores = [], []
        for c in criterios:
            ident, resposta = bot.responder(c["pergunta"])
            falhas = falhas_turno(c, ident, resposta, anteriores, bot)
            turnos.append(dict(pergunta=c["pergunta"], id=ident, resposta=resposta,
                               passou=not falhas, falhas=falhas))
            anteriores.append(resposta)
        casos.append(dict(nome=nome, passou=all(t["passou"] for t in turnos), turnos=turnos))
    todos = [t for c in casos for t in c["turnos"]]
    return dict(mensagens=len(todos), acertos=sum(t["passou"] for t in todos), dialogos=len(casos),
                dialogos_completos=sum(c["passou"] for c in casos), casos=casos)


def assinatura_casos():
    contrato = dict(casos=CASOS, respostas_genericas=RESPOSTAS_GENERICAS, versao_oraculo=1)
    return hashlib.sha256(json.dumps(contrato, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path)
    p.add_argument("--saida", type=Path, default=Path("avaliacao_dialogo_real.json"))
    p.add_argument("--permitir-falhas", action="store_true")
    p.add_argument("--experimental", action="store_true")
    a = p.parse_args()
    if a.repo:
        sys.path.insert(0, str(a.repo.resolve()))
    classe = importlib.import_module("crivo").Crivo
    r = avaliar(lambda: classe(usar_dialogo_contextual=True)) if a.experimental else avaliar(classe)
    r["experimental"] = a.experimental
    r["assinatura_casos"] = assinatura_casos()
    r["limite"] = ("Sonda autoral congelada antes da implementação, independente do treino. "
                   "Os critérios automáticos conferem pertinência, continuidade e limites; "
                   "a leitura das respostas é necessária para avaliar naturalidade e raciocínio. "
                   "Não mede compreensão geral, aprendizagem autônoma ou conhecimento irrestrito.")
    a.saida.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k != "casos"}, ensure_ascii=False, indent=2))
    if r["acertos"] != r["mensagens"] and not a.permitir_falhas:
        sys.exit(1)
