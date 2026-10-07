"""Geração ancorada (geracao_ancorada.py): o CRIVO escolhe a ficha, a busca
escolhe o fato e o Transformer escreve a resposta só a partir dele."""
import unittest

from geracao_ancorada import (aprovada_pela_guarda, comeco_torto, numero_fora_de_lugar, polaridade_inventada,
                              quem_sem_nome, repete_palavra, troca_de_palavra)

try:
    import numpy  # noqa: F401
    TEM_NUMPY = True
except ImportError:
    TEM_NUMPY = False


class Guarda(unittest.TestCase):
    def test_numeros_trocados(self):
        fato = "O Pará tem cerca de 1,25 milhão de km² e cerca de 8,1 milhões de habitantes."
        self.assertTrue(numero_fora_de_lugar("O Pará tem cerca de 8,1 milhões de km².", fato))
        self.assertFalse(numero_fora_de_lugar("O Pará tem cerca de 1,25 milhão de km².", fato))

    def test_palavra_trocada_muda_o_sentido(self):
        fato = "Intolerância à lactose é a dificuldade de digerir a lactose, por falta da enzima lactase."
        self.assertTrue(troca_de_palavra("Intolerância à lactose é a dificuldade de digerir a lactase.", fato))
        self.assertFalse(troca_de_palavra("Intolerância à lactose é a dificuldade de digerir a lactose.", fato))

    def test_quem_exige_nome(self):
        p = "Quem foi o primeiro homem a pisar na Lua?"
        self.assertTrue(quem_sem_nome("Foi o primeiro ser humano a pisar na Lua.", p))
        self.assertFalse(quem_sem_nome("Neil Armstrong foi o primeiro ser humano a pisar na Lua.", p))
        self.assertTrue(comeco_torto("Foi o primeiro ser humano a pisar na Lua.", p))

    def test_comeco_de_pergunta_ou_repetido(self):
        self.assertTrue(comeco_torto("Quem tem 90 minutos, divididos em dois tempos.", "Quanto dura um jogo?"))
        self.assertTrue(comeco_torto("Porque, porque a Suíça é neutra.", "Por que a Suíça é neutra?"))
        self.assertFalse(comeco_torto("A capital da Suíça é Berna.", "Qual a capital da Suíça?"))

    def test_polaridade_e_repeticao(self):
        self.assertTrue(polaridade_inventada("Sim. A Declaração tem 30 artigos."))
        self.assertTrue(repete_palavra("direitos civis, políticos e políticos, políticos.", "direitos civis e políticos"))

    def test_guarda_completa(self):
        fatos = ["A Suíça tem quatro línguas oficiais: alemão, francês, italiano e romanche."]
        p = "Quais línguas se falam na Suíça?"
        self.assertTrue(aprovada_pela_guarda(fatos[0], fatos, p))
        self.assertFalse(aprovada_pela_guarda("Quais línguas se falam na Suíça?", fatos, p))
        self.assertFalse(aprovada_pela_guarda("A Suíça tem cinco línguas oficiais.", fatos, p))


@unittest.skipUnless(TEM_NUMPY, "o Transformer roda em NumPy")
class Transformer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from geracao_ancorada import geracao
        cls.g = geracao()

    def test_aprovada_e_sem_pesos_externos(self):
        self.assertTrue(self.g.disponivel, self.g.motivo)
        self.assertTrue(self.g.meta["controle"]["aprovado"])

    def test_escreve_a_partir_do_fato(self):
        r = self.g.gerar("Qual é a capital da Suíça?", ["A capital da Suíça é Berna."])
        self.assertIsNotNone(r)
        self.assertIn("Berna", r)


@unittest.skipUnless(TEM_NUMPY, "o Transformer roda em NumPy")
class NoCrivo(unittest.TestCase):
    def perguntar(self, texto, ligada=True):
        from crivo import Crivo
        bot = Crivo()
        bot.usar_geracao = ligada
        return bot.responder(texto)

    def test_responde_pergunta_que_antes_era_recusada(self):
        ident, resposta = self.perguntar("Quais línguas se falam na Suíça?")
        self.assertTrue(ident.startswith("geracao:"), (ident, resposta))
        self.assertIn("romanche", resposta)

    def test_desligada_por_padrao(self):
        from crivo import Crivo
        self.assertFalse(Crivo().usar_geracao)
        ident, _ = self.perguntar("Quais línguas se falam na Suíça?", ligada=False)
        self.assertFalse(ident.startswith("geracao:"))

    def test_sim_ou_nao_fica_de_fora(self):
        ident, _ = self.perguntar("A Venezuela tem muito petróleo?")
        self.assertFalse(ident.startswith("geracao:"))

    def test_quem_foi_continua_com_a_identidade(self):
        _, resposta = self.perguntar("Quem foi Pelé?")
        self.assertIn("futebol", resposta)

    def test_site_usa_a_geracao(self):
        from web_core import responder_web
        r = responder_web({"message": "Quais línguas se falam na Suíça?"})
        self.assertTrue(r["id"].startswith("geracao:"), r)


if __name__ == "__main__":
    unittest.main()
