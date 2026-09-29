import unittest
from avaliar_rede import validacao_cruzada


class TesteValidacaoCruzada(unittest.TestCase):
    def test_quantidades_diferentes_sem_duplicar_testes(self):
        entradas = [
            {"id": "a", "perguntas": ["a um", "a dois", "a tres"]},
            {"id": "b", "perguntas": ["b um", "b dois", "b tres", "b quatro"]}
        ]
        r = validacao_cruzada(entradas, epocas=1, ocultos=4, dimensao=32,
                             modo="portugues")
        self.assertEqual(r["total"], 7)
        self.assertEqual([f["total"] for f in r["dobras"]], [2, 2, 2, 1])

    def test_todas_as_perguntas_reservadas_uma_vez(self):
        dados = [
            {"id": "a", "perguntas": ["sol brilhante", "luz solar"]},
            {"id": "b", "perguntas": ["chuva caindo", "agua da chuva"]}
        ]
        resultado = validacao_cruzada(dados, epocas=2, ocultos=4, dimensao=32)
        self.assertEqual(resultado["total"], 4)
        self.assertEqual(len(resultado["dobras"]), 2)
        self.assertEqual(sum(d["total"] for d in resultado["dobras"]), 4)
        self.assertTrue(0 <= resultado["precisao"] <= 1)
        self.assertTrue(0 <= resultado["baseline_precisao"] <= 1)


if __name__ == "__main__":
    unittest.main()
