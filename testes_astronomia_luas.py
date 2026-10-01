"""Testes escritos antes da ampliação de luas do módulo 2 de Astronomia."""
import unittest
from pathlib import Path
from curriculo_mundo import ler_curriculo

ROOT = Path(__file__).resolve().parent

class TestesAstronomiaLuas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculo = ler_curriculo(ROOT / "conhecimento_mundo.json")
        cls.itens = {i["id"]: i for i in cls.curriculo["itens"]}

    def test_luas_prioritarias_com_proveniencia_limite_e_profundidade(self):
        esperadas = {
            "mundo_lua": ("Lua", "Terra"),
            "mundo_europa": ("Europa", "Júpiter"),
            "mundo_tita": ("Titã", "Saturno"),
            "mundo_encelado": ("Encélado", "Saturno"),
        }
        for ident, (nome, planeta) in esperadas.items():
            with self.subTest(lua=nome):
                item = self.itens[ident]
                self.assertEqual(item["area"], "astronomia")
                self.assertEqual(item["nome"], nome)
                fatos = item["fatos"]
                self.assertEqual(fatos[0]["papel"], "definicao")
                self.assertTrue(any(f.get("aspecto") == "formacao" for f in fatos))
                self.assertTrue(any(f.get("aspecto") == "funcionamento" for f in fatos))
                self.assertTrue(any(f["papel"] == "limite" for f in fatos))
                self.assertTrue(any(planeta.lower() in f["texto"].lower() for f in fatos))
                self.assertGreaterEqual(len(fatos), 5)
                for fato in fatos:
                    fonte = self.curriculo["fontes"][fato["fonte"]]
                    self.assertEqual(fonte["reutilizacao"], "dominio_publico")
                    self.assertIn("nasa", fonte["credito"].lower())

    def test_incerteza_cientifica_nao_vira_certeza(self):
        lua = self.itens["mundo_lua"]
        europa = self.itens["mundo_europa"]
        self.assertTrue(any("provavelmente" in f["texto"].lower() or
                            "modelo" in f["texto"].lower() or
                            "evidência" in f["texto"].lower()
                            for f in lua["fatos"]))
        self.assertTrue(any("evidência" in f["texto"].lower() or
                            "estim" in f["texto"].lower() or
                            "aguarda" in f["texto"].lower()
                            for f in europa["fatos"]))

    def test_nao_confundir_lua_generica_com_lua_da_terra(self):
        lua = self.itens["mundo_lua"]
        aliases = {a.casefold() for a in lua.get("aliases", [])}
        self.assertNotIn("lua", aliases)
        self.assertIn("lua da terra", aliases)

if __name__ == "__main__":
    unittest.main()
