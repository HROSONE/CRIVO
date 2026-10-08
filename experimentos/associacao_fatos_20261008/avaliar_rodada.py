"""Compara dois checkpoints no painel novo após o orçamento completo.

Não treina, não seleciona pesos e não altera os critérios. O painel anterior
e a sonda anteriormente vista são apenas diagnósticos conhecidos.
"""
import argparse
import json
from pathlib import Path
import torch
from comum import ROOT, ANTERIOR, sha, escrever
from ajustar import carregar, coletar
from modelo import codificar, metricas
from tokenizers import Tokenizer

def diagnostico_preco():
    turnos=json.loads((ANTERIOR/'sondas_abertas.json').read_text())['casos'][-1]['turnos']
    def span(t,valor):
        a=turnos[t].index(str(valor));return {'turno':t,'inicio':a,'fim':a+len(str(valor)),'texto':str(valor)}
    pares=[(span(0,214),span(0,287)),(span(1,296),span(0,287)),
           (span(1,296),span(2,310)),(span(1,296),span(0,287))]
    return [dict(sessao='preco-conhecido',familia='diagnostico_conhecido',etapa=i,turnos=turnos[:i+1],
        operacao='comparar_custos',argumentos=[a,b,None],referente=None,hipotese=i==2,classe='custos')
        for i,(a,b) in enumerate(pares)]

def resumir(raw,lim):
    return {'bruto':metricas(raw),'limitado':metricas(lim),
        'limitado_executavel_errado':sum(r['execucao']['executavel'] and not r['resultado_correto'] for r in lim),
        'limitado_resultado_correto':sum(r['resultado_correto'] for r in lim)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--experimento',type=Path,required=True);args=p.parse_args()
    ex=args.experimento;congelado=json.loads((ex/'protocolo.json').read_text())
    for n,h in congelado['codigo_sha256'].items():assert sha(Path(__file__).parent/n)==h
    r=json.loads((ex/'candidato/relatorio.json').read_text())
    assert r['passos_completos']==600 and not r['teste_lido_no_treino']
    assert sha(ex/'candidato/pesos.pt')==r['pesos_sha256']
    manifest=json.loads((ex/'dados/manifesto.json').read_text())
    assert sha(ex/'dados/teste.json')==manifest['sha256']['teste']
    tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));tok.encode_special_tokens=True
    conjuntos={'novo':json.loads((ex/'dados/teste.json').read_text()),
               'anterior_conhecido':json.loads((ANTERIOR/'dados/teste.json').read_text()),
               'preco_conhecido':diagnostico_preco()}
    out=ex/'avaliacao';out.mkdir(exist_ok=False);results={}
    torch.set_num_threads(1)
    for label,pesos in [('anterior',ANTERIOR/'pesos_contextual/pesos.pt'),('ajustado',ex/'candidato/pesos.pt')]:
        m,state=carregar(pesos);assert state['tokenizer_sha256']==sha(ROOT/'artefatos/linguagem_profunda/tokenizer.json')
        results[label]={}
        for nome,es in conjuntos.items():
            itens=[codificar(tok,e) for e in es];raw,lim=coletar(m,itens,tok.token_to_id('<pad>'))
            escrever(out/f'{label}_{nome}_bruto.json',raw);escrever(out/f'{label}_{nome}_limitado.json',lim)
            results[label][nome]=resumir(raw,lim)
            print(label,nome,json.dumps(results[label][nome],ensure_ascii=False),flush=True)
    old=results['anterior']['novo']['limitado'];new=results['ajustado']['novo']['limitado']
    ganho=new['sessoes_completas']/new['sessoes']-old['sessoes_completas']/old['sessoes']
    regressao=results['ajustado']['anterior_conhecido']['limitado']['acuracia_contrato']-results['anterior']['anterior_conhecido']['limitado']['acuracia_contrato']
    util=min(f['acuracia'] for f in new['por_familia'].values())>=.8 and ganho>=.2 and regressao>=-.05
    escrever(out/'resumo.json',{'resultados':results,'ganho_sessoes_painel_novo':ganho,'delta_painel_anterior_conhecido':regressao,
        'atingiu_utilidade_local':util,'aprovado_para_chat':False,'avaliacao_independente':False,
        'pesos_anteriores_sha256':sha(ANTERIOR/'pesos_contextual/pesos.pt'),'pesos_ajustados_sha256':sha(ex/'candidato/pesos.pt'),
        'protocolo_sha256':sha(ex/'protocolo.json'),'pesos_ativos_preservados':sha(ROOT/'artefatos/linguagem_profunda/pesos.pt')==congelado['pesos_ativos_sha256'],
        'limites':'Mesmo decodificador nos dois checkpoints; compara ajuste de pesos/dados/orçamento em conjunto, sem ablação causal. Painel sintético autoral e gramática fechada; teste anterior e sonda são conhecidos. Nenhuma geração de conversa livre treinada nesta rodada.'})
    print('Avaliação conservada. Não há promoção automática.',flush=True)

if __name__=='__main__':main()
