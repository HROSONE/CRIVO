import json
import tempfile
import unittest
from pathlib import Path
from crivo import Crivo

class Testes(unittest.TestCase):
    def test_ensino_persistente(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "conhecimento.json"
            arquivo.write_text(json.dumps([{"id":"chuva","topico":"clima","perguntas":["por que chove"],"resposta":"Condensacao."}]), encoding="utf-8")
            bot = Crivo(caminho_base=arquivo)
            bot.ensinar("neve", "clima", ["o que e neve"], "Agua congelada.")
            self.assertEqual(Crivo(caminho_base=arquivo).responder("o que e neve")[0], "neve")
            with self.assertRaises(ValueError):
                bot.ensinar("neve", "clima", ["neve"], "Duplicado")

    def test_historico(self):
        bot = Crivo()
        bot.responder("o que e fotossintese")
        self.assertEqual(bot.historico[-1]["id"], "fotossintese")

if __name__ == "__main__":
    unittest.main()
