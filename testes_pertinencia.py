"""Pertinência da reação a um relato: o comentário de senso comum combina
com o que aconteceu ("gato derrubou o copo", não "gato sumiu"), a pergunta
vai para quem viveu o fato e o eco fala com "você". Vale com e sem NumPy."""
import json
import unittest
from pathlib import Path

from crivo import Crivo
from nocoes import NocoesPT, pertinencia

RAIZ = Path(__file__).resolve().parent


def responder(fala):
    bot = Crivo()
    bot.conversacao.sorteio.seed(20261003)
    return bot.responder(fala)[1]


class TestesPertinencia(unittest.TestCase):
    def test_catraca(self):
        from scripts.avaliar_pertinencia import avaliar
        limiares = json.loads((RAIZ / "avaliacoes" / "pertinencia_v1" / "limiares.json").read_text(encoding="utf-8"))
        for conjunto in ("dev", "retido"):
            with self.subTest(conjunto=conjunto):
                resumo, detalhes = avaliar(conjunto)
                falhas = [d for d in detalhes if d[2]] if conjunto == "dev" else "(retido: detalhes não exibidos)"
                self.assertGreaterEqual(resumo["acertos"], limiares[conjunto]["acertos_min"], falhas)

    def test_noção_só_quando_o_acontecimento_combina(self):
        gato = NocoesPT().por_nome("gato")
        self.assertEqual(pertinencia(gato, "meu gato derrubou um copo"), (True, True))
        self.assertEqual(pertinencia(gato, "meu gato sumiu"), (False, False))
        chuva = NocoesPT().por_nome("chuva")
        self.assertEqual(pertinencia(chuva, "hoje choveu o dia todo"), (True, True))

    def test_cena_vista_de_fora_não_traz_noção(self):
        resposta = responder("vi uma menina abrindo o guarda-chuva no ponto de ônibus")
        self.assertNotIn("costuma", resposta)
        self.assertNotIn("chegou atrasado", resposta)

    def test_pergunta_vai_para_quem_viveu(self):
        resposta = responder("meu avô plantou uma mangueira no quintal")
        self.assertNotIn("você plantou", resposta)

    def test_cirurgia_é_saúde_e_ainda_vai_acontecer(self):
        resposta = responder("meu pai vai fazer uma cirurgia amanhã")
        self.assertNotIn("histórias antigas", resposta)
        self.assertNotIn("melhore logo", resposta)
        self.assertTrue(any(t in resposta for t in ("dê tudo certo", "corra tudo bem")), resposta)

    def test_eco_converte_primeira_pessoa(self):
        resposta = responder("comi pizza ontem")
        self.assertNotIn("comi pizza", resposta)

    def test_controle_noção_que_combina_continua(self):
        self.assertIn("costuma", responder("meu gato derrubou um copo"))
        self.assertIn("latir", responder("meu cachorro latiu a noite toda"))


if __name__ == "__main__":
    unittest.main()
