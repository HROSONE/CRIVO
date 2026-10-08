"""Preserva respostas e contexto autogerado; não certifica semântica por CE."""
import argparse
import json
from pathlib import Path
import time
import torch
from rodada import ROOT,sha,escrever,codificar,avaliar_perda
from linguagem_profunda import carregar,fonte_dialogo,segmentos_dialogo,ESPECIAIS

def coletar(m,tok,casos):
    outputs=[];m.eval()
    for caso in casos:
        hist=[];rows=[]
        for i,texto in enumerate(caso['turnos']):
            prompt=fonte_dialogo(tok,texto,hist,m.config.contexto)
            segmentos,atual=segmentos_dialogo(tok,texto,hist);mantidos=0;usados=len(atual)
            for segmento in reversed(segmentos):
                if usados+len(segmento)>m.config.contexto:break
                mantidos+=1;usados+=len(segmento)
            inicio=time.monotonic()
            ids,terminou=m.gerar(prompt,tok.token_to_id('<fim>'),max_tokens=70,temperatura=0.,
                proibidos=[tok.token_to_id(t) for t in ESPECIAIS[:-1]])
            resposta=tok.decode(ids)
            row={'etapa':i,'entrada':texto,'resposta':resposta,'terminou':terminou,'tokens':len(ids),
                 'tokens_prompt':len(prompt),'falas_historico_disponiveis':len(hist),'falas_historico_mantidas':mantidos,
                 'tokens_prefixo_fora_contexto_no_fim':max(0,len(prompt)+len(ids)-1-m.config.contexto),
                 'segundos':round(time.monotonic()-inicio,3)}
            rows.append(row);hist.extend([{'papel':'usuario','texto':texto},{'papel':'assistente','texto':resposta}])
            print(caso['id'],i,json.dumps(row,ensure_ascii=False),flush=True)
        outputs.append({'id':caso['id'],'rubrica':caso['rubrica'],'respostas':rows,'historico':'autogerado, com limite de contexto do motor próprio'})
    return outputs

def main():
    p=argparse.ArgumentParser();p.add_argument('experimento',type=Path);args=p.parse_args();ex=args.experimento
    proto=json.loads((ex/'protocolo.json').read_text());code=Path(__file__).parent
    assert sha(code/'rodada.py')==proto['codigo_treinador_sha256']
    assert sha(code/'sondas_novas.json')==proto['sondas_novas_sha256']
    rel=json.loads((ex/'candidato/relatorio.json').read_text());assert rel['passos_completos']==600 and not rel['teste_lido_no_treino']
    assert sha(ex/'candidato/pesos.pt')==rel['pesos_sha256']
    manifest=json.loads((ex/'dados/manifesto.json').read_text());assert sha(ex/'dados/teste.json')==manifest['sha256']['teste']
    exemplos=json.loads((ex/'dados/teste.json').read_text());casos=json.loads((code/'sondas_novas.json').read_text())['casos']
    out=ex/'avaliacao';out.mkdir(exist_ok=False);torch.set_num_threads(1);results={}
    for label,path in [('anterior',ROOT/'artefatos/linguagem_profunda'),('ajustado',ex/'candidato')]:
        m,tok,state=carregar(path);itens=[codificar(tok,e) for e in exemplos]
        ce=avaliar_perda(m,itens,tok.token_to_id('<pad>'));rows=coletar(m,tok,casos)
        escrever(out/(label+'.json'),rows)
        results[label]={'ce_painel_autoral_reservado':ce,'respostas':sum(len(r['respostas']) for r in rows),
            'respostas_com_fim':sum(t['terminou'] for r in rows for t in r['respostas']),
            'descricao':'CE usa histórico de referência; sondas usam o próprio histórico. Término e CE não medem coerência/raciocínio.'}
    escrever(out/'resumo.json',{'resultados':results,'aprovado_para_chat':False,'avaliacao_independente':False,
        'pesos_ativos_preservados':sha(ROOT/'artefatos/linguagem_profunda/pesos.pt')==proto['pesos_ativos_sha256'],
        'limites':'Corpus pequeno/existente e cinco sessões autorais. Leitura semântica manual necessária; nenhum score automático certifica conversa livre. fonte_dialogo pode descartar histórico para caber em 256 tokens.'})

if __name__=='__main__':main()
