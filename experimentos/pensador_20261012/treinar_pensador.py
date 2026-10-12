"""Treina e avalia o pensador. Roda em CPU (piloto) ou GPU (Colab).

python experimentos/pensador_20261012/treinar_pensador.py --saida /tmp/pensador --passos 20000

O treino é gerado com semente própria e exclui todo problema dos conjuntos
congelados. A escolha do checkpoint usa só o dev; os conjuntos cegos são
avaliados uma vez, no fim. Os pesos nunca vão para o chat por este script:
o resultado grava ativo_no_chat=false.
"""
import argparse
import hashlib
import json
import math
import random
import sys
import time
from multiprocessing import Pool
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import torch  # noqa: E402

import gerar_pensador as G  # noqa: E402
import pensador as P  # noqa: E402

GATES = {"blind_iid": 0.95, "ood_profundidade": 0.80, "ood_tamanho": 0.80}


def _gerar_parte(args):
    semente, quantidade, proibidos = args
    rng = random.Random(semente)
    saida = []
    for p in G.amostrar(rng, G.TREINO, None):
        if G.assinatura(p) in proibidos:
            continue
        saida.append(p)
        if len(saida) >= quantidade:
            break
    return saida


def gerar_treino(n, semente, proibidos, processos=4):
    partes = max(1, processos * 4)
    tarefas = [(semente * 1000 + i, math.ceil(n / partes), proibidos) for i in range(partes)]
    with Pool(processos) as pool:
        blocos = pool.map(_gerar_parte, tarefas)
    return [p for b in blocos for p in b][:n]


def avaliar(problemas, previsoes):
    n = len(problemas)
    m = {"n": n, "status_acc": 0, "exato": 0, "afirmacoes_erradas_brutas": 0, "afirmacoes_erradas_conferidas": 0,
         "cobertura_conferida": 0, "pergunta_ok": 0, "politica_erros": 0, "politica_cobertura": 0}
    com_conclusao = sum(p["status"] != "indeterminado" for p in problemas)
    indet_ok = indet_n = 0
    por_status = {s: [0, 0] for s in G.STATUS}
    for p, q in zip(problemas, previsoes):
        certo = q["status"] == p["status"]
        m["status_acc"] += certo
        por_status[p["status"]][1] += 1
        conferida = q["status"] != "indeterminado" and G.conferir_prova(p, q["status"], q["prova"])
        if q["status"] in ("sustentado", "refutado") and not certo:
            m["afirmacoes_erradas_brutas"] += 1
            if conferida:
                m["afirmacoes_erradas_conferidas"] += 1
        if certo and conferida:
            m["cobertura_conferida"] += 1
        # Política de uso: só afirma com prova conferida E a base inteira consistente
        # (o enumerador checa a consistência; acima de 10 átomos, com o limite do professor).
        if q["status"] in ("sustentado", "refutado") and conferida:
            consistente = bool(G.Professor(G.para_premissas(p)).mundos)
            if consistente:
                m["politica_erros"] += not certo
                m["politica_cobertura"] += certo
        elif q["status"] == "conflito" and conferida:
            m["politica_cobertura"] += certo
        if p["status"] == "indeterminado" and certo:
            indet_n += 1
            ok = (q["perguntar"] in p["perguntar"]) if p["perguntar"] else q["perguntar"] is None
            indet_ok += ok
        exato = certo and (conferida if p["status"] != "indeterminado" else
                           ((q["perguntar"] in p["perguntar"]) if p["perguntar"] else q["perguntar"] is None))
        m["exato"] += exato
        por_status[p["status"]][0] += exato
    for k in ("status_acc", "exato", "afirmacoes_erradas_brutas", "afirmacoes_erradas_conferidas"):
        m[k] = m[k] / n
    m["cobertura_conferida"] /= max(1, com_conclusao)
    m["politica_cobertura"] /= max(1, com_conclusao)
    m["politica_erros"] /= n
    m["pergunta_ok"] = indet_ok / max(1, indet_n)
    m["exato_por_status"] = {s: (a / b if b else None) for s, (a, b) in por_status.items()}
    return m


def embaralhar(p, rng):
    ordem = list(range(len(p["premissas"])))
    rng.shuffle(ordem)
    return dict(p, premissas=[p["premissas"][i] for i in ordem], prova=sorted(ordem.index(i) for i in p["prova"]))


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", required=True)
    ap.add_argument("--passos", type=int, default=20000)
    ap.add_argument("--lote", type=int, default=256)
    ap.add_argument("--n-treino", type=int, default=400000)
    ap.add_argument("--d", type=int, default=128)
    ap.add_argument("--camadas", type=int, default=2)
    ap.add_argument("--voltas", type=int, default=8)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--avaliar-a-cada", type=int, default=1000)
    ap.add_argument("--processos", type=int, default=4)
    ap.add_argument("--semente", type=int, default=7)
    ap.add_argument("--dev-n", type=int, default=1000)
    ap.add_argument("--max-horas", type=float, default=3.0)
    a = ap.parse_args()
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    P.semear(a.semente)

    texto = (AQUI / "conjuntos_pensador.json").read_text(encoding="utf-8")
    manifesto = json.loads((AQUI / "manifesto.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(texto.encode()).hexdigest() == manifesto["conjuntos_sha256"], "conjuntos alterados"
    conjuntos = json.loads(texto)
    proibidos = frozenset(json.loads((AQUI / "proibidos_treino.json").read_text()))

    cache = saida / ("treino_%d_%d.json" % (a.n_treino, a.semente))
    t0 = time.time()
    if cache.exists():
        treino = json.loads(cache.read_text())
    else:
        treino = gerar_treino(a.n_treino, a.semente, proibidos, a.processos)
        cache.write_text(json.dumps(treino, separators=(",", ":")))
    print("treino: %d problemas (%.0fs)" % (len(treino), time.time() - t0), flush=True)

    modelo = P.Pensador(a.d, 4, a.camadas, a.voltas).to(dispositivo)
    n_param = sum(p.numel() for p in modelo.parameters())
    print("parâmetros: %d | voltas: %d | dispositivo: %s" % (n_param, a.voltas, dispositivo), flush=True)
    opt = torch.optim.AdamW(modelo.parameters(), lr=a.lr, weight_decay=0.01)
    aquec = min(500, a.passos // 10)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1, (s + 1) / aquec) *
                                              0.5 * (1 + math.cos(math.pi * min(1.0, s / a.passos))))
    rng = random.Random(a.semente + 1)
    dev = conjuntos["dev"][:a.dev_n]
    melhor, historico = -1.0, []
    inicio = time.time()
    for passo in range(1, a.passos + 1):
        modelo.train()
        x = P.lote(rng.sample(treino, a.lote), rng, dispositivo)
        l = P.perda(modelo(x), x)
        opt.zero_grad()
        l.backward()
        torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
        opt.step()
        sched.step()
        fim = (time.time() - inicio) / 3600 > a.max_horas
        if passo % a.avaliar_a_cada == 0 or passo == a.passos or fim:
            m = avaliar(dev, P.prever(modelo, dev, random.Random(5), dispositivo))
            historico.append({"passo": passo, "perda": round(l.item(), 4), **{k: m[k] for k in ("status_acc", "exato")}})
            print("passo %d perda %.4f | dev status %.3f exato %.3f" % (passo, l.item(), m["status_acc"], m["exato"]),
                  flush=True)
            if m["exato"] > melhor:
                melhor = m["exato"]
                torch.save({"estado": modelo.state_dict(), "config": vars(a), "passo": passo}, saida / "pensador.pt")
        if fim:
            print("orçamento de tempo atingido", flush=True)
            break

    ck = torch.load(saida / "pensador.pt", map_location=dispositivo)
    modelo.load_state_dict(ck["estado"])
    resultado = {"protocolo": manifesto["protocolo"], "conjuntos_sha256": manifesto["conjuntos_sha256"],
                 "parametros": n_param, "config": vars(a), "passo_escolhido": ck["passo"], "historico": historico,
                 "ativo_no_chat": False, "avaliacao": {}}
    for nome in ("blind_iid", "ood_profundidade", "ood_tamanho"):
        probs = conjuntos[nome]
        resultado["avaliacao"][nome] = {}
        for voltas in sorted({a.voltas, 2 * a.voltas, 1}):
            m = avaliar(probs, P.prever(modelo, probs, random.Random(11), dispositivo, voltas))
            resultado["avaliacao"][nome]["voltas_%d" % voltas] = m
            print(nome, "voltas", voltas, json.dumps({k: round(v, 4) for k, v in m.items()
                                                       if isinstance(v, float)}), flush=True)
    base = conjuntos["blind_iid"]
    r = random.Random(13)
    p1 = P.prever(modelo, base, random.Random(11), dispositivo)
    p2 = P.prever(modelo, [embaralhar(p, r) for p in base], random.Random(17), dispositivo)
    resultado["invariancia_status"] = sum(x["status"] == y["status"] for x, y in zip(p1, p2)) / len(base)
    # Gates no número de voltas do treino, fixado antes; 1 e 2x voltas são só relatados.
    gates = {nome: resultado["avaliacao"][nome]["voltas_%d" % a.voltas]["exato"] >= limiar
             for nome, limiar in GATES.items()}
    # A rede sozinha erra pouco ao afirmar; com a política (prova conferida + base
    # consistente) não pode afirmar errado.
    gates["afirmacoes_erradas_brutas"] = all(
        c["voltas_%d" % a.voltas]["afirmacoes_erradas_brutas"] <= 0.02 for c in resultado["avaliacao"].values())
    gates["politica_sem_erro"] = all(c["voltas_%d" % a.voltas]["politica_erros"] == 0
                                     for c in resultado["avaliacao"].values())
    gates["invariancia"] = resultado["invariancia_status"] >= 0.98
    resultado["gates"] = gates
    resultado["aprovado"] = all(gates.values())
    (saida / "resultado_pensador.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                                                   encoding="utf-8")
    print("gates:", json.dumps(gates), "| aprovado:", resultado["aprovado"], flush=True)


if __name__ == "__main__":
    principal()
