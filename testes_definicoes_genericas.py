"""Regressões de generalização linguística sem reutilizar a prova reservada."""
import tempfile
import unittest
from pathlib import Path
from composicao_textual import CompositorTextual


class TestesDefinicaoGenerica(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.compositor = CompositorTextual(
            [], Path(self.pasta.name) / "nao_existe.json", lambda _: None)
        self.compositor._adicionar({
            "id": "conceito_sintetico", "nome": "esfera fictícia",
            "aliases": ["globo experimental"],
            "fatos": [{"papel": "definicao", "texto": "Esfera fictícia é um objeto hipotético de teste."}],
        })
        self.compositor.expandidos.add("conceito_sintetico")

    def test_formulacoes_genericas_identificam_o_mesmo_conceito(self):
        for pergunta in (
            "Qual a definição de esfera fictícia?",
            "O que vem a ser uma esfera fictícia?",
            "Explique o significado de globo experimental.",
            "O que quer dizer esfera fictícia?",
            "Me diga o que é esfera fictícia.",
        ):
            with self.subTest(pergunta=pergunta):
                resposta = self.compositor.responder(pergunta)
                self.assertIsNotNone(resposta)
                self.assertEqual(resposta[0], "conhecimento:conceito_sintetico")
                self.assertIn("objeto hipotético", resposta[1])

    def test_qualificador_desconhecido_nao_herda_conceito(self):
        for pergunta in ("Defina esfera fictícia azul.",
                         "O que quer dizer globo experimental de Marte?"):
            with self.subTest(pergunta=pergunta):
                resultado = self.compositor.responder(pergunta)
                self.assertTrue(resultado is None or
                                resultado[0] != "conhecimento:conceito_sintetico")


if __name__ == "__main__":
    unittest.main()
