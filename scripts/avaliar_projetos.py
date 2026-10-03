"""Avaliar módulos reservados ou conferir referências autorais do laboratório."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from laboratorio_projetos import projetos, verificar_projeto, avaliar_projeto, node_isolado, CATALOGO
from programacao_neural import GeradorProgramacao, digest


def executar(saida, modelo=None, tsc=None, referencias=False, reparos=2):
    if not node_isolado():
        raise RuntimeError('Node isolado indisponível; não executa projetos no host nem simula APIs no QuickJS')
    gerador = None if referencias else GeradorProgramacao(modelo)
    resultados=[]
    for split in (('treino','validacao','teste') if referencias else ('teste',)):
        for p in projetos(split):
            if referencias:
                arquivos={a['caminho']:a['referencia'] for a in p['arquivos']}
                r=dict(id=p['id'], verificacao=verificar_projeto(p,arquivos,p['desenvolvimento']+p['reservados'],tsc))
            else:
                r=avaliar_projeto(gerador,p,tsc,reparos)
            resultados.append(r)
            print(json.dumps(dict(id=p['id'],final=r.get('acerto_final',r.get('verificacao',{}).get('funcional')))),flush=True)
    relatorio=dict(versao=1,catalogo_sha256=digest(CATALOGO),referencias=referencias,resultados=resultados,
        certificado_senior=False,ativacao_automatica=False,
        limite='8 famílias autorais de miniprojetos; 4 reservadas; nenhuma revisão independente')
    if not referencias:
        relatorio.update(pesos_sha256=digest(Path(modelo)/'pesos.pt'),tokenizer_sha256=digest(Path(modelo)/'tokenizer.json'),linguagens={})
        for lang in ('javascript','typescript'):
            rs=[r for r in resultados if r['linguagem']==lang]
            relatorio['linguagens'][lang]=dict(total=len(rs),pass_at_1=sum(r['acerto_inicial'] for r in rs)/len(rs),
                acerto_final=sum(r['acerto_final'] for r in rs)/len(rs),reparados=sum(r['reparado'] for r in rs))
    Path(saida).parent.mkdir(parents=True,exist_ok=True)
    Path(saida).write_text(json.dumps(relatorio,ensure_ascii=False,indent=2)+'\n')
    if referencias and not all(r['verificacao']['funcional'] for r in resultados):
        raise RuntimeError('Referência falhou; consulte relatório')
    return relatorio


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--modelo');g.add_argument('--referencias',action='store_true')
    p.add_argument('--saida',required=True);p.add_argument('--tsc',required=True);p.add_argument('--reparos',type=int,default=2,choices=(0,1,2))
    a=p.parse_args();executar(a.saida,a.modelo,a.tsc,a.referencias,a.reparos)
