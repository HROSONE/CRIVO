"""Currículo factual curado: dados locais, fontes e exemplos de conceitos.

Só sínteses próprias, conferidas em fontes científicas com condições de
reutilização registradas, entram no currículo. Nenhum texto remoto,
modelo pronto, chave ou download é necessário durante a conversa/treino.
"""
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


NATUREZAS = frozenset(("cientifico", "psicologico", "orientacao", "filosofico", "social"))
REUTILIZACOES = frozenset(("dominio_publico", "CC-BY-4.0", "permissao_institucional",
                         "somente_referencia"))


def texto_fato(fato):
    return fato["texto"]


def ler_curriculo(caminho):
    caminho = Path(caminho)
    if not caminho.is_file():
        return None
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    # Catálogos temáticos pequenos podem ampliar o currículo sem duplicar o
    # arquivo principal. Eles passam pela mesma validação de fontes, fatos e IDs.
    # O carregamento é determinístico e local; nenhum conteúdo remoto é baixado.
    if caminho.name == "conhecimento_mundo.json":
        for extra_nome in ("conhecimento_astronomia_luas.json", "conhecimento_fisica.json",
                           "conhecimento_biologia.json", "conhecimento_sociologia.json",
                           "conhecimento_filosofia.json", "conhecimento_historia.json",
                           "conhecimento_geografia.json", "conhecimento_pessoas.json",
                           "conhecimento_literatura.json", "conhecimento_ciencias.json",
                           "conhecimento_ecologia.json", "conhecimento_artes.json",
                           "conhecimento_sociedade.json", "conhecimento_saude.json",
                           "conhecimento_tecnologia.json", "conhecimento_exatas.json",
                           "conhecimento_mente.json"):
            extra_path = caminho.with_name(extra_nome)
            if not extra_path.is_file():
                continue
            extra = json.loads(extra_path.read_text(encoding="utf-8"))
            if not isinstance(extra, dict) or extra.get("versao") != 1:
                raise ValueError("Currículo temático inválido")
            dados["fontes"].update(extra.get("fontes", {}))
            dados["itens"].extend(extra.get("itens", []))
            dados.setdefault("ligacoes", []).extend(extra.get("ligacoes", []))
            dados.setdefault("comparacoes", []).extend(extra.get("comparacoes", []))
    if (not isinstance(dados, dict) or dados.get("versao") != 1 or
            not isinstance(dados.get("fontes"), dict) or
            not isinstance(dados.get("itens"), list) or
            not 1 <= len(dados["itens"]) <= 1000):
        raise ValueError("Currículo do mundo inválido")
    fontes = dados["fontes"]
    for fonte in fontes.values():
        if (not isinstance(fonte, dict) or
                not isinstance(fonte.get("titulo"), str) or
                not isinstance(fonte.get("url"), str) or
                urlparse(fonte["url"]).scheme != "https" or
                not urlparse(fonte["url"]).netloc or
                fonte.get("tipo") not in ("institucional_cientifica", "artigo_cientifico", "catalogo_tecnico") or
                type(fonte.get("ano")) is not int or
                not 1900 <= fonte["ano"] <= 2100 or
                fonte.get("ano_tipo") not in ("publicacao", "consulta")):
            raise ValueError("Fonte do mundo sem título, URL, tipo ou ano")
        if (not isinstance(fonte.get("reutilizacao"), str) or
                fonte["reutilizacao"] not in REUTILIZACOES or
                not isinstance(fonte.get("direitos_url"), str) or
                urlparse(fonte["direitos_url"]).scheme != "https" or
                not urlparse(fonte["direitos_url"]).netloc or
                not isinstance(fonte.get("credito"), str) or not fonte["credito"].strip() or
                not isinstance(fonte.get("escopo_uso"), str) or not fonte["escopo_uso"].strip() or
                not isinstance(fonte.get("verificado_em"), str) or
                not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fonte["verificado_em"])):
            raise ValueError("Fonte científica sem condições de reutilização ou crédito")
        if (fonte["reutilizacao"] == "somente_referencia" and
                fonte.get("reproducao_autorizada") is not False):
            raise ValueError("Referência bibliográfica não pode presumir autorização de reprodução")
    ids = set()
    for item in dados["itens"]:
        if (not isinstance(item, dict) or
                not isinstance(item.get("id"), str) or
                not re.fullmatch(r"mundo_[a-z0-9_]{1,56}", item["id"]) or
                item["id"] in ids or not isinstance(item.get("nome"), str) or
                not item["nome"].strip() or not isinstance(item.get("area"), str) or
                not isinstance(item.get("aliases", []), list) or
                not all(isinstance(a, str) and a.strip() for a in item.get("aliases", [])) or
                not isinstance(item.get("fatos"), list) or not 1 <= len(item["fatos"]) <= 12):
            raise ValueError("Conceito do mundo inválido ou duplicado")
        ids.add(item["id"])
        if not isinstance(item["fatos"][0], dict) or item["fatos"][0].get("papel") != "definicao":
            raise ValueError("Conceito do mundo deve começar por definição")
        for fato in item["fatos"]:
            if (not isinstance(fato, dict) or not isinstance(fato.get("fonte"), str) or
                    fato["fonte"] not in fontes or
                    not isinstance(fato.get("texto"), str) or
                    not 1 <= len(fato["texto"].strip()) <= 1000 or
                    not isinstance(fato.get("natureza"), str) or
                    fato["natureza"] not in NATUREZAS or
                    fato.get("papel") not in ("definicao", "detalhe", "causa", "exemplo", "limite") or
                    not isinstance(fato.get("fontes", []), list) or
                    not all(isinstance(f, str) and f in fontes for f in fato.get("fontes", []))):
                raise ValueError("Fato do mundo sem evidência ou natureza válida")
    # Relações são direcionais e explícitas: o predicado e os argumentos
    # inteiros precisam corresponder. Sem inferência de causalidade transitiva.
    itens = {i["id"]: i for i in dados["itens"]}
    for chave in ("ligacoes", "comparacoes"):
        registros = dados.get(chave, [])
        if not isinstance(registros, list):
            raise ValueError("Relações do mundo inválidas")
        vistos = set()
        for ref in registros:
            if (not isinstance(ref, dict) or not isinstance(ref.get("origem"), str) or
                    not isinstance(ref.get("destino"), str) or ref["origem"] not in ids or
                    ref["destino"] not in ids or ref["origem"] == ref["destino"] or
                    type(ref.get("indice_fato")) is not int or
                    not 0 <= ref["indice_fato"] < len(itens[ref["origem"]]["fatos"])):
                raise ValueError("Relação sem conceitos ou fato de origem")
            par = (ref["origem"], ref["destino"])
            if chave == "ligacoes":
                verbos = ref.get("verbos")
                if (not isinstance(verbos, list) or not verbos or
                        not all(isinstance(v, str) and re.fullmatch(r"[a-z ]+", v) for v in verbos)):
                    raise ValueError("Relação sem predicado explícito")
                par += (tuple(verbos),)
            if par in vistos:
                raise ValueError("Relação duplicada")
            vistos.add(par)
    return dados


def entradas_mundo(curriculo):
    """Exemplos genéricos de conceitos; avaliações não entram no treino."""
    if curriculo is None:
        return []
    entradas = []
    for item in curriculo["itens"]:
        nomes = list(dict.fromkeys([item["nome"]] + item.get("aliases", [])))
        perguntas = [modelo.format(nome=nome) for nome in nomes for modelo in
                     ("fale sobre {nome}", "quero conversar sobre {nome}", "assunto {nome}",
                      "me explique {nome}", "quero entender {nome}", "apresente {nome}",
                      "pode falar sobre {nome}", "qual e o significado de {nome}")]
        fontes = sorted({f["fonte"] for f in item["fatos"]})
        entradas.append({
            "id": item["id"], "topico": "mundo", "origem_curriculo": "mundo",
            "perguntas": perguntas,
            "resposta": " ".join(texto_fato(f) for f in item["fatos"][:2]),
            "fontes": [curriculo["fontes"][f]["url"] for f in fontes],
        })
    return entradas


def carregar_base(caminho, curriculo=None):
    """Mesma população para o chatbot e para a rede supervisionada."""
    caminho = Path(caminho)
    base = json.loads(caminho.read_text(encoding="utf-8"))
    if curriculo is None:
        curriculo = ler_curriculo(caminho.with_name("conhecimento_mundo.json"))
    novas = entradas_mundo(curriculo)
    if {e["id"] for e in base} & {e["id"] for e in novas}:
        raise ValueError("Currículo do mundo duplicado na base editorial")
    # Dois conceitos podem ter exemplos de consulta coincidentes em um
    # catálogo expandido ("fale sobre Marte"). Preservar a intenção antiga
    # exata e remover somente a colisão de treinamento, não o conceito.
    def chave(pergunta):
        n = unicodedata.normalize("NFD", pergunta.casefold())
        n = "".join(c for c in n if unicodedata.category(c) != "Mn")
        return " ".join(re.findall(r"[a-z0-9]+", n))

    usados = {chave(p) for item in base for p in item["perguntas"]}
    for item in novas:
        validas = []
        for pergunta in item["perguntas"]:
            q = chave(pergunta)
            if q not in usados:
                usados.add(q)
                validas.append(pergunta)
        if not validas:
            raise ValueError("Conceito sem exemplos de treino não ambíguos")
        item["perguntas"] = validas
    return base + novas
