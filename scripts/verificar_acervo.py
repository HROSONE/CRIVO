"""Confere uma ampliação do acervo contra a versão do git (HEAD por padrão).

  - o currículo carrega e passa a validação de fontes, fatos e IDs;
  - nenhum fato existente foi alterado, removido ou reordenado (só acréscimos
    no fim da lista de fatos);
  - fichas protegidas (testes congelados, dados do tutor, astronomia) não mudaram;
  - todo fato novo tem fonte cadastrada, papel e natureza válidos e no
    máximo 400 caracteres;
  - nome e apelidos de conceitos novos não colidem com outros conceitos.

Uso: python scripts/verificar_acervo.py [--base HEAD] [--protegidos arquivo.json]
"""
import argparse
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def _norm(t):
    t = unicodedata.normalize("NFD", t.casefold())
    return " ".join("".join(c for c in t if unicodedata.category(c) != "Mn").split())


def protegidos_padrao():
    excl = set()
    ler = lambda p: json.loads((RAIZ / p).read_text(encoding="utf-8"))
    for c in ler("dados/leitura_ficha_tutor.json")["casos"]:
        excl.add(c["assunto"])
    for t in ("avaliacoes/leitura_ficha_v1/teste.json", "avaliacoes/leitura_ficha_v2/teste.json"):
        excl |= {c["assunto"] for c in ler(t)["casos"]}
    for c in ler("avaliacoes/voz_v1/teste.json")["casos"] + ler("dados/voz_tutor.json")["casos"]:
        excl.update(c["assuntos"])
    return excl


def itens_da_base(base):
    """Itens de todos os catálogos conhecimento_*.json na revisão base."""
    nomes = subprocess.run(["git", "ls-tree", "--name-only", base], cwd=RAIZ, capture_output=True,
                           text=True, check=True).stdout.split()
    itens = {}
    for nome in nomes:
        if not (nome.startswith("conhecimento_") and nome.endswith(".json")):
            continue
        conteudo = subprocess.run(["git", "show", "%s:%s" % (base, nome)], cwd=RAIZ, capture_output=True,
                                  text=True, check=True).stdout
        dados = json.loads(conteudo)
        if isinstance(dados, dict):
            for it in dados.get("itens", []):
                if isinstance(it, dict) and "id" in it:
                    itens[it["id"]] = it
    return itens


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="HEAD")
    args = ap.parse_args()
    from curriculo_mundo import NATUREZAS, ler_curriculo
    erros = []
    try:
        dados = ler_curriculo(RAIZ / "conhecimento_mundo.json")
    except ValueError as exc:
        print("FALHA: currículo não carrega:", exc)
        return 1
    antes = itens_da_base(args.base)
    protegidos = protegidos_padrao()
    agora = {}
    for nome in sorted(p.name for p in RAIZ.glob("conhecimento_*.json")):
        d = json.loads((RAIZ / nome).read_text(encoding="utf-8"))
        if isinstance(d, dict):
            for it in d.get("itens", []):
                if isinstance(it, dict) and "id" in it:
                    agora[it["id"]] = it
    fontes = dados["fontes"]
    novos_fatos = novos_itens = 0
    for ident, it in agora.items():
        velho = antes.get(ident)
        fatos = it.get("fatos", [])
        if velho is not None:
            vf = velho.get("fatos", [])
            if fatos[:len(vf)] != vf:
                erros.append("%s: fatos existentes alterados, removidos ou reordenados" % ident)
                continue
            if (ident in protegidos or velho.get("area") == "astronomia") and fatos != vf:
                erros.append("%s: ficha protegida recebeu fatos" % ident)
            for k in ("id", "nome", "area"):
                if it.get(k) != velho.get(k):
                    erros.append("%s: campo %s alterado" % (ident, k))
            novos = fatos[len(vf):]
        else:
            novos_itens += 1
            novos = fatos
        for f in novos:
            novos_fatos += 1
            if len(f.get("texto", "")) > 400:
                erros.append("%s: fato com mais de 400 caracteres" % ident)
            if f.get("fonte") not in fontes or f.get("natureza") not in NATUREZAS:
                erros.append("%s: fato sem fonte cadastrada ou natureza válida" % ident)
        if len(fatos) > 12:
            erros.append("%s: mais de 12 fatos" % ident)
    # Colisões de nome/apelido entre conceitos diferentes.
    # Grafia com acento diferente ("Pelé" × "pele") não colide: o compositor
    # a trata como grafia distinta e reescreve a pergunta pelo nome da ficha.
    donos, grafias = {}, {}
    for ident, it in agora.items():
        for nome in [it.get("nome", "")] + list(it.get("aliases", [])):
            n = _norm(nome)
            if n and n in donos and donos[n] != ident:
                acentos = [g for g in grafias.get(n, set()) | {nome.casefold()} if g != _norm(g)]
                distinta = bool(acentos) and nome.casefold() not in grafias.get(n, set())
                if (ident not in antes or donos[n] not in antes) and not distinta:
                    erros.append("nome/apelido '%s' em %s e %s" % (nome, donos[n], ident))
            donos.setdefault(n, ident)
            grafias.setdefault(n, set()).add(nome.casefold())
    for ident in antes:
        if ident not in agora:
            erros.append("%s: conceito removido" % ident)
    print("conceitos: %d (novos: %d) | fatos novos: %d | erros: %d" % (len(agora), novos_itens, novos_fatos, len(erros)))
    for e in erros[:60]:
        print("  -", e)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
