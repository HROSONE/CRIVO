"""Casos adversariais novos: teste da representação, não de compreensão."""
import unittest
from rede_neural import caracteristicas
from experimento_ordem import caracteristicas_com_ordem, similaridade


PARES = [
    ("o cachorro perseguiu o gato", "o gato perseguiu o cachorro"),
    ("a menina ajudou o menino", "o menino ajudou a menina"),
    ("o vento derrubou a arvore", "a arvore derrubou o vento"),
    ("a chuva molhou a terra", "a terra molhou a chuva"),
]


class OrdemTestes(unittest.TestCase):
    def test_pares_sem_ordem_colidem(self):
        for a, b in PARES:
            self.assertEqual(caracteristicas(a, 512, "portugues_sem_filtro"),
                             caracteristicas(b, 512, "portugues_sem_filtro"))

    def test_novo_vetor_distingue_pares(self):
        for a, b in PARES:
            x = caracteristicas_com_ordem(a)
            y = caracteristicas_com_ordem(b)
            self.assertNotEqual(x, y)
            self.assertLess(similaridade(x, y), 1.0)

    def test_determinismo_e_norma(self):
        x = caracteristicas_com_ordem(PARES[0][0])
        self.assertEqual(x, caracteristicas_com_ordem(PARES[0][0]))
        self.assertAlmostEqual(similaridade(x, x), 1.0)

    def test_parametros(self):
        with self.assertRaises(ValueError):
            caracteristicas_com_ordem("texto", dimensao=0)
        with self.assertRaises(ValueError):
            caracteristicas_com_ordem("texto", peso_ordem=-1)


if __name__ == "__main__":
    unittest.main()
