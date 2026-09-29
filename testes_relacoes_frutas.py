"""Testes de raciocínio comparativo feitos antes do ajuste do PR #17.

Diferentemente de decorar pares, o mecanismo deve combinar os atributos
já curados de quaisquer dois itens do catálogo e reconhecer premissas falsas.
Estes casos passam a ser desenvolvimento após orientar alterações.
"""
import json
import unittest
from pathlib import Path

from crivo import Crivo
from frutas import ConhecimentoFrutas
from web_core import responder_web


class TestesComparacaoFrutas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = ConhecimentoFrutas.carregar(
            Path(__file__).with_name("frutas.json"))

    def test_correcao_cariopse_do_milho(self):
        texto = self.base.grupos["cariopse"]
        self.assertIn("parede do fruto", texto)
        self.assertIn("semente", texto)
        self.assertNotIn("contém o grão", texto)
        for item in ("milho", "arroz"):
            with self.subTest(item=item):
                identificador, resposta = Crivo().responder("O que é " + item + "?")
                self.assertEqual(identificador, "frutas:" + item)
                self.assertIn("parede do fruto", resposta.lower())

    def test_reconhecer_semelhanca_por_classe(self):
        for pergunta, esperados in (
            ("O que banana e uva têm em comum?",
             ("banana", "uva", "baga")),
            ("Qual a semelhança entre maçã e pera?",
             ("maçã", "pera", "pomo")),
            ("O que milho e arroz têm em comum?",
             ("milho", "arroz", "cariopse")),
            ("O que milho e uva têm em comum?",
             ("milho", "uva", "frutos")),
        ):
            with self.subTest(pergunta=pergunta):
                ident, texto = Crivo().responder(pergunta)
                self.assertEqual(ident, "frutas:relacao")
                for s in esperados:
                    self.assertIn(s, texto.lower())

    def test_comparacao_usa_diferencas_reais(self):
        for pergunta, esperados in (
            ("Por que milho e uva são frutos de tipos diferentes?",
             ("milho", "uva", "cariopse", "baga")),
            ("Qual a diferença entre manga e mangaba?",
             ("manga", "mangaba", "drupa", "baga")),
            ("Compare maçã e banana",
             ("maçã", "banana", "pomo", "baga")),
            ("Qual a diferença entre maçã e pera?",
             ("maçã", "pera", "pomo")),
            ("Por que tomate e pepino são frutos, mas usados como hortaliças?",
             ("tomate", "pepino", "hortaliça")),
        ):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertIn(ident, ("frutas:comparar", "frutas:relacao"))
                for s in esperados:
                    self.assertIn(s, resposta.lower())

    def test_premissa_sobre_classes_nao_e_aceita_cegamente(self):
        casos = (
            ("Maçã e pera são do mesmo tipo botânico?",
             ("sim", "pomo")),
            ("Banana e maçã são do mesmo tipo?",
             ("não", "baga", "pomo")),
            ("Milho e uva são do mesmo tipo botânico?",
             ("não", "cariopse", "baga")),
            ("Por que banana e uva são de tipos diferentes?",
             ("não", "baga")),
            ("Por que milho e arroz são do mesmo tipo?",
             ("cariopse", "milho", "arroz")),
        )
        for pergunta, esperados in casos:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "frutas:relacao")
                for s in esperados:
                    self.assertIn(s, resposta.lower())

    def test_limites_e_falsas_analogias(self):
        for pergunta in (
            "Banana e uva têm a mesma quantidade de açúcar?",
            "Milho e uva têm as mesmas sementes?",
            "Qual dos dois é melhor para diabetes, banana ou uva?",
            "Maçã e banana custam quanto hoje?",
            "O que manga e computador têm em comum?",
            "Qual a diferença entre manga e manga quântica?",
        ):
            with self.subTest(pergunta=pergunta):
                ident, _ = Crivo().responder(pergunta)
                self.assertNotIn(ident, ("frutas:comparar", "frutas:relacao"))
        ident, texto = Crivo().responder("O que caju e manga têm em comum?")
        self.assertEqual(ident, "frutas:relacao")
        self.assertIn("pseudofruto", texto.lower())
        self.assertNotIn("ambos são frutos botânicos", texto.lower())

    def test_comparacoes_de_todos_pares_nao_dependem_de_lista_fixa(self):
        # 63*62/2 = 1953 pares: o motor deve responder via mesmo código.
        vals = list(self.base.itens.values())
        total = 0
        for i, primeiro in enumerate(vals):
            for outro in vals[i + 1:]:
                pergunta = "Qual a diferença entre " + primeiro["nome"] + " e " + outro["nome"] + "?"
                resultado = self.base.responder(pergunta)
                with self.subTest(a=primeiro["id"], b=outro["id"]):
                    self.assertIsNotNone(resultado)
                    self.assertEqual(resultado[0], "frutas:comparar")
                    self.assertIn(primeiro["nome"], resultado[1])
                    self.assertIn(outro["nome"], resultado[1])
                total += 1
        self.assertEqual(total, 1953)

    def test_outros_assuntos_preservados_e_api(self):
        for pergunta, esperado in (
            ("O que é uma árvore?", "arvore"),
            ("O que é uma maçã?", "frutas:maca"),
            ("Por que as folhas caem no outono?", "folhas_outono"),
            ("O que é polinização?", "polinizacao"),
            ("Como usar input em Python?", "py_input"),
            ("Um pinguim é um ser vivo?", "logica:tipo_de"),
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], esperado)
        dado = responder_web({"message": "O que banana e uva têm em comum?"})
        self.assertEqual(dado["id"], "frutas:relacao")
        self.assertIn("baga", dado["response"].lower())


if __name__ == "__main__":
    unittest.main()
