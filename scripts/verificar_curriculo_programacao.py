"""Valida apenas referências autorais versionadas; nunca aceita código de modelos.

Compila referências em lote e compara saídas/mutação com oráculos Python.
Execução no host é exclusiva deste acervo revisável, não da avaliação de candidatos.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verificacao_codigo import iguais


def validar(tsc=None):
    node = shutil.which('node')
    compilador = tsc or shutil.which('tsc')
    if not node or not compilador:
        raise RuntimeError('Node e TypeScript são obrigatórios para validar referências')
    tarefas = []
    for nome in ('curriculo.json', 'algoritmos.json', 'logica.json'):
        tarefas += json.loads((ROOT / 'dados/programacao' / nome).read_text())['tarefas']
    reparos = [dict(t,resposta=t['codigo_incorreto'],casos=[dict(entrada=t['contraprova']['entrada'],saida=t['contraprova']['obtido'])])
               for t in tarefas if t.get('tipo')=='reparo']
    if any(t['contraprova']['esperado']==t['contraprova']['obtido'] for t in reparos):
        raise AssertionError('Contraexemplo não diferencia o erro')
    tarefas += reparos
    contagem = {}
    with tempfile.TemporaryDirectory() as d:
        pasta = Path(d)
        for linguagem in ('javascript', 'typescript'):
            itens = [t for t in tarefas if t['linguagem'] == linguagem]
            funcoes = [t['resposta'].replace('function resolver(', f'function referencia_{i}(', 1)
                       for i, t in enumerate(itens)]
            origem = pasta / ('referencias.ts' if linguagem == 'typescript' else 'referencias.js')
            origem.write_text('\n'.join(funcoes))
            if linguagem == 'typescript':
                cmd = [node, str(compilador)] if str(compilador).endswith('.js') else [str(compilador)]
                subprocess.run(cmd + [str(origem), '--strict', '--target', 'ES2022',
                                      '--outDir', d], check=True, timeout=120)
            else:
                subprocess.run([node, '--check', str(origem)], check=True, timeout=30)
            js = pasta / 'referencias.js'
            chamadas = []
            for i, t in enumerate(itens):
                for caso in t['casos']:
                    entrada = json.dumps(caso['entrada'], ensure_ascii=True)
                    chamadas.append(f'{{const args = {entrada}; resultados.push([referencia_{i}(...args), args]);}}')
            job = pasta / 'verificar.cjs'
            job.write_text(js.read_text() + '\nconst resultados = [];\n' + '\n'.join(chamadas)
                           + '\nconsole.log(JSON.stringify(resultados));')
            saidas = json.loads(subprocess.check_output([node, str(job)], timeout=30))
            casos = [c for t in itens for c in t['casos']]
            if len(saidas) != len(casos):
                raise AssertionError('Quantidade de saídas incorreta')
            for saida, caso in zip(saidas, casos):
                if not iguais(saida, [caso['saida'], caso['entrada']]):
                    raise AssertionError(f'Referência incorreta ou mutação: {saida!r}, {caso!r}')
            contagem[linguagem] = dict(referencias=len(itens), casos=len(casos), aprovadas=len(itens))
    return dict(natureza='somente_referencias_autorais; não é resultado do modelo', linguagens=contagem)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tsc'); p.add_argument('--saida')
    a = p.parse_args()
    resultado = validar(a.tsc)
    if a.saida:
        Path(a.saida).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(resultado, ensure_ascii=False))
