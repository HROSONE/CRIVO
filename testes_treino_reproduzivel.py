"""Testes de treinamento integral e carregamento seguro (sem dados externos)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crivo import Crivo, SINONIMOS
from rede_neural import RedeCrivo, assinatura_base, assinatura_regras, treinar_base


class TreinoReproduzivelTeste(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.base_path = Path(self.pasta.name) / "conhecimento.json"
        self.pesos_path = Path(self.pasta.name) / "rede_crivo.json"
        self.entradas = [
            {"id": "regar", "topico": "plantas",
             "perguntas": ["como regar um vaso", "molhar minhas plantas"],
             "resposta": "Regue com moderacao."},
            {"id": "chover", "topico": "clima",
             "perguntas": ["por que chove", "como se forma chuva"],
             "resposta": "A agua se condensa."}
        ]
        self.base_path.write_text(
            json.dumps(self.entradas, ensure_ascii=False), encoding="utf-8")

    def test_treino_configuravel_salvo_e_carregado(self):
        rede = treinar_base(self.base_path, self.pesos_path, epocas=3,
                            ocultos=6, dimensao=48, modo="portugues", semente=7)
        self.assertEqual((rede.dimensao, rede.ocultos, rede.modo),
                         (48, 6, "portugues"))
        self.assertEqual(rede.assinatura_base, assinatura_base(self.entradas))
        self.assertEqual(rede.assinatura_regras, assinatura_regras("portugues"))
        restaurada = RedeCrivo.carregar(self.pesos_path)
        for pergunta in ("regar um vaso", "por que chove"):
            self.assertEqual(rede.prever(pergunta), restaurada.prever(pergunta))
        bot = Crivo(self.base_path)
        self.assertIsNotNone(bot.rede)
        self.assertIsNone(bot.erro_rede)
        self.assertEqual(bot.previsao_neural("regar um vaso"),
                         restaurada.prever("regar um vaso"))

    def test_base_alterada_invalida_pesos_sem_quebrar_conversa(self):
        treinar_base(self.base_path, self.pesos_path, epocas=2,
                     ocultos=6, dimensao=48, modo="portugues")
        self.entradas[0]["perguntas"].append("nova formulacao")
        self.base_path.write_text(
            json.dumps(self.entradas, ensure_ascii=False), encoding="utf-8")
        bot = Crivo(self.base_path)
        self.assertIsNone(bot.rede)
        self.assertIn("treine a rede", bot.erro_rede)
        self.assertEqual(bot.responder("nova formulacao")[0], "regar")
        with self.assertRaisesRegex(ValueError, "Perguntas da base"):
            bot.carregar_rede(self.pesos_path)

    def test_regras_alteradas_invalidam_apenas_rede_treinada(self):
        treinar_base(self.base_path, self.pesos_path, epocas=2,
                     ocultos=6, dimensao=48, modo="portugues")
        with patch.dict(SINONIMOS, {"molhar": "alterado"}):
            bot = Crivo(self.base_path)
            self.assertIsNone(bot.rede)
            self.assertIn("Regras linguisticas", bot.erro_rede)

    def test_modelo_legacy_continua_carregando(self):
        RedeCrivo(["regar", "chover"], dimensao=24, ocultos=4).salvar(
            self.pesos_path)
        bot = Crivo(self.base_path)
        self.assertIsNotNone(bot.rede)

    def test_parametros_invalidos_nao_criam_arquivo(self):
        for kwargs in ({"epocas": 0}, {"ocultos": 0}, {"dimensao": 0},
                       {"taxa": 0}, {"taxa": 2}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    treinar_base(self.base_path, self.pesos_path, **kwargs)
                self.assertFalse(self.pesos_path.exists())


if __name__ == "__main__":
    unittest.main()
