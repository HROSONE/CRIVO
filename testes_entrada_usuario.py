"""Regressões de interpretação de entrada humana, DOM e contexto social.

Casos utilizados no desenvolvimento: não são validação cega.
"""
import unittest
from crivo import Crivo


class TestesEntradaUsuario(unittest.TestCase):
    def test_entrada_humana_no_terminal_python(self):
        for pergunta in (
            "Como obter informações de quem usa o programa Python?",
            "Como perguntar o nome da pessoa que abriu o programa Python?",
            "Como pedir a idade para alguém digitar no terminal Python?",
            "Em Python, como fazer uma pergunta e aguardar digitação?",
            "Como capturar o que a pessoa escreveu no console Python?",
            "Quero obter resposta digitada pelo usuário em Python",
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], "py_input")

    def test_nao_confundir_entrada_terminal_com_fontes_nao_ensinadas(self):
        for pergunta in (
            "Como solicitar documento de usuário por formulário web em Python?",
            "Como capturar dados de pessoa pela câmera usando Python?",
            "Como solicitar dados de uma pessoa pelo WhatsApp usando Python?",
            "Como consultar uma API de cadastro por Python?",
        ):
            with self.subTest(pergunta=pergunta):
                self.assertIn(Crivo().responder(pergunta)[0], ("fora", "duvida"))

    def test_nao_interceptar_pergunta_sobre_nome_do_usuario_com_social(self):
        self.assertEqual(
            Crivo().responder("Em Python, como solicitar que uma pessoa informe seu nome?")[0],
            "py_input",
        )
        for pergunta in ("Qual é seu nome?", "Qual é o seu nome?", "Me diga seu nome"):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], "social:quem")

    def test_funciona_generico_quando_o_assunto_esta_cadastrado(self):
        self.assertEqual(Crivo().responder("Como funciona a fotossíntese?")[0],
                         "fotossintese")
        self.assertEqual(Crivo().responder("Como funciona a Lua?")[0], "lua")
        self.assertIn(Crivo().responder("Como funciona uma usina nuclear?")[0],
                      ("fora", "duvida"))

    def test_campo_html_em_javascript_eh_dom(self):
        self.assertEqual(
            Crivo().responder("Como ler valor de um campo HTML com JavaScript?")[0],
            "js_dom",
        )
        self.assertEqual(
            Crivo().responder("Como selecionar uma tag HTML usando JavaScript?")[0],
            "js_dom",
        )


if __name__ == "__main__":
    unittest.main()
