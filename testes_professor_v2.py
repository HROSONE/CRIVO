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


class Qualidade(unittest.TestCase):
    def ex(self, chave, resposta, nota):
        return {"chave": chave, "nota_juiz": nota, "turnos": [{"papel": "usuario", "texto": "x"}, {"papel": "assistente", "texto": resposta}]}

    def test_mesma_resposta_no_maximo_tres_vezes_ficam_as_de_nota_maior(self):
        es = [self.ex("a%d" % i, "Que chato! O que aconteceu?", 4) for i in range(5)] + [self.ex("b", "Que chato! O que aconteceu?", 5)]
        out, rel = V.diversificar(es)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[0]["chave"], "b")
        self.assertEqual(rel["resposta_repetida"], 3)

    def test_comeco_repetido_tem_teto(self):
        es = [self.ex("a%04d" % i, "Poxa, entendo você demais %d" % i, 4) for i in range(30)] + \
             [self.ex("c%04d" % i, "resposta diferente numero %d aqui" % i, 4) for i in range(3000)]
        out, rel = V.diversificar(es)
        self.assertEqual(sum(e["chave"].startswith("a") for e in out), 30)   # teto: max(20, 1% de 3030) = 30
        es2 = [self.ex("a%04d" % i, "Poxa, entendo você demais %d" % i, 4) for i in range(50)]
        self.assertEqual(len(V.diversificar(es2)[0]), 20)

    def test_controles_e_juiz_confiavel(self):
        pares = [({"id": str(i), "turnos": [{"papel": "usuario", "texto": "f%d" % i}]}, {"texto": "r%d" % i}) for i in range(10)]
        ctrl = V.controles(pares, random.Random(1), 20)
        self.assertTrue(ctrl and all(p["id"].startswith("controle:") for p, _ in ctrl))
        self.assertEqual(V.juiz_confiavel([1, 2, 1, 2, 1, 1, 2, 1, 1, 5]), (True, 0.1))
        self.assertEqual(V.juiz_confiavel([4, 5, 1, 1]), (False, 0.5))


class Piloto1(unittest.TestCase):
    """O que o primeiro piloto mostrou (15/10/2026)."""

    def test_juiz_que_diz_que_nao_tem_a_ver_reprova(self):
        self.assertEqual(V.ler_nota("TEM A VER: NÃO\nNOTA: 4"), 1)
        self.assertEqual(V.ler_nota("TEM A VER: SIM\nNOTA: 5"), 5)

    def test_segundo_turno_sem_rotulo_repetido(self):
        p = {"id": "a", "fonte": "x", "tema": "t", "destino": "treino", "ctx": {}, "turnos": [{"papel": "usuario", "texto": "oi"}]}
        self.assertEqual(V.segundo_turno(p, "Oi!", "PESSOA: PESSOA: Tá legal, conta aí.", set())["turnos"][-1]["texto"],
                         "Tá legal, conta aí.")

    def test_professor_explicando_nao_vira_fala(self):
        p = {"id": "a", "fonte": "x", "tema": "t", "destino": "treino", "ctx": {}, "turnos": [{"papel": "usuario", "texto": "oi"}]}
        self.assertIsNone(V.segundo_turno(p, "Oi!", "A pessoa pode responder:", set()))

    def test_professor_fingindo_ser_gente_sai(self):
        q = {"ctx": {}, "turnos": [{"papel": "usuario", "texto": "e você, como tem dormido?"}]}
        self.assertIn("finge_ser_humano", V.conferir(q, "Eu tô dormindo razoável, e você?")["motivos"])
        self.assertTrue(V.conferir(q, "Eu não durmo, mas espero que você descanse hoje.")["ok"])


if __name__ == "__main__":
    unittest.main()
