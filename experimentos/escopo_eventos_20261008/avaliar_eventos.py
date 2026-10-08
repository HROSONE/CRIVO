"""Avaliação única depois dos dois treinos; não seleciona checkpoints."""
import argparse
import json
from pathlib import Path
import torch
from base import ROOT,ASSOC,CONTEXT,INICIAL,escrever,sha
from rede_eventos import carregar,coletar,medidas
from normalizacao import codificar
from normalizar import codificar as codificar_anterior
from tokenizers import Tokenizer

def main():
    p=argparse.ArgumentParser();p.add_argument('--laboratorio',type=Path,required=True);a=p.parse_args()
    lab=a.laboratorio;out=lab/'avaliacao';out.mkdir(exist_ok=False)
    torch.set_num_threads(1);torch.manual_seed(20261012)
    protocolo=json.loads((lab/'protocolo.json').read_text());manifesto=json.loads((lab/'dados/manifesto.json').read_text())
    for nome,sig in protocolo['codigo'].items():assert sha(Path(__file__).parent/nome)==sig
    for nome,sig in manifesto['sha256'].items():assert sha(lab/'dados'/(nome+'.json'))==sig
    for braco in ['controle','eventos']:
        r=json.loads((lab/braco/'relatorio.json').read_text());assert r['passos_completos']==600
        assert sha(lab/braco/'pesos.pt')==r['pesos_sha256']
    tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));tok.encode_special_tokens=True;pad=tok.token_to_id('<pad>')
    paineis={'novo':lab/'dados/teste.json','associacao_conhecida':ASSOC/'dados/teste.json','contextual_conhecido':CONTEXT/'dados/teste.json'}
    resumo={};rasgos={}
    condicoes=[('anterior_preparo_antigo',INICIAL,codificar_anterior),('anterior_preparo_novo',INICIAL,codificar),
               ('controle',lab/'controle/pesos.pt',codificar),('eventos',lab/'eventos/pesos.pt',codificar)]
    for nome,cp,enc in condicoes:
        m,_=carregar(cp);resumo[nome]={};rasgos[nome]={}
        for painel,path in paineis.items():
            exemplos=json.loads(path.read_text());items=[enc(tok,e) for e in exemplos]
            raw,lim=coletar(m,items,pad)
            for tipo,rows in [('bruto',raw),('limitado',lim)]:
                escrever(out/f'{nome}_{painel}_{tipo}.json',rows)
                resumo[nome][painel+'_'+tipo]=medidas(rows)
            if painel=='novo':
                rasgos[nome]={ev:{'n':len(xs),'erros':sum(not x['contrato'] for x in xs),
                    'escopo_errado':sum(not x['escopo'] for x in xs),'argumentos_errados':[sum(not x['argumentos'][i] for x in xs) for i in range(3)]}
                    for ev in ['declaracao','correcao','hipotese','retorno','consulta','confirmacao']
                    for xs in [[r for r in lim if r['evento']==ev]]}
            print(json.dumps({'condicao':nome,'painel':painel,'n':len(lim),'corretos':sum(r['contrato'] for r in lim),'sessoes':resumo[nome][painel+'_limitado']['sessoes_completas']}),flush=True)
    anterior=resumo['anterior_preparo_novo'];criterios={}
    for nome in ['controle','eventos']:
        r=resumo[nome]['novo_limitado'];b=anterior['novo_limitado']
        eventos_ok=all(r['por_evento'][ev]['acuracia_contrato']>=.80 for ev in ['correcao','hipotese','retorno','confirmacao'])
        familias_ok=all(v['acuracia']>=.80 for v in r['por_familia'].values())
        aumento=r['sessoes_completas']/r['sessoes']-b['sessoes_completas']/b['sessoes']
        queda=max(anterior[p+'_limitado']['acuracia_contrato']-resumo[nome][p+'_limitado']['acuracia_contrato'] for p in ['associacao_conhecida','contextual_conhecido'])
        criterios[nome]={'eventos_criticos_80pct':eventos_ok,'familias_80pct':familias_ok,
            'aumento_sessoes_completas_pp':100*aumento,'queda_maxima_paineis_conhecidos_pp':100*queda,
            'passou_criterio_sintetico':eventos_ok and familias_ok and aumento>=.20 and queda<=.05,
            'aprovado_para_chat':False}
    escrever(out/'resumo.json',{'resultados':resumo,'criterios':criterios,'diagnostico':rasgos,
        'protocolo_sha256':sha(lab/'protocolo.json'),'limites':'Uma semente; textos autorais de gramática finita; mesmos tipos de trajetória entre partições; preço/posse apenas. Interpretação neural + cópia literal + executor determinístico. Sem teste independente de conversa livre. Controle e eventos diferem conjuntamente em peso de escopo e perda auxiliar; não isolam as duas causas.',
        'aprovado_para_chat':False,'avaliacao_de_redacao_livre':False})
    assert sha(ROOT/'artefatos/linguagem_profunda/pesos.pt')==protocolo['pesos_ativos_sha256']

if __name__=='__main__':main()
