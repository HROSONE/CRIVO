import os
import unittest
from pathlib import Path
from unittest import mock

import motor_dialogo_17m
from api import chat


class TestesMotorDialogo17M(unittest.TestCase):
    def test_configuracao_explicita_prevalece(self):
        servidor = type('Servidor', (), {'modelo_linguagem': '/modelo/explicito'})()
        self.assertEqual(chat._modelo_linguagem(servidor), '/modelo/explicito')

    def test_chat_descobre_transformer_17m_sem_flag_manual(self):
        servidor = type('Servidor', (), {})()
        with mock.patch('motor_dialogo_17m.localizar', return_value='/modelo/17m'):
            self.assertEqual(chat._modelo_linguagem(servidor), '/modelo/17m')

    def test_env_e_primeiro_candidato(self):
        with mock.patch.dict(os.environ, {'CRIVO_TRANSFORMER_17M_DIR': '/tmp/base-17m'}):
            self.assertEqual(next(motor_dialogo_17m.candidatos()), Path('/tmp/base-17m'))

    def test_identidade_da_base_fica_presa_ao_sha_aprovado(self):
        self.assertEqual(motor_dialogo_17m.PESOS_SHA256,
                         '16102a72b21031b8bee2b4edfa633a359f7f08c5beab552b05f294e656b0cc67')
        self.assertEqual(motor_dialogo_17m.TOKENIZER_SHA256,
                         '6e3704ce921851122953b8ac20c05e3a131f9cf0fa3c76d6e2391c4ec3efc88f')

    def test_api_liga_dialogo_contextual_quando_modelo_existe(self):
        fonte = Path('api/chat.py').read_text(encoding='utf-8')
        self.assertIn('usar_dialogo_contextual=bool(modelo)', fonte)
        self.assertIn('modelo_linguagem=modelo', fonte)
        self.assertIn('smartest_dialogue_engine', fonte)

    def test_adaptador_aceita_somente_export_legado_exato(self):
        fonte = Path('dialogo_linguagem_profunda.py').read_text(encoding='utf-8')
        self.assertIn('17428224', fonte)
        self.assertIn("estado.get('passo') != 20000", fonte)
        self.assertIn('PESOS_SHA256', fonte)
        self.assertIn("'modelo': 'transformer_leitor_17m'", fonte)


if __name__ == '__main__':
    unittest.main()
