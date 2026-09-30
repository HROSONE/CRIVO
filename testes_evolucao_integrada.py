"""Contratos de execução, evidência, isolamento e pedidos compostos."""
import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from avaliar_evolucao_integrada import avaliar, base_sintetica
from crivo import Crivo
from web_core import PedidoInvalido, responder_web


class TestesEvolucaoIntegrada(unittest.TestCase):
    def bot_sintetico(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        base, expandido = base_sintetica()
        caminho = Path(pasta.name) / "conhecimento.json"
        caminho.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
        caminho.with_name("conhecimento_expandido.json").write_text(json.dumps(expandido, ensure_ascii=False), encoding="utf-8")
        return Crivo(caminho), expandido["itens"]

    def test_bateria_autoral_completa(self):
        resultado = avaliar()
        self.assertEqual(resultado["falhas"], [])

    def test_composicao_cobre_todos_os_conceitos_cientificos(self):
        bot = Crivo()
        for item in bot.curriculo_mundo["itens"]:
            with self.subTest(conceito=item["nome"]):
                _, resposta = bot.responder("Explique " + item["nome"] + "; depois resuma; mostre as fontes")
                self.assertIn(item["fatos"][0]["texto"], resposta)
                self.assertIn("Resumo:", resposta)
                self.assertIn(bot.compositor.fontes[item["fatos"][0]["fonte"]]["url"], resposta)
                self.assertTrue(bot.planejador.ultimo["completo"])

    def test_comparacao_usa_definicoes_sem_inventar_relacoes(self):
        dado = responder_web({"message": "Explique DNA e RNA; compare os dois; depois resuma tudo isso"})
        self.assertEqual(dado["id"], "escrita:plano")
        resumo = dado["response"].split("Resumo:\n")[-1]
        self.assertIn("O DNA é", resumo)
        self.assertIn("O RNA é", resumo)
        self.assertFalse(dado["has_proof"])
        self.assertTrue(dado["plan"]["completo"])

    def test_comparacao_com_e_ordinais(self):
        bot, itens = self.bot_sintetico()
        a,b=itens[:2]
        bot.responder("Explique "+a["nome"]+"; explique "+b["nome"])
        _, texto=bot.responder("Compare o primeiro com o segundo; resuma tudo isso")
        self.assertIn(a["fatos"][0]["texto"], texto)
        self.assertIn(b["fatos"][0]["texto"], texto)

    def test_as_fontes_correspondem_a_cada_etapa(self):
        dado = responder_web({"message": "Explique DNA; explique sinapse; mostre as fontes"})
        self.assertTrue(dado["plan"]["completo"])
        self.assertIn("genome.gov", dado["response"])
        self.assertIn("nida.nih.gov", dado["response"])
        for etapa in dado["plan"]["etapas"]:
            for evidencia in etapa["evidencias"]:
                self.assertTrue(evidencia["fontes"])
                self.assertIn(evidencia["texto"], dado["response"])

    def test_codigo_permanece_inteiro_em_todas_as_etapas(self):
        original = responder_web({"message": "Como usar input em Python?"})["response"]
        blocos = re.findall(r"```.*?```", original, re.S)
        dado = responder_web({"message": "Como usar input em Python? Depois reformule; depois organize em tópicos"})
        encontrados = re.findall(r"```.*?```", dado["response"], re.S)
        self.assertEqual(encontrados, blocos*3)
        self.assertFalse(dado["has_proof"])
        self.assertTrue(dado["plan"]["completo"])

    def test_prova_conservada_no_replay_e_na_transformacao(self):
        pedido = "Por que um pinguim é um ser vivo? Depois resuma"
        for historico, pergunta in (([], pedido), ([pedido], "Com outras palavras")):
            dado = responder_web({"history": historico, "message": pergunta})
            self.assertTrue(dado["has_proof"])
            self.assertIn("pinguim → ave → vertebrado → animal → ser vivo", dado["response"])

    def test_prova_na_composicao_com_outro_assunto(self):
        pedido = "Por que um pinguim é um ser vivo? Explique DNA; reformule"
        for historico, pergunta in (([], pedido), ([pedido], "Com outras palavras")):
            dado = responder_web({"history": historico, "message": pergunta})
            self.assertTrue(dado["has_proof"])
            self.assertIn("pinguim → ave → vertebrado → animal → ser vivo", dado["response"])
            self.assertIn("informações genéticas", dado["response"])

    def test_parcial_indica_a_lacuna_e_preserva_o_conhecimento(self):
        dado = responder_web({"message": "Explique sinapse; dê um exemplo; mostre as fontes"})
        self.assertEqual(dado["id"], "escrita:plano_parcial")
        self.assertFalse(dado["plan"]["completo"])
        self.assertIn("Não tenho exemplo cadastrado", dado["response"])
        self.assertIn("ponto de comunicação", dado["response"])
        self.assertEqual(dado["plan"]["etapas"][1]["evidencias"], [])

    def test_pedido_desconhecido_nao_resume_o_assunto_anterior(self):
        bot = Crivo()
        bot.responder("O que é DNA?")
        _, texto = bot.responder("Explique o módulo inexistente PX; depois resuma")
        self.assertNotIn("informações genéticas", texto)
        self.assertIsNone(bot.contexto_textual)

    def test_nega_pedido_completo_sem_executar_outros_trechos(self):
        bot = Crivo()
        for pedido in ("Não explique DNA; depois resuma", "Explique DNA; não mostre as fontes",
                       "Explique DNA só se isso curar todas as doenças; depois resuma"):
            with self.subTest(pedido=pedido):
                _, texto=bot.responder(pedido)
                self.assertNotIn("O DNA é a molécula", texto)
                self.assertIsNone(bot.contexto_textual)

    def test_busca_de_detalhes_exige_qualificadores_completos(self):
        bot, itens = self.bot_sintetico()
        nome = itens[0]["nome"]
        for detalhe in ("registro de marcas ultravioletas", "pulsos luminosos alienígenas", "cura doenças", "inverte a função"):
            with self.subTest(detalhe=detalhe):
                ident,texto=bot.responder("Sobre "+nome+", explique "+detalhe)
                self.assertEqual(ident,"fora")
                self.assertNotIn("marcas verdes",texto)
                self.assertEqual(bot.planejador.ultimo["etapas"][0]["evidencias"],[])

    def test_resumo_preserva_condicoes_numeros_e_limites(self):
        bot,itens=self.bot_sintetico()
        _,texto=bot.responder("Explique "+itens[0]["nome"]+"; aprofunde; resuma")
        resumo=texto.split("Resumo:\n")[-1]
        self.assertIn("7",resumo)
        self.assertIn("Se não há luz",resumo)
        self.assertIn("pode falhar",resumo)
        self.assertIn("não garante precisão",resumo)

    def test_resumo_em_uma_frase_preserva_as_evidencias(self):
        bot,itens=self.bot_sintetico()
        _,texto=bot.responder("Explique "+itens[0]["nome"]+"; aprofunde; resuma em uma frase")
        resumo=texto.split("Resumo:\n")[-1]
        self.assertEqual(resumo.count("."),1)
        self.assertNotIn("\n",resumo)
        self.assertIn("7 marcas verdes",resumo)
        self.assertIn("não garante precisão",resumo)

    def test_busca_de_detalhe_em_um_pedido_composto(self):
        bot,itens=self.bot_sintetico()
        _,texto=bot.responder("Sobre "+itens[0]["nome"]+", explique marcas verdes; resuma; cite as fontes")
        self.assertTrue(bot.planejador.ultimo["completo"])
        self.assertIn(itens[0]["fatos"][1]["texto"],texto)
        self.assertIn("example.org/manual-ficticio",texto)

    def test_confirmacao_nao_escolhe_entre_alvos(self):
        bot,itens=self.bot_sintetico()
        bot.responder("Explique "+itens[0]["nome"]+"; explique "+itens[1]["nome"])
        self.assertEqual(bot.responder("Resuma isso")[0],"duvida")
        self.assertEqual(bot.responder("sim")[0],"duvida")
        _,texto=bot.responder("2")
        self.assertIn(itens[1]["fatos"][0]["texto"],texto)
        self.assertNotIn(itens[0]["fatos"][0]["texto"],texto)

    def test_referencia_expira_apos_recusa_e_troca_de_tema(self):
        bot,itens=self.bot_sintetico()
        introducao="Explique "+itens[0]["nome"]+"; explique "+itens[1]["nome"]
        for entre in ("Oi!", "Mudar de assunto", "O que é o objeto inexistente ZX?"):
            bot.responder(introducao)
            bot.responder(entre)
            _,texto=bot.responder("Resuma o segundo")
            self.assertNotIn(itens[1]["fatos"][0]["texto"],texto)

    def test_ensinar_reconstroi_o_indice_e_esquece_referencias(self):
        bot,itens=self.bot_sintetico()
        bot.responder("Explique "+itens[0]["nome"]+"; depois resuma")
        bot.ensinar("novo_objeto", "clima", ["o que é Fralo"], "Fralo é um objeto fictício com 13 pontos.", salvar=False)
        self.assertFalse(bot.planejador.opcoes)
        _,texto=bot.responder("Explique Fralo; depois resuma")
        self.assertIn("13 pontos",texto)
        self.assertNotIn("Vétron",texto)

    def test_limite_de_etapas_e_citacoes(self):
        bot=Crivo()
        ident,texto=bot.responder("; ".join(["Explique DNA"]*7))
        self.assertEqual(ident,"duvida")
        self.assertNotIn("informações genéticas",texto)
        for pedido in ('Ele disse "explique DNA; depois resuma"', '```explique DNA; depois resuma```'):
            bot.responder(pedido)
            self.assertIsNone(bot.planejador.ultimo)

    def test_relato_com_uma_pergunta_nao_vira_plano_incompleto(self):
        bot=Crivo()
        self.assertIsNone(bot.planejador.analisar("Minha planta tá com folhas amareladas, o que pode ser?"))
        self.assertEqual(bot.responder("minha planta tá com as folhas amareladas, o que pode ser?")[0],"folha_amarela")

    def test_determinismo_e_isolamento_http(self):
        entrada={"history":["Explique DNA; explique RNA", "Resuma isso"], "message":"2"}
        self.assertEqual(responder_web(entrada),responder_web(copy.deepcopy(entrada)))
        self.assertEqual(responder_web({"message":"Resuma o segundo"})["id"],"fora")
        with self.assertRaises(PedidoInvalido):
            responder_web({"message":"oi", "plan":{"completo":True}})


if __name__ == "__main__":
    unittest.main()
