import sys, json, torch
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts')
sys.path.insert(0, sys.argv[2])
from treinar_codificador_sentido import construir
from pontuador_frases import BPE
pasta = sys.argv[1]
m, cfg = construir(pasta); bpe = BPE(pasta + '/tokenizer.json'); e = bpe.especiais
print(list(e)[:20])
for prompt in ["A capital do Brasil é", "O Sol é uma estrela que", "Pelé foi um jogador de futebol brasileiro que"]:
    ids = [e['<documento>']] + bpe.codificar(prompt)
    out = m.gerar(ids, e['<fim>'], max_tokens=30, temperatura=0.7, top_k=30)
    print(prompt, '→', bpe.decodificar(out) if hasattr(bpe, 'decodificar') else out)
