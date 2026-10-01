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


    def test_formacao_e_mecanismos_documentados(self):
        curriculo = ler_curriculo(PASTA / "conhecimento_mundo.json")
        itens = {item["nome"]: item for item in curriculo["itens"]}
        expectativas = {
            "planeta": ("formacao", "funcionamento"),
            "estrela": ("formacao", "funcionamento"),
            "sistema solar": ("formacao", "funcionamento"),
            "disco protoplanetário": ("definicao", "detalhe"),
            "acréscimo planetário": ("definicao", "detalhe"),
            "protoestrela": ("definicao", "detalhe"),
            "planetesimal": ("definicao", "detalhe"),
            "diferenciação planetária": ("definicao", "detalhe"),
            "zona habitável": ("definicao", "limite"),
        }
        for nome, papeis in expectativas.items():
            with self.subTest(conceito=nome):
                self.assertIn(nome, itens)
                fatos = itens[nome]["fatos"]
                self.assertGreaterEqual(len(fatos), 3)
                self.assertTrue(all(f["fonte"] in curriculo["fontes"] for f in fatos))
                for aspecto in papeis:
                    self.assertTrue(any(f["papel"] == aspecto or f.get("aspecto") == aspecto for f in fatos), (nome, aspecto))

    def test_limites_cientificos_explicitos(self):
        curriculo = ler_curriculo(PASTA / "conhecimento_mundo.json")
        itens = {item["nome"]: item for item in curriculo["itens"]}
        for nome in ("planeta", "estrela", "sistema solar", "zona habitável"):
            with self.subTest(conceito=nome):
                self.assertTrue(any(f["papel"] == "limite" for f in itens[nome]["fatos"]))

if __name__ == "__main__":
    unittest.main()
