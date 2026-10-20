"""Testes da síntese de funções Python a partir de exemplos (sintese_python.py)."""
import unittest

import sintese_python as sp


def executar(programa, entrada):
    """Roda o texto Python gerado pelo próprio motor (nunca código enviado pela pessoa)."""
    ns = {}
    exec(compile(programa, "<sintese>", "exec"), ns)
    return ns["resolver"](entrada)


class Traducao(unittest.TestCase):
    """O texto Python precisa dar o mesmo resultado que a avaliação interna, em toda expressão."""

    def conferir_banco(self, entradas, tipo):
        pontos = entradas + sp.gerar_sondas(entradas, tipo)
        banco = sp.Banco(pontos, "entrada", tipo, sp._constantes(entradas), 20000, n_exemplos=len(entradas))
        for tam in range(2, 5):
            for ex in sp._crescer(banco, tam):
                banco.add(ex, tam)
        conferidas = 0
        for tam, itens in banco.por_tam.items():
            for ex, vals in itens:
                programa = sp.programa_python(ex)
                for p, v in zip(pontos, vals):
                    if v is sp.ERRO:
                        continue
                    with self.subTest(programa=programa, entrada=p):
                        self.assertTrue(sp.iguais(executar(programa, p), v))
                conferidas += 1
        self.assertGreater(conferidas, 100)

    def test_numeros(self):
        self.conferir_banco([3, -2, 7], "int")

    def test_textos(self):
        self.conferir_banco(["casa", "Bom dia", "a"], "str")

    def test_listas(self):
        self.conferir_banco([[1, 2, 3], [-4, 0], [7]], "li")

    def test_listas_de_texto(self):
        self.conferir_banco([["bom", "dia"], ["a"], ["x", "y", "z"]], "ls")


class Busca(unittest.TestCase):
    def sint(self, pares):
        return sp.sintetizar([{"entrada": e, "saida": s} for e, s in pares])

    def test_soma(self):
        r = self.sint([([1, 2, 3], 6), ([10, -4], 6), ([], 0), ([2, 2], 4), ([5], 5)])
        self.assertIn("sum(entrada)", r["programa"])
        self.assertEqual(executar(r["programa"], [4, 4, 4]), 12)

    def test_palindromo_com_perguntas(self):
        pares = [("ovo", True), ("casa", False), ("arara", True)]
        ref = lambda s: s == s[::-1]
        for _ in range(10):
            r = self.sint(pares)
            if not r["pergunta"]:
                break
            p = r["pergunta"]["entrada"]
            pares.append((p, ref(p)))
        self.assertFalse(r["ambigua"])
        for s in ("radar", "ab", "python", "aba"):
            self.assertEqual(executar(r["programa"], s), ref(s))

    def test_ambiguidade_vira_pergunta(self):
        r = self.sint([(4, True), (7, False), (0, True)])
        self.assertTrue(r["ambigua"])
        self.assertEqual(len(r["pergunta"]["opcoes"]), 2)
        self.assertNotEqual(sp.chave(r["pergunta"]["opcoes"][0]), sp.chave(r["pergunta"]["opcoes"][1]))

    def test_tipos_estritos(self):
        # 2 e 2.0 são saídas diferentes; True não é 1.
        self.assertNotEqual(sp.chave(2), sp.chave(2.0))
        self.assertNotEqual(sp.chave(True), sp.chave(1))

    def test_entradas_misturadas(self):
        with self.assertRaises(sp.Falha):
            self.sint([(1, 2), ("a", "b")])

    def test_sem_solucao(self):
        r = sp.sintetizar([{"entrada": n, "saida": bin(n)[2:]} for n in (5, 2, 8)], limite_itens=5000)
        self.assertIsNone(r["programa"])


if __name__ == "__main__":
    unittest.main()
