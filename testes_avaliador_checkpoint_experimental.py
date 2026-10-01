"""Regressoes para avaliar pesos experimentais sem tocar no modelo de producao."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from scripts import avaliar_astronomia_independente as avaliador


class TestesCheckpointExperimental(unittest.TestCase):
    def test_caminho_experimental_e_resolvido_sem_substituir_producao(self):
        with TemporaryDirectory() as pasta:
            candidato = Path(pasta) / "pesos.json"
            candidato.write_text("{}", encoding="utf-8")
            with patch.object(avaliador, "RAIZ", Path(pasta)):
                self.assertEqual(avaliador.resolver_modelo(str(candidato)), candidato.resolve())
                self.assertEqual(avaliador.resolver_modelo(None), Path(pasta) / "rede_crivo.json")

    def test_checkpoint_inexistente_e_rejeitado(self):
        with TemporaryDirectory() as pasta:
            with self.assertRaises(FileNotFoundError):
                avaliador.resolver_modelo(str(Path(pasta) / "ausente.json"))


if __name__ == "__main__":
    unittest.main()
