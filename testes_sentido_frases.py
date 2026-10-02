"""Sentido das frases e memória do que a pessoa conta."""
import json
import unittest
from pathlib import Path

try:
    import numpy  # noqa: F401
    from analisador_frases import analisador
    LIGADO = analisador().disponivel
except ImportError:
    LIGADO = False

LIMIARES = json.loads((Path(__file__).parent / "avaliacoes" / "memoria_relatos_v1" /
                       "limiares.json").read_text(encoding="utf-8"))


@unittest.skipUnless(LIGADO, "analisador de frases desligado (sem NumPy ou sem pesos)")
class TestesSentido(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sentido_frases import Leitor
        cls.leitor = Leitor()

    def test_evento_com_causa_tempo_e_lugar(self):
        ev = self.leitor.eventos("meu cachorro latiu a noite toda porque viu um gato")[0]
        self.assertEqual((ev.acao, ev.agente), ("latir", "meu cachorro"))
        self.assertEqual(ev.tempo, ["a noite toda"])
        self.assertIn("gato", ev.relacoes["causa"].texto)
        ev = self.leitor.eventos("meu gato dormiu em cima do sofá")[0]
        self.assertEqual(ev.lugar, ["em cima do sofá"])

    def test_negacao_e_condicao(self):
        ev = self.leitor.eventos("meu filho não foi à escola porque estava doente")[0]
        self.assertTrue(ev.negado)
        ev = self.leitor.eventos("se chover amanhã, a gente fica em casa")[0]
        self.assertEqual(ev.relacoes["condicao"].acao, "chover")


@unittest.skipUnless(LIGADO, "analisador de frases desligado (sem NumPy ou sem pesos)")
class TestesMemoria(unittest.TestCase):
    def test_catraca(self):
        from scripts.avaliar_memoria_relatos import avaliar
        for conjunto in ("dev", "retido", "retido2", "informal_dev", "informal_retido"):
            with self.subTest(conjunto=conjunto):
                resumo, falhas = avaliar(conjunto)
                if "retido" in conjunto:
                    falhas = "(retido: detalhes não exibidos)"
                self.assertGreaterEqual(resumo["dialogos_ok"], LIMIARES[conjunto]["dialogos_ok_min"], falhas)

    def test_ele_e_ela_viram_quem_foi_contado_antes(self):
        from sentido_frases import MemoriaRelatos, _genero_numero
        self.assertEqual(_genero_numero("minha vó"), ("f", "s"))
        self.assertEqual(_genero_numero("meus pais"), ("m", "p"))
        self.assertIsNone(_genero_numero("Pedro"))
        m = MemoriaRelatos()
        m.guardar("minha irmã chegou cedo")
        m.guardar("meu primo chegou tarde")
        m.guardar("ela trouxe um bolo")
        self.assertIn("sua irmã", m.responder("quem trouxe o bolo?")[0])
        m.guardar("comprei um celular novo")
        m.guardar("ele já quebrou")
        self.assertIn("celular", m.responder("o que quebrou?")[0])
        # Sem referente compatível, o pronome fica.
        m2 = MemoriaRelatos()
        m2.guardar("ela ligou cedo")
        self.assertIn("ela", m2.responder("quem ligou?")[0])

    def test_responde_como_relato_e_nao_inventa(self):
        from crivo import Crivo
        bot = Crivo()
        bot.responder("meu pai vendeu a moto porque precisava de dinheiro")
        ident, resposta = bot.responder("por que meu pai vendeu a moto?")
        self.assertEqual(ident, "memoria:relato")
        self.assertTrue(resposta.startswith("Você me contou"))
        self.assertIn("dinheiro", resposta)
        self.assertNotEqual(bot.responder("por que o vizinho gritou?")[0], "memoria:relato")
        self.assertIn("95", bot.responder("quantas luas tem Júpiter?")[1])

    def test_sem_motivo_contado_diz_que_nao_sabe(self):
        from crivo import Crivo
        bot = Crivo()
        bot.responder("o ônibus atrasou hoje")
        self.assertIn("não disse por quê", bot.responder("por que o ônibus atrasou?")[1])


if __name__ == "__main__":
    unittest.main()
