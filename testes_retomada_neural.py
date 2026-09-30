"""Retomadas por nomes variáveis, conservação de argumentos e replay HTTP.

Casos autorais registrados antes da correção; regressões de desenvolvimento,
não uma avaliação externa cega. Não fazem parte do currículo de treino.
"""
import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from linguagem_neural import LinguagemNeural
from web_core import responder_web
from avaliar_retomada import FORMAS, ALVOS
from treinar_linguagem import avaliar_quadros


class RetomadaNeuralTestes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rede = LinguagemNeural(json.loads(
            Path(__file__).with_name("rede_linguagem.json").read_text(encoding="utf-8")))

    def test_extrai_alvos_ineditos_sem_transformar_preambulo_em_assunto(self):
        for forma in FORMAS:
            for alvo in ALVOS:
                with self.subTest(forma=forma, alvo=alvo):
                    pergunta = forma.format(alvo=alvo)
                    q = self.rede.analisar(pergunta)
                    self.assertEqual((q.ato, q.alvo, q.outro), ("retomar", alvo, ""))
                    self.assertTrue(q.conservado)
                    self.assertEqual(pergunta[q.spans[0][1]:q.spans[0][2]], alvo)

    def test_retomada_real_apos_troca_de_tema_e_saudacao(self):
        for forma in FORMAS:
            for alvo, outro in (("memória", "DNA"), ("RNA", "sinapse"), ("gravidade", "neurônio")):
                with self.subTest(forma=forma, alvo=alvo):
                    bot = Crivo()
                    bot.responder("O que é " + alvo + "?")
                    anterior = bot.contexto_textual
                    bot.responder("O que é " + outro + "?")
                    bot.responder("Oi")
                    pergunta = forma.format(alvo=alvo)
                    self.assertEqual(bot.responder(pergunta)[0], "escrita:retomada")
                    self.assertEqual(bot.contexto_textual.temas, anterior.temas)
                    self.assertEqual(bot.contexto_textual.exibidos, anterior.exibidos)
                    self.assertEqual(bot.ultimo_turno["pergunta"], pergunta)

    def test_qualificador_nao_e_apagado_para_retornar_a_um_assunto_conhecido(self):
        for alvo in ("DNA alienígena", "memória sem limite", "RNA com outra função", "DNA/alienígena"):
            with self.subTest(alvo=alvo):
                pergunta = FORMAS[0].format(alvo=alvo)
                q = self.rede.analisar(pergunta)
                self.assertTrue(not q.conservado or q.alvo == alvo, q)
                bot = Crivo()
                bot.responder("O que é DNA?")
                bot.responder("O que é RNA?")
                bot.responder("O que é memória?")
                self.assertIn(bot.responder(pergunta)[0], ("duvida", "fora"))
                self.assertIsNone(bot.contexto_textual)

    def test_replay_reconstroi_o_assunto_e_suas_fontes(self):
        history = ["O que é memória?", "O que é DNA?", "Oi", FORMAS[0].format(alvo="memória")]
        resposta = responder_web({"history": history, "message": "Qual é a fonte?"})
        self.assertEqual(resposta["id"], "escrita:fontes")
        self.assertIn("journals.plos.org", resposta["response"])
        self.assertNotIn("genome.gov", resposta["response"])

    def test_retomada_neural_respeita_cancelamento_e_isolamento(self):
        pergunta = FORMAS[0].format(alvo="memória")
        bot = Crivo()
        bot.responder("O que é memória?")
        bot.responder("Mudar de assunto")
        self.assertIn(bot.responder(pergunta)[0], ("duvida", "fora"))
        self.assertIn(Crivo().responder(pergunta)[0], ("duvida", "fora"))
        self.assertFalse(bot.conversacao.lembrancas)

    def test_retomada_funciona_em_base_personalizada_sem_herdar_o_curriculo(self):
        base = [dict(id="kavor", topico="objetos", perguntas=["o que é Kavor Z17"],
                     resposta="Kavor Z17 é um objeto fictício. Ele possui 7 marcas azuis."),
                dict(id="nevia", topico="objetos", perguntas=["o que é circuito de Névia"],
                     resposta="Circuito de Névia é um mecanismo fictício. Ele possui 3 sinais verdes.")]
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "conhecimento.json"
            caminho.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
            for forma in FORMAS:
                bot = Crivo(caminho)
                bot.responder("O que é Kavor Z17?")
                bot.responder("O que é circuito de Névia?")
                bot.responder("Oi")
                ident, texto = bot.responder(forma.format(alvo="Kavor Z17"))
                self.assertEqual(ident, "escrita:retomada")
                self.assertIn("7 marcas azuis", texto)
                self.assertNotIn("3 sinais verdes", texto)
                self.assertIsNone(bot.curriculo_mundo)

    def test_negacao_e_condicoes_conservam_o_escopo_do_pedido(self):
        for alvo in ALVOS:
            pergunta = "Definir " + alvo + " não foi meu pedido."
            q = self.rede.analisar(pergunta)
            self.assertTrue(q.negacao_pedido)
            self.assertEqual(q.alvo, alvo)
        for alvo in ("rede não circular", "objeto sem nome"):
            q = self.rede.analisar("Me explica o que é " + alvo + ".")
            self.assertFalse(q.negacao_pedido)
            self.assertTrue(not q.conservado or q.alvo == alvo)
        pergunta = "Podemos retomar o assunto DNA se existir em outra dimensão?"
        bot = Crivo()
        bot.responder("O que é DNA?")
        self.assertIn(bot.responder(pergunta)[0], ("duvida", "fora"))

    def test_checkpoint_preserva_as_familias_de_validacao(self):
        dados = json.loads(Path(__file__).with_name("curriculo_linguagem_neural.json").read_text(encoding="utf-8"))
        casos = [c for c in dados["exemplos"] if c["split"] == "validacao"]
        resultado = avaliar_quadros(self.rede, casos)
        self.assertGreaterEqual(resultado["atos_corretos"], 75)
        self.assertGreaterEqual(resultado["quadros_corretos"], 75)
        for ato in ("retomar", "comparar", "negado"):
            self.assertEqual(resultado["por_ato"][ato]["quadros"], 8)
        treino = [c for c in dados["exemplos"] if c["split"] == "treino"]
        self.assertFalse({c["texto"] for c in treino} &
                         {f.format(alvo=a) for f in FORMAS for a in ALVOS})

    def test_fallback_neural_nao_executa_pedido_apenas_citado_ou_em_codigo(self):
        bot = Crivo()
        bot.responder("O que é memória?")
        for pergunta in ('Ele disse "podemos retomar o assunto memória?"',
                         '`Podemos retomar o assunto memória?`'):
            self.assertIsNone(bot.conversacao._analisar_neural(pergunta))

    def test_pedido_de_retomada_negado_nao_reabre_o_assunto(self):
        for pergunta in ("Não retome memória.", "Não quero retomar memória.",
                         "Não volte ao assunto memória."):
            bot = Crivo()
            bot.responder("O que é memória?")
            bot.responder("O que é DNA?")
            self.assertIsNone(bot.conversacao._analisar_neural(pergunta))
            self.assertNotEqual(bot.responder(pergunta)[0], "escrita:retomada")

    def test_operadores_fora_do_nome_nao_sao_apagados(self):
        for sufixo in ("===", "/", "*", "&", "^"):
            pergunta = "Podemos retomar o assunto DNA " + sufixo + "?"
            self.assertFalse(self.rede.analisar(pergunta).conservado)
            bot = Crivo()
            bot.responder("O que é DNA?")
            self.assertNotEqual(bot.responder(pergunta)[0], "escrita:retomada")
