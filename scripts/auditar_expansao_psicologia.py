"""Audita os lotes rascunho de psicologia/neurociência contra o contrato real do CRIVO.

Uso: python scripts/auditar_expansao_psicologia.py
Não atribui fontes nem converte papéis automaticamente. A integração é bloqueada
enquanto houver fatos sem fonte verificável ou incompatibilidades de esquema.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from curriculo_mundo import NATUREZAS, REUTILIZACOES

FILES = sorted(ROOT.glob("conhecimento_psicologia_cognitiva_neurociencia_v*.json"))
VALID_ROLES = {"definicao", "detalhe", "causa", "exemplo", "limite"}
VALID_SOURCE_TYPES = {
    "institucional_cientifica", "artigo_cientifico", "catalogo_tecnico",
    "institucional_religiosa",
}


def norm(value):
    value = unicodedata.normalize("NFD", value.casefold())
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def main():
    if not FILES:
        print("BLOQUEIO: nenhum lote V1–Vn encontrado.")
        return 2

    total_items = total_facts = total_sources = 0
    seen_names, seen_ids = {}, {}
    duplicate_names, duplicate_ids, issues = [], [], []
    role_counts = {}
    missing_fact_source = 0

    for path in FILES:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(f"{path.name}: JSON inválido: {exc}")
            continue
        if not isinstance(data, dict) or data.get("versao") != 1:
            issues.append(f"{path.name}: envelope/versão inválidos")
            continue

        sources, items = data.get("fontes", {}), data.get("itens", [])
        if not isinstance(sources, dict) or not isinstance(items, list):
            issues.append(f"{path.name}: fontes/itens com tipo inválido")
            continue

        total_sources += len(sources)
        print(f"{path.name}: {len(items)} conceitos, "
              f"{sum(len(x.get('fatos', [])) for x in items if isinstance(x, dict))} fatos, "
              f"{len(sources)} entradas de fonte")
        total_items += len(items)

        for source_id, source in sources.items():
            required = ("titulo", "url", "tipo", "ano", "ano_tipo", "reutilizacao",
                        "direitos_url", "credito", "verificado_em", "escopo_uso")
            if not isinstance(source, dict):
                issues.append(f"{path.name}: fonte {source_id!r} não é objeto")
                continue
            missing = [key for key in required if key not in source]
            if missing:
                issues.append(f"{path.name}: fonte {source_id!r} sem campos: {', '.join(missing)}")
            if source.get("tipo") not in VALID_SOURCE_TYPES:
                issues.append(f"{path.name}: fonte {source_id!r} tem tipo não aceito")
            if source.get("reutilizacao") not in REUTILIZACOES:
                issues.append(f"{path.name}: fonte {source_id!r} tem reutilização não aceita")
            for key in ("url", "direitos_url"):
                if key in source and (not isinstance(source[key], str) or not source[key].startswith("https://")):
                    issues.append(f"{path.name}: fonte {source_id!r} tem {key} inválida")
            if "ano" in source and (type(source["ano"]) is not int or not 1900 <= source["ano"] <= 2100):
                issues.append(f"{path.name}: fonte {source_id!r} tem ano inválido")
            if source.get("ano_tipo") not in ("publicacao", "consulta"):
                issues.append(f"{path.name}: fonte {source_id!r} tem ano_tipo inválido")
            if source.get("reutilizacao") == "somente_referencia" and source.get("reproducao_autorizada") is not False:
                issues.append(f"{path.name}: fonte {source_id!r} presume reprodução sem autorização explícita")

        for item in items:
            if not isinstance(item, dict):
                issues.append(f"{path.name}: item não é objeto")
                continue
            ident, name = item.get("id"), item.get("nome", "")
            if not isinstance(ident, str) or not re.fullmatch(r"mundo_[a-z0-9_]{1,56}", ident):
                issues.append(f"{path.name}: ID incompatível: {ident!r}")
            if ident in seen_ids:
                duplicate_ids.append((ident, seen_ids[ident], path.name))
            else:
                seen_ids[ident] = path.name
            name_key = norm(name) if isinstance(name, str) else ""
            if name_key and name_key in seen_names:
                duplicate_names.append((name, seen_names[name_key], path.name))
            elif name_key:
                seen_names[name_key] = path.name

            facts = item.get("fatos", [])
            if not isinstance(facts, list) or not facts:
                issues.append(f"{path.name}: {ident}: sem lista de fatos")
                continue
            if len(facts) > 12:
                issues.append(f"{path.name}: {ident}: mais de 12 fatos")
            if not isinstance(facts[0], dict) or facts[0].get("papel") != "definicao":
                issues.append(f"{path.name}: {ident}: primeiro fato não é definição")

            for index, fact in enumerate(facts):
                if not isinstance(fact, dict):
                    issues.append(f"{path.name}: {ident}[{index}]: fato não é objeto")
                    continue
                total_facts += 1
                role = fact.get("papel")
                role_counts[role] = role_counts.get(role, 0) + 1
                if role not in VALID_ROLES:
                    issues.append(f"{path.name}: {ident}[{index}]: papel incompatível: {role!r}")
                if fact.get("natureza") not in NATUREZAS:
                    issues.append(f"{path.name}: {ident}[{index}]: natureza incompatível com curriculo_mundo.NATUREZAS")
                text = fact.get("texto")
                if not isinstance(text, str) or not text.strip():
                    issues.append(f"{path.name}: {ident}[{index}]: texto vazio/inválido")
                elif len(text) > 400:
                    issues.append(f"{path.name}: {ident}[{index}]: texto >400 caracteres")
                source_id = fact.get("fonte")
                if not isinstance(source_id, str) or source_id not in sources:
                    missing_fact_source += 1
                    issues.append(f"{path.name}: {ident}[{index}]: sem fonte específica cadastrada")

    print("\\nRESUMO")
    print(f"Arquivos: {len(FILES)}")
    print(f"Conceitos: {total_items}")
    print(f"Fatos: {total_facts}")
    print(f"Entradas de fonte somadas (podem repetir URLs): {total_sources}")
    print(f"Fatos sem fonte associada: {missing_fact_source}")
    print(f"Papéis encontrados: {role_counts}")
    print(f"Nomes duplicados entre lotes: {len(duplicate_names)}")
    for name, old_file, new_file in duplicate_names:
        print(f"  DUPLICADO: {name!r} — {old_file} / {new_file}")
    print(f"IDs duplicados entre lotes: {len(duplicate_ids)}")
    for ident, old_file, new_file in duplicate_ids:
        print(f"  ID REPETIDO: {ident!r} — {old_file} / {new_file}")
    print(f"Problemas de compatibilidade encontrados: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")

    if issues or duplicate_names or duplicate_ids:
        print("\\nSTATUS: BLOQUEADO — NÃO INTEGRAR AO CURRÍCULO ATIVO")
        return 1
    print("\\nSTATUS: COMPATIBILIDADE ESTRUTURAL APROVADA; AINDA EXIGE REVISÃO CIENTÍFICA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
