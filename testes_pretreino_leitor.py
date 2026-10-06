"""Caderno e script do Transformer do leitor: dados conferidos e Drive sem encher."""
import json
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "scripts"))

import pretreinar_leitor_16m as pt  # noqa: E402

CADERNO = RAIZ / "notebooks" / "treinar_transformer_leitor_colab.ipynb"


class TestesPretreinoLeitor(unittest.TestCase):
    def setUp(self):
        nb = json.loads(CADERNO.read_text(encoding="utf-8"))
        self.codigo = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")

    def test_checkpoint_no_drive_so_a_cada_10000_passos(self):
        m = re.search(r"CHECKPOINT_A_CADA\s*=\s*(\d+)", self.codigo)
        self.assertIsNotNone(m)
        self.assertGreaterEqual(int(m.group(1)), 10000)
        self.assertIn("'--checkpoint-a-cada', str(CHECKPOINT_A_CADA)", self.codigo)
        # Nenhuma outra opção de gravação periódica.
        self.assertNotIn("salvar-a-cada", self.codigo)

    def test_drive_recebe_so_checkpoint_base_e_resultado(self):
        usos = set(re.findall(r"DRIVE\s*/\s*'([^']+)'", self.codigo))
        self.assertEqual(usos, {"checkpoint.pt", "base", "resultado_leitor", "resultado_leitor.zip"})
        # Dados e intermediários no disco do Colab.
        self.assertIn("DADOS = Path('/content/crivo-dados')", self.codigo)
        self.assertIn("LEITOR = Path('/content/leitor')", self.codigo)

    def test_progresso_aparece_na_celula_e_no_log(self):
        # O Colab não mostra o que um subprocesso escreve direto no terminal;
        # o caderno repassa linha a linha e grava em /content/crivo-log.txt.
        import ast
        import tempfile
        arvore = ast.parse(self.codigo)
        funcao = next(n for n in arvore.body if isinstance(n, ast.FunctionDef) and n.name == "executar")
        with tempfile.TemporaryDirectory() as pasta:
            ambiente = {"subprocess": __import__("subprocess"), "Path": Path, "ROOT": pasta,
                        "LOG": Path(pasta) / "log.txt"}
            exec(compile(ast.Module(body=[funcao], type_ignores=[]), "celula", "exec"), ambiente)
            ambiente["executar"]([sys.executable, "-c", "print('passo 100/40000')"])
            self.assertIn("passo 100/40000", (Path(pasta) / "log.txt").read_text())
            with self.assertRaises(RuntimeError):
                ambiente["executar"]([sys.executable, "-c", "import sys; sys.exit(3)"])
        self.assertNotIn("subprocess.run([sys.executable, '-u', 'scripts/", self.codigo)

    def test_script_recusa_checkpoint_frequente_no_drive(self):
        argv = ["pretreinar_leitor_16m.py", "--etapa", "treinar", "--checkpoint-a-cada", "50",
                "--checkpoint", "/content/drive/MyDrive/CRIVO/transformer-leitor/checkpoint.pt"]
        with mock.patch.object(sys, "argv", argv):
            with self.assertRaises(SystemExit) as erro:
                pt.main()
        self.assertIn("10.000", str(erro.exception))

    def test_wikipedia_inteira_com_sha256(self):
        self.assertEqual(len(pt.WIKIPEDIA), 6)
        for nome, sha in pt.WIKIPEDIA:
            self.assertRegex(nome, r"train-0000[0-5]-of-00006\.parquet")
            self.assertRegex(sha, r"^[0-9a-f]{64}$")

    def test_limpeza_corta_referencias_e_restos(self):
        texto = ("Brasília é a capital federal do Brasil desde 1960, planejada por Lúcio Costa.\n"
                 "Geografia\n"
                 "A cidade fica no Planalto Central, a cerca de mil metros de altitude.\n"
                 "Referências\n"
                 "Fulano, Livro, 1999.")
        limpo = pt.limpar_artigo(texto)
        self.assertIn("Planalto Central", limpo)
        self.assertNotIn("Fulano", limpo)
        self.assertNotIn("Geografia", limpo)

    def test_validacao_estavel_e_pequena(self):
        textos = ["documento %d" % i for i in range(20000)]
        val = sum(pt.particao(t) == "validacao" for t in textos)
        self.assertTrue(50 <= val <= 150, val)
        self.assertEqual(pt.particao("abc"), pt.particao("abc"))

    def test_modelo_do_tamanho_anunciado(self):
        m = pt.MODELO
        d, v, c, n = m["dimensao"], m["vocabulario"], m["contexto"], m["camadas"]
        aprox = v * d + c * d + n * 12 * d * d
        self.assertTrue(15e6 < aprox < 20e6, aprox)


if __name__ == "__main__":
    unittest.main()
