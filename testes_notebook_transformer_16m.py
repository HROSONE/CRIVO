"""Executa a inicialização real do notebook com Git local, sem Google/treino."""
import ast
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('git'), 'Git necessário para a preparação do Colab')
class InicializacaoColab(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.origem = self.base/'origem'
        self.origem.mkdir()
        self.git(self.origem, 'init', '-b', 'codex/transformer-16m')
        (self.origem/'codigo.py').write_text('versao = 1\n')
        self.git(self.origem, 'add', 'codigo.py')
        self.git(self.origem, '-c', 'user.name=Teste', '-c', 'user.email=teste@example.invalid',
                 'commit', '-m', 'fixture local')
        self.revisao = self.git(self.origem, 'rev-parse', 'HEAD').strip()
        self.raiz = self.base/'checkout'
        notebook = json.loads((Path(__file__).parent/'notebooks/treinar_transformer_16m_colab.ipynb').read_text())
        fonte = ''.join(notebook['cells'][1]['source'])
        arvore = ast.parse(fonte)
        funcao = next(n for n in arvore.body if isinstance(n, ast.FunctionDef) and n.name == 'preparar_codigo')
        ambiente = {'Path': Path, 'subprocess': subprocess}
        exec(compile(ast.Module(body=[funcao], type_ignores=[]), 'celula-colab', 'exec'), ambiente)
        self.preparar = ambiente['preparar_codigo']

    @staticmethod
    def git(pasta, *args):
        return subprocess.run(['git', *args], cwd=pasta, text=True,
                              capture_output=True, check=True).stdout

    def test_primeira_execucao_clona_e_materializa_a_revisao(self):
        self.assertEqual(self.preparar(self.raiz, self.revisao, str(self.origem)), self.revisao)
        self.assertEqual((self.raiz/'codigo.py').read_text(), 'versao = 1\n')
        self.assertFalse(self.git(self.raiz, 'status', '--porcelain').strip())

    def test_recupera_o_clone_incompleto_deixado_pela_celula_antiga(self):
        subprocess.run(['git', 'clone', '--no-checkout', str(self.origem), str(self.raiz)],
                       check=True, capture_output=True)
        self.assertIn('D ', self.git(self.raiz, 'status', '--porcelain'))
        self.assertEqual(self.preparar(self.raiz, self.revisao), self.revisao)
        self.assertTrue((self.raiz/'codigo.py').is_file())

    def test_reexecutar_preserva_checkpoint_no_drive_e_revisao_fixada(self):
        drive = self.base/'drive';drive.mkdir()
        checkpoint = drive/'checkpoint.pt';checkpoint.write_bytes(b'pesos-preservados')
        self.preparar(self.raiz, self.revisao, str(self.origem))
        (self.origem/'codigo.py').write_text('versao = 2\n')
        self.git(self.origem, 'add', 'codigo.py')
        self.git(self.origem, '-c', 'user.name=Teste', '-c', 'user.email=teste@example.invalid',
                 'commit', '-m', 'nova revisao')
        self.assertEqual(self.preparar(self.raiz, self.revisao), self.revisao)
        self.assertEqual((self.raiz/'codigo.py').read_text(), 'versao = 1\n')
        self.assertEqual(checkpoint.read_bytes(), b'pesos-preservados')

    def test_alteracao_real_e_recusada_sem_sobrescrever_arquivo(self):
        self.preparar(self.raiz, self.revisao, str(self.origem))
        arquivo=self.raiz/'codigo.py';arquivo.write_text('alteracao do usuario\n')
        with self.assertRaisesRegex(RuntimeError, 'alterações reais'):
            self.preparar(self.raiz, self.revisao)
        self.assertEqual(arquivo.read_text(), 'alteracao do usuario\n')

    def test_arquivo_nao_rastreado_em_clone_incompleto_e_preservado(self):
        subprocess.run(['git', 'clone', '--no-checkout', str(self.origem), str(self.raiz)],
                       check=True, capture_output=True)
        arquivo=self.raiz/'anotacao.txt';arquivo.write_text('conteudo do usuario')
        with self.assertRaisesRegex(RuntimeError, 'alterações reais'):
            self.preparar(self.raiz, self.revisao)
        self.assertEqual(arquivo.read_text(), 'conteudo do usuario')
        self.assertFalse((self.raiz/'codigo.py').exists())


if __name__ == '__main__':
    unittest.main()
