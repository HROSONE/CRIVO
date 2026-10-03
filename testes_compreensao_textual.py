"""Regressões para compreensão do pedido inteiro e retomada sem invenção."""
import unittest

from crivo import Crivo
from web_core import responder_web


class TestesCompreensaoTextual(unittest.TestCase):
    def test_aplica_raciocinio_simbolico_ao_labirinto(self):
        ident, resposta = Crivo().responder(
            "Explique como o raciocínio simbólico pode ser usado para resolver um "
            "problema de lógica complexo, como o enigma das portas de um labirinto.")
        self.assertEqual(ident, "texto:raciocinio_simbolico")
        self.assertIn("cada porta", resposta)
        self.assertIn("restrição", resposta)
        self.assertIn("contradizem", resposta)

    def test_arvore_binaria_nao_e_confundida_com_arvore_botanica(self):
        ident, resposta = Crivo().responder("O que é uma árvore binária?")
        self.assertEqual(ident, "conhecimento:arvore_binaria")
        self.assertIn("cada nó", resposta)
        self.assertNotIn("planta", resposta.lower())

    def test_funcionamento_do_aprendizado_de_maquina(self):
        ident, resposta = Crivo().responder("Como funciona o aprendizado de máquina?")
        self.assertEqual(ident, "escrita:explicacao")
        self.assertIn("treinamento", resposta)
        self.assertIn("rótulos", resposta)

    def test_retomada_explica_resposta_real_anterior(self):
        bot = Crivo()
        bot.responder("Como funciona o aprendizado de máquina?")
        ident, resposta = bot.responder(
            "Você consegue entender o significado do texto sobre aprendizado de "
            "máquina que enviei anteriormente?")
        self.assertEqual(ident, "texto:retomada")
        self.assertIn("ideia central", resposta)
        self.assertIn("treinamento", resposta)
        self.assertIn("sem inventar", resposta)

    def test_interpreta_comparacao_no_poema(self):
        ident, resposta = Crivo().responder(
            "Interprete este poema: 'O vento sopra forte sobre as árvores, "
            "balançando as folhas como um mar verde.'")
        self.assertEqual(ident, "texto:interpretacao")
        self.assertIn("comparação", resposta)
        self.assertIn("movimento", resposta)
        self.assertIn("não a única", resposta)

    def test_autodescricao_nao_vira_relato_do_usuario(self):
        ident, resposta = Crivo().responder(
            "Crivo, você é uma inteligência artificial em desenvolvimento, focada em "
            "conhecimento simbólico próprio e com limitações para interpretar contextos complexos.")
        self.assertEqual(ident, "social:autodescricao")
        self.assertIn("essencialmente correta", resposta)
        self.assertIn("descreve a mim", resposta)
        self.assertNotIn("Você contou", resposta)

    def test_endpoint_informa_mecanismo_de_compreensao(self):
        resultado = responder_web({
            "message": "Interprete esta frase: 'A cidade acordou nervosa.'"
        })
        self.assertEqual(resultado["id"], "texto:interpretacao")
        self.assertEqual(resultado["mechanism"], "compreensao_textual")


if __name__ == "__main__":
    unittest.main()
