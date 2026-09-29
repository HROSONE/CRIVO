import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from rede_neural import RedeCrivo


class TesteIntegracaoNeural(unittest.TestCase):
    def test_confirmacao_neural_preserva_alternativas_de_mais(self):
        sem_rede, com_rede = Crivo(), Crivo()
        sem_rede.rede = None
        com_rede.previsao_neural = lambda p: (
            com_rede.base[com_rede._ranking(p)[0][1]]["id"], 1.0)
        self.assertEqual(sem_rede.responder("cachorro"), com_rede.responder("cachorro"))
        esperado = sem_rede.responder("mais")
        self.assertNotEqual(esperado[0], "mais:fim")
        self.assertEqual(com_rede.responder("mais"), esperado)

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
