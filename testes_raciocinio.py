"""Regressões do raciocínio relacional sem modelos externos.

Não mede inteligência geral: verifica encadeamento exato dos fatos curados,
abstenção, isolamento entre bases e recombinação de relações INÉDITAS.
"""
import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from raciocinio import GrafoRaciocinio, limpar


class TestesRaciocinioRelacional(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = Crivo()

    def test_fatos_combinados_sem_pergunta_pronta(self):
        consultas = [
            ("Um golfinho é um animal?", "logica:tipo_de",
             ["golfinho", "mamífero", "vertebrado", "animal"]),
            ("Por que um pinguim é um ser vivo?", "logica:tipo_de",
             ["pinguim", "ave", "vertebrado", "animal", "ser vivo"]),
            ("Um cacto é um ser vivo?", "logica:tipo_de",
             ["cacto", "planta", "ser vivo"]),
            ("A Lua é um astro?", "logica:tipo_de",
             ["Lua", "satélite natural", "astro"]),
            ("O Sol faz parte do Universo?", "logica:parte_de",
             ["Sol", "Sistema Solar", "Via Láctea", "Universo"]),
            ("A Terra faz parte da Via Láctea?", "logica:parte_de",
             ["Terra", "Sistema Solar", "Via Láctea"]),
        ]
        for pergunta, id_esperado, etapas in consultas:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, id_esperado)
                self.assertIn(" → ".join(etapas), resposta)

    def test_nao_concluir_negacao_por_ausencia(self):
        for pergunta in ("O gato é um peixe?", "A baleia é uma ave?",
                         "A Via Láctea faz parte da Terra?"):
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "logica:desconhecido")
                self.assertIn("não significa que a afirmação seja falsa", resposta)

    def test_negacao_nao_e_reescrita_para_afirmacao(self):
        self.assertEqual(Crivo().responder("O gato não é um animal?")[0], "duvida")
        self.assertIsNone(self.bot.raciocinio.interpretar("Um gato nunca é mamífero?"))

    def test_nao_intercepta_perguntas_desconhecidas_ou_abertas(self):
        for pergunta in ("O que é uma variável em Python?",
                         "Como nasce um planeta?", "Por que chove?",
                         "Um pandas é navegador?"):
            with self.subTest(pergunta=pergunta):
                self.assertIsNone(self.bot.raciocinio.interpretar(pergunta))
        self.assertEqual(Crivo().responder("O que é o Sol?")[0], "sol")

    def test_fatos_novos_sinteticos_usam_mesmo_algoritmo(self):
        # Nenhum destes nomes existe no arquivo de conhecimento. A mesma
        # implementação precisa recombinar uma cadeia arbitrária de 14 elos.
        entidades = {"elo_%02d" % i: {"nome": "elo %d" % i}
                     for i in range(15)}
        fatos = [{"sujeito": "elo_%02d" % i, "relacao": "tipo_de",
                  "objeto": "elo_%02d" % (i + 1)}
                 for i in range(14)]
        grafo = GrafoRaciocinio({"versao": 1, "entidades": entidades, "fatos": fatos})
        cadeia = grafo.provar("elo_00", "elo_14", "tipo_de")
        self.assertEqual(len(cadeia), 15)
        self.assertIsNone(grafo.provar("elo_14", "elo_00", "tipo_de"))
        self.assertEqual(grafo.interpretar("Elo 0 é um elo 14?")[0],
                         "logica:tipo_de")

    def test_grafo_rejeita_alias_colidente(self):
        with self.assertRaisesRegex(ValueError, "ambíguo"):
            GrafoRaciocinio({
                "versao": 1, "entidades": {
                    "um": {"nome": "gato"},
                    "dois": {"nome": "gata", "aliases": ["gato"]}},
                "fatos": []})

    def test_grafo_rejeita_ciclos(self):
        with self.assertRaisesRegex(ValueError, "Ciclo"):
            GrafoRaciocinio({
                "versao": 1,
                "entidades": {"alfa": {"nome": "alfa"},
                             "beta": {"nome": "beta"},
                             "gama": {"nome": "gama"}},
                "fatos": [
                    {"sujeito": "alfa", "relacao": "tipo_de", "objeto": "beta"},
                    {"sujeito": "beta", "relacao": "tipo_de", "objeto": "gama"},
                    {"sujeito": "gama", "relacao": "tipo_de", "objeto": "alfa"}]})

    def test_grafo_nao_contamina_base_personalizada(self):
        with tempfile.TemporaryDirectory() as temp:
            arquivo = Path(temp) / "conhecimento.json"
            arquivo.write_text(json.dumps([{
                "id": "teste", "topico": "plantas", "perguntas": ["teste simples"],
                "resposta": "Resposta de teste."
            }]), encoding="utf-8")
            bot = Crivo(arquivo)
            self.assertIsNone(bot.raciocinio)
            self.assertNotEqual(bot.responder("Um golfinho é um animal?")[0],
                                "logica:tipo_de")

    def test_normalizacao_preserva_entidade_composta(self):
        self.assertEqual(limpar("À Via Láctea?!"), "via lactea")
        self.assertEqual(limpar("Os Seres Vivos"), "seres vivos")

    def test_prova_usa_apenas_um_tipo_por_vez(self):
        grafo = self.bot.raciocinio
        self.assertIsNone(grafo.provar("sol", "universo", "tipo_de"))
        self.assertIsNone(grafo.provar("sol", "astro", "parte_de"))
        self.assertEqual(grafo.provar("sol", "astro", "tipo_de"),
                         ["sol", "estrela", "astro"])


if __name__ == "__main__":
    unittest.main()
