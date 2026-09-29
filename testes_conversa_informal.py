"""Falas sociais, feedback e pedidos compostos; não medem compreensão universal."""
import unittest

from crivo import Crivo
from web_core import responder_web


class TestesConversaInformal(unittest.TestCase):
    def test_sequencia_da_captura(self):
        bot = Crivo()
        respostas = []
        for pergunta, esperado in (
            ("eae beleza?", "social:tudobem"),
            ("voce é um idiota", "social:critica"),
            ("você é muito burro", "social:critica"),
            ("não sabe de nada também", "social:critica"),
        ):
            ident, texto = bot.responder(pergunta)
            self.assertEqual(ident, esperado)
            self.assertNotIn("essa negação", texto)
            self.assertNotIn("Assuntos da base", texto)
            respostas.append(texto)
        self.assertNotEqual(respostas[1], respostas[2])
        self.assertNotEqual(respostas[2], respostas[3])

    def test_saudacoes_e_perguntas_informais(self):
        for q in ("E aí, beleza?", "Eaê, blz?", "eai tudo certo", "Oi, tudo bem?",
                  "Opa! Tudo bom?", "Bom dia, tudo bem com você?", "Salve, tranquilo?",
                  "Tudo certo por aí?", "Como cê tá?", "como vc está?", "de boa?"):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], "social:tudobem")

    def test_continua_o_contato_sem_buscar_fato(self):
        for q in ("tô bem", "estou bem também", "tudo certo", "de boa", "sim", "tô bem, e você?"):
            with self.subTest(q=q):
                bot = Crivo()
                bot.responder("eae beleza?")
                self.assertEqual(bot.responder(q)[0], "social:acolhimento")

    def test_variantes_de_critica_direta(self):
        for sujeito in ("Você", "vc", "tu", "Crivo"):
            for q in (sujeito + " é muito burro", sujeito + " não entende nada",
                      sujeito + " é um idiota", sujeito + " está confuso"):
                with self.subTest(q=q):
                    self.assertEqual(Crivo().responder(q)[0], "social:critica")

    def test_feedback_sobre_resposta_nao_declara_fato_falso(self):
        bot = Crivo()
        bot.responder("O que é DNA?")
        ident, texto = bot.responder("essa resposta está errada")
        self.assertEqual(ident, "social:critica")
        self.assertIn("O que é DNA?", texto)
        self.assertIn("trecho", texto)
        self.assertNotIn("DNA não", texto)
        self.assertIsNone(bot.ultima_resposta_mostrada)

    def test_feedback_de_falha_cita_somente_ultimo_pedido(self):
        bot = Crivo()
        bot.responder("O que é DNA?")
        bot.responder("zarquiflores desconhecidos")
        ident, texto = bot.responder("não foi isso que eu perguntei")
        self.assertEqual(ident, "social:critica")
        self.assertIn("zarquiflores desconhecidos", texto)
        self.assertNotIn("DNA", texto)
        bot.responder("oi")
        self.assertNotIn("zarquiflores", bot.responder("isso está errado")[1])

    def test_saudacao_composta_preserva_o_pedido(self):
        for q, esperado in (
            ("Oi, tudo bem? O que é DNA?", "conhecimento:dna"),
            ("eae beleza, o que é Andrômeda?", "conhecimento:andromeda"),
            ("Bom dia! Tudo certo? A Lua orbita a Terra?", "logica:orbita"),
            ("Oi, tudo bem? Escreva um texto sobre DNA", "escrita:texto"),
            ("valeu, o que é HTML?", "web_html"),
        ):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], esperado)

    def test_critica_seguida_de_pedido_prioriza_pedido(self):
        for q in ("você é burro. O que é DNA?", "isso está errado; o que é DNA?",
                  "não foi isso que eu pedi. Você pode explicar o que é DNA?"):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], "conhecimento:dna")
        self.assertEqual(Crivo().responder("Você é um idiota, mas a Lua orbita a Terra?")[0],
                         "logica:orbita")

    def test_feedback_e_vocativos_fora_da_captura(self):
        for q in ("Não entendeu minha pergunta", "você não entendeu meu pedido",
                  "Isso não faz sentido", "não gostei da resposta", "que resposta ruim"):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], "social:critica")
        for q in ("Eae mano beleza?", "Oi meu amigo, tudo bem?", "Tudo certo, cara?"):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], "social:tudobem")
        self.assertEqual(Crivo().responder("Eae mano beleza. O que é RNA?")[0],
                         "conhecimento:rna")

    def test_reformulacao_explicita_e_comprovacao(self):
        for q, esperado in (
            ("não, quero saber o que é DNA", "conhecimento:dna"),
            ("quis dizer o que é RNA", "conhecimento:rna"),
            ("minha pergunta é: a Lua orbita a Terra?", "logica:orbita"),
        ):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], esperado)

    def test_palavras_sociais_em_conteudo_nao_roubam_a_intencao(self):
        for q in ("O que significa idiota?", "O que é beleza?", "Um burro é um mamífero?",
                  "A Lua não sabe de nada?", "Meu amigo é um idiota",
                  "Você acha que o burro é um mamífero?",
                  "Escreva um programa que mostre 'tudo bem'",
                  "Não quero saber o que é DNA", "Não sei se DNA é uma molécula"):
            with self.subTest(q=q):
                ident, _ = Crivo().responder(q)
                self.assertNotIn(ident, ("social:critica", "social:tudobem", "social:elogio"))

    def test_feedback_nao_escolhe_opcao_de_esclarecimento(self):
        bot = Crivo()
        self.assertEqual(bot.responder("planta")[0], "duvida")
        self.assertEqual(bot.responder("não foi isso que eu pedi")[0], "social:critica")
        self.assertIsNone(bot.esclarecimento)
        self.assertEqual(bot.responder("2")[0], "duvida")

    def test_elogio_e_convite(self):
        for q in ("mandou bem", "boa resposta", "vc é inteligente", "gostei da resposta"):
            self.assertEqual(Crivo().responder(q)[0], "social:elogio")
        for q in ("vamos conversar", "bora bater um papo", "quero conversar com você"):
            self.assertEqual(Crivo().responder(q)[0], "social:conversar")

    def test_api_replay_e_isolamento_do_feedback(self):
        dado = responder_web({"message": "isso está errado", "history": ["O que é DNA?"]})
        self.assertEqual(dado["id"], "social:critica")
        self.assertEqual(dado["mechanism"], "conversa_assistente")
        self.assertFalse(dado["has_proof"])
        self.assertIn("DNA", dado["response"])
        isolado = responder_web({"message": "isso está errado"})
        self.assertNotIn("DNA", isolado["response"])
        self.assertEqual(responder_web({"message": "tô bem", "history": ["eae beleza?"]})["id"],
                         "social:acolhimento")


if __name__ == "__main__":
    unittest.main()
