"""O pensador: rede recursiva pequena, treinada do zero, que raciocina sobre o quadro.

Entrada: as premissas estruturadas e a pergunta (gerar_pensador.py), em tokens.
Os átomos e as premissas recebem "vagas" sorteadas a cada exemplo, então a rede
não pode decorar nomes nem posições — só a estrutura importa.

A rede é um bloco Transformer pequeno (2 camadas) aplicado várias vezes sobre o
próprio estado, com a entrada reinjetada a cada volta (ideia dos modelos
recursivos pequenos, como o TRM): pensar mais = dar mais voltas, sem mais
parâmetros. Cada volta é supervisionada (deep supervision).

Saídas:
  status     sustentado / refutado / indeterminado / conflito (do token CLS);
  prova      quais premissas entram na prova (um logit por premissa);
  perguntar  qual átomo perguntar quando indeterminado, ou "nenhum".

No uso, o pensador PROPÕE e o enumerador do CRIVO CONFERE a prova proposta
(gerar_pensador.conferir_prova), que é pequena e barata de checar. Afirmação
sem prova conferida vira "não consigo concluir".
"""
import random

import torch
import torch.nn as nn
import torch.nn.functional as F

STATUS = ("sustentado", "refutado", "indeterminado", "conflito")
PAD, CLS, PREM, NEG, E, OU, ENTAO, QUERY, FATO = range(9)
BASE_ATOMO = 16
VAGAS_ATOMO = 64
VAGAS_PREMISSA = 40
SEG_CLS, SEG_PERGUNTA = VAGAS_PREMISSA, VAGAS_PREMISSA + 1
MAX_POS = 12
# Papel de cada token: marcador, condição de uma regra, conclusão de uma regra, fato, pergunta.
MARCA, CONDICAO, CONCLUSAO, PAPEL_FATO, PERGUNTA = range(5)


def codificar(problema, rng):
    """Tokens com vagas sorteadas. Devolve dicionário de listas."""
    n = problema["atomos"]
    vagas_a = rng.sample(range(VAGAS_ATOMO), n)
    vagas_p = rng.sample(range(VAGAS_PREMISSA), len(problema["premissas"]))
    tok, seg, pos, premissa, atomo, papel = [CLS], [SEG_CLS], [0], [-1], [-1], [MARCA]

    def por(t, s, p, i=-1, a=-1, r=MARCA):
        tok.append(t); seg.append(s); pos.append(min(p, MAX_POS - 1)); premissa.append(i); atomo.append(a)
        papel.append(r)

    def lit(a, negativo, s, p, i, r):
        if negativo:
            por(NEG, s, p, i, -1, r); p += 1
        por(BASE_ATOMO + vagas_a[a], s, p, i, a, r)
        return p + 1

    for i, pr in enumerate(problema["premissas"]):
        s = vagas_p[i]
        por(PREM, s, 0, i)
        p = 1
        if not pr["a"]:
            por(FATO, s, p, -1); p += 1
        else:
            for a, ng in pr["a"]:
                p = lit(a, ng, s, p, -1, CONDICAO)
            por(OU if pr.get("op") == "ou" else E, s, p); p += 1
            por(ENTAO, s, p); p += 1
        lit(pr["c"][0], pr["c"][1], s, p, -1, CONCLUSAO if pr["a"] else PAPEL_FATO)
    por(QUERY, SEG_PERGUNTA, 0)
    lit(problema["pergunta"][0], problema["pergunta"][1], SEG_PERGUNTA, 1, -1, PERGUNTA)
    return {"tok": tok, "seg": seg, "pos": pos, "premissa": premissa, "atomo": atomo, "papel": papel}


def lote(problemas, rng, dispositivo="cpu"):
    """Tensores de um lote, com os alvos do professor."""
    cods = [codificar(p, rng) for p in problemas]
    L = max(len(c["tok"]) for c in cods)
    B = len(cods)
    t = {k: torch.full((B, L), v, dtype=torch.long) for k, v in
         (("tok", PAD), ("seg", 0), ("pos", 0), ("premissa", -1), ("atomo", -1), ("papel", MARCA))}
    for b, c in enumerate(cods):
        for k in t:
            t[k][b, :len(c[k])] = torch.tensor(c[k])
    status = torch.tensor([STATUS.index(p["status"]) if "status" in p else 0 for p in problemas])
    prova = torch.zeros(B, L)
    perg = torch.zeros(B, L + 1, dtype=torch.bool)  # última coluna: "nenhum"
    for b, p in enumerate(problemas):
        conjunto = set(p.get("prova", ()))
        for j in range(L):
            i = t["premissa"][b, j].item()
            if i >= 0 and i in conjunto:
                prova[b, j] = 1.0
        if p.get("status") == "indeterminado":
            uteis = set(p.get("perguntar", ()))
            if uteis:
                for j in range(L):
                    a = t["atomo"][b, j].item()
                    if a >= 0 and a in uteis and t["tok"][b, j] >= BASE_ATOMO:
                        perg[b, j] = True
            else:
                perg[b, L] = True
    saida = {k: v.to(dispositivo) for k, v in t.items()}
    saida.update(status=status.to(dispositivo), prova=prova.to(dispositivo), perguntar=perg.to(dispositivo))
    return saida


class Pensador(nn.Module):
    def __init__(self, d=128, cabecas=4, camadas=2, voltas=8):
        super().__init__()
        self.voltas = voltas
        self.tok = nn.Embedding(BASE_ATOMO + VAGAS_ATOMO, d)
        self.seg = nn.Embedding(VAGAS_PREMISSA + 2, d)
        self.pos = nn.Embedding(MAX_POS, d)
        self.papel = nn.Embedding(5, d)
        self.estado0 = nn.Parameter(torch.zeros(d))
        camada = nn.TransformerEncoderLayer(d, cabecas, 4 * d, dropout=0.0, batch_first=True, norm_first=True)
        self.bloco = nn.TransformerEncoder(camada, camadas, enable_nested_tensor=False)
        self.norma = nn.LayerNorm(d)
        self.cab_status = nn.Linear(d, len(STATUS))
        self.cab_prova = nn.Linear(d, 1)
        self.cab_perg = nn.Linear(d, 1)
        self.cab_nenhum = nn.Linear(d, 1)

    def forward(self, x, voltas=None):
        """Lista com as saídas de cada volta."""
        mascara = x["tok"].eq(PAD)
        entrada = self.tok(x["tok"]) + self.seg(x["seg"]) + self.pos(x["pos"]) + self.papel(x["papel"])
        h = self.estado0.expand_as(entrada)
        saidas = []
        for _ in range(voltas or self.voltas):
            h = self.bloco(h + entrada, src_key_padding_mask=mascara)
            z = self.norma(h)
            prova = self.cab_prova(z).squeeze(-1)
            perg = self.cab_perg(z).squeeze(-1).masked_fill(x["tok"].lt(BASE_ATOMO), -1e4)
            perg = torch.cat([perg, self.cab_nenhum(z[:, 0])], dim=1)
            saidas.append({"status": self.cab_status(z[:, 0]), "prova": prova, "perguntar": perg})
        return saidas


def perda(saidas, x):
    total = 0.0
    pesos = [i + 1 for i in range(len(saidas))]
    eh_prova = (x["premissa"] >= 0).float()
    com_prova = torch.tensor([s != 2 for s in x["status"].tolist()], device=eh_prova.device).float()
    indet = x["status"].eq(2)
    for w, s in zip(pesos, saidas):
        l_status = F.cross_entropy(s["status"], x["status"])
        bce = F.binary_cross_entropy_with_logits(s["prova"], x["prova"], reduction="none")
        l_prova = (bce * eh_prova * com_prova[:, None]).sum() / (eh_prova * com_prova[:, None]).sum().clamp(min=1)
        if indet.any():
            lp = s["perguntar"][indet]
            pos = lp.masked_fill(~x["perguntar"][indet], -1e4)
            l_perg = (torch.logsumexp(lp, 1) - torch.logsumexp(pos, 1)).mean()
        else:
            l_perg = s["status"].sum() * 0
        total = total + w * (l_status + l_prova + 0.5 * l_perg)
    return total / sum(pesos)


@torch.no_grad()
def prever(modelo, problemas, rng, dispositivo="cpu", voltas=None, lote_max=256):
    """Decisão final de cada problema: status, prova (índices) e átomo a perguntar."""
    modelo.eval()
    saida = []
    for i in range(0, len(problemas), lote_max):
        parte = problemas[i:i + lote_max]
        x = lote(parte, rng, dispositivo)
        s = modelo(x, voltas)[-1]
        st = s["status"].argmax(1).tolist()
        L = x["tok"].shape[1]
        for b, p in enumerate(parte):
            prova = sorted({x["premissa"][b, j].item() for j in range(L)
                            if x["premissa"][b, j] >= 0 and s["prova"][b, j] > 0})
            k = s["perguntar"][b].argmax().item()
            perguntar = None if k == L else x["atomo"][b, k].item()
            saida.append({"status": STATUS[st[b]], "prova": prova, "perguntar": perguntar})
    return saida


def semear(semente):
    random.seed(semente)
    torch.manual_seed(semente)
