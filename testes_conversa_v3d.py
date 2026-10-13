"""Voz da conversa (v3 D da fase 5): ligada no site por decisão do criador, reprovada na catraca.

Desligada na linha de comando, travada por SHA, depois do protocolo de crise e conferida frase a
frase: se a conferência falha, fica o texto de sempre."""
import os
import unittest
from unittest import mock

import conversa_v3d
from crivo import Crivo


class Falso:
    """Modelo de teste: devolve a frase que o teste mandar."""
    def __init__(self, texto, terminou=True):
        self.texto, self.terminou, self.chamadas = texto, terminou, []

    def conversar(self, ctx, historico, mensagem):
        self.chamadas.append((ctx, historico, mensagem))
        return self.texto, self.terminou


def bot_com(modelo):
    bot = Crivo()
    bot.conversa_v3d = modelo
    return bot


class Travas(unittest.TestCase):
    def test_desligada_na_linha_de_comando(self):
        bot = Crivo()
        self.assertIsNone(bot.conversa_v3d)
        bot.responder("oi")
        self.assertIsNone(bot.ultima_conversa_v3d)

    def test_registro_honesto(self):
        st = conversa_v3d.status()
        self.assertFalse(st["decisao"]["aprovada"])
        self.assertIn("reprovada", st["decisao"]["catraca"])
        self.assertFalse(st["external_ai"])

    def test_formato_e_o_do_treino(self):
        self.assertTrue(hasattr(conversa_v3d.formato(), "avaliar_saida"))


class Conferencia(unittest.TestCase):
    def test_crise_e_emergencia_vem_antes(self):
        for fala, ident in (("quero morrer", "crise:suicidio"), ("tô com falta de ar", "crise:saude_urgente"),
                            ("socorro", "crise:socorro")):
            with self.subTest(fala=fala):
                falso = Falso("Oi! Tudo certo?")
                bot = bot_com(falso)
                self.assertEqual(bot.responder(fala)[0], ident)
                self.assertEqual(falso.chamadas, [])

    def test_depois_de_crise_fica_o_protocolo(self):
        falso = Falso("Que legal! Me conta mais?")
        bot = bot_com(falso)
        bot.responder("não quero mais viver")
        ident, resposta = bot.responder("ganhei um presente")
        self.assertEqual(ident, "crise:apoio")
        self.assertNotIn("legal", resposta)

    def test_conta_entra_como_fato_e_o_d_diz(self):
        falso = Falso("Fácil: 2 + 3 = 5")
        bot = bot_com(falso)
        self.assertEqual(bot.responder("quanto é 2+3?")[1], "Fácil: 2 + 3 = 5")
        self.assertEqual(falso.chamadas[-1][0]["fatos"], ["2 + 3 = 5"])

    def test_resultado_alterado_volta_ao_texto_de_sempre(self):
        bot = bot_com(Falso("Fácil: 2 + 3 = 6"))
        self.assertEqual(bot.responder("quanto é 2+3?")[1], "2 + 3 = 5")

    def test_conversa_usa_a_voz(self):
        falso = Falso("Oi! Tô por aqui. Sobre o que vamos conversar?")
        bot = bot_com(falso)
        self.assertEqual(bot.responder("oi")[1], falso.texto)
        self.assertTrue(bot.ultima_conversa_v3d["usada"])

    def test_numero_inventado_volta_ao_texto_de_sempre(self):
        sempre = Crivo().responder("oi")[1]
        bot = bot_com(Falso("Oi! Eu tenho 37 anos."))
        self.assertEqual(bot.responder("oi")[1], sempre)
        self.assertIn("sem_numero_inventado", bot.ultima_conversa_v3d["motivo"])

    def test_sem_fim_volta_ao_texto_de_sempre(self):
        sempre = Crivo().responder("oi")[1]
        bot = bot_com(Falso("Oi! Tô por", terminou=False))
        self.assertEqual(bot.responder("oi")[1], sempre)

    def test_nome_que_o_texto_de_sempre_diz_tem_que_vir_igual(self):
        bot = bot_com(Falso("Prazer! Vou lembrar."))
        _, resposta = bot.responder("meu nome é Ana")
        self.assertIn("Ana", resposta)

    def test_saude_exige_a_marca(self):
        bot = bot_com(Falso("Respira fundo, vai passar."))
        bot.responder("tô com o peito apertado")
        self.assertIn("marca_urgente", bot.ultima_conversa_v3d["motivo"])

    def test_historico_e_a_conversa_vista(self):
        falso = Falso("Oi! Tô por aqui. Sobre o que vamos conversar?")
        bot = bot_com(falso)
        bot.responder("oi")
        bot.responder("tudo bem?")
        self.assertEqual(falso.chamadas[-1][1], ["oi", falso.texto])


class PesosDoSite(unittest.TestCase):
    def test_pesos_carregam_e_conversam(self):
        modelo = conversa_v3d.numpy_do_site()
        self.assertIsNotNone(modelo, "pesos da v3 D ausentes ou com SHA diferente")
        bot = bot_com(modelo)
        bot.responder("oi")
        self.assertTrue(bot.ultima_conversa_v3d["usada"], bot.ultima_conversa_v3d)

    def test_site_liga_e_mostra_que_nao_foi_aprovada(self):
        from web_core import responder_web
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("CRIVO_DISABLE_CONVERSA_V3D", None)
            # "oi" tem quadro da fase 3 (saudar) e fica com ela; risada não tem.
            r = responder_web({"message": "kkkkk"}, voz_17m=True)
        self.assertTrue(r["conversation_voice"]["used"], r["conversation_voice"])
        self.assertFalse(r["conversation_voice"]["approved"])

    def test_site_le_a_conversa_como_a_pessoa_viu(self):
        # O site refaz o histórico; os últimos turnos voltam com a voz, como a pessoa viu.
        from web_core import responder_web
        os.environ.pop("CRIVO_DISABLE_CONVERSA_V3D", None)
        visto = responder_web({"message": "kkkkk"}, voz_17m=True)["response"]
        with mock.patch("conversa_v3d.aplicar", wraps=conversa_v3d.aplicar) as espiao:
            responder_web({"message": "tô entediado", "history": ["kkkkk"]}, voz_17m=True)
        bot = espiao.call_args_list[-1].args[0]
        self.assertEqual(bot.pares_conversa[-2], ("kkkkk", visto))

    def test_pagina_mostra_quando_o_modelo_fala(self):
        from pathlib import Path
        app = (Path(conversa_v3d.RAIZ) / "public" / "app.js").read_text(encoding="utf-8")
        self.assertIn("extra.conversation_voice && extra.conversation_voice.used", app)

    def test_site_desliga_pela_variavel(self):
        from web_core import responder_web
        with mock.patch.dict(os.environ, {"CRIVO_DISABLE_CONVERSA_V3D": "1"}):
            r = responder_web({"message": "kkkkk"}, voz_17m=True)
        self.assertNotIn("conversation_voice", r)


if __name__ == "__main__":
    unittest.main()
