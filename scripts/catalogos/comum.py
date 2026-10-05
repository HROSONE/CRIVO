"""Utilitários para montar catálogos temáticos no esquema de curriculo_mundo.

Uso: ``cd scripts/catalogos && python historia.py ../../conhecimento_historia.json``.
"""
import json
import re

VERIFICADO = "2026-10-05"
ESCOPO_CC = ("Síntese própria em português de conteúdo consolidado; sem reprodução de trechos, "
             "figuras ou exercícios da obra. Verificação por catálogo e licença.")
ESCOPO_REF = ("Somente referência bibliográfica de síntese factual autoral; não reproduz textos, imagens, "
              "tabelas ou dados da obra. Não implica autorização ou endosso institucional.")


def openstax(chave, titulo, slug, credito):
    return chave, {
        "titulo": titulo, "url": "https://openstax.org/details/books/" + slug,
        "tipo": "institucional_cientifica", "ano": 2026, "ano_tipo": "consulta",
        "credito": credito, "reutilizacao": "CC-BY-4.0",
        "direitos_url": "https://creativecommons.org/licenses/by/4.0/",
        "verificado_em": VERIFICADO, "escopo_uso": ESCOPO_CC,
    }


def referencia(chave, titulo, url, credito, direitos_url):
    return chave, {
        "titulo": titulo, "url": url, "tipo": "institucional_cientifica", "ano": 2026,
        "ano_tipo": "consulta", "credito": credito, "reutilizacao": "somente_referencia",
        "reproducao_autorizada": False, "direitos_url": direitos_url,
        "verificado_em": VERIFICADO, "escopo_uso": ESCOPO_REF,
    }


def dominio_publico(chave, titulo, url, credito, direitos_url):
    return chave, {
        "titulo": titulo, "url": url, "tipo": "institucional_cientifica", "ano": 2026,
        "ano_tipo": "consulta", "credito": credito, "reutilizacao": "dominio_publico",
        "direitos_url": direitos_url, "verificado_em": VERIFICADO,
        "escopo_uso": "Síntese própria em português dos fatos; sem imagens, logotipos ou indicação de endosso.",
    }


def conceito(ident, nome, area, fonte, natureza, definicao, *detalhes, aliases=(), papeis=None):
    """Primeiro fato é a definição; os demais são detalhes (ou papéis indicados)."""
    fatos = [{"texto": definicao, "fonte": fonte, "papel": "definicao", "natureza": natureza}]
    for i, texto in enumerate(detalhes):
        papel = (papeis or {}).get(i, "detalhe")
        fatos.append({"texto": texto, "fonte": fonte, "papel": papel, "natureza": natureza})
    assert re.fullmatch(r"mundo_[a-z0-9_]{1,56}", ident), ident
    return {"id": ident, "nome": nome, "area": area, "aliases": list(aliases), "fatos": fatos}


def salvar(caminho, criterio, fontes, itens, ligacoes=(), comparacoes=()):
    dados = {"versao": 1, "revisado_em": VERIFICADO, "criterio": criterio,
             "fontes": dict(fontes), "itens": list(itens),
             "ligacoes": list(ligacoes), "comparacoes": list(comparacoes)}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return dados


def fonte_existente(chave, arquivo="conhecimento_biologia.json"):
    """Reaproveita o registro exato de uma fonte já presente no acervo."""
    import os
    raiz = os.environ.get("CRIVO_RAIZ") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    with open(os.path.join(raiz, arquivo), encoding="utf-8") as f:
        return chave, json.load(f)["fontes"][chave]
