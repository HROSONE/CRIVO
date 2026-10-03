"""Ciclo reproduzível com limite de tempo: corpus, treino, avaliação e artefatos."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.escalar_programacao import PERFIS,estimar


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida',required=True);p.add_argument('--perfil',choices=PERFIS,default='atual')
    p.add_argument('--passos',type=int,default=200)
    p.add_argument('--lote',type=int,default=4);p.add_argument('--threads',type=int,default=3)
    p.add_argument('--selecionar-melhor',action='store_true')
    p.add_argument('--paciencia-validacoes',type=int,default=0)
    p.add_argument('--timeout-segundos',type=int,default=1800);p.add_argument('--tsc')
    a=p.parse_args()
    if min(a.passos,a.lote,a.threads,a.timeout_segundos)<1: p.error('Contagens devem ser positivas')
    out=Path(a.saida).resolve()
    if out.exists() and any(out.iterdir()): p.error('Saída deve estar vazia; retomada usa o treinador original')
    out.mkdir(parents=True,exist_ok=True)
    c=PERFIS[a.perfil];inicio=time.monotonic()
    print(json.dumps(estimar(a.perfil),ensure_ascii=False),flush=True)
    def run(script,args):
        restante=a.timeout_segundos-(time.monotonic()-inicio)
        if restante<=0: raise TimeoutError('Orçamento de tempo esgotado')
        subprocess.run([sys.executable,str(ROOT/'scripts'/script)]+list(map(str,args)),
                       cwd=ROOT,check=True,timeout=restante)
    prep=['--saida',out/'corpus','--contexto',c['contexto'],'--vocabulario',c['vocabulario']]
    if a.perfil=='atual': prep+=['--tokenizer',ROOT/'artefatos/linguagem_profunda/tokenizer.json']
    run('preparar_programacao.py',prep)
    base=['--corpus',out/'corpus','--passos',a.passos,'--lote',a.lote,'--threads',a.threads,
          '--dimensao',c['dimensao'],'--camadas',c['camadas'],'--cabecas',c['cabecas'],
          '--contexto',c['contexto'],'--avaliar-a-cada',min(200,a.passos),
          '--salvar-a-cada',min(100,a.passos)]
    if a.selecionar_melhor:
        base+=['--selecionar-melhor','--paciencia-validacoes',a.paciencia_validacoes]
    if a.perfil=='atual':
        inicial=ROOT/'artefatos/linguagem_profunda'
        extra=['--ajustar-proprio']
    else:
        run('treinar_linguagem_profunda.py',base+['--saida',out/'pretreino','--fase','linguagem'])
        inicial=out/'pretreino' / 'melhor' if a.selecionar_melhor else out/'pretreino';extra=[]
    run('treinar_linguagem_profunda.py',base+['--saida',out/'candidato','--fase','dialogo',
        '--inicial',inicial,'--lr','.0001']+extra)
    selecionado=out/'candidato'/'melhor' if a.selecionar_melhor else out/'candidato'
    (out/'selecao.json').write_text(json.dumps(dict(modelo=str(selecionado),criterio='validacao' if a.selecionar_melhor else 'ultimo_passo'),ensure_ascii=False,indent=2)+'\n')
    evalargs=['--modelo',selecionado,'--saida',out/'avaliacao.json']
    if a.tsc: evalargs+=['--tsc',a.tsc]
    run('avaliar_programacao.py',evalargs)
    print('Ciclo concluído. Consulte avaliacao.json; nenhuma promoção automática.',flush=True)


if __name__=='__main__': main()
