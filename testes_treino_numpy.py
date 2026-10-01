"""O acelerador precisa preservar o SGD e o aprendizado da rede original."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

from rede_neural import RedeCrivo


@unittest.skipUnless(importlib.util.find_spec("numpy"), "NumPy opcional ausente")
class TreinoNumpyTestes(unittest.TestCase):
    def test_gradientes_ordem_e_persistencia_equivalentes_ao_python(self):
        import numpy as np
        exemplos = [("regar o vaso", "regar"), ("molhar a planta", "regar"),
                    ("nuvem de chuva", "chuva"), ("vai chover", "chuva"),
                    ("", "chuva")]
        puro = RedeCrivo(["regar", "chuva"], 48, 8, semente=17)
        rapido = RedeCrivo(["regar", "chuva"], 48, 8, semente=17)
        for rede, acelerar in ((puro, False), (rapido, True)):
            rede.treinar(exemplos, epocas=9, taxa=.12, semente=31,
                         acelerar=acelerar)
        for nome in ("w1", "b1", "w2", "b2"):
            np.testing.assert_allclose(getattr(puro, nome), getattr(rapido, nome),
                                       rtol=1e-12, atol=1e-12)
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "rede.json"
            rapido.salvar(caminho)
            restaurada = RedeCrivo.carregar(caminho)
            for texto in ("regar", "chuva", "", "planta desconhecida"):
                a, b = puro.prever(texto), restaurada.prever(texto)
                self.assertEqual(a[0], b[0])
                self.assertAlmostEqual(a[1], b[1], places=12)

    def test_aprende_classes_distintas_desde_pesos_aleatorios(self):
        rede = RedeCrivo(["regar", "chuva"], 48, 8, semente=7)
        dados = [("regar vaso", "regar"), ("nuvem chuva", "chuva")]
        rede.treinar(dados, epocas=80, semente=13, acelerar=True)
        for texto, esperado in dados:
            rotulo, confianca = rede.prever(texto)
            self.assertEqual(rotulo, esperado)
            self.assertGreater(confianca, .9)
