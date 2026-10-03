"""Regressões do print: duas definições e classes vs. composição.

Casos pré-registrados antes da mudança. Verificação de desenvolvimento.
"""
import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from raciocinio import GrafoRaciocinio
from interpretacao_geral import InterpretadorGeral
from web_core import responder_web


class TestesCoordenacaoDefinicional(unittest.TestCase):
    def test_html_css_recebem_duas_definicoes_sem_javascript(self):
        for pergunta in ("O que é HTML e CSS?", "O que são HTML e CSS?",
                         "Defina HTML e CSS.", "Explique o que é HTML e CSS."):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "composto:definicao")
                self.assertIn("HTML:", resposta)
                self.assertIn("CSS:", resposta)
                self.assertIn("estrutura", resposta.lower())
                self.assertIn("apresentação", resposta.lower())
                self.assertNotIn("JavaScript pode reagir", resposta)
                self.assertNotIn(chr(96) * 3, resposta)

    def test_dominios_e_tres_conceitos(self):
        casos = (
            ("O que é o Sol e a Lua?", ("Sol:", "Lua:")),
            ("O que é Git e SQL?", ("Git:", "SQL:")),
            ("O que é fotossíntese e árvore?", ("fotossíntese:", "árvore:")),
            ("O que é HTML, CSS e SQL?", ("HTML:", "CSS:", "SQL:")),
            ("O que são árvore, Lua e Git?", ("árvore:", "Lua:", "Git:")),
        )
        for pergunta, termos in casos:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "composto:definicao")
                for termo in termos:
                    self.assertIn(termo, resposta)

    def test_um_alvo_desconhecido_nao_aciona_assunto_vizinho(self):
        for pergunta in ("O que é HTML e Rust?",
                         "O que é Sol e planeta quântico?",
                         "O que é CSS e uma entidade inventada?"):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertIn(ident, ("fora", "duvida"))
                self.assertNotIn("JavaScript pode reagir", resposta)
                self.assertNotIn("Uma árvore é uma planta", resposta)

    def test_nao_confundir_perguntas_sobre_causas_nem_quatro_conceitos(self):
        for pergunta in ("O que é CSS e HTML e SQL e Git?",
                         "O que é HTML e por que CSS existe?"):
            with self.subTest(pergunta=pergunta):
                ident, _ = Crivo().responder(pergunta)
                self.assertNotEqual(ident, "composto:definicao")

    def test_base_customizada_nao_herda_fatos_padrao(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "conhecimento.json"
            entries = [
                {"id": "luz_ficticia", "topico": "clima",
                 "perguntas": ["o que é lumix", "explique lumix"],
                 "resposta": "Lumix é uma partícula imaginária."},
                {"id": "sombra_ficticia", "topico": "clima",
                 "perguntas": ["o que é dromix", "explique dromix"],
                 "resposta": "Dromix é um fenômeno imaginário."},
            ]
            path.write_text(json.dumps(entries, ensure_ascii=False),
                            encoding="utf-8")
            bot = Crivo(path)
            ident, resposta = bot.responder("O que é lumix e dromix?")
            self.assertEqual(ident, "composto:definicao")
            self.assertIn("Lumix", resposta)
            self.assertIn("Dromix", resposta)
            self.assertNotIn("JavaScript", resposta)

    def test_nao_altera_definicoes_simples_com_exemplos(self):
        for pergunta, ident in (
            ("O que é HTML?", "web_html"),
            ("O que é CSS?", "web_css"),
            ("O que é JavaScript?", "js_intro"),
            ("O que é uma árvore?", "arvore"),
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], ident)

    def test_endpoint_e_estado_de_dialogo(self):
        resposta = responder_web({"message": "O que é HTML e CSS?"})
        self.assertEqual(resposta["id"], "composto:definicao")
        self.assertIn("HTML:", resposta["response"])
        self.assertIn("CSS:", resposta["response"])
        self.assertFalse(resposta["has_proof"])
        bot = Crivo()
        self.assertEqual(bot.responder("planta")[0], "duvida")
        self.assertEqual(bot.responder("O que é HTML e CSS?")[0],
                         "composto:definicao")
        self.assertIsNone(bot.esclarecimento)
        self.assertEqual(bot.responder("2")[0], "duvida")


class TestesRelacoesAntesDeAusencia(unittest.TestCase):
    def test_print_terra_via_lactea(self):
        ident, resposta = Crivo().responder(
            "Qual é a semelhança entre a terra e a via Láctea?")
        self.assertEqual(ident, "logica:ligacao")
        self.assertIn("Terra → Sistema Solar → Via Láctea", resposta)
        self.assertIn("parte", resposta.lower())
        self.assertIn("classe comum", resposta.lower())

    def test_outros_exemplos_bidirecionais(self):
        casos = (
            ("O que Terra e Via Láctea têm em comum?",
             "Terra → Sistema Solar → Via Láctea"),
            ("Qual a semelhança entre Via Láctea e Terra?",
             "Terra → Sistema Solar → Via Láctea"),
            ("Qual a semelhança entre Sol e Universo?",
             "Sol → Sistema Solar → Via Láctea → Universo"),
        )
        for pergunta, prova in casos:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "logica:ligacao")
                self.assertIn(prova, resposta)

    def test_ainda_identifica_ancestral_comum(self):
        for pergunta, esperado in (
            ("O que pinguim e tucano têm em comum?", "ave"),
            ("Qual a semelhança entre Terra e Marte?", "planeta"),
            ("O que gato e cachorro têm em comum?", "mamífero"),
        ):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "logica:comum")
                self.assertIn(esperado, resposta.lower())

    def test_desconhecido_continua_sem_prova(self):
        for pergunta in ("Qual a semelhança entre gato e Sistema Solar?",
                         "Qual é a relação entre gato e Sistema Solar?"):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "logica:sem_ligacao")
                self.assertIn("não prova", resposta.lower())
                resultado = responder_web({"message": pergunta})
                self.assertFalse(resultado["has_proof"])
        self.assertFalse(responder_web({"message": "O gato é um peixe?"})
                         ["has_proof"])

    def test_grafo_sintetico_sem_regras_por_nome(self):
        grafo = GrafoRaciocinio({
            "versao": 1, "entidades": {
                "a": {"nome": "rolim"},
                "b": {"nome": "mapax"},
                "c": {"nome": "zentra"},
                "d": {"nome": "nolix"},
            },
            "fatos": [
                {"sujeito": "a", "relacao": "parte_de", "objeto": "b"},
                {"sujeito": "b", "relacao": "parte_de", "objeto": "c"},
            ],
        })
        inter = InterpretadorGeral(grafo)
        ident, resposta = inter.interpretar(
            "Qual a semelhança entre rolim e zentra?")
        self.assertEqual(ident, "logica:ligacao")
        self.assertIn("rolim → mapax → zentra", resposta)
        ident, resposta = inter.interpretar(
            "Qual a semelhança entre rolim e nolix?")
        self.assertEqual(ident, "logica:sem_ligacao")
        self.assertIn("não prova", resposta)
