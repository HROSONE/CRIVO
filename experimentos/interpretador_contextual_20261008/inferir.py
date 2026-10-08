"""Inspecionar o candidato próprio; não o integra ao chat.

python inferir.py --pesos pacote/pesos.pt --tokenizer pacote/tokenizer.json
                 --entrada conversa.json
conversa.json: lista de falas do usuário, sem alvos de avaliação.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import torch
from modelo import Interprete, codificar, lote, proposta, executar
from decodificar_limitado import proposta_limitada


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pesos',type=Path,required=True)
    parser.add_argument('--tokenizer',type=Path,required=True);parser.add_argument('--entrada',type=Path,required=True)
    parser.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parents[2]);args=parser.parse_args()
    torch.set_num_threads(1);sys.path.insert(0,str(args.raiz))
    from linguagem_profunda import Configuracao,LinguagemProfunda
    from tokenizers import Tokenizer
    state=torch.load(args.pesos,map_location='cpu',weights_only=True)
    assert hashlib.sha256(args.tokenizer.read_bytes()).hexdigest()==state['tokenizer_sha256']
    m=Interprete(LinguagemProfunda(Configuracao(**state['config'])),'contextual')
    m.load_state_dict(state['modelo']);m.eval()
    tok=Tokenizer.from_file(str(args.tokenizer));tok.encode_special_tokens=True
    turnos=json.loads(args.entrada.read_text())
    if not isinstance(turnos,list) or not turnos or not all(isinstance(t,str) for t in turnos):
        raise ValueError('Entrada deve ser uma lista de falas.')
    item=codificar(tok,dict(turnos=turnos,argumentos=[None,None,None],referente=None))
    with torch.no_grad():
        x,l=lote([item],tok.token_to_id('<pad>'));logits=m(x,l)
        a=proposta(item,logits,0);b=proposta_limitada(item,logits,0)
    print(json.dumps({'aprovado_para_chat':False,'parametros':sum(p.numel() for p in m.parameters()),
        'bruto':{'proposta':a,'execucao':executar(a)},
        'limitado':{'proposta':b,'execucao':executar(b)},
        'limite':'Pode selecionar argumentos incorretos mesmo com alta confiança. Execução aritmética válida não certifica interpretação. Não é um gerador de conversa livre.'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
