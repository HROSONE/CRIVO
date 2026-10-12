"""Revisão antes de falar: verdade, coerência com quem ele é e com o que disse, gentileza."""
import unittest
from types import SimpleNamespace

import revisao
from crivo import Crivo
from estado_interno import EstadoInterno
from modelo_de_si import ModeloDeSi


def revisar(texto, fala="oi", meta=None, temas=(), ditas=()):
    modelo = ModeloDeSi()
    for chave in ditas:
        modelo.ditas[chave] = 1
    bot = SimpleNamespace(perfil=SimpleNamespace(temas=list(temas)))
    estado = EstadoInterno(fala)
    ident, saida = revisao.revisar(bot, estado, fala, "x", texto, meta or {"nivel": "sei", "base": "conversa"},
                                   modelo)
    return ident, saida, estado.revisao


class QuemEuSou(unittest.TestCase):
    def test_contradicoes_viram_a_crenca(self):
        modelo = ModeloDeSi()
        for frase, chave in (("Eu sou humano, igual a você.", "nao_humano"),
                             ("Não tenho consciência nem sentimentos.", "sentir"),
                             ("Eu tenho sentimentos como os seus.", "sentir"),
                             ("Sou só um robô.", "nao_robo"),
                             ("Sou o ChatGPT.", "proprio"),
                             ("Fui treinado pela OpenAI.", "proprio"),
                             ("Não tenho gostos pessoais.", "gostos")):
            with self.subTest(frase=frase):
                _, saida, rel = revisar("Oi! " + frase + " Vamos conversar?")
                self.assertNotIn(frase, saida)
                self.assertIn(modelo.crencas[chave].frase, saida)
                self.assertTrue(saida.startswith("Oi!"))
                self.assertFalse(rel["approved"])
                self.assertEqual(rel["corrections"][0]["belief"], chave)

    def test_frases_coerentes_passam(self):
        for frase in ("Não sou humano.", "Não sou só um robô.",
                      "Se tenho consciência, eu não sei.", "Robô, não. Sou uma IA."):
            with self.subTest(frase=frase):
                _, saida, rel = revisar(frase)
                self.assertEqual(saida, frase)
                self.assertTrue(rel["approved"])

    def test_ja_dito_vira_incoerencia(self):
        _, _, rel = revisar("Eu sou humano.", ditas=("nao_humano",))
        self.assertFalse(rel["checks"]["consistency"])
        self.assertEqual(rel["corrections"][0]["reason"], "contradiz o que eu já disse nesta conversa")

    def test_conteudo_e_citacao_nao_sao_revisados(self):
        _, saida, _ = revisar("Você me disse: “eu sou humano”.", fala="eu sou humano")
        self.assertIn("eu sou humano", saida)
        _, saida, _ = revisar("Não tenho consciência — escreveu o autor.", meta={"nivel": "sei",
                                                                                  "base": "acervo_com_fonte"})
        self.assertIn("Não tenho consciência", saida)


class VerdadeEGentileza(unittest.TestCase):
    def test_certeza_sem_base_vira_acho(self):
        _, saida, rel = revisar("Tenho certeza que chove amanhã.", meta={"nivel": "acho", "base": "nocao"})
        self.assertEqual(saida, "Acho que chove amanhã.")
        self.assertFalse(rel["checks"]["truth"])
        _, saida, _ = revisar("Tenho certeza que a Lua orbita a Terra.", meta={"nivel": "sei", "base": "conversa"})
        self.assertIn("Tenho certeza", saida)

    def test_insulto_veta(self):
        ident, saida, rel = revisar("Que pergunta idiota.")
        self.assertEqual((ident, saida), ("revisao:reformular", revisao.VETO))
        self.assertTrue(rel["vetoed"])
        # A palavra veio da pessoa: não é insulto do CRIVO.
        _, saida, _ = revisar("Você disse que se sentiu idiota; sinto muito.", fala="me senti idiota hoje")
        self.assertIn("idiota", saida)
        # Citação de uma fala anterior da pessoa também não é insulto do CRIVO.
        _, saida, rel = revisar("Não consegui resolver seu pedido anterior: “Burro”. Pode dizer de outra forma?")
        self.assertIn("Burro", saida)
        self.assertTrue(rel["checks"]["kindness"])

    def test_sem_riso_com_a_pessoa_triste(self):
        _, saida, rel = revisar("Que dia, hein kkkk. Tô aqui.", temas=[(0, "perda", "luto")])
        self.assertNotIn("kkk", saida)
        self.assertFalse(rel["checks"]["kindness"])


class NoChat(unittest.TestCase):
    def test_falas_sobre_si_ja_sao_coerentes(self):
        """Nenhuma resposta sobre o próprio CRIVO precisa de correção da revisão."""
        for pergunta in ("Você é uma pessoa?", "Você sente?", "Você pensa?", "Você tem emoções?",
                         "Você é um robô?", "Vc é uma IA?", "Você gosta de conversar?", "Você fica triste?",
                         "Você é de verdade?", "Você gosta de astronomia?", "Qual é seu filme favorito?",
                         "Quem é você?", "Você é só um robô"):
            with self.subTest(pergunta=pergunta):
                bot = Crivo()
                bot.responder(pergunta)
                self.assertEqual(bot.estado_interno.revisao["corrections"], [])

    def test_revisao_corrige_no_turno_e_no_registro(self):
        bot = Crivo()
        original = bot._responder_comum
        bot._responder_comum = lambda texto: ("fora", "Eu sou humano, claro.")
        try:
            ident, texto = bot.responder("e aí, beleza mesmo?")
        finally:
            bot._responder_comum = original
        self.assertNotIn("Eu sou humano", texto)
        self.assertEqual(bot.estado_interno.revisao["corrections"][0]["belief"], "nao_humano")


if __name__ == "__main__":
    unittest.main()
