"""Treina o decisor aprendido (decisor_resposta.py): este fato responde?

Uso: python scripts/treinar_decisor.py [--perguntas 1500]

Dados de treino: as perguntas do tutor em dados/decisor_tutor.json (formulação
real, sem o nome do assunto; com e sem resposta) e perguntas geradas para as
fichas permitidas (sem tutor, testes de
leitura v1/v2, teste de perguntas sem nome e astronomia):
  com resposta  perguntas sintéticas de cada fato, com e sem o nome do
                assunto (as mesmas da busca aprendida); o fato de origem
                responde, os outros candidatos não;
  sem resposta  a mesma pergunta com a ficha que responde retirada do
                acervo: nenhum candidato responde. É assim que o decisor
                aprende a calar, sem regra escrita à mão.
Como na rota da busca, as fichas citadas na pergunta ficam de fora dos
candidatos (já foram lidas): uma pergunta que cita a ficha que responde vira,
aqui, um caso sem resposta.

Validação (escolhe a regularização e os dois cortes): as perguntas do tutor
e o dev das perguntas sem nome, ambos com casos sem resposta. Os cortes:
afirmar com precisão >= 0,9 e aproximar com precisão >= 0,7 na validação,
contando como erro tanto o fato errado quanto responder a uma pergunta sem
resposta, e o par de maior nota (fatos certos entregues, menos 4 por
pergunta sem resposta respondida). Os testes congelados são medidos depois, com o CRIVO inteiro
(scripts/avaliar_busca_sem_nome.py e scripts/avaliar_bateria.py).
"""
import argparse
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

import numpy as np  # noqa: E402

from decisor_resposta import CAMINHO_MODELO, TRACOS, ler_pergunta  # noqa: E402

SEMENTE = 20261007
PRECISAO_AFIRMAR = 0.9
PRECISAO_APROXIMAR = 0.7
PESO_SEM_RESPOSTA = 4
L2 = (0.0, 0.001, 0.01, 0.1, 1.0)


def _ler(caminho):
    return json.loads((RAIZ / caminho).read_text(encoding="utf-8"))


def grupo(bot, pergunta, assunto, fato, excluir=frozenset()):
    """(matriz, rótulos, leituras, l_todas por candidato) de uma pergunta;
    None se não há candidatos."""
    quadro = bot.compositor.interpretar(pergunta)
    if quadro is None or quadro.recusa == "negacao_ou_qualificador":
        return None
    citados = frozenset(((quadro.assunto,) if quadro.assunto else ()) + tuple(quadro.outros))
    # Como na rota da busca: as fichas citadas já foram lidas e ficam de fora.
    lidos = ler_pergunta(bot, pergunta, quadro, citados, frozenset(excluir) | citados)
    if not lidos:
        return None
    x = np.asarray([l[0] for l in lidos], dtype=np.float64)
    y = np.asarray([1.0 if (l[2], l[3]) == (assunto, fato) else 0.0 for l in lidos])
    tem_leitura = np.asarray([l[1] is not None for l in lidos])
    return x, y, tem_leitura, fato is not None


def treinar(grupos, l2, passos=4000, taxa=0.5):
    """Logística com as evidências padronizadas (média 0, desvio 1); os pesos
    devolvidos já valem para as evidências originais."""
    X = np.concatenate([g[0] for g in grupos])
    y = np.concatenate([g[1] for g in grupos])
    media, desvio = X.mean(0), X.std(0)
    media[0], desvio[0] = 0.0, 1.0          # viés
    desvio[desvio < 1e-9] = 1.0
    Z = (X - media) / desvio
    peso_pos = (len(y) - y.sum()) / max(1.0, y.sum())
    amostra = np.where(y == 1, peso_pos, 1.0)
    w = np.zeros(X.shape[1])
    m, v = np.zeros_like(w), np.zeros_like(w)
    for t in range(1, passos + 1):
        p = 1 / (1 + np.exp(-np.clip(Z @ w, -30, 30)))
        g = Z.T @ ((p - y) * amostra) / amostra.sum() + l2 * np.r_[0.0, w[1:]]
        m = 0.9 * m + 0.1 * g
        v = 0.999 * v + 0.001 * g * g
        w -= taxa * 0.02 * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
    pesos = w / desvio
    pesos[0] = w[0] - float((w[1:] * media[1:] / desvio[1:]).sum())
    return pesos


def propostas(w, grupos):
    """[(prob, certo?, respondível?, afirmável?, tem leitura?)] do melhor candidato de cada pergunta."""
    i_todas, i_par = TRACOS.index("l_todas"), TRACOS.index("b_tipo_sem_par")
    saida = []
    for x, y, tem_leitura, respondivel in grupos:
        p = 1 / (1 + np.exp(-np.clip(x @ w, -30, 30)))
        a = int(np.argmax(p))
        saida.append((float(p[a]), bool(y[a]), respondivel, bool(x[a, i_todas]) and not x[a, i_par],
                      bool(tem_leitura[a])))
    return saida


def politica(linhas, t_afirmar, t_aproximar):
    afirma = [l for l in linhas if l[4] and l[3] and l[0] >= t_afirmar]
    aproxima = [l for l in linhas if l[4] and not (l[3] and l[0] >= t_afirmar) and l[0] >= t_aproximar]
    return afirma, aproxima


def contar(grupo_linhas):
    return {"n": len(grupo_linhas), "certos": sum(1 for l in grupo_linhas if l[1]),
            "errados": sum(1 for l in grupo_linhas if not l[1] and l[2]),
            "sem_resposta": sum(1 for l in grupo_linhas if not l[2])}


def precisao(c):
    return c["certos"] / c["n"] if c["n"] else 1.0


def nota(r):
    """Fatos certos entregues; responder a uma pergunta sem resposta custa 4."""
    return r["certos_entregues"] - PESO_SEM_RESPOSTA * r["sem_resposta_respondidas"]


def cortes(linhas):
    """Os dois cortes de maior nota com as precisões mínimas."""
    grade = [i / 100 for i in range(10, 100, 2)]
    melhor = (0.99, 0.99)
    melhor_nota = nota(resumo(linhas, *melhor))
    for t_a in grade:
        a = contar(politica(linhas, t_a, 2.0)[0])
        if precisao(a) < PRECISAO_AFIRMAR:
            continue
        for t_b in grade:
            if t_b > t_a:
                break
            r = resumo(linhas, t_a, t_b)
            if precisao(r["aproxima"]) >= PRECISAO_APROXIMAR and nota(r) > melhor_nota:
                melhor, melhor_nota = (t_a, t_b), nota(r)
    return melhor


def resumo(linhas, t_a, t_b):
    a, b = politica(linhas, t_a, t_b)
    ca, cb = contar(a), contar(b)
    return {"perguntas": len(linhas), "respondiveis": sum(1 for l in linhas if l[2]),
            "afirma": ca, "aproxima": cb, "certos_entregues": ca["certos"] + cb["certos"],
            "sem_resposta_respondidas": ca["sem_resposta"] + cb["sem_resposta"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--perguntas", type=int, default=1500, help="perguntas sintéticas (0 = nenhuma)")
    ap.add_argument("--repetir-tutor", type=int, default=3,
                    help="vezes que as perguntas do tutor (dados/decisor_tutor.json) entram no treino")
    ap.add_argument("--saida", default=str(CAMINHO_MODELO))
    args = ap.parse_args()
    random.seed(SEMENTE)
    rng = random.Random(SEMENTE)
    from crivo import Crivo
    from treinar_busca_semantica import exemplos_sinteticos
    bot = Crivo()
    comp = bot.compositor
    fora = {c["assunto"] for c in _ler("avaliacoes/busca_sem_nome_v1/teste.json")["casos"] if c["assunto"]}
    fora |= {c["assunto"] for c in _ler("avaliacoes/busca_sem_nome_v1/dev.json")["casos"] if c["assunto"]}
    exemplos = [e for e in exemplos_sinteticos(comp, rng) if e[1] not in fora]
    rng.shuffle(exemplos)
    treino = []
    for q, assunto, fato in exemplos[:args.perguntas]:
        for g in (grupo(bot, q, assunto, fato), grupo(bot, q, assunto, None, excluir={assunto})):
            if g is not None:
                treino.append(g)
    # Perguntas do tutor, com formulação real (sem o nome do assunto, outras
    # palavras): com a ficha que responde e sem ela; e as sem resposta.
    tutor = []
    for c in _ler("dados/decisor_tutor.json")["casos"]:
        if c["assunto"] is None:
            tutor.append(grupo(bot, c["pergunta"], None, None))
        else:
            tutor.append(grupo(bot, c["pergunta"], c["assunto"], c["fato"]))
            tutor.append(grupo(bot, c["pergunta"], c["assunto"], None, excluir={c["assunto"]}))
    tutor = [g for g in tutor if g is not None]
    treino += tutor * args.repetir_tutor
    validacao = []
    for caminho in ("dados/leitura_ficha_tutor.json", "avaliacoes/busca_sem_nome_v1/dev.json"):
        for c in _ler(caminho)["casos"]:
            if c["assunto"] is None or c["assunto"] in comp.itens:
                g = grupo(bot, c["pergunta"], c["assunto"], c["fato"])
                if g is not None:
                    validacao.append(g)
    print("treino:", len(treino), "perguntas (com e sem resposta) | validação:", len(validacao), flush=True)
    melhor = None
    for l2 in L2:
        w = treinar(treino, l2)
        linhas = propostas(w, validacao)
        t_a, t_b = cortes(linhas)
        r = resumo(linhas, t_a, t_b)
        print("L2 %-6s cortes %.2f/%.2f %s" % (l2, t_a, t_b, r), flush=True)
        if melhor is None or nota(r) > nota(melhor[4]):
            melhor = (l2, w, t_a, t_b, r)
    l2, w, t_a, t_b, r = melhor
    print("pesos:", {t: round(float(p), 3) for t, p in zip(TRACOS, w)}, flush=True)
    aprovado = (precisao(r["afirma"]) >= PRECISAO_AFIRMAR and precisao(r["aproxima"]) >= PRECISAO_APROXIMAR
                and r["certos_entregues"] > 0)
    meta = {"versao": 1, "tracos": list(TRACOS), "pesos": [round(float(p), 5) for p in w],
            "limiar_afirmar": t_a, "limiar_aproximar": t_b,
            "treino": {"perguntas": len(treino), "l2": l2, "semente": SEMENTE,
                       "dados": "sintéticas das fichas permitidas, com e sem a ficha que responde"},
            "validacao": r,
            "controle": {"aprovado": aprovado,
                         "criterio": "na validação (tutor + dev sem nome), afirmar com precisão >= 0,9 e "
                                     "aproximar com precisão >= 0,7; ligado no CRIVO só se os testes "
                                     "congelados não piorarem"}}
    Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.saida).write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("aprovado:", aprovado, flush=True)


if __name__ == "__main__":
    main()
