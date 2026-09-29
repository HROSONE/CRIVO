"""Regressão da conversa real e testes genéricos de referência demonstrativa.

Primeiro registra o problema antes da implementação. O analisador
não deve inventar nomes nem transformar 'você falou' em despedida.
"""
import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from web_core import responder_web


class TestesReferenciasConversacionais(unittest.TestCase):
    def test_reproduz_print_sem_confundir_falou_com_despedida(self):
        bot = Crivo()
        ident, resposta = bot.responder("O que é Andrômeda?")
        self.assertIn(ident, ("fora", "duvida"))
        ident, resposta = bot.responder("O que é Via Láctea?")
        self.assertEqual(ident, "via_lactea")
        ident, resposta = bot.responder(
            "Qual é o nome desse braço que você falou?")
        self.assertEqual(ident, "contexto:detalhe_ausente")
        self.assertIn("braço", resposta.lower())
        self.assertIn("não tenho", resposta.lower())
        self.assertNotIn("Até logo!", resposta)
        self.assertNotIn("Órion", resposta)  # a base NÃO fornece esse nome

    def test_reproduz_endpoint_serverless_com_historico_de_perguntas(self):
        dados = responder_web({
            "message": "Qual é o nome desse braço que você falou?",
            "history": ["O que é Andrômeda?", "O que é Via Láctea?"],
        })
        self.assertEqual(dados["id"], "contexto:detalhe_ausente")
        self.assertFalse(dados["has_proof"])
        self.assertIn("braço", dados["response"].lower())

    def test_outras_referencias_sobre_outros_conceitos(self):
        casos = (
            ("O que é o Sol?",
             "Que temperatura tem esse gás que você mencionou?", "gás"),
            ("O que é a Via Láctea?",
             "Como se chama esse braço que você citou?", "braço"),
            ("O que é a Via Láctea?",
             "Onde fica esse braço de que você falou?", "braço"),
        )
        for primeira, segunda, termo in casos:
            with self.subTest(pergunta=segunda):
                bot = Crivo()
                bot.responder(primeira)
                ident, resposta = bot.responder(segunda)
                self.assertEqual(ident, "contexto:detalhe_ausente")
                self.assertIn(termo, resposta.lower())
                self.assertNotIn("Até logo!", resposta)

    def test_sem_contexto_pede_esclarecimento(self):
        bot = Crivo()
        ident, resposta = bot.responder("Qual é o nome desse braço?")
        self.assertEqual(ident, "contexto:sem_referencia")
        self.assertIn("qual", resposta.lower())
        bot = Crivo()
        bot.responder("O que é Via Láctea?")
        bot.responder("Oi!")
        ident, resposta = bot.responder("Qual é o nome desse braço?")
        self.assertEqual(ident, "contexto:sem_referencia")
        bot = Crivo()
        bot.responder("O que é o Sol?")
        bot.responder("O que é a Lua?")
        ident, resposta = bot.responder("Qual é o nome desse gás?")
        self.assertEqual(ident, "contexto:sem_referencia")

    def test_grupo_social_nao_intercepta_perguntas_com_verbo_falou(self):
        casos = (
            ("Qual é o nome dessa coisa que você falou?", "contexto:sem_referencia"),
            ("O que você falou sobre o Sol?", "fora"),
            ("Você falou da Lua?", "fora"),
        )
        for pergunta, proibido in casos:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertNotEqual(ident, "social:tchau")
                self.assertNotEqual(resposta, "Até logo!")
        for pergunta in ("falou", "tchau", "até logo", "até mais", "adeus"):
            with self.subTest(despedida=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], "social:tchau")

    def test_base_personalizada_sem_nome_do_objeto(self):
        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta) / "conhecimento.json"
            base.write_text(json.dumps([{
                "id": "lumix",
                "topico": "clima",
                "perguntas": ["o que é lumix"],
                "resposta": "Lumix é uma nebulosa que abriga um anel cintilante."
            }], ensure_ascii=False), encoding="utf-8")
            bot = Crivo(base)
            self.assertEqual(bot.responder("O que é lumix?")[0], "lumix")
            ident, resposta = bot.responder(
                "Qual é o nome desse anel que você citou?")
            self.assertEqual(ident, "contexto:detalhe_ausente")
            self.assertIn("anel", resposta.lower())
            self.assertNotIn("Via Láctea", resposta)

    def test_conteudo_de_outro_turno_nao_e_assumido(self):
        bot = Crivo()
        bot.responder("O que é Via Láctea?")
        bot.responder("Isso que você falou de modo nenhum faz sentido.")
        ident, _ = bot.responder("Qual o nome desse braço?")
        self.assertEqual(ident, "contexto:sem_referencia")

    def test_preserva_outras_intencoes(self):
        for pergunta, esperado in (
            ("O que é Via Láctea?", "via_lactea"),
            ("O que é HTML e CSS?", "composto:definicao"),
            ("Qual é a relação entre Terra e Via Láctea?", "logica:ligacao"),
            ("Como usar input em Python?", "py_input"),
            ("Um pinguim é um ser vivo?", "logica:tipo_de"),
            ("Tudo bem com você?", "social:tudobem"),
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], esperado)


if __name__ == "__main__":
    unittest.main()
