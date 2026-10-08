import os
"""Validação do combinador com cabeças próprias treinadas sem o assunto externo."""
import sys,json,random
from pathlib import Path
import numpy as np
import torch
ROOT=Path(os.environ['CRIVO_REPO']);OUT=Path(os.environ['CRIVO_SAIDA'])
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(OUT),str(Path(__file__).resolve().parent)]
from diagnosticar_cabeca import treinar as ajustar_cabeca
from continuar_leitor import carregar
from treinar_leitura_ficha import exemplos,treinar,propostas,politica,limiares,contar,regra,_entregues,precisao
from leitura_ficha import LeituraFicha,TRACOS

def resumo(lines):
    a,b=limiares(lines);aa,bb,cc=(contar(g) for g in politica(lines,a,b))
    return {'limiar':a,'limiar_aproximar':b,'validacao_cruzada_por_assunto':{'modelo_afirma':aa,'modelo_aproxima':bb,'modelo_cala':cc},'controle':{'aprovado':False}}

def main():
    torch.set_num_threads(2)
    from crivo import Crivo
    comp=Crivo().compositor
    raw=json.loads((ROOT/'dados/leitura_ficha_tutor.json').read_text())['casos']
    raw=[c for c in raw if c['assunto'] in comp.itens]
    index={c['pergunta']:i for i,c in enumerate(raw)}
    path=OUT/'tracos_tutor.json'
    if path.exists():cases=json.loads(path.read_text())
    else:
        cases,ignored=exemplos(comp,LeituraFicha(comp,caminho_modelo='/nao/existe'))
        path.write_text(json.dumps(cases,ensure_ascii=False)+'\n')
        print('casos elegíveis',len(cases),'ignorados',ignored,flush=True)
    z=np.load(OUT/'ocultos_tutor.npz',allow_pickle=False)
    xs=[torch.from_numpy(z['x'+str(i)]) for i in range(len(raw))]
    m,_,_=carregar(ROOT/'experimentos/pesos_base/leitor_transformer','cpu')
    w0=m.cabeca.weight.detach()[0].numpy().copy();b0=float(m.cabeca.bias.detach()[0])
    subjects=sorted({c['assunto'] for c in raw});random.Random(20261008).shuffle(subjects)
    fold={s:i%5 for i,s in enumerate(subjects)}
    sel=json.loads((OUT/'controle_cabeca.json').read_text())['selecao']
    outputs={k:[] for k in ['sem','original','adaptado']}
    for k in range(5):
        train=[i for i,c in enumerate(raw) if fold[c['assunto']]!=k]
        w,b=ajustar_cabeca(xs,raw,train,w0,b0,sel[k]['l2'])
        for name in outputs:
            enriched=[]
            for c in cases:
                i=index[c['pergunta']]
                ps=torch.sigmoid(xs[i]@(torch.tensor(w0) if name=='original' else w)+(b0 if name=='original' else b)).tolist() if name!='sem' else None
                enriched.append(dict(c,x=[list(x)+([ps[j]] if ps else []) for j,x in enumerate(c['x'])]))
            tr=[c for c in enriched if fold[c['assunto']]!=k];va=[c for c in enriched if fold[c['assunto']]==k]
            cw=treinar(tr)
            outputs[name]+=propostas(va,lambda x:float(1/(1+np.exp(-(np.array(x)@cw)))))
        print('combinador bloco',k,'feito',flush=True)
    result={k:resumo(lines) for k,lines in outputs.items()}
    print('PIPELINE',json.dumps(result,ensure_ascii=False),flush=True)
    (OUT/'controle_pipeline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    # Modelo final em todos os dados de supervisão: não usar para alegar CV.
    cm,_,_=carregar(OUT/'candidato_cabeca','cpu')
    final=[]
    for c in cases:
        ps=torch.sigmoid(cm.cabeca(xs[index[c['pergunta']]])).squeeze(-1).detach().tolist()
        final.append(dict(c,x=[list(x)+[ps[j]] for j,x in enumerate(c['x'])]))
    weights=treinar(final)
    final_meta=dict(result['adaptado'],versao=1,tracos=list(TRACOS)+['transformer'],pesos=[round(float(v),5) for v in weights],dados={'casos':len(cases),'supervisao':'tutor; leitor treinado dentro de cada bloco por assunto'},comparacao=result)
    (OUT/'combinador_cabeca.json').write_text(json.dumps(final_meta,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
