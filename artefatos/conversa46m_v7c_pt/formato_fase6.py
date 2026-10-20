"""Formato da conversa da fase 6b: o CRIVO crescido (46M, 1024 tokens) conversando.

Diferente da fase 5, ninguém escreve as falas dele: os alvos de treino são respostas escritas por
pessoas (OASST2 em português, legendas) e textos do acervo. O CRIVO só entrega, no contexto, o que é
informação conferida:

    quem        quem ele é, lido do IDENTIDADE.md (decisão do criador: ele se apresenta do jeito dele);
    lembrancas  o que a pessoa contou antes (nesta conversa ou em outras);
    fatos       frases do acervo com fonte;
    assunto     o assunto que o acervo não responde;
    nomes       os nomes que a pessoa deu (relação=nome);
    cuidado     "saude" quando a fala toca em saúde.

Entrada (mesmos tokens especiais da base):
    <documento> contexto <fim> [<usuario> fala <fim> <assistente> resposta <fim>]... <assistente>
No treino, todas as falas de <assistente> da janela têm perda (não só a última).
"""
import re

CAMPOS = ("quem", "lembrancas", "fatos", "assunto", "nomes", "cuidado")
MAX_CONTEXTO_TOKENS = 256
ESPECIAIS = re.compile(r"<(?:pad|documento|usuario|assistente|fim)>")


def limpar(texto):
    """O tokenizador reconhece tokens especiais dentro do texto: uma fala não pode trazer um <fim>."""
    return ESPECIAIS.sub(" ", texto)


def serializar_contexto(ctx):
    partes = []
    for campo in CAMPOS:
        valor = (ctx or {}).get(campo)
        if not valor:
            continue
        if campo in ("fatos", "lembrancas"):
            valor = " | ".join(valor)
        elif campo == "nomes":
            valor = ", ".join("%s=%s" % (r, n) for r, n in valor.items())
        partes.append("%s: %s" % (campo, valor))
    return "; ".join(partes) or "nada"


def montar(codificar, esp, ctx, turnos, contexto=1024, gerar=False):
    """(ids, alvo) com alvo[i] = 1 nos tokens que têm perda (falas do assistente e o <fim> delas).

    codificar(texto) -> lista de ids, sem tokens especiais. turnos: [{"papel", "texto"}], o último
    do assistente no treino; com gerar=True, o prompt termina em <assistente>.
    Os turnos mais antigos saem quando não cabem."""
    doc = [esp["<documento>"]] + list(codificar(limpar(serializar_contexto(ctx))))[:MAX_CONTEXTO_TOKENS] + [esp["<fim>"]]
    segs = []
    for t in turnos:
        papel = "<usuario>" if t["papel"] == "usuario" else "<assistente>"
        ids = [esp[papel]] + list(codificar(limpar(t["texto"]))) + [esp["<fim>"]]
        alvo = [0] + [1] * (len(ids) - 1) if papel == "<assistente>" else [0] * len(ids)
        segs.append((ids, alvo))
    if gerar:
        segs.append(([esp["<assistente>"]], [0]))
    orc = contexto - len(doc)
    escolhidos, total = [], 0
    for ids, alvo in reversed(segs):
        if total + len(ids) > orc:
            break
        escolhidos.insert(0, (ids, alvo)); total += len(ids)
    if not escolhidos or (not gerar and sum(escolhidos[-1][1]) == 0):
        raise ValueError("a fala-alvo não cabe")
    ids = doc + [i for s, _ in escolhidos for i in s]
    alvo = [0] * len(doc) + [a for _, al in escolhidos for a in al]
    return ids, alvo
