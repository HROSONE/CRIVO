"""Confere a entrada NPM e o servidor Python real iniciado pelo launcher."""
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

RAIZ = Path(__file__).resolve().parent


@unittest.skipUnless(shutil.which("node") and shutil.which("npm"), "Requer Node e NPM")
class TestesInicializacaoLocal(unittest.TestCase):
    def test_npm_dev_e_start_encaminham_argumentos(self):
        npm = shutil.which("npm")
        for script in ("dev", "start"):
            with self.subTest(script=script):
                result = subprocess.run(
                    [npm, "run", "--silent", script, "--", "--help"],
                    cwd=str(RAIZ), capture_output=True, text=True, timeout=20,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("--host", result.stdout)
                self.assertIn("--port", result.stdout)

    @unittest.skipIf(os.name == "nt", "Teste de encerramento por sinal POSIX")
    def test_launcher_roda_api_e_encerra_python(self):
        # Uma pasta diferente prova que os imports e dados são relativos
        # ao projeto, sem depender do diretório de quem executa o comando.
        with tempfile.TemporaryDirectory(prefix="crivo local ") as pasta:
            proc = subprocess.Popen(
                [shutil.which("node"), str(RAIZ / "scripts" / "dev.cjs"), "--port", "0"],
                cwd=pasta, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, start_new_session=os.name != "nt",
            )
            linhas = queue.Queue()
            def ler_saida():
                for linha in proc.stdout:
                    linhas.put(linha)
                linhas.put(None)

            reader = threading.Thread(target=ler_saida, daemon=True)
            reader.start()
            try:
                url = None
                output = []
                prazo = time.monotonic() + 15
                while time.monotonic() < prazo:
                    try:
                        linha = linhas.get(timeout=max(0.01, prazo - time.monotonic()))
                    except queue.Empty:
                        break
                    if linha is None:
                        break
                    output.append(linha)
                    match = re.search(r"CRIVO web: (http://127\.0\.0\.1:\d+)", linha)
                    if match:
                        url = match.group(1)
                        break
                self.assertIsNotNone(url, "".join(output))
                with urlopen(url + "/api/chat", timeout=5) as resposta:
                    self.assertEqual(json.load(resposta)["status"], "ok")
                pedido = Request(
                    url + "/api/chat",
                    data=json.dumps({"message": "O que é Andrômeda?"}).encode(),
                    headers={"Content-Type": "application/json"}, method="POST",
                )
                with urlopen(pedido, timeout=5) as resposta:
                    dados = json.load(resposta)
                self.assertEqual(dados["id"], "conhecimento:andromeda")
                self.assertIn("galáxia", dados["response"])
                proc.terminate()
                proc.wait(timeout=5)
                self.assertIsNotNone(proc.returncode)
                with self.assertRaises(OSError):
                    urlopen(url + "/api/chat", timeout=1)
            finally:
                if os.name != "nt":
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                elif proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=5)
                reader.join(timeout=2)
                proc.stdout.close()
