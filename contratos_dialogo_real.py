"""Contratos da meta de conversa espontânea, reparo, memória e HTTP.

Execute explicitamente: python -m unittest contratos_dialogo_real -v.
Ainda há contratos NÃO atendidos pelos candidatos; a sonda e seus critérios
permanecem integrais. As regressões do serviço padrão são testes separados.

Sem IDs escolhidos para aprovar metaconversa ou acompanhamento pessoal: a
asserção examina a resposta exibida e os dados declarados pelo usuário.
"""
import json
import threading
import unittest
from urllib.request import Request, urlopen

from avaliar_dialogo_real import CASOS, assinatura_casos, falhas_turno
from crivo import Crivo
from web_core import responder_web
from web_local import criar_servidor


class TestesOraculoDialogoReal(unittest.TestCase):
    def test_sonda_congelada_antes_das_novas_respostas(self):
        self.assertEqual(len(CASOS), 18)
        self.assertEqual(sum(len(cs) for _, cs in CASOS), 72)
        self.assertEqual(assinatura_casos(),
                         "6cc7ca80126a8ca1e49b9d21736ebc1a18c7753cde3eb32bdd6c4184df1d503e")

    def test_id_conversacional_nao_aprova_resposta_generica(self):
        criterio = dict(CASOS)["identidade e compreensão coloquial"][1]
        falhas = falhas_turno(criterio, "conversa:entendimento",
                             "Ainda não consegui entender esse pedido. Pode indicar o assunto e o que quer saber?")
        self.assertIn("resposta genérica sem acompanhar o sentido", falhas)

    def test_id_de_memoria_nao_aprova_dado_errado(self):
        criterio = dict(CASOS)["correção de memória sem inventar biografia"][2]
        self.assertTrue(falhas_turno(criterio, "conversa:memoria", "Você disse que tem um cachorro."))

    def test_repeticao_pertinente_ainda_precisa_avancar(self):
        criterio = dict(CASOS)["abreviações e linguagem cotidiana"][3]
        resposta = "Você quer falar da sua expectativa."
        self.assertIn("repetição integral sem avançar",
                      falhas_turno(criterio, "conversa:relato", resposta, [resposta]))

    def test_nao_execucao_nao_e_aprovada_por_copia_de_tema(self):
        criterio = dict(CASOS)["negação de ação e memória da restrição"][1]
        self.assertIn("escrita executada apesar da intenção",
                      falhas_turno(criterio, "conversa:gerada_mensagem", "Rascunho: vamos conversar sobre a mensagem."))


class TestesDialogoReal(unittest.TestCase):
    def verificar_sequencia(self, nome):
        criterios = dict(CASOS)[nome]
        bot, anteriores = Crivo(usar_dialogo_contextual=True), []
        for c in criterios:
            with self.subTest(pergunta=c["pergunta"]):
                ident, resposta = bot.responder(c["pergunta"])
                self.assertEqual(falhas_turno(c, ident, resposta, anteriores, bot), [], resposta)
                anteriores.append(resposta)
        return bot

    def test_identidade_e_compreensao_em_linguagem_informal(self):
        self.verificar_sequencia("identidade e compreensão coloquial")

    def test_reparo_muda_a_intencao_ativa(self):
        self.verificar_sequencia("reparo explícito de intenção")

    def test_comparacao_hipotetica_sem_resposta_aritmetica(self):
        self.verificar_sequencia("comparação de situações hipotéticas")

    def test_correcoes_substituem_o_dado_sem_inventar_biografia(self):
        self.verificar_sequencia("correção de memória sem inventar biografia")

    def test_hipotese_e_citacao_nao_mudam_estado_real(self):
        self.verificar_sequencia("fala citada e hipótese não substituem estado real")

    def test_fatos_codigo_e_fontes_conservam_seu_motor(self):
        self.verificar_sequencia("fato, fonte, código e prova mantêm prioridade")

    def test_prova_logica_depois_de_conversa_aberta(self):
        bot = self.verificar_sequencia("vida como questão aberta e reparo de sentido")
        i, r = bot.responder("Por que um pinguim é um ser vivo?")
        self.assertEqual(i, "logica:tipo_de")
        self.assertIn("pinguim → ave", r)
        self.assertIsNotNone(bot.ultimo_turno)

    def test_replay_web_e_isolamento_da_memoria(self):
        history = [c["pergunta"] for c in dict(CASOS)["correção de memória sem inventar biografia"][:2]]
        pedido = dict(history=history, message="Qual bicho eu disse que tenho mesmo?")
        a = responder_web(pedido, usar_dialogo_contextual=True)
        self.assertEqual(a, responder_web(pedido, usar_dialogo_contextual=True))
        self.assertIn("gato", a["response"].casefold())
        self.assertNotIn("cachorro", a["response"].casefold())
        self.assertFalse(a["has_proof"])
        isolada = responder_web(dict(message=pedido["message"]), usar_dialogo_contextual=True)
        self.assertNotIn("Pingo", isolada["response"])
        self.assertNotIn("Nairu", isolada["response"])


class TestesDialogoRealHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = criar_servidor("127.0.0.1", 0, usar_dialogo_contextual=True)
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      kwargs={"poll_interval": .02}, daemon=True)
        cls.thread.start()
        cls.url = "http://127.0.0.1:%s/api/chat" % cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_http_entendimento_e_continuidade_exibidos(self):
        cs = dict(CASOS)["identidade e compreensão coloquial"]
        payload = dict(message=cs[1]["pergunta"], history=[cs[0]["pergunta"]])
        pedido = Request(self.url, data=json.dumps(payload).encode("utf-8"),
                         headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(pedido, timeout=30) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers["Cache-Control"], "no-store")
            dado = json.loads(r.read().decode("utf-8"))
        self.assertEqual(dado, responder_web(payload, usar_dialogo_contextual=True))
        self.assertEqual(falhas_turno(cs[1], dado["id"], dado["response"]), [], dado["response"])
        self.assertFalse(dado["has_proof"])


if __name__ == "__main__":
    unittest.main()
