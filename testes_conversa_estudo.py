"""Rodada de conversa de 02/10/2026: falas reais que falhavam."""
import unittest

from crivo import Crivo


def conversa(*falas):
    bot = Crivo()
    return bot, [bot.responder(f) for f in falas]


class TestesContexto(unittest.TestCase):
    def test_pronome_retoma_o_assunto(self):
        _, r = conversa("o que é a zona habitável?", "a Terra está nela?")
        self.assertIn("zona habitável", r[1][1])
        _, r = conversa("e Júpiter, é feito de quê?", "tem como pousar lá?")
        self.assertIn("superfície sólida", r[1][1])

    def test_elipse_herda_a_pergunta_anterior(self):
        _, r = conversa("quanto tempo dura um dia em Vênus?", "e em Marte?")
        self.assertIn("243 dias", r[0][1])
        self.assertIn("24,6 horas", r[1][1])

    def test_resposta_antiga_so_vale_se_o_assunto_for_o_tema(self):
        ident, resposta = Crivo().responder("quantos anos tem o sol?")
        self.assertIn("4,6 bilhões", resposta)

    def test_linguagem_de_programacao_lembrada(self):
        _, r = conversa("como usar if em python?", "como faço um loop?", "e uma função?")
        self.assertEqual(r[1][0], "py_while")
        self.assertEqual(r[2][0], "py_funcao")

    def test_relato_que_e_tema_da_base_vai_para_a_base(self):
        self.assertEqual(Crivo().responder("minha planta tá com folhas amarelas")[0], "folha_amarela")
        self.assertNotEqual(Crivo().responder("estou cansado hoje")[0], "previsao_hoje")


class TestesFatosNovos(unittest.TestCase):
    def test_sol_lua_mares(self):
        casos = {
            "o sol vai explodir?": "anã branca",
            "o que causa as marés?": "gravidade da Lua",
            "a Lua causa as marés?": "gravidade da Lua",
            "por que a gente só vê um lado da Lua?": "travamento de maré",
            "e Júpiter, é feito de quê?": "hidrogênio",
        }
        for pergunta, trecho in casos.items():
            with self.subTest(pergunta=pergunta):
                self.assertIn(trecho, Crivo().responder(pergunta)[1])

    def test_relacao_sem_linguagem_causal_continua_recusada(self):
        quadro = Crivo().compositor.interpretar("Por que a memória ajuda o sono?")
        self.assertEqual(quadro.recusa, "relacao_entre_conceitos")


class TestesEstudo(unittest.TestCase):
    def test_ensino_simples(self):
        ident, resposta = Crivo().responder("me explica o big bang como se eu tivesse 10 anos")
        self.assertEqual(ident, "escrita:simples")
        self.assertIn("Big Bang", resposta)
        ident, resposta = Crivo().responder("quero aprender sobre buracos negros")
        self.assertIn("buraco negro", resposta.lower())
        self.assertIn("treinar com perguntas", resposta)

    def test_quiz_mantem_o_tema_e_corrige(self):
        bot, r = conversa("me testa sobre Marte")
        self.assertEqual(r[0][0], "estudo:pergunta")
        certa = bot.conversacao.quiz["resposta"]
        self.assertTrue(bot.responder(certa)[1].startswith("Acertou!"))
        self.assertIn("acertou", bot.responder("acertei?")[1])
        ident, pergunta = bot.responder("outra")
        self.assertEqual(ident, "estudo:pergunta")
        self.assertEqual(bot.conversacao.quiz["assunto"], "mundo_marte")
        self.assertTrue(bot.responder("não sei")[1].startswith("Sem problema"))

    def test_tema_de_estudo(self):
        bot, r = conversa("o tema é sistema solar", "me faz umas perguntas para eu treinar")
        self.assertEqual(r[0][0], "social:tema")
        self.assertEqual(r[1][0], "estudo:pergunta")

    def test_sobre_mim_e_fonte(self):
        _, r = conversa("você aprende comigo?", "qual a temperatura do Sol?", "qual a fonte disso?")
        self.assertEqual(r[0][0], "social:sobre_mim")
        self.assertIn("NASA", r[2][1])


if __name__ == "__main__":
    unittest.main()
