"""Testes de desenvolvimento: ampliação editorial de astronomia, sem alegar treino neural."""
import unittest
from crivo import Crivo, PASTA
from curriculo_mundo import ler_curriculo

NOVOS = ("galáxia", "estrela", "planeta", "satélite natural", "sistema solar", "via láctea", "exoplaneta", "planeta anão", "asteroide", "cometa", "meteoroide", "meteoro", "meteorito", "cinturão de kuiper", "nuvem de oort", "unidade astronômica", "órbita", "nebulosa", "buraco negro", "ano-luz")

class TestesAstronomiaEditorial(unittest.TestCase):
    def test_conceitos_e_proveniencia(self):
        curriculo = ler_curriculo(PASTA / "conhecimento_mundo.json")
        por_nome = {i["nome"]: i for i in curriculo["itens"]}
        for nome in NOVOS:
            with self.subTest(nome=nome):
                self.assertIn(nome, por_nome)
                item = por_nome[nome]
                self.assertEqual(item["fatos"][0]["papel"], "definicao")
                self.assertIn(item["fatos"][0]["fonte"], curriculo["fontes"])
                self.assertEqual(item["area"], "astronomia")

    def test_consulta_basica_de_assuntos_distintos(self):
        bot = Crivo()
        for nome in NOVOS:
            with self.subTest(nome=nome):
                identificador, resposta = bot.responder("O que é " + nome + "?")
                self.assertTrue(identificador.startswith("conhecimento:mundo_"), (nome, identificador))
                self.assertTrue(resposta.strip())

    def test_desconhecido_nao_recebe_resposta_inventada(self):
        for pergunta in ("O que é o planeta Zorvax-913?", "O que é a estrela Fictícia-XY99?"):
            with self.subTest(pergunta=pergunta):
                identificador, _ = Crivo().responder(pergunta)
                self.assertEqual(identificador, "fora")

if __name__ == "__main__":
    unittest.main()
