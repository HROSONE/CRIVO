import json
import tempfile
import unittest
from pathlib import Path
from crivo import Crivo
from rede_neural import RedeCrivo
from avaliar_rede import avaliar


class TestesTreinoAutomatico(unittest.TestCase):
    def test_carrega_pesos_automaticamente(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            (pasta / "conhecimento.json").write_text(json.dumps([
                {"id": "agua", "topico": "clima", "perguntas": ["agua e chuva"],
                 "resposta": "Chuva."},
                {"id": "terra", "topico": "plantas", "perguntas": ["terra e planta"],
                 "resposta": "Planta."}
            ]), encoding="utf-8")
            RedeCrivo(["agua", "terra"], dimensao=32, ocultos=4).salvar(
                pasta / "rede_crivo.json")
            bot = Crivo(caminho_base=pasta / "conhecimento.json")
            self.assertIsNotNone(bot.rede)
            bot.ensinar("novo", "clima", ["um novo assunto"], "Novo.")
            self.assertIsNone(bot.rede)

    def test_avaliacao_separa_perguntas(self):
        base = [{"id": "a", "perguntas": ["sol quente", "calor do sol"]},
                {"id": "b", "perguntas": ["chuva forte", "agua de chuva"]}]
        resultado = avaliar(base, epocas=2)
        self.assertEqual(resultado["total"], 2)
        self.assertTrue(0 <= resultado["precisao"] <= 1)


if __name__ == "__main__":
    unittest.main()
