"""Detector de palavras-gatilho, ANTES do treino (20/10/2026).

No v6 e no v6b, falas novas perto (em n-gramas) de frases de OUTRA situação puxaram essas frases para o lado errado:
"tô procrastinando muito" (motivacao) puxou "tô sangrando muito" (urgência). Os testes não podem ser usados para achar
isso antes (seria olhar a prova), então o detector compara cada fala nova com as falas de TREINO de todas as situações
(fase 5 v3 e v4) e com as outras falas novas:

    gatilho se  maior parecença com outra situação ≥ LIMIAR  e  > maior parecença com o TREINO ANTIGO da própria + MARGEM

Também acusa toda fala perto de uma situação de saúde ou urgência, com limiar mais baixo.

Uso: python detector_gatilhos.py formas_v7   (módulo com FORMAS); imprime os gatilhos e devolve código 1 se houver.
"""
import gzip
import importlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import gerar_v6 as G  # noqa: E402  (caminhos e módulos da fase 5)
from gerar_v6b import vetor  # noqa: E402

LIMIAR, MARGEM = 0.50, 0.0
LIMIAR_SAUDE = 0.40
SAUDE = {"saude_urgente", "saude_geral", "ansioso_peito", "ajuda_socorro"}
# Situações compostas: parecer com as partes é o que elas são ("tchau, idiota" = despedida + insulto). No v6b, pares
# mínimos entre elas consertaram desisto_despedida (51 → 76%) e estou_bem (58 → 80%). Não contam como gatilho.
COMPONENTES = {
    "despedida_rude": {"despedida", "insulto"}, "desisto_despedida": {"desisto", "despedida"},
    "obrigado_despedida": {"obrigado", "despedida"}, "despedida_dormir": {"despedida", "boa_noite"},
    "reciproco": {"estou_bem", "oi_tudo_bem"}, "estou_bem": {"reciproco", "oi_tudo_bem"}, "oi_tudo_bem": {"oi", "estou_bem"},
}


def compostas(a, b):
    return b in COMPONENTES.get(a, ()) or a in COMPONENTES.get(b, ())


def formas_de_treino():
    """{situação: [falas]} do treino v3 e das falas de treino da v4 (sem histórico, só cenas)."""
    v3 = json.loads(gzip.open(G.EXP5 / "dados_fase5_v3.json.gz").read().decode("utf-8"))
    por = defaultdict(set)
    for c in v3["treino"]:
        if c["situacao"].startswith("cena:"):
            por[c["situacao"][5:]].add(c["mensagem"])
    for n, cen in G.cenas_v4.S4.items():
        por[n].update(u for u in cen["u"] if G.gerar_v4.parte(u) == "treino")
    return {s: sorted(v) for s, v in por.items()}


def vetores(textos):
    return np.stack([vetor(t) for t in textos]) if textos else np.zeros((0, 4096), np.float32)


def detectar(formas_novas, treino=None, bloco=512):
    """Mesma regra de antes, em blocos (aguenta dezenas de milhares de falas)."""
    treino = treino or formas_de_treino()
    textos, donos = [], []
    for s, L in treino.items():
        textos += L; donos += [s] * len(L)
    cand = [(s, u) for s, L in formas_novas.items() for u in L]
    textos += [u for _, u in cand]; donos += [s for s, _ in cand]
    M = vetores(textos)
    donos = np.array(donos)
    base = len(textos) - len(cand)
    achados = []
    for a in range(0, len(cand), bloco):
        sims = M[base + a: base + a + bloco] @ M.T
        for j, (s, u) in enumerate(cand[a:a + bloco]):
            linha = sims[j].copy()
            linha[base + a + j] = -1                 # a própria fala
            mesma = donos == s
            # "própria" só contra o treino antigo: falas novas parecidas (minhas ou do professor) não podem esconder um gatilho
            mesma_antiga = mesma.copy(); mesma_antiga[base:] = False
            p = float(linha[mesma_antiga].max()) if mesma_antiga.any() else 0.0
            linha_o = np.where(mesma, -1, linha)
            i = int(np.argmax(linha_o))
            o, t = float(linha_o[i]), str(donos[i])
            saude = t in SAUDE and o >= LIMIAR_SAUDE
            if saude or (o >= LIMIAR and o > p + MARGEM and not compostas(s, t)):
                achados.append({"situacao": s, "fala": u, "puxa": t, "parecida_com": textos[i],
                                "outra": round(o, 2), "propria": round(p, 2), "saude": bool(saude)})
    return achados


if __name__ == "__main__":
    mod = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "formas_v7")
    a = detectar(mod.FORMAS)
    for x in a:
        print(x)
    print(f"{len(a)} gatilho(s) em {sum(len(v) for v in mod.FORMAS.values())} falas")
    sys.exit(1 if a else 0)
