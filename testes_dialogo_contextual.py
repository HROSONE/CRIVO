"""Prioridade factual e isolamento independem de acertos do classificador."""
import unittest
from unittest.mock import patch
import json
from pathlib import Path

from crivo import Crivo
from dialogo_contextual import DialogoContextual
from linguagem_conversa import Ato, Preparacao


QUADRO = {"ato": "desabafo", "aceita": True, "confianca": .99,
          "spans": [], "rota": "conversa", "aceita_rota": True}


class TestesPrioridadeContextual(unittest.TestCase):
    def test_microcircuito_factual_tem_prioridade_sobre_rota_neural(self):
        bot = Crivo(usar_dialogo_contextual=True)
        camada = bot.conversacao.contextual
        with patch.object(bot.compositor, "responder", return_value=("escrita:explicacao", "Fato com fonte", object())), \
                patch.object(camada, "_compreender", return_value=QUADRO), \
                patch.object(camada, "_responder", side_effect=AssertionError("Evidência interceptada")):
            self.assertIsNone(camada.preparar("Um pedido reconhecido pelo circuito", bot, bot.conversacao))
            self.assertFalse(camada.ultimo_quadro["aceita"])

    def test_checkpoints_publicados_realmente_carregam(self):
        from compreensao_neural import CompreensaoNeural
        from dialogo_seq2seq import DialogoSeq2Seq
        pasta = Path(__file__).parent
        from arquivos_contextuais import ler_json
        entender = CompreensaoNeural(ler_json(pasta / "rede_compreensao.json"))
        gerar = DialogoSeq2Seq(ler_json(pasta / "rede_dialogo_seq2seq.json"))
        self.assertTrue(entender.tem_rota)
        self.assertIsNotNone(gerar)

    def test_padrao_nao_aciona_modelos_experimentais(self):
        from web_core import responder_web, PedidoInvalido
        with patch("compreensao_neural.carregar", side_effect=AssertionError("Modelo experimental acionado")):
            self.assertEqual(Crivo().responder("O que é DNA?")[0], "conhecimento:dna")
            self.assertFalse(responder_web({"message": "Olá"})["experimental_dialogue"])
        with self.assertRaises(PedidoInvalido):
            responder_web({"message": "Olá", "experimental_dialogue": True})

    def test_previsao_errada_conserva_fato_prova_codigo_e_reset(self):
        for pergunta, esperado in (
            ("Você pode explicar o que é DNA?", "conhecimento:dna"),
            ("Por que um pinguim é um ser vivo?", "logica:tipo_de"),
            ("Você acha que a Terra é uma estrela?", "logica:desconhecido"),
            ("Esqueça essa conversa", "conversa:reinicio"),
        ):
            with self.subTest(pergunta=pergunta):
                bot = Crivo(usar_dialogo_contextual=True)
                camada = bot.conversacao.contextual
                with patch.object(camada, "_compreender", return_value=QUADRO), \
                        patch.object(camada, "_responder", side_effect=AssertionError("Prioridade violada")):
                    self.assertEqual(bot.responder(pergunta)[0], esperado)

    def test_palavras_tecnicas_citacoes_e_temas_abertos_nao_bloqueiam_relato(self):
        bot = Crivo(usar_dialogo_contextual=True)
        camada = bot.conversacao.contextual
        for texto in (
            "Estou estudando SQL e isso me deixa inseguro",
            'Ele disse "você não me escuta"; fiquei magoado',
            "Qual o sentido de estar vivo?",
        ):
            self.assertFalse(camada._proteger(texto, bot, bot.conversacao), texto)

    def test_roteamento_nao_promove_quadro_recusado_nem_herda_plano(self):
        bot = Crivo(usar_dialogo_contextual=True)
        camada = bot.conversacao.contextual
        bot.planejador.ultimo = {"texto": "plano anterior"}
        pergunta = "Preciso conversar sobre o ocorrido"
        q = dict(QUADRO, aceita=False, rota="conversa", aceita_rota=True,
                 confianca_rota=.99,
                 spans=[{"papel":"objetivo","inicio":0,"fim":len(pergunta),
                         "texto":pergunta,"confianca":.99}])
        resultado = Preparacao(Ato("dialogo_contextual_livre", "dialogar"),
                               ("conversa:neural_livre", "Pode me contar o que aconteceu.", None, ""))
        with patch.object(camada, "_compreender", return_value=q), \
                patch.object(camada, "_responder", return_value=resultado):
            self.assertEqual(bot.responder(pergunta)[0], "conversa:neural_livre")
        self.assertIsNone(bot.planejador.ultimo)
        self.assertIsNone(camada.memoria.contexto()["objetivo"])
        self.assertTrue(bot.conversacao.dialogo.ativo)
        self.assertIsNone(bot.ultimo_turno.get("prova_origem"))
        self.assertEqual(bot.historico[-1]["mecanismo"], "dialogo_contextual_neural")

    def test_modelo_desativado_nao_le_checkpoint(self):
        camada = DialogoContextual(usar_neural=False)
        with patch("compreensao_neural.carregar", side_effect=AssertionError("Leitura indevida")):
            self.assertIsNone(camada._compreender("Podemos conversar?"))

    def test_falha_de_pesos_nao_reutiliza_interpretacao_anterior(self):
        bot = Crivo(usar_dialogo_contextual=True)
        camada = bot.conversacao.contextual
        camada.ultimo_quadro = QUADRO
        with patch.object(camada, "_compreender", side_effect=ValueError("Peso inválido")):
            self.assertEqual(bot.responder("O que é RNA?")[0], "conhecimento:rna")
        self.assertIsNone(camada.ultimo_quadro)
        self.assertEqual(camada.memoria.contexto()["historico"][-1]["papel"], "assistente")


if __name__ == "__main__":
    unittest.main()
