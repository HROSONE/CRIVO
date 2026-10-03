"""Regressões do acervo ativo e do ciclo de programação experimental."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from conhecimento_programacao import ConhecimentoProgramacao
from programacao_neural import gate,extrair_codigo,pode_ativar
from scripts.preparar_programacao import exemplos
from scripts.escalar_programacao import PERFIS,estimar
ROOT=Path(__file__).resolve().parent
CAT=ROOT/'docs/pesquisa_conhecimento/programacao/catalogo-avancado.json'
DEPENDENCIAS=all(importlib.util.find_spec(n) for n in ('torch','tokenizers','numpy'))


class Recuperacao(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.c=ConhecimentoProgramacao(CAT)

    def test_conceitos_com_fontes_e_proveniencia(self):
        for q,esperado in [('Explique closures em JS','js_closures'),
                           ('Explique event loop em JavaScript','js_event-loop'),
                           ('Como funciona conditional types em TS?','ts_conditional')]:
            with self.subTest(q=q):
                u=self.c.buscar(q,1)[0]
                self.assertEqual(u['id'],esperado)
                self.assertEqual(len(u['catalogo_sha256']),64)
                self.assertTrue(u['referencias'][0]['url'].startswith('https://'))

    def test_linguagens_nao_misturadas(self):
        self.assertEqual(self.c.buscar('closures em typescript'),[])
        self.assertTrue(all(u['dominio']=='typescript' for u in self.c.buscar('conditional types em ts')))

    def test_recusa_desconhecido_negacao_e_pedido_de_codigo(self):
        for q in ['Explique banana cósmica','Explique que closures não existem','Crie closures em JS',
                  'Você poderia me explicar o que é uma árvore binária?',
                  'O que são árvore e árvore binária?', 'Explique closures em Python']:
            self.assertIsNone(self.c.responder(q))

    def test_integracao_http_e_preserva_perguntas_comuns(self):
        from web_core import responder_web,PedidoInvalido
        with patch('dialogo_linguagem_profunda.carregar_modelo',side_effect=AssertionError('não importar modelo')):
            r=responder_web({'message':'Explique event loop em javascript'})
        self.assertTrue(r['id'].startswith('programacao:'))
        self.assertEqual(r['mechanism'],'conhecimento_programacao')
        self.assertIn('html.spec.whatwg.org',r['response'])
        self.assertEqual(responder_web({'message':'O que é DNA?'})['id'],'conhecimento:dna')
        with self.assertRaises(PedidoInvalido):
            responder_web({'message':'oi','modelo_programacao':'/tmp/candidato'})

    def test_experimental_web_rotulado_sem_executar_codigo(self):
        from web_core import responder_web
        from unittest.mock import Mock
        gerador=Mock()
        gerador.gerar.return_value=dict(codigo="function resolver(n) { return n*2; }", completa=True)
        r=responder_web({'message':'Implemente function resolver(n) em javascript'},gerador_programacao=gerador)
        self.assertEqual(r['id'],'programacao:experimental')
        self.assertTrue(r['experimental_programming'])
        self.assertIn('código não verificado',r['response'])
        gerador.gerar.assert_called_once()

    def test_servidor_recusa_ativar_candidato_sem_gate(self):
        from web_local import criar_servidor
        with patch('programacao_neural.GeradorProgramacao',side_effect=AssertionError('não carregar')):
            with self.assertRaisesRegex(ValueError,'Modelo não aprovado'):
                criar_servidor(port=0,modelo_programacao='/nao-aprovado')

    def test_base_personalizada_nao_herda_acervo(self):
        from crivo import Crivo
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'conhecimento.json';base.write_text((ROOT/'conhecimento.json').read_text())
            b=Crivo(base,usar_linguagem_neural=False)
            self.assertIsNone(b.programacao)
            self.assertFalse(b.responder('Explique closures em javascript')[0].startswith('programacao:'))


class DadosEGates(unittest.TestCase):
    def test_familias_e_alvos_nao_vazam(self):
        grupos={};alvos={}
        for e in exemplos():
            grupos.setdefault(e['grupo'],set()).add(e['split'])
            alvos.setdefault(e['resposta'].strip(),set()).add(e['split'])
        self.assertTrue(all(len(s)==1 for s in grupos.values()))
        self.assertTrue(all(len(s)==1 for s in alvos.values()))
        self.assertGreater(len(grupos),300)
        for s in ('treino','validacao','teste'): self.assertTrue(any(s in g for g in grupos.values()))

    def test_curriculo_tem_codigo_testado_e_familias_separadas(self):
        tarefas=json.loads((ROOT/'dados/programacao/curriculo.json').read_text())['tarefas']
        self.assertEqual(len(tarefas),3600)
        grupos={}
        for t in tarefas:
            self.assertEqual(len(t['casos']),4)
            grupos.setdefault(t['familia'],set()).add(t['split'])
        self.assertEqual(len(grupos),30)
        self.assertTrue(all(len(s)==1 for s in grupos.values()))
        self.assertEqual(sum(s=={'treino'} for s in grupos.values()),24)

    def test_algoritmos_reproduziveis_e_curriculo_nao_domina_por_variantes(self):
        from scripts.gerar_algoritmos_programacao import gerar
        tarefas=json.loads((ROOT/'dados/programacao/algoritmos.json').read_text())
        self.assertEqual(gerar(),tarefas)
        self.assertEqual(len({t['familia'] for t in tarefas['tarefas']}),30)
        es=exemplos()
        simples=[e for e in es if e['grupo'].startswith('codigo:curriculo_')]
        self.assertEqual(len(simples),240)
        self.assertTrue(any(e['grupo']=='codigo:alg_mdc_euclides' for e in es))

    def test_benchmark_reservado_nunca_entra_no_treino(self):
        ts=json.loads((ROOT/'dados/programacao/tarefas.json').read_text())['tarefas']
        treino={e['grupo'] for e in exemplos() if e['split']=='treino'}
        self.assertTrue(all('codigo:'+t['familia'] not in treino for t in ts if t['split']=='teste'))
        self.assertEqual(len([t for t in ts if t['split']=='teste']),16)

    def test_gate_exige_execucao_cobertura_regressao_revisao(self):
        r=dict(particao='teste',familias=50,isolamento=True,regressao_geral_aprovada=True,
               revisao_independente=True,linguagens={l:dict(total=50,completas=50,pass_at_1=.94)
                   for l in ('javascript','typescript')})
        self.assertTrue(gate(r)['aprovado'])
        self.assertFalse(gate(dict(r,runtimes={'quickjs_sem_apis_host':100}))['aprovado'])
        for campo,valor in [('isolamento',False),('familias',8),('particao','treino'),
                             ('regressao_geral_aprovada',False),('revisao_independente',False)]:
            self.assertFalse(gate(dict(r,**{campo:valor}))['aprovado'])

    def test_extracao_nao_repara_automaticamente_codigo_incompleto(self):
        self.assertEqual(extrair_codigo('```ts\nfunction resolver() {}\n```'),'function resolver() {}')
        self.assertEqual(extrair_codigo('function resolver('),'function resolver(')

    def test_verificacao_bloqueia_execucao_sem_sandbox(self):
        if not shutil.which('node'): self.skipTest('Node ausente')
        from verificacao_codigo import verificar
        with patch('verificacao_codigo.sandbox_args',return_value=None), patch('verificacao_codigo.quickjs_disponivel',return_value=False):
            r=verificar('function resolver(n) { return n*2; }','javascript',[dict(entrada=[2],saida=4)])
        self.assertTrue(r['compila']);self.assertFalse(r['executado']);self.assertFalse(r['funcional'])

    def test_quickjs_resultados_erros_sem_host_e_loop(self):
        from verificacao_codigo import verificar, quickjs_disponivel
        if not quickjs_disponivel() or not shutil.which('node'):
            self.skipTest('QuickJS/Node ausente')
        with patch('verificacao_codigo.sandbox_args', return_value=None):
            casos = [dict(entrada=[2], saida=4)]
            r = verificar('function resolver(n) { return n*2; }', 'javascript', casos)
            self.assertTrue(r['funcional']); self.assertEqual(r['runtime'], 'quickjs_sem_apis_host')
            for codigo in ['function resolver(n) { return n; }',
                           'function resolver(n) { return process.env; }',
                           'function resolver(n) { return require("fs"); }',
                           'function resolver(n) { return fetch("https://example.com"); }',
                           'function resolver(n) { while (true) {} }']:
                with self.subTest(codigo=codigo):
                    r = verificar(codigo, 'javascript', casos)
                    self.assertTrue(r['executado']); self.assertFalse(r['funcional'])

    def test_sintaxe_invalida_nao_executa(self):
        if not shutil.which('node'): self.skipTest('Node ausente')
        from verificacao_codigo import verificar
        with patch('verificacao_codigo.sandbox_args',side_effect=AssertionError('não executar')):
            r=verificar('function resolver(','javascript',[])
        self.assertFalse(r['compila']);self.assertFalse(r['executado'])

    def test_saida_zero_sem_protocolo_nao_certifica_testes(self):
        if not shutil.which('node'): self.skipTest('Node ausente')
        from verificacao_codigo import verificar
        with patch('verificacao_codigo.sandbox_args',return_value=['sandbox']), patch(
                'verificacao_codigo.comando',return_value=(True,'')):
            r=verificar('function resolver(n) { return n*2; }','javascript',[dict(entrada=[2],saida=4)])
        self.assertTrue(r['compila']);self.assertTrue(r['executado']);self.assertFalse(r['funcional'])

    def test_comparacao_distingue_booleano_numero_e_mutacao(self):
        from verificacao_codigo import iguais
        self.assertFalse(iguais([True],[1]))
        self.assertFalse(iguais([1,2],[2,1]))
        self.assertTrue(iguais([4.0],[4]))


@unittest.skipUnless(DEPENDENCIAS,'Laboratório opcional requer torch/tokenizers/numpy')
class Laboratorio(unittest.TestCase):
    def test_contagem_de_parametros_de_todos_os_perfis(self):
        from linguagem_profunda import Configuracao,LinguagemProfunda
        for nome,c in PERFIS.items():
            with self.subTest(perfil=nome):
                m=LinguagemProfunda(Configuracao(**c))
                self.assertEqual(sum(p.numel() for p in m.parameters()),estimar(nome)['parametros'])
        self.assertEqual(estimar('atual')['parametros'],2612352)

    def test_tokenizer_preservado_manifesto_e_dados_carregaveis(self):
        from scripts.preparar_programacao import preparar,sha
        from scripts.treinar_linguagem_profunda import Corpus
        with tempfile.TemporaryDirectory() as d:
            tok=ROOT/'artefatos/linguagem_profunda/tokenizer.json'
            m=preparar(d,256,tok)
            self.assertEqual(m['arquivos']['tokenizer.json'],sha(tok))
            corpus=Corpus(d,256)
            import numpy as np
            x,y=corpus.lote('treino','dialogo',2,np.random.default_rng(4),'cpu')
            self.assertEqual(tuple(x.shape),(2,256));self.assertTrue((y==-100).any())
            with self.assertRaises(ValueError): preparar(d,256,tok)
            p=Path(d)/'dialogos_treino.jsonl';p.write_text('alterado')
            with self.assertRaisesRegex(ValueError,'Corpus alterado'): Corpus(d,256)


if __name__=='__main__': unittest.main()
