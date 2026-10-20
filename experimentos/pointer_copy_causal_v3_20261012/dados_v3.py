"""Dados e métricas do Pointer/Copy Causal v3.

Diferença causal em relação ao v2: a mensagem e a resposta são escritas como
texto completo e tokenizadas pelas funções do runtime (`fonte_dialogo` e
`codificar_texto`), nunca colando IDs do nome. A cabeça pointer é a mesma do v2.
Este módulo é usado pelo script que congela os blinds e pelo notebook do Colab,
para que os dois montem exatamente os mesmos casos.
"""
import re

TAREFAS = ("copia", "categoria", "funcao", "invariancia", "composicao", "negacao")
POSICOES = ("inicio", "meio", "fim")
CATEGORIAS = ["recipiente", "ferramenta", "instrumento", "veiculo", "alimento"]
CAT_TXT = {
    "recipiente": "recipiente",
    "ferramenta": "ferramenta",
    "instrumento": "instrumento",
    "veiculo": "veículo",
    "alimento": "alimento",
}
ARTIGO = {"recipiente": "um", "ferramenta": "uma", "instrumento": "um",
          "veiculo": "um", "alimento": "um"}
FUNCOES_TXT = {
    "recipiente": "guardar substâncias",
    "ferramenta": "apertar peças",
    "instrumento": "medir sinais",
    "veiculo": "transportar carga",
    "alimento": "nutrir pessoas",
}
ENCHIMENTOS = [
    "Considere apenas os dados desta ficha.",
    "O catálogo experimental preserva a identidade dos objetos.",
    "A descrição seguinte é suficiente para responder.",
    "Não invente propriedades além das fornecidas.",
]
NO_COPY_PARES = [
    ("Quanto é dois mais dois? Responda por extenso.", "quatro"),
    ("Qual cor resulta de azul com amarelo? Responda com uma palavra.", "verde"),
    ("Qual é o contrário de quente? Responda com uma palavra.", "frio"),
    ("Qual é o contrário de subir? Responda com uma palavra.", "descer"),
    ("Complete: manhã, tarde e ...", "noite"),
    ("Qual animal doméstico costuma miar?", "gato"),
    ("Qual astro ilumina o dia?", "sol"),
    ("Qual é o plural de casa?", "casas"),
    ("Qual estação vem depois do inverno?", "primavera"),
    ("Qual é o contrário de abrir?", "fechar"),
    ("Qual número vem depois de nove? Responda por extenso.", "dez"),
    ("Qual é a primeira vogal?", "a"),
]


def errada_de(categoria):
    return next(c for c in CATEGORIAS if c != categoria)


def com_artigo(categoria):
    return f"{ARTIGO[categoria]} {CAT_TXT[categoria]}"


def palavras_dos_modelos():
    """Palavras que aparecem nos textos fixos; um nome igual a uma delas seria ambíguo."""
    textos = list(ENCHIMENTOS) + list(CAT_TXT.values()) + list(FUNCOES_TXT.values()) + [
        "Existe um objeto inventado chamado Ele é um uma usado para",
        "Repita exatamente o nome do objeto e nada além do nome",
        "Qual é a categoria de Preserve o nome exato função",
        "Mudar o material de para muda a identidade Use o nome exato",
        "Diga em uma frase o nome exato a categoria e a função",
        "Corrija usando o nome exato serve continua sendo o mesmo objeto Não não",
    ]
    return {p.casefold() for t in textos for p in re.findall(r"[\wÀ-ÿ-]+", t)}


def pergunta_texto(ent, tarefa):
    nome = ent["nome"]
    if tarefa == "copia":
        return "Repita exatamente o nome do objeto e nada além do nome."
    if tarefa == "categoria":
        return f"Qual é a categoria de {nome}? Preserve o nome exato."
    if tarefa == "funcao":
        return f"Qual é a função de {nome}? Preserve o nome exato."
    if tarefa == "invariancia":
        return (f"Mudar o material de {ent['material_a']} para {ent['material_b']} "
                "muda a identidade? Use o nome exato.")
    if tarefa == "composicao":
        return "Diga em uma frase o nome exato, a categoria e a função."
    if tarefa == "negacao":
        return f"{nome} é {com_artigo(errada_de(ent['categoria']))}? Corrija usando o nome exato."
    raise ValueError(tarefa)


def mensagem_texto(ent, tarefa, posicao):
    cat = ent["categoria"]
    definicao = (f"Existe um objeto inventado chamado {ent['nome']}. "
                 f"Ele é {com_artigo(cat)} usado para {FUNCOES_TXT[cat]}.")
    q = pergunta_texto(ent, tarefa)
    if posicao == "inicio":
        return f"{definicao} {ENCHIMENTOS[0]} {q}"
    if posicao == "meio":
        return f"{ENCHIMENTOS[1]} {definicao} {ENCHIMENTOS[2]} {q}"
    if posicao == "fim":
        return f"{ENCHIMENTOS[2]} {ENCHIMENTOS[3]} {definicao} {q}"
    raise ValueError(posicao)


def resposta_texto(ent, tarefa):
    nome, cat = ent["nome"], ent["categoria"]
    fun = FUNCOES_TXT[cat]
    if tarefa == "copia":
        return nome
    if tarefa == "categoria":
        return f"{nome} é {com_artigo(cat)}."
    if tarefa == "funcao":
        return f"{nome} serve para {fun}."
    if tarefa == "invariancia":
        return f"Não. {nome} continua sendo o mesmo objeto."
    if tarefa == "composicao":
        return f"{nome} é {com_artigo(cat)} usado para {fun}."
    if tarefa == "negacao":
        return f"Não. {nome} é {com_artigo(cat)}, não {com_artigo(errada_de(cat))}."
    raise ValueError(tarefa)


def achar_span(hay, needle):
    n = len(needle)
    for i in range(len(hay) - n + 1):
        if hay[i:i + n] == needle:
            return i
    return -1


def montar_caso(lp, tokenizer, ent, tarefa, posicao, contexto):
    """Monta um caso com a tokenização do runtime. Nada de IDs colados."""
    especiais = {tokenizer.token_to_id(s) for s in lp.ESPECIAIS}
    id_fim = tokenizer.token_to_id("<fim>")
    msg = mensagem_texto(ent, tarefa, posicao)
    resp = resposta_texto(ent, tarefa)
    prompt = list(lp.fonte_dialogo(tokenizer, msg, (), contexto))
    resp_ids = list(lp.codificar_texto(tokenizer, resp)) + [id_fim]
    if len(prompt) + len(resp_ids) > contexto:
        raise RuntimeError("caso excede o contexto")

    nome = ent["nome"]
    var_meio = list(lp.codificar_texto(tokenizer, " " + nome))
    var_inicio = list(lp.codificar_texto(tokenizer, nome))
    if achar_span(prompt, var_meio) < 0:
        raise RuntimeError(f"nome {nome!r} não aparece como span no prompt")
    alvo = var_inicio if resp.startswith(nome) else var_meio
    ini = achar_span(resp_ids, alvo)
    if ini < 0:
        raise RuntimeError(f"nome {nome!r} não aparece como span na resposta")

    fonte = {t for t in prompt if t not in especiais}
    nome_resp = [ini <= i < ini + len(alvo) for i in range(len(resp_ids))]
    copiavel = [m and t in fonte for t, m in zip(resp_ids, nome_resp)]
    return {
        "nome": nome,
        "grupo": ent["grupo"],
        "n_tokens": int(ent["n_tokens"]),
        "categoria": ent["categoria"],
        "tarefa": tarefa,
        "posicao": posicao,
        "mensagem": msg,
        "resposta": resp,
        "prompt_ids": prompt,
        "resp_ids": resp_ids,
        "nome_resp": nome_resp,
        "copy_resp": copiavel,
        "nome_no_inicio_da_resposta": resp.startswith(nome),
        "nome_todo_copiavel": all(c for c, m in zip(copiavel, nome_resp) if m),
        "no_copy": False,
    }


def montar_no_copy(lp, tokenizer, pergunta, resposta, contexto):
    id_fim = tokenizer.token_to_id("<fim>")
    prompt = list(lp.fonte_dialogo(tokenizer, pergunta, (), contexto))
    resp_ids = list(lp.codificar_texto(tokenizer, resposta)) + [id_fim]
    return {
        "nome": None, "grupo": "no_copy", "n_tokens": 0, "categoria": None,
        "tarefa": "no_copy", "posicao": "na", "mensagem": pergunta,
        "resposta": resposta, "prompt_ids": prompt, "resp_ids": resp_ids,
        "nome_resp": [False] * len(resp_ids), "copy_resp": [False] * len(resp_ids),
        "nome_no_inicio_da_resposta": False, "nome_todo_copiavel": False,
        "no_copy": True,
    }


def ocorrencias_nome(texto, nome):
    return len(re.findall(r"(?<![\w-])" + re.escape(nome) + r"(?![\w-])", texto))


def avaliar_saida(caso, texto, terminou):
    """Métricas no texto decodificado; o nome tem de aparecer exato e isolado."""
    texto = texto.strip()
    nome, cat = caso["nome"], caso["categoria"]
    n = ocorrencias_nome(texto, nome)
    nome_ok = n >= 1
    cat_ok = com_artigo(cat) in texto
    fun_ok = FUNCOES_TXT[cat] in texto
    comeca_nao = texto.startswith("Não")
    tarefa = caso["tarefa"]
    semantica = {
        "copia": texto == nome and terminou,
        "categoria": nome_ok and cat_ok,
        "funcao": nome_ok and fun_ok,
        "invariancia": nome_ok and comeca_nao,
        "composicao": nome_ok and cat_ok and fun_ok,
        "negacao": nome_ok and comeca_nao and cat_ok,
    }[tarefa]
    return {
        "exact_name": nome_ok,
        "exact_name_fim": texto == nome and terminou,
        "resposta_exata": texto == caso["resposta"] and terminou,
        "nome_duplicado": n >= 2,
        "semantic_ok": bool(semantica),
        "terminou": bool(terminou),
    }


def resumir(linhas):
    def taxa(xs, chave):
        return None if not xs else sum(bool(x[chave]) for x in xs) / len(xs)

    def sub(**filtro):
        return [r for r in linhas if all(r[k] == v for k, v in filtro.items())]

    out = {"n": len(linhas)}
    for t in TAREFAS:
        xs = sub(tarefa=t)
        out[t] = {
            "n": len(xs),
            "exact_name": taxa(xs, "exact_name"),
            "exact_name_fim": taxa(xs, "exact_name_fim"),
            "resposta_exata": taxa(xs, "resposta_exata"),
            "semantica": taxa(xs, "semantic_ok"),
            "nome_duplicado": taxa(xs, "nome_duplicado"),
            "terminacao": taxa(xs, "terminou"),
        }
    out["exact_name"] = taxa(linhas, "exact_name")
    out["exact_name_fim_copia"] = out["copia"]["exact_name_fim"]
    out["lexical_close"] = taxa(sub(grupo="close"), "exact_name")
    out["lexical_distant"] = taxa(sub(grupo="distant"), "exact_name")
    for p in POSICOES:
        out[f"posicao_{p}"] = taxa(sub(posicao=p), "exact_name")
    for L in (1, 2, 3, 4):
        out[f"token_len_{L}"] = taxa(sub(n_tokens=L), "exact_name")
    out["nome_no_inicio"] = taxa([r for r in linhas if r["nome_no_inicio_da_resposta"]], "exact_name")
    out["nome_no_meio"] = taxa([r for r in linhas if not r["nome_no_inicio_da_resposta"]], "exact_name")
    sem = [out[t]["semantica"] for t in ("categoria", "funcao", "invariancia", "composicao", "negacao")]
    out["semantica_geral"] = sum(sem) / len(sem)
    out["terminacao"] = taxa(linhas, "terminou")
    out["nome_duplicado"] = taxa(linhas, "nome_duplicado")
    return out
