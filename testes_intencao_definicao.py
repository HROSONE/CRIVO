"""Regressões de perguntas definicionais, criadas antes da correção.

Um termo coincidente não basta para responder "o que é X" com
uma explicação "por que X acontece". Ainda não são testes cegos.
"""
import unittest
from crivo import Crivo
from web_core import responder_web


class TestesIntencaoDefinicao(unittest.TestCase):
    def test_definicao_de_arvore_no_chat_real(self):
        for pergunta in (
            "O que é uma árvore?", "o que é árvore",
            "Defina árvore.", "O que significa árvore?",
            "Poderia me explicar o que é uma árvore?",
        ):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "arvore")
                self.assertIn("planta", resposta.lower())
                self.assertIn("tronco", resposta.lower())
                self.assertNotIn("dias mais curtos", resposta.lower())

        via_web = responder_web({"message": "O que é uma árvore?"})
        self.assertEqual(via_web["id"], "arvore")
        self.assertIn("tronco", via_web["response"].lower())

    def test_definicoes_de_assuntos_existentes(self):
        for pergunta, esperada in (
            ("O que é fotossíntese?", "fotossintese"),
            ("O que é adubo?", "adubo"),
            ("O que é polinização?", "polinizacao"),
            ("O que é uma planta tóxica?", "plantas_toxicas"),
            ("O que é solstício?", "solsticio_equinocio"),
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], esperada)

    def test_definicao_desconhecida_nao_dispara_fenomeno_vizinho(self):
        for pergunta in (
            "O que é uma árvore genealógica?",
            # "árvore de Natal" saiu em 07/10/2026: a ficha do Natal cita a árvore
            # entre os símbolos da festa, e responder com ela é correto.
            "O que é uma nuvem de pontos?",
            "O que é uma nuvem?",
            "O que é uma folha?",
            "O que é uma semente?",
            "Defina árvore quântica.",
        ):
            with self.subTest(pergunta=pergunta):
                obtido, resposta = Crivo().responder(pergunta)
                self.assertIn(obtido, ("fora", "duvida"))
                self.assertNotIn("Com dias mais curtos", resposta)
                self.assertNotIn("tronco lenhoso", resposta)

    def test_pergunta_causal_sobre_arvore_preservada(self):
        for pergunta in (
            "Por que as árvores perdem as folhas?",
            "Por que as folhas caem no outono?",
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], "folhas_outono")

    def test_definicao_tem_que_apontar_ao_conceito_alvo(self):
        # Conhecer muitos fatos com o termo X não significa conhecer o
        # conceito X. Não recuperar resposta só por coincidência lexical.
        pergunta = "O que é uma folha virtual no inverno?"
        obtido, _ = Crivo().responder(pergunta)
        self.assertIn(obtido, ("fora", "duvida"))


if __name__ == "__main__":
    unittest.main()
