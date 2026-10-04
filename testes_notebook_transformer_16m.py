"""Inicialização Git e retomada de blocos do notebook sem conexão ao Google."""
import ast
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import importlib.util
from unittest.mock import patch


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


@unittest.skipUnless(all(importlib.util.find_spec(n) for n in ('torch','numpy','tokenizers')),
                     'Retomada requer as ferramentas opcionais de treino')
class RetomadaBlocosColab(unittest.TestCase):
    def test_dois_blocos_reproduzem_treino_continuo_sem_reiniciar_lr_adam_ou_rng(self):
        import torch
        from scripts import experimento_transformer_16m as experimento
        from linguagem_profunda import Configuracao
        from testes_linguagem_profunda import TestesMatematicaLinguagem
        root=Path(__file__).parent
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);corpus=p/'corpus';corpus.mkdir()
            TestesMatematicaLinguagem().fixture_corpus(corpus)
            manifesto=json.loads((corpus/'manifesto.json').read_text())
            config=Configuracao(vocabulario=manifesto['vocabulario'],dimensao=24,
                                camadas=1,cabecas=3,contexto=16)
            dados=dict(semente=20261004,pretreino=dict(passos=4,lote=2,lr=.0008,
                        avaliar_a_cada=2,salvar_a_cada=1))
            original=experimento.comando_treino
            def cpu(dados,config,corpus,saida,etapa,dispositivo,threads,max_segundos):
                return original(dados,config,corpus,saida,etapa,'cpu',1,max_segundos)
            notebook=json.loads((root/'notebooks/treinar_transformer_16m_colab.ipynb').read_text())
            arvore=ast.parse(''.join(notebook['cells'][1]['source']))
            funcao=next(n for n in arvore.body if isinstance(n,ast.FunctionDef) and n.name=='treinar_bloco')
            ambiente=dict(Path=Path,json=json,subprocess=subprocess,ROOT=root,SAIDA=p/'blocos',
                CORPUS=corpus,PASSOS_POR_BLOCO=2,TEMPO_BLOCO_SEGUNDOS=900,SALVAR_A_CADA=1)
            exec(compile(ast.Module(body=[funcao],type_ignores=[]),'bloco-colab','exec'),ambiente)
            with patch.object(experimento,'carregar_config',return_value=(dados,config,1)), \
                 patch.object(experimento,'comando_treino',side_effect=cpu):
                a=ambiente['treinar_bloco']('pretreino')
                self.assertEqual((a['passo'],a['horizonte']),(2,4))
                b=ambiente['treinar_bloco']('pretreino')
                self.assertEqual((b['passo'],b['horizonte']),(4,4))
            subprocess.run(cpu(dados,config,corpus,p/'continuo','pretreino','cpu',1,900),
                           cwd=root,check=True,capture_output=True,text=True,timeout=90)
            a=torch.load(p/'blocos/pretreino/checkpoint.pt',weights_only=True)
            b=torch.load(p/'continuo/pretreino/checkpoint.pt',weights_only=True)
            self.assertEqual(a['tokens_alvo'],b['tokens_alvo'])
            self.assertEqual(a['historico'],b['historico'])
            self.assertEqual(a['rng_numpy'],b['rng_numpy'])
            self.assertTrue(torch.equal(a['rng_torch'],b['rng_torch']))
            for k,peso in a['modelo'].items():
                self.assertTrue(torch.equal(peso,b['modelo'][k]),k)
            for k,estado in a['otimizador']['state'].items():
                for campo,valor in estado.items():
                    self.assertTrue(torch.equal(valor,b['otimizador']['state'][k][campo]))


if __name__ == '__main__':
    unittest.main()
