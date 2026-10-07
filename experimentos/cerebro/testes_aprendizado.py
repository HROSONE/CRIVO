"""Aprender com a conversa, curiosidade e consolidação (07/10/2026)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "scripts"))

from crivo import Crivo  # noqa: E402
from web_core import PedidoInvalido, responder_web  # noqa: E402


class Correcao(unittest.TestCase):
    def test_nao_e_isso_oferece_alternativas_e_a_escolha_vale_na_conversa(self):
        bot = Crivo()
        bot.usar_confianca = False
        bot.responder("Quando acabou a escravidão no Brasil?")
        ident, resposta = bot.responder("não é isso")
        self.assertEqual(ident, "aprendizado:opcoes")
        self.assertIn("1.", resposta)
        opcoes = bot.aprendizado.pendente["opcoes"]
        ident, resposta = bot.responder("1")
        self.assertEqual(ident, "aprendizado:correcao")
        # A mesma pergunta, de novo, usa o que foi aprendido.
        self.assertEqual(bot.responder("Quando acabou a escravidão no Brasil?")[0], "aprendizado:sessao")
        aprendido = bot.exportar_memoria()["aprendizados"][-1]
        self.assertEqual((aprendido["assunto"], aprendido["fato"], aprendido["sinal"]), opcoes[0] + (1,))

    def test_resposta_do_usuario_e_anotada_e_nao_vira_fato(self):
        bot = Crivo()
        bot.responder("Quem inventou o zorbix?")
        bot.responder("errado")
        ident, resposta = bot.responder("Foi o professor Zorb em 1990")
        self.assertEqual(ident, "aprendizado:anotado")
        self.assertIn("conferir", resposta)
        lacuna = bot.exportar_memoria()["lacunas"][-1]
        self.assertEqual(lacuna["resposta_usuario"], "Foi o professor Zorb em 1990")
        # Não aprendeu como fato: a pergunta continua sem resposta.
        self.assertNotEqual(bot.responder("Quem inventou o zorbix?")[0], "aprendizado:sessao")

    def test_confirmacao_positiva_e_guardada(self):
        bot = Crivo()
        bot.responder("Quem descobriu o Brasil?")
        self.assertEqual(bot.responder("isso mesmo")[0], "aprendizado:confirmado")
        self.assertEqual(bot.exportar_memoria()["aprendizados"][-1]["sinal"], 1)

    def test_negativo_sem_resposta_anterior_segue_o_turno_comum(self):
        self.assertFalse(Crivo().responder("não é isso")[0].startswith("aprendizado:"))


class Curiosidade(unittest.TestCase):
    def test_lacunas_e_convite_a_ensinar(self):
        bot = Crivo()
        for q in ("Quem inventou o zorbix?", "Quanto pesa um zorbax?", "Onde mora o quiblorf?"):
            ident, resposta = bot.responder(q)
        self.assertIn("me conte", resposta)
        ident, resposta = bot.responder("o que você não sabe?")
        self.assertEqual(ident, "aprendizado:lacunas")
        self.assertIn("zorbix", resposta)


class Memoria(unittest.TestCase):
    def test_aprendizado_viaja_na_memoria_do_navegador(self):
        memoria = {"aprendizados": [{"pergunta": "Qual é o maior país do mundo?", "assunto": "mundo_russia",
                                     "fato": 0, "sinal": 1}],
                   "lacunas": [{"pergunta": "Quem inventou o zorbix?"}]}
        r = responder_web({"message": "Qual é o maior país do mundo?", "memory": memoria})
        self.assertEqual(r["id"], "aprendizado:sessao")
        self.assertIn("Rússia", r["response"])
        self.assertEqual(r["memory"]["lacunas"][0]["pergunta"], "Quem inventou o zorbix?")

    def test_memoria_invalida_e_recusada(self):
        with self.assertRaises(PedidoInvalido):
            responder_web({"message": "oi", "memory": {"aprendizados": [{"pergunta": "x", "assunto": "y",
                                                                          "fato": "0", "sinal": 1}]}})


class Consolidacao(unittest.TestCase):
    def test_pares_e_lacunas_de_varias_conversas(self):
        from consolidar_aprendizados import consolidar
        m1 = {"aprendizados": [{"pergunta": "Qual é o maior país?", "assunto": "mundo_russia", "fato": 0, "sinal": 1}],
              "lacunas": [{"pergunta": "Quem inventou o zorbix?", "resposta_usuario": "Zorb"}]}
        m2 = {"aprendizados": [{"pergunta": "qual é o maior país?", "assunto": "mundo_russia", "fato": 0, "sinal": 1}],
              "lacunas": [{"pergunta": "Quem inventou o zorbix?"}]}
        d = consolidar([m1, m2])
        self.assertEqual(d["pares"][0]["saldo"], 2)
        self.assertEqual((d["lacunas"][0]["vezes"], d["lacunas"][0]["respostas_usuario"]), (2, ["Zorb"]))
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "a.json"
            caminho.write_text(json.dumps(d), encoding="utf-8")
            from consolidar_aprendizados import pares_positivos
            self.assertEqual(pares_positivos(caminho), [("Qual é o maior país?", "mundo_russia", 0)])


if __name__ == "__main__":
    unittest.main()
