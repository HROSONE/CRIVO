'use strict';

const { spawn, spawnSync } = require('node:child_process');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const candidates = process.platform === 'win32'
  ? [['py', ['-3']], ['python', []], ['python3', []]]
  : [['python3', []], ['python', []]];
const checkVersion = 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)';
const python = candidates.find(([command, prefix]) => {
  const result = spawnSync(command, [...prefix, '-c', checkVersion], {
    stdio: 'ignore',
    timeout: 5000,
    windowsHide: true,
  });
  return !result.error && result.status === 0;
});

if (!python) {
  console.error('O CRIVO precisa de Python 3.8 ou superior no PATH. Instale o Python e abra um novo terminal.');
  process.exitCode = 1;
} else {
  const [command, prefix] = python;
  const child = spawn(command, [
    ...prefix, '-u', path.join(root, 'web_local.py'), ...process.argv.slice(2),
  ], { cwd: root, stdio: 'inherit', windowsHide: true });

  for (const signal of ['SIGINT', 'SIGTERM']) {
    process.on(signal, () => {
      if (!child.killed) child.kill(signal);
    });
  }
  child.on('error', (error) => {
    console.error('Não foi possível iniciar o servidor Python: ' + error.message);
    process.exitCode = 1;
  });
  child.on('exit', (code, signal) => {
    process.exitCode = code === null ? (signal === 'SIGINT' ? 130 : 1) : code;
  });
}
