"""Testes para não regredir nas regras técnicas introduzidas no PR #8.

Estes casos já fizeram parte da investigação e são regressões de
desenvolvimento; não constituem medição cega de generalização.
"""
import unittest

from crivo import Crivo


class TestesSemanticaProgramacao(unittest.TestCase):
    def test_entrada_escrita_eh_entrada_python(self):
        for pergunta in (
            "Preciso coletar uma informação digitada em Python",
            "Como receber dados do teclado em Python",
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], "py_input")

    def test_javascript_manipulando_html(self):
        self.assertEqual(
            Crivo().responder("Como selecionar um nó do HTML pelo JavaScript?")[0],
            "js_dom",
        )

    def test_const_sem_liberar_negacoes_genericas(self):
        self.assertEqual(
            Crivo().responder("Em JavaScript, como declarar uma variável que não muda?")[0],
            "js_variavel",
        )
        for pergunta in ("posso não regar a planta?", "qual planeta não tem anéis?"):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], "duvida")

    def test_revisar_mudancas_nao_eh_fazer_commit(self):
        self.assertEqual(
            Crivo().responder("Como inspecionar diferenças entre duas alterações no Git?")[0],
            "git_diff",
        )
        self.assertEqual(
            Crivo().responder("Qual a diferença entre commit e push no Git?")[0],
            "git_commit",
        )

    def test_pergunta_sem_intencao_unica_pede_esclarecimento(self):
        self.assertEqual(Crivo().responder("Como funciona o sistema solar?")[0], "duvida")


if __name__ == "__main__":
    unittest.main()
