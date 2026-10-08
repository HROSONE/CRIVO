"""Inspeção local dos candidatos, sem registrar conversa ou ativar chat."""
import argparse
import json
from pathlib import Path
import torch
from comum import ROOT,sha
from ajustar import carregar
from modelo import codificar as bruto,lote,proposta,executar
from normalizar import codificar as normalizado
from decodificar import proposta_limitada
from tokenizers import Tokenizer

def main():
    p=argparse.ArgumentParser();p.add_argument('--pesos',type=Path,required=True);p.add_argument('--entrada',type=Path,required=True)
    p.add_argument('--normalizado',action='store_true');a=p.parse_args();torch.set_num_threads(1)
    m,state=carregar(a.pesos);m.eval();t=ROOT/'artefatos/linguagem_profunda/tokenizer.json'
    assert sha(t)==state['tokenizer_sha256'];tok=Tokenizer.from_file(str(t));tok.encode_special_tokens=True
    turnos=json.loads(a.entrada.read_text())
    if not isinstance(turnos,list) or not turnos or not all(isinstance(x,str) for x in turnos):raise ValueError('Entrada deve ser uma lista de falas.')
    encoder=normalizado if a.normalizado else bruto
    item=encoder(tok,{'turnos':turnos,'argumentos':[None]*3,'referente':None})
    with torch.no_grad():
        x,l=lote([item],tok.token_to_id('<pad>'));ls=m(x,l);raw=proposta(item,ls,0);limited=proposta_limitada(item,ls,0)
    print(json.dumps({'aprovado_para_chat':False,'normalizado':a.normalizado,'simbolos_locais':item.get('simbolos_locais'),
        'bruto':{'proposta':raw,'execucao':executar(raw)},'limitado':{'proposta':limited,'execucao':executar(limited)},
        'limites':'Pode confundir fatos e entidades. Não é redação livre; índices de custos são propostas em relação à consulta. Sem integração no chat.'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
