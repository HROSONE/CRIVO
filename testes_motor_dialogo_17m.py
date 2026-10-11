import os
import unittest
from pathlib import Path
from unittest import mock

import motor_dialogo_17m
from api import chat


class TestesMotorDialogo17M(unittest.TestCase):
    def test_configuracao_explicita_prevalece(self):
        servidor = type('Servidor', (), {'modelo_linguagem': '/modelo/explicito'})()
        with mock.patch.dict(os.environ, {'CRIVO_DISABLE_TRANSFORMER_17M': '1'}, clear=True):
            self.assertEqual(chat._modelo_linguagem(servidor), '/modelo/explicito')

    def test_chat_nao_autoativa_transformer_17m_so_por_existir_base(self):
        servidor = type('Servidor', (), {})()
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch('motor_dialogo_17m.localizar', return_value='/modelo/17m') as localizar:
            self.assertIsNone(chat._modelo_linguagem(servidor))
            localizar.assert_not_called()

    def test_chat_ativa_transformer_17m_apenas_com_opt_in(self):
        servidor = type('Servidor', (), {})()
        with mock.patch.dict(os.environ, {'CRIVO_ENABLE_TRANSFORMER_17M': '1'}, clear=True), \
             mock.patch('motor_dialogo_17m.localizar', return_value='/modelo/17m'):
            self.assertEqual(chat._modelo_linguagem(servidor), '/modelo/17m')

    def test_chat_recua_se_base_17m_nao_estiver_disponivel_mesmo_com_opt_in(self):
        servidor = type('Servidor', (), {})()
        with mock.patch.dict(os.environ, {'CRIVO_ENABLE_TRANSFORMER_17M': 'true'}, clear=True), \
             mock.patch('motor_dialogo_17m.localizar', return_value=None):
            self.assertIsNone(chat._modelo_linguagem(servidor))

    def test_chat_permite_trava_de_emergencia_mesmo_com_opt_in(self):
        servidor = type('Servidor', (), {})()
        with mock.patch.dict(os.environ, {
                'CRIVO_ENABLE_TRANSFORMER_17M': '1',
                'CRIVO_DISABLE_TRANSFORMER_17M': '1'}, clear=True), \
             mock.patch('motor_dialogo_17m.localizar', return_value='/modelo/17m') as localizar:
            self.assertIsNone(chat._modelo_linguagem(servidor))
            localizar.assert_not_called()

    def test_env_e_primeiro_candidato(self):
        with mock.patch.dict(os.environ, {'CRIVO_TRANSFORMER_17M_DIR': '/tmp/base-17m'}):
            self.assertEqual(next(motor_dialogo_17m.candidatos()), Path('/tmp/base-17m'))

    def test_identidade_da_base_fica_presa_ao_sha_aprovado(self):
        self.assertEqual(motor_dialogo_17m.PESOS_SHA256,
                         '16102a72b21031b8bee2b4edfa633a359f7f08c5beab552b05f294e656b0cc67')
        self.assertEqual(motor_dialogo_17m.TOKENIZER_SHA256,
                         '6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e')

    def test_api_exige_opt_in_sem_remover_fallback(self):
        fonte = Path('api/chat.py').read_text(encoding='utf-8')
        self.assertIn('CRIVO_ENABLE_TRANSFORMER_17M', fonte)
        self.assertIn('CRIVO_DISABLE_TRANSFORMER_17M', fonte)
        self.assertIn('usar_dialogo_contextual=bool(modelo)', fonte)
        self.assertIn('modelo_linguagem=modelo', fonte)
        self.assertIn('transformer["ativacao_automatica"] = False', fonte)
        self.assertIn('transformer["opt_in_necessario"] = True', fonte)
        self.assertIn('conversa_livre_opt_in_com_fallback', fonte)

    def test_adaptador_aceita_somente_export_legado_exato(self):
        fonte = Path('dialogo_linguagem_profunda.py').read_text(encoding='utf-8')
        self.assertIn('17428224', fonte)
        self.assertIn("estado.get('passo') != 20000", fonte)
        self.assertIn('PESOS_SHA256', fonte)
        self.assertIn("'modelo': 'transformer_leitor_17m'", fonte)


if __name__ == '__main__':
    unittest.main()