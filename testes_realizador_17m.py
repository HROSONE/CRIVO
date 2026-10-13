"""Voz experimental do 17M: desligada por padrão, travada por SHA e conferida antes de falar."""
import os
import unittest
from unittest import mock

import quadro_fala
import realizador_17m
from crivo import Crivo


class Falso:
    """Realizador de teste: devolve a frase que o teste mandar."""
    def __init__(self, texto, terminou=True):
        self.texto, self.terminou, self.chamadas = texto, terminou, []

    def realizar(self, quadro, mensagem):
        self.chamadas.append((quadro, mensagem))
        return self.texto, self.terminou


class Travas(unittest.TestCase):
    def test_desligado_por_padrao(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR", None)
            self.assertFalse(realizador_17m.habilitado())
            bot = Crivo()
            bot.responder("O que é a Lua?")
            self.assertNotIn("realizador", bot.historico[-1])

    def test_duas_travas(self):
        with mock.patch.dict(os.environ, {"CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR": "1"}):
            os.environ.pop("CRIVO_REALIZADOR_DIR", None)
            self.assertFalse(realizador_17m.habilitado())

    def test_pesos_errados_nao_carregam(self):
        with self.assertRaises(Exception):
            realizador_17m.Realizador(realizador_17m.RAIZ)  # sem pesos aprovados aqui

    def test_formato_e_o_do_treino(self):
        self.assertTrue(hasattr(realizador_17m.formato(), "avaliar_saida"))


class Api(unittest.TestCase):
    def test_status_publico(self):
        st = realizador_17m.status()
        self.assertEqual(st["pesos_sha256"], realizador_17m.PESOS_SHA256)
        self.assertFalse(st["decisao"]["promovido"])
        self.assertEqual(st["decisao"]["padrao"], "desligado")
        self.assertFalse(st["external_ai"])

    def test_resposta_da_api_sem_travas_nao_mostra_voz(self):
        from web_core import responder_web
        os.environ.pop("CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR", None)
        self.assertNotIn("experimental_voice", responder_web({"message": "Meu gato se chama Tupo."}))


class Adaptador(unittest.TestCase):
    def quadro(self, *falas):
        bot = Crivo()
        for f in falas:
            ident, resp = bot.responder(f)
        return quadro_fala.quadro_do_turno(bot, falas[-1], ident, resp)

    def test_atos(self):
        self.assertEqual(self.quadro("Meu gato se chama Tupo.")["ato"], "registrar")
        self.assertEqual(self.quadro("Meu gato se chama Tupo.", "Qual é o nome do meu gato?"),
                         {"ato": "recordar", "relacao": "gato", "nome": "Tupo"})
        # A pessoa corrigiu a própria informação: registro novo, sem "desculpa, errei".
        self.assertEqual(self.quadro("Meu gato se chama Tupo.", "Na verdade, meu gato se chama Dano."),
                         {"ato": "registrar", "relacao": "gato", "nome": "Dano"})
        q = self.quadro("O que é a Lua?")
        self.assertEqual(q["ato"], "explicar")
        self.assertTrue(q["fatos"])
        self.assertEqual(self.quadro("Estou triste hoje."), {"ato": "acolher", "sentimento": "triste"})
        self.assertEqual(self.quadro("O que é um zorblax?"), {"ato": "nao_sei", "assunto": "zorblax"})

    def test_sem_quadro_fica_o_texto_de_sempre(self):
        self.assertIsNone(self.quadro("Quanto é 2 mais 2?"))
        # Relação que o realizador não treinou (feminino) e cumprimento com período do dia.
        self.assertIsNone(self.quadro("Tenho uma irmã chamada Lia."))
        self.assertIsNone(self.quadro("Boa noite!"))
        # Resposta com aviso ("Vale lembrar que…") além dos fatos: o aviso não pode sumir.
        self.assertIsNone(self.quadro("O que é um buraco negro?"))
        self.assertIsNone(self.quadro("Escreva um texto sobre a Lua em duas frases."))


class Conferencia(unittest.TestCase):
    def falar(self, frase_falsa, *falas):
        bot = Crivo()
        bot.realizador = Falso(frase_falsa)
        for f in falas:
            ident, texto = bot.responder(f)
        return bot, texto

    def test_frase_aprovada_e_usada(self):
        bot, texto = self.falar("Que legal! Tupo é um nome bonito. Me conta mais sobre seu gato?",
                                "Meu gato se chama Tupo.")
        self.assertEqual(texto, "Que legal! Tupo é um nome bonito. Me conta mais sobre seu gato?")
        self.assertTrue(bot.historico[-1]["realizador"]["usada"])

    def test_nome_trocado_volta_ao_texto_de_sempre(self):
        bot, texto = self.falar("Que legal! Tupe é um nome bonito.", "Meu gato se chama Tupo.")
        self.assertIn("Tupo", texto)
        self.assertNotIn("Tupe", texto)
        self.assertIn("reprovado", bot.historico[-1]["realizador"]["motivo"])

    def test_relacao_trocada_volta_ao_texto_de_sempre(self):
        bot, texto = self.falar("Anotado: seu irmão se chama Tupo. Gostei do nome!", "Meu gato se chama Tupo.")
        self.assertNotIn("irmão", texto)
        self.assertIn("relacao_certa", bot.historico[-1]["realizador"]["motivo"])
        bot, texto = self.falar("Tupo. Que nome diferente. Como é seu nome?", "Meu gato se chama Tupo.")
        self.assertNotIn("seu nome", texto)

    def test_fato_alterado_volta_ao_texto_de_sempre(self):
        bot, texto = self.falar("Claro! A Lua é o satélite artificial da Terra.", "O que é a Lua?")
        self.assertIn("satélite natural", texto)
        self.assertFalse(bot.historico[-1]["realizador"]["usada"])

    def test_sem_fim_volta_ao_texto_de_sempre(self):
        bot = Crivo()
        bot.realizador = Falso("Sinto muito que você esteja se sentindo assim.", terminou=False)
        _, texto = bot.responder("Estou triste hoje.")
        self.assertFalse(bot.historico[-1]["realizador"]["usada"])

    def test_revisao_ainda_confere(self):
        bot, _ = self.falar("Sinto muito por isso. Respira com calma; se quiser desabafar, eu escuto.",
                            "Estou triste hoje.")
        self.assertTrue(bot.historico[-1]["realizador"]["usada"])
        self.assertIsNotNone(bot.estado_interno.revisao)


if __name__ == "__main__":
    unittest.main()
