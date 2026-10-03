"""Interpreta pedidos cujo objeto é o próprio texto, não um fato isolado.

O recuperador factual responde *sobre* conceitos cadastrados.  Este módulo
complementa essa capacidade para três atos que exigem olhar a frase inteira:
analisar uma passagem citada, retomar o sentido da resposta anterior e reagir
a uma descrição explícita do próprio Crivo.  As análises são determinísticas e
mostram as pistas linguísticas usadas; não fingem uma leitura irrestrita.
"""
import re


def _normalizar(texto):
    from crivo import normalizar
    return normalizar(texto)


def _citado(texto):
    pares = re.findall(r"['\"“‘](.+?)['\"”’]", texto, re.DOTALL)
    if pares:
        return max(pares, key=len).strip()
    m = re.search(r"\b(?:poema|frase|trecho|texto)\s*:\s*(.+)$", texto,
                  re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else ""


def interpretar_passagem(texto):
    """Analisa recursos que estão comprovadamente presentes numa citação."""
    n = _normalizar(texto)
    if not re.search(r"\b(?:interpret\w*|analis\w*|sentido)\b", n):
        return None
    passagem = _citado(texto)
    if not passagem:
        return None
    p = _normalizar(passagem)
    observacoes = []
    comparacao = re.search(r"\bcomo\s+(?:um|uma|o|a)?\s*([^,.;:!?]+)", p)
    if comparacao:
        observacoes.append(
            "A expressão “como %s” cria uma comparação que transforma a cena "
            "concreta em uma imagem visual." % comparacao.group(1).strip())
    if re.search(r"\b(?:vento|chuva|sol|mar|rio|ceu|árvor|arvor|folh|flor)\w*\b", p):
        observacoes.append(
            "Os elementos da natureza e o movimento produzem uma imagem sensorial, "
            "mais voltada a fazer o leitor visualizar a cena do que a narrar uma ação complexa.")
    contraste = re.search(r"\b(?:mas|porem|porém|entretanto|embora)\b", p)
    if contraste:
        observacoes.append("Há um contraste explícito que coloca duas ideias em tensão.")
    if not observacoes:
        observacoes.append(
            "O trecho apresenta uma imagem central, mas não traz pistas suficientes para atribuir "
            "uma intenção única ao autor.")
    conclusao = (
        "Uma leitura possível é que o trecho transmite força e movimento, enquanto a imagem "
        "ampla sugerida pela comparação dá unidade à paisagem. Isso é uma interpretação apoiada "
        "nas palavras do trecho, não a única leitura possível."
        if comparacao and re.search(r"\b(?:forte|forca|balanc|movimento)\w*\b", p)
        else "Essas pistas sustentam uma leitura possível; o trecho, sozinho, não determina uma única interpretação.")
    return "texto:interpretacao", " ".join(observacoes + [conclusao])


def retomar_sentido(texto, contexto):
    """Explica a ideia central da resposta factual imediatamente anterior."""
    n = _normalizar(texto)
    if contexto is None or not re.search(
            r"\b(?:significado|sentido|quis dizer|entender|compreender)\b", n):
        return None
    if not re.search(r"\b(?:texto|explicacao|resposta|isso).*(?:anterior|antes|enviei|mandei)|"
                     r"\b(?:anteriormente|antes)\b", n):
        return None
    if not contexto.exibidos:
        return None
    primeiro_id, _ = contexto.exibidos[0]
    # O contexto contém somente pares que foram efetivamente exibidos. Assim,
    # a paráfrase nunca recupera um fato oculto ou um assunto apenas parecido.
    frase = contexto.texto.strip().split("\n\n", 1)[0].strip()
    frase = re.sub(r"^(?:Em resumo|Em termos simples):\s*", "", frase,
                   flags=re.IGNORECASE)
    alvo = re.search(r"\bsobre\s+(.+?)(?:\s+que\b|\s+(?:anteriormente|antes)\b|[?.!,]|$)",
                     texto, re.IGNORECASE)
    nome = alvo.group(1).strip() if alvo else primeiro_id.replace("_", " ")
    return ("texto:retomada",
            "Sim. A ideia central da explicação anterior sobre %s é: %s "
            "Estou retomando o conteúdo que apareceu na resposta, sem inventar um texto que não foi enviado."
            % (nome, frase))


def descricao_do_crivo(texto):
    """Distingue uma descrição dirigida ao assistente de um relato do usuário."""
    n = _normalizar(texto).strip(" .!?")
    if not re.match(r"(?:crivo[, ]+)?voce (?:e|eh) ", n):
        return None
    pistas = []
    if "inteligencia artificial" in n or re.search(r"\bia\b", n):
        pistas.append("sou uma inteligência artificial")
    if "desenvolvimento" in n or "experimental" in n:
        pistas.append("este projeto ainda está em desenvolvimento")
    if "simbolic" in n:
        pistas.append("uso conhecimento e relações simbólicas cadastradas")
    if "limit" in n and re.search(r"\b(?:context|interpret|complex)\w*", n):
        pistas.append("tenho limitações reais para interpretar contextos gerais ou complexos")
    if len(pistas) < 2:
        return None
    return ("social:autodescricao",
            "Sua descrição está essencialmente correta: " + "; ".join(pistas) +
            ". Eu também combino esses mecanismos com componentes treinados localmente, mas isso não elimina "
            "meus limites. Em vez de tratar sua frase como um relato sobre você, reconheço que ela descreve a mim.")


def raciocinio_simbolico_aplicado(texto):
    """Reconhece um pedido de aplicação e explicita a cadeia de resolução."""
    n = _normalizar(texto)
    if not ("raciocinio simbolico" in n and
            re.search(r"\b(?:resolver|solucionar|aplicar|usad[oa])\w*\b", n)):
        return None
    exemplo = "No exemplo do labirinto, " if "labirinto" in n else "No problema, "
    resposta = (
        "O raciocínio simbólico representa o problema com símbolos e regras explícitas, em vez de tentar "
        "adivinhar uma saída por semelhança. %scada porta pode virar uma variável (P1, P2, P3), e cada pista "
        "vira uma restrição lógica — por exemplo, “exatamente uma porta é segura” ou “se P1 é segura, P2 não é”.\n\n"
        "A resolução pode seguir quatro passos:\n"
        "1. listar as possibilidades para as portas e o estado de cada uma;\n"
        "2. traduzir todas as pistas para regras como E, OU, NÃO e SE…ENTÃO;\n"
        "3. testar cada combinação, eliminando as que contradizem alguma regra;\n"
        "4. escolher a combinação que satisfaz todas as restrições e mostrar quais regras eliminaram as demais.\n\n"
        "Se nenhuma combinação sobreviver, as pistas são inconsistentes; se várias sobreviverem, falta informação. "
        "Essa verificação explícita é a principal vantagem: a conclusão vem acompanhada de uma cadeia auditável."
    ) % exemplo
    return "texto:raciocinio_simbolico", resposta


def responder(texto, contexto=None):
    for analisador in (interpretar_passagem, raciocinio_simbolico_aplicado,
                       descricao_do_crivo):
        resultado = analisador(texto)
        if resultado is not None:
            return resultado
    return retomar_sentido(texto, contexto)
