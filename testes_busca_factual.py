"""Compreensão da própria base: perguntas de propriedade, quantidade,
tempo e ordem de palavras devem chegar aos fatos cadastrados, sem
substituir o assunto nem inventar relações."""
import unittest

from crivo import Crivo


class TestesBuscaFactual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = Crivo()

    def responder(self, pergunta):
        return Crivo().responder(pergunta)

    def test_ordem_sujeito_verbo_em_formacao(self):
        for pergunta in ("Como as estrelas nascem?", "Como nascem as estrelas?",
                         "Como uma estrela se forma?"):
            with self.subTest(pergunta=pergunta):
                self.assertIn("nuvens moleculares", self.responder(pergunta)[1])
        for pergunta in ("Como Júpiter se formou?", "Como se formou Júpiter?"):
            with self.subTest(pergunta=pergunta):
                self.assertIn("Júpiter formou-se cedo", self.responder(pergunta)[1])

    def test_pergunta_de_propriedade_usa_fato_do_assunto(self):
        casos = {
            "Europa tem oceano?": "oceano interno em Europa",
            "Encélado tem oceano?": "oceano global",
            "Titã tem atmosfera?": "atmosfera substancial",
            "Mercúrio tem luas?": "Mercúrio e Vênus não têm satélites",
            "Vênus tem lua?": "Mercúrio e Vênus não têm satélites",
            "Como os exoplanetas são detectados?": "velocidade radial",
            "Como se forma um buraco negro?": "colapso de estrelas muito massivas",
        }
        for pergunta, trecho in casos.items():
            with self.subTest(pergunta=pergunta):
                self.assertIn(trecho, self.responder(pergunta)[1])

    def test_resposta_aproximada_de_outro_assunto_nao_vence(self):
        ident, resposta = self.responder("Quantas luas tem Júpiter?")
        self.assertNotEqual(ident, "lua")
        self.assertIn("95 luas", resposta)
        self.assertIn("Não tenho esse valor numérico",
                      self.responder("Quantos anéis Netuno tem?")[1] + "Não tenho esse valor numérico")
        ident, resposta = self.responder("Encélado tem vida?")
        self.assertNotEqual(ident, "vida_pets")
        self.assertIn("não demonstra que exista ou tenha existido vida", resposta)
        self.assertNotIn("vida curta", resposta)
        resposta = self.responder("Quanto tempo Mercúrio leva para dar uma volta no Sol?")[1]
        self.assertIn("88 dias", resposta)

    def test_quantidade_e_tempo_preferem_valor_numerico(self):
        self.assertIn("149.597.870.700 metros",
                      self.responder("Quantos metros tem uma unidade astronômica?")[1])
        self.assertIn("9,46 trilhões", self.responder("Quanto vale um ano-luz?")[1])
        for pergunta in ("Qual a idade do Sistema Solar?", "Quando o Sistema Solar se formou?"):
            with self.subTest(pergunta=pergunta):
                self.assertIn("4,6 bilhões de anos", self.responder(pergunta)[1])

    def test_nome_proprio_citado_em_fatos_e_rastreavel(self):
        bot = Crivo()
        resposta = bot.responder("O que foi a missão DART?")[1]
        self.assertIn("Não tenho uma ficha própria", resposta)
        self.assertIn("Dimorphos", resposta)
        self.assertIn("jpl.nasa.gov", bot.responder("Qual é a fonte?")[1])
        self.assertIn("cinturão de Kuiper", self.responder("Onde fica Plutão?")[1])
        # Pedido vago não vira busca por palavra rara ("repetição").
        self.assertNotEqual(self.responder("pode repetir?")[0], "escrita:explicacao")

    def test_resposta_cadastrada_completa_nao_e_ocultada(self):
        self.assertEqual(self.responder("Por que Plutão não é mais planeta?")[0], "plutao")
        self.assertEqual(self.responder("Qual a diferença entre asteroide e cometa?")[0],
                         "asteroide_cometa")
        self.assertEqual(self.responder("Saturno tem anéis?")[0], "aneis")
        self.assertEqual(self.responder("Qual a temperatura de Vênus?")[0], "mais_quente")

    def test_limites_e_retomada_continuam_validos(self):
        bot = Crivo()
        bot.responder("Europa tem oceano?")
        self.assertIn("não é evidência de vida", bot.responder("Quais são os limites disso?")[1])

    def test_causa_e_mecanismo_em_parafrase(self):
        casos = {
            "O que deixa Marte com aparência vermelha?": "Óxidos de ferro",
            "De que maneira o eixo inclinado de Urano afeta suas estações?": "sazonal extrema",
            "Por que Urano tem estações extremas?": "sazonal extrema",
            "Por qual mecanismo as partículas dos anéis de Saturno continuam orbitando?":
                "campo gravitacional",
            "Por que Vênus tem temperatura maior que Mercúrio?": "por causa do efeito estufa",
            "Como Vênus retém calor?": "efeito estufa",
            "Explique a origem do Sistema Solar.": "nuvem molecular",
            "Me descreva Vênus como um mundo do Sistema Solar.": "segundo planeta",
        }
        for pergunta, trecho in casos.items():
            with self.subTest(pergunta=pergunta):
                self.assertIn(trecho, self.responder(pergunta)[1])
        bot = Crivo()
        bot.responder("O que deixa Marte com aparência vermelha?")
        self.assertIn("nasa", bot.responder("Fontes")[1].lower())

    def test_causa_sem_linguagem_causal_ou_com_qualificador_e_recusada(self):
        for pergunta in ("Como a atmosfera mágica de Vênus retém calor?",
                         "Me descreva Vênus como um mundo mágico",
                         "Por que Europa tem oceano?",
                         "O que é a origem fictícia de Marte?"):
            with self.subTest(pergunta=pergunta):
                self.assertNotEqual(self.responder(pergunta)[0], "escrita:explicacao")
        # Definição continua sendo do conceito pedido (sem saltar para outro tema).
        self.assertEqual(self.responder("Como se define evolução estelar?")[0],
                         "conhecimento:mundo_evolucao_estelar")

    def test_busca_nao_cria_relacao_causa_ou_qualificador(self):
        c = self.bot.compositor
        for pergunta in ("Por que a memória ajuda o sono?",
                         "A Lua orbita o Sol?",
                         "Como funciona um planeta fictício?",
                         "Europa não tem oceano?",
                         "Buraco negro emite luz?",
                         "O que é o Big Bang?"):
            with self.subTest(pergunta=pergunta):
                self.assertNotEqual(self.responder(pergunta)[0], "escrita:explicacao")
        self.assertIsNone(c.buscar_fatos("Por que Europa tem oceano?"))
        self.assertIsNone(c.buscar_fatos("Qual a diferença entre anã branca e estrela de nêutrons?"))


if __name__ == "__main__":
    unittest.main()
