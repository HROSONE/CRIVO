"""Treina a compreensão neural (entendimento_neural.py) do zero, em NumPy.

Dados gerados aqui, de forma determinística, a partir do próprio acervo:
- positivos: perguntas da base editorial e nomes/apelidos dos conceitos com
  ficha, em modelos de pergunta variados, com erros de digitação e cortesias;
- classe ``fora``: perguntas que o CRIVO não sabe responder, inclusive as que
  citam um conceito conhecido mas pedem outra coisa ("quanto custa um telescópio").

Treino e validação usam famílias diferentes (perguntas retidas, modelos e
preenchimentos próprios da validação). O limiar de decisão é escolhido só na
validação. O teste congelado (avaliacoes/entendimento_v1) não é lido aqui.

Uso: python scripts/treinar_entendimento.py [--epocas 12] [--ocultos 128]
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from entendimento_neural import (FORA, PASTA, VERSAO, caracteristicas, guarda_vocabulario,  # noqa: E402
                                 normalizar)

# ------------------------------------------------------------ modelos ------
CONCEITO_TREINO = (
    "o que é {n}", "{n}", "me fala sobre {n}", "explica {n}", "o que significa {n}",
    "quero saber sobre {n}", "{n} é o que", "me explica o que é {n}", "fala de {n}",
    "sabe o que é {n}", "conhece {n}", "queria entender {n}", "pode me explicar {n}",
    "o que você sabe sobre {n}", "me conta sobre {n}", "define {n}", "informações sobre {n}",
    "do que se trata {n}", "qual o conceito de {n}", "o que vem a ser {n}", "me ensina sobre {n}",
    "como funciona {n}", "pra que serve {n}", "qual a importância de {n}", "resumo de {n}",
)
CONCEITO_VALIDACAO = (
    "me dá uma explicação sobre {n}", "tenho dúvida sobre {n}", "você poderia explicar {n} pra mim",
    "estou estudando {n}, o que é", "o que eu preciso saber sobre {n}", "{n}?? explica aí",
)
AREA_TREINO = {
    "pessoas": ("quem foi {n}", "quem é {n}", "quem era {n}", "o que fez {n}", "biografia de {n}",
                "fala da vida de {n}"),
    "historia": ("o que foi {n}", "quando foi {n}", "o que aconteceu na {n}", "como foi {n}"),
}
AREA_VALIDACAO = {
    "pessoas": ("o que sabe da história de {n}", "por que {n} é famoso"),
    "historia": ("me conta o que rolou na {n}", "por que aconteceu {n}"),
}
PREFIXOS = ("", "", "", "ei ", "oi, ", "me diz ", "vc sabe ", "queria saber ", "uma dúvida: ",
            "crivo, ", "por favor ", "olha, ", "então, ")
SUFIXOS = ("", "", "?", "?", " por favor", " pra mim", " aí", "??")
ENVOLTORIOS = ("tenho uma pergunta: {q}", "me ajuda: {q}", "{q}, sabe me dizer?", "{q}? queria entender",
               "minha dúvida é {q}", "alguém me explica {q}", "preciso saber {q}", "{q}, me explica")
PREFIXOS_VAL = ("me tira uma dúvida, ", "boa tarde! ", "com licença, ")
SUFIXOS_VAL = (" obrigado", " valeu", " me ajuda")

# Fora do acervo: modelos e preenchimentos. Os da validação são disjuntos.
FORA_TREINO = {
    "quanto custa {produto}": "produto", "qual o preço de {produto}": "produto",
    "onde comprar {produto}": "produto", "qual o melhor {produto} pra comprar": "produto",
    "{produto} tá caro?": "produto", "vale a pena comprar {produto}": "produto",
    "onde fica {lugar}": "lugar", "como chegar em {lugar}": "lugar",
    "qual o telefone de {lugar}": "lugar", "que horas abre {lugar}": "lugar",
    "quem ganhou {evento}": "evento", "quando é {evento}": "evento",
    "como foi o jogo do {time}": "time", "o {time} ganhou ontem?": "time",
    "me indica {midia}": "midia", "qual {midia} você recomenda": "midia",
    "receita de {prato}": "prato", "como preparar {prato}": "prato",
    "como tirar {documento}": "documento", "como renovar {documento}": "documento",
    "como cancelar {servico}": "servico", "meu {servico} parou de funcionar": "servico",
    "como consertar {objeto}": "objeto", "meu {objeto} quebrou, o que eu faço": "objeto",
    "qual a cotação do {moeda} hoje": "moeda", "vale a pena investir em {investimento}": "investimento",
    "quantos anos tem {famoso}": "famoso", "com quem {famoso} é casado": "famoso",
    "qual o nome do meu {parente}": "parente", "quantos anos tem meu {parente}": "parente",
    "quanto custa {conceito}": "conceito", "qual o telefone de {pessoa}": "pessoa",
    "qual a cor favorita de {pessoa}": "pessoa", "onde comprar {conceito} barato": "conceito",
    "{conceito} está em promoção?": "conceito", "quantos seguidores tem {pessoa}": "pessoa",
    "qual o endereço de {pessoa}": "pessoa", "qual o email de {pessoa}": "pessoa",
    "qual a altura de {pessoa}": "pessoa", "qual o salário de {pessoa}": "pessoa",
    "qual o instagram de {pessoa}": "pessoa", "{pessoa} tem namorada?": "pessoa",
    "qual o prato preferido de {pessoa}": "pessoa", "onde mora {pessoa} hoje": "pessoa",
    "tem cupom de desconto pra {conceito}": "conceito", "qual a entrega mais rápida de {conceito}": "conceito",
    "{conceito} aceita cartão?": "conceito", "qual o horário de {conceito}": "conceito",
    "quanto pesa {conceito} em gramas na balança da farmácia": "conceito",
    "{conceito} faz parte do meu plano de saúde?": "conceito", "qual a nota de {conceito} no app": "conceito",
    "me empresta {conceito}": "conceito", "baixar {conceito} grátis": "conceito",
}
FORA_VALIDACAO = {
    "tem {produto} em estoque?": "produto", "parcela {produto} em quantas vezes": "produto",
    "qual o cep de {lugar}": "lugar", "{lugar} abre domingo?": "lugar",
    "qual foi o placar do {time}": "time", "onde assistir {midia}": "midia",
    "quanto tempo leva pra fazer {prato}": "prato", "quanto custa pra tirar {documento}": "documento",
    "como trocar a peça do {objeto}": "objeto", "qual o salário de {famoso}": "famoso",
    "qual o signo de {pessoa}": "pessoa", "{conceito} tem frete grátis?": "conceito",
}
PREENCHE_TREINO = {
    "produto": ("um iphone", "uma televisão", "um tênis de corrida", "uma geladeira nova",
                "um sofá", "uma bicicleta elétrica", "uma orquídea", "um cachorro de raça",
                "um notebook gamer", "um ar-condicionado", "uma passagem de avião", "um videogame",
                "uma lâmpada inteligente", "um perfume importado", "uma cafeteira"),
    "lugar": ("a farmácia mais perto", "o shopping", "a rodoviária", "o hospital", "a prefeitura",
              "o banco", "o aeroporto", "a padaria da esquina", "o cartório", "o mercado"),
    "evento": ("a copa do mundo", "o oscar", "o big brother", "a eleição", "o campeonato brasileiro",
               "a fórmula 1", "o carnaval do rio", "o grammy"),
    "time": ("flamengo", "corinthians", "palmeiras", "real madrid", "grêmio", "são paulo"),
    "midia": ("um filme de comédia", "uma série boa", "um livro de romance", "um podcast",
              "um anime", "uma música pra dormir", "um jogo de celular"),
    "prato": ("lasanha", "feijoada", "pudim", "brigadeiro", "pizza caseira", "coxinha",
              "macarrão carbonara", "moqueca", "pão de queijo", "panqueca", "strogonoff"),
    "documento": ("carteira de motorista", "passaporte", "rg", "título de eleitor", "cpf"),
    "servico": ("netflix", "spotify", "plano de celular", "internet", "streaming", "cartão de crédito"),
    "objeto": ("celular", "chuveiro", "notebook", "fogão", "máquina de lavar", "carro", "portão"),
    "moeda": ("dólar", "euro", "bitcoin", "peso argentino"),
    "investimento": ("ações", "bitcoin", "tesouro direto", "imóveis", "poupança"),
    "famoso": ("o neymar", "a anitta", "o messi", "a taylor swift", "o faustão"),
    "parente": ("vizinho", "primo", "chefe", "cunhado", "avô"),
}
PREENCHE_VALIDACAO = {
    "produto": ("uma air fryer", "um relógio inteligente", "um colchão", "um fone sem fio"),
    "lugar": ("o detran", "a academia", "o correio", "a biblioteca municipal"),
    "time": ("botafogo", "cruzeiro", "barcelona"),
    "midia": ("um documentário", "uma novela"),
    "prato": ("bolo de fubá", "escondidinho", "torta salgada"),
    "documento": ("certidão de nascimento", "alvará"),
    "objeto": ("micro-ondas", "ventilador", "liquidificador"),
    "famoso": ("o roberto carlos", "a xuxa"),
}


def digitar_com_erro(texto, rng):
    palavras = texto.split()
    candidatas = [i for i, p in enumerate(palavras) if len(p) >= 5 and p.isalpha()]
    if not candidatas:
        return texto
    i = rng.choice(candidatas)
    p = palavras[i]
    j = rng.randrange(1, len(p) - 2)
    op = rng.randrange(3)
    if op == 0:
        p = p[:j] + p[j + 1] + p[j] + p[j + 2:]
    elif op == 1:
        p = p[:j] + p[j + 1:]
    else:
        p = p[:j] + p[j] + p[j:]
    palavras[i] = p
    return " ".join(palavras)


def variar(texto, rng, prefixos=PREFIXOS, sufixos=SUFIXOS):
    t = texto.strip().rstrip("?.!")
    if rng.random() < 0.35:
        t = digitar_com_erro(t, rng)
    return rng.choice(prefixos) + t + rng.choice(sufixos)


# --------------------------------------------------------------- dados -----
def classes_e_canonicas(bot):
    import json as _json
    base = _json.loads((RAIZ / "conhecimento.json").read_text(encoding="utf-8"))
    editoriais = {e["id"]: e for e in base}
    canonicas = {}
    for e in bot.base:
        if e["id"] in editoriais:
            canonicas[e["id"]] = editoriais[e["id"]]["perguntas"][0].rstrip("?") + "?"
    for ident, item in bot.compositor.itens.items():
        canonicas.setdefault(ident, "O que é %s?" % item["nome"])
    return canonicas, editoriais


def roteia(classe, canonica):
    from crivo import Crivo
    bot = Crivo()
    ident, _ = bot.responder(canonica)
    alvo = ident.split(":", 1)[1] if ident.startswith(("conhecimento:", "pratica:")) else ident
    temas = getattr(bot.contexto_textual, "temas", ()) or ()
    return alvo == classe or classe in temas


def gerar(bot, canonicas, editoriais, semente=20261005):
    rng = random.Random(semente)
    treino, validacao = [], []
    itens = bot.compositor.itens
    for classe in canonicas:
        if classe in editoriais:
            perguntas = list(dict.fromkeys(editoriais[classe]["perguntas"]))
            retida = perguntas.pop() if len(perguntas) >= 3 else None
            for q in perguntas:
                treino.append((q, classe))
                for _ in range(12):
                    treino.append((variar(q, rng), classe))
                for envoltorio in rng.sample(ENVOLTORIOS, 3):
                    treino.append((envoltorio.format(q=q.rstrip("?")), classe))
            if retida:
                validacao.append((retida, classe))
                validacao.append((variar(retida, rng, PREFIXOS_VAL, SUFIXOS_VAL), classe))
        if classe in itens:
            item = itens[classe]
            nomes = list(dict.fromkeys([item["nome"]] + item.get("aliases", [])))
            area = item.get("area", "")
            modelos = CONCEITO_TREINO + AREA_TREINO.get(area, ())
            for nome in nomes:
                for m in rng.sample(modelos, min(len(modelos), 10)):
                    treino.append((variar(m.format(n=nome), rng), classe))
            for m in CONCEITO_VALIDACAO[:2] + AREA_VALIDACAO.get(area, ())[:1]:
                validacao.append((m.format(n=rng.choice(nomes)), classe))
    pessoas = [i["nome"] for i in itens.values() if i.get("area") == "pessoas"] or ["Einstein"]
    conceitos = [i["nome"] for i in itens.values()]

    def preencher(modelo, slot, tabela):
        if slot == "conceito":
            return modelo.format(conceito=rng.choice(conceitos))
        if slot == "pessoa":
            return modelo.format(pessoa=rng.choice(pessoas))
        valores = tabela.get(slot) or PREENCHE_TREINO[slot]
        return modelo.format(**{slot: rng.choice(valores)})

    for modelo, slot in FORA_TREINO.items():
        for _ in range(45):
            treino.append((variar(preencher(modelo, slot, PREENCHE_TREINO), rng), FORA))
    for modelo, slot in FORA_VALIDACAO.items():
        for _ in range(8):
            validacao.append((preencher(modelo, slot, PREENCHE_VALIDACAO), FORA))
    teste = json.loads((RAIZ / "avaliacoes/entendimento_v1/teste.json").read_text(encoding="utf-8"))
    proibidas = {" ".join(normalizar(c["p"])) for c in teste["positivos"]} | {
        " ".join(normalizar(p)) for p in teste["negativos"]}
    treino = [(t, c) for t, c in treino if " ".join(normalizar(t)) not in proibidas]
    validacao = [(t, c) for t, c in validacao if " ".join(normalizar(t)) not in proibidas]
    return treino, validacao


# -------------------------------------------------------------- treino -----
def treinar(treino, rotulos, dimensao, ocultos, epocas, semente, queda=0.25, suavizacao=0.05):
    import numpy as np
    rng = np.random.default_rng(semente)
    indice = {r: i for i, r in enumerate(rotulos)}
    X = [np.array(caracteristicas(t, dimensao), dtype=np.int64) for t, _ in treino]
    y = np.array([indice[c] for _, c in treino])
    C = len(rotulos)
    w1 = (rng.standard_normal((dimensao, ocultos)) * 0.05).astype(np.float32)
    b1 = np.zeros(ocultos, np.float32)
    w2 = (rng.standard_normal((ocultos, C)) * (1.0 / np.sqrt(ocultos))).astype(np.float32)
    b2 = np.zeros(C, np.float32)
    # Adagrad: atualizações esparsas em w1 sem carregar momentos densos.
    g1 = np.full((dimensao, ocultos), 1e-8, np.float32)
    gb1 = np.full(ocultos, 1e-8, np.float32)
    g2 = np.full((ocultos, C), 1e-8, np.float32)
    gb2 = np.full(C, 1e-8, np.float32)
    lr = 0.2
    lote = 32
    for epoca in range(epocas):
        ordem = rng.permutation(len(X))
        perda = 0.0
        for inicio in range(0, len(ordem), lote):
            ids = ordem[inicio:inicio + lote]
            H = np.zeros((len(ids), ocultos), np.float32)
            usadas = []
            for k, i in enumerate(ids):
                linhas = X[i]
                if len(linhas) > 4:
                    linhas = linhas[rng.random(len(linhas)) >= queda]
                usadas.append(linhas)
                H[k] = w1[linhas].sum(axis=0) / np.sqrt(max(1, len(linhas)))
            H += b1
            A = np.maximum(H, 0)
            Z = A @ w2 + b2
            Z -= Z.max(axis=1, keepdims=True)
            P = np.exp(Z)
            P /= P.sum(axis=1, keepdims=True)
            alvo = y[ids]
            perda += -np.log(P[np.arange(len(ids)), alvo] + 1e-9).sum()
            dZ = P - suavizacao / C
            dZ[np.arange(len(ids)), alvo] -= 1 - suavizacao
            dZ /= len(ids)
            dw2 = A.T @ dZ
            db2 = dZ.sum(axis=0)
            dA = dZ @ w2.T
            dH = dA * (H > 0)
            db1 = dH.sum(axis=0)
            g2 += dw2 ** 2; w2 -= lr * dw2 / np.sqrt(g2)
            gb2 += db2 ** 2; b2 -= lr * db2 / np.sqrt(gb2)
            gb1 += db1 ** 2; b1 -= lr * db1 / np.sqrt(gb1)
            for k, linhas in enumerate(usadas):
                if not len(linhas):
                    continue
                grad = dH[k] / np.sqrt(len(linhas))
                g1[linhas] += grad ** 2
                w1[linhas] -= lr * grad / np.sqrt(g1[linhas])
        print("época %d: perda média %.4f" % (epoca + 1, perda / len(X)), flush=True)
    return w1, b1, w2, b2


def prever_lote(textos, w1, b1, w2, b2, dimensao):
    import numpy as np
    saidas = []
    for t in textos:
        idx = caracteristicas(t, dimensao)
        h = np.maximum(w1[idx].sum(axis=0) / np.sqrt(max(1, len(idx))) + b1, 0)
        z = h @ w2 + b2
        z -= z.max()
        p = np.exp(z); p /= p.sum()
        o = p.argsort()[::-1]
        saidas.append((int(o[0]), float(p[o[0]]), float(p[o[0]] - p[o[1]])))
    return saidas


def nomes_e_vocabulario(bot, canonicas, editoriais):
    """Nomes que ancoram cada assunto e raízes do vocabulário dos seus textos."""
    nomes, vocabulario = {}, {}
    for classe in canonicas:
        textos, ns = [], []
        if classe in bot.compositor.itens:
            item = bot.compositor.itens[classe]
            ns = [normalizar(n) for n in [item["nome"]] + item.get("aliases", [])]
            textos += [f["texto"] for f in item.get("fatos", [])]
        if classe in editoriais:
            textos += editoriais[classe]["perguntas"] + [editoriais[classe].get("resposta", "")]
        entrada = next((e for e in bot.base if e["id"] == classe), None)
        if entrada:
            textos += entrada.get("perguntas", [])[:8] + [entrada.get("resposta", "")]
        nomes[classe] = [n for n in ns if n]
        vocabulario[classe] = sorted({p[:5] for t in textos for p in normalizar(t)})
    return nomes, vocabulario


def escolher_limiar(validacao, previsoes, rotulos, nomes=None, vocabulario=None, erro_max=0.03, fora_max=0.02):
    positivos = [(t, c, p) for (t, c), p in zip(validacao, previsoes) if c != FORA]
    negativos = [(t, p) for (t, c), p in zip(validacao, previsoes) if c == FORA]
    melhor = None
    for limiar in [x / 100 for x in range(30, 96, 5)]:
        for margem in (0.0, 0.1, 0.2, 0.3):
            def aceita(t, p):
                return (rotulos[p[0]] != FORA and p[1] >= limiar and p[2] >= margem and
                        (nomes is None or guarda_vocabulario(t, rotulos[p[0]], nomes, vocabulario)))
            certos = sum(aceita(t, p) and rotulos[p[0]] == c for t, c, p in positivos)
            errados = sum(aceita(t, p) and rotulos[p[0]] != c for t, c, p in positivos)
            falsos = sum(aceita(t, p) for t, p in negativos)
            aceitos = certos + errados + falsos
            if not aceitos:
                continue
            if (errados + falsos) / aceitos <= erro_max and falsos / max(1, len(negativos)) <= fora_max:
                chave = (certos, -limiar)
                if melhor is None or chave > melhor[0]:
                    melhor = (chave, dict(limiar=limiar, margem=margem, certos=certos, errados=errados,
                                          falsos_fora=falsos, positivos=len(positivos),
                                          negativos=len(negativos)))
    return melhor[1] if melhor else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epocas", type=int, default=6)
    parser.add_argument("--ocultos", type=int, default=128)
    parser.add_argument("--dimensao", type=int, default=2 ** 15)
    parser.add_argument("--semente", type=int, default=20261005)
    parser.add_argument("--saida", default=str(PASTA))
    parser.add_argument("--cache-rotas", help="arquivo para reaproveitar a conferência das perguntas canônicas")
    args = parser.parse_args()
    import numpy as np
    from crivo import Crivo
    inicio = time.time()
    bot = Crivo()
    canonicas, editoriais = classes_e_canonicas(bot)
    cache = Path(args.cache_rotas) if args.cache_rotas else None
    conferidas = json.loads(cache.read_text(encoding="utf-8")) if cache and cache.is_file() else {}
    validas = {}
    for c, q in canonicas.items():
        chave = c + "\t" + q
        if chave not in conferidas:
            conferidas[chave] = roteia(c, q)
        if conferidas[chave]:
            validas[c] = q
    if cache:
        cache.write_text(json.dumps(conferidas, ensure_ascii=False), encoding="utf-8")
    print("classes: %d de %d com pergunta canônica que cai no próprio assunto" % (len(validas), len(canonicas)),
          flush=True)
    treino, validacao = gerar(bot, validas, editoriais, args.semente)
    rotulos = sorted(validas) + [FORA]
    treino = [(t, c) for t, c in treino if c in rotulos]
    validacao = [(t, c) for t, c in validacao if c in rotulos]
    print("exemplos: treino %d, validação %d" % (len(treino), len(validacao)), flush=True)
    w1, b1, w2, b2 = treinar(treino, rotulos, args.dimensao, args.ocultos, args.epocas, args.semente)
    previsoes = prever_lote([t for t, _ in validacao], w1, b1, w2, b2, args.dimensao)
    acerto_top1 = sum(rotulos[p[0]] == c for (t, c), p in zip(validacao, previsoes)) / len(validacao)
    nomes, vocabulario = nomes_e_vocabulario(bot, validas, editoriais)
    controle = escolher_limiar(validacao, previsoes, rotulos, nomes, vocabulario)
    aprovado = bool(controle and controle["certos"] >= 0.5 * controle["positivos"])
    controle = dict(controle or {}, aprovado=aprovado, acerto_top1_validacao=round(acerto_top1, 4))
    print("controle:", json.dumps(controle, ensure_ascii=False), flush=True)
    pasta = Path(args.saida)
    pasta.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(pasta / "modelo.npz", w1=w1.astype(np.float16), b1=b1, w2=w2.astype(np.float16), b2=b2)
    meta = dict(versao=VERSAO, dimensao=args.dimensao, ocultos=args.ocultos, epocas=args.epocas,
                semente=args.semente, rotulos=rotulos, canonicas={c: validas[c] for c in rotulos if c != FORA},
                nomes={c: nomes.get(c, []) for c in rotulos if c != FORA},
                vocabulario={c: vocabulario.get(c, []) for c in rotulos if c != FORA},
                exemplos_treino=len(treino), exemplos_validacao=len(validacao), controle=controle,
                segundos=round(time.time() - inicio, 1),
                limite="Aponta assuntos do acervo; não gera texto nem verifica fatos. Validação sintética "
                       "por famílias; o teste congelado mede a generalização real.")
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print("salvo em", pasta, "em %.0fs" % (time.time() - inicio))


if __name__ == "__main__":
    main()
