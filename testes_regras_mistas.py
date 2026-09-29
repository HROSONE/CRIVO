"""Casos definidos antes da implementação de regras mistas.

Testam três coisas distintas: herança controlada de propriedade via tipo_de,
relação orbital DIRETA e ausência de inferências sem suporte.
Estes casos tornam-se desenvolvimento ao orientar correções; não são teste cego.
"""
import json
import random
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from raciocinio import GrafoRaciocinio


class TestesRegrasMistas(unittest.TestCase):
    def test_heranca_de_caracteristicas_com_prova(self):
        casos = (
            ("Um pinguim tem penas?", ("pinguim", "ave", "penas")),
            ("Por que um tucano tem penas?", ("tucano", "ave", "penas")),
            ("Uma baleia tem respiração aérea?", ("baleia", "mamífero", "respiração aérea")),
            ("Um golfinho tem coluna vertebral?", ("golfinho", "mamífero", "vertebrado", "coluna vertebral")),
            ("Um cacto tem células?", ("cacto", "planta", "ser vivo", "células")),
            ("Um inseto possui seis patas?", ("inseto", "seis patas")),
            ("Uma abelha tem seis patas?", ("abelha", "inseto", "seis patas")),
            ("Uma aranha tem oito patas?", ("aranha", "aracnídeo", "oito patas")),
            ("O Sol possui luz própria?", ("Sol", "estrela", "luz própria")),
        )
        for pergunta, nomes in casos:
            with self.subTest(pergunta=pergunta):
                obtido, resposta = Crivo().responder(pergunta)
                self.assertEqual(obtido, "logica:tem_caracteristica")
                for nome in nomes:
                    self.assertIn(nome, resposta)
                self.assertIn("tipo_de", resposta if len(nomes) > 2 else "tipo_de")
                self.assertIn("tem_caracteristica", resposta)

    def test_orbitas_sao_relacao_direta(self):
        for pergunta in ("A Terra orbita o Sol?", "A Lua orbita a Terra?",
                         "A Lua gira em torno da Terra?"):
            with self.subTest(pergunta=pergunta):
                obtido, resposta = Crivo().responder(pergunta)
                self.assertEqual(obtido, "logica:orbita")
                self.assertIn("orbita", resposta)

    def test_nao_faz_inferencias_incorretas(self):
        casos = (
            "Um gato tem penas?",
            "Uma abelha tem oito patas?",
            "Uma aranha tem seis patas?",
            "A Lua orbita Júpiter?",
            "A Lua orbita o Sol?",
        )
        for pergunta in casos:
            with self.subTest(pergunta=pergunta):
                obtido, resposta = Crivo().responder(pergunta)
                self.assertEqual(obtido, "logica:desconhecido")
                self.assertIn("não significa", resposta)

    def test_outras_consultas_nao_interceptadas(self):
        bot = Crivo()
        for pergunta in ("Meu gato tem sede?", "Por que a Lua tem fases?",
                         "O que uma abelha come?", "Como é feito um programa?"):
            with self.subTest(pergunta=pergunta):
                self.assertIsNone(bot.raciocinio.interpretar(pergunta))
        self.assertEqual(Crivo().responder("Um pinguim não tem penas?")[0], "duvida")
        self.assertEqual(Crivo().responder("O que é o Sol?")[0], "sol")

    def test_heranca_generica_em_grafo_aleatorio(self):
        # Nomes sintéticos, outras dimensões: a regra não pode depender
        # de palavras como "pinguim", "ave" ou "penas".
        for seed in (11, 19, 43, 91, 1337):
            rng = random.Random(seed)
            n = rng.randint(7, 33)
            entidades = {"objeto_%s" % i: {"nome": "objeto %s" % i}
                         for i in range(n)}
            entidades["propriedade"] = {"nome": "propriedade z",
                                       "tipo": "caracteristica"}
            entidades["distrator"] = {"nome": "propriedade q",
                                     "tipo": "caracteristica"}
            fatos = [{"sujeito": "objeto_%s" % i, "relacao": "tipo_de",
                      "objeto": "objeto_%s" % (i+1)} for i in range(n-1)]
            fatos.append({"sujeito": "objeto_%s" % (n-1),
                          "relacao": "tem_caracteristica", "objeto": "propriedade"})
            g = GrafoRaciocinio({"versao": 1, "entidades": entidades, "fatos": fatos})
            caminho = g.provar("objeto_0", "propriedade", "tem_caracteristica")
            self.assertEqual(len(caminho), n+1)
            self.assertIsNone(g.provar("objeto_0", "distrator", "tem_caracteristica"))
            self.assertIsNone(g.provar("propriedade", "objeto_0", "tem_caracteristica"))

    def test_orbitar_nao_se_propaga_indiretamente(self):
        entidades = {x: {"nome": x} for x in ("sat", "planeta", "estrela")}
        g = GrafoRaciocinio({"versao": 1, "entidades": entidades, "fatos": [
            {"sujeito": "sat", "relacao": "orbita", "objeto": "planeta"},
            {"sujeito": "planeta", "relacao": "orbita", "objeto": "estrela"},
        ]})
        self.assertEqual(g.provar("sat", "planeta", "orbita"), ["sat", "planeta"])
        self.assertIsNone(g.provar("sat", "estrela", "orbita"))

    def test_rejeita_propriedades_mal_tipadas(self):
        entidades = {"sujeito": {"nome": "sujeito"},
                     "objeto": {"nome": "objeto"}}
        with self.assertRaisesRegex(ValueError, "caracteristica"):
            GrafoRaciocinio({"versao": 1, "entidades": entidades, "fatos": [
                {"sujeito": "sujeito", "relacao": "tem_caracteristica",
                 "objeto": "objeto"}]})

    def test_base_temporaria_nao_herda_propriedades(self):
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / "conhecimento.json"
            arq.write_text(json.dumps([{"id": "x", "topico": "animais",
                                        "perguntas": ["um x"], "resposta": "Um x."}]),
                           encoding="utf-8")
            self.assertIsNone(Crivo(arq).raciocinio)


if __name__ == "__main__":
    unittest.main()
