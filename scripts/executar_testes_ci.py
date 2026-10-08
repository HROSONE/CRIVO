"""Distribui a descoberta completa entre jobs, sem excluir testes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
GRUPOS = ("composicao", "treino", "regressoes-a", "regressoes-b")


def grupo_do_teste(teste):
    modulo = teste.__class__.__module__
    # Estes dois módulos concentram o maior custo da descoberta completa.
    if modulo == "testes_composicao_textual":
        return "composicao"
    if modulo == "testes_treino_experimental_96":
        return "treino"
    digest = hashlib.sha256(modulo.encode("utf-8")).digest()
    return "regressoes-a" if digest[0] % 2 == 0 else "regressoes-b"


def testes_individuais(suite):
    for teste in suite:
        if isinstance(teste, unittest.TestSuite):
            yield from testes_individuais(teste)
        else:
            yield teste


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grupo", choices=GRUPOS, required=True)
    parser.add_argument("--listar", action="store_true")
    parser.add_argument("--modulos", nargs="+", help="Suíte explícita de outro workflow")
    args = parser.parse_args()
    # O mesmo padrão da suíte anterior inclui automaticamente novos módulos.
    if args.modulos:
        suite = unittest.defaultTestLoader.loadTestsFromNames(args.modulos)
    else:
        suite = unittest.defaultTestLoader.discover(str(RAIZ), pattern="testes*.py")
    testes = [t for t in testes_individuais(suite) if grupo_do_teste(t) == args.grupo]
    if args.listar:
        print(json.dumps([t.id() for t in testes], ensure_ascii=False))
        return 0
    print("Grupo %s: %d testes" % (args.grupo, len(testes)), flush=True)
    resultado = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(testes))
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
