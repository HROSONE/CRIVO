"""O pensador v2 no chat: a rede própria propõe, o enumerador do CRIVO confere.

O pensador (experimentos/pensador_20261012, aprovado nos gates em 15/10/2026, RESULTADO.md) é uma
rede recursiva pequena (918 mil parâmetros, treinada do zero) que lê as premissas estruturadas e diz
o veredito (sustentado, refutado, indeterminado, conflito) e quais premissas importam. Aqui ele roda
em NumPy (sem PyTorch), com a parada adaptativa da v2 (para quando a decisão fica igual 3 voltas
seguidas, entre 4 e 32 voltas) e a busca conferida: entre as 10 premissas em que ele mais confia,
o verificador acha a menor prova que basta.

Segurança: o raciocinio_ativo continua calculando a resposta exata (enumera os mundos). O pensador
só responde quando o veredito dele é o mesmo do enumerador e a prova dele basta e é mínima; senão,
fica a resposta do enumerador. Ele nunca muda o que é verdade, só quem chegou lá e por qual caminho.

Pesos: artefatos/pensador_v2_pt/pensador_numpy.npz (scripts/exportar_pensador_numpy.py, SHA conferido).
`CRIVO_DISABLE_PENSADOR=1` desliga.
"""
import hashlib
import json
import os
import random
from functools import lru_cache
from pathlib import Path

import numpy as np

ARQUIVO = Path(__file__).resolve().parent / "artefatos" / "pensador_v2_pt" / "pensador_numpy.npz"  # _pt: entra no pacote do site (vercel.json)
SHA256 = "f57fd4869b53890d89727c7614dcb698ac8426d345b6ad5af9c5646d7fff1412"

STATUS = ("sustentado", "refutado", "indeterminado", "conflito")
PAD, CLS, PREM, NEG, E, OU, ENTAO, QUERY, FATO = range(9)
BASE_ATOMO, VAGAS_ATOMO, VAGAS_PREMISSA, MAX_POS = 16, 64, 40, 12
SEG_CLS, SEG_PERGUNTA = VAGAS_PREMISSA, VAGAS_PREMISSA + 1
MARCA, CONDICAO, CONCLUSAO, PAPEL_FATO, PERGUNTA = range(5)
MAX_VOLTAS, ESTAVEL, MIN_VOLTAS, K_BUSCA = 32, 3, 4, 10


def desligado():
    return os.environ.get("CRIVO_DISABLE_PENSADOR", "").strip().lower() in ("1", "true", "yes", "on", "sim")


@lru_cache(maxsize=1)
def _pesos():
    if desligado() or not ARQUIVO.is_file():
        return None
    if hashlib.sha256(ARQUIVO.read_bytes()).hexdigest() != SHA256:
        return None
    z = np.load(ARQUIVO)
    p = {k: z[k] for k in z.files if k != "meta"}
    p["_meta"] = json.loads(str(z["meta"]))
    return p


def status():
    p = _pesos()
    return {"ligado": p is not None, "sha256": SHA256, "parametros": 918343,
            "passo": p["_meta"]["passo"] if p else None, "protocolo": "pensador_v2_20261014"}


def codificar(problema, semente=0):
    """O mesmo formato do treino (pensador.codificar), com as vagas sorteadas por uma semente fixa."""
    rng = random.Random(semente)
    n = problema["atomos"]
    vagas_a = rng.sample(range(VAGAS_ATOMO), n)
    vagas_p = rng.sample(range(VAGAS_PREMISSA), len(problema["premissas"]))
    tok, seg, pos, premissa, papel = [CLS], [SEG_CLS], [0], [-1], [MARCA]

    def por(t, s, p, i=-1, r=MARCA):
        tok.append(t); seg.append(s); pos.append(min(p, MAX_POS - 1)); premissa.append(i); papel.append(r)

    def lit(a, negativo, s, p, i, r):
        if negativo:
            por(NEG, s, p, i, r); p += 1
        por(BASE_ATOMO + vagas_a[a], s, p, i, r)
        return p + 1

    for i, pr in enumerate(problema["premissas"]):
        s = vagas_p[i]
        por(PREM, s, 0, i)
        p = 1
        if not pr["a"]:
            por(FATO, s, p); p += 1
        else:
            for a, ng in pr["a"]:
                p = lit(a, ng, s, p, -1, CONDICAO)
            por(OU if pr.get("op") == "ou" else E, s, p); p += 1
            por(ENTAO, s, p); p += 1
        lit(pr["c"][0], pr["c"][1], s, p, -1, CONCLUSAO if pr["a"] else PAPEL_FATO)
    por(QUERY, SEG_PERGUNTA, 0)
    lit(problema["pergunta"][0], problema["pergunta"][1], SEG_PERGUNTA, 1, -1, PERGUNTA)
    return {k: np.asarray(v) for k, v in (("tok", tok), ("seg", seg), ("pos", pos), ("premissa", premissa), ("papel", papel))}


def _norma(x, w, b):
    m = x.mean(-1, keepdims=True)
    v = ((x - m) ** 2).mean(-1, keepdims=True)
    return (x - m) / np.sqrt(v + 1e-5) * w + b


def _camada(h, p, i, cabecas=4):
    pre = "bloco.layers.%d." % i
    L, d = h.shape
    dh = d // cabecas
    x = _norma(h, p[pre + "norm1.weight"], p[pre + "norm1.bias"])
    qkv = x @ p[pre + "self_attn.in_proj_weight"].T + p[pre + "self_attn.in_proj_bias"]
    q, k, v = (qkv[:, j * d:(j + 1) * d].reshape(L, cabecas, dh).transpose(1, 0, 2) for j in range(3))
    a = q @ k.transpose(0, 2, 1) / np.sqrt(dh)
    a = np.exp(a - a.max(-1, keepdims=True))
    a /= a.sum(-1, keepdims=True)
    o = (a @ v).transpose(1, 0, 2).reshape(L, d)
    h = h + o @ p[pre + "self_attn.out_proj.weight"].T + p[pre + "self_attn.out_proj.bias"]
    x = _norma(h, p[pre + "norm2.weight"], p[pre + "norm2.bias"])
    f = np.maximum(0, x @ p[pre + "linear1.weight"].T + p[pre + "linear1.bias"])
    return h + f @ p[pre + "linear2.weight"].T + p[pre + "linear2.bias"]


def voltas_de(x, p, voltas=MAX_VOLTAS):
    """Uma volta por vez: (logits de status, logits de prova por token). Quem usa decide quando parar."""
    entrada = p["tok.weight"][x["tok"]] + p["seg.weight"][x["seg"]] + p["pos.weight"][x["pos"]] + p["papel.weight"][x["papel"]]
    h = np.broadcast_to(p["estado0"], entrada.shape).astype(np.float32)
    camadas = p["_meta"]["config"]["camadas"]
    for _ in range(voltas):
        h = h + entrada
        for i in range(camadas):
            h = _camada(h, p, i)
        z = _norma(h, p["norma.weight"], p["norma.bias"])
        yield (z[0] @ p["cab_status.weight"].T + p["cab_status.bias"],
               (z @ p["cab_prova.weight"].T + p["cab_prova.bias"])[:, 0])


def rodar(x, p, voltas=MAX_VOLTAS):
    """Saída de todas as voltas (para conferir contra o treino)."""
    return list(voltas_de(x, p, voltas))


def para_problema(premissas, alvo):
    """Premissas do raciocinio_ativo → o formato do pensador (átomos numerados pela ordem em que aparecem)."""
    nomes = {}
    for pr in premissas:
        for l in pr.antecedentes + (pr.consequente,):
            nomes.setdefault(l.nome, len(nomes))
    if alvo.nome not in nomes or len(nomes) > VAGAS_ATOMO or len(premissas) > VAGAS_PREMISSA:
        return None
    return {"atomos": len(nomes), "pergunta": (nomes[alvo.nome], alvo.negativo),
            "premissas": [{"a": [(nomes[l.nome], l.negativo) for l in pr.antecedentes],
                           "c": (nomes[pr.consequente.nome], pr.consequente.negativo), "op": pr.operador} for pr in premissas]}


def _basta(premissas, alvo, estado, indices):
    from raciocinio_ativo import SistemaPremissas
    if not indices:
        return False
    s = SistemaPremissas([premissas[i] for i in indices])
    if estado == "conflito":
        return not s.mundos
    if not s.mundos or alvo.nome not in s.bits:
        return False
    objetivo = alvo if estado == "sustentado" else alvo.oposto()
    return all(s.verdadeiro(m, objetivo) for m in s.mundos)


def busca_conferida(premissas, alvo, estado, ordem, k=K_BUSCA):
    """Menor conjunto que basta entre as k premissas mais confiáveis, ou None (como pensador_v2.busca_conferida)."""
    if estado not in ("sustentado", "refutado", "conflito"):
        return None
    cand = ordem[:k]
    for n in range(1, len(cand) + 1):
        if _basta(premissas, alvo, estado, cand[:n]):
            prova = list(cand[:n])
            for i in reversed(cand[:n]):
                resto = [j for j in prova if j != i]
                if _basta(premissas, alvo, estado, resto):
                    prova = resto
            prova = sorted(prova)
            minima = not any(_basta(premissas, alvo, estado, [j for j in prova if j != i]) for i in prova)
            return prova if minima else None
    return None


def pensar(premissas, alvo):
    """O que o pensador propõe para a pergunta: {"status", "prova", "voltas"} (prova já conferida), ou None."""
    p = _pesos()
    if p is None:
        return None
    problema = para_problema(premissas, alvo)
    if problema is None:
        return None
    x = codificar(problema)
    eh_premissa = x["premissa"] >= 0
    anterior, iguais, fim = None, 0, 0
    for st, pv in voltas_de(x, p):   # para quando a decisão fica igual ESTAVEL voltas seguidas
        fim += 1
        d = (STATUS[int(st.argmax())], tuple(sorted({int(x["premissa"][j]) for j in np.flatnonzero(eh_premissa & (pv > 0))})))
        iguais = iguais + 1 if d == anterior else 1
        anterior = d
        if iguais >= ESTAVEL and fim >= MIN_VOLTAS:
            break
    estado = anterior[0]
    confianca = {}
    for j in np.flatnonzero(eh_premissa):
        i = int(x["premissa"][j])
        confianca[i] = max(confianca.get(i, -1e9), float(pv[j]))
    ordem = sorted(confianca, key=lambda i: -confianca[i])
    prova = busca_conferida(list(premissas), alvo, estado, ordem)
    return {"status": estado, "prova": prova, "voltas": fim}
