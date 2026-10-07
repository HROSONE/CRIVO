"""Geração ancorada (geracao_ancorada.py): o CRIVO escolhe a ficha, a busca
escolhe o fato e o Transformer escreve a resposta só a partir dele."""
import unittest

from geracao_ancorada import (aprovada_pela_guarda, comeco_torto, numero_fora_de_lugar, polaridade_inventada,
                              quem_sem_nome, repete_palavra, troca_de_palavra, preserva_evidencia)

try:
    import numpy  # noqa: F401
    TEM_NUMPY = True
except ImportError:
    TEM_NUMPY = False


class Guarda(unittest.TestCase):
    def test_omissao_de_valor_ou_negacao_rejeita_a_resposta(self):
        fato = "O tratamento não cura a doença e dura 30 dias."
        self.assertTrue(preserva_evidencia(fato, [fato]))
        self.assertFalse(preserva_evidencia("O tratamento cura a doença e dura 30 dias.", [fato]))
        self.assertFalse(preserva_evidencia("O tratamento não cura a doença.", [fato]))

    def test_siglas_curtas_tambem_sao_conteudo(self):
        fato = "O DNA armazena informações genéticas. O RNA participa da síntese de proteínas."
        self.assertTrue(troca_de_palavra("O RNA armazena informações genéticas.", fato))
        self.assertFalse(troca_de_palavra("O DNA armazena informações genéticas.", fato))

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

    def test_recusa_nao_e_promovida_so_por_confianca_da_busca(self):
        from crivo import Crivo
        bot = Crivo()
        gerada = bot.responder("Quais línguas se falam na Suíça?")
        controle = self.perguntar("Quais línguas se falam na Suíça?", ligada=False)
        self.assertEqual(gerada, controle)
        self.assertFalse(bot.ultima_geracao["usada"])
        self.assertEqual(bot.ultima_geracao["motivo"], "sem_resposta_verificada")

    def test_ligada_por_padrao_com_controle_explicito(self):
        from crivo import Crivo
        self.assertTrue(Crivo().usar_geracao)
        ident, _ = self.perguntar("Quais línguas se falam na Suíça?", ligada=False)
        self.assertFalse(ident.startswith("geracao:"))

    def test_sim_ou_nao_fica_de_fora(self):
        ident, _ = self.perguntar("A Venezuela tem muito petróleo?")
        self.assertFalse(ident.startswith("geracao:"))

    def test_quem_foi_continua_com_a_identidade(self):
        _, resposta = self.perguntar("Quem foi Pelé?")
        self.assertIn("futebol", resposta)

    def test_web_e_crivo_usam_o_mesmo_padrao(self):
        from web_core import responder_web
        self.assertEqual(responder_web({"message": "O que é DNA?"})["id"], "conhecimento:dna")
        r = responder_web({"message": "O que é DNA?"})
        self.assertEqual(r["mechanism"], "geracao_ancorada", r)
        self.assertTrue(r["generation"]["usada"])

    def test_fidelidade_nao_basta_quando_o_fato_nao_responde(self):
        from web_core import responder_web
        r = responder_web({"message": "Por que uma geada que destrói parte da safra de café faz o preço subir?"})
        self.assertFalse(r["generation"]["usada"])
        self.assertNotIn("cafeína", r["response"])
        self.assertEqual(r["generation"]["motivo"], "resposta_incerta")

    def test_replay_resumo_e_fontes_usam_os_fatos_do_turno(self):
        from web_core import responder_web
        r = responder_web({"message": "Resuma isso", "history": ["O que é DNA?"]})
        self.assertTrue(r["generation"]["usada"], r)
        self.assertEqual(r["generation"]["modo"], "composicao")
        self.assertIn("genéticas", r["response"])
        f = responder_web({"message": "Qual a fonte?", "history": ["O que é DNA?", "Resuma isso"]})
        self.assertFalse(f["generation"]["usada"])
        self.assertIn("http", f["response"])

    def test_comparacao_mantem_os_dois_assuntos_e_fontes(self):
        from web_core import responder_web
        r = responder_web({"message": "Qual a diferença entre DNA e RNA?"})
        self.assertTrue(r["generation"]["usada"], r)
        self.assertIn("dupla hélice", r["response"])
        self.assertIn("única fita", r["response"])
        self.assertEqual({e["assunto"] for e in r["generation"]["evidencias"]}, {"dna", "rna"})

    def test_resumo_da_comparacao_e_fontes_mantem_ambos_os_assuntos(self):
        from web_core import responder_web
        perguntas = ["Qual a diferença entre DNA e RNA?", "Resuma isso"]
        r = responder_web({"message": perguntas[1], "history": perguntas[:1]})
        self.assertTrue(r["generation"]["usada"], r)
        self.assertIn("DNA", r["response"])
        self.assertIn("RNA", r["response"])
        f = responder_web({"message": "Qual a fonte?", "history": perguntas})
        self.assertFalse(f["generation"]["usada"])
        self.assertIn("http", f["response"])
        self.assertIn("DNA", f["response"])
        self.assertIn("RNA", f["response"])

    def test_diagnostico_desligado_e_modelo_ausente(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        from web_core import responder_web
        r = responder_web({"message": "O que é DNA?"}, usar_geracao=False)
        self.assertEqual(r["generation"]["motivo"], "desligada")
        with patch("geracao_ancorada.geracao", return_value=SimpleNamespace(disponivel=False, motivo="sem pesos")):
            r = responder_web({"message": "O que é DNA?"})
        self.assertEqual(r["generation"]["motivo"], "modelo_indisponivel")
        self.assertIn("genéticas", r["response"])

    def test_registro_preserva_analise_e_estado_do_turno(self):
        from crivo import Crivo
        bot = Crivo()
        ident, resposta = bot.responder("O que é DNA?")
        self.assertTrue(bot.ultima_geracao["usada"])
        self.assertEqual(bot.ultimo_turno["id"], ident)
        self.assertEqual(bot.conversacao.ultima_resposta_texto, resposta)
        self.assertEqual(bot.contexto_textual.texto, resposta)
        controle = Crivo(usar_geracao=False)
        controle.responder("O que é DNA?")
        for campo, valor in controle.historico[-1].items():
            if campo not in ("id", "mecanismo"):
                self.assertEqual(bot.historico[-1][campo], valor)


if __name__ == "__main__":
    unittest.main()
