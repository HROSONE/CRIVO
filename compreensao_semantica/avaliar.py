"""Mede o classificador no conjunto semente. A régua (split 'regua') não serve para ajustar regras."""
import json
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import classificador_regras as R  # noqa: E402


def carregar():
    return [json.loads(l) for l in (AQUI / "seed.jsonl").read_text(encoding="utf-8").splitlines()]


def medir(exemplos, classificar, campo):
    certos = [classificar(e["texto"]) == e[campo] for e in exemplos]
    erros = [(e["texto"], e[campo], classificar(e["texto"])) for e, ok in zip(exemplos, certos) if not ok]
    return sum(certos) / max(1, len(certos)), erros


if __name__ == "__main__":
    dados = carregar()
    for split in ("treino", "dev", "regua"):
        sub = [e for e in dados if e["split"] == split]
        for campo, fn in (("tipo", R.tipo), ("alvo", R.alvo)):
            acc, erros = medir(sub, fn, campo)
            print(f"{split:7} {campo:5} acerto {acc:.2f} ({len(sub)} exemplos)")
            if split == "dev":
                for t, esperado, obtido in erros[:8]:
                    print(f"      erro: {t!r}  esperado={esperado}  obtido={obtido}")
