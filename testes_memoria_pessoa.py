"""Memória do que a pessoa conta de si: nome (com correção), idade, trabalho, origem e time.

Teste às cegas de 21/10/2026 (avaliacoes/cegas_agentes_20261021/memoria.json): "não é Renata, é
Regina" seguido de "quem sou eu?" dava "Renata"; "quantos anos eu tenho?" virava ano bissexto. As
frases daqui são outras: as cegas medem, estas protegem."""
import unittest

from conversa_cotidiana import _apresentacao
from web_core import responder_web


def conversar(*falas):
    h, respostas = [], []
    for fala in falas:
        r = responder_web({"message": fala, "history": h})
        h.append(fala)
        respostas.append((r["id"], r["response"]))
    return respostas


class Nome(unittest.TestCase):
    def test_formas_de_dizer_o_nome(self):
        for fala, nome in (("meu nome e Otavio", "Otavio"), ("meu nomi eh Clara", "Clara"), ("sou o Tadeu", "Tadeu"),
                           ("eu me chamo Lia", "Lia"), ("Meu nome é Ana, e o seu?", "Ana"),
                           ("Boa noite, eu me chamo Dona Cida e queria uma ajuda", "Dona Cida")):
            with self.subTest(fala=fala):
                self.assertEqual(_apresentacao(fala), nome)

    def test_o_que_nao_e_nome(self):
        for fala in ("sou de Manaus", "sou estudante", "sou feliz", "é isso", "nao é verdade"):
            with self.subTest(fala=fala):
                self.assertIsNone(_apresentacao(fala))
        self.assertIsNone(_apresentacao("não é isso, é aquilo", "Ana"))
        self.assertIsNone(_apresentacao("na verdade é Bruno"))  # sem nome dito antes, não é correção

    def test_correcao_do_nome(self):
        for fala in ("não é Ana, é Joana", "nao, meu nome e Joana", "na verdade é Joana", "pera, errei, é Joana"):
            with self.subTest(fala=fala):
                r = conversar("Oi, meu nome é Ana", fala, "qual é o meu nome?")
                self.assertTrue(r[1][1].startswith("Ah, desculpa! Joana"), r[1])
                self.assertIn("Joana", r[2][1])
                self.assertNotIn("Ana.", r[2][1])


class FatosDaPessoa(unittest.TestCase):
    def test_lembra_o_que_foi_dito(self):
        for fala, pergunta, esperado in (("tenho 42 anos", "quantos anos eu tenho?", "42 anos"),
                                         ("eu trabalho como padeiro", "qual é o meu trabalho?", "padeiro"),
                                         ("sou de Manaus", "de onde eu sou?", "Manaus"),
                                         ("eu torço pro Bahia", "qual é o meu time?", "Bahia")):
            with self.subTest(fala=fala):
                ident, resposta = conversar(fala, pergunta)[1]
                self.assertEqual(ident, "conversa:memoria")
                self.assertIn(esperado, resposta)

    def test_sem_o_fato_diz_que_nao_foi_contado(self):
        for pergunta in ("qual é a minha idade?", "de onde eu sou?", "qual é o meu trabalho?"):
            with self.subTest(pergunta=pergunta):
                ident, resposta = conversar(pergunta)[0]
                self.assertEqual(ident, "conversa:memoria")
                self.assertIn("ainda não me contou", resposta)

    def test_nao_confunde(self):
        self.assertIn("ainda não", conversar("tenho 3 anos de experiência", "quantos anos eu tenho?")[1][1])
        self.assertIn("ainda não", conversar("sou de boa", "de onde eu sou?")[1][1])

    def test_correcao_da_idade(self):
        r = conversar("tenho 20 anos", "na verdade tenho 21 anos", "quantos anos eu tenho?")
        self.assertIn("21 anos", r[1][1])
        self.assertIn("21 anos", r[2][1])
        r = conversar("Oi, meu nome é Ana e tenho 30 anos", "pera, errei, tenho 31", "qual minha idade?")
        self.assertIn("31 anos", r[2][1])


if __name__ == "__main__":
    unittest.main()
