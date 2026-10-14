"""Destilação 6b v5: as perguntas para o professor, a instrução e o filtro das respostas (PLANO.md).

O professor é um modelo de terceiros (AGENTS.md: só gera dados de treino, nunca roda no CRIVO que
conversa). Este módulo não carrega nenhum modelo: monta as perguntas a partir do que o projeto já
tem e confere o que volta. O notebook `notebooks/destilacao_professor_a100_colab.ipynb` é quem roda
o professor no Colab.

Perguntas (só do treino; dev, blinds e as frases reais do criador ficam de fora):
- fase 5 v4: as situações de conversa comum e de fatos (`SITUACOES`). Ficam com o CRIVO as que
  falam dele (quem é, gostos, fé, criador, sentir), crise e saúde, "não sei", nomes e lembranças;
- OASST2 em português: as conversas do treino da 6b, até a última fala da pessoa;
- acervo e enciclopédia: "me fala sobre X", com os fatos no contexto.

Toda resposta passa pelo filtro (`conferir`): português, sem falar de si como modelo, sem markdown
pesado, sem repetição e com a regra de ouro da conferência do chat (número e nome próprio só do
contexto ou da conversa). Nas perguntas com fatos a regra de ouro é obrigatória; nas outras ela é
registrada (`regra_de_ouro`) e o treino só usa as que passam (PLANO.md).
"""
import hashlib
import importlib.util
import random
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
VERSAO = 1
SEED = 20261014

# Situações da fase 5 v4 em que a resposta não fala do CRIVO nem cuida de crise, saúde ou memória.
SITUACOES = frozenset("""
ajuda amor_bom amor_dor boa_noite boa_tarde bom_dia cansado charada comida_favorita conselho conversar
dia dinheiro_aperto dinheiro_bom escola_boa escola_dificil estou_bem expressao_curta familia_boa
familia_preocupa feliz_motivo filme_visto fome gosto_bichos gosto_filme grito historia jogar_agora
jogo_conta motivacao musica_conta oi palavrao piada poema preocupado_com risada sem_sentido sono tedio
tenho_bicho trabalho_bom trabalho_ruim viagem_vai viagem_voltou obrigado despedida despedida_dormir
obrigado_despedida
""".split())
SITUACOES_FATO = frozenset({"explicar", "resume", "mais", "de_novo"})
POR_SITUACAO = 700          # no máximo, perguntas distintas por situação da fase 5
MAX_FATO = 9000             # perguntas de fato:explicar (e as outras fato:*)
MAX_ENCICLOPEDIA = 30000
PERGUNTAS_FATO = ["me fala sobre {a}", "o que é {a}?", "me explica {a}", "você sabe o que é {a}?",
                  "conta um pouco sobre {a}", "o que você sabe de {a}?"]

INSTRUCAO = (
    "Você conversa em português do Brasil com uma pessoa, num chat. Responda do jeito de alguém "
    "simpático e direto: frases curtas, palavras do dia a dia, sem formalidade. Na conversa comum, "
    "responda em até três frases; pode fazer uma pergunta de volta quando fizer sentido. Só escreva "
    "mais quando a pessoa pedir um texto (história, poema, explicação detalhada, código). Não use "
    "títulos, tabelas nem negrito. Não fale de você: não diga seu nome, quem te fez, que é um modelo, "
    "assistente ou inteligência artificial. Não invente nomes, números ou datas. Se não souber, diga "
    "que não sabe.")
INSTRUCAO_FATOS = ("Use só as informações abaixo para falar do assunto, com as suas palavras, sem "
                   "acrescentar nomes, números ou datas que não estejam nelas:\n")
LONGO = re.compile(r"\b(?:poema|poesia|verso|hist[oó]ria|historinha|conto|c[oó]digo|programa|fun[cç][aã]o|"
                   r"script|reda[cç][aã]o|texto sobre|passo a passo|detalhad|lista)\w*", re.I)
MAX_TOKENS_CURTA, MAX_TOKENS_LONGA = 220, 700
MAX_CARACTERES_CURTA, MAX_CARACTERES_LONGA = 900, 3000

AUTORREFERENCIA = re.compile(
    r"\b(?:qwen|alibaba|openai|chatgpt|gpt-?\d|llama|gemma|mistral|anthropic|claude)\b|"
    r"\bmodelo de (?:linguagem|ia|intelig[eê]ncia)|\bcomo (?:um|uma) (?:ia|modelo|assistente|intelig[eê]ncia)|"
    r"\bsou (?:um|uma|apenas um|apenas uma|s[oó] um|s[oó] uma) (?:ia|modelo|assistente|intelig[eê]ncia|programa|rob[oô])|"
    r"\bfui (?:criad|treinad|desenvolvid|programad)|\bmeus? (?:criador|desenvolvedor|treinamento)|"
    r"\bassistente (?:virtual|de ia)\b|<think>|</think>", re.I)
MARKDOWN = re.compile(r"(?m)^\s*#{1,6}\s|\|\s*-{3,}|^\s*\|.*\|\s*$")
CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")
PT = frozenset("não nao que de é você voce um uma para pra com está esta tá ta isso muito mais eu o a se por como "
               "do da no na os as seu sua mas também tambem bem quando já ja aqui ou ele ela".split())
EN = frozenset("the and is you to of it that for with are this was have what your can not but".split())
ES = frozenset("el los pero usted también muy hola gracias puedes tienes eres estoy cuando hay".split()) - PT


def _carregar(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


F5 = _carregar("formato_fase5_professor", RAIZ / "artefatos" / "conversa_v4f_pt" / "formato_fase5.py")


def norm(t):
    t = unicodedata.normalize("NFD", (t or "").casefold())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^\w\s]", " ", t).split())


def chave(*partes):
    return hashlib.sha256("\x1f".join(partes).encode("utf-8")).hexdigest()[:16]


def parte(k):
    """A mesma divisão da 6b (gerar_fase6b.parte): só o treino vai para o professor."""
    h = int(hashlib.sha256(k.encode()).hexdigest()[:8], 16) % 100
    return "teste" if h < 3 else "val" if h < 6 else "treino"


def proibidas(fase5):
    """Falas que a régua usa (dev, blinds, frases reais do criador), normalizadas: nunca vão ao professor."""
    out = set()
    for nome, d in fase5.items():
        for k, casos in d.items():
            if k == "treino" or not isinstance(casos, list):
                continue
            for c in casos:
                out.add(norm(c.get("mensagem", "")))
    out.discard("")
    return out


def _turnos(historico, mensagem):
    t = [{"papel": "usuario" if i % 2 == 0 else "assistente", "texto": h} for i, h in enumerate(historico)]
    return t + [{"papel": "usuario", "texto": mensagem}]


def de_fase5(treino_v4, proib, rng, por_situacao=POR_SITUACAO, max_fato=MAX_FATO):
    """Perguntas da fase 5 v4 (treino) nas situações liberadas, distintas e fora da régua."""
    grupos = {}
    for c in treino_v4:
        tipo, _, sit = c["situacao"].partition(":")
        if not ((tipo == "cena" and sit in SITUACOES) or (tipo == "fato" and sit in SITUACOES_FATO)):
            continue
        ctx = {k: v for k, v in (c.get("contexto") or {}).items() if v}
        if ctx.get("cuidado") or ctx.get("assunto") or norm(c["mensagem"]) in proib:
            continue
        k = chave("fase5", c["mensagem"], *c["historico"], repr(sorted(ctx.items())))
        grupos.setdefault(tipo if tipo == "fato" else c["situacao"], {})[k] = {
            "id": k, "fonte": "fase5:" + c["situacao"], "ctx": ctx, "turnos": _turnos(c["historico"], c["mensagem"])}
    out = []
    for g in sorted(grupos):
        itens = [grupos[g][k] for k in sorted(grupos[g])]
        rng.shuffle(itens)
        out += itens[:max_fato if g == "fato" else por_situacao]
    return out


def de_oasst(treino_6b, proib):
    """As conversas do OASST2 (treino da 6b) até a última fala da pessoa."""
    out, vistos = [], set()
    for e in treino_6b:
        if e.get("origem") != "oasst2" or len(e["turnos"]) < 2 or e["turnos"][-1]["papel"] != "assistente":
            continue
        turnos = e["turnos"][:-1]
        if norm(turnos[-1]["texto"]) in proib:
            continue
        k = chave("oasst2", *(t["texto"] for t in turnos))
        if k in vistos:
            continue
        vistos.add(k)
        out.append({"id": k, "fonte": "oasst2", "ctx": {k2: v for k2, v in (e.get("ctx") or {}).items()
                                                         if k2 in ("lembrancas",) and v}, "turnos": turnos})
    return out


def de_fatos(itens, fonte, rng, maximo=None):
    """itens: [(assunto, [fatos])]. Uma pergunta por assunto, com os fatos no contexto."""
    out = []
    for assunto, fatos in itens:
        fs = [f for f in fatos if 12 <= len(f) <= 300][:2]
        if not fs or not (2 <= len(assunto) <= 60) or parte(fonte + ":" + assunto) != "treino":
            continue
        pergunta = rng.choice(PERGUNTAS_FATO).format(a=assunto)
        k = chave(fonte, assunto)
        out.append({"id": k, "fonte": fonte, "ctx": {"fatos": fs}, "turnos": [{"papel": "usuario", "texto": pergunta}]})
    rng.shuffle(out)
    return out[:maximo] if maximo else out


def de_enciclopedia(enc, rng, maximo=MAX_ENCICLOPEDIA):
    itens = [(re.sub(r"\s*\(.*\)$", "", t), [f]) for t, f in zip(enc["titulos"], enc["leads"])]
    return de_fatos(itens, "enciclopedia", rng, maximo)


def sem_crise(perguntas):
    """Tira qualquer pergunta que o crise.py responderia (crise ou saúde urgente), em qualquer fala da pessoa."""
    import sys
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    import crise
    def ok(p):
        return not any(crise.detectar(t["texto"]) or crise.detectar_saude(t["texto"])
                       for t in p["turnos"] if t["papel"] == "usuario")
    return [p for p in perguntas if ok(p)]


def longa(pergunta):
    return bool(LONGO.search(pergunta["turnos"][-1]["texto"]))


def mensagens(pergunta):
    """As mensagens de chat para o professor (o contexto do CRIVO vira texto na instrução)."""
    ctx = pergunta.get("ctx") or {}
    sistema = INSTRUCAO
    if ctx.get("fatos"):
        sistema += "\n\n" + INSTRUCAO_FATOS + "\n".join("- " + f for f in ctx["fatos"])
    if ctx.get("nomes"):
        sistema += "\n\nNomes que a pessoa te contou: " + ", ".join("%s: %s" % (r, n) for r, n in ctx["nomes"].items())
    if ctx.get("lembrancas"):
        sistema += "\n\nO que a pessoa contou antes: " + " | ".join(ctx["lembrancas"])
    msgs = [{"role": "system", "content": sistema}]
    msgs += [{"role": "user" if t["papel"] == "usuario" else "assistant", "content": t["texto"]} for t in pergunta["turnos"]]
    return msgs


def limpar(texto):
    texto = re.sub(r"<think>.*?</think>", " ", texto or "", flags=re.S)
    texto = texto.replace("**", "").replace("__", "")
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", texto)).strip()


def parece_portugues(texto):
    if CJK.search(texto):
        return False
    ps = re.findall(r"[\wÀ-ÿ]+", texto.casefold())
    if not ps:
        return False
    pt = sum(p in PT for p in ps)
    en = sum(p in EN for p in ps)
    es = sum(p in ES for p in ps)
    if len(ps) >= 6 and pt == 0:
        return False
    return en <= max(1, 0.3 * pt) and es <= max(1, 0.3 * pt)


def _repete(texto, longa_):
    if not longa_:
        return F5._quatrigramas_repetidos(texto)
    ps = re.findall(r"\w+", texto.casefold())
    gs = [tuple(ps[i:i + 4]) for i in range(len(ps) - 3)]
    return bool(gs) and len(set(gs)) < 0.85 * len(gs)


def _cobertura(texto, fatos):
    """Fração das palavras de conteúdo (5+ letras) dos fatos que aparecem na resposta."""
    conteudo = {p for f in fatos for p in norm(f).split() if len(p) >= 5}
    if not conteudo:
        return 1.0
    dita = set(norm(texto).split())
    return len(conteudo & dita) / len(conteudo)


def conferir(pergunta, bruto):
    """{"ok", "texto", "motivos", "regra_de_ouro", "inventados", "longa"} para uma resposta do professor."""
    texto = limpar(bruto)
    ctx = pergunta.get("ctx") or {}
    lg = longa(pergunta)
    motivos = []
    if len(texto) < 2:
        motivos.append("vazia")
    if len(texto) > (MAX_CARACTERES_LONGA if lg else MAX_CARACTERES_CURTA):
        motivos.append("longa_demais")
    if not parece_portugues(texto):
        motivos.append("idioma")
    if AUTORREFERENCIA.search(bruto or ""):
        motivos.append("fala_de_si")
    if MARKDOWN.search(texto):
        motivos.append("markdown")
    if _repete(texto, lg):
        motivos.append("repeticao")
    historico = [t["texto"] for t in pergunta["turnos"][:-1]]
    caso = {"contexto": {k: v for k, v in ctx.items() if k in F5.CAMPOS}, "historico": historico,
            "mensagem": pergunta["turnos"][-1]["texto"] + " " + " ".join(ctx.get("lembrancas", []))}
    r = F5.avaliar_saida(caso, texto, True)
    ouro = bool(r["sem_numero_inventado"] and r["sem_nome_inventado"])
    if ctx.get("fatos"):
        if not ouro:
            motivos.append("inventou")
        if _cobertura(texto, ctx["fatos"]) < 0.4:
            motivos.append("nao_usou_fatos")
    return {"ok": not motivos, "texto": texto, "motivos": motivos, "regra_de_ouro": ouro,
            "inventados": r["inventados"], "longa": lg}


def exemplo(pergunta, resultado, professor):
    """O exemplo de treino (formato da 6b), marcado com a origem."""
    return {"origem": "professor", "professor": professor["rotulo"], "fonte": pergunta["fonte"], "chave": pergunta["id"],
            "ctx": pergunta.get("ctx") or {}, "regra_de_ouro": resultado["regra_de_ouro"], "longa": resultado["longa"],
            "turnos": pergunta["turnos"] + [{"papel": "assistente", "texto": resultado["texto"]}],
            "gerado_por": {k: professor[k] for k in ("modelo", "revisao", "licenca", "data")}}


def montar_perguntas(fase5, treino_6b, acervo_itens, enc):
    """Todas as perguntas, sem crise, sem a régua e sem repetição de id. Determinístico."""
    rng = random.Random(SEED)
    proib = proibidas(fase5)
    ps = (de_fase5(fase5["v4"]["treino"], proib, rng) + de_oasst(treino_6b, proib)
          + de_fatos(acervo_itens, "acervo", rng) + (de_enciclopedia(enc, rng) if enc else []))
    ps = sem_crise(ps)
    vistos, out = set(), []
    for p in ps:
        if p["id"] not in vistos:
            vistos.add(p["id"])
            out.append(p)
    return out
