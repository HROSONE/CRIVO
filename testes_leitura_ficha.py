"""Leitura da ficha e estado interno do turno (leitura_ficha.py, estado_interno.py).

A catraca usa o teste congelado avaliacoes/leitura_ficha_v1: só o agregado.
"""
import json
import unittest
from pathlib import Path

from crivo import Crivo
from web_core import responder_web

RAIZ = Path(__file__).resolve().parent


class Modelo(unittest.TestCase):
    def test_modelo_aprovado_com_precisao_registrada(self):
        meta = json.loads((RAIZ / "artefatos" / "leitura_ficha" / "meta.json").read_text(encoding="utf-8"))
        self.assertTrue(meta["controle"]["aprovado"])
        afirma = meta["validacao_cruzada_por_assunto"]["modelo_afirma"]
        self.assertGreaterEqual(afirma["certos"] / afirma["n"], 0.9)

    def test_sem_modelo_vale_a_regra(self):
        from leitura_ficha import LeituraFicha
        bot = Crivo()
        regra = LeituraFicha(bot.compositor, caminho_modelo="/nao/existe")
        self.assertFalse(regra.aprendida)
        quadro = bot.compositor.interpretar("Chove em Titã?")
        leitura = regra.ler(quadro)
        self.assertEqual(regra.decisao(leitura), "afirmar")
        self.assertIn("chuva", bot.compositor.itens["mundo_tita"]["fatos"][leitura.indice]["texto"])


class Arbitro(unittest.TestCase):
    def test_recusa_vira_fato_da_ficha(self):
        bot = Crivo()
        ident, resposta = bot.responder("Chove em Titã?")
        self.assertIn("chuva", resposta)
        self.assertEqual(bot.historico[-1]["mecanismo"], "leitura_ficha")
        self.assertEqual(bot.estado_interno.decisao["especie"], "leitura_ficha")
        acoes = [p.acao for p in bot.estado_interno.propostas]
        self.assertEqual(acoes[0], "recusar")

    def test_resposta_e_o_fato_inteiro(self):
        bot = Crivo()
        _, resposta = bot.responder("A que distância fica Andrômeda?")
        self.assertIn("Andrômeda fica a cerca de 2,5 milhões de anos-luz da Terra.", resposta)

    def test_quantidade_sem_numero_nao_e_afirmada(self):
        bot = Crivo()
        ident, resposta = bot.responder("Qual a temperatura de Netuno?")
        self.assertNotEqual(bot.estado_interno.decisao["acao"], "afirmar")
        self.assertTrue(resposta.startswith(("Não tenho", "Reconheci", "Ainda não")), resposta)
        # Mesmo forçando a leitura: "quentes" não é um valor de temperatura.
        from leitura_ficha import LeituraFicha
        leitor = LeituraFicha(bot.compositor)
        leitura = leitor.ler(bot.compositor.interpretar("Qual a temperatura de Netuno?"))
        self.assertNotEqual(leitor.decisao(leitura), "afirmar")

    def test_negacao_fica_fora_do_nicho(self):
        bot = Crivo()
        bot.responder("Titã não tem chuva?")
        self.assertNotEqual(bot.historico[-1].get("mecanismo") if bot.historico else None, "leitura_ficha")

    def test_desligada_mantem_a_recusa(self):
        bot = Crivo()
        bot.usar_leitura_ficha = False
        ident, resposta = bot.responder("Chove em Titã?")
        self.assertEqual(ident, "fora")

    def test_resposta_comum_nao_passa_pela_leitura(self):
        bot = Crivo()
        bot.responder("O que é Júpiter?")
        self.assertEqual(bot.estado_interno.propostas[0].acao, "responder")
        self.assertEqual(len(bot.estado_interno.propostas), 1)

    def test_premissa_absoluta_nao_vira_aproximacao(self):
        bot = Crivo()
        self.assertTrue(bot.leitura_ficha.aproximar_parcial)
        ident, _ = bot.responder("Como o cérebro tem memória infinita?")
        self.assertEqual(ident, "fora")

    def test_aproximacao_parcial_avisa_que_nao_e_exata(self):
        bot = Crivo()
        ident, resposta = bot.responder("Quanto dura um ano em Mercúrio?")
        self.assertEqual(ident, "leitura:aproximacao")
        self.assertTrue(resposta.startswith("Não tenho uma resposta exata"))
        self.assertIn("88 dias", resposta)


class Api(unittest.TestCase):
    def test_estado_interno_na_api(self):
        r = responder_web({"message": "Chove em Titã?"})
        estado = r["internal_state"]
        self.assertEqual(estado["understanding"]["entities"][0]["id"], "mundo_tita")
        self.assertEqual(estado["decision"]["species"], "leitura_ficha")
        self.assertEqual(r["mechanism"], "leitura_ficha")
        self.assertIn("probability", r["card_reading"])

    def test_contexto_vira_entidade_do_estado(self):
        bot = Crivo()
        bot.responder("O que é Titã?")
        bot.responder("E ele tem chuva?")
        entidades = bot.estado_interno.entidades
        self.assertTrue(entidades)
        self.assertEqual(entidades[0].id, "mundo_tita")


class Catraca(unittest.TestCase):
    """Teste congelado da leitura (72 perguntas, fichas fora do treino).

    Medido em 05/10/2026 com a aproximação parcial ligada: respondíveis
    24 afirmadas certas + 13 aproximadas certas (eram 22 + 0 sem a leitura),
    0 afirmações erradas; sem resposta na ficha, 3 afirmadas (eram 2) e
    3 aproximadas com aviso."""

    def test_teste_congelado(self):
        from scripts.avaliar_leitura_ficha import avaliar
        resumo, _ = avaliar("teste")
        resp, nulos = resumo["respondiveis"], resumo["sem_resposta"]
        self.assertGreaterEqual(resp.get("afirmou_certo", 0) + resp.get("aproximou_certo", 0), 37, resumo)
        self.assertLessEqual(resp.get("afirmou_errado", 0), 0, resumo)
        self.assertLessEqual(nulos.get("afirmou", 0), 3, resumo)


if __name__ == "__main__":
    unittest.main()
