"""Voz própria: forma de conversa sem acrescentar fatos.

A catraca usa o teste congelado avaliacoes/voz_v1 (respostas do tutor escritas
antes do treino, com assuntos disjuntos dos dados de treino).
"""
import json
import unittest
from pathlib import Path

import voz
from crivo import Crivo
from web_core import responder_web

RAIZ = Path(__file__).resolve().parent


class GuardaDeFidelidade(unittest.TestCase):
    def test_palavra_nova_e_detectada(self):
        fontes = ["Fotossíntese é o processo que usa energia luminosa para produzir matéria orgânica."]
        self.assertEqual(voz.palavras_inventadas("Na prática, fotossíntese usa energia luminosa.", fontes), [])
        self.assertIn("clor", voz.palavras_inventadas("Fotossíntese usa clorofila e energia.", fontes))

    def test_sem_pesos_fica_desligada(self):
        decisor = voz.ModeloDecisoes("/caminho/que/nao/existe")
        self.assertFalse(decisor.ativo)
        bot = Crivo()
        item = bot.compositor.itens["mundo_fotossintese"]
        self.assertIsNone(voz.realizar("O que é fotossíntese?", item, [0, 1], decisor=decisor))


class FormaDaVoz(unittest.TestCase):
    def itens(self):
        return Crivo().compositor.itens

    def test_genero_e_numero_do_nome(self):
        itens = self.itens()
        self.assertEqual(voz._genero_numero(itens["mundo_grandes_navegacoes"]), ("f", True))
        self.assertEqual(voz._genero_numero(itens["mundo_fotossintese"])[0], "f")
        self.assertEqual(voz._artigo(itens["mundo_neutrino"], "O que é um neutrino?"), "o")
        self.assertEqual(voz._pronome(itens["mundo_marie_curie"]), "Ela")
        self.assertEqual(voz._pronome(itens["mundo_albert_einstein"]), "Ele")

    def test_pronome_nao_entra_antes_de_verbo_impessoal(self):
        self.assertFalse(voz._comeca_com_verbo("Existem 64 códons para 20 aminoácidos."))
        self.assertTrue(voz._comeca_com_verbo("Fundou a Academia, em Atenas."))

    def test_sigla_e_nome_proprio_nao_viram_minuscula(self):
        textos = ["Copérnico propôs o modelo heliocêntrico; Galileu e Newton deram base.", "Por Copérnico."]
        self.assertTrue(voz._minuscula("Copérnico propôs o modelo.", textos).startswith("Copérnico"))
        self.assertTrue(voz._minuscula("DNA guarda informação.", []).startswith("DNA"))
        self.assertTrue(voz._minuscula("A origem dos anéis.", []).startswith("a origem"))


class VozNoChat(unittest.TestCase):
    def test_composicao_pura_ganha_voz(self):
        r = responder_web({"message": "O que é fotossíntese?"})
        self.assertEqual(r.get("voice"), "voz_propria")
        self.assertNotIn("Além disso", r["response"])
        self.assertIn("energia luminosa", r["response"])

    def test_aspecto_nao_ganha_sujeito_nem_limite_alheio(self):
        r = responder_web({"message": "Como funciona a fotossíntese?"})
        self.assertFalse(r["response"].startswith(("Um ", "Uma ")))
        r = responder_web({"message": "Como se formou Júpiter?"})
        self.assertNotIn("superfície sólida", r["response"])

    def test_comparacao_e_recusa_ficam_como_estao(self):
        r = responder_web({"message": "Qual a diferença entre vírus e bactéria?"})
        self.assertNotEqual(r.get("voice"), "voz_propria")
        r = responder_web({"message": "qual a senha do wifi daqui"})
        self.assertNotEqual(r.get("voice"), "voz_propria")

    def test_sem_voz_o_texto_de_sempre_volta(self):
        # O texto literal anterior pertence ao compositor. Desativar a voz
        # não desativa o gerador, que tem uma realização textual própria.
        bot = Crivo(usar_geracao=False)
        bot.usar_voz = False
        _, resposta = bot.responder("O que é fotossíntese?")
        self.assertIn("Além disso", resposta)

    def test_sem_voz_preserva_os_fatos_com_ambos_os_escritores(self):
        for geracao in (False, True):
            with self.subTest(geracao=geracao):
                bot = Crivo(usar_geracao=geracao)
                bot.usar_voz = False
                _, resposta = bot.responder("O que é fotossíntese?")
                for evidencia in ("energia luminosa", "dióxido de carbono", "liberação de oxigênio"):
                    self.assertIn(evidencia, resposta)
                self.assertIsNone(bot.historico[-1].get('voz'))
                self.assertEqual(bot.contexto_textual.temas, ('mundo_fotossintese',))
                if not geracao:
                    self.assertFalse(bot.ultima_geracao['usada'])


class OfertasCumpridas(unittest.TestCase):
    def test_sim_depois_da_oferta_generica_continua(self):
        r = responder_web({"message": "sim", "history": ["O que é inflação?"]})
        self.assertEqual(r["id"], "escrita:continuacao")
        self.assertIn("Plano Real", r["response"])

    def test_sim_depois_da_ligacao_responde_a_relacao_sem_repetir_a_oferta(self):
        r = responder_web({"message": "sim", "history": ["O que é neurônio?"]})
        self.assertEqual(r["id"], "escrita:relacao")
        self.assertIn("sinapses", r["response"])
        self.assertNotIn("Se quiser", r["response"])

    def test_oferta_vale_so_para_a_fala_seguinte(self):
        # A oferta sobre inflação foi substituída pela da resposta sobre DNA.
        r = responder_web({"message": "sim", "history": ["O que é inflação?", "O que é DNA?"]})
        self.assertNotIn("Plano Real", r["response"])
        r = responder_web({"message": "sim", "history": ["O que é inflação?", "Oi"]})
        self.assertNotIn("Plano Real", r["response"])

    def test_oferta_especifica_vem_do_acervo(self):
        self.assertEqual(voz._nome_proprio_inicial("O Código de Hamurábi, da Babilônia, é antigo."),
                         "o Código de Hamurábi")
        self.assertIsNone(voz._nome_proprio_inicial("O Brasil viveu hiperinflação."))


class Catraca(unittest.TestCase):
    def test_tutor_e_teste_congelado_sao_disjuntos(self):
        teste = json.loads((RAIZ / "avaliacoes/voz_v1/teste.json").read_text(encoding="utf-8"))
        tutor = json.loads((RAIZ / "dados/voz_tutor.json").read_text(encoding="utf-8"))
        a = {x for c in teste["casos"] for x in c["assuntos"]}
        b = {x for c in tutor["casos"] for x in c["assuntos"]}
        self.assertFalse(a & b)

    def test_pesos_aprovados(self):
        self.assertTrue(voz.modelo().ativo, voz.modelo().motivo)

    def test_teste_congelado(self):
        from scripts.avaliar_voz import avaliar
        resumo = avaliar(Crivo)["resumo"]
        self.assertEqual(resumo["fieis"], resumo["casos"], resumo)
        self.assertEqual(resumo["marcas_mecanicas"], 0, resumo)
        self.assertGreaterEqual(resumo["chrf_medio"], 87.0, resumo)


if __name__ == "__main__":
    unittest.main()
