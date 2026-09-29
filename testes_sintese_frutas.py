"""Regressões de síntese, escritas antes da implementação.

Mede seleção e apresentação de FATOS CADASTRADOS, não linguagem aberta.
Verifica também o mesmo algoritmo em todos os pares, sem hardcode de
uma resposta ao par banana-coco.
"""
import json
import unittest
from pathlib import Path

from crivo import Crivo
from frutas import ConhecimentoFrutas
from web_core import responder_web


class TestesSinteseFrutas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = ConhecimentoFrutas.carregar(
            Path(__file__).resolve().with_name("frutas.json"))

    def test_banana_coco_conciso_e_informativo(self):
        pergunta = "Qual a diferença entre banana e coco?"
        identificador, resposta = Crivo().responder(pergunta)
        self.assertEqual(identificador, "frutas:comparar")
        for termo in ("banana", "coco", "baga", "drupa",
                      "fibros", "semente"):
            with self.subTest(termo=termo):
                self.assertIn(termo, resposta.lower())
        self.assertLess(len(resposta), 500)
        # Não concatenar as descrições integrais em vez de sintetizar.
        self.assertNotIn(self.base.itens["banana"]["descricao"], resposta)
        self.assertNotIn(self.base.itens["coco"]["descricao"], resposta)
        self.assertNotIn("Classificação botânica: ", resposta)

    def test_sintese_modo_semelhanca_respeita_classes(self):
        casos = (
            ("O que banana e uva têm em comum?", ("banana", "uva", "baga")),
            ("O que milho e arroz têm em comum?", ("milho", "arroz", "cariopse")),
            ("O que milho e uva têm em comum?", ("milho", "uva", "frutos")),
            ("Qual a semelhança entre maçã e pera?", ("maçã", "pera", "pomo")),
        )
        for pergunta, termos in casos:
            with self.subTest(pergunta=pergunta):
                identificador, resposta = Crivo().responder(pergunta)
                self.assertEqual(identificador, "frutas:relacao")
                for termo in termos:
                    self.assertIn(termo, resposta.lower())
                self.assertLess(len(resposta), 470)

    def test_sintese_diferencas_relevantes_em_tipos_iguais(self):
        identificador, resposta = Crivo().responder(
            "Qual a diferença entre maçã e pera?")
        self.assertEqual(identificador, "frutas:comparar")
        for termo in ("maçã", "pera", "pomo"):
            self.assertIn(termo, resposta.lower())
        self.assertLess(len(resposta), 500)

    def test_nao_afirma_comparacoes_que_nao_sabe(self):
        for pergunta in (
            "Banana e coco têm o mesmo valor nutricional?",
            "Qual deles cura diabetes, banana ou coco?",
            "Banana e coco produzem a mesma quantidade de sementes?",
            "Qual vale mais hoje: banana ou coco?",
            "Compare banana e árvore binária.",
        ):
            with self.subTest(pergunta=pergunta):
                ident, _ = Crivo().responder(pergunta)
                self.assertNotIn(ident, ("frutas:comparar", "frutas:relacao"))

    def test_comparador_nao_confunde_semente_com_fruto_inteiro(self):
        for pergunta, fragmento in (
            ("O que feijão e arroz têm em comum?", "sementes"),
            ("O que amendoim e milho têm em comum?", "sementes"),
            ("O que caju e manga têm em comum?", "pseudofruto"),
        ):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "frutas:relacao")
                self.assertIn(fragmento, resposta.lower())
                self.assertNotIn("Ambos são frutos botânicos", resposta)
                self.assertLess(len(resposta), 600)

    def test_1953_pares_produzem_resposta_breve(self):
        itens = list(self.base.itens.values())
        total = 0
        for indice, a in enumerate(itens):
            for b in itens[indice + 1:]:
                pergunta = ("Qual a diferença entre " + a["nome"] +
                            " e " + b["nome"] + "?")
                dado = self.base.responder(pergunta)
                with self.subTest(a=a["id"], b=b["id"]):
                    self.assertIsNotNone(dado)
                    self.assertEqual(dado[0], "frutas:comparar")
                    self.assertIn(a["nome"], dado[1])
                    self.assertIn(b["nome"], dado[1])
                    self.assertLess(len(dado[1]), 650)
                    self.assertNotIn("Descrição de ", dado[1])
                total += 1
        self.assertEqual(total, 1953)

    def test_identidade_terminos_nomes_curtos(self):
        for pergunta, termos in (
            ("Compare coco e banana", ("coco", "banana")),
            ("Qual a diferença entre manga e mangaba?",
             ("manga", "mangaba", "drupa", "baga")),
            ("Por que banana e uva são de tipos diferentes?",
             ("não", "baga")),
            ("Tomate e pepino são do mesmo tipo botânico?",
             ("tomate", "pepino", "não")),
        ):
            with self.subTest(pergunta=pergunta):
                id_, resposta = Crivo().responder(pergunta)
                self.assertIn(id_, ("frutas:relacao", "frutas:comparar"))
                for termo in termos:
                    self.assertIn(termo, resposta.lower())

    def test_conhecimento_original_inalterado_e_endpoint(self):
        for pergunta, esperado in (
            ("O que é uma árvore?", "arvore"),
            ("O que são frutos?", "fruto"),
            ("O que é uma banana?", "frutas:banana"),
            ("Por que as folhas caem no outono?", "folhas_outono"),
            ("Um pinguim é um ser vivo?", "logica:tipo_de"),
            ("Como usar input em Python?", "py_input"),
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], esperado)
        dado = responder_web({"message": "Qual a diferença entre banana e coco?"})
        self.assertEqual(dado["id"], "frutas:comparar")
        self.assertIn("drupa", dado["response"].lower())
        self.assertLess(len(dado["response"]), 500)


if __name__ == "__main__":
    unittest.main()
