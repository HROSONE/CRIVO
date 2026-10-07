"""Consolidação ("sono"): junta o que o CRIVO aprendeu em várias conversas.

Uso: python scripts/consolidar_aprendizados.py memoria1.json [memoria2.json ...]

Cada arquivo é uma memória exportada pelo site (a que fica no navegador de
quem optou por ela) ou por Crivo.exportar_memoria(). Saída:
dados/aprendizados.json, com
  - pares: pergunta → (ficha, fato), com quantas vezes foi confirmado (+1)
    ou corrigido (-1). Pares com saldo positivo viram exemplos dos treinos
    (busca aprendida, codificador de sentido);
  - lacunas: perguntas que o CRIVO não soube, com quantas vezes apareceram e
    as respostas que os usuários contaram. As respostas dos usuários NÃO viram
    fatos: são pistas para escrever fichas, conferidas em fonte.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
SAIDA = RAIZ / "dados" / "aprendizados.json"


def _chave(texto):
    from composicao_textual import normalizar
    return " ".join(normalizar(texto).split())


def consolidar(memorias, anterior=None):
    pares = {(_chave(p["pergunta"]), p["assunto"], p["fato"]): dict(p) for p in (anterior or {}).get("pares", [])}
    lacunas = {_chave(l["pergunta"]): dict(l) for l in (anterior or {}).get("lacunas", [])}
    for memoria in memorias:
        for a in memoria.get("aprendizados", []):
            chave = (_chave(a["pergunta"]), a["assunto"], a["fato"])
            p = pares.setdefault(chave, {"pergunta": a["pergunta"], "assunto": a["assunto"], "fato": a["fato"],
                                         "saldo": 0})
            p["saldo"] += a.get("sinal", 1)
        for l in memoria.get("lacunas", []):
            item = lacunas.setdefault(_chave(l["pergunta"]), {"pergunta": l["pergunta"], "vezes": 0,
                                                             "respostas_usuario": []})
            item["vezes"] += 1
            r = l.get("resposta_usuario")
            if r and r not in item["respostas_usuario"]:
                item["respostas_usuario"].append(r)
    return {"versao": 1,
            "descricao": "Aprendizados consolidados das conversas (scripts/consolidar_aprendizados.py). "
                         "Respostas de usuários são pistas, não fatos.",
            "pares": sorted(pares.values(), key=lambda p: (-p["saldo"], p["pergunta"])),
            "lacunas": sorted(lacunas.values(), key=lambda l: (-l["vezes"], l["pergunta"]))}


def pares_positivos(caminho=SAIDA):
    """[(pergunta, assunto, fato)] com saldo positivo, para os treinos."""
    if not Path(caminho).exists():
        return []
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return [(p["pergunta"], p["assunto"], p["fato"]) for p in dados.get("pares", []) if p.get("saldo", 0) > 0]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    anterior = json.loads(SAIDA.read_text(encoding="utf-8")) if SAIDA.exists() else None
    memorias = [json.loads(Path(c).read_text(encoding="utf-8")) for c in sys.argv[1:]]
    dados = consolidar(memorias, anterior)
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("pares: %d (positivos: %d) | lacunas: %d" % (
        len(dados["pares"]), sum(p["saldo"] > 0 for p in dados["pares"]), len(dados["lacunas"])))
    for l in dados["lacunas"][:10]:
        print("  %dx %s" % (l["vezes"], l["pergunta"]))


if __name__ == "__main__":
    main()
