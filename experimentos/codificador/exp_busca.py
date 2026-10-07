import sys, json, math, torch
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts'); sys.path.insert(0, sys.argv[2])
import treinar_codificador_sentido as tcs
from pathlib import Path
tcs.RAIZ = Path(__file__).resolve().parents[2]
from treinar_codificador_sentido import construir, codificar, ids_texto, texto_fato, validacao
from pontuador_frases import BPE
from crivo import Crivo
from leitura_ficha import busca_aprendida
pasta = sys.argv[1]
m, cfg = construir(pasta); m.eval(); bpe = BPE(pasta + '/tokenizer.json')
comp = Crivo().compositor
busca = busca_aprendida(comp)
fatos = [(a, i, texto_fato(f)) for a, it in sorted(comp.itens.items()) for i, f in enumerate(it.get('fatos', []))]
pos = {(a, i): j for j, (a, i, _) in enumerate(fatos)}
with torch.no_grad():
    vf = torch.cat([codificar(m, [ids_texto(bpe, t, 'fato') for _, _, t in fatos[s:s+128]], torch) for s in range(0, len(fatos), 128)])
val = [(q, a, i) for q, a, i in validacao(comp) if (a, i) in pos]
regs = []
with torch.no_grad():
    for q, a, i in val:
        vq = codificar(m, [ids_texto(bpe, q, 'pergunta')], torch)[0]
        sims = vf @ vq
        ach = busca.buscar(q, k=10)
        cand = {(x, y): p for p, x, y in ach}
        for j in sims.topk(10).indices.tolist():
            cand.setdefault(fatos[j][:2], 1e-4)
        regs.append(((a, i), [(c, p, float(sims[pos[c]])) for c, p in cand.items()]))
for w in (0, 2, 5, 10, 20, 40):
    f1 = a1 = 0
    for alvo, cs in regs:
        best = max(cs, key=lambda c: math.log(c[1]) + w * c[2])
        f1 += best[0] == alvo; a1 += best[0][0] == alvo[0]
    print('w=%-3d fato@1 %d ficha@1 %d / %d' % (w, f1, a1, len(regs)))
