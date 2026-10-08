import os
"""Controles congelados: publica somente agregados, nunca perguntas ou erros."""
import sys,json,time,hashlib
from pathlib import Path
import torch
ROOT=Path(os.environ['CRIVO_REPO']);OUT=Path(os.environ['CRIVO_SAIDA'])
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(OUT),str(Path(__file__).resolve().parent)]
from continuar_leitor import carregar
from scripts.treinar_leitor_transformer import lote_tensores
from diagnosticar_cabeca import metricas

def main():
    torch.set_num_threads(2)
    from crivo import Crivo
    comp=Crivo().compositor
    candidates={'original':ROOT/'experimentos/pesos_base/leitor_transformer','cabeca':OUT/'candidato_cabeca'}
    if (OUT/'candidato_duas_camadas/pesos_numpy.npz').exists():candidates['duas_camadas']=OUT/'candidato_duas_camadas'
    # Compromisso dos candidatos anterior à primeira leitura dos controles.
    manifest={k:hashlib.sha256((v/'pesos_numpy.npz').read_bytes()).hexdigest() for k,v in candidates.items()}
    (OUT/'candidatos_antes_controle.json').write_text(json.dumps(manifest,indent=2)+'\n')
    report={'protocolo':'Pesos congelados antes de abrir controles; avaliação só em agregados; não usados para otimização','sha256':manifest,'conjuntos':{},'aprovado_chat':False}
    for name,path in [('v1',ROOT/'avaliacoes/leitura_ficha_v1/teste.json'),('v2',ROOT/'avaliacoes/leitura_ficha_v2/teste.json')]:
        cases=json.loads(path.read_text())['casos']
        available=[c for c in cases if c['assunto'] in comp.itens]
        groups={}
        for key,folder in candidates.items():
            m,bpe,_=carregar(folder,'cpu');m.eval();pred=[]
            with torch.no_grad():
                for c in available:
                    facts=[f['texto'] for f in comp.itens[c['assunto']]['fatos']]
                    ids,u=lote_tensores([(c['pergunta'],f) for f in facts],bpe,256,'cpu')
                    pred.append(m(ids,u).numpy())
            groups[key]=metricas(pred,available)
            print(name,key,groups[key],flush=True)
        report['conjuntos'][name]={'casos':len(cases),'avaliados':len(available),'metricas':groups}
        (OUT/'controle_congelado.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
