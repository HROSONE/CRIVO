"""Ablacão de texto bruto versus nomes normalizados, fixada antes do teste."""
import argparse
import json
from pathlib import Path
import torch
from comum import ROOT, ANTERIOR, sha, escrever
from ajustar import carregar,coletar
from avaliar_rodada import resumir,diagnostico_preco
from modelo import codificar as bruto
from normalizar import codificar as normalizado
from tokenizers import Tokenizer

def main():
    p=argparse.ArgumentParser();p.add_argument('--experimento',type=Path,required=True);args=p.parse_args()
    ex=args.experimento;proto=json.loads((ex/'protocolo.json').read_text());ab=json.loads((ex/'ablation_preteste.json').read_text())
    for manifest in [proto,ab]:
        for n,h in manifest['codigo_sha256'].items():assert sha(Path(__file__).parent/n)==h
    for name in ['candidato','candidato_normalizado']:
        rel=json.loads((ex/name/'relatorio.json').read_text())
        assert rel['passos_completos']==600 and not rel['teste_lido_no_treino']
        assert rel['pesos_sha256']==sha(ex/name/'pesos.pt')
    manifest=json.loads((ex/'dados/manifesto.json').read_text())
    assert sha(ex/'dados/teste.json')==manifest['sha256']['teste']
    tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));tok.encode_special_tokens=True
    sets={'novo':json.loads((ex/'dados/teste.json').read_text()),
          'anterior_conhecido':json.loads((ANTERIOR/'dados/teste.json').read_text()),'preco_conhecido':diagnostico_preco()}
    out=ex/'avaliacao_ablation';out.mkdir(exist_ok=False);res={};torch.set_num_threads(1)
    initial=ANTERIOR/'pesos_contextual/pesos.pt'
    branches=[('anterior_bruto',initial,bruto),('anterior_normalizado',initial,normalizado),
              ('ajustado_bruto',ex/'candidato/pesos.pt',bruto),('ajustado_normalizado',ex/'candidato_normalizado/pesos.pt',normalizado)]
    for label,checkpoint,encoder in branches:
        m,meta=carregar(checkpoint);assert meta['tokenizer_sha256']==sha(ROOT/'artefatos/linguagem_profunda/tokenizer.json')
        res[label]={}
        for nome,es in sets.items():
            itens=[encoder(tok,e) for e in es];raw,lim=coletar(m,itens,tok.token_to_id('<pad>'))
            escrever(out/f'{label}_{nome}_bruto.json',raw);escrever(out/f'{label}_{nome}_limitado.json',lim)
            res[label][nome]=resumir(raw,lim);print(label,nome,json.dumps(res[label][nome],ensure_ascii=False),flush=True)
    criterios={}
    for arm in ['bruto','normalizado']:
        prev=res['anterior_'+arm];new=res['ajustado_'+arm];a=prev['novo']['limitado'];b=new['novo']['limitado']
        delta=b['sessoes_completas']/b['sessoes']-a['sessoes_completas']/a['sessoes']
        regress=new['anterior_conhecido']['limitado']['acuracia_contrato']-prev['anterior_conhecido']['limitado']['acuracia_contrato']
        util=min(f['acuracia'] for f in b['por_familia'].values())>=.8 and delta>=.2 and regress>=-.05
        criterios[arm]={'ganho_sessoes_novas_sobre_mesma_representacao':delta,'delta_anterior_conhecido':regress,'atingiu_utilidade_local':util}
    escrever(out/'resumo.json',{'resultados':res,'criterios':criterios,'aprovado_para_chat':False,'avaliacao_independente':False,
        'protocolo_sha256':sha(ex/'protocolo.json'),'ablation_preteste_sha256':sha(ex/'ablation_preteste.json'),
        'pesos_ativos_preservados':sha(ROOT/'artefatos/linguagem_profunda/pesos.pt')==proto['pesos_ativos_sha256'],
        'limites':'Quatro condições exibidas, incluindo efeito imediato da normalização sem treino. Bancos e autoria sintéticos compartilhados. Código de gramática e normalização auxilia a rede. Não constitui raciocínio geral ou geração de conversa; não seleciona pesos pelo teste.'})
    print('Todas as condições conservadas; nenhuma promoção automática.',flush=True)

if __name__=='__main__':main()
