"""Treina o analisador de frases biafim (BiLSTM + Dozat & Manning, 2017).

Feito para GPU (Google Colab: notebooks/treinar_analisador_colab.ipynb),
mas roda em CPU. A rede é treinada do zero em PyTorch sobre o UD
Portuguese-Bosque (CC BY-SA 4.0, conferido por SHA-256) e exportada para
NumPy: a execução no Crivo (analisador_frases.AnalisadorBiafim) não usa
torch. A avaliação final no teste oficial é feita pela execução em NumPy,
a mesma que o Crivo usa, depois de conferir que ela reproduz o torch.

Uso:
  python scripts/treinar_analisador_biafim.py --dados PASTA_CONLLU --saida artefatos/analisador_pt
"""
import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analisador_frases as af  # noqa: E402
from treinar_analisador import conferir_origem, lemas_fixos, ler_conllu, tabela_contracoes  # noqa: E402


class Vocab:
    def __init__(self, treino, vetores, min_freq=2):
        freq = Counter(af.forma_chave(p["forma"]) for f in treino for p in f)
        self.palavras = [af.NULO, af.UNK, af.RAIZ] + sorted(w for w, c in freq.items() if c >= min_freq)
        self.pal_id = {w: i for i, w in enumerate(self.palavras)}
        self.freq = freq
        self.sufixos = [af.NULO, af.UNK, af.RAIZ] + sorted({af.sufixo(p["forma"]) for f in treino for p in f})
        self.suf_id = {w: i for i, w in enumerate(self.sufixos)}
        self.formatos = [af.NULO, af.UNK, af.RAIZ, "num", "pont", "maius", "inicial", "minus"]
        self.fmt_id = {w: i for i, w in enumerate(self.formatos)}
        self.classes = sorted({p["classe"] for f in treino for p in f})
        self.cls_id = {w: i for i, w in enumerate(self.classes)}
        self.ligacoes = sorted({p["ligacao"] for f in treino for p in f})
        self.lig_id = {w: i for i, w in enumerate(self.ligacoes)}
        regras = Counter(af.regra_lema(p["forma"], p["lema"]) for f in treino for p in f)
        self.regras = [af.UNK] + [r for r, c in regras.most_common() if c >= 2][:800]
        self.reg_id = {w: i for i, w in enumerate(self.regras)}
        self.vet_palavras, self.vet_matriz = vetores
        self.vet_id = {w: i + 1 for i, w in enumerate(self.vet_palavras)}  # 0 = sem vetor

    def ids(self, formas):
        return af.ids_biafim(formas, self.pal_id, self.vet_id, self.suf_id, self.fmt_id)


class Biafim(nn.Module):
    def __init__(self, v, dim_pal=100, oculta=200, camadas=2, mlp_arco=400, mlp_rot=100, queda=0.33):
        super().__init__()
        pre = np.zeros((len(v.vet_palavras) + 1, v.vet_matriz.shape[1]), np.float32)
        pre[1:] = v.vet_matriz
        self.pal = nn.Embedding(len(v.palavras), dim_pal, padding_idx=0)
        nn.init.normal_(self.pal.weight, 0, 0.1)
        self.pre = nn.Embedding.from_pretrained(torch.tensor(pre), freeze=True, padding_idx=0)
        self.suf = nn.Embedding(len(v.sufixos), 32, padding_idx=0)
        self.fmt = nn.Embedding(len(v.formatos), 8, padding_idx=0)
        entrada = dim_pal + pre.shape[1] + 32 + 8
        self.lstm = nn.LSTM(entrada, oculta, num_layers=camadas, bidirectional=True, batch_first=True,
                            dropout=queda)
        h = 2 * oculta
        self.queda = queda
        self.cls = nn.Sequential(nn.Linear(h, 100), nn.ReLU(), nn.Dropout(queda), nn.Linear(100, len(v.classes)))
        self.lem = nn.Sequential(nn.Linear(h, 100), nn.ReLU(), nn.Dropout(queda), nn.Linear(100, len(v.regras)))
        self.arco_dep = nn.Linear(h, mlp_arco)
        self.arco_cab = nn.Linear(h, mlp_arco)
        self.rot_dep = nn.Linear(h, mlp_rot)
        self.rot_cab = nn.Linear(h, mlp_rot)
        self.U_arco = nn.Parameter(torch.zeros(mlp_arco, mlp_arco))
        self.u_arco = nn.Parameter(torch.zeros(mlp_arco))
        nl = len(v.ligacoes)
        self.U_rot = nn.Parameter(torch.zeros(nl, mlp_rot + 1, mlp_rot + 1))

    def forward(self, pal, pre, suf, fmt):
        x = torch.cat([self.pal(pal), self.pre(pre), self.suf(suf), self.fmt(fmt)], -1)
        x = F.dropout(x, self.queda, self.training)
        h, _ = self.lstm(x)
        h = F.dropout(h, self.queda, self.training)
        cls = self.cls(h)
        lem = self.lem(h)
        ad = F.dropout(F.relu(self.arco_dep(h)), self.queda, self.training)
        ac = F.dropout(F.relu(self.arco_cab(h)), self.queda, self.training)
        # s[b, i, j]: pontuação de j ser a cabeça de i.
        arco = torch.einsum("bid,de,bje->bij", ad, self.U_arco, ac) + (ac @ self.u_arco).unsqueeze(1)
        rd = F.dropout(F.relu(self.rot_dep(h)), self.queda, self.training)
        rc = F.dropout(F.relu(self.rot_cab(h)), self.queda, self.training)
        um = torch.ones(rd.shape[:2] + (1,), device=rd.device)
        return cls, lem, arco, torch.cat([rd, um], -1), torch.cat([rc, um], -1)

    def rotulos(self, rd, rc, cabecas):
        """rd, rc: [b, n, d+1]; cabecas: [b, n] → pontuações [b, n, L]."""
        rc_sel = rc.gather(1, cabecas.unsqueeze(-1).expand(-1, -1, rc.shape[-1]))
        return torch.einsum("bid,lde,bie->bil", rd, self.U_rot, rc_sel)


def lote_tensores(frases, v, dispositivo, abandono=0.0, rng=None):
    n = max(len(f) for f in frases) + 1
    b = len(frases)
    T = {k: torch.zeros((b, n), dtype=torch.long) for k in ("pal", "pre", "suf", "fmt", "cls", "lem", "cab", "lig")}
    mascara = torch.zeros((b, n), dtype=torch.bool)
    for k, f in enumerate(frases):
        ids = v.ids([p["forma"] for p in f])
        for campo, col in (("pal", 0), ("pre", 1), ("suf", 2), ("fmt", 3)):
            T[campo][k, :len(f) + 1] = torch.tensor([linha[col] for linha in ids])
        if abandono:
            for i, p in enumerate(f, 1):
                w = T["pal"][k, i].item()
                c = v.freq.get(af.forma_chave(p["forma"]), 0)
                if w > 2 and rng.random() < abandono / (abandono + c):
                    T["pal"][k, i] = 1
        for i, p in enumerate(f, 1):
            T["cls"][k, i] = v.cls_id.get(p["classe"], 0)
            T["lem"][k, i] = v.reg_id.get(af.regra_lema(p["forma"], p["lema"]), 0)
            T["cab"][k, i] = p["pai"]
            T["lig"][k, i] = v.lig_id.get(p["ligacao"], 0)
        mascara[k, 1:len(f) + 1] = True
    return {k: t.to(dispositivo) for k, t in T.items()}, mascara.to(dispositivo), n


def perda(modelo, T, mascara, n):
    cls, lem, arco, rd, rc = modelo(T["pal"], T["pre"], T["suf"], T["fmt"])
    valido_cab = torch.zeros_like(arco, dtype=torch.bool)
    valido_cab[:, :, 0] = True
    valido_cab |= mascara.unsqueeze(1)
    arco = arco.masked_fill(~valido_cab, -1e9)
    m = mascara
    l_cls = F.cross_entropy(cls[m], T["cls"][m])
    l_lem = F.cross_entropy(lem[m], T["lem"][m])
    l_arco = F.cross_entropy(arco[m], T["cab"][m])
    rot = modelo.rotulos(rd, rc, T["cab"])
    l_rot = F.cross_entropy(rot[m], T["lig"][m])
    return l_cls + l_lem + l_arco + l_rot


def exportar(modelo, v, meta_extra):
    p = {}
    sd = {k: t.detach().cpu().numpy().astype(np.float32) for k, t in modelo.state_dict().items()}
    p["bi_pal"] = sd["pal.weight"]
    p["bi_suf"] = sd["suf.weight"]
    p["bi_fmt"] = sd["fmt.weight"]
    camadas = modelo.lstm.num_layers
    for c in range(camadas):
        for sentido, suf in (("f", ""), ("r", "_reverse")):
            p["bi_lstm%d%s_Wi" % (c, sentido)] = sd["lstm.weight_ih_l%d%s" % (c, suf)]
            p["bi_lstm%d%s_Wh" % (c, sentido)] = sd["lstm.weight_hh_l%d%s" % (c, suf)]
            p["bi_lstm%d%s_b" % (c, sentido)] = sd["lstm.bias_ih_l%d%s" % (c, suf)] + sd["lstm.bias_hh_l%d%s" % (c, suf)]
    for nome in ("cls", "lem"):
        p["bi_%s_W1" % nome], p["bi_%s_b1" % nome] = sd[nome + ".0.weight"], sd[nome + ".0.bias"]
        p["bi_%s_W2" % nome], p["bi_%s_b2" % nome] = sd[nome + ".3.weight"], sd[nome + ".3.bias"]
    for nome in ("arco_dep", "arco_cab", "rot_dep", "rot_cab"):
        p["bi_%s_W" % nome], p["bi_%s_b" % nome] = sd[nome + ".weight"], sd[nome + ".bias"]
    p["bi_U_arco"], p["bi_u_arco"], p["bi_U_rot"] = sd["U_arco"], sd["u_arco"], sd["U_rot"]
    meta = dict(meta_extra)
    meta.update({"arquitetura": "biafim", "camadas_lstm": camadas, "vocab_biafim": v.palavras,
                 "sufixos": v.sufixos, "formatos": v.formatos, "classes": v.classes,
                 "regras_lema": v.regras, "ligacoes": v.ligacoes})
    return p, meta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--epocas", type=int, default=40)
    ap.add_argument("--lote", type=int, default=32)
    ap.add_argument("--semente", type=int, default=20261002)
    ap.add_argument("--limite-frases", type=int, default=0, help="só para testes rápidos")
    a = ap.parse_args()
    origem = conferir_origem(a.dados)
    random.seed(a.semente)
    np.random.seed(a.semente)
    torch.manual_seed(a.semente)
    rng = random.Random(a.semente)
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    pasta = Path(a.dados)
    treino, contr, inteiras = ler_conllu(pasta / "pt_bosque-ud-train.conllu")
    dev, _, _ = ler_conllu(pasta / "pt_bosque-ud-dev.conllu")
    teste, _, _ = ler_conllu(pasta / "pt_bosque-ud-test.conllu")
    if a.limite_frases:
        treino, dev, teste = treino[:a.limite_frases], dev[:a.limite_frases // 4], teste[:a.limite_frases // 4]
    vetores = af.carregar_vetores(np)
    if vetores[1] is None:
        raise SystemExit("Vetores de palavras ausentes em artefatos/vetores_pt")
    v = Vocab(treino, vetores)
    print("dispositivo %s; treino %d, dev %d, teste %d frases; vocabulário %d; ligações %d"
          % (dispositivo, len(treino), len(dev), len(teste), len(v.palavras), len(v.ligacoes)), flush=True)
    modelo = Biafim(v).to(dispositivo)
    otim = torch.optim.Adam([p for p in modelo.parameters() if p.requires_grad], lr=2e-3, betas=(0.9, 0.9))
    meta_base = {"contracoes": tabela_contracoes(contr, inteiras), "lemas_fixos": lemas_fixos(treino),
                 "minimo": af.MINIMO, "origem": origem}
    melhor, melhor_estado = -1.0, None
    for epoca in range(a.epocas):
        modelo.train()
        inicio = time.time()
        ordem = sorted(range(len(treino)), key=lambda i: len(treino[i]) + rng.random() * 4)
        lotes = [ordem[k:k + a.lote] for k in range(0, len(ordem), a.lote)]
        rng.shuffle(lotes)
        perdas = []
        for lote in lotes:
            T, mascara, n = lote_tensores([treino[i] for i in lote], v, dispositivo, 0.25, rng)
            l = perda(modelo, T, mascara, n)
            otim.zero_grad()
            l.backward()
            nn.utils.clip_grad_norm_(modelo.parameters(), 5.0)
            otim.step()
            perdas.append(l.item())
        las = avaliar_torch(modelo, dev, v, dispositivo)
        print("época %d perda %.3f dev UAS %.4f LAS %.4f classe %.4f (%.0fs)"
              % (epoca + 1, np.mean(perdas), las[0], las[1], las[2], time.time() - inicio), flush=True)
        if las[1] > melhor:
            melhor, melhor_estado = las[1], {k: t.detach().clone() for k, t in modelo.state_dict().items()}
    modelo.load_state_dict(melhor_estado)
    modelo.eval()
    pesos, meta = exportar(modelo, v, meta_base)

    # A execução em NumPy precisa reproduzir o torch antes de ser avaliada.
    numpy_ = af.AnalisadorBiafim.de_pesos(pesos, meta)
    diferenca = conferir_paridade(modelo, numpy_, dev[:20], v, dispositivo)
    print("paridade torch × NumPy: maior diferença de pontuação %.2e" % diferenca, flush=True)
    if diferenca > 1e-3:
        raise SystemExit("A execução em NumPy não reproduz o modelo treinado")

    meta["avaliacao"] = {"teste": avaliar_execucao(numpy_, teste), "dev": avaliar_execucao(numpy_, dev),
                         "observacao": "Tokenização de referência do treebank; pontuação incluída; "
                                       "árvore pela execução em NumPy (MST de Chu-Liu-Edmonds)."}
    meta["treino"] = {"semente": a.semente, "epocas": a.epocas, "lote": a.lote, "dispositivo": dispositivo,
                      "metodo": "BiLSTM 2×200 + atenção biafim (Dozat & Manning, 2017), PyTorch, do zero; "
                                "vetores de palavras do projeto como entrada fixa"}
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(saida / "modelo.npz", **{k: x.astype(np.float16) for k, x in pesos.items()})
    (saida / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    # Confere que o arquivo salvo (float16) carrega e passa no controle.
    carregado = af.AnalisadorFrases(saida)
    print("carregado: %s %s" % (carregado.disponivel, carregado.motivo), flush=True)
    print(json.dumps(meta["avaliacao"], ensure_ascii=False, indent=1))


@torch.no_grad()
def avaliar_torch(modelo, frases, v, dispositivo):
    modelo.eval()
    certo_u = certo_l = certo_c = total = 0
    for k in range(0, len(frases), 64):
        lote = frases[k:k + 64]
        T, mascara, n = lote_tensores(lote, v, dispositivo)
        cls, _, arco, rd, rc = modelo(T["pal"], T["pre"], T["suf"], T["fmt"])
        cab = arco.argmax(-1)
        rot = modelo.rotulos(rd, rc, cab).argmax(-1)
        m = mascara
        certo_u += (cab[m] == T["cab"][m]).sum().item()
        certo_l += ((cab[m] == T["cab"][m]) & (rot[m] == T["lig"][m])).sum().item()
        certo_c += (cls.argmax(-1)[m] == T["cls"][m]).sum().item()
        total += m.sum().item()
    return certo_u / total, certo_l / total, certo_c / total


@torch.no_grad()
def conferir_paridade(modelo, numpy_, frases, v, dispositivo):
    maior = 0.0
    for f in frases:
        formas = [p["forma"] for p in f]
        T, _, _ = lote_tensores([f], v, dispositivo)
        _, _, arco, _, _ = modelo(T["pal"], T["pre"], T["suf"], T["fmt"])
        a_np = numpy_.pontuacoes(formas)["arco"]
        maior = max(maior, float(np.abs(arco[0].cpu().numpy() - a_np).max()))
    return maior


def avaliar_execucao(analisador, frases):
    total = upos = lema = uas = las = 0
    for f in frases:
        palavras = analisador.analisar_formas([p["forma"] for p in f])
        for p, w in zip(f, palavras):
            total += 1
            upos += w.classe == p["classe"]
            lema += w.lema.lower() == p["lema"].lower()
            if w.pai == p["pai"]:
                uas += 1
                las += w.ligacao == p["ligacao"]
    return {"upos": round(upos / total, 4), "lema": round(lema / total, 4), "uas": round(uas / total, 4),
            "las": round(las / total, 4), "palavras": total, "frases": len(frases)}


if __name__ == "__main__":
    main()
