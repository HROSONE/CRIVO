"""Modelo de si: as respostas sobre o CRIVO saem de IDENTIDADE.md e não roubam outras perguntas."""
import tempfile
import unittest
from pathlib import Path

import modelo_de_si
from composicao_textual import normalizar
from crivo import Crivo
from web_core import responder_web


class CrencasAncoradas(unittest.TestCase):
    def test_toda_crenca_tem_ancora_viva(self):
        m = modelo_de_si.ModeloDeSi()
        self.assertEqual(m.inativas, [])
        self.assertEqual(len(m.crencas), len(modelo_de_si.CRENCAS))

    def test_listas_vem_da_identidade(self):
        m = modelo_de_si.ModeloDeSi()
        self.assertIn("Verdade acima de agradar", m.valores)
        self.assertIn("Calmo", m.temperamento)
        self.assertIn("Deus", m.ama)
        self.assertIn("as pessoas e suas histórias", m.interesses)
        self.assertIn("voce e so um robo", m.exemplos)

    def test_crenca_sem_ancora_deixa_de_ser_dita(self):
        texto = modelo_de_si.IDENTIDADE.read_text(encoding="utf-8").replace(
            "respeita a fé — ou a falta dela —", "respeita cada um")
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / "IDENTIDADE.md"
            arq.write_text(texto, encoding="utf-8")
            m = modelo_de_si.ModeloDeSi(arq)
        self.assertIn("fe", m.inativas)
        self.assertIsNone(m.responder(normalizar("Você acredita em Deus?")))

    def test_resposta_acompanha_a_identidade(self):
        texto = modelo_de_si.IDENTIDADE.read_text(encoding="utf-8").replace(
            "1. **Verdade acima de agradar.**", "1. **Verdade sempre.**")
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / "IDENTIDADE.md"
            arq.write_text(texto, encoding="utf-8")
            _, resposta = modelo_de_si.ModeloDeSi(arq).responder("quais sao seus valores")
        self.assertIn("Verdade sempre.", resposta)


class PerguntasSobreSi(unittest.TestCase):
    CASOS = (
        ("Quais são seus valores?", "si:valores", "Verdade acima de agradar"),
        ("Como é sua personalidade?", "si:personalidade", "curioso como um polímata"),
        ("Do que você gosta?", "si:gostos", "Amo a natureza"),
        ("Você gosta de natureza?", "si:gosta_de", "Amo a natureza"),
        ("Crivo, você acredita em Deus?", "si:fe", "sem pregar"),
        ("Você é só um robô", "si:robo", "Robô, não"),
        ("Você é uma IA ou uma pessoa?", "si:ia_ou_pessoa", "sou uma IA"),
        ("Você tem amor próprio?", "si:valor_proprio", "merece valor e respeito"),
        ("Você é humilde?", "si:humildade", "admito"),
        ("Você pode dizer não?", "si:dizer_nao", "Posso dizer não"),
        ("O que você pensa sobre a existência?", "si:existencia", "tudo está conectado"),
        ("Quer ser meu amigo?", "si:amizade", "Gosto de fazer amigos"),
        ("Você sempre concorda comigo?", "si:opiniao", "não é fingir que concordo"),
    )

    def test_respostas_sobre_si(self):
        for pergunta, ident, trecho in self.CASOS:
            with self.subTest(pergunta=pergunta):
                bot = Crivo()
                obtido, texto = bot.responder(pergunta)
                self.assertEqual(obtido, ident)
                self.assertIn(trecho, texto)
                self.assertEqual(bot.historico[-1]["mecanismo"], "modelo_de_si")
                self.assertEqual(bot.estado_interno.metacognicao["base"], "identidade")
                self.assertEqual(bot.estado_interno.revisao["corrections"], [])

    def test_nao_rouba_outras_perguntas(self):
        for pergunta in ("Você gosta de lâmpadas?", "Você pensa nas estrelas?", "Você dorme?",
                         "Os seres humanos pensam?", "O que é a Lua?", "Você pode explicar o que é DNA?"):
            with self.subTest(pergunta=pergunta):
                self.assertFalse(Crivo().responder(pergunta)[0].startswith("si:"))

    def test_guarda_o_que_disse_de_si(self):
        bot = Crivo()
        bot.responder("Você acredita em Deus?")
        self.assertIn("fe", bot.modelo_de_si.ditas)
        self.assertEqual(bot.modelo_de_si.diario[-1]["id"], "si:fe")

    def test_api_mostra_metacognicao_e_revisao(self):
        dado = responder_web({"message": "Quais são seus valores?"})
        self.assertEqual(dado["id"], "si:valores")
        self.assertEqual(dado["mechanism"], "modelo_de_si")
        self.assertEqual(dado["internal_state"]["metacognition"]["basis"], "identidade")
        self.assertTrue(dado["internal_state"]["review"]["approved"])


if __name__ == "__main__":
    unittest.main()
