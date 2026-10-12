"""Formato e métricas da fase 3: o 17M como realizador do quadro do CRIVO.

O quadro decide o ATO e o CONTEÚDO (fatos verificados, nomes, sentimento, motivo);
o 17M só transforma isso em fala, no tom de IDENTIDADE.md, e para em <fim>.

Entrada do modelo (mesmos tokens especiais da base, nenhum novo):
    <documento> quadro serializado <fim> <usuario> mensagem <fim> <assistente>
Saída:
    resposta <fim>

Este módulo é usado pelo gerador de dados, pelo notebook e, mais tarde, pelo
runtime — para que treino e uso montem a entrada exatamente igual.
"""
import re

CAMPOS = ("ato", "assunto", "fatos", "relacao", "nome", "sentimento", "motivo", "falta", "ponto", "certo")

# Palavras com maiúscula que o realizador pode usar sem tirá-las da entrada.
MAIUSCULAS_PERMITIDAS = {"CRIVO", "IA", "Deus", "Oi", "Olá", "Bom", "Boa", "Que", "Isso", "Lembro",
                         "Você", "Me", "Se", "Olha", "Então", "Vamos", "Adoro", "Hmm", "Anotado",
                         "Obrigado", "Sinto", "Tô", "Não", "Sim", "Quer", "Achei", "Um", "Uma", "E",
                         "Sobre", "Puxa", "Poxa", "Eita", "Legal", "Entendi", "Desculpa", "Certo",
                         "Claro", "Faz", "Tudo", "Muito", "Opa", "Imagina", "Valeu", "Bom-dia",
                         "Essa", "Esse", "Eu", "Seu", "Sua", "Ah", "Nossa", "Acho", "Pode", "Prefiro",
                         "Nem", "Ainda", "Ótimo", "Ótima", "Boa-noite", "Boa-tarde", "Aqui", "Agora",
                         "Fico", "Conta", "Robô", "Perfeito", "Combinado", "Beleza", "Valeu!", "Gosto",
                         "Penso", "Sei", "Mas", "Quando", "Por", "Para", "Pra", "O", "A", "Os", "As",
                         "Já", "Tem", "Pensa", "Até", "Aí", "Ele", "Ela", "Foi", "Era", "Dá", "Também",
                         "Gostei", "Imagino", "Respira", "Sempre", "Sinceramente", "Sou", "Prazer",
                         "Depende", "Como", "É", "Com", "Do", "Qual", "Quero"}

# Marcas mínimas que mostram que o ato certo foi realizado (minúsculas, sem acento opcional).
MARCAS_ATO = {
    "explicar": None,  # conferido pela cópia fiel dos fatos
    "nao_sei": r"\bn[ãa]o (sei|tenho)\b",
    "esclarecer": r"\?",
    "acolher": r"(sinto muito|t[ôo] aqui|quer (me )?contar|que bom|imagino|faz sentido|fico feliz|"
               r"compreens[íi]vel|pode contar comigo|respira)",
    "registrar": None,  # conferido pelo nome exato
    "recordar": None,   # conferido pelo nome exato
    "aceitar_correcao": r"(raz[ãa]o|errei|obrigad)",
    "recusar": r"\bn[ãa]o (vou|posso|topo|fa[çc]o)\b",
    "falar_de_si": r"\bia\b",
    "saudar": r"\b(oi|ol[áa]|bom dia|boa tarde|boa noite|e a[ií])\b",
}


def serializar_quadro(quadro):
    """Texto curto e estável. Fatos separados por ' | '."""
    partes = []
    for campo in CAMPOS:
        if campo not in quadro or quadro[campo] in (None, "", []):
            continue
        valor = quadro[campo]
        if campo == "fatos":
            valor = " | ".join(valor)
        partes.append(f"{campo}: {valor}")
    return "; ".join(partes)


def montar_ids(lp, tokenizer, quadro, mensagem, resposta, contexto):
    ids = {s: tokenizer.token_to_id(s) for s in lp.ESPECIAIS}
    qid = lp.codificar_texto(tokenizer, serializar_quadro(quadro))
    prompt = [ids["<documento>"]] + list(qid) + [ids["<fim>"]] + list(
        lp.fonte_dialogo(tokenizer, mensagem, (), contexto))
    resp = list(lp.codificar_texto(tokenizer, resposta)) + [ids["<fim>"]] if resposta is not None else []
    if len(prompt) + len(resp) > contexto:
        raise ValueError("caso excede o contexto")
    return prompt, resp


def _quatrigramas_repetidos(texto):
    palavras = re.findall(r"\w+", texto.casefold())
    vistos = set()
    for i in range(len(palavras) - 3):
        g = tuple(palavras[i:i + 4])
        if g in vistos:
            return True
        vistos.add(g)
    return False


def avaliar_saida(caso, texto, terminou):
    """Critérios de forma; o conteúdo já foi decidido pelo quadro."""
    texto = texto.strip()
    q = caso["quadro"]
    baixo = texto.casefold()
    fatos = q.get("fatos") or []
    # Repetição medida fora dos fatos copiados (o próprio acervo pode repetir trechos);
    # cada fato só pode aparecer uma vez.
    resto = texto
    for f in fatos:
        resto = resto.replace(f, " ")
    r = {"terminou": bool(terminou),
         "sem_repeticao": not _quatrigramas_repetidos(resto) and all(texto.count(f) <= 1 for f in fatos)}
    r["fatos_fieis"] = all(f in texto for f in fatos) if fatos else None
    nome = q.get("nome") or q.get("certo")
    if q.get("ato") == "nao_sei":
        nome = q.get("assunto")
    r["nome_exato"] = (re.search(r"(?<![\w-])" + re.escape(nome) + r"(?![\w-])", texto) is not None) if nome else None
    marca = MARCAS_ATO.get(q["ato"])
    r["ato_ok"] = bool(re.search(marca, baixo)) if marca else True
    if q["ato"] == "recusar" and q.get("motivo"):
        r["ato_ok"] = r["ato_ok"] and q["motivo"].casefold() in baixo
    entrada = serializar_quadro(q) + " " + caso["mensagem"]
    extras = [w for w in re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ-]*", texto)
              if w not in MAIUSCULAS_PERMITIDAS and w not in entrada]
    r["sem_nome_inventado"] = not extras
    r["inventados"] = extras[:5]
    obrig = [v for k, v in r.items() if k in ("terminou", "sem_repeticao", "fatos_fieis", "nome_exato",
                                               "ato_ok", "sem_nome_inventado") and v is not None]
    r["tudo_ok"] = all(obrig)
    return r


def resumir(linhas):
    def taxa(xs, k):
        vals = [x[k] for x in xs if x.get(k) is not None]
        return None if not vals else sum(bool(v) for v in vals) / len(vals)
    chaves = ("tudo_ok", "terminou", "sem_repeticao", "fatos_fieis", "nome_exato", "ato_ok", "sem_nome_inventado")
    out = {"n": len(linhas), **{k: taxa(linhas, k) for k in chaves}, "por_ato": {}}
    for ato in sorted({x["ato"] for x in linhas}):
        xs = [x for x in linhas if x["ato"] == ato]
        out["por_ato"][ato] = {"n": len(xs), **{k: taxa(xs, k) for k in chaves}}
    return out
