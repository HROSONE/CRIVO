"""Comparação com os contratos independentes anteriores, sem alterar pesos.

Identifica quantos turnos chegaram à geração neural de fato. Acerto do motor
factual/cadastrado não pode ser atribuído ao Transformer. Nunca ativa o modelo.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from avaliar_dialogo_real import avaliar,assinatura_casos
from crivo import Crivo


def comparar(pasta,saida):
    pasta=Path(pasta).resolve()
    nome='pesos.pt' if (pasta/'pesos.pt').is_file() else 'pesos_numpy.npz'
    class Candidato(Crivo):
        def __init__(self):super().__init__(modelo_linguagem=str(pasta))
    baseline=avaliar(Crivo);candidato=avaliar(Candidato)
    neural=[t for c in candidato['casos'] for t in c['turnos'] if t['id']=='conversa:neural_livre']
    r=dict(versao=1,contrato_sha256=assinatura_casos(),pesos_sha256=hashlib.sha256((pasta/nome).read_bytes()).hexdigest(),
        baseline=baseline,candidato=candidato,respostas_do_gerador=len(neural),
        acertos_do_gerador=sum(t['passou'] for t in neural),
        regressao=candidato['acertos']<baseline['acertos'],
        contrato_completo=candidato['acertos']==candidato['mensagens'],
        promocao_automatica=False,
        limites=['Acertos do motor factual não são acertos da geração neural.',
                 'Os contratos não cobrem toda conversa aberta.',
                 'Amostras livres e alegações factuais continuam exigindo revisão.'])
    Path(saida).parent.mkdir(parents=True,exist_ok=True)
    Path(saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:{n:r[k][n] for n in ('mensagens','acertos','dialogos_completos')} for k in ('baseline','candidato')}))
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modelo',required=True);p.add_argument('--saida',required=True)
    a=p.parse_args();comparar(a.modelo,a.saida)
