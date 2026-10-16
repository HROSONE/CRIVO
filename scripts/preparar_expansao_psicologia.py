"""Prepara os lotes V1–V8 para revisão, sem ativá-los no currículo.

Normaliza IDs e papéis, consolida conceitos com o mesmo nome e gera uma
lista de afirmações que ainda precisam de fonte específica revisada. Não
atribui fontes automaticamente: referências gerais não provam cada afirmação.

Uso:
  python scripts/preparar_expansao_psicologia.py
  python scripts/preparar_expansao_psicologia.py --saida /tmp/expansao_preparada.json
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = sorted(ROOT.glob("conhecimento_psicologia_cognitiva_neurociencia_v[0-9]*.json"))
ROLE_MAP = {
    "definicao": "definicao",
    "explicacao": "detalhe", "mecanismo": "causa", "causa": "causa",
    "aplicacao": "exemplo", "exemplo": "exemplo",
    "limite_inferencial": "limite", "limite": "limite",
    "distincao": "detalhe", "processo": "detalhe", "correcao_de_conceito": "detalhe",
    "metodo": "detalhe", "teoria": "detalhe", "evidencia": "detalhe",
    "equivoco_comum": "limite", "medida": "detalhe", "variabilidade": "limite",
    "conceito": "detalhe",
}
VALID_NATURES = {"cientifico", "psicologico", "orientacao", "filosofico", "social", "religioso"}


def normalize(text):
    text = unicodedata.normalize("NFD", text.casefold())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def make_id(name):
    slug = normalize(name).replace(" ", "_")[:56].strip("_") or "conceito"
    return "mundo_" + slug


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saida", default=str(ROOT / "conhecimento_psicologia_cognitiva_neurociencia_preparado.json"))
    args = ap.parse_args()
    if not INPUTS:
        raise SystemExit("BLOQUEADO: nenhum lote V1–Vn encontrado.")

    grouped = {}
    source_catalog = {}
    warnings = []
    counts = {"lotes": len(INPUTS), "conceitos_origem": 0, "fatos_origem": 0}
    for path in INPUTS:
        data = json.loads(path.read_text(encoding="utf-8"))
        source_catalog.update(data.get("fontes", {}))
        for item in data.get("itens", []):
            counts["conceitos_origem"] += 1
            key = normalize(item.get("nome", ""))
            if not key:
                warnings.append(f"{path.name}: conceito sem nome")
                continue
            if key not in grouped:
                grouped[key] = {"id": make_id(item["nome"]), "nome": item["nome"],
                                "area": item.get("area", "psicologia_cognitiva"),
                                "aliases": [], "fatos": [], "_origens": []}
            target = grouped[key]
            target["_origens"].append(path.name)
            if item.get("nome") != target["nome"] and item.get("nome") not in target["aliases"]:
                target["aliases"].append(item["nome"])
            for fact in item.get("fatos", []):
                counts["fatos_origem"] += 1
                text = fact.get("texto", "").strip()
                if not text:
                    warnings.append(f"{path.name}/{item.get('id')}: fato vazio")
                    continue
                fingerprint = normalize(text)
                if any(normalize(old["texto"]) == fingerprint for old in target["fatos"]):
                    continue
                old_role = fact.get("papel")
                if old_role not in ROLE_MAP:
                    warnings.append(f"{path.name}/{item.get('id')}: papel sem mapeamento: {old_role!r}")
                    continue
                if fact.get("natureza") not in VALID_NATURES:
                    warnings.append(f"{path.name}/{item.get('id')}: natureza inválida")
                    continue
                target["fatos"].append({
                    "texto": text, "fonte": "",
                    "papel": ROLE_MAP[old_role], "natureza": fact["natureza"],
                    "revisao_fonte": {"arquivo_origem": path.name,
                                      "id_conceito_origem": item.get("id"),
                                      "papel_original": old_role}
                })

    used = set()
    items = []
    for item in grouped.values():
        base = item["id"]
        candidate, n = base, 2
        while candidate in used:
            candidate = f"{base[:61]}_{n}"
            n += 1
        item["id"] = candidate
        used.add(candidate)
        definitions = [f for f in item["fatos"] if f["papel"] == "definicao"]
        if definitions:
            item["fatos"] = definitions[:1] + [f for f in item["fatos"] if f is not definitions[0]]
        else:
            warnings.append(f"{item['nome']}: sem fato marcado como definição; revisão necessária")
        if len(item["fatos"]) > 12:
            warnings.append(f"{item['nome']}: {len(item['fatos'])} fatos; excede limite de 12")
        item["aliases"] = list(dict.fromkeys(item["aliases"]))
        item["origens"] = sorted(set(item.pop("_origens")))
        items.append(item)

    output = {
        "versao": 1,
        "revisado_em": "2026-10-15",
        "status": "PREPARACAO_NAO_ATIVAR",
        "criterio": "Arquivo intermediário. Fontes por afirmação, metadados e revisão científica pendentes.",
        "fontes": {},
        "itens": items,
        "relatorio": {
            **counts,
            "conceitos_consolidados": len(items),
            "fatos_consolidados": sum(len(i["fatos"]) for i in items),
            "fatos_sem_fonte_revisada": sum(not f["fonte"] for i in items for f in i["fatos"]),
            "fontes_rascunho_referenciadas_apenas_para_revisao": sorted(source_catalog),
            "avisos": warnings,
        },
    }
    out = Path(args.saida)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Produz uma fila auditável por afirmação; nunca preenche fonte automaticamente.
    review_path = out.with_name(out.stem + "_revisao_fontes.jsonl")
    with review_path.open("w", encoding="utf-8") as review_file:
        for item in items:
            for index, fact in enumerate(item["fatos"], start=1):
                row = {
                    "id_conceito": item["id"],
                    "conceito": item["nome"],
                    "area": item["area"],
                    "indice_fato": index,
                    "afirmacao": fact["texto"],
                    "fonte": "",
                    "url_evidencia": "",
                    "trecho_ou_localizador": "",
                    "tipo_evidencia": "",
                    "revisado_por": "",
                    "status_revisao": "PENDENTE",
                    "origem": fact["revisao_fonte"],
                }
                review_file.write(json.dumps(row, ensure_ascii=False) + "\\n")
    print(f"Arquivo intermediário: {out}")
    print(f"Fila de revisão de fontes: {review_path}")
    print(f"Lotes: {counts['lotes']} | conceitos: {counts['conceitos_origem']} -> {len(items)}")
    print(f"Fatos: {counts['fatos_origem']} -> {output['relatorio']['fatos_consolidados']}")
    print(f"Fatos sem fonte revisada: {output['relatorio']['fatos_sem_fonte_revisada']}")
    print(f"Avisos: {len(warnings)}")
    print("STATUS: NÃO ATIVAR — a ausência de fontes por afirmação é bloqueio intencional.")


if __name__ == "__main__":
    main()
