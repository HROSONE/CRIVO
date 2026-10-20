"""Metacognição: o CRIVO sabe dizer quanto sabe da própria resposta e como sabe."""
import unittest

import metacognicao
from crivo import Crivo
from web_core import responder_web


class NivelDoTurno(unittest.TestCase):
    def _meta(self, *falas):
        bot = Crivo()
        for fala in falas:
            bot.responder(fala)
        return bot.estado_interno.metacognicao

    def test_fato_com_fonte(self):
        meta = self._meta("O que é a Lua?")
        self.assertEqual((meta["nivel"], meta["base"], meta["escolha"]), ("sei", "acervo_com_fonte", "responder"))

    def test_leitura_mede_confianca(self):
        meta = self._meta("Chove em Titã?")
        self.assertEqual(meta["base"], "leitura")
        self.assertGreaterEqual(meta["confianca"], 0.8)

    def test_recusa_admite(self):
        meta = self._meta("O que é um zorblax?")
        self.assertEqual((meta["nivel"], meta["escolha"]), ("nao_sei", "admitir"))
        self.assertIsNone(meta["confianca"])

    def test_calculo_e_relato(self):
        self.assertEqual(self._meta("Quanto é 2 mais 2?")["base"], "calculo")
        self.assertEqual(self._meta("Meu nome é Ana", "Qual é o meu nome?")["base"], "relato")


class Introspeccao(unittest.TestCase):
    def test_tem_certeza_depois_de_fato(self):
        bot = Crivo()
        bot.responder("O que é a Lua?")
        ident, texto = bot.responder("Tem certeza?")
        self.assertEqual(ident, "metacognicao:certeza")
        self.assertTrue(texto.startswith("Tenho, sim."))
        self.assertIn("fonte", texto)
        self.assertEqual(bot.historico[-1]["mecanismo"], "metacognicao")
        # A fonte da resposta anterior continua disponível.
        self.assertEqual(bot.responder("Qual é a fonte?")[0], "escrita:fontes")

    def test_tem_certeza_depois_de_recusa(self):
        bot = Crivo()
        bot.responder("O que é um zorblax?")
        ident, texto = bot.responder("tem certeza?")
        self.assertEqual(ident, "metacognicao:certeza")
        self.assertTrue(texto.startswith("Não — e foi por isso"))

    def test_por_que_mostra_o_motivo_do_quadro(self):
        bot = Crivo()
        bot.responder("Chove em Titã?")
        ident, texto = bot.responder("Por que você respondeu isso?")
        self.assertEqual(ident, "metacognicao:por_que")
        self.assertIn("Titã", texto)
        self.assertIn("No meu quadro ficou registrado", texto)

    def test_introspeccao_nao_substitui_a_resposta_anterior(self):
        bot = Crivo()
        bot.responder("O que é um zorblax?")
        bot.responder("Tem certeza?")
        _, texto = bot.responder("Como você sabe disso?")
        self.assertIn("não tinha evidência", texto)

    def test_sem_resposta_anterior_nao_ha_introspeccao(self):
        self.assertNotEqual(Crivo().responder("Tem certeza?")[0][:13], "metacognicao:")
        self.assertIsNone(metacognicao.introspectar("tem certeza", None))

    def test_api(self):
        dado = responder_web({"message": "Tem certeza?", "history": ["O que é a Lua?"]})
        self.assertEqual(dado["id"], "metacognicao:certeza")
        self.assertEqual(dado["mechanism"], "metacognicao")


if __name__ == "__main__":
    unittest.main()
