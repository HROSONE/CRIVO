"""Pensador v2: pensar até a resposta parar de mudar e buscar a prova com o verificador.

A v1 (RESULTADO.md) acertava o veredito (status 97–100%) e errava a prova mínima, e 16 voltas não
eram melhores que 8. A v2 muda o uso e o treino, não a régua (mesmos conjuntos congelados, mesmos
gates):

- **voltas sorteadas no treino** (4 a 16 por lote): a rede aprende a ser útil em qualquer
  profundidade, não num número fixo de passos;
- **parada adaptativa**: na hora de usar, ela dá voltas até a decisão (status e prova) ficar igual
  em ESTAVEL voltas seguidas, depois de pelo menos MIN_VOLTAS e até MAX_VOLTAS;
- **busca conferida da prova**: a rede ordena as premissas pela confiança, e o verificador do CRIVO
  (gerar_pensador.conferir_prova e o mesmo teste de suficiência) procura, nas K primeiras, o menor
  conjunto que basta. O verificador só aceita prova verdadeira, então a busca não cria afirmação
  errada: no pior caso, não acha nada e o CRIVO diz que não consegue concluir.

Registrado antes de rodar (14/10/2026): o resultado mostra as três contas (rede como na v1,
adaptativa e adaptativa com busca). **A aprovação usa a adaptativa com busca**, porque é ela que
rodaria no CRIVO; as outras duas são só relatadas.
"""
import random

import torch

import gerar_pensador as G
import pensador as P

MAX_VOLTAS = 32
ESTAVEL = 3
MIN_VOLTAS = 4   # não para antes disso (o treino sorteia de 4 a 16)
K_BUSCA = 10


def basta(problema, status, indices):
    """As premissas `indices` bastam para `status` (o mesmo teste de conferir_prova, sem a minimalidade)."""
    if not indices:
        return False
    alvo = G.literal(*problema["pergunta"])
    todas = G.para_premissas(problema)
    s = G.Professor([todas[i] for i in indices])
    if status == "conflito":
        return not s.mundos
    if not s.mundos or alvo.nome not in s.bits:
        return False
    objetivo = alvo if status == "sustentado" else alvo.oposto()
    return all(s.verdadeiro(m, objetivo) for m in s.mundos)


def busca_conferida(problema, status, ordem, k=K_BUSCA):
    """Menor conjunto que basta entre as k premissas mais confiáveis (ordem: da mais para a menos)."""
    if status not in ("sustentado", "refutado", "conflito"):
        return None
    candidatas = ordem[:k]
    for n in range(1, len(candidatas) + 1):
        if basta(problema, status, candidatas[:n]):
            prova = list(candidatas[:n])
            for i in reversed(candidatas[:n]):   # tira a menos confiável primeiro, enquanto ainda basta
                resto = [j for j in prova if j != i]
                if basta(problema, status, resto):
                    prova = resto
            prova = sorted(prova)
            return prova if G.conferir_prova(problema, status, prova) else None
    return None


def _decisao(s, x, b, L):
    st = P.STATUS[s["status"][b].argmax().item()]
    prova = tuple(sorted({x["premissa"][b, j].item() for j in range(L) if x["premissa"][b, j] >= 0 and s["prova"][b, j] > 0}))
    k = s["perguntar"][b].argmax().item()
    perguntar = None if k == L else x["atomo"][b, k].item()
    return st, prova, perguntar


@torch.no_grad()
def prever_v2(modelo, problemas, rng, dispositivo="cpu", voltas_fixas=8, max_voltas=MAX_VOLTAS, estavel=ESTAVEL,
              lote_max=256):
    """{"rede": [...], "adaptativo": [...], "adaptativo_busca": [...]}, cada um como pensador.prever."""
    modelo.eval()
    out = {"rede": [], "adaptativo": [], "adaptativo_busca": []}
    for i in range(0, len(problemas), lote_max):
        parte = problemas[i:i + lote_max]
        x = P.lote(parte, rng, dispositivo)
        saidas = modelo(x, max(max_voltas, voltas_fixas))
        L = x["tok"].shape[1]
        for b, p in enumerate(parte):
            st, prova, perg = _decisao(saidas[voltas_fixas - 1], x, b, L)
            out["rede"].append({"status": st, "prova": list(prova), "perguntar": perg, "voltas": voltas_fixas})
            anterior, iguais, t_fim = None, 0, max_voltas
            for t in range(max_voltas):
                d = _decisao(saidas[t], x, b, L)
                iguais = iguais + 1 if d == anterior else 1
                anterior = d
                if iguais >= estavel and t + 1 >= MIN_VOLTAS:
                    t_fim = t + 1
                    break
            st, prova, perg = anterior
            out["adaptativo"].append({"status": st, "prova": list(prova), "perguntar": perg, "voltas": t_fim})
            s = saidas[t_fim - 1]
            logit = {}
            for j in range(L):
                k = x["premissa"][b, j].item()
                if k >= 0:
                    logit[k] = max(logit.get(k, -1e9), s["prova"][b, j].item())
            ordem = sorted(logit, key=lambda k: -logit[k])
            achada = busca_conferida(p, st, ordem)
            out["adaptativo_busca"].append({"status": st, "prova": achada if achada is not None else list(prova),
                                            "perguntar": perg, "voltas": t_fim, "busca_achou": achada is not None})
    return out


def voltas_do_lote(rng, minimo=4, maximo=16):
    return rng.randint(minimo, maximo)


def semear(semente):
    random.seed(semente)
    torch.manual_seed(semente)
