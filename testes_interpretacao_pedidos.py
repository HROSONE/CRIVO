"""Generalização estrutural com categorias e entidades geradas fora do currículo."""
import json
import random
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from web_core import responder_web


class TestesInterpretacaoPedidos(unittest.TestCase):
    def test_captura(self):
        b = Crivo()
        ident, texto = b.responder("meu DEUS")
        self.assertEqual(ident, "social:reacao")
        self.assertNotIn("Assuntos da base", texto)
        ident, texto = b.responder("quais galáxias você conhece?")
        self.assertEqual(ident, "logica:consulta")
        self.assertEqual(set(b.contexto_consulta), {"andromeda", "via_lactea"})
        self.assertIn("Andrômeda", texto)
        self.assertIn("Via Láctea", texto)
        self.assertNotIn("condições da consulta", texto)

    def test_operadores_independentes_do_assunto(self):
        modelos = (
            "Quais {} você conhece?", "Quais {} vc conhece?",
            "Que {} tu conhece?", "Quais são as {} que você conhece?",
            "Você conhece {}?", "Quais {} existem?",
            "Você sabe quais {} existem?", "Me dê exemplos de {}",
            "Você pode citar exemplos de {}?", "Me diga nomes de {}",
        )
        for categoria, esperado in (("galáxias", {"andromeda", "via_lactea"}),
                                    ("aves", {"pinguim", "tucano"}),
                                    ("planetas", {"mercurio", "venus", "terra", "marte", "jupiter", "saturno", "urano", "netuno"})):
            for modelo in modelos:
                with self.subTest(categoria=categoria, modelo=modelo):
                    bot = Crivo()
                    self.assertEqual(bot.responder(modelo.format(categoria))[0], "logica:consulta")
                    self.assertEqual(set(bot.contexto_consulta), esperado)

    def test_categorias_e_nomes_gerados_com_oraculo_independente(self):
        # O oráculo vem das atribuições do gerador, não do parser/provador.
        for semente in (13, 47, 91, 203):
            rng = random.Random(semente)
            nome = "grupo zul" + str(semente)
            entidades = {"raiz": {"nome": nome}, "sub": {"nome": "subgrupo nex"},
                         "outra": {"nome": "grupo fora"}, "alvo": {"nome": "centro y"}}
            fatos = [{"sujeito": "sub", "relacao": "tipo_de", "objeto": "raiz"}]
            esperado, filtrado = set(), set()
            for i in range(16):
                ident = "item_" + str(i)
                entidades[ident] = {"nome": "objeto " + str(rng.randrange(10000, 99999))}
                pertence = rng.choice((True, False))
                orbita = rng.choice((True, False))
                fatos.append({"sujeito": ident, "relacao": "tipo_de",
                              "objeto": "sub" if pertence else "outra"})
                if pertence:
                    esperado.add(ident)
                    if orbita:
                        filtrado.add(ident)
                if orbita:
                    fatos.append({"sujeito": ident, "relacao": "orbita", "objeto": "alvo"})
            with tempfile.TemporaryDirectory() as pasta:
                p = Path(pasta)
                (p / "conhecimento.json").write_text(json.dumps([{
                    "id": "ficcao", "topico": "clima", "perguntas": ["o que é lum"],
                    "resposta": "Lum é um termo fictício de teste."}]), encoding="utf-8")
                (p / "relacoes.json").write_text(json.dumps({"versao": 1,
                    "entidades": entidades, "fatos": fatos}), encoding="utf-8")
                bot = Crivo(p / "conhecimento.json")
                for q in ("Quais " + nome + " você conhece?", "Me dê exemplos de " + nome):
                    self.assertEqual(bot.responder(q)[0], "logica:consulta")
                    self.assertEqual(set(bot.contexto_consulta), esperado)
                bot.responder("Quais " + nome + " você conhece que orbitam centro y?")
                self.assertEqual(set(bot.contexto_consulta or ()), filtrado)
                exemplo = sorted(esperado)[0]
                ident, resposta = bot.responder("O que você sabe sobre " + entidades[exemplo]["nome"] + "?")
                self.assertEqual(ident, "logica:fatos")
                self.assertIn(entidades[exemplo]["nome"] + " é um tipo de subgrupo nex", resposta)

    def test_classes_e_exemplos_sao_operacoes_diferentes(self):
        bot = Crivo()
        self.assertEqual(bot.responder("Quais tipos de galáxias você conhece?")[0], "logica:consulta")
        self.assertEqual(set(bot.contexto_consulta), {"galaxia_espiral"})
        bot.responder("Quais galáxias espirais você conhece?")
        self.assertEqual(set(bot.contexto_consulta), {"andromeda", "via_lactea"})

    def test_preserva_todas_as_condicoes(self):
        for q in ("Quais galáxias vermelhas você conhece?",
                  "Quais galáxias você conhece que podem orbitar o Sol?",
                  "Quais galáxias você conhece que orbitam o Sol ou a Terra?",
                  "Quais galáxias quânticas você conhece?",
                  "Quais galáxias ou planetas você conhece?"):
            with self.subTest(q=q):
                bot = Crivo()
                ident, _ = bot.responder(q)
                self.assertNotEqual(ident, "logica:consulta")
                self.assertIsNone(bot.contexto_consulta)

    def test_escopo_do_conhecimento_nao_finge_lista_universal(self):
        ident, texto = Crivo().responder("Quais galáxias existem?")
        self.assertEqual(ident, "logica:consulta")
        self.assertIn("base", texto)
        self.assertIn("outros", texto)

    def test_pedidos_de_informacao_usam_o_conceito_inteiro(self):
        for q, esperado in (("O que você sabe sobre DNA?", "conhecimento:dna"),
                            ("O que vc conhece sobre RNA?", "conhecimento:rna"),
                            ("Você conhece Andrômeda?", "conhecimento:andromeda"),
                            ("Você tem informações sobre HTML?", "web_html")):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], esperado)
        for q in ("O que você sabe sobre DNA quântico?", "Você conhece Andrômeda vermelha?"):
            self.assertNotIn(Crivo().responder(q)[0], ("conhecimento:dna", "conhecimento:andromeda"))

    def test_informacoes_relacionais_sem_verbete_editorial(self):
        r = responder_web({"message": "O que você sabe sobre o tucano?"})
        self.assertEqual(r["id"], "logica:fatos")
        self.assertIn("tucano é um tipo de ave", r["response"])
        self.assertTrue(r["has_proof"])
        self.assertNotEqual(Crivo().responder("O que você sabe sobre o tucano quântico?")[0],
                            "logica:fatos")

    def test_lista_sustenta_refinamento_e_referencia_por_posicao(self):
        bot = Crivo()
        bot.responder("Quais galáxias você conhece?")
        self.assertEqual(bot.responder("fale sobre a primeira")[0], "conhecimento:andromeda")
        bot.responder("Quais galáxias você conhece?")
        self.assertEqual(bot.responder("Dessas, quais são galáxias espirais?")[0], "logica:consulta")
        self.assertEqual(set(bot.contexto_consulta), {"andromeda", "via_lactea"})
        bot.responder("Oi")
        self.assertEqual(bot.responder("fale sobre a primeira")[0], "duvida")

    def test_reacoes_nao_engolem_perguntas_ou_comandos(self):
        for q in ("meu Deus", "nossa", "caramba", "eita", "aff"):
            self.assertEqual(Crivo().responder(q)[0], "social:reacao")
        self.assertEqual(Crivo().responder("Meu Deus! Quais galáxias você conhece?")[0], "logica:consulta")
        for q in ("O que é Deus?", "Escreva um programa que imprima 'meu Deus'",
                  "Quais galáxias uma pessoa conhece?", "Você não conhece DNA?",
                  "Se você conhece galáxias, quais são vermelhas?"):
            self.assertNotEqual(Crivo().responder(q)[0], "social:reacao")

    def test_api_e_pedido_explicitado(self):
        r = responder_web({"message": "Quais galáxias você conhece?", "history": ["meu Deus"]})
        self.assertEqual(r["id"], "logica:consulta")
        self.assertTrue(r["has_proof"])
        bot = Crivo()
        bot.responder("Quais galáxias você conhece?")
        self.assertEqual(bot.historico[-1]["pedido"]["intencao"], "listar")
        self.assertEqual(bot.historico[-1]["pedido"]["alvo"], "galaxias")
        self.assertEqual(responder_web({"message": "fale sobre a primeira"})["id"], "duvida")

    def test_categoria_sem_exemplos_nao_e_negada(self):
        r = Crivo().responder("Quais galáxias você conhece que orbitam Marte?")
        self.assertEqual(r[0], "logica:desconhecido")
        self.assertIn("não prova que não existam", r[1])

    def test_listas_editoriais_sem_esquema_nao_sao_bloqueadas(self):
        for q, esperado in (("tipos de clima brasileiro", "climas_brasil"),
                            ("nomes das estações", "quais_estacoes"),
                            ("nomes dos planetas em ordem", "planetas")):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], esperado)

    def test_limite_e_contexto_nao_recuperam_itens_ocultos(self):
        from testes_consultas_relacionais import grafo_sintetico
        from consultas_relacionais import ConsultasRelacionais, MAX_EXIBIDOS
        from raciocinio import GrafoRaciocinio
        from interpretacao_pedidos import InterpretadorPedidos
        dados, _, _, _ = grafo_sintetico(60, 219)
        g = GrafoRaciocinio(dados)
        consultor = ConsultasRelacionais(g)
        motor = InterpretadorPedidos(g, consultor)
        ident, resposta, contexto = motor.responder(motor.analisar("Quais zutrins você conhece?"))
        self.assertEqual(ident, "logica:consulta")
        self.assertEqual(len(contexto), MAX_EXIBIDOS)
        self.assertTrue(all(e.startswith("objeto_") for e in contexto))
        _, _, filtrado = consultor.responder("Desses, quais orbitam nex?", contexto)
        self.assertLessEqual(set(filtrado or ()), set(contexto))
        self.assertIn("Exibindo", resposta)


if __name__ == "__main__":
    unittest.main()
