"""Mede a síntese de funções Python (sintese_python.py) nas tarefas congeladas.

Uso: python avaliar.py [--parte desenvolvimento|blind] [--saida arquivo.json]

Três modos, na mesma busca:
- direto: responde a menor função que bate com os exemplos, mesmo se houver outra possível;
- cauteloso: se houver duas funções que discordam numa entrada nova, não responde;
- pergunta: nesse caso pergunta a saída daquela entrada (a referência responde, como a pessoa
  responderia) e busca de novo, até 3 perguntas.

Para cada tarefa: certa (passa em todas as entradas ocultas), errada (bate com os exemplos e erra
alguma oculta) ou sem resposta. A conta que mais importa é a de erradas: o chat só deve mostrar
função que está certa.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1]))
sys.path.insert(0, str(AQUI))

import sintese_python as sp  # noqa: E402
import tarefas  # noqa: E402

MAX_PERGUNTAS = 3


def certa(expr, ref, ocultas):
    for x in ocultas:
        try:
            if not sp.iguais(sp.avaliar(expr, {"entrada": x}), ref(x)):
                return False
        except Exception:
            return False
    return True


def rodar(tarefa):
    nome, descricao, ref, dev, ocultas = tarefa
    exemplos = [{"entrada": x, "saida": ref(x)} for x in dev]
    t0 = time.time()
    r = sp.sintetizar(exemplos)
    linha = {"nome": nome, "descricao": descricao}
    if r["programa"] is None:
        linha.update(direto="sem_resposta", cauteloso="sem_resposta")
    else:
        ok = certa(r["expressao"], ref, ocultas)
        linha["direto"] = "certa" if ok else "errada"
        linha["cauteloso"] = "sem_resposta" if r["ambigua"] else linha["direto"]
        linha["programa_direto"] = r["programa"]
    perguntas = 0
    while r["programa"] is not None and r["pergunta"] and perguntas < MAX_PERGUNTAS:
        p = r["pergunta"]["entrada"]
        try:
            novo = {"entrada": p, "saida": sp.conferir(ref(p))}
        except Exception:
            break  # a referência nem aceita essa entrada; a pessoa diria "não vale"
        exemplos.append(novo)
        perguntas += 1
        r = sp.sintetizar(exemplos)
    if r["programa"] is None:
        linha["pergunta"] = "sem_resposta"
    elif r["ambigua"]:
        linha["pergunta"] = "sem_resposta"
    else:
        linha["pergunta"] = "certa" if certa(r["expressao"], ref, ocultas) else "errada"
        linha["programa"] = r["programa"]
    linha.update(perguntas=perguntas, segundos=round(time.time() - t0, 2))
    return linha


def resumo(linhas):
    out = {}
    for modo in ("direto", "cauteloso", "pergunta"):
        c = {k: sum(l[modo] == k for l in linhas) for k in ("certa", "errada", "sem_resposta")}
        respondidas = c["certa"] + c["errada"]
        c["taxa_certa"] = round(c["certa"] / len(linhas), 3)
        c["erradas_entre_respondidas"] = round(c["errada"] / respondidas, 3) if respondidas else 0.0
        out[modo] = c
    out["perguntas_media"] = round(sum(l["perguntas"] for l in linhas) / len(linhas), 2)
    return out


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parte", default="desenvolvimento", choices=("desenvolvimento", "blind"))
    ap.add_argument("--saida")
    a = ap.parse_args()
    lista = tarefas.DESENVOLVIMENTO if a.parte == "desenvolvimento" else tarefas.BLIND
    linhas = []
    for t in lista:
        l = rodar(t)
        linhas.append(l)
        print(f"{l['nome']:24s} direto={l['direto']:12s} cauteloso={l['cauteloso']:12s} "
              f"pergunta={l['pergunta']:12s} perguntas={l['perguntas']} {l['segundos']}s", flush=True)
    r = resumo(linhas)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if a.saida:
        sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
        Path(a.saida).write_text(json.dumps({
            "parte": a.parte, "tarefas_sha256": sha(AQUI / "tarefas.py"),
            "motor_sha256": sha(AQUI.parents[1] / "sintese_python.py"), "resumo": r, "linhas": linhas},
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    principal()
