"""Contratos de certificação do módulo 1: nunca promover por conteúdo cadastrado."""
import unittest
from pathlib import Path
from curriculo_mundo import ler_curriculo

ROOT = Path(__file__).resolve().parent

class TestesGateAstronomiaModulo1(unittest.TestCase):
    def test_curriculo_congelado_tem_vinte_termos_com_evidencia(self):
        dados = ler_curriculo(ROOT / "conhecimento_mundo.json")
        itens = [i for i in dados["itens"] if i["area"] == "astronomia"]
        self.assertGreaterEqual(len(itens), 20)
        for item in itens:
            with self.subTest(conceito=item["id"]):
                self.assertEqual(item["fatos"][0]["papel"], "definicao")
                self.assertTrue(any(f["papel"] == "limite" for f in item["fatos"]))
                self.assertTrue(all(f["fonte"] in dados["fontes"] for f in item["fatos"]))

    def test_gate_nao_promove_sem_prova_ci_e_revisao(self):
        from certificacao_astronomia import certificar_modulo
        base = dict(editorial=True, simbolico=1.0, neural=1.0,
                    controles=1.0, ci=True, revisao=True, prova_independente=True)
        for campo in base:
            with self.subTest(falta=campo):
                caso = dict(base)
                caso[campo] = False if isinstance(caso[campo], bool) else 0.0
                self.assertFalse(certificar_modulo(caso))
        self.assertTrue(certificar_modulo(base))

    def test_gate_recusa_metricas_ausentes_e_nota_inferior(self):
        from certificacao_astronomia import certificar_modulo
        self.assertFalse(certificar_modulo({}))
        caso = dict(editorial=True, simbolico=0.899, neural=1.0,
                    controles=1.0, ci=True, revisao=True, prova_independente=True)
        self.assertFalse(certificar_modulo(caso))
        caso["simbolico"] = 1.0
        caso["neural"] = 0.899
        self.assertFalse(certificar_modulo(caso))

if __name__ == "__main__":
    unittest.main()
