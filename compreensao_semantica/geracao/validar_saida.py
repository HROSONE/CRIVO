"""Confere a saída do professor (rodar_modelo.py) e gera os exemplos candidatos.

Uso: python compreensao_semantica/geracao/validar_saida.py saida.jsonl.gz [modelo_meta.json]
- separa as mensagens (uma por linha) e tira numeração, aspas e linhas vazias;
- descarta mensagens repetidas e qualquer mensagem igual a um exemplo da semente (inclusive a régua);
- compara o rótulo do pedido com o classificador de regras: concordância vai para 'ok', divergência
  para 'revisar' (não é descartado: a revisão humana decide);
- grava exemplos_candidatos.jsonl com a origem (modelo, revisão, data, licença) quando o meta é dado.
"""
import gzip
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ))
import classificador_regras as R  # noqa: E402


def linhas_da_saida(texto):
    out = []
    for l in texto.splitlines():
        l = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", l).strip().strip('"“”\'')
        if 3 <= len(l) <= 200:
            out.append(l)
    return out


def dividir(texto_normal):
    h = int(hashlib.sha256(texto_normal.encode()).hexdigest()[:8], 16) % 100
    return "treino" if h < 80 else "dev" if h < 90 else "regua_gerada"


def principal(entrada, meta_path=None):
    origem = {}
    if meta_path:
        m = json.loads(Path(meta_path).read_text(encoding="utf-8"))
        origem = {"modelo": m.get("modelo"), "revisao": m.get("revisao"), "licenca": m.get("licenca"), "data": m.get("data")}
    with gzip.open(entrada, "rt", encoding="utf-8") as f:
        pedidos = [json.loads(l) for l in f]
    seed = [json.loads(l) for l in (RAIZ / "seed.jsonl").read_text(encoding="utf-8").splitlines()]
    proibidos = {R.normalizar(e["texto"]) for e in seed}
    vistos, saida, cont = set(), [], Counter()
    for p in pedidos:
        tipo, alvo, _ = p["id"].split("__")
        for texto in linhas_da_saida(p["texto"]):
            n = R.normalizar(texto)
            if n in proibidos:
                cont["igual_a_seed_ou_regua"] += 1
                continue
            if n in vistos:
                cont["repetida"] += 1
                continue
            vistos.add(n)
            status = "ok" if (R.tipo(texto) == tipo and R.alvo(texto) == alvo) else "revisar"
            cont[status] += 1
            saida.append({"texto": texto, "tipo": tipo, "alvo": alvo, "status": status,
                          "split": dividir(n), "origem": dict(origem, tipo_de_origem="professor_licenca_aberta")})
    dest = AQUI / "exemplos_candidatos.jsonl"
    dest.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in saida) + "\n", encoding="utf-8")
    print("resumo:", dict(cont), "| total gravado:", len(saida), "->", dest)
    por_tipo = Counter(x["tipo"] for x in saida)
    print("por tipo:", dict(por_tipo))


if __name__ == "__main__":
    principal(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
