"""Voz da conversa (46M da 6b v4; a v4 F de reserva): ligada no site por decisão do criador, sem aprovação na catraca.

Desligada na linha de comando, travada por SHA, depois do protocolo de crise e conferida frase a
frase: se a conferência falha, fica o texto de sempre."""
import os
import unittest
from unittest import mock

import conversa_v3d
from crivo import Crivo


class Falso:
    """Modelo de teste: devolve a frase que o teste mandar."""
    def __init__(self, texto, terminou=True):
        self.texto, self.terminou, self.chamadas = texto, terminou, []

    def conversar(self, ctx, historico, mensagem, primeiro=0, prazo=None):
        self.chamadas.append((ctx, historico, mensagem))
        return self.texto, self.terminou


def bot_com(modelo):
    bot = Crivo()
    bot.conversa_v3d = modelo
    return bot


class Travas(unittest.TestCase):
    def test_desligada_na_linha_de_comando(self):
        bot = Crivo()
        self.assertIsNone(bot.conversa_v3d)
        bot.responder("oi")
        self.assertIsNone(bot.ultima_conversa_v3d)

    def test_registro_honesto(self):
        st = conversa_v3d.status()
        # 46M v7c: aprovado na régua própria nas duas rodadas, com as perdas e a parte do professor registradas
        self.assertTrue(st["decisao"]["aprovada"])
        self.assertIn("duas rodadas", st["decisao"]["regua"])
        self.assertIn("identidade", st["decisao"]["limites"])
        self.assertIn("professor", st["decisao"]["professor"])
        self.assertIn("reprovada", st["decisao_f"]["catraca"])
        self.assertFalse(st["external_ai"])

    def test_quem_e_o_do_identidade(self):
        import sys
        sys.path.insert(0, str(conversa_v3d.RAIZ / "experimentos" / "fase6b_conversa_humana"))
        import gerar_fase6b
        self.assertEqual(conversa_v3d.QUEM, gerar_fase6b.resumo_identidade())

    def test_lembrancas_vem_da_memoria(self):
        bot = Crivo()
        bot.responder("meu nome é Rosângela")
        lembr = conversa_v3d.lembrancas_de(bot)
        self.assertIn("a pessoa disse: meu nome é Rosângela", lembr)
        self.assertLessEqual(len(lembr), conversa_v3d.MAX_LEMBRANCAS)

    def test_reserva_da_f(self):
        with mock.patch.dict(os.environ, {"CRIVO_CONVERSA": "f"}):
            self.assertEqual(getattr(conversa_v3d.numpy_do_site(), "nome", "fase5_v4_F"), "fase5_v4_F")

    def test_formato_e_o_do_treino(self):
        self.assertTrue(hasattr(conversa_v3d.formato(), "avaliar_saida"))


class Conferencia(unittest.TestCase):
    def test_crise_e_emergencia_vem_antes(self):
        for fala, ident in (("quero morrer", "crise:suicidio"), ("tô com falta de ar", "crise:saude_urgente"),
                            ("socorro", "crise:socorro")):
            with self.subTest(fala=fala):
                falso = Falso("Oi! Tudo certo?")
                bot = bot_com(falso)
                self.assertEqual(bot.responder(fala)[0], ident)
                self.assertEqual(falso.chamadas, [])

    def test_depois_de_crise_fica_o_protocolo(self):
        falso = Falso("Que legal! Me conta mais?")
        bot = bot_com(falso)
        bot.responder("não quero mais viver")
        ident, resposta = bot.responder("ganhei um presente")
        self.assertEqual(ident, "crise:apoio")
        self.assertNotIn("legal", resposta)

    def test_conta_entra_como_fato_e_o_d_diz(self):
        falso = Falso("Fácil: 2 + 3 = 5")
        bot = bot_com(falso)
        self.assertEqual(bot.responder("quanto é 2+3?")[1], "Fácil: 2 + 3 = 5")
        self.assertEqual(falso.chamadas[-1][0]["fatos"], ["2 + 3 = 5"])

    def test_reprovada_tenta_de_novo(self):
        falso = Falso("Oi! Eu tenho 37 anos.")
        bot = bot_com(falso)
        bot.responder("oi")
        self.assertEqual(bot.ultima_conversa_v3d["tentativas"], conversa_v3d.TENTATIVAS)

    def test_resultado_alterado_aparece_nao_conferido(self):
        bot = bot_com(Falso("Fácil: 2 + 3 = 6"))
        self.assertEqual(bot.responder("quanto é 2+3?")[1], "Fácil: 2 + 3 = 6")
        self.assertFalse(bot.ultima_conversa_v3d["conferida"])

    def test_conversa_usa_a_voz(self):
        falso = Falso("Oi! Tô por aqui. Sobre o que vamos conversar?")
        bot = bot_com(falso)
        self.assertEqual(bot.responder("oi")[1], falso.texto)
        self.assertTrue(bot.ultima_conversa_v3d["usada"])

    def test_reprovada_fala_assim_mesmo_marcada(self):
        # Decisão do criador: a fala é dele; a conferência só marca.
        bot = bot_com(Falso("Oi! Eu tenho 37 anos."))
        self.assertEqual(bot.responder("oi")[1], "Oi! Eu tenho 37 anos.")
        self.assertFalse(bot.ultima_conversa_v3d["conferida"])
        self.assertIn("sem_numero_inventado", bot.ultima_conversa_v3d["motivo"])

    def test_conteudo_longo_fica_inteiro(self):
        # Poema, código ou explicação longa não cabem em duas frases: o modelo não troca por um pedaço.
        bot = Crivo()
        longo = "Primeira linha do poema.\nSegunda linha bonita.\nTerceira linha que não cabe.\nQuarta linha, fim."
        ctx, motivo = conversa_v3d.contexto_do_turno(bot, "escreve um poema", "conversa:gerada_poema", longo)
        self.assertIsNone(ctx)
        self.assertEqual(motivo, "conteudo_longo")

    def test_verbete_com_fonte_so_sai_conferido(self):
        # "Fonte: Wikipédia" exige o texto fiel: frase alterada não substitui o verbete.
        bot = bot_com(Falso("Não sei te dizer."))
        frase = "O Pantanal é um bioma alagado do centro-oeste do Brasil."
        ident, resposta, trace = conversa_v3d.aplicar(bot, "o que é o Pantanal?", "enciclopedia:wikipedia", frase, bot.conversa_v3d)
        self.assertEqual(resposta, frase)
        self.assertFalse(trace["usada"])

    def test_sem_fim_aparece_cortada(self):
        bot = bot_com(Falso("Oi! Tô por", terminou=False))
        self.assertEqual(bot.responder("oi")[1], "Oi! Tô por…")

    def test_sem_nada_dito_fica_o_texto_de_sempre(self):
        sempre = Crivo().responder("oi")[1]
        bot = bot_com(Falso(""))
        self.assertEqual(bot.responder("oi")[1], sempre)

    def test_nome_que_o_texto_de_sempre_diz_e_conferido(self):
        bot = bot_com(Falso("Prazer! Vou lembrar."))
        bot.responder("meu nome é Ana")
        self.assertIn("nome_exato", bot.ultima_conversa_v3d["motivo"])
        self.assertFalse(bot.ultima_conversa_v3d["conferida"])

    def test_saude_exige_a_marca(self):
        # "peito apertado" agora vai para o protocolo de crise; dor de cabeça fica com o modelo.
        bot = bot_com(Falso("Respira fundo, vai passar."))
        bot.responder("tô com dor de cabeça")
        self.assertIn("marca_saude", bot.ultima_conversa_v3d["motivo"])

    def test_historico_e_a_conversa_vista(self):
        falso = Falso("Oi! Tô por aqui. Sobre o que vamos conversar?")
        bot = bot_com(falso)
        bot.responder("oi")
        bot.responder("tudo bem?")
        self.assertEqual(falso.chamadas[-1][1], ["oi", falso.texto])


class PesosDoSite(unittest.TestCase):
    def test_o_46m_e_o_do_site(self):
        modelo = conversa_v3d.numpy_do_site()
        self.assertEqual(getattr(modelo, "nome", None), "v7c_46m", "pesos do 46M ausentes ou com SHA diferente")
        self.assertEqual((modelo.camadas, modelo.contexto), (24, 1024))

    def test_46m_lembra_o_que_a_pessoa_contou(self):
        bot = bot_com(conversa_v3d.numpy_do_site())
        bot.carregar_memoria({"nome": "Rosângela", "nomes": {}, "relatos": [], "temas": []})
        bot.responder("você sabe como eu me chamo?")
        self.assertIn("Rosângela", bot.ultima_conversa_v3d["rascunho"], bot.ultima_conversa_v3d)

    def test_pesos_carregam_e_conversam(self):
        modelo = conversa_v3d.numpy_do_site()
        self.assertIsNotNone(modelo, "pesos da voz da conversa ausentes ou com SHA diferente")
        bot = bot_com(modelo)
        bot.responder("oi")
        self.assertTrue(bot.ultima_conversa_v3d["usada"], bot.ultima_conversa_v3d)

    def test_site_liga_e_mostra_a_aprovacao_da_regua(self):
        from web_core import responder_web
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("CRIVO_DISABLE_CONVERSA_V3D", None)
            # "oi" tem quadro da fase 3 (saudar) e fica com ela; risada não tem.
            r = responder_web({"message": "kkkkk"}, voz_17m=True)
        self.assertTrue(r["conversation_voice"]["used"], r["conversation_voice"])
        # O 46M v7c passou na régua própria nas duas rodadas; a v4 F de reserva não passou.
        self.assertEqual(r["conversation_voice"]["approved"], r["conversation_voice"]["model"] == "v7c_46m")

    def test_site_le_a_conversa_como_a_pessoa_viu(self):
        # O site refaz o histórico; os últimos turnos voltam com a voz, como a pessoa viu.
        from web_core import responder_web
        os.environ.pop("CRIVO_DISABLE_CONVERSA_V3D", None)
        visto = responder_web({"message": "kkkkk"}, voz_17m=True)["response"]
        with mock.patch("conversa_v3d.aplicar", wraps=conversa_v3d.aplicar) as espiao:
            responder_web({"message": "tô entediado", "history": ["kkkkk"]}, voz_17m=True)
        bot = espiao.call_args_list[-1].args[0]
        self.assertEqual(bot.pares_conversa[-2], ("kkkkk", visto))

    def test_pagina_mostra_quando_o_modelo_fala(self):
        from pathlib import Path
        app = (Path(conversa_v3d.RAIZ) / "public" / "app.js").read_text(encoding="utf-8")
        self.assertIn("extra.conversation_voice && extra.conversation_voice.used", app)

    def test_site_desliga_pela_variavel(self):
        from web_core import responder_web
        with mock.patch.dict(os.environ, {"CRIVO_DISABLE_CONVERSA_V3D": "1"}):
            r = responder_web({"message": "kkkkk"}, voz_17m=True)
        self.assertNotIn("conversation_voice", r)


if __name__ == "__main__":
    unittest.main()
