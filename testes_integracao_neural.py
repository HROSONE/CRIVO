import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from rede_neural import RedeCrivo


class TesteIntegracaoNeural(unittest.TestCase):
    def test_integracao_e_compatibilidade(self):
        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta) / "base.json"
            pesos = Path(pasta) / "pesos.json"
            base.write_text(json.dumps([
                {"id": "planta", "topico": "plantas", "perguntas": ["regar planta"],
                 "resposta": "Use agua."},
                {"id": "animal", "topico": "animais", "perguntas": ["cuidar cachorro"],
                 "resposta": "Cuide do animal."}
            ]), encoding="utf-8")
            rede = RedeCrivo(["planta", "animal"], dimensao=64, ocultos=8)
            rede.treinar([("regar planta", "planta"),
                          ("cuidar cachorro", "animal")], epocas=80)
            rede.salvar(pesos)
            bot = Crivo(caminho_base=base)
            antes = bot.responder("regar planta")
            bot.carregar_rede(pesos)
            self.assertEqual(bot.responder("regar planta"), antes)
            self.assertIn(bot.previsao_neural("regar planta")[0],
                          {"planta", "animal"})

    def test_rejeita_pesos_incompativeis(self):
        with tempfile.TemporaryDirectory() as pasta:
            pesos = Path(pasta) / "pesos.json"
            RedeCrivo(["inexistente"]).salvar(pesos)
            with self.assertRaises(ValueError):
                Crivo().carregar_rede(pesos)


if __name__ == "__main__":
    unittest.main()
