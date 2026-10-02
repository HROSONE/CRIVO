"""Provas prospectivas da consolidacao de conhecimento.

As perguntas abaixo nao sao copiadas da prova congelada de astronomia. Elas
cobram parafrase, recuperacao de mecanismo, comparacao e um caso sintetico
com nomes inexistentes no curriculo, para verificar que a logica e generica.
"""
import unittest

from consolidacao_conhecimento import ConsolidadorConhecimento
from crivo import Crivo, tokens


class TestesConsolidacaoConhecimento(unittest.TestCase):
    def test_definicao_com_enquadramento_extra(self):
        ident, resposta = Crivo().responder(
            "Me descreva Vênus como um mundo do Sistema Solar.")
        self.assertNotEqual(ident, "fora")
        self.assertIn("segundo planeta", resposta)
        self.assertIn("rochoso", resposta)

    def test_comparacao_recupera_fato_que_liga_duas_entidades(self):
        bot = Crivo()
        ident, resposta = bot.responder(
            "Por que Vênus tem temperatura maior que Mercúrio?")
        self.assertNotEqual(ident, "fora")
        self.assertIn("efeito estufa", resposta.lower())
        self.assertIn("Mercúrio", resposta)
        self.assertIsNotNone(bot.contexto_textual)
        self.assertTrue(bot.contexto_textual.provas)

    def test_causa_em_parafrase_recupera_marte(self):
        ident, resposta = Crivo().responder(
            "O que deixa Marte com aparência vermelha?")
        self.assertNotEqual(ident, "fora")
        self.assertIn("Óxidos de ferro", resposta)

    def test_mecanismo_em_parafrase_recupera_urano(self):
        ident, resposta = Crivo().responder(
            "De que maneira o eixo inclinado de Urano afeta suas estações?")
        self.assertNotEqual(ident, "fora")
        self.assertIn("sazonal", resposta.lower())
        self.assertIn("inclinação", resposta.lower())

    def test_mecanismo_recupera_aneis_de_saturno(self):
        ident, resposta = Crivo().responder(
            "Por qual mecanismo as partículas dos anéis de Saturno continuam orbitando?")
        self.assertNotEqual(ident, "fora")
        self.assertIn("campo gravitacional", resposta.lower())
        self.assertIn("partículas", resposta.lower())

    def test_formacao_recupera_conhecimento_sem_pergunta_memorizada(self):
        ident, resposta = Crivo().responder(
            "Explique a origem do Sistema Solar.")
        self.assertNotEqual(ident, "fora")
        self.assertTrue("nuvem" in resposta.lower() or "disco" in resposta.lower())

    def test_fontes_continuam_ligadas_aos_fatos_usados(self):
        bot = Crivo()
        bot.responder("O que deixa Marte com aparência vermelha?")
        ident, resposta = bot.responder("Fontes")
        self.assertEqual(ident, "escrita:fontes")
        self.assertIn("nasa", resposta.lower())

    def test_qualificador_sem_evidencia_nao_e_descartado(self):
        ident, _ = Crivo().responder(
            "Como a atmosfera mágica de Vênus retém calor?")
        self.assertEqual(ident, "fora")

    def test_algoritmo_funciona_com_conceitos_sinteticos(self):
        itens = {
            "zunto": {
                "nome": "zunto",
                "aliases": [],
                "fatos": [{
                    "texto": "Zunto produz calor ao comprimir torva.",
                    "papel": "detalhe",
                    "aspecto": "funcionamento",
                }],
            },
            "torva": {
                "nome": "torva",
                "aliases": [],
                "fatos": [{
                    "texto": "Torva é uma peça fictícia de teste.",
                    "papel": "definicao",
                }],
            },
        }
        aliases = {"zunto": {"zunto"}, "torva": {"torva"}}
        motor = ConsolidadorConhecimento(itens, aliases, tokens)
        plano = motor.buscar("Por que zunto deixa torva quente?")
        self.assertIsNotNone(plano)
        self.assertEqual(plano.selecionados[0], ("zunto", 0))


if __name__ == "__main__":
    unittest.main()
