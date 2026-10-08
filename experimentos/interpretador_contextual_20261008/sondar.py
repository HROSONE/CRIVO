"""Coleta de diálogo aberto e transferência adicional, sem treinar ou pontuar automaticamente."""
import argparse
import json
from pathlib import Path
import sys
import torch
from corpus import escrever
from modelo import Interprete,codificar,lote,proposta,executar
from decodificar_limitado import proposta_limitada


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--raiz',type=Path,required=True)
    parser.add_argument('--experimento',type=Path,required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.raiz));from linguagem_profunda import carregar
    from crivo import Crivo
    p=args.experimento;destino=p/'sondas_respostas.json'
    if destino.exists():raise ValueError('Não sobrescrever coleta.')
    torch.set_num_threads(1);corpo,tok,_=carregar(args.raiz/'artefatos/linguagem_profunda')
    estado=torch.load(p/'contextual/pesos.pt',map_location='cpu',weights_only=True)
    m=Interprete(corpo,'contextual');m.load_state_dict(estado['modelo']);m.eval()
    casos=json.loads((p/'sondas_abertas.json').read_text())['casos'];out=[]
    with torch.no_grad():
        for c in casos:
            bot=Crivo();hist=[];s={'id':c['id'],'rubrica':c['rubrica'],'turnos':[]};out.append(s)
            for texto in c['turnos']:
                hist.append(texto)
                e={'turnos':hist,'argumentos':[None,None,None],'referente':None}
                ident,resposta=bot.responder(texto)
                r={'texto':texto,'crivo_atual':{'id':ident,'resposta':resposta}}
                try:
                    item=codificar(tok,e);x,l=lote([item],tok.token_to_id('<pad>'));ls=m(x,l)
                    raw=proposta(item,ls,0);limit=proposta_limitada(item,ls,0)
                    r.update(candidato_bruto=raw,execucao_bruta=executar(raw),
                             candidato_limitado=limit,execucao_limitada=executar(limit))
                except ValueError as exc:
                    r['candidato_recusa']=str(exc)
                s['turnos'].append(r);escrever(destino,out)
                print(c['id'],len(s['turnos']),flush=True)


if __name__=='__main__':main()
