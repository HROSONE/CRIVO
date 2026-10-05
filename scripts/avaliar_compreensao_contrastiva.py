"""Avalia alvos contrastantes e geração livre separadamente; nunca treina."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.compreensao_contrastiva import gerar, medir, geracao_livre, assinatura


def avaliar(modelo_path, split='validacao'):
    import torch
    from linguagem_profunda import carregar
    torch.set_num_threads(2)
    modelo,t,e=carregar(modelo_path)
    pares=gerar(split)
    selecionados=[]
    for familia in sorted({p['familia'] for p in pares}):
        ps=sorted((p for p in pares if p['familia']==familia),key=lambda p:hashlib.sha256(p['id'].encode()).hexdigest())
        selecionados.extend(ps[:2])
    return dict(split=split,passo=e['passo'],
        pesos_sha256=hashlib.sha256((Path(modelo_path)/'pesos.pt').read_bytes()).hexdigest(),
        ranking=medir(modelo,t,pares),geracao=geracao_livre(modelo,t,selecionados),
        painel_livre_sha256=assinatura(selecionados),
        limite='Cenários sintéticos controlados, não certificação de conversa geral; teste só após congelar o candidato.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modelo',required=True);p.add_argument('--saida',required=True)
    p.add_argument('--split',choices=['validacao','teste'],default='validacao')
    a=p.parse_args();r=avaliar(a.modelo,a.split)
    Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(split=r['split'],passo=r['passo'],ranking=r['ranking'],
        livres_exatas=r['geracao']['exatas'],livres_total=r['geracao']['casos']),ensure_ascii=False))
