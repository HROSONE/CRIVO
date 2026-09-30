"""Treino local do roteador, separado das respostas e das sondas finais."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

from intencao_gerativa import (ACOES, DIMENSAO, IntencaoGerativa,
                              atributos, assinatura_atributos, normalizar_estado)
from rede_sequencial import RedeSequencial, assinatura, normalizar, palavras

MANTER_LEXICO = frozenset(("a", "as", "o", "os", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos",
                           "em", "na", "no", "nas", "nos", "num", "numa", "por", "pelo", "pela", "para", "com",
                           "e", "ou", "que", "se", "eu", "me", "meu", "minha", "voce", "isso", "esse", "essa",
                           "historia", "conto", "narrativa", "poema", "poesia", "versos", "dialogo", "cena",
                           "mensagem", "carta", "recado"))


def tipo_historico(texto):
    """Reconhece um pedido anterior, sem confundir menções num relato."""
    n = normalizar(texto).strip()
    m = re.match(r"^(?:(?:por favor|agora|entao)[, ]+)*(?:eu )?"
                 r"(?:(?:voce )?(?:pode|poderia|consegue|conseguiria) )?(?:me )?"
                 r"(?:invente|inventa|inventar|crie|cria|criar|escreva|escreve|escrever|"
                 r"conte|conta|contar|componha|compor|imagine|imagina|imaginar|narre|narrar|"
                 r"faca|fazer|prepare|preparar|redija|redigir|mostre|mostrar|quero|gostaria|queria) "
                 r"(?:de )?(?:(?:um|uma|o|a|outro|outra) )?"
                 r"(historia|conto|narrativa|poema|versos|poesia|mensagem|recado|carta|dialogo|cena|"
                 r"conversa (?:ficticia|imaginaria))\b", n)
    if not m:
        return ""
    genero = m.group(1)
    for nome, generos in (("historia", ("historia", "conto", "narrativa")),
                          ("poema", ("poema", "versos", "poesia")),
                          ("mensagem", ("mensagem", "recado", "carta")),
                          ("dialogo", ("dialogo", "cena", "conversa ficticia", "conversa imaginaria"))):
        if genero in generos:
            return nome
    return ""


def estado_contexto(contexto):
    """Reconstrói informação disponível antes do pedido, sem ler seu rótulo.

    Slots pessoais são declarações já extraídas pelo gerenciador. O gênero
    de uma criação anterior vem exclusivamente do histórico de pedidos.
    """
    slots = contexto.get("slots", {})
    historico = contexto.get("historico", [])
    if not isinstance(slots, dict) or not isinstance(historico, list) or any(
            not isinstance(t, str) for t in historico):
        raise ValueError("Contexto de intenção inválido")
    tipo = ""
    for texto in historico:
        reconhecido = tipo_historico(texto)
        if reconhecido:
            tipo = reconhecido
    return normalizar_estado({"relato": bool(slots.get("relato")),
                              "objetivo": bool(slots.get("objetivo")),
                              "restricao": bool(slots.get("restricao")),
                              "criacao": tipo in ("historia", "poema", "dialogo"), "tipo_escrita": tipo})


def chave_exemplo(texto, estado):
    return assinatura({"texto": " ".join(normalizar(texto).split()), "estado": estado})


def preparar_dados(dados, exigir_todas=True):
    if dados.get("versao") != 1 or not isinstance(dados.get("exemplos"), list):
        raise ValueError("Currículo de intenção inválido")
    grupos = {"treino": {}, "validacao": {}}
    familias = {"treino": set(), "validacao": set()}
    dialogos = {"treino": set(), "validacao": set()}
    for c in dados["exemplos"]:
        split = c.get("split")
        ctx = c.get("contexto", {})
        acao, texto = ctx.get("acao"), ctx.get("mensagem")
        if (split not in grupos or acao not in ACOES or not isinstance(texto, str) or
                not texto.strip() or len(texto) > 1200 or not isinstance(c.get("familia"), str) or
                not isinstance(c.get("dialogo"), str)):
            raise ValueError("Exemplo de intenção inválido")
        estado = estado_contexto(ctx)
        chave = chave_exemplo(texto, estado)
        anterior = grupos[split].get(chave)
        if anterior and anterior["acao"] != acao:
            raise ValueError("O mesmo pedido e estado têm ações conflitantes")
        familias[split].add(c["familia"])
        dialogos[split].add(c["dialogo"])
        if anterior is None:
            grupos[split][chave] = {"texto": texto, "estado": estado, "acao": acao,
                                     "familia": c["familia"], "dialogo": c["dialogo"]}
    if (familias["treino"] & familias["validacao"] or
            dialogos["treino"] & dialogos["validacao"] or
            set(grupos["treino"]) & set(grupos["validacao"])):
        raise ValueError("Famílias, grupos ou pedidos com estado misturados entre partições")
    treino, validacao = list(grupos["treino"].values()), list(grupos["validacao"].values())
    if not treino or not validacao or (exigir_todas and {c["acao"] for c in treino} != set(ACOES)):
        raise ValueError("Treino e validação são necessários; o treino deve cobrir as 16 ações")
    return treino, validacao


def temas_treino(dados):
    """Nomes copiáveis não são operadores; a validação não fornece léxico."""
    temas = set()
    for c in dados["exemplos"]:
        if c["split"] == "treino":
            slots = c["contexto"].get("slots", {})
            for nome in ("tema1", "tema2", "destinatario"):
                valor = slots.get(nome, "")
                if isinstance(valor, str):
                    temas.update(t for t, _, _ in palavras(valor))
    return sorted(temas - MANTER_LEXICO)


def lexico_treino(casos, termos_temas=()):
    # A contagem usa um voto por pedido, não as variantes de sua resposta.
    contagem = Counter()
    for c in casos:
        contagem.update(set(t for t, _, _ in palavras(c["texto"])))
    ignorar = set(termos_temas) - MANTER_LEXICO
    return sorted(t for t, quantidade in contagem.items() if quantidade >= 3 and t not in ignorar)


def avaliar(modelo, casos):
    resultado = {"total": len(casos), "acertos": 0, "aceitos": 0,
                 "aceitos_corretos": 0, "por_acao": {}, "erros": []}
    for c in casos:
        q = modelo.analisar(c["texto"], c["estado"])
        correto, aceito = q["acao"] == c["acao"], q["aceita"]
        linha = resultado["por_acao"].setdefault(c["acao"],
                  {"total": 0, "acertos": 0, "aceitos": 0, "aceitos_corretos": 0})
        for destino in (resultado, linha):
            if destino is linha:
                destino["total"] += 1
            destino["acertos"] += int(correto)
            destino["aceitos"] += int(aceito)
            destino["aceitos_corretos"] += int(correto and aceito)
        if not correto:
            resultado["erros"].append({"texto": c["texto"], "estado": c["estado"],
              "esperado": c["acao"], "obtido": q["acao"], "confianca": q["confianca"],
              "margem": q["margem"], "aceita": aceito})
    return resultado


def treinar(caminho, destino, epocas=110, semente=107, acelerar=False, ocultos=48):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    treino, validacao = preparar_dados(dados)
    termos_temas = temas_treino(dados)
    lexico = lexico_treino(treino, termos_temas)
    rede = RedeSequencial(ACOES, DIMENSAO, ocultos, semente)
    rede.treinar([(atributos(c["texto"], c["estado"], lexico), c["acao"]) for c in treino],
                 epocas=epocas, semente=semente, acelerar=acelerar)
    checkpoint = {"versao": 1, "assinatura_atributos": assinatura_atributos(),
                  "assinatura_treino": assinatura(treino), "assinatura_curriculo": assinatura(dados), "lexico": lexico,
                  "limiar": .80, "margem_minima": .20, "rede": rede.dados(),
                  "treino": {"epocas": epocas, "semente": semente, "pedidos_unicos": len(treino),
                    "representacao": "temas_abstraidos_do_treino-v1", "termos_temas": termos_temas,
                    "familias": len({c["familia"] for c in treino}),
                    "grupos": len({c["dialogo"] for c in treino}),
                    "acoes": dict(Counter(c["acao"] for c in treino)),
                    "acelerador": "numpy" if acelerar else "python"}}
    modelo = IntencaoGerativa(checkpoint)
    # Neste ajuste, a validação entra apenas na inferência. A representação
    # foi revisada no diagnóstico documentado, usando somente temas do
    # treino; os limiares e hiperparâmetros permaneceram fixos.
    resultado = {"treino": avaliar(modelo, treino), "validacao": avaliar(modelo, validacao),
                 "assinatura_treino": checkpoint["assinatura_treino"],
                 "assinatura_curriculo": checkpoint["assinatura_curriculo"],
                 "limite": "Validação interna autoral de pedidos com famílias, grupos e pares pedido/estado separados. Consultada no diagnóstico da representação dos temas; não é avaliação cega. Não mede conhecimento, geração livre nem compreensão universal."}
    Path(destino).write_text(json.dumps(checkpoint, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return resultado


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dados", default="curriculo_geracao.json")
    p.add_argument("--saida", default="rede_intencao_gerativa.json")
    p.add_argument("--relatorio", default="avaliacao_intencao_gerativa.json")
    p.add_argument("--epocas", type=int, default=110)
    p.add_argument("--semente", type=int, default=107)
    p.add_argument("--ocultos", type=int, default=48)
    p.add_argument("--numpy", action="store_true")
    a = p.parse_args()
    resultado = treinar(a.dados, a.saida, a.epocas, a.semente, a.numpy, a.ocultos)
    Path(a.relatorio).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {f: v[f] for f in ("total", "acertos", "aceitos", "aceitos_corretos")}
                      for k, v in resultado.items() if k in ("treino", "validacao")}, ensure_ascii=False))
