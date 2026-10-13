"""Memória de nomes: o CRIVO lembra o nome que a pessoa deu, com a grafia dela."""
import unittest
from types import SimpleNamespace

import memoria_nomes as mn
from crivo import Crivo
from web_core import responder_web


class Observar(unittest.TestCase):
    def test_formas_de_dar_nome(self):
        for frase, rel, nome in (("Meu gato se chama Tupo.", "gato", "Tupo"),
                                 ("Tenho uma irmã chamada Lia", "irmã", "Lia"),
                                 ("O nome do meu cachorro é Thor!", "cachorro", "Thor"),
                                 ("Quero te apresentar meu cavalo: Tupo.", "cavalo", "Tupo"),
                                 ("Meu melhor amigo se chama João Pedro", "melhor amigo", "João Pedro")):
            with self.subTest(frase=frase):
                p = SimpleNamespace(nomes={})
                ev = mn.observar(p, frase)
                self.assertEqual((ev["tipo"], ev["rel"], ev["nome"]), ("registro", rel, nome))
                self.assertEqual(p.nomes[rel], nome)

    def test_nao_grava_negacao_condicao_citacao_ficcao(self):
        for frase in ("Meu gato não se chama Tupo", "Se meu gato se chama Tupo, então…",
                      'Meu amigo disse "meu gato se chama Tupo"', "meu gato se chama tupo", "Meu projeto se chama Flume"):
            with self.subTest(frase=frase):
                p = SimpleNamespace(nomes={})
                self.assertIsNone(mn.observar(p, frase))
                self.assertEqual(p.nomes, {})
        self.assertIsNone(mn.observar(SimpleNamespace(nomes={}), "Meu gato se chama Tupo", ficcao=True))

    def test_correcao(self):
        p = SimpleNamespace(nomes={"gato": "Tupo"})
        ev = mn.observar(p, "Na verdade, meu gato se chama Dano.")
        self.assertEqual((ev["tipo"], ev["antigo"], p.nomes["gato"]), ("correcao", "Tupo", "Dano"))
        ev = mn.observar(p, "Você errou, o nome do meu gato é Rufo.")
        self.assertEqual((ev["tipo"], p.nomes["gato"]), ("correcao", "Rufo"))


class NoChat(unittest.TestCase):
    def test_lembra_e_corrige(self):
        bot = Crivo()
        bot.responder("Meu gato se chama Tupo.")
        ident, texto = bot.responder("Qual é o nome do meu gato?")
        self.assertEqual(ident, "memoria:nome")
        self.assertIn("Tupo", texto)
        self.assertEqual(bot.historico[-1]["mecanismo"], "memoria_nomes")
        bot.responder("Na verdade, meu gato se chama Dano.")
        _, texto = bot.responder("Como se chama meu gato?")
        self.assertIn("Dano", texto)
        self.assertNotIn("Tupo", texto)

    def test_avo_e_avo_nao_se_confundem(self):
        bot = Crivo()
        bot.responder("Minha avó se chama Dona Cida.")
        self.assertIn("Dona Cida", bot.responder("Qual é o nome da minha avó?")[1])
        self.assertIn("ainda não me contou o nome do seu avô", bot.responder("Qual é o nome do meu avô?")[1])

    def test_nome_que_nao_foi_dito(self):
        ident, texto = Crivo().responder("Qual o nome da minha tia?")
        self.assertEqual(ident, "memoria:nome_desconhecido")
        self.assertIn("ainda não me contou", texto)

    def test_api_reconstroi_pelo_historico(self):
        dado = responder_web({"message": "Lembra do nome do meu cachorro?",
                              "history": ["Oi", "O nome do meu cachorro é Thor"]})
        self.assertEqual(dado["id"], "memoria:nome")
        self.assertIn("Thor", dado["response"])


if __name__ == "__main__":
    unittest.main()
