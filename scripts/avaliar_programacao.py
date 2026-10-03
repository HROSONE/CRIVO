"""Pass@1 de famílias reservadas, compilação, término e reparo sem acessar respostas."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from programacao_neural import GeradorProgramacao,digest,gate
from verificacao_codigo import verificar,sandbox_disponivel


def avaliar(modelo,saida,split='teste',tsc=None,reparos=1):
    if reparos not in (0,1,2): raise ValueError('Reparos deve estar entre 0 e 2')
    tarefas_path=ROOT/'dados/programacao/tarefas.json'
    tarefas=[t for t in json.loads(tarefas_path.read_text())['tarefas'] if t['split']==split]
    gerador=GeradorProgramacao(modelo)  # Sem recuperação do catálogo reservado.
    r=dict(particao=split,familias=len({t['familia'] for t in tarefas}),
        pesos_sha256=digest(Path(modelo)/'pesos.pt'),tokenizer_sha256=digest(Path(modelo)/'tokenizer.json'),
        tarefas_sha256=digest(tarefas_path),isolamento=sandbox_disponivel(),
        regressao_geral_aprovada=False,revisao_independente=False,
        benchmark='sintético autoral pequeno; não demonstra nível sênior nem avalia projetos reais',
        recuperacao=False,linguagens={},resultados=[])
    for t in tarefas:
        tentativas=[]; anterior=None; diagnostico=None
        for tentativa in range(reparos+1):
            try:
                g=gerador.gerar(t['mensagem'],diagnostico=diagnostico,codigo_anterior=anterior)
                v=verificar(g['codigo'],t['linguagem'],t['casos'],tsc=tsc)
                tentativas.append(dict(geracao=g,verificacao=v))
                if v['funcional'] and g['completa']: break
                anterior=g['codigo'];diagnostico=v['diagnostico'] or 'A geração não terminou; retorne a função completa.'
            except ValueError as e:
                tentativas.append(dict(erro=str(e)));break
        primeiro=tentativas[0];v=primeiro.get('verificacao',{});g=primeiro.get('geracao',{})
        r['resultados'].append(dict(id=t['id'],familia=t['familia'],linguagem=t['linguagem'],tentativas=tentativas))
        m=r['linguagens'].setdefault(t['linguagem'],dict(total=0,compilam=0,completas=0,executadas=0,corretas=0,reparadas=0,nao_avaliadas=0))
        m['total']+=1;m['compilam']+=int(v.get('compila',False));m['completas']+=int(g.get('completa',False))
        m['executadas']+=int(v.get('executado',False));m['corretas']+=int(v.get('funcional',False) and g.get('completa',False))
        m['nao_avaliadas']+=int(v.get('compila',False) and not v.get('executado',False))
        m['reparadas']+=int(any(x.get('verificacao',{}).get('funcional') and x.get('geracao',{}).get('completa') for x in tentativas[1:]))
        print(json.dumps(dict(tarefa=t['id'],compila=v.get('compila'),completa=g.get('completa'))),flush=True)
    for m in r['linguagens'].values():
        m['pass_at_1']=None if m['nao_avaliadas'] else m['corretas']/m['total']
        m['taxa_compilacao']=m['compilam']/m['total']
    r['gate']=gate(r)
    Path(saida).parent.mkdir(parents=True,exist_ok=True)
    Path(saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modelo',required=True);p.add_argument('--saida',required=True)
    p.add_argument('--split',choices=('validacao','teste'),default='teste');p.add_argument('--tsc')
    p.add_argument('--reparos',type=int,default=1)
    a=p.parse_args();r=avaliar(a.modelo,a.saida,a.split,a.tsc,a.reparos)
    print(json.dumps({k:v for k,v in r.items() if k!='resultados'},ensure_ascii=False,indent=2))
