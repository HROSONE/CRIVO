"""Executa um treino experimental real no CI, sem alterar o checkpoint de producao.

O checkpoint fica no ambiente efemero do job. Nao representa artefato
publicado nem modelo certificado. Treino integral exige pipeline de artefatos.
"""
import json
import tempfile
import unittest
from pathlib import Path
from rede_neural import RedeCrivo, assinatura_base, assinatura_regras, treinar_base
from curriculo_mundo import carregar_base


class TestesTreinoExperimental(unittest.TestCase):
    def test_checkpoint_dobrado_treinado_e_recarregado(self):
        raiz = Path(__file__).resolve().parent
        base = carregar_base(raiz / "conhecimento.json")
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "rede_96_treinada.json"
            rede = treinar_base(str(raiz / "conhecimento.json"), str(destino),
                                epocas=3, ocultos=96, dimensao=512,
                                modo="portugues")
            self.assertTrue(destino.is_file())
            recarregada = RedeCrivo.carregar(destino)
            self.assertEqual(recarregada.ocultos, 96)
            self.assertEqual(recarregada.assinatura_base, assinatura_base(base))
            self.assertEqual(recarregada.assinatura_regras, assinatura_regras("portugues"))
            self.assertEqual(rede.prever("O que e um planeta?"),
                             recarregada.prever("O que e um planeta?"))
            print("TREINO_EXECUTADO", json.dumps({
                "epocas": 3, "neuronios_ocultos": 96,
                "classes": len(rede.rotulos),
                "parametros": 512*96+96+96*len(rede.rotulos)+len(rede.rotulos),
                "checkpoint_gerado_e_recarregado": True,
                "persistencia": "temporaria_no_job_CI"
            }))


if __name__ == "__main__":
    unittest.main()
