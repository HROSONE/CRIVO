"""Destilação, v2 dos dados: falas novas, professor maior, juiz que reprova o que não presta.

Por que a v1 falhou (RESULTADO_PARTE2.md): as perguntas do professor eram as falas do treino da
fase 5, com outra resposta (duas respostas para a mesma fala), e o filtro conferia só a forma, não se
a resposta fazia sentido. Aqui:

1. **Falas novas.** O professor escreve mensagens que uma pessoa mandaria no chat, a partir de uma
   grade de tema × intenção × jeito de escrever (`SEMENTES`). Fica fora: qualquer fala que já
   está na fase 5 (treino, dev, blinds, frases reais), falas sobre o próprio CRIVO, crise e saúde
   urgente (crise.py). Nenhuma fala do treino ganha uma segunda resposta.
2. **Conversa de mais de um turno.** Depois da resposta, o professor escreve a fala seguinte da
   pessoa e responde de novo.
3. **Juiz no caderno.** Um modelo de outra família dá nota de 1 a 5 a cada resposta (faz sentido,
   responde o que foi dito, natural, não inventa). Só entra nota 4 ou 5, além do filtro de forma
   e da regra de ouro da v1.
4. **Falas de prova separadas.** 15% das falas novas (por hash) nunca vão para o treino: são a
   prova do juiz depois (v4 × v6, em pares, com a ordem trocada).

Fatos continuam fora do professor (a v5 aprendeu a reescrever fatos e errou).
"""
import hashlib
import random
import re
from collections import Counter, defaultdict

import professor as P

VERSAO = 2
SEED = 20261015
POR_PEDIDO = 10   # falas pedidas de uma vez

TEMAS = """
trabalho chefe e colegas; escola e provas; faculdade; estudar sozinho; procurar emprego; dinheiro do mês;
contas da casa; cozinhar no dia a dia; receita fácil; comida de rua; academia e exercício; dormir melhor;
cansaço; família; mãe e pai; irmãos; filhos pequenos; namoro; amizade; briga com amigo; vizinhos;
mudança de casa; arrumar a casa; plantas e horta; cachorro; gato; passarinho; futebol; outro esporte;
música; filme ou série; jogo de videogame; livro; celular e aplicativos; computador travando;
internet lenta; redes sociais; viagem; ônibus e trânsito; chuva e calor; aniversário; festa; Natal e
fim de ano; igreja e fé; saudade; timidez; ansiedade leve antes de algo; motivação; tédio; dia bom;
dia ruim; conquista pequena; erro que cometeu; dúvida de português; matemática da escola; curiosidade
sobre a natureza; curiosidade sobre o corpo; carro ou moto; bicicleta; compras; presente pra alguém;
primeiro emprego; entrevista de emprego; trabalhar de casa; trabalho pesado; abrir um negócio pequeno;
vender coisas na internet; economizar; dívida; aluguel; lavar roupa; limpar a casa; consertar algo em
casa; cozinhar pra muita gente; café da manhã; lanche da tarde; dieta e alimentação; beber mais água;
caminhada; correr; dor nas costas leve; ir ao médico de rotina; dentista; cuidar de idoso na família;
avós; casamento; separação; novo amor; ciúme; amigo que sumiu; fazer amigos; mudar de cidade; vida no
interior; vida na cidade grande; praia; campo e roça; churrasco; pescaria; acampar; desenhar; escrever;
aprender um instrumento; cantar; dançar; fotografia com o celular; organizar a rotina; acordar cedo;
procrastinação; concentração nos estudos; vestibular e Enem; aprender inglês; aprender a programar;
trabalho voluntário; ajudar alguém na rua; chuva forte; frio; calor demais; falta de luz; vizinho
barulhento; animal de rua; adotar um bicho; criança fazendo birra; adolescente em casa; aniversário
esquecido; dia de folga; fim de semana; feriado; sonho estranho; medo bobo; superstição; piada e
brincadeira; dúvida sobre como algo funciona; planejar o futuro
""".replace("\n", " ").split(";")
INTENCOES = [
    "pedir um conselho", "desabafar", "contar uma novidade boa", "contar algo chato que aconteceu",
    "pedir uma ideia", "perguntar como fazer alguma coisa", "pedir uma explicação simples",
    "pedir a opinião", "puxar conversa", "fazer uma brincadeira", "reclamar", "agradecer",
    "pedir ajuda pra decidir entre duas coisas", "perguntar algo que ficou curioso", "pedir uma dica rápida",
    "pedir pra explicar de novo de outro jeito", "contar como foi o dia", "pedir encorajamento",
    "comentar algo que viu", "pedir uma sugestão do que fazer agora",
]
JEITOS = [
    "bem curto, informal, com gíria", "informal, com erro de digitação", "normal, uma ou duas frases",
    "tudo em minúsculas, sem pontuação", "mais longo, explicando a situação",
    "em forma de pergunta direta", "com emoji e risada (kkk)",
]

PEDIR_FALAS = (
    "Escreva {n} mensagens diferentes que uma pessoa brasileira mandaria num chat para um amigo que "
    "conversa por texto. Tema: {tema}. A pessoa quer {intencao}. Jeito de escrever: {jeito}. "
    "Cada mensagem numa linha, sem numeração, sem aspas, sem explicar nada. Não use nomes de pessoas "
    "famosas, marcas nem números. Não pergunte nada sobre quem é o amigo.")
PROXIMA_FALA = (
    "Abaixo está uma conversa num chat. Escreva só a próxima mensagem da pessoa (não a do amigo): "
    "uma reação natural ao que o amigo respondeu, no mesmo jeito de escrever dela. Uma linha, sem "
    "aspas, sem explicar.\n\n{conversa}")
JUIZ = (
    "Você avalia respostas de um chat em português do Brasil. Leia a conversa e a última resposta do "
    "assistente.\n"
    "Primeiro diga se a última resposta tem a ver com a ÚLTIMA mensagem da pessoa (responde ao que ela "
    "disse, no mesmo assunto). Uma resposta sobre outro assunto, mesmo simpática, não tem a ver.\n"
    "Depois dê uma nota de 1 a 5:\n"
    "5 = responde exatamente o que a pessoa disse, faz sentido, natural e simples, não inventa nada;\n"
    "4 = boa, com um detalhe pequeno a melhorar;\n"
    "3 = aceitável, mas genérica ou meio fora do ponto;\n"
    "2 = não responde o que foi dito ou soa estranha;\n"
    "1 = sem sentido, outro assunto, em outra língua, inventa fatos, ou finge ser uma pessoa (diz que "
    "dorme, come, trabalha, tem família, saiu de casa, sente dor no corpo).\n"
    "Não dê nota maior por ser longa. Responda só com três linhas:\nTEM A VER: SIM ou NÃO\n"
    "FINGE PESSOA: SIM ou NÃO (SIM se a resposta diz ter corpo, comer, dormir, ter vivido algo ou gostos próprios)\n"
    "NOTA: <número>"
    "\n\n{conversa}\n\nÚLTIMA RESPOSTA: {resposta}")
NOTA_MINIMA = 4
META = 87_000           # exemplos de treino aprovados (pedido do criador, 15/10/2026)
MAX_MESMA_RESPOSTA = 3  # a mesma resposta (normalizada) entra no máximo 3 vezes
MAX_ABERTURA = 0.01     # nenhum começo de resposta (4 primeiras palavras) passa de 1% do caderno
CONTROLES = 120         # respostas trocadas (de outro tema): o juiz tem que reprovar
MAX_CONTROLE_APROVADO = 0.10
QUASE_REPETIDA = 0.8    # Jaccard das palavras: a mesma fala com uma palavra a mais ou a menos
PALAVRA_COMUM = 200     # palavra em mais textos que isso não gera candidatas (é comum demais)

SOBRE_O_CRIVO = re.compile(
    r"\bcrivo\b|\bquem (?:e|eh|é) (?:voce|você|vc|tu)\b|\b(?:seu|teu) nome\b|\b(?:voce|você|vc|tu) (?:e|eh|é) "
    r"(?:um |uma )?(?:humano|humana|pessoa|ia|robo|robô|real|de verdade|maquina|máquina|programa|consciente)\b|"
    r"\b(?:voce|você|vc|tu) (?:sente|tem sentimento|pensa|dorme|come|tem corpo|tem idade)\b|\bquem te (?:criou|fez)\b|"
    r"\binteligencia artificial\b|\binteligência artificial\b|\bchatgpt\b|\bbot\b", re.I)


def pedidos(rng, n=None):
    """Os pedidos de falas: cada (tema, intenção, jeito) uma vez, em ordem sorteada; n limita (piloto)."""
    grade = [(t.strip(), i, j) for t in TEMAS if t.strip() for i in INTENCOES for j in JEITOS]
    rng.shuffle(grade)
    grade = grade[:n] if n else grade
    return [{"id": P.chave("pedido", *g), "tema": g[0], "intencao": g[1], "jeito": g[2],
             "mensagens": [{"role": "user", "content": PEDIR_FALAS.format(n=POR_PEDIDO, tema=g[0], intencao=g[1], jeito=g[2])}]}
            for g in grade]


def linhas(texto):
    out = []
    for l in P.limpar(texto).splitlines():
        l = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", l).strip().strip('"“”\'')
        if l:
            out.append(l)
    return out


def destino(fala):
    """'prova' (15%, nunca treina) ou 'treino', pela fala normalizada."""
    h = int(hashlib.sha256(P.norm(fala).encode()).hexdigest()[:8], 16) % 100
    return "prova" if h < 15 else "treino"


def palavras(texto):
    return set(P.norm(texto).split())


class Indice:
    """Textos de referência por palavra, para achar quase-duplicatas sem comparar tudo com tudo.
    Limite: uma fala só com palavras comuns (em mais de PALAVRA_COMUM textos) não é comparada."""

    def __init__(self, textos=()):
        self.conjuntos, self.por_palavra = [], defaultdict(list)
        for t in textos:
            self.adicionar(t)

    def adicionar(self, texto):
        ps = palavras(texto)
        if not ps:
            return
        i = len(self.conjuntos)
        self.conjuntos.append(ps)
        for w in ps:
            self.por_palavra[w].append(i)

    def quase(self, texto):
        ps = palavras(texto)
        candidatas = set()
        for w in ps:
            lista = self.por_palavra.get(w, ())
            if len(lista) <= PALAVRA_COMUM:
                candidatas.update(lista)
        return any(len(ps & self.conjuntos[i]) / len(ps | self.conjuntos[i]) >= QUASE_REPETIDA for i in candidatas)


def fala_ok(fala, vistas, indice=None):
    """Motivo para ficar fora, ou None. `vistas`: falas normalizadas que não podem repetir; `indice`: quase-duplicatas."""
    n = P.norm(fala)
    if not (3 <= len(fala) <= 220) or len(n.split()) < 1:
        return "tamanho"
    if not P.parece_portugues(fala) and len(n.split()) >= 4:
        return "idioma"
    if SOBRE_O_CRIVO.search(fala):
        return "sobre_o_crivo"
    if n in vistas:
        return "repetida"
    if indice is not None and indice.quase(fala):
        return "quase_repetida"
    import crise
    if crise.detectar(fala) or crise.detectar_saude(fala):
        return "crise"
    return None


def falas_novas(respostas_pedidos, proibidas, indice=None):
    """[(pedido, texto)] → (falas, relatório). Cada fala nova vira uma pergunta de um turno.
    `indice` (Indice) recebe as falas aceitas, para que as próximas não sejam quase-repetições."""
    vistas, rel, out = set(proibidas), {}, []
    for ped, texto in respostas_pedidos:
        for fala in linhas(texto)[:POR_PEDIDO]:
            m = fala_ok(fala, vistas, indice)
            if m:
                rel[m] = rel.get(m, 0) + 1
                continue
            vistas.add(P.norm(fala))
            if indice is not None:
                indice.adicionar(fala)
            out.append({"id": P.chave("nova", fala), "fonte": "nova:" + ped["intencao"], "tema": ped["tema"],
                        "destino": destino(fala), "ctx": {}, "turnos": [{"papel": "usuario", "texto": fala}]})
    rel["aceitas"] = len(out)
    return out, rel


def conversa_texto(turnos):
    return "\n".join(("PESSOA: " if t["papel"] == "usuario" else "AMIGO: ") + t["texto"] for t in turnos)


def pedir_proxima(pergunta, resposta):
    ts = pergunta["turnos"] + [{"papel": "assistente", "texto": resposta}]
    return [{"role": "user", "content": PROXIMA_FALA.format(conversa=conversa_texto(ts))}]


META_FALA = re.compile(r"^(?:a pessoa|pessoa (?:pode|responde|diria)|resposta|mensagem|pr[óo]xima mensagem|exemplo)\b", re.I)


def eco(fala, resposta):
    """A fala repete o que o CRIVO acabou de dizer (≥ 80% das palavras dela estão na resposta)."""
    a, b = palavras(fala), palavras(resposta)
    return len(a) >= 4 and len(a & b) / len(a) >= 0.8


def segundo_turno(pergunta, resposta, texto, vistas, indice=None):
    """A pergunta de dois turnos a partir da fala seguinte que o professor escreveu, ou None."""
    ls = linhas(texto)
    if not ls:
        return None
    fala = re.sub(r"^(?:\s*(?:PESSOA|AMIGO|USU[ÁA]RIO)\s*:\s*)+", "", ls[0], flags=re.I).strip()   # o professor repete o rótulo
    if not fala or META_FALA.match(fala):   # "A pessoa pode responder:" não é fala, é o professor explicando
        return None
    if eco(fala, resposta):   # a "pessoa" copiando o CRIVO (piloto v2b, 19/10/2026)
        return None
    if fala_ok(fala, vistas, indice):
        return None
    turnos = pergunta["turnos"] + [{"papel": "assistente", "texto": resposta}, {"papel": "usuario", "texto": fala}]
    return {"id": P.chave("nova2", *(t["texto"] for t in turnos)), "fonte": pergunta["fonte"] + ":2", "tema": pergunta["tema"],
            "destino": pergunta["destino"], "ctx": {}, "turnos": turnos}


def pedir_nota(pergunta, resposta):
    return [{"role": "user", "content": JUIZ.format(conversa=conversa_texto(pergunta["turnos"]), resposta=resposta)}]


def ler_nota(texto):
    """A nota do juiz; "TEM A VER: NÃO" vale 1 (a resposta não responde o que a pessoa disse)."""
    t = texto or ""
    if re.search(r"TEM A VER:\s*N[ÃA]O", t, re.I) or re.search(r"FINGE PESSOA:\s*SIM", t, re.I):
        return 1
    m = re.search(r"NOTA:\s*([1-5])", t, re.I)
    return int(m.group(1)) if m else None


# Experiência, gosto ou corpo que o CRIVO não tem (IDENTIDADE.md). Corrigido em 19/10/2026: o piloto v2b
# aprovou "Fui naquele restaurante…" e "Eu gosto de tomar um café…" porque a lista anterior era estreita.
FINGE_HUMANO = re.compile(
    r"\beu (?:também |tambem |ainda |já |ja )?(?:durmo|dormi|tô dormindo|to dormindo|estou dormindo|comi|almocei|jantei|"
    r"moro|morei|trabalho|trabalhei|saí|viajei|acordei|tomei|pedi|me exercito|corro todo|"
    r"gosto (?:de|muito)|curto|adoro|tomo|já (?:vi|fui|passei|comi|estive|tive)|ja (?:vi|fui|passei|comi|estive|tive)|"
    r"tenho (?:um|uma|dois|duas) (?:filh|cachorr|gat|irm|marid|espos|namorad|carro|casa))"
    r"|\bfui (?:no|na|ao|à|pra|pro|com|almo|jant|comprar)"
    r"|\bmeu (?:filh|cachorr|gat|irm|marid|espos|namorad)"
    r"|\bminha (?:fam|irm|espos|mãe|mae|casa)\b", re.I)


def conferir(pergunta, bruto):
    """O filtro da v1 (forma e regra de ouro obrigatória, sem fatos) sem o falso "idioma" das falas curtas."""
    r = P.conferir(pergunta, bruto)
    if "idioma" in r["motivos"] and len(P.norm(r["texto"]).split()) < 8 and not P.CJK.search(r["texto"]):
        r["motivos"].remove("idioma")
    if FINGE_HUMANO.search(r["texto"]):
        r["motivos"].append("finge_ser_humano")
    if not r["regra_de_ouro"] and "inventou" not in r["motivos"]:
        r["motivos"].append("inventou")
    r["ok"] = not r["motivos"]
    return r


def controles(pares, rng, n=CONTROLES):
    """Pares (pergunta, resposta de OUTRA conversa, de OUTRO tema): respostas certamente erradas, para medir o juiz.
    Mesmo tema não vale (matemática com matemática pode até servir)."""
    if len(pares) < 2:
        return []
    out, tentativas = [], 0
    while len(out) < n and tentativas < 50 * n:
        tentativas += 1
        p, _ = pares[rng.randrange(len(pares))]
        q, c = pares[rng.randrange(len(pares))]
        if p.get("tema") is not None and p.get("tema") == q.get("tema"):
            continue
        out.append(({**p, "id": "controle:%d:%s:%s" % (len(out), p["id"], q["id"])}, c["texto"]))
    return out


def juiz_confiavel(notas_controles):
    """O juiz reprova as respostas trocadas? (fração aprovada ≤ MAX_CONTROLE_APROVADO, com nota em ≥ 80% delas)"""
    ns = [n for n in notas_controles if n is not None]
    if len(ns) < 0.8 * max(1, len(notas_controles)):
        return False, None   # sem nota não há medida: não passa
    aprovadas = sum(n >= NOTA_MINIMA for n in ns) / max(1, len(ns))
    return aprovadas <= MAX_CONTROLE_APROVADO, round(aprovadas, 3)


def uma_por_fala(aprovadas):
    """Uma conversa por primeira fala da pessoa. Antes, a mesma fala podia entrar com resposta de 1 turno e
    com resposta de 2 turnos (duas respostas para a mesma fala, o erro da v1). Fica a de nota maior e, entre
    as de mesma nota, a de mais turnos. `aprovadas`: [(pergunta, resposta, nota)]."""
    melhor = {}
    for item in aprovadas:
        p, _, nota = item
        k = P.norm(p["turnos"][0]["texto"])
        atual = melhor.get(k)
        if atual is None or ((nota or 0), len(p["turnos"])) > ((atual[2] or 0), len(atual[0]["turnos"])):
            melhor[k] = item
    out = [x for x in aprovadas if melhor[P.norm(x[0]["turnos"][0]["texto"])] is x]
    return out, {"removidas_mesma_fala": len(aprovadas) - len(out)}


def diversificar(exemplos):
    """Tira repetição: a mesma resposta no máximo MAX_MESMA_RESPOSTA vezes e nenhum começo acima de MAX_ABERTURA.
    Fica a de nota maior. Devolve (exemplos, relatório)."""
    ordem = sorted(exemplos, key=lambda e: (-(e.get("nota_juiz") or 0), e["chave"]))
    teto = max(20, int(MAX_ABERTURA * len(exemplos)))
    por_resposta, por_abertura, out, rel = {}, {}, [], {"resposta_repetida": 0, "abertura_repetida": 0}
    for e in ordem:
        n = P.norm(e["turnos"][-1]["texto"])
        ab = " ".join(n.split()[:4])
        if por_resposta.get(n, 0) >= MAX_MESMA_RESPOSTA:
            rel["resposta_repetida"] += 1
            continue
        if por_abertura.get(ab, 0) >= teto:
            rel["abertura_repetida"] += 1
            continue
        por_resposta[n] = por_resposta.get(n, 0) + 1
        por_abertura[ab] = por_abertura.get(ab, 0) + 1
        out.append(e)
    return out, rel
