"""Extrai aprofundamento_<nome>.json: o que o catálogo conhecimento_<nome>.json
tem a mais que o gerador <nome>.py (fontes novas e fatos acrescentados no fim
das fichas). Depois disso, o gerador volta a reproduzir o catálogo.

Uso: cd scripts/catalogos && python extrair_aprofundamento.py historia [geografia ...]
"""
import json
import os
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..", "..")


def extrair(nome):
    alvo = os.path.join(AQUI, "aprofundamento_%s.json" % nome)
    guardado = None
    if os.path.exists(alvo):
        guardado = open(alvo, encoding="utf-8").read()
        os.remove(alvo)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            destino = os.path.join(tmp, "base.json")
            subprocess.run([sys.executable, "%s.py" % nome, destino], cwd=AQUI, check=True)
            base = json.load(open(destino, encoding="utf-8"))
    except Exception:
        if guardado is not None:
            open(alvo, "w", encoding="utf-8").write(guardado)
        raise
    atual = json.load(open(os.path.join(RAIZ, "conhecimento_%s.json" % nome), encoding="utf-8"))
    for k, v in base["fontes"].items():
        if atual["fontes"].get(k) != v:
            raise SystemExit("%s: fonte %s alterada no catálogo" % (nome, k))
    fontes = {k: v for k, v in atual["fontes"].items() if k not in base["fontes"]}
    bitens = {it["id"]: it for it in base["itens"]}
    fatos = {}
    for it in atual["itens"]:
        b = bitens.get(it["id"])
        if b is None:
            raise SystemExit("%s: conceito %s não existe no gerador" % (nome, it["id"]))
        if it["fatos"][:len(b["fatos"])] != b["fatos"] or {k: v for k, v in it.items() if k != "fatos"} != \
                {k: v for k, v in b.items() if k != "fatos"}:
            raise SystemExit("%s: %s difere do gerador além de fatos acrescentados" % (nome, it["id"]))
        if len(it["fatos"]) > len(b["fatos"]):
            fatos[it["id"]] = it["fatos"][len(b["fatos"]):]
    for chave in ("criterio", "ligacoes", "comparacoes"):
        if atual.get(chave) != base.get(chave):
            raise SystemExit("%s: campo %s difere do gerador" % (nome, chave))
    dados = {"versao": 1, "revisado_em": "2026-10-06",
             "uso": "Fatos de aprofundamento acrescentados no fim das fichas por comum.aprofundar; fontes novas que eles citam.",
             "fontes": fontes, "fatos": fatos}
    with open(alvo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(nome, "fontes novas:", len(fontes), "| fichas:", len(fatos), "| fatos:", sum(map(len, fatos.values())))


if __name__ == "__main__":
    for n in sys.argv[1:]:
        extrair(n)
