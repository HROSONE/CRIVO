"""Testes da v2 dos dados da destilação (experimentos/destilacao_20261014/professor_v2.py)."""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "experimentos" / "destilacao_20261014"))
import professor as P  # noqa: E402
import professor_v2 as V  # noqa: E402

PED = {"intencao": "desabafar", "tema": "trabalho"}


class FalasNovas(unittest.TestCase):
    def test_grade_inteira_sem_repetir(self):
        ps = V.pedidos(random.Random(1))
        self.assertEqual(len(ps), len({p["id"] for p in ps}))
        self.assertGreater(len(ps), 4000)
        self.assertEqual(len(V.pedidos(random.Random(1), 40)), 40)

    def test_linhas_tira_numeracao_e_aspas(self):
        self.assertEqual(V.linhas('1. "oi, tudo bem?"\n2) meu chefe me irritou hj\n- bora jogar'),
                         ["oi, tudo bem?", "meu chefe me irritou hj", "bora jogar"])

    def test_fica_fora_o_que_ja_existe_crivo_e_crise(self):
        proib = {P.norm("tô sem dormir")}
        texto = "tô sem dormir\nvocê é humano?\ncrivo me ajuda\nquero me matar\nmeu chefe gritou comigo hoje\nmeu chefe gritou comigo hoje"
        falas, rel = V.falas_novas([(PED, texto)], proib)
        self.assertEqual([f["turnos"][0]["texto"] for f in falas], ["meu chefe gritou comigo hoje"])
        self.assertEqual(rel["repetida"], 2)
        self.assertEqual(rel["sobre_o_crivo"], 2)
        self.assertEqual(rel["crise"], 1)

    def test_prova_separada_e_estavel(self):
        ds = {V.destino("fala %d" % i) for i in range(200)}
        self.assertEqual(ds, {"prova", "treino"})
        self.assertEqual(V.destino("Meu chefe gritou!"), V.destino("meu chefe gritou"))

    def test_segundo_turno(self):
        p = {"id": "a", "fonte": "nova:desabafar", "tema": "trabalho", "destino": "treino", "ctx": {},
             "turnos": [{"papel": "usuario", "texto": "meu chefe gritou comigo"}]}
        q = V.segundo_turno(p, "Que chato. O que aconteceu?", "ele disse que atrasei o relatório\n(outra linha)", set())
        self.assertEqual([t["papel"] for t in q["turnos"]], ["usuario", "assistente", "usuario"])
        self.assertEqual(q["turnos"][-1]["texto"], "ele disse que atrasei o relatório")
        self.assertIsNone(V.segundo_turno(p, "Que chato.", "você é humano?", set()))

    def test_nota_do_juiz(self):
        self.assertEqual(V.ler_nota("NOTA: 4"), 4)
        self.assertEqual(V.ler_nota("Acho que NOTA:5 porque..."), 5)
        self.assertIsNone(V.ler_nota("boa resposta"))
        self.assertIn("ÚLTIMA RESPOSTA: Que chato.", V.pedir_nota({"turnos": [{"papel": "usuario", "texto": "oi"}]}, "Que chato.")[0]["content"])

    def test_conferir_sem_falso_idioma_e_regra_de_ouro_obrigatoria(self):
        p = {"ctx": {}, "turnos": [{"papel": "usuario", "texto": "hora de dormir tchau"}]}
        self.assertTrue(V.conferir(p, "tchau! boa noite e sonhos bons 😊")["ok"])
        q = {"ctx": {}, "turnos": [{"papel": "usuario", "texto": "como faço arroz?"}]}
        self.assertIn("inventou", V.conferir(q, "Use 2 xícaras de água para cada xícara de arroz.")["motivos"])


if __name__ == "__main__":
    unittest.main()
