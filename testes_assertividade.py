import datetime
import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from avaliar_recuperador import avaliar


# Casos de regressão de desenvolvimento; não são um teste cego.
CASOS = [
    ("Oi, como cuidar de cachorro?", "cuidar_cachorro"),
    ("Bom dia, o que é fotossíntese?", "fotossintese"),
    ("Como cozinhar arroz, obrigado!", "arroz"),
    ("que horas são em Portugal?", "fuso"),
    ("quantas estações existem?", "quais_estacoes"),
    ("o que cachorro não pode comer", "cuidar_cachorro"),
    ("qual planeta não tem anéis?", "duvida"),
    ("posso não regar a planta?", "duvida"),
    ("o que é fotossintesse?", "fotossintese"),
    ("como cuidar de cachoro?", "cuidar_cachorro"),
    ("como cuidar de gatto?", "cuidar_gato"),
    ("quero poupar energia", "energia"),
    ("como remover mofo", "mofo"),
    ("qual bicho é mais veloz?", "mais_rapido"),
    ("o que é uma planta tóxica?", "plantas_toxicas"),
    ("planta", "duvida"),
    ("o que é buraco negro?", "fora"),
    ("sol blockchain", "fora"),
    ("qual planta tem bluetooth?", "fora"),
]


class TestesAssertividade(unittest.TestCase):
    def test_regressoes_de_conversa(self):
        for pergunta, esperado in CASOS:
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], esperado)

    def test_relogio_nao_responde_data_historica(self):
        bot = Crivo(agora=datetime.datetime(2026, 9, 29, 15, 30))
        self.assertEqual(bot.responder("que horas são?")[1], "Agora são 15:30.")
        for pergunta in ("em que ano o Brasil foi descoberto?",
                         "qual a data da descoberta de Marte?",
                         "em que mês começa o inverno?"):
            self.assertFalse(bot.responder(pergunta)[0].startswith("dyn:"))

    def test_mais_nao_recupera_assunto_abandonado(self):
        bot = Crivo()
        bot.responder("como cuidar de cachorro?")
        bot.responder("qual a capital da Austrália?")
        self.assertEqual(bot.responder("mais")[0], "mais:fim")

    def test_historico_inclui_pergunta_exata(self):
        bot = Crivo()
        bot.responder("quantas estações existem?")
        self.assertEqual(bot.historico[-1]["id"], "quais_estacoes")

    def test_duplicar_exemplos_nao_aumenta_pontos(self):
        bot = Crivo()
        antes = bot._ranking("como regar minhas plantas?")
        for e in bot.base:
            e["perguntas"] *= 3
        bot._indexar()
        self.assertEqual(bot._ranking("como regar minhas plantas?"), antes)

    def test_ambiguidade_nao_e_ignorada_pela_rede(self):
        bot = Crivo()
        self.assertEqual(bot.responder("planta")[0], "duvida")
        bot.previsao_neural = lambda p: (bot.base[bot._ranking(p)[0][1]]["id"], 1.0)
        self.assertEqual(bot.responder("planta")[0], "duvida")

    def test_base_personalizada_sem_ids_especiais(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "base.json"
            caminho.write_text(json.dumps([{"id": "flor", "topico": "plantas",
                "perguntas": ["uma flor"], "resposta": "Uma flor."}]), encoding="utf-8")
            bot = Crivo(caminho)
            for p in ("por que existem as estações?", "como as abelhas ajudam?"):
                self.assertIn(bot.responder(p)[0], ("fora", "duvida"))

    def test_avaliacao_remove_a_pergunta_testada(self):
        observadas = []
        class Espiao(Crivo):
            def responder(self, texto):
                observadas.append(texto)
                assert all(texto not in e["perguntas"] for e in self.base)
                return super().responder(texto)
        base = [{"id": "planta", "topico": "plantas", "perguntas": ["planta verde", "folha verde"],
                 "resposta": "Uma planta verde."}]
        resultado = avaliar(base, Espiao)
        self.assertEqual(observadas, base[0]["perguntas"])
        self.assertEqual(resultado["total"], 2)


if __name__ == "__main__":
    unittest.main()
