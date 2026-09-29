"""Contratos pré-registrados antes da implementação do PR #12.

O recuperador não deve inventar provas negativas pela ausência de fatos.
Quando há evidências disjuntas explícitas e referência editorial validada,
pode usar a explicação já escrita na base, com a prova estruturada.
"""
import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from raciocinio import GrafoRaciocinio


class TestesIntegracaoEvidencias(unittest.TestCase):
    def test_negação_explicita_consulta_texto_verificado(self):
        for pergunta, expected, evidencias in (
            ("aranha é inseto?", "insetos", ("não são insetos", "aracnídeo")),
            ("sapo é réptil?", "reptil_anfibio", ("anfíbios", "réptil")),
        ):
            with self.subTest(pergunta=pergunta):
                bot = Crivo()
                identificador, resposta = bot.responder(pergunta)
                self.assertEqual(identificador, expected)
                for evid in evidencias:
                    self.assertIn(evid.lower(), resposta.lower())
                self.assertIn("Relações", resposta)
                self.assertEqual(bot.historico[-1]["id"], expected)

    def test_afirmacao_com_fonte_editorial_usada_sem_perder_prova(self):
        bot = Crivo()
        ident, resposta = bot.responder("o sol é uma estrela?")
        self.assertEqual(ident, "sol")
        self.assertIn("O Sol é uma estrela", resposta)
        self.assertIn("Sol → estrela", resposta)

    def test_conclusao_positiva_nova_continua_multissalto(self):
        bot = Crivo()
        ident, resposta = bot.responder("Um pinguim é um ser vivo?")
        self.assertEqual(ident, "logica:tipo_de")
        self.assertIn("pinguim → ave → vertebrado → animal → ser vivo", resposta)

    def test_ausencia_de_prova_nao_gera_negacao(self):
        for pergunta in ("O gato é um peixe?", "A baleia é uma ave?",
                         "A Lua orbita Júpiter?"):
            with self.subTest(pergunta=pergunta):
                bot = Crivo()
                ident, resposta = bot.responder(pergunta)
                self.assertEqual(ident, "logica:desconhecido")
                self.assertIn("não significa que a afirmação seja falsa", resposta)

    def test_a_prova_disjunta_funciona_sem_nomes_conhecidos(self):
        entidades = {chave: {"nome": chave} for chave in
                     ("x", "a", "b", "d", "z")}
        fatos = [
            {"sujeito": "x", "objeto": "a", "relacao": "tipo_de"},
            {"sujeito": "a", "objeto": "b", "relacao": "tipo_de"},
            {"sujeito": "b", "objeto": "d", "relacao": "disjunto_de",
             "fonte_id": "explicacao"},
        ]
        g = GrafoRaciocinio({"versao": 1, "entidades": entidades, "fatos": fatos})
        proof = g.provar_incompatibilidade("x", "d")
        self.assertIsNotNone(proof)
        self.assertEqual(proof[0], ["x", "a", "b"])
        self.assertEqual(proof[1], ["d"])
        self.assertEqual(proof[2], "explicacao")
        self.assertIsNone(g.provar_incompatibilidade("x", "z"))
        self.assertEqual(g.interpretar("x é d?")[0], "logica:negacao_comprovada")
        self.assertEqual(g.interpretar("d é x?")[0], "logica:negacao_comprovada")

    def test_incompatibilidade_nao_usa_parte_de(self):
        entidades = {chave: {"nome": chave} for chave in
                     ("x", "a", "b", "z")}
        fatos = [
            {"sujeito": "x", "objeto": "a", "relacao": "parte_de"},
            {"sujeito": "a", "objeto": "b", "relacao": "disjunto_de"},
        ]
        g = GrafoRaciocinio({"versao": 1, "entidades": entidades, "fatos": fatos})
        self.assertIsNone(g.provar_incompatibilidade("x", "b"))
        self.assertEqual(g.interpretar("x é b?")[0], "logica:desconhecido")

    def test_incompatibilidade_contraditoria_e_rejeitada(self):
        entidades = {chave: {"nome": chave} for chave in ("x", "a", "b")}
        for fatos in (
            [{"sujeito": "x", "objeto": "a", "relacao": "tipo_de"},
             {"sujeito": "a", "objeto": "x", "relacao": "disjunto_de"}],
            [{"sujeito": "a", "objeto": "x", "relacao": "disjunto_de"},
             {"sujeito": "x", "objeto": "a", "relacao": "tipo_de"}],
        ):
            with self.subTest(fatos=fatos), self.assertRaises(ValueError):
                GrafoRaciocinio({"versao": 1, "entidades": entidades, "fatos": fatos})

    def test_fonte_inexistente_nao_ganha_validade_automatica(self):
        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta) / "conhecimento.json"
            base.write_text(json.dumps([{
                "id": "assunto", "topico": "animais",
                "perguntas": ["o que é assunto", "explique assunto"],
                "resposta": "Texto do assunto.",
            }]), encoding="utf-8")
            grafo = {
                "versao": 1,
                "entidades": {"x": {"nome": "x"},
                              "a": {"nome": "a"},
                              "b": {"nome": "b"}},
                "fatos": [
                    {"sujeito": "x", "objeto": "a", "relacao": "tipo_de"},
                    {"sujeito": "a", "objeto": "b", "relacao": "disjunto_de",
                     "fonte_id": "fonte_ausente"},
                ]
            }
            (Path(pasta) / "relacoes.json").write_text(
                json.dumps(grafo), encoding="utf-8")
            bot = Crivo(base)
            ident, resposta = bot.responder("x é b?")
            self.assertEqual(ident, "logica:negacao_comprovada")
            self.assertNotIn("fonte_ausente", resposta)
            self.assertNotIn("Texto do assunto", resposta)

    def test_conflito_nao_contamina_deducoes_hipoteticas(self):
        bot = Crivo()
        ident, resposta = bot.responder(
            "Se todo flumbo é blim, todo blim é taro, então flumbo é taro?")
        self.assertEqual(ident, "logica:hipotese")
        self.assertIn("somente se assumirmos", resposta)


if __name__ == "__main__":
    unittest.main()
