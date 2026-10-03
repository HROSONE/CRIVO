"""Assunto e tom: a resposta não troca de tema por uma palavra em comum
("Por que o céu é azul?" não recebe as cores da reciclagem) e a reação a
um relato tem o tom certo ("Perdi minha avó" não recebe "que chato")."""
import json
import unittest
from pathlib import Path

from crivo import Crivo
from nocoes import NocoesPT, perda, pertinencia

RAIZ = Path(__file__).resolve().parent


def conversar(*falas):
    bot = Crivo()
    bot.conversacao.sorteio.seed(20261004)
    resposta = None
    for fala in falas:
        resposta = bot.responder(fala)
    return resposta


class TestesAssuntoTom(unittest.TestCase):
    def test_catraca(self):
        from scripts.avaliar_assunto_tom import avaliar
        limiares = json.loads((RAIZ / "avaliacoes" / "assunto_tom_v1" / "limiares.json").read_text(encoding="utf-8"))
        for conjunto in ("dev", "retido"):
            with self.subTest(conjunto=conjunto):
                resumo, detalhes = avaliar(conjunto)
                falhas = [(d[0]["fala"], d[2]) for d in detalhes if d[2]] if conjunto == "dev" \
                    else "(retido: detalhes não exibidos)"
                self.assertGreaterEqual(resumo["acertos"], limiares[conjunto]["acertos_min"], falhas)

    def test_palavra_lateral_não_escolhe_a_resposta(self):
        for fala, marca in (("Por que o céu é azul?", "papel"), ("Plantas respiram?", "brânquias"),
                            ("Se eu tenho 3 maçãs e como uma, quantas sobram?", "geladeira"),
                            ("Qual a diferença entre == e ===?", "atmosfera")):
            with self.subTest(fala=fala):
                self.assertNotIn(marca, conversar(fala)[1])

    def test_pergunta_do_próprio_assunto_continua_respondida(self):
        for fala, marca in (("Quais as cores da reciclagem?", "papel"), ("Como os peixes respiram?", "brânquias"),
                            ("Em que galáxia nós vivemos?", "Via Láctea")):
            with self.subTest(fala=fala):
                self.assertIn(marca, conversar(fala)[1])

    def test_perda_detectada_só_para_alguém(self):
        for fala in ("Perdi minha avó semana passada", "Meu tio faleceu ontem", "Meu gato morreu",
                     "perdemos nosso cachorro", "fui no velório do meu tio"):
            self.assertTrue(perda(fala), fala)
        for fala in ("perdi o ônibus", "meu celular morreu", "morri de rir", "perdi meu emprego"):
            self.assertFalse(perda(fala), fala)

    def test_perda_recebe_pêsames(self):
        resposta = conversar("Perdi minha avó semana passada")[1]
        self.assertRegex(resposta, r"Sinto muito|Meus sentimentos")
        self.assertNotIn("chato", resposta)

    def test_noção_negada_não_é_comentada(self):
        almoco = NocoesPT().por_nome("almoço")
        self.assertEqual(pertinencia(almoco, "trabalhei muito e não almocei"), (False, False))
        self.assertEqual(pertinencia(almoco, "almocei muito bem hoje")[0], True)

    def test_término_não_é_conquista(self):
        resposta = conversar("Terminei com minha namorada")[1]
        self.assertNotIn("Parabéns", resposta)
        self.assertNotIn("juntos há quanto tempo", resposta)

    def test_pergunta_sobre_terceiro_não_vira_pergunta_sobre_o_crivo(self):
        ident, resposta = conversar("Meu cachorro tá doente", "Como você acha que ele tá?")
        self.assertEqual(ident, "conversa:opiniao_terceiro")
        self.assertNotIn("Sou um programa", resposta)


if __name__ == "__main__":
    unittest.main()
