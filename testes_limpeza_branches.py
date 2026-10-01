"""Limpeza deve preservar trabalho novo e comprovar integração."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import limpar_branches_integradas as limpeza

SHA = "a" * 40
MAIN = "b" * 40


class LimpezaBranchesTestes(unittest.TestCase):
    def test_branch_alterada_ou_protegida_nao_e_elegivel(self):
        chamadas = []
        def consultar(recurso):
            chamadas.append(recurso)
            return {"object": {"sha": "c" * 40}}
        for nome in ("main", "archive/meu-trabalho"):
            self.assertIn("protegida", limpeza.avaliar({"branch": nome, "sha": SHA}, MAIN, consultar))
        self.assertEqual(chamadas, [])
        self.assertIn("SHA mudou", limpeza.avaliar({"branch": "trabalho", "sha": SHA}, MAIN, consultar))

    def test_squash_exige_pr_mesclada_exata_na_main(self):
        registro = {"branch": "concluido", "sha": SHA, "pr_integrado": 7, "merge_sha": MAIN}
        pr = {"merged": True, "head": {"sha": SHA}, "base": {"ref": "main"},
              "merge_commit_sha": MAIN}
        def consultar(recurso):
            return pr if recurso.startswith("pulls/") else {"object": {"sha": SHA}}
        with patch.object(limpeza, "ancestral", side_effect=lambda a, b: a == MAIN):
            self.assertTrue(limpeza.avaliar(registro, MAIN, consultar).startswith("integrada:"))
            pr["merged"] = False
            self.assertIn("não comprovada", limpeza.avaliar(registro, MAIN, consultar))
            pr["merged"] = True
            pr["base"]["ref"] = "outra"
            self.assertIn("não comprovada", limpeza.avaliar(registro, MAIN, consultar))

    def test_servidor_recusa_exclusao_se_branch_avanca_depois_da_consulta(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            remoto, trabalho = raiz / "remoto.git", raiz / "trabalho"
            executar = subprocess.run
            def git(*args, cwd=None):
                resultado = executar(["git", *args], cwd=cwd, capture_output=True, text=True)
                self.assertEqual(resultado.returncode, 0, resultado.stderr)
                return resultado.stdout.strip()
            git("init", "--bare", str(remoto))
            git("init", str(trabalho))
            git("config", "user.name", "Teste CRIVO", cwd=trabalho)
            git("config", "user.email", "teste@crivo.local", cwd=trabalho)
            git("remote", "add", "origin", str(remoto), cwd=trabalho)
            arquivo = trabalho / "dados.txt"
            arquivo.write_text("estado aprovado")
            git("add", "dados.txt", cwd=trabalho)
            git("commit", "-m", "estado aprovado", cwd=trabalho)
            antigo = git("rev-parse", "HEAD", cwd=trabalho)
            git("push", "origin", "HEAD:refs/heads/trabalho", cwd=trabalho)
            arquivo.write_text("novo trabalho do usuário")
            git("commit", "-am", "novo trabalho", cwd=trabalho)
            novo = git("rev-parse", "HEAD", cwd=trabalho)
            git("push", "origin", "HEAD:refs/heads/trabalho", cwd=trabalho)
            with patch.object(limpeza.subprocess, "run",
                              side_effect=lambda *a, **kw: executar(*a, cwd=trabalho, **kw)):
                self.assertFalse(limpeza.excluir("trabalho", antigo))
            self.assertEqual(git("rev-parse", "refs/heads/trabalho", cwd=remoto), novo)
