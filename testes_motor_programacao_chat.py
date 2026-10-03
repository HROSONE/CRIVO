"""Ligação real entre conversa, contrato, executor próprio e HTTP."""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen

from programacao_chat import MotorCodigoChat
from crivo import Crivo
from web_core import responder_web
from web_local import criar_servidor

CODIGO = 'Corrija este código JavaScript:\n```javascript\nreturn entrada - 2;\n```'
EXEMPLOS = 'Exemplos: [{"entrada":0,"saida":2},{"entrada":3,"saida":5}]'
COMPLETO = CODIGO+'\n'+EXEMPLOS


class MotorChatTestes(unittest.TestCase):
    def test_mencionar_codigo_em_um_texto_nao_aciona_programacao(self):
        from programacao_chat import extrair
        for mensagem in ('Escreva um texto sobre HTML, CSS e JavaScript',
                         'Escreva um texto sobre clorofila e código genético',
                         'Analise o código genético', 'Crie um poema sobre JavaScript'):
            with self.subTest(mensagem=mensagem):
                self.assertIsNone(extrair(mensagem))
                m = MotorCodigoChat()
                m.responder(CODIGO)
                self.assertIsNone(m.responder(mensagem))
                self.assertIsNone(m.pendente)
        for mensagem in ('Escreva código', 'Corrija meu código', 'Gere JavaScript',
                         'Crie uma função TypeScript', 'Interprete este código JS'):
            with self.subTest(mensagem=mensagem):
                self.assertIsNotNone(extrair(mensagem))

    def test_empacotamento_respeita_limite_vercel_e_inclui_pesos(self):
        import fnmatch
        root = Path(__file__).resolve().parent
        pattern = json.loads((root/'vercel.json').read_text())['functions']['api/chat.py']['includeFiles']
        self.assertLessEqual(len(pattern), 256)
        patterns = pattern.strip('{}').split(',')
        for path in ('frutas.py', 'frutas.json', 'artefatos/efeitos_programacao/rede.npz',
                     'artefatos/efeitos_programacao/config.json',
                     'artefatos/efeitos_programacao/proveniencia.json',
                     'artefatos/linguagem_profunda/tokenizer.json'):
            self.assertTrue(any(fnmatch.fnmatchcase(path, p) for p in patterns), path)

    def test_crivo_usa_motor_preservando_fonte_e_conversa_normal(self):
        b = Crivo(usar_linguagem_neural=False)
        ident, resposta = b.responder(COMPLETO)
        self.assertEqual(ident, 'programacao:motor_diagnostico')
        self.assertIn('entrada + 2', resposta)
        self.assertEqual(b.historico[-1]['mecanismo'], 'motor_programacao_proprio')
        self.assertFalse(b.motor_codigo.ultimo['casos_reservados_consultados'])
        self.assertTrue(b.motor_codigo.ultimo['atende_desenvolvimento'])
        self.assertTrue(b.responder('Olá')[0].startswith('social:'))
        self.assertIsNone(b.motor_codigo.ultimo)

    def test_dois_turnos_reconstroem_contrato_em_requisicoes_independentes(self):
        r = responder_web({'message': CODIGO})
        self.assertEqual(r['id'], 'programacao:motor_pendente')
        r = responder_web({'message': EXEMPLOS, 'history':[CODIGO]})
        self.assertEqual(r['id'], 'programacao:motor_diagnostico')
        self.assertTrue(r['code_analysis']['atende_desenvolvimento'])
        self.assertFalse(r['has_proof'])
        self.assertEqual(r['mechanism'], 'motor_programacao_proprio')
        isolada = responder_web({'message': EXEMPLOS})
        self.assertNotIn('code_analysis', isolada)

    def test_replay_nao_reexecuta_buscas(self):
        with patch('programacao_chat.diagnosticar', side_effect=AssertionError('Reexecutou busca')):
            r = responder_web({'message':'Oi', 'history':[COMPLETO]})
        self.assertTrue(r['id'].startswith('social:'))
        self.assertNotIn('code_analysis', r)

    def test_interpreta_funcao_typescript_e_rastreia_estados(self):
        m = MotorCodigoChat()
        ident, texto = m.responder('Interprete este código TypeScript:\n```typescript\nfunction resolver(entrada: number): number { let total = entrada + 2; return total; }\n```\nEntrada: 3')
        self.assertEqual(ident, 'programacao:motor_interpretacao')
        self.assertEqual(m.ultimo['resultado'], 5)
        self.assertIn('Estados observados', texto)

    def test_sintese_e_regressao_de_tipo(self):
        m = MotorCodigoChat()
        ident, texto = m.responder('Gere JavaScript com estes exemplos:\n'+EXEMPLOS)
        self.assertEqual(ident, 'programacao:motor_sintese')
        self.assertTrue(m.ultimo['atende_desenvolvimento'])
        from interpretacao_estruturas import executar
        self.assertEqual(executar(m.ultimo['corpo'], 7)['resultado'], 9)
        ident, _ = m.responder(json.dumps({'acao':'gerar','tipo':'array','desenvolvimento':[{'entrada':2,'saida':4}]}))
        self.assertEqual(ident, 'programacao:motor_limite')

    def test_exemplos_primeiro_e_nova_fonte_nao_herda_outro_contrato(self):
        m = MotorCodigoChat()
        m.responder('Corrija código JavaScript.\n'+EXEMPLOS)
        ident, _ = m.responder('```javascript\nreturn entrada - 2;\n```')
        self.assertEqual(ident, 'programacao:motor_diagnostico')
        ident, _ = m.responder('Corrija este código JS:\n```javascript\nreturn entrada * 3;\n```')
        self.assertEqual(ident, 'programacao:motor_pendente')
        self.assertNotIn('desenvolvimento', m.pendente)

    def test_rejeita_host_referencia_reserva_tipos_e_orcamento(self):
        m = MotorCodigoChat()
        ruins = [
            {'codigo':'return process.exit();','entrada':0,'acao':'interpretar'},
            {'codigo':None,'entrada':0,'acao':'interpretar'},
            {'codigo':'return entrada;','reservados':[]},
            {'codigo':'return entrada;','referencia':'return 1;'},
            {'codigo':'return entrada;','desenvolvimento':[{'entrada':x,'saida':x} for x in range(7)]},
            {'codigo':'return entrada;','entrada':[[[0]*16]*16]*2,'acao':'interpretar'},
        ]
        for r in ruins:
            with self.subTest(r=r):
                self.assertEqual(m.responder(json.dumps(r))[0], 'programacao:motor_limite')
        m.responder(COMPLETO)
        self.assertIsNone(m.responder('Não execute este código:\n```js\nreturn entrada + 1;\n```'))

    def test_strings_mantem_grafia_e_erros_de_execucao_sao_respostas(self):
        m = MotorCodigoChat()
        m.responder('Interprete código JS:\n```js\nreturn "João + JS";\n```\nEntrada: 0')
        self.assertEqual(m.ultimo['resultado'], 'João + JS')
        ident, texto = m.responder('Execute código JS:\n```js\nwhile (true) { entrada; } return 0;\n```\nEntrada: 0')
        self.assertEqual(ident, 'programacao:motor_interpretacao')
        self.assertIn('Orçamento', texto)
        self.assertIn('erro', m.ultimo)

    def test_capacidades_descrevem_motor_ativo(self):
        b = Crivo(usar_linguagem_neural=False)
        self.assertIn('rastrear estados', b.responder('O que você consegue fazer?')[1])
        self.assertEqual(b.responder('Você consegue corrigir código?')[0], 'programacao:motor_ajuda')

    @unittest.skipUnless(importlib.util.find_spec('numpy'), 'NumPy opcional ausente')
    def test_modelo_proprio_em_uso_e_integridade_dos_pesos(self):
        from modelo_efeitos_chat import carregar_modelo, status_modelo
        r = responder_web({'message':COMPLETO})
        self.assertTrue(r['programming_effects_model']['active'])
        self.assertEqual(r['programming_effects_model']['parameters'], 1679)
        self.assertGreater(r['code_analysis']['efeitos_neurais']['comparados'], 0)
        self.assertEqual(r['code_analysis']['efeitos_neurais']['concordantes'], r['code_analysis']['efeitos_neurais']['comparados'])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/'proveniencia.json').write_text(json.dumps(dict(parametros=1679,pesos_externos=False,pesos_sha256='errado')))
            (p/'rede.npz').write_bytes(b'corrompido')
            self.assertFalse(status_modelo(d)['active'])
        # Não há cache de respostas ou dados do usuário.
        self.assertIsNotNone(carregar_modelo()[0])


class MotorChatHTTPTestes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = criar_servidor(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, kwargs={'poll_interval':.02}, daemon=True)
        cls.thread.start()
        cls.root = 'http://127.0.0.1:'+str(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_health_e_correcao_http_real(self):
        with urlopen(self.root+'/api/chat', timeout=8) as r:
            self.assertTrue(json.load(r)['programming_active'])
        req = Request(self.root+'/api/chat', data=json.dumps(dict(message=COMPLETO)).encode(), headers={'Content-Type':'application/json'})
        with urlopen(req, timeout=8) as r:
            data = json.load(r)
        self.assertTrue(data['code_analysis']['atende_desenvolvimento'])
        self.assertIn('function resolver', data['response'])

    def test_slice_utf16_isolado_chega_ao_navegador_sem_erro_http(self):
        m = 'Interprete código JS:\n```js\nreturn entrada.slice(0, 1);\n```\nEntrada: "💻"'
        req = Request(self.root+'/api/chat', data=json.dumps(dict(message=m)).encode(), headers={'Content-Type':'application/json'})
        with urlopen(req, timeout=8) as r:
            data = json.load(r)
        self.assertEqual(data['code_analysis']['resultado'], '\ud83d')
        self.assertIn('Resultado', data['response'])


if __name__=='__main__':
    unittest.main()
