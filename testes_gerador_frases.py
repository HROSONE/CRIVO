"""Gerador de frases: candidatas, verificador de fidelidade, pontuador
neural em NumPy (paridade com PyTorch e com a biblioteca tokenizers quando
estão instaladas) e a catraca de fluência."""
import json
import random
import unittest
from pathlib import Path

import gerador_frases as g
from presenca import Variacao

try:
    import numpy  # noqa: F401
except ImportError:
    numpy = None

RAIZ = Path(__file__).resolve().parent


def plano(**extra):
    base = dict(tom="neg", aberturas=("Poxa.", "Putz."), eco="você perdeu o ônibus", eco_na_abertura=True,
                nocao="Ônibus atrasado costuma bagunçar o horário de todo mundo.",
                perguntas=("Você chegou atrasado por causa disso?",), fala="hoje perdi o ônibus")
    base.update(extra)
    return g.Plano(**base)


class TestesVerificador(unittest.TestCase):
    def test_todas_as_candidatas_do_plano_sao_fieis(self):
        p = plano()
        candidatas = g.candidatos(p)
        self.assertGreater(len({f for _, f in candidatas}), 1)
        for texto, _ in candidatas:
            self.assertIsNone(g.verificar(texto, p), texto)

    def test_rejeita_fato_acrescentado_parte_perdida_negacao_e_reacao_repetida(self):
        p = plano()
        self.assertIn("acrescenta", g.verificar(
            "Poxa, você perdeu o ônibus e o carro quebrou. Você chegou atrasado por causa disso?", p))
        self.assertIn("perde", g.verificar("Poxa. Você chegou atrasado por causa disso?", p))
        self.assertIn("negação", g.verificar(
            "Poxa, você não perdeu o ônibus. Ônibus atrasado costuma bagunçar o horário de todo mundo. "
            "Você chegou atrasado por causa disso?", p))
        self.assertEqual(g.verificar("Que legal, você estudou! Que bom saber disso. O que mais aconteceu?",
                                     plano(tom="pos", eco="você estudou", nocao="", perguntas=())),
                         "reação repetida")

    def test_eco_em_voce_nao_conta_como_palavra_nova(self):
        self.assertEqual(g.palavras_novas("Boa, você fez um bolo! Você viu?", ["fiz um bolo e vi"]), [])

    def test_realizar_varia_a_estrutura_e_registra_o_uso(self):
        v = Variacao(random.Random(0))
        texto, forma = g.realizar(plano(), v)
        texto2, forma2 = g.realizar(plano(aberturas=("Puxa vida.",)), v, anterior=forma)
        self.assertNotEqual(forma, forma2)
        self.assertTrue(set(v.usadas) & {"Poxa.", "Putz."})

    def test_tempo_da_pergunta(self):
        self.assertFalse(g.tempo_compativel("vou comemorar com uma pizza", "Qual sabor você pediu?"))
        self.assertTrue(g.tempo_compativel("comi uma pizza", "Qual sabor você pediu?"))
        self.assertTrue(g.tempo_compativel("vou comemorar com uma pizza", "Qual sabor você vai pedir?"))

    def test_estrutura(self):
        self.assertEqual(g.estrutura("Poxa, você perdeu o ônibus. Ônibus atrasa. Chegou tarde?"), ("Ae", "N", "P"))
        self.assertEqual(g.estrutura("Você passou na prova? Parabéns! Era difícil?"), ("E?", "A", "P"))


@unittest.skipUnless(numpy is not None, "NumPy necessário")
class TestesPontuador(unittest.TestCase):
    def test_bpe_igual_ao_tokenizer_json(self):
        try:
            from tokenizers import Tokenizer
        except ImportError:
            self.skipTest("biblioteca tokenizers ausente")
        from pontuador_frases import pontuador
        ref = Tokenizer.from_file(str(RAIZ / "artefatos" / "linguagem_profunda" / "tokenizer.json"))
        for texto in ("Poxa, você perdeu o ônibus!", "Olá!! 123 ação... já\n  tchau 'oi' café-com-leite",
                      "São Paulo, 3,5 km; e-mail: a@b.com"):
            self.assertEqual(pontuador().bpe.codificar(texto), ref.encode(texto, add_special_tokens=False).ids)

    def test_numpy_reproduz_o_torch(self):
        try:
            import torch
            from linguagem_profunda import carregar
        except ImportError:
            self.skipTest("PyTorch ausente")
        from pontuador_frases import pontuador
        p = pontuador()
        modelo, _, _ = carregar(RAIZ / "artefatos" / "linguagem_profunda")
        ids = p.prefixo("hoje perdi o ônibus") + p.bpe.codificar("Poxa, que chato.")
        with torch.no_grad():
            ref = modelo(torch.tensor([ids]))[0][0].numpy()
        self.assertLess(float(abs(ref - p.logits(ids)).max()), 0.05)  # pesos em float16

    def test_catraca_de_fluencia(self):
        from scripts.avaliar_fluencia import avaliar
        limiares = json.loads((RAIZ / "avaliacoes" / "fluencia_v1" / "limiares.json").read_text(encoding="utf-8"))
        for conjunto in ("dev", "retido"):
            with self.subTest(conjunto=conjunto):
                resumo, _ = avaliar(conjunto)
                self.assertTrue(resumo.get("disponivel", True), resumo)
                self.assertGreaterEqual(resumo["acertos"], limiares[conjunto]["acertos_min"],
                                        "(detalhes só no dev)" if conjunto == "retido" else resumo)


if __name__ == "__main__":
    unittest.main()
