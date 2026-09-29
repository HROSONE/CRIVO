"""Testes pré-registrados do analisador de português.

A análise separa INTENÇÃO, SUJEITO, PREDICADO e OBJETO. A resposta só
pode ser produzida a partir de definições ou relações já cadastradas.
Testes são desenvolvimento; nenhum deles treina a rede neural.
"""
import json
import tempfile
import unittest
from pathlib import Path

from analisador_portugues import AnalisadorPortugues, QuadroSemantico
from crivo import Crivo
from raciocinio import GrafoRaciocinio
from web_core import responder_web


class TestesQuadrosSemanticos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = Crivo()
        cls.analisador = AnalisadorPortugues(cls.bot.raciocinio)

    def test_separa_intencao_e_sujeito_predicado_objeto(self):
        casos = (
            ("Gostaria de saber se o pinguim pertence ao grupo das aves",
             ("verificar", "pinguim", "tipo_de", "ave")),
            ("O Sistema Solar contém a Terra?",
             ("verificar", "terra", "parte_de", "sistema_solar")),
            ("A Terra é orbitada pela Lua?",
             ("verificar", "lua", "orbita", "terra")),
            ("O pinguim possui penas?",
             ("verificar", "pinguim", "tem_caracteristica", "penas")),
            ("Em que pinguim e tucano se parecem?",
             ("comparar", "pinguim", "comum", "tucano")),
            ("Existe alguma ligação entre Terra e Via Láctea?",
             ("relacionar", "terra", "ligacao", "via_lactea")),
            ("Você poderia me explicar o que é HTML?",
             ("definir", "html", "definicao", None)),
            ("Qual característica o pinguim apresenta?",
             ("enumerar", "pinguim", "tem_caracteristica", None)),
        )
        for texto, esperado in casos:
            with self.subTest(texto=texto):
                quadro = self.analisador.analisar(texto)
                self.assertIsInstance(quadro, QuadroSemantico)
                self.assertEqual((quadro.intencao, quadro.sujeito,
                                  quadro.predicado, quadro.objeto), esperado)

    def test_variacoes_de_classificacao_em_qualquer_area(self):
        casos = (
            ("Quero saber se o pinguim pertence ao grupo das aves",
             "logica:tipo_de", "pinguim → ave"),
            ("Você pode dizer se o golfinho é considerado mamífero?",
             "logica:tipo_de", "golfinho → mamífero"),
            ("O Sol pode ser considerado uma estrela?",
             "logica:tipo_de", "Sol → estrela"),
            ("Os gatos são classificados como mamíferos?",
             "logica:tipo_de", "gato → mamífero"),
            ("Seria correto classificar o tucano como ave?",
             "logica:tipo_de", "tucano → ave"),
            ("Marte pertence à categoria dos planetas?",
             "logica:tipo_de", "Marte → planeta"),
            ("A baleia pertence ao grupo dos répteis?",
             "logica:desconhecido", "não significa"),
        )
        for pergunta, id_, trecho in casos:
            with self.subTest(pergunta=pergunta):
                obtido, resposta = Crivo().responder(pergunta)
                self.assertEqual(obtido, id_)
                self.assertIn(trecho, resposta)

    def test_partes_orbitas_e_propriedades_sem_inverter_sentido(self):
        casos = (
            ("O Sistema Solar contém a Terra?",
             "logica:parte_de", "Terra → Sistema Solar"),
            ("O universo contém a Terra?",
             "logica:parte_de", "Terra → Sistema Solar → Via Láctea → Universo"),
            ("A Terra está contida no Sistema Solar?",
             "logica:parte_de", "Terra → Sistema Solar"),
            ("A Via Láctea inclui o Sistema Solar?",
             "logica:parte_de", "Sistema Solar → Via Láctea"),
            ("A Terra é orbitada pela Lua?",
             "logica:orbita", "Lua --orbita--> Terra"),
            ("O Sol é orbitado por Marte?",
             "logica:orbita", "Marte --orbita--> Sol"),
            ("A Lua dá voltas ao redor da Terra?",
             "logica:orbita", "Lua --orbita--> Terra"),
            ("O pinguim apresenta penas?",
             "logica:tem_caracteristica", "pinguim"),
            ("Marte gira em torno do Sol?",
             "logica:orbita", "Marte --orbita--> Sol"),
        )
        for pergunta, esperado, prova in casos:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, esperado)
                self.assertIn(prova, resposta)

    def test_comparacao_variando_ordem_e_formulacao(self):
        casos = (
            ("Em que pinguim e tucano se parecem?",
             "logica:comum", "ave"),
            ("Pinguim e tucano compartilham alguma classificação?",
             "logica:comum", "ave"),
            ("Existe alguma ligação entre Terra e Via Láctea?",
             "logica:ligacao", "Terra → Sistema Solar → Via Láctea"),
            ("Como a Lua e a Terra se relacionam?",
             "logica:ligacao", "Lua --orbita--> Terra"),
            ("Que relação há entre o Sol e o Universo?",
             "logica:ligacao", "Sol → Sistema Solar → Via Láctea → Universo"),
        )
        for pergunta, esperado, prova in casos:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, esperado)
                self.assertIn(prova, resposta)

    def test_extrai_definicao_sem_achar_assunto_vizinho(self):
        casos = (
            ("Você poderia me explicar o que é HTML?", "web_html"),
            ("Me diga o que significa fotossíntese", "fotossintese"),
            ("Gostaria de saber o que é o Sol", "sol"),
            ("Poderia definir CSS pra mim?", "web_css"),
            ("Como se define a Lua?", "lua"),
            ("Me explique o que é uma árvore", "arvore"),
        )
        for pergunta, esperado in casos:
            with self.subTest(pergunta=pergunta):
                ident, _ = Crivo().responder(pergunta)
                self.assertEqual(ident, esperado)
        for pergunta in (
            "Você poderia me explicar o que é uma árvore binária?",
            "Me diga o que é uma tecnologia quântica desconhecida",
            "Poderia definir Rust pra mim?",
        ):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertIn(ident, ("fora", "duvida"))
                self.assertNotIn("HTML descreve", resposta)

    def test_perguntas_abertas_de_caracteristicas_exigem_prova(self):
        for pergunta, trecho in (
            ("Qual característica o pinguim apresenta?", "penas"),
            ("Que característica os gatos possuem?", "respiração aérea"),
        ):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "logica:caracteristicas")
                self.assertIn(trecho, resposta)
                self.assertIn("→", resposta)
                resposta_api = responder_web({"message": pergunta})
                self.assertTrue(resposta_api["has_proof"])
        ident, resposta = Crivo().responder(
            "Que característica a Lua possui?")
        self.assertEqual(ident, "logica:desconhecido")
        self.assertIn("não significa", resposta)

    def test_abstencao_sobre_fatos_ausentes_e_negacao(self):
        for pergunta in (
            "O pinguim não é uma ave?",
            "O gato nunca foi mamífero?",
            "Se a Lua fosse planeta, ela seria orbitada pelo Sol?",
            "A Via Láctea contém um planeta quântico inventado?",
            "A Terra dá voltas em torno da Lua?",
            "O gato está dentro do Sistema Solar?",
        ):
            with self.subTest(pergunta=pergunta):
                resultado = Crivo().responder(pergunta)
                self.assertNotIn(resultado[0],
                                 ("logica:tipo_de", "logica:parte_de", "logica:orbita",
                                  "logica:tem_caracteristica", "logica:ligacao",
                                  "logica:comum"))
        # Relações não cadastradas NÃO devem ser automaticamente falsas.
        ident, resposta = Crivo().responder(
            "A Lua dá voltas ao redor de Marte?")
        self.assertEqual(ident, "logica:desconhecido")
        self.assertIn("não significa", resposta)

    def test_parser_generaliza_em_grafo_sintetico(self):
        g = GrafoRaciocinio({
            "versao": 1,
            "entidades": {
                "gorb": {"nome": "gorb"},
                "flim": {"nome": "flim"},
                "taro": {"nome": "taro"},
                "cora": {"nome": "cora", "tipo": "caracteristica"},
                "astrox": {"nome": "astrox"},
                "vilaz": {"nome": "vilaz"},
                "univz": {"nome": "univz"},
            },
            "fatos": [
                {"sujeito": "gorb", "relacao": "tipo_de", "objeto": "flim"},
                {"sujeito": "flim", "relacao": "tipo_de", "objeto": "taro"},
                {"sujeito": "flim", "relacao": "tem_caracteristica",
                 "objeto": "cora"},
                {"sujeito": "astrox", "relacao": "orbita", "objeto": "vilaz"},
                {"sujeito": "vilaz", "relacao": "parte_de", "objeto": "univz"},
            ],
        })
        parser = AnalisadorPortugues(g)
        exemplos = (
            ("Gorb pode ser considerado um taro?", "logica:tipo_de", "gorb → flim → taro"),
            ("O taro contém o gorb?", "logica:desconhecido", "não significa"),
            ("Que característica o gorb possui?", "logica:caracteristicas", "cora"),
            ("Vilaz é orbitado por astrox?", "logica:orbita", "astrox --orbita--> vilaz"),
            ("Univz contém vilaz?", "logica:parte_de", "vilaz → univz"),
            ("Existe alguma ligação entre vilaz e univz?",
             "logica:ligacao", "vilaz → univz"),
        )
        for pergunta, identificador, sinal in exemplos:
            with self.subTest(pergunta=pergunta):
                quadro = parser.analisar(pergunta)
                self.assertIsNotNone(quadro)
                ident, resp = parser.responder(quadro)
                self.assertEqual(ident, identificador)
                self.assertIn(sinal, resp)

    def test_isolamento_de_bases_customizadas(self):
        with tempfile.TemporaryDirectory() as pasta:
            b = Path(pasta) / "conhecimento.json"
            b.write_text(json.dumps([
                {"id": "teste", "topico": "clima",
                 "perguntas": ["o que é lumix", "explica lumix"],
                 "resposta": "Lumix é um termo imaginário."}
            ]), encoding="utf-8")
            bot = Crivo(b)
            self.assertIsNone(bot.analisador_portugues.grafo)
            self.assertEqual(bot.responder("Me diga o que é lumix")[0], "teste")
            self.assertNotEqual(bot.responder(
                "O universo contém a Terra?")[0], "logica:parte_de")

    def test_api_distingue_prova_de_desconhecimento(self):
        positivo = responder_web({"message":
                                  "Gostaria de saber se o pinguim pertence ao grupo das aves"})
        self.assertEqual(positivo["id"], "logica:tipo_de")
        self.assertTrue(positivo["has_proof"])
        negativo = responder_web({"message":
                                  "A Lua dá voltas ao redor de Marte?"})
        self.assertEqual(negativo["id"], "logica:desconhecido")
        self.assertFalse(negativo["has_proof"])


if __name__ == "__main__":
    unittest.main()
