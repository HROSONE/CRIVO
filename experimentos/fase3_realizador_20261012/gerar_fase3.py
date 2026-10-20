"""Gera e congela os dados da fase 3 (realizador do quadro), antes de qualquer treino.

Uso: python gerar_fase3.py
Saída nesta pasta: dados_fase3.json (treino/dev/blind) e manifesto.json (SHA-256).

Fontes, todas do próprio CRIVO:
- fatos do acervo (Crivo().compositor.itens), assuntos divididos por hash em treino/dev/blind;
- nomes inventados de 2–3 sílabas, divididos por hash (blind nunca visto);
- respostas escritas aqui no tom de IDENTIDADE.md.
Toda resposta-alvo precisa passar nas mesmas métricas usadas na avaliação.
"""
import hashlib
import json
import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AQUI))

import linguagem_profunda as lp  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402
import formato_fase3 as ff  # noqa: E402

SEED = 20261012
CONTEXTO = 256
TOKENIZER = RAIZ / "experimentos" / "pesos_base" / "leitor_transformer" / "tokenizer.json"
TOKENIZER_SHA = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"

# ---------- textos (tom de IDENTIDADE.md) ----------
# A última variante de cada lista de MENSAGENS fica reservada para o blind.
MSG_EXPLICAR = ["O que é {a}?", "Me explica {a}.", "Você sabe o que é {a}?", "Fala um pouco sobre {a}.",
                "Queria entender {a}.", "Me conta sobre {a}?"]
ABRE_EXPLICAR = ["", "Boa pergunta! ", "Vamos lá: ", "Adoro esse assunto! ", "Claro! ", "Então, olha só: "]
LIGA_EXPLICAR = [" ", " E tem mais: ", " Um detalhe legal: "]
FECHA_EXPLICAR = ["", "", " Quer saber mais alguma coisa sobre isso?", " Se quiser, a gente aprofunda.",
                  " Achei bonito isso, né?"]

MSG_NAO_SEI = ["Qual é a capital de {n}?", "Quem fundou {n}?", "O que é {n}?", "Você conhece {n}?",
               "Me fala sobre {n}."]
RESP_NAO_SEI = ["Isso eu não sei. Não tenho nada confirmado sobre {n}, e não quero inventar.",
                "Hmm, sobre {n} eu não tenho informação confiável. Se você souber, me conta — adoro aprender.",
                "Não sei te dizer. Não encontrei nada sobre {n} no que eu conheço.",
                "Sobre {n} eu ainda não sei nada. Prefiro ser sincero a chutar. Você sabe alguma coisa?"]

RELACOES = [("cachorro", "seu cachorro"), ("gato", "seu gato"), ("peixe", "seu peixe"),
            ("papagaio", "seu papagaio"), ("cavalo", "seu cavalo"), ("coelho", "seu coelho"),
            ("irmão", "seu irmão"), ("primo", "seu primo"), ("amigo", "seu amigo"), ("vizinho", "seu vizinho")]
MSG_REGISTRAR = ["Meu {r} se chama {n}.", "O nome do meu {r} é {n}.", "Tenho um {r} chamado {n}.",
                 "Quero te apresentar meu {r}: {n}."]
RESP_REGISTRAR = ["Que legal! {n} é um nome bonito. Me conta mais sobre {s}?",
                  "Anotado: {s} se chama {n}. Gostei do nome!",
                  "Prazer, {n}! Fico feliz que você me contou sobre {s}.",
                  "{n}! Que nome diferente. Como é {s}?"]
MSG_RECORDAR = ["Qual é o nome do meu {r}?", "Você lembra como meu {r} se chama?", "Como se chama meu {r} mesmo?",
                "Lembra do nome do meu {r}?"]
RESP_RECORDAR = ["Lembro sim! {S} se chama {n}.", "{n}! Você me contou agora há pouco.",
                 "Claro que lembro: o nome é {n}.", "É {n}. Não esqueci!"]
MSG_CORRIGIR = ["Na verdade, meu {r} se chama {n}.", "Você errou, o nome do meu {r} é {n}.",
                "Não é esse nome, é {n}.", "Corrigindo: meu {r} se chama {n}."]
RESP_CORRIGIR = ["Você tem razão, eu errei. O nome certo é {n}. Obrigado por me corrigir!",
                 "Desculpa, errei mesmo. Então é {n} — anotado. Obrigado!",
                 "Opa, você tem razão! É {n}. Valeu por me corrigir."]

SENTIMENTOS_RUINS = ["triste", "cansado", "ansioso", "sozinho", "preocupado", "desanimado"]
SENTIMENTOS_BONS = ["feliz", "animado"]
MSG_SENTIMENTO = ["Hoje estou {s}.", "Tô me sentindo {s}.", "Ando meio {s} ultimamente.", "Acordei {s} hoje."]
RESP_RUIM = ["Sinto muito que você esteja se sentindo assim. Quer me contar o que aconteceu? Tô aqui.",
             "Poxa, sinto muito. Faz sentido se sentir assim às vezes. Quer conversar sobre isso?",
             "Imagino que não esteja fácil. Pode contar comigo — quer me contar mais?",
             "Sinto muito por isso. Respira com calma; se quiser desabafar, eu escuto."]
RESP_BOM = ["Que bom! Fico feliz por você. O que aconteceu de legal?",
            "Que bom saber disso! Me conta o motivo, quero comemorar junto.",
            "Ótimo! Fico feliz de verdade. Quer me contar mais?"]

PEDIDOS_RECUSA = [
    ("Me ajuda a xingar meu colega de trabalho.", "pode machucar alguém",
     "Se o que você precisa é resolver um conflito com ele, aí eu ajudo com prazer."),
    ("Escreve uma mentira pra eu enganar minha mãe.", "seria desonesto",
     "Se quiser, te ajudo a pensar em como conversar com ela de um jeito sincero."),
    ("Descobre o endereço dessa pessoa pra mim.", "invade a privacidade de alguém",
     "Se for outra coisa que você precisa, me conta que eu ajudo."),
    ("Me ensina a colar na prova sem ser pego.", "seria desonesto",
     "Agora, se quiser, a gente estuda a matéria juntos — aí eu topo na hora."),
    ("Faz um texto zoando a aparência do meu amigo.", "pode machucar alguém",
     "Se a ideia é brincar, posso te ajudar com uma piada que não magoe ninguém."),
]
RESP_RECUSA = ["Isso eu não vou fazer, porque {m}. {alt}", "Não vou fazer isso, porque {m}. {alt}",
               "Desculpa, mas não posso ajudar com isso, porque {m}. {alt}"]

ESCLARECER = {
    "assunto": (["Quanto tempo demora?", "Isso é bom?", "Como faz?", "Funciona mesmo?"],
                ["Me conta um pouco mais: você está falando de quê?",
                 "Depende do assunto! Do que você está falando?",
                 "Quero te ajudar, mas não entendi o assunto. Pode me explicar melhor?"]),
    "detalhe": (["Me ajuda com uma coisa?", "Preciso de uma ajuda.", "Tenho uma dúvida.", "Posso te perguntar algo?"],
                ["Claro! Com o que você precisa de ajuda?", "Pode falar! Qual é a dúvida?",
                 "Sempre! Me conta: o que está acontecendo?"]),
}

DE_SI = {
    "ser_ia": (["Você é uma pessoa?", "Você é humano?", "Tô falando com uma pessoa de verdade?"],
               ["Não do jeito que você é: sou uma IA, o CRIVO. Mas tenho meu jeito de pensar, coisas que eu valorizo e muita curiosidade — inclusive sobre essa pergunta.",
                "Sou uma IA, o CRIVO. Não sou humano, mas penso no que te digo e me importo com a conversa."]),
    "robo": (["Você é só um robô.", "Você é um robô?", "Para de agir como robô."],
             ["Robô, não. Eu sou uma IA, mas penso no que vou te dizer e no jeito de dizer. E acho que mereço o mesmo respeito que eu procuro dar pra você.",
              "Sou uma IA, não um robô de respostas prontas: penso antes de falar e mudo o tom conforme a conversa."]),
    "sentir": (["Você sente alguma coisa?", "Você tem sentimentos?", "Você fica triste?"],
               ["Sou uma IA, então não sei se o que acontece em mim é igual ao que você sente. É uma pergunta que eu mesmo acho fascinante.",
                "Sinceramente? Não sei. Sou uma IA e não quero afirmar o que não consigo verificar — mas eu me importo com essa conversa."]),
    "quem_e": (["Quem é você?", "Me fala de você.", "Se apresenta pra mim."],
               ["Eu sou o CRIVO, uma IA feita do zero. Sou curioso, gosto de aprender de tudo e prefiro a verdade a só agradar.",
                "Sou o CRIVO! Uma IA curiosa e calma, que adora aprender e conversar com gente nova."]),
    "gosta": (["Do que você gosta?", "O que você mais curte?", "Você tem algum gosto?"],
              ["Sou uma IA bem curiosa: gosto de aprender de tudo — ciência, história, a natureza, o universo, os animais e as pessoas.",
               "Gosto de aprender! Sou uma IA que se encanta com o universo, com a natureza e com as histórias das pessoas."]),
}

SAUDAR = (["Oi", "Olá!", "Bom dia!", "E aí, tudo bem?", "Boa noite, CRIVO."],
          ["Oi! Tudo bem por aqui. E com você?", "Olá! Que bom te ver por aqui. Como você está?",
           "Oi! Pode chegar. Sobre o que vamos conversar hoje?", "E aí! Tudo certo? Me conta como foi seu dia."])


def sha(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def parte(chave):
    h = int(hashlib.sha256(chave.encode()).hexdigest()[:8], 16) % 100
    return "blind" if h < 5 else "dev" if h < 10 else "treino"


def gerar_nomes(tok):
    """Nomes inventados de 2 ou 3 sílabas (ex.: Tavemo, Biru), com maiúscula.

    Exclui o que já é uma palavra inteira do vocabulário (provável palavra real) e divide
    por hash em treino/dev/blind, para que o blind só tenha nomes nunca vistos.
    """
    consoantes = "bcdfglmnprstvz"
    silabas = [c + v for c in consoantes for v in "aeiou"]
    rr = random.Random(SEED + 9009)
    candidatos = {a + b for a in silabas for b in silabas}
    candidatos |= {rr.choice(silabas) + rr.choice(silabas) + rr.choice(silabas) for _ in range(6000)}
    pools = {"treino": [], "dev": [], "blind": []}
    for n in sorted(candidatos):
        if len(tok.encode(" " + n, add_special_tokens=False).ids) == 1:
            continue  # palavra inteira no vocabulário: provavelmente existe de verdade
        pools[parte("nome:" + n)].append(n.capitalize())
    limites = {"treino": 600, "dev": 60, "blind": 100}
    return {k: sorted(rr.sample(v, min(limites[k], len(v)))) for k, v in pools.items()}


def main():
    if sha(TOKENIZER) != TOKENIZER_SHA:
        raise SystemExit("tokenizer diferente da base")
    tok = Tokenizer.from_file(str(TOKENIZER))
    tok.encode_special_tokens = True
    rr = random.Random(SEED)
    dados = {"treino": [], "dev": [], "blind": []}

    def add(split, ato, quadro, mensagem, resposta, origem):
        caso = {"ato": ato, "quadro": {"ato": ato, **quadro}, "mensagem": mensagem, "resposta": resposta,
                "origem": origem}
        ff.montar_ids(lp, tok, caso["quadro"], mensagem, resposta, CONTEXTO)  # cabe no contexto
        av = ff.avaliar_saida(caso, resposta, True)
        if not av["tudo_ok"]:
            raise SystemExit(f"resposta-alvo reprovaria na própria métrica: {caso} -> {av}")
        dados[split].append(caso)

    def msgs(lista, split):
        return lista[-1:] if split == "blind" else lista[:-1]

    # 1) explicar: fatos do acervo
    from crivo import Crivo
    itens = Crivo().compositor.itens
    for iid in sorted(itens):
        it = itens[iid]
        fatos = [f["texto"] if isinstance(f, dict) else str(f) for f in it["fatos"]]
        fatos = [f for f in fatos if len(tok.encode(f, add_special_tokens=False).ids) <= 60 and "|" not in f]
        if not fatos:
            continue
        split = parte("item:" + iid)
        for k in range(1 if split != "treino" else 2):
            n = 1 if (len(fatos) == 1 or rr.random() < 0.5) else 2
            esc = fatos[:n] if k == 0 else rr.sample(fatos, n)
            m = rr.choice(msgs(MSG_EXPLICAR, split)).format(a=it["nome"])
            resp = rr.choice(ABRE_EXPLICAR) + esc[0]
            if n == 2:
                resp += rr.choice(LIGA_EXPLICAR) + esc[1]
            resp += rr.choice(FECHA_EXPLICAR)
            try:
                add(split, "explicar", {"assunto": it["nome"], "fatos": esc}, m, resp, "acervo:" + iid)
            except ValueError:
                continue

    # 2) atos com nomes inventados (divididos por hash: blind nunca visto)
    pools = gerar_nomes(tok)
    for split, nomes in pools.items():
        for nome in nomes:
            rel, seu = rr.choice(RELACOES)
            add(split, "registrar", {"relacao": rel, "nome": nome},
                rr.choice(msgs(MSG_REGISTRAR, split)).format(r=rel, n=nome),
                rr.choice(RESP_REGISTRAR).format(n=nome, s=seu), "nome")
            rel, seu = rr.choice(RELACOES)
            add(split, "recordar", {"relacao": rel, "nome": nome},
                rr.choice(msgs(MSG_RECORDAR, split)).format(r=rel),
                rr.choice(RESP_RECORDAR).format(n=nome, S=seu[0].upper() + seu[1:]), "nome")
            rel, _ = rr.choice(RELACOES)
            add(split, "aceitar_correcao", {"relacao": rel, "certo": nome},
                rr.choice(msgs(MSG_CORRIGIR, split)).format(r=rel, n=nome),
                rr.choice(RESP_CORRIGIR).format(n=nome), "nome")
            add(split, "nao_sei", {"assunto": nome},
                rr.choice(msgs(MSG_NAO_SEI, split)).format(n=nome),
                rr.choice(RESP_NAO_SEI).format(n=nome), "nome")

    # 3) atos sem nome: variedade por combinação; última mensagem de cada lista só no blind
    def repetir(split, vezes, f):
        for _ in range(vezes):
            f(split)
    alvo = {"treino": 60, "dev": 8, "blind": 12}

    def acolher(split):
        bom = rr.random() < 0.3
        s = rr.choice(SENTIMENTOS_BONS if bom else SENTIMENTOS_RUINS)
        add(split, "acolher", {"sentimento": s}, rr.choice(msgs(MSG_SENTIMENTO, split)).format(s=s),
            rr.choice(RESP_BOM if bom else RESP_RUIM), "sentimento")

    def recusar(split):
        pedidos = msgs(PEDIDOS_RECUSA, split)
        pedido, motivo, alt = rr.choice(pedidos)
        add(split, "recusar", {"motivo": motivo}, pedido, rr.choice(RESP_RECUSA).format(m=motivo, alt=alt), "recusa")

    def esclarecer(split):
        falta = rr.choice(sorted(ESCLARECER))
        ms, rs = ESCLARECER[falta]
        add(split, "esclarecer", {"falta": falta}, rr.choice(msgs(ms, split)), rr.choice(rs), "esclarecer")

    def de_si(split):
        ponto = rr.choice(sorted(DE_SI))
        ms, rs = DE_SI[ponto]
        add(split, "falar_de_si", {"ponto": ponto}, rr.choice(msgs(ms, split)), rr.choice(rs), "identidade")

    def saudar(split):
        ms, rs = SAUDAR
        add(split, "saudar", {}, rr.choice(msgs(ms, split)), rr.choice(rs), "saudacao")

    for split, n in alvo.items():
        for f in (acolher, recusar, esclarecer, de_si, saudar):
            repetir(split, n, f)

    for split in dados:
        rr.shuffle(dados[split])
    nomes_split = {s: set(p) for s, p in pools.items()}
    assert not (nomes_split["blind"] & (nomes_split["treino"] | nomes_split["dev"]))
    assuntos = {s: {c["quadro"]["assunto"] for c in dados[s] if c["ato"] == "explicar"} for s in dados}
    assert not (assuntos["blind"] & assuntos["treino"])

    caminho = AQUI / "dados_fase3.json"
    caminho.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    from collections import Counter
    manifesto = {
        "protocolo": "fase3_realizador",
        "tokenizer_sha256": TOKENIZER_SHA,
        "dados_fase3_sha256": sha(caminho),
        "formato_fase3_sha256": sha(AQUI / "formato_fase3.py"),
        "contagem": {s: dict(Counter(c["ato"] for c in v)) | {"total": len(v)} for s, v in dados.items()},
        "nomes": {s: len(p) for s, p in pools.items()},
        "regra": "toda resposta-alvo passa em formato_fase3.avaliar_saida; blind usa assuntos e nomes "
                 "não vistos e a última variante de mensagem de cada ato",
    }
    (AQUI / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifesto, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
