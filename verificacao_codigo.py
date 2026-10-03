"""Compilação e testes de código gerado. Execução em bubblewrap ou VM QuickJS sem APIs host."""
import json
import importlib.util
import sys
import os
from pathlib import Path
import resource
import shutil
import subprocess
import tempfile


def iguais(a, b):
    """Comparação JSON com booleanos distintos de números, como em JS."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(iguais(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(iguais(a[k], b[k]) for k in a)
    return a == b



def tipo_saida(valores):
    """Tipo de contrato por estrutura JSON, sem inserir valores esperados no candidato."""
    tipos=set()
    for valor in valores:
        if valor is None:tipos.add('null')
        elif isinstance(valor,bool):tipos.add('boolean')
        elif isinstance(valor,(int,float)):tipos.add('number')
        elif isinstance(valor,str):tipos.add('string')
        elif isinstance(valor,list):
            itens=[x for v in valores if isinstance(v,list) for x in v]
            tipo=tipo_saida(itens) if itens else 'unknown'
            tipos.add('('+tipo+')[]')
        elif isinstance(valor,dict):
            itens=[x for v in valores if isinstance(v,dict) for x in v.values()]
            tipos.add('Record<string, '+(tipo_saida(itens) if itens else 'unknown')+'>')
        else:raise ValueError('Contrato não JSON')
    return ' | '.join(sorted(tipos)) or 'unknown'

def limites(memoria=False, cpu=4):
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_FSIZE, (131072, 131072))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if memoria:
        resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))


def comando(args, pasta, timeout=12, memoria=False, cpu=4):
    with tempfile.TemporaryFile() as log:
        try:
            p = subprocess.run(args, cwd=pasta, stdin=subprocess.DEVNULL, stdout=log,
                               stderr=log, timeout=timeout, preexec_fn=lambda: limites(memoria, cpu),
                               env={'PATH': os.environ.get('PATH', ''), 'LANG': 'C.UTF-8'})
            log.seek(0)
            return p.returncode == 0, log.read(8000).decode('utf-8', errors='replace')
        except subprocess.TimeoutExpired:
            return False, 'Tempo limite excedido'
        except OSError as e:
            return False, str(e)


def sandbox_args(node, job):
    bwrap = shutil.which('bwrap')
    if not bwrap:
        return None
    args = [bwrap, '--unshare-all', '--new-session', '--die-with-parent', '--cap-drop', 'ALL']
    # Não monta home, workspace, credenciais nem a raiz do host.
    # Node não exige procfs: diretório vazio evita mount proc proibido no Colab.
    for path in ('/usr', '/lib', '/lib64', '/etc/ld.so.cache'):
        if Path(path).exists():
            args += ['--ro-bind', path, path]
    args += ['--ro-bind', str(Path(node).resolve()), '/node', '--ro-bind', str(job), '/job',
             '--tmpfs', '/tmp', '--dir', '/proc', '--dev', '/dev', '--chdir', '/job',
             '/node', '--jitless', '--max-old-space-size=128']
    return args


def quickjs_disponivel():
    return importlib.util.find_spec('quickjs') is not None


def executar_quickjs(job, pasta):
    # VM sem add_callable, módulos, bindings de SO ou acesso ao processo Python.
    # O subprocesso impõe limites adicionais; QuickJS limita heap, pilha e tempo.
    runner = """import quickjs, sys
from pathlib import Path
ctx = quickjs.Context()
ctx.set_memory_limit(64 * 1024 * 1024)
ctx.set_max_stack_size(1024 * 1024)
ctx.set_time_limit(2)
resultado = ctx.eval('const console = {log: x => x};\\n' + Path(sys.argv[1]).read_text())
print(resultado)
"""
    return comando([sys.executable, '-I', '-c', runner, str(job)], pasta, memoria=True)


def sandbox_disponivel():
    node = shutil.which('node')
    if not node:
        return False
    with tempfile.TemporaryDirectory() as d:
        args = sandbox_args(node, d)
        return bool(args and comando(args + ['-e', 'console.log("isolado")'], d, memoria=True)[0]) or quickjs_disponivel()


def verificar(codigo, linguagem, casos, tsc=None):
    if linguagem not in ('javascript', 'typescript'):
        raise ValueError('Linguagem não suportada')
    if not codigo.strip() or len(codigo.encode()) > 24000 or len(casos) > 100:
        return dict(compila=False, funcional=False, executado=False, diagnostico='Código/casos fora do limite')
    node = shutil.which('node')
    if not node:
        return dict(compila=False, funcional=False, executado=False, diagnostico='Node indisponível')
    with tempfile.TemporaryDirectory() as d:
        pasta = Path(d)
        origem = pasta / ('codigo.ts' if linguagem == 'typescript' else 'codigo.mjs')
        origem.write_text(codigo, encoding='utf-8')
        if linguagem == 'typescript':
            compilador = tsc or shutil.which('tsc')
            if not compilador:
                return dict(compila=False, funcional=False, executado=False, diagnostico='TypeScript indisponível')
            cmd = ([node, compilador] if str(compilador).endswith('.js') else [compilador])
            contrato=pasta/'contrato.ts'
            tipo=tipo_saida([c['saida'] for c in casos])
            chamadas=['const resultado_'+str(i)+': '+tipo+' = resolver('+', '.join(json.dumps(x,ensure_ascii=True) for x in c['entrada'])+');' for i,c in enumerate(casos)]
            contrato.write_text('namespace crivoContrato {\n'+'\n'.join(chamadas)+'\n}')
            ok, log = comando(cmd + [str(origem), str(contrato), '--strict', '--noEmitOnError', '--target',
                                      'ES2022', '--module', 'commonjs', '--outDir', d], d, timeout=30, cpu=20)
            compilado = pasta / 'codigo.js'
        else:
            ok, log = comando([node, '--check', str(origem)], d)
            compilado = origem
        r = dict(compila=ok, funcional=False, executado=False, diagnostico=log,casos_total=len(casos),casos_corretos=0)
        if not ok:
            return r
        args = sandbox_args(node, pasta)
        # O processo candidato recebe entradas; o oráculo fica no processo pai.
        harness = '\nconst entradas = ' + json.dumps([c['entrada'] for c in casos], ensure_ascii=True) + ''';
const saidas = entradas.map(args => resolver(...args));
const resultado = JSON.stringify({saidas, entradas}, (key, value) => {
 if (typeof value === 'number' && !Number.isFinite(value)) throw Error('Número não finito');
 if (typeof value === 'undefined') throw Error('Resultado undefined');
 return value;
});
console.log('CRIVO_RESULTADO:' + resultado);
'''
        (pasta / 'teste.cjs').write_text(compilado.read_text() + harness, encoding='utf-8')
        # Preflight separado: indisponibilidade não conta como falha funcional do modelo.
        pronto, diagnostico = (comando(args + ['-e', 'console.log("isolado")'], d, memoria=True)
                               if args else (False, 'bubblewrap indisponível'))
        if pronto:
            r['runtime'] = 'node_bubblewrap'
            funcional, diagnostico = comando(args + ['/job/teste.cjs'], d, memoria=True)
        elif quickjs_disponivel():
            r['runtime'] = 'quickjs_sem_apis_host'
            funcional, diagnostico = executar_quickjs(pasta / 'teste.cjs', d)
        else:
            r['diagnostico'] = 'Execução bloqueada: isolamento indisponível: ' + diagnostico
            return r
        if funcional:
            linhas = [l[len('CRIVO_RESULTADO:'):] for l in diagnostico.split('\n')
                      if l.startswith('CRIVO_RESULTADO:')]
            try:
                medido = json.loads(linhas[0]) if len(linhas) == 1 else None
                protocolo = (isinstance(medido,dict) and isinstance(medido.get('saidas'),list) and
                    isinstance(medido.get('entradas'),list) and len(medido['saidas'])==len(casos) and
                    len(medido['entradas'])==len(casos))
                comparacoes = [dict(indice=i,correto=iguais(medido['saidas'][i],c['saida']) and
                    iguais(medido['entradas'][i],c['entrada'])) for i,c in enumerate(casos)] if protocolo else []
                r['casos_corretos'] = sum(x['correto'] for x in comparacoes)
                r['casos'] = comparacoes
                funcional = protocolo and r['casos_corretos']==len(casos)
                if protocolo and not funcional:
                    r['contraexemplos'] = [dict(entrada=c['entrada'],esperado=c['saida'],obtido=medido['saidas'][i],
                        entrada_alterada=not iguais(medido['entradas'][i],c['entrada']))
                        for i,c in enumerate(casos) if not comparacoes[i]['correto']][:3]
            except (ValueError, TypeError):
                funcional = False
            if not funcional:
                diagnostico = 'Saída incorreta, entrada alterada ou protocolo de teste ausente'
        r.update(funcional=funcional, executado=True, diagnostico=diagnostico)
        return r
