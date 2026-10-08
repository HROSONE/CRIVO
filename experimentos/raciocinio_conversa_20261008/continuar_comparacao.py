"""Completa o painel interrompido; adapta só o formato do arquivo modular.

O NPZ modular não contém o campo meta esperado por GeradorNumpy. Copiamos
os arrays intactos para uma pasta temporária com a configuração já publicada.
Não treinamos nem promovemos estes pesos, nem alteramos a coleta anterior.
"""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time
import numpy as np
from comparar_checkpoints import CASOS, PASTA, ROOT, GeradorNumpy


def main():
    out = PASTA / 'comparacao_modular_bruta.json'
    if out.exists():
        raise SystemExit('Preserve a execução anterior.')
    origem = ROOT / 'experimentos/raciocinio_generativo/pesos_modulares'
    meta = json.loads((origem / 'meta.json').read_text())
    with tempfile.TemporaryDirectory(prefix='crivo-formato-') as pasta:
        pasta = Path(pasta)
        shutil.copyfile(origem / 'tokenizer.json', pasta / 'tokenizer.json')
        cfg = dict(meta['base']['config'], passo=meta['treino']['checkpoint'])
        cfg['tokenizer_sha256'] = hashlib.sha256((pasta / 'tokenizer.json').read_bytes()).hexdigest()
        with np.load(origem / 'pesos_numpy.npz') as p:
            arrays = {k: p[k] for k in p.files}
        np.savez(pasta / 'pesos_numpy.npz', meta=np.array(json.dumps(cfg)), **arrays)
        g = GeradorNumpy(pasta)
        r = dict(modelo='modular_17m', parametros=sum(v.size for v in arrays.values()),
                 pesos_sha256=hashlib.sha256((origem / 'pesos_numpy.npz').read_bytes()).hexdigest(),
                 adaptacao='Mesmos arrays; configuração externa copiada para meta do executor.', casos=[])
        for cid, perguntas in CASOS:
            hist = []; caso = dict(id=cid, turnos=[]); r['casos'].append(caso)
            for pergunta in perguntas:
                inicio = time.monotonic()
                try:
                    s = g.responder(pergunta, hist, max_tokens=64, temperatura=0.)
                except Exception as exc:
                    s = dict(erro=type(exc).__name__, mensagem=str(exc))
                s.update(pergunta=pergunta, segundos=round(time.monotonic()-inicio, 3))
                caso['turnos'].append(s)
                hist.extend([dict(papel='usuario', texto=pergunta),
                             dict(papel='assistente', texto=s.get('texto', ''))])
                out.write_text(json.dumps(r, ensure_ascii=False, indent=2)+'\n')
                print(cid, json.dumps(s, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
