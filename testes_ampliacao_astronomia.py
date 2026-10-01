"""Confere integridade da ampliação científica antes do treinamento neural."""
import unittest
from pathlib import Path
from curriculo_mundo import carregar_base, ler_curriculo


class TestesAmpliacaoAstronomia(unittest.TestCase):
    def test_fichas_cientificas_e_limites(self):
        dados = ler_curriculo(Path(__file__).with_name("conhecimento_mundo.json"))
        itens = {x["id"]: x for x in dados["itens"]}
        for ident in ("mundo_exoplaneta", "mundo_gigante_gasoso",
                      "mundo_gigante_gelo", "mundo_disco_espalhado",
                      "mundo_nebulosa_solar"):
            with self.subTest(ident=ident):
                ficha = itens[ident]
                self.assertEqual(ficha["area"], "astronomia")
                self.assertTrue(any(f["papel"] == "definicao" for f in ficha["fatos"]))
                self.assertTrue(any(f["papel"] == "limite" for f in ficha["fatos"]))
                for fato in ficha["fatos"]:
                    self.assertIn(fato["fonte"], dados["fontes"])
                    self.assertTrue(dados["fontes"][fato["fonte"]]["url"].startswith("https://"))

    def test_treino_inclui_conceitos_novos(self):
        base = carregar_base(Path(__file__).with_name("conhecimento.json"))
        ids = {x["id"] for x in base}
        self.assertTrue({"mundo_exoplaneta", "mundo_gigante_gasoso",
                         "mundo_gigante_gelo", "mundo_disco_espalhado",
                         "mundo_nebulosa_solar"} <= ids)


if __name__ == "__main__":
    unittest.main()
