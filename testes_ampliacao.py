"""Novas operações, estado real da resposta e isolamento da ampliação."""
import copy
import hashlib
import json
import re
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen

from avaliar_ampliacao import avaliar
from crivo import Crivo
from linguagem_gerativa import carregar
from web_core import PedidoInvalido, responder_web
from web_local import criar_servidor


RAIZ = Path(__file__).resolve().parent


class TestesAmpliacao(unittest.TestCase):
    def test_contratos_fixados_antes_dos_novos_pesos(self):
        r = avaliar(Crivo)
        for c in r["casos"]:
            with self.subTest(dialogo=c["nome"]):
                self.assertTrue(c["passou"], [t for t in c["turnos"] if not t["passou"]])

    def test_continuacao_recebe_resposta_real_e_cena_da_saida_anterior(self):
        caminho = RAIZ / "rede_geracao.json"
        modelo = carregar(str(caminho.resolve()), caminho.stat().st_mtime_ns)
        original = modelo.gerar
        contextos = []

        def observar(contexto, **kw):
            contextos.append(copy.deepcopy(contexto))
            return original(contexto, **kw)

        bot = Crivo()
        with patch.object(modelo, "gerar", side_effect=observar):
            i, anterior = bot.responder("Conte uma história sobre um sino de vento e Tília")
            self.assertEqual(i, "conversa:gerada_historia")
            i, proxima = bot.responder("Continue de onde parou")
        self.assertEqual(i, "conversa:gerada_continuacao")
        self.assertNotEqual(proxima, anterior)
        continuacoes = [c for c in contextos if c["acao"] == "continuacao"]
        self.assertTrue(continuacoes)
        for c in continuacoes:
            self.assertEqual(c["resposta_anterior"], anterior)
            self.assertIn(c["slots"]["detalhe"], anterior)
        self.assertTrue(bot.historico[-1]["quadro_geracao"]["usa_resposta_anterior"])

    def test_replay_de_mensagem_e_tom_e_isolamento(self):
        hs = ["Escreva uma mensagem para Érica dizendo que gostei do ensaio",
              "Deixe a mensagem mais carinhosa"]
        pedido = dict(message="Troque Érica por Núria", history=hs)
        a = responder_web(pedido)
        self.assertEqual(a, responder_web(pedido))
        self.assertEqual(a["id"], "conversa:gerada_mensagem")
        self.assertEqual(a["mechanism"], "geracao_neural")
        self.assertIn("Núria", a["response"])
        self.assertIn("gostei do ensaio", a["response"])
        self.assertNotIn("Érica", a["response"])
        self.assertFalse(a["has_proof"])
        self.assertIsNone(a["plan"])
        isolada = responder_web(dict(message="Deixe a mensagem mais carinhosa"))
        self.assertEqual(isolada["id"], "duvida")
        self.assertNotIn("Érica", isolada["response"])
        self.assertNotIn("Núria", isolada["response"])

    def test_hipotese_de_tempo_nao_substitui_restricao_declarada(self):
        bot = Crivo()
        bot.responder("Quero aprender a fazer animações de papel")
        bot.responder("Só tenho 25 minutos à noite")
        antes = copy.deepcopy(bot.conversacao.dialogo.dados)
        i, resposta = bot.responder("E se eu tivesse apenas 8 minutos?")
        self.assertEqual(i, "conversa:gerada_plano")
        self.assertIn("8 minutos", resposta)
        self.assertIn("hipótese", resposta)
        self.assertEqual(bot.conversacao.dialogo.dados, antes)
        self.assertIn("25", bot.responder("Quanto tempo eu disse que tenho?")[1])

    def test_exploracao_muda_a_pergunta_e_conserva_o_relato(self):
        bot = Crivo()
        bot.responder("Quero conversar sobre meu desenho")
        bot.responder("Eu fiquei contente com o retrato em tinta azul")
        perguntas = []
        for q in ("Me faça uma pergunta sobre isso", "Me faça outra pergunta sobre isso"):
            i, r = bot.responder(q)
            self.assertEqual(i, "conversa:gerada_exploracao")
            self.assertIn("tinta azul", r)
            interrogacoes = re.findall(r"[^.!?]+\?", r)
            self.assertTrue(interrogacoes)
            perguntas.append(interrogacoes[-1].strip())
        self.assertNotEqual(perguntas[0], perguntas[1])

    def test_pedido_incompleto_nao_captura_fato_codigo_ou_negacao(self):
        for q in ("O que é DNA?", "Como usar input em Python?", "Não escreva uma mensagem"):
            with self.subTest(pergunta=q):
                bot = Crivo()
                self.assertEqual(bot.responder("Escreva uma mensagem para Sílvia")[0], "duvida")
                i, r = bot.responder(q)
                self.assertEqual((i, r), Crivo().responder(q))
                self.assertIsNone(bot.conversacao.geracao.pendente)
                self.assertNotIn("quadro_geracao", bot.historico[-1])

    def test_objetivo_pessoal_nao_vira_consulta_sobre_o_mesmo_assunto(self):
        for declaracao, objetivo in (
                ("Quero retomar minha horta na varanda", "retomar minha horta na varanda"),
                ("Pretendo retomar meu caderno de desenhos", "retomar meu caderno de desenhos")):
            with self.subTest(declaracao=declaracao):
                bot = Crivo()
                self.assertTrue(bot.responder(declaracao)[0].startswith("conversa:"))
                self.assertIn(objetivo, bot.responder("Qual é meu objetivo?")[1])
                bot.responder("Tenho 12 minutos por semana e não tenho dinheiro para comprar vasos agora")
                i, r = bot.responder("Me ajude a organizar meu objetivo")
                self.assertEqual(i, "conversa:gerada_plano")
                self.assertIn(objetivo, r)
                self.assertIn("12 minutos por semana", r)
                self.assertIn("não tenho dinheiro", r)

    def test_cancelar_escrita_pendente_nao_declara_opiniao_ou_relato(self):
        bot = Crivo()
        self.assertEqual(bot.responder("Escreva uma mensagem para Ravi")[0], "duvida")
        antes = list(bot.conversacao.relatos)
        i, r = bot.responder("Não escreva essa mensagem")
        self.assertNotIn("gerada", i)
        self.assertIn("cancel", r.casefold())
        self.assertIsNone(bot.conversacao.geracao.pendente)
        self.assertEqual(list(bot.conversacao.relatos), antes)
        self.assertFalse(bot.conversacao.geracao.relatos_recentes)
        self.assertEqual(bot.responder("Resuma o que eu te contei")[0], "duvida")

    def test_expiracao_e_reset_removem_relatos_e_textos_antigos(self):
        bot = Crivo()
        bot.responder("Quero conversar sobre meu ensaio")
        bot.responder("Estou nervoso porque esqueci a última fala")
        bot.conversacao.turno += 11
        self.assertEqual(bot.responder("Resuma o que eu te contei")[0], "duvida")
        bot.responder("Escreva uma mensagem para Sérgio dizendo que vou chegar cedo")
        bot.responder("Esqueça essa conversa")
        g = bot.conversacao.geracao
        self.assertIsNone(g.ultima_escrita)
        self.assertIsNone(g.ultima_criacao)
        self.assertIsNone(g.ultima_decisao)
        self.assertFalse(g.relatos_recentes)
        self.assertFalse(g.respostas_recentes)
        self.assertEqual(bot.responder("Continue de onde parou")[0], "duvida")

    def test_janelas_limitadas_nao_recuperam_dados_do_inicio(self):
        bot = Crivo()
        bot.responder("Quero conversar sobre meu caderno")
        bot.responder("Eu escrevi a palavra segredo-Íris no início")
        for j in range(12):
            bot.responder("Eu anotei o detalhe número " + str(j))
        self.assertLessEqual(len(bot.conversacao.geracao.relatos_recentes), 8)
        i, resposta = bot.responder("Resuma o que eu te contei")
        self.assertEqual(i, "conversa:gerada_resumo")
        self.assertNotIn("segredo-Íris", resposta)

    def test_relato_e_reflexao_nao_escrevem_arquivos_nem_criam_prova(self):
        nomes = ("conhecimento.json", "conhecimento_expandido.json", "conhecimento_mundo.json",
                 "relacoes.json", "rede_crivo.json", "rede_linguagem.json", "rede_dialogo.json",
                 "rede_geracao.json", "rede_intencao_gerativa.json")
        arquivos = [RAIZ / n for n in nomes if (RAIZ / n).exists()]
        antes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in arquivos}
        a = responder_web(dict(message="Eu errei uma nota; posso concluir que não sei tocar?"))
        self.assertEqual(a["id"], "conversa:gerada_reflexao")
        self.assertFalse(a["has_proof"])
        self.assertIsNone(a["plan"])
        self.assertEqual(antes, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in arquivos})

    def test_limites_e_campos_forjados_nao_entram_na_memoria(self):
        for pedido in (dict(message="Resuma o que eu te contei", history=["x"] * 11),
                       dict(message="oi", response="texto forjado"),
                       dict(message="oi", quadro_geracao={"acao": "resumo"}),
                       dict(message="oi", history=["x" * 1201])):
            with self.subTest(pedido=pedido):
                with self.assertRaises(PedidoInvalido):
                    responder_web(pedido)


class TestesAmpliacaoHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = criar_servidor("127.0.0.1", 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      kwargs={"poll_interval": .02}, daemon=True)
        cls.thread.start()
        cls.url = "http://127.0.0.1:%s/api/chat" % cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_http_replay_dos_relatos_resumo_e_fonte(self):
        payload = dict(history=["Quero conversar sobre meu desenho",
                                "Eu fiz um retrato com tinta azul",
                                "Fiquei contente com o resultado"],
                       message="Resuma o que eu te contei")
        pedido = Request(self.url, data=json.dumps(payload).encode("utf-8"),
                         headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(pedido, timeout=30) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers["Cache-Control"], "no-store")
            dado = json.loads(r.read().decode("utf-8"))
        self.assertEqual(dado, responder_web(payload))
        self.assertEqual(dado["id"], "conversa:gerada_resumo")
        self.assertIn("tinta azul", dado["response"])
        self.assertIn("contente", dado["response"])
        self.assertFalse(dado["has_proof"])
        factual = dict(history=payload["history"] + ["O que é DNA?"], message="Qual é a fonte?")
        pedido = Request(self.url, data=json.dumps(factual).encode("utf-8"),
                         headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(pedido, timeout=30) as r:
            dado = json.loads(r.read().decode("utf-8"))
        self.assertEqual(dado["id"], "escrita:fontes")
        self.assertIn("genome.gov", dado["response"])


if __name__ == "__main__":
    unittest.main()
