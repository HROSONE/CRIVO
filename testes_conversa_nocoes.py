"""Noções do dia a dia: três níveis de saber (sei / tenho noção / não sei).

A catraca usa a bateria avaliacoes/conversa_cotidiana_v1; o conjunto retido
é avaliado só pelos números agregados.
"""
import json
import random
import unittest
from pathlib import Path

from crivo import Crivo
from nocoes import NocoesPT
from scripts.avaliar_conversa_cotidiana import avaliar

LIMIARES = json.loads((Path(__file__).parent / "avaliacoes" / "conversa_cotidiana_v1" /
                       "limiares.json").read_text(encoding="utf-8"))


class TestesCatraca(unittest.TestCase):
    def conferir(self, conjunto):
        resumo, _, _ = avaliar(conjunto)
        limite = LIMIARES[conjunto]
        self.assertGreaterEqual(resumo["acertos"], limite["acertos_min"], resumo)
        self.assertLessEqual(resumo["fatos_errados"], limite["fatos_errados_max"], resumo)
        self.assertGreaterEqual(resumo["dialogos_ok"], limite["dialogos_ok_min"], resumo)

    def test_dev(self):
        self.conferir("dev")

    def test_retido(self):
        self.conferir("retido")


class TestesNocoes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = NocoesPT()

    def test_formas_longas_e_ordem(self):
        nomes = [n["nome"] for n in self.base.encontrar("acordei com dor de cabeça e com fome")]
        self.assertEqual(nomes, ["dor de cabeça", "fome"])

    def test_afirmacao_nao_e_pergunta_nem_pedido(self):
        self.assertTrue(self.base.afirmacao("hoje choveu o dia todo"))
        for texto in ("por que chove?", "me explica a chuva", "quero aprender sobre chuva",
                      "valeu por ouvir", "crie uma história sobre chuva"):
            with self.subTest(texto=texto):
                self.assertFalse(self.base.afirmacao(texto))

    def test_reacao_tem_tom_nocao_e_pergunta(self):
        _, resposta = self.base.observar("o celular quebrou", random.Random(0))
        self.assertTrue(resposta.startswith(("Poxa.", "Que chato.", "Puxa vida.")))
        self.assertIn("costuma", resposta)
        self.assertTrue(resposta.endswith("?"))

    def test_saude_e_dose_nao_viram_nocao(self):
        self.assertIsNone(self.base.definir("qual a dose de remédio para dor de cabeça?"))
        self.assertIsNone(self.base.nao_sei("como funciona o remédio para gripe?"))

    def test_noções_nao_tem_fonte(self):
        dados = json.loads(Path("dados/nocoes_pt.json").read_text(encoding="utf-8"))
        self.assertEqual(dados["natureza"], "nocao")
        for nocao in dados["nocoes"]:
            self.assertNotIn("fonte", nocao)
            self.assertIn("costuma", nocao["costuma"])


class TestesConversa(unittest.TestCase):
    def test_observacao_nao_vira_palestra(self):
        ident, resposta = Crivo().responder("hoje choveu o dia todo")
        self.assertEqual(ident, "nocao:observacao")
        self.assertNotIn("evapora", resposta)
        # A pergunta continua indo para o conhecimento.
        self.assertIn("evapora", Crivo().responder("por que chove?")[1])

    def test_tres_niveis(self):
        self.assertIn("5.500", Crivo().responder("qual a temperatura do Sol?")[1])
        ident, resposta = Crivo().responder("o que é saudade?")
        self.assertEqual(ident, "nocao:definicao")
        self.assertIn("noção, sem fonte", resposta)
        ident, resposta = Crivo().responder("como funciona a geladeira por dentro?")
        self.assertEqual(ident, "nocao:nao_sei")
        self.assertIn("Não sei explicar", resposta)

    def test_conversa_continua_e_lembra(self):
        bot = Crivo()
        self.assertEqual(bot.responder("o trabalho hoje foi pesado")[0], "nocao:observacao")
        self.assertEqual(bot.responder("pois é")[0], "nocao:reacao")
        self.assertEqual(bot.responder("e ainda tenho que entregar um relatório amanhã")[0],
                         "nocao:continuacao")
        self.assertIn("trabalho hoje foi pesado", bot.responder("sobre o que eu falei?")[1])
        self.assertEqual(bot.responder("valeu por ouvir")[0], "social:obrigado")

    def test_pronome_retoma_a_nocao(self):
        bot = Crivo()
        bot.responder("comprei uma bicicleta")
        ident, resposta = bot.responder("como funciona a marcha dela?")
        self.assertEqual(ident, "nocao:nao_sei")
        self.assertIn("bicicleta", resposta)

    def test_relato_em_primeira_pessoa_fica_com_o_dialogo(self):
        self.assertEqual(Crivo().responder("Tô cansado hoje")[0], "conversa:relato")

    def test_pergunta_com_ficha_nao_vira_nocao(self):
        for pergunta in ("Por que o sono favorece a memória?", "Por que a energia solar sustenta a fotossíntese?",
                         "Por que sono cura depressão?"):
            with self.subTest(pergunta=pergunta):
                self.assertFalse(Crivo().responder(pergunta)[0].startswith("nocao:"))

    def test_base_com_orientacao_continua_valendo(self):
        self.assertEqual(Crivo().responder("minha planta tá com folhas amarelas")[0], "folha_amarela")

    def test_conversa_guiada_nao_e_interrompida(self):
        bot = Crivo()
        bot.responder("Quero conversar sobre meu desenho")
        ident, _ = bot.responder("Eu fiquei contente com o retrato em tinta azul")
        self.assertFalse(ident.startswith("nocao:"))


if __name__ == "__main__":
    unittest.main()
