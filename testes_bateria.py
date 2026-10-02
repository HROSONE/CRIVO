"""Catraca da bateria de medição: nenhuma mudança pode piorar os números.

O conjunto retido é avaliado só pelos números agregados; não ajuste código
olhando suas falhas individuais.
"""
import json
import unittest
from pathlib import Path

from scripts.avaliar_bateria import avaliar

LIMIARES = json.loads((Path(__file__).parent / "avaliacoes" / "bateria_v1" /
                       "limiares.json").read_text(encoding="utf-8"))


class TestesBateria(unittest.TestCase):
    def conferir(self, conjunto):
        resumo, _, _ = avaliar(conjunto)
        limite = LIMIARES[conjunto]
        self.assertGreaterEqual(resumo["acertos_fato"], limite["acertos_fato_min"], resumo)
        self.assertLessEqual(resumo["assunto_errado"], limite["assunto_errado_max"], resumo)
        self.assertLessEqual(resumo["inventou"], limite["inventou_max"], resumo)
        self.assertGreaterEqual(resumo["dialogos_ok"], limite["dialogos_ok_min"], resumo)

    def test_dev(self):
        self.conferir("dev")

    def test_retido(self):
        self.conferir("retido")


if __name__ == "__main__":
    unittest.main()
