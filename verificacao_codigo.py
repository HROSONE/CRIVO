"""Compilação e testes de código gerado. Execução exige isolamento bubblewrap."""
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import tempfile


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
        harness = '\nconst casos = ' + json.dumps(casos, ensure_ascii=True) + ''';
for (const c of casos) {
 const antes = JSON.stringify(c.entrada);
 const recebido = resolver(...c.entrada);
 if (JSON.stringify(recebido) !== JSON.stringify(c.saida)) throw Error('Saída incorreta');
 if (JSON.stringify(c.entrada) !== antes) throw Error('Entrada alterada');
}
console.log('casos aprovados');
'''
        (pasta / 'teste.cjs').write_text(compilado.read_text() + harness, encoding='utf-8')
        # Preflight separado: indisponibilidade não conta como falha funcional do modelo.
        pronto, diagnostico = comando(args + ['-e', 'console.log("isolado")'], d, memoria=True)
        if not pronto:
            r['diagnostico'] = 'Execução bloqueada: isolamento indisponível: ' + diagnostico
            return r
        funcional, diagnostico = comando(args + ['/job/teste.cjs'], d, memoria=True)
        r.update(funcional=funcional, executado=True, diagnostico=diagnostico)
        return r
