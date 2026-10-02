"""Bate-papo curto: estado, reações, confirmações, continuação,
repetição, curiosidades e preferências, sempre com o turno anterior."""
import unittest

from crivo import Crivo


def conversa(*falas):
    bot = Crivo()
    return bot, [bot.responder(f) for f in falas]


class TestesConversaCotidiana(unittest.TestCase):
    def test_responde_ao_como_voce_esta(self):
        _, r = conversa("oi tudo bem?", "estou bem, obrigado por perguntar")
        self.assertEqual(r[1][0], "social:acolhimento")
        self.assertIn("Sobre o que você quer conversar", r[1][1])
        _, r = conversa("tudo ótimo e você?")
        self.assertIn("Por aqui está tudo certo", r[0][1])

    def test_reacoes_curtas_nao_viram_fato_nem_coaching(self):
        bot, _ = conversa("oi")
        for fala in ("legal", "que bom", "haha", "kkkk", "tá bom", "entendi", "ok", "uau, que legal"):
            with self.subTest(fala=fala):
                ident, resposta = bot.responder(fala)
                self.assertTrue(ident.startswith("social:"), (fala, ident))
                self.assertNotIn("ovo", resposta)
                self.assertNotIn("próximo passo", resposta)

    def test_reacao_oferece_continuar_e_sim_continua(self):
        bot, r = conversa("O que é Titã?", "legal", "sim")
        self.assertIn("Quer saber mais sobre Titã", r[1][1])
        self.assertEqual(r[2][0], "escrita:continuacao")
        self.assertIn("Titã", r[2][1])
        self.assertIn("nasa.gov", bot.responder("qual é a fonte?")[1])

    def test_me_fala_mais_continua_assunto_de_resposta_antiga(self):
        _, r = conversa("e sobre Marte?", "interessante, me fala mais")
        self.assertEqual(r[1][0], "escrita:continuacao")
        self.assertIn("Marte", r[1][1])

    def test_me_fala_sobre_compoe_o_assunto(self):
        _, r = conversa("me fala sobre o sistema solar")
        self.assertIn("Sistema Solar reúne o Sol", r[0][1])

    def test_repetir_e_nome_do_usuario(self):
        bot, r = conversa("O que é um ano-luz?", "pode repetir?")
        self.assertEqual(r[1][1], r[0][1])
        bot.responder("meu nome é Henrique")
        self.assertIn("Henrique", bot.responder("qual é o meu nome?")[1])
        self.assertIn("ainda não me disse", Crivo().responder("qual é o meu nome?")[1])

    def test_curiosidade_e_piada_usam_fatos_com_fonte(self):
        bot, r = conversa("me conta uma piada", "sim")
        self.assertIn("não sei contar piadas", r[0][1])
        self.assertEqual(r[1][0], "escrita:curiosidade")
        self.assertEqual(bot.responder("qual é a fonte?")[0], "escrita:fontes")
        outra = bot.responder("outra curiosidade")[1]
        self.assertNotEqual(outra, r[1][1])

    def test_preferencia_so_para_assunto_conhecido(self):
        _, r = conversa("você gosta de astronomia?")
        self.assertEqual(r[0][0], "social:preferencia")
        self.assertIn("Não tenho gostos pessoais", r[0][1])
        self.assertEqual(Crivo().responder("Você gosta de lâmpadas?")[0], "social:nao_entendido")

    def test_relato_neutro_nao_recebe_plano_de_acao(self):
        _, r = conversa("oi", "eu moro no Brasil", "talvez")
        self.assertNotIn("próximo passo", r[1][1])
        self.assertNotIn("já tentou", r[1][1])
        self.assertEqual(r[2][0], "social:incerteza")



if __name__ == "__main__":
    unittest.main()
