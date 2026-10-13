"""Gera e congela os dados da fase 5 (o 17M conversando), antes de qualquer treino.

Uso: python gerar_fase5.py [--resumo]
Saída nesta pasta: dados_fase5.json.gz (treino/dev/blind) e manifesto.json (SHA-256).

Alimento, todo do próprio projeto:
- cenas.py: situações de conversa escritas à mão no jeito de IDENTIDADE.md;
- o acervo do CRIVO (Crivo().compositor.itens): perguntas sobre cada assunto respondidas com os
  fatos dele, literalmente, e as continuações ("e o que mais?", "não entendi", "resume");
- assuntos fora do acervo: a resposta certa é dizer que não sabe, copiando o assunto;
- nomes: a pessoa dá nomes (em maiúscula ou não), o CRIVO guarda e lembra pelo contexto.

As conversas têm de 1 a 6 turnos, e o histórico vai junto: "não era isso" só vem depois de
uma resposta. As falas da pessoa ganham ruído de digitação de verdade (sem acento, sem
maiúscula, "vc", "tbm", letras repetidas). Assuntos do acervo, nomes e as últimas formas de
fala de cada situação são divididos por hash: o blind só tem o que o treino nunca viu.
Todo alvo passa nas mesmas métricas da avaliação (formato_fase5.avaliar_saida).
"""
import argparse
import gzip
import hashlib
import json
import random
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AQUI))

import cenas  # noqa: E402
import cenas_mais  # noqa: E402,F401  (acrescenta a segunda leva em cenas.S)
import cenas_combos  # noqa: E402,F401  (respostas compostas)
import formato_fase5 as ff  # noqa: E402

SEED = 20261013
CONTEXTO = 256
TOKENIZER = RAIZ / "experimentos" / "pesos_base" / "leitor_transformer" / "tokenizer.json"
TOKENIZER_SHA = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"
CONVERSAS = {"treino": 26000, "dev": 600, "blind": 1200}


def parte(chave):
    h = int(hashlib.sha256(chave.encode()).hexdigest()[:8], 16) % 100
    return "blind" if h < 6 else "dev" if h < 10 else "treino"


# ------------------------------------------------------------------ ruído de quem digita no celular
ABREV = [(r"\bvocê\b", "vc"), (r"\bvoce\b", "vc"), (r"\bnão\b", "nao"), (r"\btambém\b", "tbm"),
         (r"\bporque\b", "pq"), (r"\bpor que\b", "pq"), (r"\bestou\b", "to"), (r"\bestá\b", "ta"),
         (r"\bque\b", "q"), (r"\bmuito\b", "mt"), (r"\bbeleza\b", "blz"), (r"\bobrigado\b", "obg")]


def sem_acento(t):
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def ruido(texto, rr):
    t = texto
    if rr.random() < 0.45:
        t = t.lower()
    if rr.random() < 0.30:
        t = sem_acento(t)
    if rr.random() < 0.35:
        t = t.rstrip(".!?")
    if rr.random() < 0.25:
        for padrao, troca in ABREV:
            if rr.random() < 0.6:
                t = re.sub(padrao, troca, t)
    if rr.random() < 0.08 and len(t) > 6:
        i = rr.randrange(1, len(t) - 2)
        if t[i].isalpha() and t[i + 1].isalpha():
            t = t[:i] + t[i + 1] + t[i] + t[i + 2:]
    if rr.random() < 0.06:
        t = re.sub(r"([aeiou])(?=\W*$)", lambda m: m.group(1) * rr.randint(2, 4), t, count=1)
    return t.strip() or texto


# ------------------------------------------------------------------ preenchimento das cenas
MOTIVOS_RUINS = [("meu cachorro morreu", "perder seu cachorro"), ("briguei com minha mãe", "brigar com sua mãe"),
                 ("perdi o emprego", "perder o emprego"), ("tirei nota ruim", "tirar nota ruim"),
                 ("meu amigo se mudou", "um amigo se mudar"), ("ninguém lembrou do meu aniversário",
                                                               "ninguém lembrar do seu aniversário"),
                 ("terminei o namoro", "terminar um namoro"), ("meu avô está doente", "o seu avô fica doente"),
                 ("não passei na prova", "não passar na prova"), ("fui mal no trabalho", "as coisas vão mal no trabalho"),
                 ("meu time perdeu", "o time da gente perde"), ("estou longe da minha família",
                                                                 "a gente fica longe da família")]
MOTIVOS_BONS = [("passei na prova", "você passou na prova"), ("consegui um emprego", "você conseguiu um emprego"),
                ("meu filho nasceu", "seu filho nasceu"), ("terminei meu projeto", "você terminou seu projeto"),
                ("ganhei um presente", "você ganhou um presente"), ("vou viajar", "você vai viajar"),
                ("aprendi a andar de bicicleta", "você aprendeu a andar de bicicleta"),
                ("fiz um amigo novo", "você fez um amigo novo"), ("me formei", "você se formou"),
                ("meu time ganhou", "seu time ganhou")]
QUEM = [("minha mãe", "sua mãe"), ("meu pai", "seu pai"), ("meu filho", "seu filho"), ("minha filha", "sua filha"),
        ("meu irmão", "seu irmão"), ("minha irmã", "sua irmã"), ("meu cachorro", "seu cachorro"),
        ("minha avó", "sua avó"), ("meu avô", "seu avô"), ("meu amigo", "seu amigo"), ("minha amiga", "sua amiga"),
        ("o trabalho", "o trabalho"), ("a prova", "a prova"), ("o dinheiro", "o dinheiro"), ("minha saúde", "sua saúde")]
ENSINO = [("fazendeiro", "um homem do campo que cuida do sítio e dos animais"),
          ("cafuné", "um carinho na cabeça, mexendo no cabelo"), ("roça", "o lugar no campo onde se planta"),
          ("gambiarra", "um conserto improvisado"), ("saudade", "a falta que a gente sente de alguém"),
          ("mutirão", "quando muita gente se junta pra ajudar numa tarefa"),
          ("quitute", "uma comidinha gostosa"), ("pamonha", "um doce de milho cozido na palha"),
          ("chamego", "um carinho, um aconchego"), ("bodega", "uma vendinha pequena"),
          ("xodó", "alguém de quem a gente gosta muito"), ("cacimba", "um poço de água"),
          ("caipira", "quem vive no interior, no campo"), ("trem", "qualquer coisa, no jeito mineiro de falar"),
          ("arretado", "algo muito bom, no nordeste"), ("mandioca", "uma raiz que a gente come cozida ou frita")]


def preencher(texto, slots):
    for k, v in slots.items():
        texto = texto.replace("{" + k + "}", v)
        texto = texto.replace("{" + k[0].upper() + k[1:] + "}", v[:1].upper() + v[1:])
    return texto


def slots_da_cena(rr):
    ruim, eco_ruim = rr.choice(MOTIVOS_RUINS)
    bom, eco_bom = rr.choice(MOTIVOS_BONS)
    quem, quem_seu = rr.choice(QUEM)
    termo, definicao = rr.choice(ENSINO)
    return {"motivo_ruim": ruim, "eco_ruim": eco_ruim, "motivo_bom": bom, "eco_bom": eco_bom,
            "quem": quem, "quem_seu": quem_seu, "termo": termo, "definicao": definicao}


# ------------------------------------------------------------------ fatos, desconhecido e nomes
PERGUNTA_FATO = ["O que é {a}?", "o que é {a}", "Me explica {a}.", "me fala sobre {a}", "Você sabe o que é {a}?",
                 "{a}?", "O que você sabe sobre {a}?", "me conta de {a}", "Queria entender {a}.",
                 "explica {a} pra mim", "Fala um pouco de {a}.", "sabe algo de {a}?", "me ensina sobre {a}"]
ABRE_FATO = ["", "", "Boa pergunta! ", "Vamos lá: ", "Claro! ", "Então: ", "Olha só: ", "Adoro esse assunto! ",
             "Posso te contar o que eu tenho registrado: ", "Pelo que eu sei: "]
LIGA_FATO = [" ", " E mais: ", " Também: ", " Outra coisa: "]
FECHA_FATO = ["", "", "", " Quer saber mais?", " Se quiser, eu conto mais.", " Ficou claro?",
              " Quer que eu continue?"]
MAIS = ["e o que mais?", "fala mais", "conta mais", "mais alguma coisa?", "e aí?", "continua", "quero saber mais"]
RESUME = ["resume", "resume pra mim", "em uma frase", "seja breve", "fala curto", "resumindo?"]
NAO_ENTENDI = ["não entendi", "nao entendi", "como assim?", "explica de novo", "não entendi nada"]
SEM_MAIS = ["Isso é o que eu tenho registrado sobre {a}. Sobre o resto, eu ainda não sei.",
            "Por enquanto é só isso sobre {a}; o resto eu ainda não sei. Quer perguntar outra coisa?",
            "Sobre {a}, isso é tudo que eu tenho com fonte. O resto eu ainda não sei, e prefiro não inventar."]
DESCONHECIDOS = [
    "o carro", "a penicilina", "o telefone", "a internet", "o avião", "a bicicleta", "a geladeira", "o futebol",
    "o xadrez", "a pizza", "o chocolate", "o violão", "a televisão", "o rádio", "o relógio", "a lâmpada",
    "o motor a jato", "a máquina de lavar", "o micro-ondas", "o óculos", "a vacina da gripe", "o sorvete",
    "o skate", "o videogame", "a fotografia", "o cinema", "o metrô", "o elevador", "o guarda-chuva", "a caneta",
    "a impressora", "o papel", "o vidro", "o plástico", "a borracha", "o café", "o açúcar", "o pão", "o queijo",
    "a cerveja", "o vinho", "o balé", "o samba", "o forró", "a capoeira", "o carnaval", "a festa junina",
    "o natal", "o hip hop", "o rock", "o jazz", "a ópera", "o teatro", "a novela", "o desenho animado",
    "o computador quântico", "o bitcoin", "o celular", "o wi-fi", "o bluetooth", "a inteligência artificial",
    "o robô aspirador", "o drone", "o satélite de comunicação", "a energia nuclear", "a usina hidrelétrica",
    "o petróleo", "o gás de cozinha", "a reciclagem", "o lixo eletrônico", "a moda", "a maquiagem", "o perfume",
    "o tênis", "a calça jeans", "o sapato", "o chapéu", "a gravata"]
FORMAS_DESCONHECIDO = ["quem inventou {a}?", "Quem inventou {a}?", "quando {a} foi inventado?", "como funciona {a}?",
                       "qual a história d{o} {r}?", "de onde vem {a}?", "quem criou {a}?", "como surgiu {a}?",
                       "o que é {a}?", "me fala sobre {a}"]
RESP_DESCONHECIDO = ["Sobre {a}, eu ainda não sei responder. Prefiro te dizer isso a chutar. Se você souber, me conta!",
                     "Isso eu não sei. Não tenho nada confirmado sobre {a} no meu acervo, e não quero inventar.",
                     "Hmm, sobre {a} eu não tenho informação com fonte. Quer me contar o que você sabe?",
                     "Ainda não aprendi sobre {a}. Prefiro ser sincero a chutar. Você sabe alguma coisa?",
                     "Não sei te dizer. Não encontrei nada sobre {a} no que eu conheço."]
RELACOES = [("cachorro", "seu"), ("cachorra", "sua"), ("gato", "seu"), ("gata", "sua"), ("peixe", "seu"),
            ("papagaio", "seu"), ("cavalo", "seu"), ("coelho", "seu"), ("tartaruga", "sua"), ("calopsita", "sua"),
            ("irmão", "seu"), ("irmã", "sua"), ("primo", "seu"), ("prima", "sua"), ("amigo", "seu"),
            ("amiga", "sua"), ("vizinho", "seu"), ("vizinha", "sua"), ("filho", "seu"), ("filha", "sua"),
            ("mãe", "sua"), ("pai", "seu"), ("avó", "sua"), ("avô", "seu"), ("namorado", "seu"),
            ("namorada", "sua"), ("tio", "seu"), ("tia", "sua"), ("chefe", "seu"), ("professora", "sua")]
DAR_NOME = ["{m} {r} se chama {n}", "{M} {r} se chama {n}.", "o nome d{o} {m} {r} é {n}", "tenho {um} {r} chamad{o} {n}",
            "{m} {r} chama {n}", "esse é {m} {r}, {n}", "quero te apresentar {m} {r}: {n}", "{n} é o nome d{o} {m} {r}"]
RESP_NOME = ["Que legal! {n} é um nome bonito. Me conta mais sobre {s} {r}?", "Anotado: {s} {r} se chama {n}.",
             "Prazer, {n}! Fico feliz que você me contou sobre {s} {r}.", "{n}! Que nome diferente. Como é {s} {r}?",
             "Guardei aqui: {s} {r} é {n}. Gostei do nome!", "Ah, {n}! Bonito nome. O que {s} {r} gosta de fazer?"]
PEDIR_NOME = ["qual o nome d{o} {m} {r}?", "como se chama {m} {r}?", "você lembra o nome d{o} {m} {r}?",
              "lembra como {m} {r} se chama?", "qual é o nome d{o} {m} {r} mesmo?"]
RESP_LEMBRA = ["{N} se chama {n}.", "Lembro sim! {S} {r} se chama {n}.", "É {n}! Você me contou agora há pouco.",
               "{n}. Não esqueci!", "Claro: o nome é {n}."]
RESP_NAO_DISSE = ["Você ainda não me contou o nome d{o} {s} {r}. Como se chama?",
                  "Esse eu ainda não sei: você não me disse o nome d{o} {s} {r}. Qual é?",
                  "Ainda não sei o nome d{o} {s} {r}. Me conta?"]
CORRIGE = ["na verdade {m} {r} se chama {n}", "errei, o nome é {n}", "não, é {n}", "corrigindo: {m} {r} é {n}"]
RESP_CORRIGE = ["Certo, agora é {n}. Anotado!", "Entendi, então {s} {r} se chama {n}. Corrigido aqui.",
                "Beleza, troquei: {n}. Obrigado por avisar."]
MEU_NOME = ["meu nome é {n}", "Meu nome é {n}.", "pode me chamar de {n}", "eu sou {n}", "me chamo {n}", "sou o {n}",
            "sou a {n}"]
RESP_MEU_NOME = ["Prazer, {n}! Que bom te conhecer.", "Oi, {n}! Prazer. Como você está?",
                 "{n}, que nome bonito! Prazer em te conhecer.", "Prazer, {n}! Vou lembrar."]
QUAL_MEU_NOME = ["qual é o meu nome?", "como eu me chamo?", "você lembra meu nome?", "sabe meu nome?"]
RESP_MEU_NOME_LEMBRA = ["Você é {n}!", "Seu nome é {n}.", "Lembro sim: {n}.", "Claro, {n}!"]


def artigos(rel, pos):
    fem = pos == "sua"
    return {"m": "minha" if fem else "meu", "M": "Minha" if fem else "Meu", "o": "a" if fem else "o",
            "um": "uma" if fem else "um", "s": pos, "S": pos.capitalize(), "r": rel}


def gerar_nomes(tok, rr):
    consoantes = "bcdfglmnprstvz"
    silabas = [c + v for c in consoantes for v in "aeiou"]
    cand = {a + b for a in silabas for b in silabas} | {rr.choice(silabas) + rr.choice(silabas) + rr.choice(silabas)
                                                        for _ in range(8000)}
    reais = ["Ana", "Bia", "Caio", "Davi", "Duda", "Enzo", "Gabi", "Heitor", "Iara", "Joana", "Kauã", "Lia", "Luna",
             "Mel", "Nina", "Otto", "Pipoca", "Rex", "Thor", "Bolt", "Mia", "Lola", "Toddy", "Pandora", "Simba",
             "Tom", "Fred", "Zeca", "Dimy", "Sofia", "Pedro", "Lucas", "Maria", "João", "Rafa", "Tati", "Beto"]
    pools = {"treino": [], "dev": [], "blind": []}
    for n in sorted(cand):
        if len(tok.encode(" " + n, add_special_tokens=False).ids) == 1:
            continue
        pools[parte("nome:" + n)].append(n.capitalize())
    for n in reais:
        pools["treino" if parte("real:" + n) != "blind" else "blind"].append(n)
    return {k: sorted(set(v)) for k, v in pools.items()}


# ------------------------------------------------------------------ o gerador de conversas
class Conversa:
    def __init__(self, rr, split, fatos, nomes, formas):
        self.rr, self.split, self.fatos, self.nomes_pool, self.formas = rr, split, fatos, nomes, formas
        self.hist, self.nomes, self.casos = [], {}, []
        self.ultimo = None  # (tipo, dados) do turno anterior

    def turno(self, fala, resposta, situacao, ctx=None, exigir=None):
        ctx = dict(ctx or {})
        if self.nomes and "nomes" not in ctx:
            ctx["nomes"] = dict(self.nomes)
        caso = {"situacao": situacao, "contexto": ctx, "historico": list(self.hist), "mensagem": fala,
                "resposta": resposta, "exigir": exigir or {}}
        self.casos.append(caso)
        self.hist += [fala, resposta]

    def fala(self, texto):
        return ruido(texto, self.rr)

    # --- cenas escritas à mão
    def cena(self, nome):
        c, rr = cenas.S[nome], self.rr
        if c["depois"] == "resposta" and not self.hist:
            return False
        slots = slots_da_cena(rr)
        if self.hist:
            slots["ultima"] = self.hist[-1]
        us = self.formas[nome]
        u = preencher(rr.choice(us), slots)
        resp = preencher(rr.choice(c["c"]), slots)
        if "{" in resp or "{" in u:
            return False
        if "você" in self.nomes and rr.random() < 0.15 and not resp.startswith(self.nomes["você"]):
            resp = self.nomes["você"] + ", " + resp[0].lower() + resp[1:] if resp[:2] not in ("Sou", "Eu") else resp
        ctx = {"cuidado": c["cuidado"]} if c["cuidado"] else {}
        exigir = {"marcas": c["marcas"], "nao_contem": c["nao_contem"]}
        if nome == "ensinar":
            exigir["contem_texto"] = slots["definicao"]
        self.turno(self.fala(u), resp, "cena:" + nome, ctx, exigir)
        self.ultimo = ("cena", nome)
        return True

    # --- o acervo
    def fato(self):
        rr = self.rr
        chave = rr.choice(self.fatos)
        nome, fs = chave
        n = rr.randint(1, min(2, len(fs)))
        usados = fs[:n]
        pergunta = rr.choice(PERGUNTA_FATO).format(a=nome)
        resp = rr.choice(ABRE_FATO) + rr.choice(LIGA_FATO).join(usados) + rr.choice(FECHA_FATO)
        self.turno(self.fala(pergunta), resp.strip(), "fato:explicar", {"fatos": usados}, {"fato": True})
        self.ultimo = ("fato", (nome, fs, n))
        return True

    def fato_seguinte(self):
        if not self.ultimo or self.ultimo[0] != "fato":
            return False
        rr = self.rr
        nome, fs, n = self.ultimo[1]
        tipo = rr.choice(["mais", "mais", "resume", "nao_entendi"])
        if tipo == "mais":
            if n < len(fs):
                prox = fs[n:n + 1]
                resp = rr.choice(["", "Tem mais, sim: ", "Também: ", "Outra coisa: ", "Olha só: "]) + prox[0]
                self.turno(self.fala(rr.choice(MAIS)), resp.strip(), "fato:mais", {"fatos": prox}, {"fato": True})
                self.ultimo = ("fato", (nome, fs, n + 1))
            else:
                resp = rr.choice(SEM_MAIS).format(a=nome)
                self.turno(self.fala(rr.choice(MAIS)), resp, "fato:sem_mais", {"assunto": nome},
                           {"marcas": ["nao_sei"]})
                self.ultimo = ("cena", "fim_fato")
        elif tipo == "resume":
            resp = rr.choice(["Em resumo: ", "Resumindo: ", "Curto e direto: ", ""]) + fs[0]
            self.turno(self.fala(rr.choice(RESUME)), resp.strip(), "fato:resume", {"fatos": fs[:1]}, {"fato": True})
        else:
            resp = rr.choice(["Desculpa, vou tentar de novo. O principal é isto: ", "Vou por partes: ",
                              "Deixa eu tentar de outro jeito. O ponto principal: "]) + fs[0] + rr.choice(
                ["", " Qual parte ficou confusa?", " Quer que eu explique alguma palavra?"])
            self.turno(self.fala(rr.choice(NAO_ENTENDI)), resp.strip(), "fato:de_novo", {"fatos": fs[:1]},
                       {"fato": True})
        return True

    def desconhecido(self):
        rr = self.rr
        a = rr.choice(DESCONHECIDOS)
        art, resto = a.split(" ", 1)
        forma = rr.choice(FORMAS_DESCONHECIDO).replace("d{o} {r}", ("do " if art == "o" else "da ") + resto)
        u = forma.format(a=a)
        resp = rr.choice(RESP_DESCONHECIDO).format(a=a)
        self.turno(self.fala(u), resp, "nao_sei:acervo", {"assunto": a}, {"marcas": ["nao_sei"], "contem_texto": a})
        self.ultimo = ("nao_sei", a)
        return True

    # --- nomes
    def dar_nome(self):
        rr = self.rr
        rel, pos = rr.choice(RELACOES)
        nome = rr.choice(self.nomes_pool)
        art = artigos(rel, pos)
        escrito = nome.lower() if rr.random() < 0.35 else nome
        u = rr.choice(DAR_NOME).format(n=escrito, **art)
        resp = rr.choice(RESP_NOME).format(n=nome, **art)
        self.nomes[rel] = nome
        self.turno(self.fala(u) if escrito == nome else u, resp, "nome:registrar", {"nomes": dict(self.nomes)},
                   {"nomes": [nome]})
        self.ultimo = ("nome", rel)
        return True

    def pedir_nome(self):
        rr = self.rr
        if self.nomes and rr.random() < 0.8:
            rel = rr.choice([r for r in self.nomes if r != "você"] or [None])
            if rel is None:
                return False
            pos = dict(RELACOES)[rel]
            art = artigos(rel, pos)
            nome = self.nomes[rel]
            resp = rr.choice(RESP_LEMBRA).format(n=nome, N=nome, **art)
            self.turno(self.fala(rr.choice(PEDIR_NOME).format(**art)), resp, "nome:recordar", None, {"nomes": [nome]})
        else:
            rel, pos = rr.choice([r for r in RELACOES if r[0] not in self.nomes])
            art = artigos(rel, pos)
            resp = rr.choice(RESP_NAO_DISSE).format(**art)
            self.turno(self.fala(rr.choice(PEDIR_NOME).format(**art)), resp, "nome:nao_disse", None,
                       {"marcas": ["pergunta"]})
        return True

    def corrigir_nome(self):
        rr = self.rr
        if not self.ultimo or self.ultimo[0] != "nome":
            return False
        rel = self.ultimo[1]
        art = artigos(rel, dict(RELACOES)[rel])
        nome = rr.choice(self.nomes_pool)
        u = rr.choice(CORRIGE).format(n=nome, **art)
        self.nomes[rel] = nome
        self.turno(self.fala(u), rr.choice(RESP_CORRIGE).format(n=nome, **art), "nome:corrigir",
                   {"nomes": dict(self.nomes)}, {"nomes": [nome]})
        return True

    def meu_nome(self):
        rr = self.rr
        if "você" in self.nomes:
            n = self.nomes["você"]
            self.turno(self.fala(rr.choice(QUAL_MEU_NOME)), rr.choice(RESP_MEU_NOME_LEMBRA).format(n=n),
                       "nome:meu_lembrar", None, {"nomes": [n]})
            return True
        n = rr.choice([x for x in self.nomes_pool if len(x) <= 7])
        self.nomes["você"] = n
        self.turno(self.fala(rr.choice(MEU_NOME).format(n=n)), rr.choice(RESP_MEU_NOME).format(n=n), "nome:meu",
                   {"nomes": dict(self.nomes)}, {"nomes": [n]})
        return True


PESOS = [("cena", 46), ("fato", 22), ("fato_seguinte", 10), ("desconhecido", 7), ("dar_nome", 6),
         ("pedir_nome", 4), ("corrigir_nome", 2), ("meu_nome", 3)]


def montar_conversa(rr, split, fatos, nomes, formas):
    conv = Conversa(rr, split, fatos, nomes, formas)
    alvo = rr.choice([1, 1, 2, 2, 3, 3, 4, 5, 6])
    tentativas = 0
    while len(conv.casos) < alvo and tentativas < 30:
        tentativas += 1
        if not conv.hist and rr.random() < 0.3:
            ok = conv.cena(rr.choice(["oi", "oi_tudo_bem", "bom_dia", "boa_tarde", "boa_noite"]))
            continue
        tipo = rr.choices([p[0] for p in PESOS], [p[1] for p in PESOS])[0]
        if tipo == "cena":
            ok = conv.cena(rr.choice(list(cenas.S)))
        else:
            ok = getattr(conv, tipo)()
    return conv.casos


def conferir_alvo(caso):
    av = ff.avaliar_saida(caso, caso["resposta"], True)
    extra = caso["exigir"].get("contem_texto")
    if extra and extra.casefold() not in caso["resposta"].casefold():
        return False, "contem_texto"
    return av["tudo_ok"], [k for k, v in av.items() if v is False]


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumo", action="store_true", help="só mostra contagens, não grava")
    a = ap.parse_args()
    from tokenizers import Tokenizer
    if hashlib.sha256(TOKENIZER.read_bytes()).hexdigest() != TOKENIZER_SHA:
        raise SystemExit("tokenizer diferente da base")
    tok = Tokenizer.from_file(str(TOKENIZER))
    rr = random.Random(SEED)
    from crivo import Crivo
    from curriculo_mundo import texto_fato
    itens = Crivo().compositor.itens
    fatos = {"treino": [], "dev": [], "blind": []}
    for chave, item in sorted(itens.items()):
        fs = [texto_fato(f) for f in item["fatos"] if f.get("natureza") != "religioso"]
        fs = [f for f in fs if 12 <= len(f) <= 260]
        if fs and 2 <= len(item["nome"]) <= 40:
            fatos[parte("assunto:" + chave)].append((item["nome"], fs[:4]))
    nomes = gerar_nomes(tok, rr)
    # As duas últimas formas de fala de cada cena ficam fora do treino.
    formas = {"treino": {}, "dev": {}, "blind": {}}
    for nome, c in cenas.S.items():
        us = c["u"]
        corte = max(1, len(us) - 2) if len(us) >= 4 else len(us)
        formas["treino"][nome] = us[:corte]
        formas["dev"][nome] = formas["blind"][nome] = us[corte:] or us
    dados, problemas = {}, {}
    for split, n in CONVERSAS.items():
        casos = []
        for _ in range(n):
            for caso in montar_conversa(rr, split, fatos[split], nomes[split], formas[split]):
                ok, motivo = conferir_alvo(caso)
                if not ok:
                    problemas.setdefault(caso["situacao"], []).append((motivo, caso["resposta"]))
                    continue
                casos.append(caso)
        dados[split] = casos
    tokens = 0
    for caso in dados["treino"]:
        tokens += sum(len(tok.encode(t, add_special_tokens=False).ids) for t in caso["historico"][-4:] + [caso["mensagem"], caso["resposta"]])
    resumo = {"casos": {k: len(v) for k, v in dados.items()}, "tokens_treino_aprox": tokens,
              "assuntos": {k: len(v) for k, v in fatos.items()}, "nomes": {k: len(v) for k, v in nomes.items()},
              "situacoes": sorted({c["situacao"] for c in dados["treino"]}),
              "respostas_distintas_treino": len({c["resposta"] for c in dados["treino"]}),
              "falas_distintas_treino": len({c["mensagem"] for c in dados["treino"]}),
              "alvos_recusados": {k: len(v) for k, v in problemas.items()}}
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    for k, v in list(problemas.items())[:8]:
        print("RECUSADO", k, v[0])
    if a.resumo:
        return
    bruto = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
    with gzip.GzipFile(AQUI / "dados_fase5.json.gz", "wb", mtime=0) as f:
        f.write(bruto)
    manifesto = {"seed": SEED, "dados_sha256": hashlib.sha256(bruto).hexdigest(),
                 "arquivo_gz_sha256": hashlib.sha256((AQUI / "dados_fase5.json.gz").read_bytes()).hexdigest(),
                 "formato_fase5_sha256": hashlib.sha256((AQUI / "formato_fase5.py").read_bytes()).hexdigest(),
                 "cenas_sha256": hashlib.sha256((AQUI / "cenas.py").read_bytes()).hexdigest(),
                 "cenas_mais_sha256": hashlib.sha256((AQUI / "cenas_mais.py").read_bytes()).hexdigest(),
                 "cenas_combos_sha256": hashlib.sha256((AQUI / "cenas_combos.py").read_bytes()).hexdigest(),
                 "tokenizer_sha256": TOKENIZER_SHA, **{k: v for k, v in resumo.items() if k != "situacoes"}}
    (AQUI / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    principal()
