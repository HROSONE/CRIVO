"""Gera respostas próprias para inspeção; não ativa o chat do produto."""
import argparse
import json
from pathlib import Path
import torch
from rodada import ROOT
from linguagem_profunda import carregar
from avaliar import coletar

def main():
    p=argparse.ArgumentParser();p.add_argument('--modelo',type=Path,required=True);p.add_argument('--entrada',type=Path,required=True)
    a=p.parse_args();turnos=json.loads(a.entrada.read_text())
    if not isinstance(turnos,list) or not turnos or not all(isinstance(x,str) for x in turnos):raise ValueError('Entrada deve ser uma lista de falas.')
    torch.set_num_threads(1);m,tok,_=carregar(a.modelo)
    rows=coletar(m,tok,[{'id':'inspecao','turnos':turnos,'rubrica':'Inspeção autoral, sem aprovação automática.'}])
    print(json.dumps({'aprovado_para_chat':False,'sessoes':rows,
        'limite':'Candidato com poucos dados. Pode gerar texto incoerente ou inventar fatos. Histórico pode ser descartado pelo limite de 256 tokens.'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
