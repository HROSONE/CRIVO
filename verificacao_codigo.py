"""Compilação e testes de código gerado. Execução exige isolamento bubblewrap."""
import json
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


def limites(memoria=False):
    resource.setrlimit(resource.RLIMIT_CPU, (4, 4))
    resource.setrlimit(resource.RLIMIT_FSIZE, (131072, 131072))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if memoria:
        resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))


def comando(args, pasta, timeout=12, memoria=False):
    with tempfile.TemporaryFile() as log:
        try:
            p = subprocess.run(args, cwd=pasta, stdin=subprocess.DEVNULL, stdout=log,
                               stderr=log, timeout=timeout, preexec_fn=lambda: limites(memoria),
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
    for path in ('/usr', '/lib', '/lib64', '/etc/ld.so.cache'):
        if Path(path).exists():
            args += ['--ro-bind', path, path]
    args += ['--ro-bind', str(Path(node).resolve()), '/node', '--ro-bind', str(job), '/job',
             '--tmpfs', '/tmp', '--proc', '/proc', '--dev', '/dev', '--chdir', '/job',
             '/node', '--jitless', '--max-old-space-size=128']
    return args


def sandbox_disponivel():
    node = shutil.which('node')
    if not node:
        return False
    with tempfile.TemporaryDirectory() as d:
        args = sandbox_args(node, d)
        return bool(args and comando(args + ['-e', 'console.log("isolado")'], d, memoria=True)[0])


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
            ok, log = comando(cmd + [str(origem), '--strict', '--noEmitOnError', '--target',
                                      'ES2022', '--module', 'commonjs', '--outDir', d], d)
            compilado = pasta / 'codigo.js'
        else:
            ok, log = comando([node, '--check', str(origem)], d)
            compilado = origem
        r = dict(compila=ok, funcional=False, executado=False, diagnostico=log)
        if not ok:
            return r
        args = sandbox_args(node, pasta)
        if not args:
            r['diagnostico'] = 'Execução bloqueada: bubblewrap indisponível'
            return r
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
        pronto, diagnostico = comando(args + ['-e', 'console.log("isolado")'], d, memoria=True)
        if not pronto:
            r['diagnostico'] = 'Execução bloqueada: isolamento indisponível: ' + diagnostico
            return r
        funcional, diagnostico = comando(args + ['/job/teste.cjs'], d, memoria=True)
        if funcional:
            linhas = [l[len('CRIVO_RESULTADO:'):] for l in diagnostico.splitlines()
                      if l.startswith('CRIVO_RESULTADO:')]
            try:
                medido = json.loads(linhas[0]) if len(linhas) == 1 else None
                funcional = (isinstance(medido, dict) and
                             iguais(medido.get('saidas'), [c['saida'] for c in casos]) and
                             iguais(medido.get('entradas'), [c['entrada'] for c in casos]))
            except (ValueError, TypeError):
                funcional = False
            if not funcional:
                diagnostico = 'Saída incorreta, entrada alterada ou protocolo de teste ausente'
        r.update(funcional=funcional, executado=True, diagnostico=diagnostico)
        return r
