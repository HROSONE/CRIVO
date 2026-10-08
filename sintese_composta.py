"""Extensão estrutural da síntese, após a busca congelada V3 falhar.

Usa apenas exemplos fornecidos e o executor do Crivo. A gramática amplia
expressões aritméticas com duas operações e reduções de arrays. Não aprende
pesos, não usa referências ocultas e divide o orçamento com a busca inicial.
"""
from busca_estados import acertou, validar_casos
from interpretacao_estruturas import javascript


def candidatos(tipo):
    if tipo == "numero":
        constantes = (-2, -1, 0, 1, 2, 3, 4, 5)
        for formato in ("return (entrada * {a}) + {b};",
                        "return (entrada + {a}) * {b};",
                        "return (entrada * {a}) - {b};"):
            for a in constantes:
                for b in constantes:
                    yield formato.format(a=a, b=b)
    elif tipo == "array":
        for comparacao in (">", "<"):
            # null explicita o domínio vazio; a própria validação decide
            # se esse comportamento é compatível com o contrato fornecido.
            yield ("if (entrada.length === 0) { return null; } "
                   "let melhor = entrada[0]; let i = 1; "
                   "while (i < entrada.length) { if (entrada[i] " + comparacao +
                   " melhor) { melhor = entrada[i]; } i += 1; } return melhor;")


def buscar_composta(casos, tipo, limite):
    validar_casos(casos)
    if type(limite) is not int or not 0 <= limite <= 1000:
        raise ValueError("Orçamento restante inválido")
    verificadas = 0
    for codigo in candidatos(tipo):
        if verificadas >= limite:
            break
        verificadas += 1
        if all(acertou(codigo, c) for c in casos):
            return dict(corpo=codigo, codigo=javascript(codigo), verificadas=verificadas,
                        atende_desenvolvimento=True, origem="estrutural_composta")
    return dict(corpo=None, codigo=None, verificadas=verificadas,
                atende_desenvolvimento=False, origem="estrutural_composta")
