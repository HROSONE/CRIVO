"""Capacidade, proveniência, seleção humana e retomada do experimento próprio."""
import tempfile
import unittest
import json
import subprocess
import sys
import importlib.util
from pathlib import Path

from scripts.selecao_programacao import pontuacao_validacao
DISPONIVEL = all(importlib.util.find_spec(n) for n in ('torch', 'numpy', 'tokenizers'))
if DISPONIVEL:
    import numpy as np
    import torch
    from scripts.experimento_transformer_16m import carregar_config, comando_treino
    from scripts.treinar_linguagem_profunda import avaliar


@unittest.skipUnless(DISPONIVEL, 'Experimento opcional requer ferramentas de treino; CI próprio as instala')
class Experimento16M(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.dados, cls.config, cls.n = carregar_config()

    def test_capacidade_real_e_pre_treino_sem_pesos_importados(self):
        self.assertEqual(self.n, 15855360)
        cmd = comando_treino(self.dados, self.config, 'corpus', 'ensaio', 'pretreino', 'cpu', 1)
        self.assertNotIn('--inicial', cmd)
        self.assertNotIn('--retomar', cmd)
        self.assertEqual(cmd[cmd.index('--camadas')+1], '8')
        self.assertEqual(cmd[cmd.index('--dimensao')+1], '384')

    def test_retomada_nao_carrega_novamente_o_pre_treino(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'dialogo').mkdir();(out/'dialogo/checkpoint.pt').touch()
            cmd=comando_treino(self.dados,self.config,'corpus',out,'dialogo','cpu',1)
            self.assertIn('--retomar',cmd)
            self.assertNotIn('--inicial',cmd)
            self.assertIn('--selecao-humana',cmd)
            self.assertNotIn('--equilibrar-familias',cmd)

    def test_sft_sem_pre_treino_e_recusado(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'pré-treino próprio'):
                comando_treino(self.dados,self.config,'corpus',tmp,'dialogo','cpu',1)

    def test_memorizar_sinteticos_nao_compensa_piorar_humanos(self):
        def h(agregado,humano,split='validacao'):
            return {'avaliacao':{'dialogo':{'entropia_cruzada':agregado},
                'dialogo_humano':{'entropia_cruzada':humano,'particao':split,'tokens_avaliados':30}}}
        antes, depois = h(4.,4.),h(.5,4.4)
        self.assertGreater(pontuacao_validacao(depois,'dialogo'),pontuacao_validacao(antes,'dialogo'))
        self.assertLess(pontuacao_validacao(depois,'dialogo',humanos=True),pontuacao_validacao(antes,'dialogo',humanos=True))
        with self.assertRaisesRegex(ValueError,'nunca do teste'):
            pontuacao_validacao(h(.5,3.,'teste'),'dialogo',humanos=True)

    def test_validacao_humana_completa_ignora_sinteticos_e_padding(self):
        class Modelo:
            def eval(self): pass
            def __call__(self,x,y): return None,torch.tensor(float(y[y!=-100].float().mean()))
        class Dados:
            humanos={'validacao':np.array([0,2])}
            x={'validacao':np.ones((3,4),dtype=np.int64)}
            y={'validacao':np.array([[2,-100,-100,-100],[99,99,99,99],[4,4,4,-100]])}
            def lote(self,*args): return torch.ones((1,4),dtype=torch.long),torch.ones((1,4),dtype=torch.long)
        r=avaliar(Modelo(),Dados(),'cpu',lotes=1,tamanho=1,humanos=True)['dialogo_humano']
        self.assertEqual(r['tokens_avaliados'],4)
        self.assertEqual(r['janelas'],2)
        self.assertEqual(r['entropia_cruzada'],3.5)
        vazio=Dados();vazio.humanos={'validacao':np.array([],dtype=np.int64)}
        with self.assertRaisesRegex(ValueError,'diálogos humanos'):
            avaliar(Modelo(),vazio,'cpu',lotes=1,humanos=True)

    def test_sft_humano_retomado_reproduz_pesos_adam_rng_e_selecao(self):
        from testes_linguagem_profunda import TestesMatematicaLinguagem
        root=Path(__file__).parent
        with tempfile.TemporaryDirectory() as tmp:
            pasta=Path(tmp);corpus=pasta/'corpus';corpus.mkdir()
            TestesMatematicaLinguagem().fixture_corpus(corpus)
            base=[sys.executable,str(root/'scripts/treinar_linguagem_profunda.py'),
                  '--corpus',str(corpus),'--passos','4','--lote','2','--dimensao','24',
                  '--camadas','1','--cabecas','3','--contexto','16','--threads','1',
                  '--dispositivo','cpu','--avaliar-a-cada','2','--salvar-a-cada','2']
            def rodar(args):
                r=subprocess.run(args,capture_output=True,text=True,timeout=90)
                self.assertEqual(r.returncode,0,r.stderr)
            rodar(base+['--saida',str(pasta/'pre')])
            sft=base+['--fase','dialogo','--selecionar-melhor','--selecao-humana',
                      '--repeticao-linguagem','0']
            rodar(sft+['--saida',str(pasta/'inteiro'),'--inicial',str(pasta/'pre')])
            rodar(sft+['--saida',str(pasta/'retomado'),'--inicial',str(pasta/'pre'),'--parar-em','2'])
            rodar(sft+['--saida',str(pasta/'retomado'),'--retomar'])
            for nome in ('checkpoint.pt','melhor/checkpoint.pt'):
                a=torch.load(pasta/'inteiro'/nome,weights_only=True)
                b=torch.load(pasta/'retomado'/nome,weights_only=True)
                self.assertEqual(a['passo'],b['passo'])
                for k,peso in a['modelo'].items():
                    self.assertTrue(torch.equal(peso,b['modelo'][k]),k)
                for k,estado in a['otimizador']['state'].items():
                    for campo,valor in estado.items():
                        self.assertTrue(torch.equal(valor,b['otimizador']['state'][k][campo]))
                self.assertTrue(torch.equal(a['rng_torch'],b['rng_torch']))
                self.assertEqual(a['rng_numpy'],b['rng_numpy'])
                self.assertEqual(a['historico'],b['historico'])
            report=json.loads((pasta/'retomado/relatorio.json').read_text())
            self.assertIn('dialogo_humano_completa',report['execucao']['selecao']['criterio'])
            # Mudar a política para a média sintética/humana invalida a retomada.
            mudado=[x for x in sft if x!='--selecao-humana']
            r=subprocess.run(mudado+['--saida',str(pasta/'retomado'),'--retomar'],
                             capture_output=True,text=True,timeout=90)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('Retomada incompatível',r.stderr)


if __name__ == '__main__':
    unittest.main()
