"""Inspeciona gerações e resultados já salvos; não executa código nem alimenta o treino."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import shutil


def analisar(avaliacao):
    grupos=defaultdict(list);tarefas=[]
    for r in avaliacao['resultados']:
        t=r['tentativas'][0];g=t.get('geracao',{});v=t.get('verificacao',{})
        codigo=g.get('codigo','');h=hashlib.sha256(codigo.strip().encode()).hexdigest()
        grupos[(r['linguagem'],h)].append(r['id'])
        categoria='correta' if v.get('funcional') else 'sintaxe' if not v.get('compila') else 'execucao' if not v.get('executado') else 'logica'
        tarefas.append(dict(id=r['id'],familia=r['familia'],linguagem=r['linguagem'],
            categoria=categoria,codigo=codigo,diagnostico=v.get('diagnostico'),completa=g.get('completa')))
    return dict(particao=avaliacao['particao'],pesos_sha256=avaliacao['pesos_sha256'],
        categorias=dict(Counter(t['categoria'] for t in tarefas)),
        solucoes_repetidas=[dict(linguagem=lang,tarefas=ids) for (lang,h),ids in grupos.items() if len(ids)>1],
        tarefas=tarefas,restricao='Dados de teste servem apenas ao diagnóstico. Não copiar respostas/soluções para treino.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ciclo',required=True);p.add_argument('--saida',required=True)
    a=p.parse_args();c=Path(a.ciclo);out=Path(a.saida);out.mkdir(parents=True,exist_ok=True)
    for nome in ('avaliacao.json','selecao.json','candidato/melhor/relatorio.json','pretreino/melhor/relatorio.json','corpus/manifesto.json'):
        alvo=out/nome;alvo.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(c/nome,alvo)
    for path in sorted((c/'candidato').glob('validacao_funcional_*.json')):shutil.copyfile(path,out/path.name)
    diag=analisar(json.loads((c/'avaliacao.json').read_text()))
    (out/'diagnostico.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(diag,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
