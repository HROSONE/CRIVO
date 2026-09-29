"""Regressões de diálogo de desenvolvimento, não teste cego de português."""
import datetime
import unittest
from unittest.mock import patch

from crivo import Crivo


# Congelados antes da implementação. Cada sequência começa sem memória.
CASOS = [
    (["planta", "a primeira"], ["duvida", "fotossintese"]),
    (["planta", "a segunda"], ["duvida", "regar"]),
    (["planta", "1"], ["duvida", "fotossintese"]),
    (["planta", "2"], ["duvida", "regar"]),
    (["planta", "opção 2"], ["duvida", "regar"]),
    (["planta", "a 2ª opção"], ["duvida", "regar"]),
    (["planta", "a de regar"], ["duvida", "regar"]),
    (["planta", "a fotossíntese"], ["duvida", "fotossintese"]),
    (["sistema", "a segunda"], ["duvida", "planetas"]),
    (["sistema", "a primeira"], ["duvida", "via_lactea"]),
    (["planta", "sim", "2"], ["duvida", "duvida", "regar"]),
    (["planta", "isso mesmo", "1"], ["duvida", "duvida", "fotossintese"]),
    (["planta", "3", "2"], ["duvida", "duvida", "regar"]),
    (["planta", "a terceira", "1"], ["duvida", "duvida", "fotossintese"]),
    (["planta", "não", "2"], ["duvida", "duvida", "duvida"]),
    (["planta", "nenhuma das duas", "1"], ["duvida", "duvida", "duvida"]),
    (["planta", "o que é a lua", "a segunda"], ["duvida", "lua", "duvida"]),
    (["planta", "que horas são", "1"], ["duvida", "dyn:hora", "duvida"]),
    (["planta", "buraco negro", "2"], ["duvida", "conhecimento:buraco_negro", "duvida"]),
    (["planta", "mais", "2"], ["duvida", "duvida", "regar"]),
    (["planta", "a segunda", "mais"], ["duvida", "regar", "mais:fim"]),
    (["planta", "o que cachorro não pode comer"], ["duvida", "cuidar_cachorro"]),
    (["planta", "posso não regar a planta?", "2"], ["duvida", "duvida", "duvida"]),
    (["a segunda"], ["duvida"]),
]


def avaliar_dialogos(classe=Crivo):
    resultados = []
    for perguntas, esperado in CASOS:
        bot = classe(agora=datetime.datetime(2026, 9, 29, 15, 30))
        obtido = [bot.responder(p)[0] for p in perguntas]
        resultados.append({"perguntas": perguntas, "esperado": esperado,
                           "obtido": obtido, "passou": obtido == esperado})
    return {"total": len(resultados),
            "acertos": sum(r["passou"] for r in resultados),
            "casos": resultados}


class TestesDialogo(unittest.TestCase):
    def test_sequencias_completas(self):
        for resultado in avaliar_dialogos()["casos"]:
            with self.subTest(perguntas=resultado["perguntas"]):
                self.assertEqual(resultado["obtido"], resultado["esperado"])

    def test_opcoes_numeradas_e_historico_da_escolha(self):
        bot = Crivo()
        resposta = bot.responder("planta")[1]
        self.assertIn("1.", resposta)
        self.assertIn("2.", resposta)
        self.assertEqual(bot.historico, [])
        bot.responder("a segunda")
        self.assertEqual(bot.historico[-1], {
            "pergunta": "a segunda", "id": "regar", "pergunta_contexto": "planta"})
        self.assertEqual(bot.ultimo_assunto, "quantas vezes devo regar as plantas")
        self.assertIsNone(bot.esclarecimento)

    def test_conversa_de_outra_instancia_nao_herda_escolhas(self):
        primeiro, segundo = Crivo(), Crivo()
        primeiro.responder("planta")
        self.assertEqual(segundo.responder("2")[0], "duvida")
        self.assertEqual(primeiro.responder("2")[0], "regar")

    def test_rede_nao_decide_no_lugar_do_usuario(self):
        bot = Crivo()
        bot.previsao_neural = lambda p: ("fotossintese", 1.0)
        self.assertEqual(bot.responder("planta")[0], "duvida")
        self.assertEqual(bot.responder("sim")[0], "duvida")
        self.assertEqual(bot.responder("a segunda")[0], "regar")

    def test_ensinar_invalida_esclarecimento(self):
        bot = Crivo()
        bot.responder("planta")
        bot.ensinar("novo_tema", "clima", ["um novo tema"], "Um tema novo.", salvar=False)
        self.assertEqual(bot.responder("2")[0], "duvida")

    def test_sim_so_confirma_uma_sugestao(self):
        # Isola a decisão de confirmação de uma oscilação no ranking.
        for escolha, esperado in (("sim", "lua"), ("não", "duvida")):
            with self.subTest(escolha=escolha):
                bot = Crivo()
                indice = next(i for i, e in enumerate(bot.base) if e["id"] == "lua")
                with patch.object(bot, "_ranking", return_value=[(0.4, indice)]):
                    pergunta = bot.responder("satélite")
                self.assertEqual(pergunta[0], "duvida")
                self.assertIn("Responda sim, não", pergunta[1])
                self.assertEqual(bot.responder(escolha)[0], esperado)
                self.assertIsNone(bot.esclarecimento)
                self.assertEqual(bot.responder("1")[0], "duvida")

    def test_palavra_compartilhada_nao_escolhe_sozinha(self):
        bot = Crivo()
        self.assertEqual(bot.responder("planta")[0], "duvida")
        self.assertEqual(bot.responder("planta")[0], "duvida")
        self.assertEqual(bot.responder("2")[0], "regar")

    def test_mais_atualiza_memoria_da_resposta_mostrada(self):
        bot = Crivo()
        bot.responder("cachorro")
        resposta = bot.responder("mais")
        self.assertNotEqual(resposta[0], "mais:fim")
        self.assertEqual(bot.historico[-1], {"pergunta": "mais", "id": resposta[0]})
        entrada = next(e for e in bot.base if e["id"] == resposta[0])
        self.assertEqual(bot.ultimo_assunto, entrada["perguntas"][0])


if __name__ == "__main__":
    unittest.main()
