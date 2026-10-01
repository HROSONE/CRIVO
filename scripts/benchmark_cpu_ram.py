"""Mede CPU/RAM e crescimento do classificador sem alterar producao.

python scripts/benchmark_cpu_ram.py --ocultos 48 128 256 512 --repeticoes 30
Usa apenas biblioteca padrao; resultados sao do computador onde executado.
"""
import argparse
import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rede_neural import RedeCrivo


def medir(ocultos, classes=193, dimensao=512, repeticoes=30):
    rotulos = ["classe_%d" % i for i in range(classes)]
    tracemalloc.start()
    inicio = time.perf_counter()
    rede = RedeCrivo(rotulos, dimensao=dimensao, ocultos=ocultos, modo="caracteres")
    inicializacao_ms = (time.perf_counter() - inicio) * 1000
    memoria_atual, memoria_pico = tracemalloc.get_traced_memory()
    amostras = ["Por que as estrelas brilham?", "Qual a diferenca entre Terra e Jupiter?",
                "Como funciona a gravidade?", "Explique a origem do sistema solar"]
    for texto in amostras:
        rede.prever(texto)
    tempos = []
    for i in range(repeticoes):
        t = time.perf_counter()
        rede.prever(amostras[i % len(amostras)])
        tempos.append((time.perf_counter() - t) * 1000)
    _, pico_final = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    parametros = dimensao * ocultos + ocultos + ocultos * classes + classes
    return {"ocultos": ocultos, "classes": classes, "dimensao": dimensao,
            "parametros": parametros, "peso_teorico_float32_mib": round(parametros * 4 / 1048576, 3),
            "inicializacao_ms": round(inicializacao_ms, 2),
            "pico_python_tracemalloc_mib": round(pico_final / 1048576, 2),
            "latencia_mediana_ms": round(statistics.median(tempos), 2),
            "latencia_p95_ms": round(sorted(tempos)[max(0, int(len(tempos)*0.95)-1)], 2),
            "nota": "tracemalloc mede alocacoes Python, nao o RSS total do processo; rede nao treinada"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocultos", type=int, nargs="+", default=[48, 128, 256, 512])
    parser.add_argument("--repeticoes", type=int, default=30)
    parser.add_argument("--saida", default="")
    args = parser.parse_args()
    if args.repeticoes < 5 or any(n < 1 or n > 4096 for n in args.ocultos):
        parser.error("repeticoes >= 5 e 1 <= ocultos <= 4096")
    resultados = {"ambiente": {"python": sys.version.split()[0], "plataforma": sys.platform},
                  "configuracoes": [medir(n, repeticoes=args.repeticoes) for n in args.ocultos]}
    payload = json.dumps(resultados, ensure_ascii=False, indent=2)
    if args.saida:
        Path(args.saida).write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
