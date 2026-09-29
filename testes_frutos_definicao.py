"""Reprodução de bug real: definição de frutos confundida com polinização.

Testes registrados antes da implementação. Não equivalem a prova cega.
"""
import unittest

from crivo import Crivo
from web_core import responder_web


class TestesFrutosDefinicao(unittest.TestCase):
    def test_fruto_e_frutos_sao_definidos_em_linguagem_natural(self):
        perguntas = (
            "E o que são frutos?",
            "O que são frutos?",
            "O que é um fruto?",
            "Defina fruto.",
            "O que significa fruto?",
            "O que são frutas?",
            "O que é uma fruta?",
        )
        for pergunta in perguntas:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "fruto")
                self.assertIn("flor", resposta.lower())
                self.assertIn("sement", resposta.lower())
                self.assertNotIn("Polinização é o transporte", resposta)
                self.assertIn("fruto", resposta.lower())

    def test_conversa_da_captura_no_endpoint_real(self):
        dados = responder_web({
            "message": "E o que são frutos?",
            "history": ["O que é uma árvore?"],
        })
        self.assertEqual(dados["id"], "fruto")
        self.assertIn("sement", dados["response"].lower())

    def test_processos_relacionados_nao_se_tornam_definicoes(self):
        for pergunta, esperado in (
            ("Como as flores viram frutos?", "polinizacao"),
            ("O que é polinização?", "polinizacao"),
            ("Por que as folhas caem no outono?", "folhas_outono"),
            ("O que é uma árvore?", "arvore"),
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], esperado)

    def test_desconhecidos_e_compostos_nao_herdam_definicao(self):
        for pergunta in (
            "E o que são frutos quânticos?",
            "O que são árvores genealógicas?",
            "O que são flores artificiais?",
            "E o que são sementes?",
            "O que são nuvens de pontos?",
        ):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertIn(ident, ("fora", "duvida"))
                self.assertNotIn("Um fruto", resposta)

    def test_pergunta_de_tipos_de_dados_ja_ensinada(self):
        ident, resposta = Crivo().responder("O que são tipos de dados?")
        self.assertEqual(ident, "prog_tipos")
        self.assertIn("tipos", resposta.lower())


if __name__ == "__main__":
    unittest.main()
