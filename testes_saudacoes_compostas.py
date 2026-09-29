"""Regressões da captura do celular e de frases com atos misturados.

Casos pré-registrados antes de mudar o código. As regras não recebem
conhecimento factual novo e precisam atuar em domínios variados.
"""
import datetime
import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from web_core import responder_web


class TestesSaudacoesEIntencoes(unittest.TestCase):
    def test_repetir_saudacao_explicita_sem_relogio_do_servidor(self):
        for hora in (0, 3, 8, 11, 15, 18, 23):
            for fala, esperada in (
                ("Bom dia", "Bom dia!"),
                ("Boa tarde", "Boa tarde!"),
                ("Boa noite", "Boa noite!"),
                ("Bom dia, Crivo!", "Bom dia!"),
            ):
                with self.subTest(hora=hora, fala=fala):
                    bot = Crivo(agora=datetime.datetime(2026, 9, 29, hora, 31))
                    ident, resposta = bot.responder(fala)
                    self.assertEqual(ident, "social:oi")
                    self.assertTrue(resposta.startswith(esperada), resposta)

    def test_saudacoes_informais_sem_engolir_consultas(self):
        casos = (
            ("Eae, crivo. O que é HTML?", "web_html"),
            ("E aí, Crivo! O que é CSS?", "web_css"),
            ("Oi, crivo. O que é o Sol?", "sol"),
            ("Salve, Crivo. O que é fotossíntese?", "fotossintese"),
            ("Boa tarde, crivo. Qual é a relação entre Terra e Via Láctea?",
             "logica:ligacao"),
            ("Bom dia, Crivo. O que é HTML e CSS?", "composto:definicao"),
            ("Eae, crivo! A Terra é orbitada pela Lua?", "logica:orbita"),
        )
        for pergunta, id_esperado in casos:
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], id_esperado)
        for saudacao in ("Eae!", "E aí", "Oi, Crivo", "Salve, Crivo"):
            with self.subTest(saudacao=saudacao):
                self.assertEqual(Crivo().responder(saudacao)[0], "social:oi")

    def test_pergunta_da_captura_nao_vira_resposta_aleatoria(self):
        bot = Crivo(agora=datetime.datetime(2026, 9, 29, 15, 31))
        bot.responder("Bom dia")
        id_, resposta = bot.responder(
            "Eae, crivo. O que é andromeda e uma estrela?")
        self.assertEqual(id_, "duvida")
        self.assertIn("andromeda", resposta.lower())
        self.assertIn("estrela", resposta.lower())
        self.assertIn("ou", resposta.lower())
        self.assertNotIn("Até logo", resposta)
        self.assertNotIn("O Sol é", resposta)

    def test_pergunta_ambigua_em_muitos_conceitos_nao_inventa_fatos(self):
        for pergunta in (
            "O que é lumix e um dromix?",
            "O que é alforje e uma nebulosa?",
            "O que é rust e uma linguagem?",
            "O que é uma árvore e uma galáxia fictícia?",
        ):
            with self.subTest(pergunta=pergunta):
                id_, resposta = Crivo().responder(pergunta)
                self.assertEqual(id_, "duvida")
                self.assertIn("ou", resposta.lower())
                self.assertNotIn("JavaScript pode reagir", resposta)

    def test_compostos_conhecidos_permanecem_funcionais(self):
        for pergunta, esperado in (
            ("O que é HTML e CSS?", "composto:definicao"),
            ("O que é o Sol e a Lua?", "composto:definicao"),
            ("O que é rotação e translação?", "rotacao_translacao"),
            ("O que é HTML e Rust?", "fora"),
            ("O que é Sol e planeta quântico?", "fora"),
            ("Quais são as estações do ano?", "quais_estacoes"),
            ("Você falou da Lua?", "fora"),
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], esperado)

    def test_api_e_base_personalizada(self):
        dados = responder_web({"message": "Bom dia"})
        self.assertEqual(dados["id"], "social:oi")
        self.assertTrue(dados["response"].startswith("Bom dia!"))
        dados = responder_web({"message": "Eae, crivo. O que é HTML?"})
        self.assertEqual(dados["id"], "web_html")
        with tempfile.TemporaryDirectory() as tmp:
            arq = Path(tmp) / "conhecimento.json"
            arq.write_text(json.dumps([
                {"id": "lumix", "topico": "clima",
                 "perguntas": ["o que é lumix"],
                 "resposta": "Lumix é um termo de teste."},
                {"id": "dromix", "topico": "clima",
                 "perguntas": ["o que é dromix"],
                 "resposta": "Dromix é outro termo de teste."}
            ]), encoding="utf-8")
            bot = Crivo(arq)
            self.assertEqual(bot.responder(
                "Eae, Crivo. O que é lumix e dromix?")[0], "composto:definicao")
            id_, msg = bot.responder(
                "Oi, Crivo. O que é lumix e uma entidade inventada?")
            self.assertEqual(id_, "duvida")
            self.assertNotIn("Via Láctea", msg)


if __name__ == "__main__":
    unittest.main()
