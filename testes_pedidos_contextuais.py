"""Casos de desenvolvimento: escopo do pedido e fonte da resposta real.

Não constituem prova retida nem dados de treinamento dos modelos novos.
"""
import unittest
from unittest.mock import patch

from crivo import Crivo
from conversa_assistente import limpar_cortesia, preparar_pedido


class TestesPedidosContextuais(unittest.TestCase):
    def test_pedido_educado_conserva_operadores_e_qualificadores(self):
        for conteudo in ("RNA não codificante", "árvore binária em C++",
                         "DNA sob uma condição inventada", "um termo e compare com outro"):
            pedido = "Você poderia definir " + conteudo + "?"
            self.assertEqual(preparar_pedido(pedido), "defina " + conteudo + "?")
        self.assertEqual(Crivo._alvo_definicao("Defina uma árvore binária, por gentileza."),
                         "arvore binaria")
        self.assertEqual(Crivo._alvo_definicao("Qual o significado do termo C++?"), "c++")

    def test_cortesia_nao_apaga_citacoes_condicoes_ou_novos_pedidos(self):
        for texto in ('Defina "por favor"', 'print("por gentileza")',
                      "Se puder, defina o termo", "Não defina RNA, por favor; explique DNA",
                      "Defina RNA, por favor, e compare com DNA"):
            self.assertEqual(limpar_cortesia(texto), texto)
        self.assertEqual(preparar_pedido("Você não pode definir RNA?"),
                         "Você não pode definir RNA?")

    def test_definicoes_reais_nao_respondem_so_ao_topico(self):
        for pedido in ("Você poderia definir o termo RNA?", "O que quer dizer RNA?",
                       "Qual é o significado de RNA?", "Defina RNA, por gentileza."):
            with self.subTest(pedido=pedido):
                self.assertEqual(Crivo().responder(pedido)[0], "conhecimento:rna")
        self.assertEqual(Crivo().responder("Defina RNA antigravitacional, por gentileza.")[0], "fora")

    def test_identidade_e_entendimento_nao_roubam_pergunta_factual(self):
        for pedido in ("vc é uma ia?", "Você é uma inteligência artificial?"):
            self.assertEqual(Crivo().responder(pedido)[0], "social:identidade")
        self.assertEqual(Crivo().responder("vc me entende?")[0], "social:compreensao")
        for pedido in ("Você pode explicar o que é RNA?", "Você acha que a Terra é uma estrela?"):
            self.assertNotIn(Crivo().responder(pedido)[0], ("social:identidade", "social:compreensao"))

    def test_fonte_da_ultima_resposta_sem_transferir_evidencias(self):
        bot = Crivo()
        bot.responder("O que é RNA?")
        ident, texto = bot.responder("Quais são as fontes dessa explicação?")
        self.assertEqual(ident, "escrita:fontes")
        self.assertIn("https://", texto)
        bot.responder("Olá")
        ident, texto = bot.responder("Qual é a fonte dessa resposta?")
        self.assertEqual(ident, "duvida")
        self.assertNotIn("https://", texto)
        self.assertEqual(Crivo().responder("Qual é a fonte dessa informação?")[0], "duvida")

    def test_interpretacao_neural_errada_nao_intercepta_fonte(self):
        bot = Crivo(usar_dialogo_contextual=True)
        bot.responder("O que é RNA?")
        with patch.object(bot.conversacao.contextual, "_compreender", side_effect=AssertionError("Fonte interceptada")):
            self.assertEqual(bot.responder("Qual é a fonte dessa resposta?")[0], "escrita:fontes")


if __name__ == "__main__":
    unittest.main()
