"""Controle fixado antes das alterações; reserva só após a resposta única."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
sys.path.insert(0, str(RAIZ))
from crivo import Crivo
from composicao_textual import normalizar
from interpretacao_estruturas import executar
from verificacao_codigo import iguais


def avaliar(grupo):
    fonte = PASTA / "controle_prospectivo.json"
    digest = hashlib.sha256(fonte.read_bytes()).hexdigest()
    assert digest == (PASTA / "controle_prospectivo.sha256").read_text().split()[0]
    casos = json.loads(fonte.read_text())[grupo]
    detalhes = []
    for c in casos:
        bot = Crivo()
        if grupo == "programacao":
            ident, texto = bot.responder(json.dumps(dict(acao="gerar", desenvolvimento=c["desenvolvimento"])))
            ultimo = copy.deepcopy(bot.motor_codigo.ultimo or {})
            corpo = ultimo.get("corpo")
            certos = []
            for r in c["reservados"]:
                try:
                    e = executar(corpo, copy.deepcopy(r["entrada"])) if corpo else None
                    certos.append(bool(e) and not e.get("erro") and iguais(e["resultado"], r["saida"])
                                  and iguais(e["estado"]["entrada"], r["entrada"]))
                except ValueError:
                    certos.append(False)
            passou = bool(ultimo.get("atende_desenvolvimento")) and all(certos)
            detalhes.append(dict(id=c["id"], passou=passou, resposta=texto, response_id=ident,
                                 execucao=ultimo, reservados_corretos=sum(certos), reservados_total=len(certos)))
        else:
            respostas = []
            for t in c["turnos"]:
                ident, texto = bot.responder(t)
                respostas.append(dict(pergunta=t, resposta=texto, response_id=ident))
            n = normalizar(texto)
            passou = all(x in n for x in c["presentes"]) and not any(x in n for x in c["ausentes"])
            detalhes.append(dict(id=c["id"], passou=passou, turnos=respostas))
    return dict(grupo=grupo, casos=len(casos), acertos=sum(x["passou"] for x in detalhes),
                controle_sha256=digest, detalhes=detalhes)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("grupo", choices=("programacao", "memoria"))
    p.add_argument("--saida", required=True, type=Path)
    args = p.parse_args()
    if args.saida.exists():
        raise SystemExit("Use uma saída nova.")
    inicio = time.monotonic()
    r = avaliar(args.grupo)
    r["tempo_segundos"] = round(time.monotonic() - inicio, 3)
    r["fontes_sha256"] = {n: hashlib.sha256((RAIZ / n).read_bytes()).hexdigest()
                           for n in ("programacao_chat.py", "dialogo_aberto.py", "linguagem_conversa.py")}
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k:v for k,v in r.items() if k != "detalhes"}), flush=True)


if __name__ == "__main__":
    main()
