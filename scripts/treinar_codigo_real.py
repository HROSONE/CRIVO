"""Código real -> pré-treino nativo do zero -> instruções -> seleção funcional -> teste."""
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
    p.add_argument('--saida',required=True);p.add_argument('--cache',required=True);p.add_argument('--tsc',required=True)
    p.add_argument('--perfil',choices=('atual','codigo6m','10m'),default='codigo6m')
    p.add_argument('--pretreino-passos',type=int,default=12000);p.add_argument('--sft-passos',type=int,default=8000)
    p.add_argument('--lote',type=int,default=4);p.add_argument('--threads',type=int,default=2)
    p.add_argument('--max-segundos',type=int,default=9600)
    a=p.parse_args()
    if min(a.pretreino_passos,a.sft_passos,a.lote,a.threads,a.max_segundos)<1: p.error('Contagens positivas obrigatórias')
    out=Path(a.saida).resolve()
    if out.exists() and any(out.iterdir()): p.error('Use uma saída nova; checkpoints podem ser retomados pelo treinador original')
    out.mkdir(parents=True,exist_ok=True); c=PERFIS[a.perfil];inicio=time.monotonic()
    print(json.dumps(estimar(a.perfil),ensure_ascii=False),flush=True)
    def run(script,args,timeout):
        subprocess.run([sys.executable,str(ROOT/'scripts'/script)]+list(map(str,args)),cwd=ROOT,check=True,timeout=timeout)
    run('preparar_codigo_real.py',['--saida',out/'corpus','--cache',a.cache,'--tsc',a.tsc,
        '--contexto',c['contexto'],'--vocabulario',c['vocabulario']],600)
    base=['--corpus',out/'corpus','--lote',a.lote,'--threads',a.threads,
          '--dimensao',c['dimensao'],'--camadas',c['camadas'],'--cabecas',c['cabecas'],
          '--contexto',c['contexto'],'--selecionar-melhor','--salvar-a-cada',250]
    pre_budget=max(1,int(a.max_segundos*.6))
    run('treinar_linguagem_profunda.py',base+['--saida',out/'pretreino','--fase','linguagem',
        '--passos',a.pretreino_passos,'--lr','.0008','--avaliar-a-cada',min(1000,a.pretreino_passos),
        '--max-segundos',pre_budget],pre_budget+600)
    sft_budget=max(1,int(a.max_segundos-(time.monotonic()-inicio)-600))
    run('treinar_linguagem_profunda.py',base+['--saida',out/'candidato','--fase','dialogo',
        '--inicial',out/'pretreino/melhor','--passos',a.sft_passos,'--lr','.0003',
        '--avaliar-a-cada',min(1000,a.sft_passos),'--validacao-funcional','--tsc',a.tsc,
        '--repeticao-linguagem','.1','--max-segundos',sft_budget],sft_budget+1200)
    escolhido=out/'candidato/melhor'
    r=json.loads((escolhido/'relatorio.json').read_text())
    (out/'selecao.json').write_text(json.dumps(dict(modelo=str(escolhido),passo=r['passo'],
        pesos_sha256=r['pesos_sha256'],criterio='corretas_compilacao_termino_ce_validacao',
        validacao=r['historico'][-1]['funcional'],promovido=False),ensure_ascii=False,indent=2)+'\n')
    run('avaliar_programacao.py',['--modelo',escolhido,'--saida',out/'avaliacao.json','--tsc',a.tsc,'--reparos',0],600)
    # Apenas cópias temporárias de validação: melhores e últimos checkpoints continuam preservados.
    import shutil
    shutil.rmtree(out/'candidato/validacao_modelo',ignore_errors=True)
    print('Treino concluído; consulte selecao.json e avaliacao.json. Candidato permanece experimental.',flush=True)


if __name__=='__main__':main()
