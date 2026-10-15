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
sobre a natureza; curiosidade sobre o corpo; carro ou moto; bicicleta; compras; presente pra alguém
""".replace("\n", " ").split(";")
INTENCOES = [
    "pedir um conselho", "desabafar", "contar uma novidade boa", "contar algo chato que aconteceu",
    "pedir uma ideia", "perguntar como fazer alguma coisa", "pedir uma explicação simples",
    "pedir a opinião", "puxar conversa", "fazer uma brincadeira", "reclamar", "agradecer",
    "pedir ajuda pra decidir entre duas coisas", "perguntar algo que ficou curioso", "pedir uma dica rápida",
]
JEITOS = [
    "bem curto, informal, com gíria", "informal, com erro de digitação", "normal, uma ou duas frases",
    "tudo em minúsculas, sem pontuação", "mais longo, explicando a situação",
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
    "assistente. Dê uma nota de 1 a 5:\n"
    "5 = responde exatamente o que a pessoa disse, faz sentido, natural e simples, não inventa nada;\n"
    "4 = boa, com um detalhe pequeno a melhorar;\n"
    "3 = aceitável, mas genérica ou meio fora do ponto;\n"
    "2 = não responde o que foi dito ou soa estranha;\n"
    "1 = sem sentido, errada, em outra língua ou inventa fatos.\n"
    "Não dê nota maior por ser longa. Responda só com: NOTA: <número>\n\n{conversa}\n\nÚLTIMA RESPOSTA: {resposta}")
NOTA_MINIMA = 4

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


def fala_ok(fala, vistas):
    """Motivo para ficar fora, ou None. `vistas`: falas normalizadas que não podem repetir."""
    n = P.norm(fala)
    if not (3 <= len(fala) <= 220) or len(n.split()) < 1:
        return "tamanho"
    if not P.parece_portugues(fala) and len(n.split()) >= 4:
        return "idioma"
    if SOBRE_O_CRIVO.search(fala):
        return "sobre_o_crivo"
    if n in vistas:
        return "repetida"
    import crise
    if crise.detectar(fala) or crise.detectar_saude(fala):
        return "crise"
    return None


def falas_novas(respostas_pedidos, proibidas):
    """[(pedido, texto)] → (falas, relatório). Cada fala nova vira uma pergunta de um turno."""
    vistas, rel, out = set(proibidas), {}, []
    for ped, texto in respostas_pedidos:
        for fala in linhas(texto)[:POR_PEDIDO]:
            m = fala_ok(fala, vistas)
            if m:
                rel[m] = rel.get(m, 0) + 1
                continue
            vistas.add(P.norm(fala))
            out.append({"id": P.chave("nova", fala), "fonte": "nova:" + ped["intencao"], "tema": ped["tema"],
                        "destino": destino(fala), "ctx": {}, "turnos": [{"papel": "usuario", "texto": fala}]})
    rel["aceitas"] = len(out)
    return out, rel


def conversa_texto(turnos):
    return "\n".join(("PESSOA: " if t["papel"] == "usuario" else "AMIGO: ") + t["texto"] for t in turnos)


def pedir_proxima(pergunta, resposta):
    ts = pergunta["turnos"] + [{"papel": "assistente", "texto": resposta}]
    return [{"role": "user", "content": PROXIMA_FALA.format(conversa=conversa_texto(ts))}]


def segundo_turno(pergunta, resposta, texto, vistas):
    """A pergunta de dois turnos a partir da fala seguinte que o professor escreveu, ou None."""
    ls = linhas(texto)
    if not ls:
        return None
    fala = ls[0]
    if fala_ok(fala, vistas):
        return None
    turnos = pergunta["turnos"] + [{"papel": "assistente", "texto": resposta}, {"papel": "usuario", "texto": fala}]
    return {"id": P.chave("nova2", *(t["texto"] for t in turnos)), "fonte": pergunta["fonte"] + ":2", "tema": pergunta["tema"],
            "destino": pergunta["destino"], "ctx": {}, "turnos": turnos}


def pedir_nota(pergunta, resposta):
    return [{"role": "user", "content": JUIZ.format(conversa=conversa_texto(pergunta["turnos"]), resposta=resposta)}]


def ler_nota(texto):
    m = re.search(r"NOTA:\s*([1-5])", texto or "")
    return int(m.group(1)) if m else None


def conferir(pergunta, bruto):
    """O filtro da v1 (forma e regra de ouro obrigatória, sem fatos) sem o falso "idioma" das falas curtas."""
    r = P.conferir(pergunta, bruto)
    if "idioma" in r["motivos"] and len(P.norm(r["texto"]).split()) < 8 and not P.CJK.search(r["texto"]):
        r["motivos"].remove("idioma")
    if not r["regra_de_ouro"] and "inventou" not in r["motivos"]:
        r["motivos"].append("inventou")
    r["ok"] = not r["motivos"]
    return r
