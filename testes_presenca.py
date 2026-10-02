"""Presença na conversa: refletir, variar, lembrar e retomar."""
import json
import random
import unittest
from pathlib import Path

from presenca import Perfil, Variacao, despedida, para_voce, verbo_para_voce

try:
    import numpy  # noqa: F401
    from analisador_frases import analisador
    LIGADO = analisador().disponivel
except ImportError:
    LIGADO = False

LIMIARES = json.loads((Path(__file__).parent / "avaliacoes" / "presenca_v1" / "limiares.json")
                      .read_text(encoding="utf-8"))


class TestesConjugacao(unittest.TestCase):
    def test_primeira_pessoa_vira_voce(self):
        casos = {("perdi", "perder"): "perdeu", ("dormi", "dormir"): "dormiu", ("estudei", "estudar"): "estudou",
                 ("fui", "ir"): "foi", ("estou", "estar"): "está", ("tenho", "ter"): "tem",
                 ("acho", "achar"): "acha", ("vi", "ver"): "viu", ("estava", "estar"): "estava"}
        for (forma, lema), esperado in casos.items():
            with self.subTest(forma=forma):
                self.assertEqual(verbo_para_voce(forma, lema), esperado)


    def test_preterito_pela_grafia_futuro_pelo_lema_e_presente_comum(self):
        for forma, lema, esperado in (("peguei", "peguer", "pegou"), ("fiquei", "", "ficou"),
                                      ("comecei", "começar", "começou"), ("parei", "par", "parou"),
                                      ("comerei", "comer", "comerá"), ("gosto", "", "gosta"),
                                      ("consigo", "conseguir", "consegue")):
            self.assertEqual(verbo_para_voce(forma, lema), esperado, forma)

    def test_consigo_separado_pelo_tokenizador_volta_a_ser_verbo(self):
        from analisador_frases import Palavra
        palavras = [Palavra(1, "Eu", "eu", "PRON", 4, "nsubj"), Palavra(2, "não", "não", "ADV", 4, "advmod"),
                    Palavra(3, "com", "com", "ADP", 4, "case"), Palavra(4, "si", "se", "PRON", 0, "root"),
                    Palavra(5, "estudar", "estudar", "VERB", 4, "xcomp")]
        self.assertEqual(para_voce(palavras), "você não consegue estudar")
        palavras[0] = Palavra(1, "Ele", "ele", "PRON", 4, "nsubj")
        self.assertNotIn("consegue", para_voce(palavras[:1] + palavras[2:]))


class TestesVariacaoEPerfil(unittest.TestCase):
    def test_variacao_nao_repete_enquanto_ha_opcoes(self):
        v = Variacao(random.Random(1))
        escolhas = [v.escolher(("a", "b", "c")) for _ in range(3)]
        self.assertEqual(sorted(escolhas), ["a", "b", "c"])

    def test_marcante_prefere_saude_e_coisas_ruins(self):
        p = Perfil()
        p.anotar("pizza", "pos", "você comeu pizza")
        p.turno = 1
        p.anotar("gripe", "saude", "sua mãe está gripada", "sua mãe")
        p.turno = 2
        p.anotar("filme", "neutro", "")
        self.assertEqual(p.marcante()[1], "gripe")

    def test_despedida_lembra_o_que_foi_contado(self):
        class Bot:
            pass
        bot = Bot()
        bot.perfil = Perfil()
        bot.perfil.anotar("gripe", "saude", "sua mãe está gripada", "sua mãe")
        bot.conversacao = type("C", (), {"dialogo": type("D", (), {"dados": {"nome": "Ana"}})()})()
        texto = despedida(bot, Variacao(random.Random(0)), "tchau")
        self.assertIn("Ana", texto)
        self.assertIn("sua mãe", texto)


@unittest.skipUnless(LIGADO, "analisador de frases desligado (sem NumPy ou sem pesos)")
class TestesConversa(unittest.TestCase):
    def test_catraca(self):
        from scripts.avaliar_presenca import avaliar
        for conjunto in ("dev", "retido", "retido2"):
            with self.subTest(conjunto=conjunto):
                resumo, falhas, _ = avaliar(conjunto)
                if conjunto.startswith("retido"):
                    falhas = "(retido: detalhes não exibidos)"
                limite = LIMIARES[conjunto]
                self.assertGreaterEqual(resumo["turnos_ok"], limite["turnos_ok_min"], falhas)
                self.assertLessEqual(resumo["genericas"], limite["genericas_max"], resumo)
                self.assertLessEqual(resumo["repeticoes"], limite["repeticoes_max"], resumo)
                self.assertLessEqual(resumo["mesma_estrutura"], limite["mesma_estrutura_max"], resumo)
                self.assertLessEqual(resumo["fatos_novos"], limite["fatos_novos_max"], falhas)

    def test_catraca_dialogo_unico(self):
        from scripts.avaliar_presenca import avaliar
        limiares = json.loads((Path(__file__).parent / "avaliacoes" / "dialogo_unico_v1" / "limiares.json")
                              .read_text(encoding="utf-8"))
        for conjunto in ("dev", "retido"):
            with self.subTest(conjunto=conjunto):
                resumo, falhas, _ = avaliar(conjunto, bateria="dialogo_unico_v1")
                if conjunto == "retido":
                    falhas = "(retido: detalhes não exibidos)"
                limite = limiares[conjunto]
                self.assertGreaterEqual(resumo["turnos_ok"], limite["turnos_ok_min"], falhas)
                for chave in ("genericas", "repeticoes", "mesma_estrutura", "fatos_novos"):
                    self.assertLessEqual(resumo[chave], limite[chave + "_max"], resumo)

    def test_reflete_lembra_nome_e_retoma(self):
        from crivo import Crivo
        bot = Crivo()
        bot.conversacao.sorteio.seed(3)
        self.assertIn("você perdeu o ônibus", bot.responder("eu perdi o ônibus hoje")[1])
        bot.responder("meu cachorro latiu a noite toda")
        self.assertIn("Thor", bot.responder("ele se chama Thor")[1])
        bot.responder("obrigado")
        self.assertEqual(bot.responder("e aí, tudo bem?")[0], "social:retomada")

    def test_nao_entendi_no_meio_da_conversa_retoma_o_assunto(self):
        from crivo import Crivo
        bot = Crivo()
        bot.responder("fiz um bolo de chocolate")
        ident, resposta = bot.responder("xablau tremeluzente")
        self.assertEqual(ident, "conversa:esclarecer")
        self.assertNotIn("ajuda", resposta)


if __name__ == "__main__":
    unittest.main()
