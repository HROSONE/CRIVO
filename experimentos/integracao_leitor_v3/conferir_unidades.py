"""Confere a equivalência dos predicados nos controles, sem expor casos."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
sys.path[:0] = [str(RAIZ), str(RAIZ / "scripts")]
from avaliar_leitura_ficha import CONJUNTOS
from crivo import Crivo
from leitura_ficha import TRACOS
from verificacao_campo_factual import verificar_campo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    if args.saida.exists():
        raise SystemExit("Use uma saída nova para preservar o relatório anterior.")
    antigo = PASTA / "historico/verificacao_campo_antes_unidades.py"
    spec = importlib.util.spec_from_file_location("verificador_anterior", antigo)
    anterior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(anterior)
    conjuntos = dict(CONJUNTOS, prospectivo=PASTA / "prospectivo.json",
                     prospectivo_campo=PASTA / "prospectivo_campo.json")
    bot = Crivo(usar_geracao=False)
    resultado = {
        "criterio": "Comparar só predicados; não inspecionar erros ou respostas individuais dos controles.",
        "fontes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                   (antigo, RAIZ / "verificacao_campo_factual.py")},
        "conjuntos": {},
    }
    for nome in ("teste", "teste_v2", "prospectivo", "prospectivo_campo"):
        casos = json.loads(conjuntos[nome].read_text(encoding="utf-8"))["casos"]
        pares = alterados = 0
        for caso in casos:
            quadro = bot.compositor.interpretar(caso["pergunta"])
            item = bot.compositor.itens[caso["assunto"]]
            for prob, i, cobertura, tipo, x in bot.leitura_ficha.candidatos(quadro, caso["assunto"]):
                argumentos = (caso["pergunta"], item["fatos"][i]["texto"], dict(zip(TRACOS, x)), item.get("area"))
                pares += 1
                alterados += int(anterior.verificar_campo(*argumentos) != verificar_campo(*argumentos))
        resultado["conjuntos"][nome] = dict(perguntas=len(casos), pares_pergunta_fato=pares,
                                            predicados_alterados=alterados)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False))


if __name__ == "__main__":
    main()
