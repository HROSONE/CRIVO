"""Quadro único de interpretação e aproximação de uma palavra por vetores."""
import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from vetores_palavras import VetoresPalavras


def criar_vetores(pasta, pares, controle_ok=True):
    import numpy as np
    vocab, linhas = [], []
    rng = np.random.default_rng(0)
    for a, b in pares:
        base = rng.normal(size=8)
        for palavra in (a, b):
            vocab.append(palavra)
            linhas.append(base + rng.normal(scale=0.05, size=8))
    for k in range(40):
        vocab.append("ruido%d" % k)
        linhas.append(rng.normal(size=8))
    m = np.array(linhas)
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    np.save(Path(pasta) / "vetores.npy", m.astype(np.float16))
    (Path(pasta) / "vocabulario.json").write_text(json.dumps(vocab), encoding="utf-8")
    controle = ({"pares_equivalentes": 0.7, "pares_aleatorios": 0.02, "pares_antonimos": 0.3,
                 "pares_avaliados": 12}
                if controle_ok else {"pares_equivalentes": 0.58, "pares_aleatorios": 0.0,
                                     "pares_antonimos": 0.6, "pares_avaliados": 12})
    (Path(pasta) / "treino.json").write_text(json.dumps({"controle": controle}), encoding="utf-8")


class TestesQuadro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Crivo().compositor

    def test_intencoes_e_assunto(self):
        casos = {
            "Europa tem oceano?": ("propriedade", "mundo_europa"),
            "Quantas luas tem Júpiter?": ("quantidade", "mundo_jupiter"),
            "Qual a temperatura do Sol?": ("quantidade", "ceu_sol"),
            "Qual a idade do Sistema Solar?": ("tempo", "sistema_solar"),
            "O que deixa Marte vermelho?": ("causa", "mundo_marte"),
            "De que maneira o eixo de Urano afeta suas estações?": ("mecanismo", "mundo_urano"),
            "Por que Vênus é mais quente que Mercúrio?": ("comparacao", "mundo_venus"),
        }
        for pergunta, (intencao, assunto) in casos.items():
            with self.subTest(pergunta=pergunta):
                quadro = self.c.interpretar(pergunta)
                self.assertEqual((quadro.intencao, quadro.assunto), (intencao, assunto))
                self.assertEqual(quadro.recusa, "")

    def test_motivos_de_recusa(self):
        casos = {
            "Europa não tem oceano?": "negacao_ou_qualificador",
            "Como funciona um planeta fictício?": "negacao_ou_qualificador",
            "Por que a memória ajuda o sono?": "relacao_entre_conceitos",
            "Qual planeta é o maior de todos?": "superlativo",
        }
        for pergunta, motivo in casos.items():
            with self.subTest(pergunta=pergunta):
                self.assertEqual(self.c.interpretar(pergunta).recusa, motivo)

    def test_nome_proprio_sem_plural_e_posse(self):
        self.assertEqual(self.c.interpretar("Quantas luas tem Júpiter?").assunto, "mundo_jupiter")
        quadro = self.c.interpretar("Por que Urano tem estações extremas?")
        self.assertEqual(quadro.outros, ())
        self.assertEqual(quadro.recusa, "")

    def test_quadro_registrado_no_historico(self):
        bot = Crivo()
        bot.responder("Europa tem oceano?")
        self.assertEqual(bot.historico[-1]["quadro_factual"]["assunto"], "mundo_europa")

    def test_fichas_de_busca_nao_alteram_definicoes_antigas(self):
        self.assertEqual(Crivo().responder("O que é o Sol?")[0], "sol")
        self.assertIn("5.500 °C", Crivo().responder("Qual a temperatura do Sol?")[1])


class TestesLexico(unittest.TestCase):
    def test_sinonimo_listado_e_aproximado_com_aviso(self):
        resposta = Crivo().responder("Netuno tem ventos fortes?")[1]
        self.assertIn("Entendi “fortes” como próximo de “intensos”", resposta)

    def test_antonimo_nunca_e_aproximado(self):
        from lexico_pt import LexicoPT
        lexico = LexicoPT()
        self.assertTrue(lexico.antonimo("fortes", "fracos"))
        self.assertTrue(lexico.sinonimo("fortes", "intensos"))
        self.assertNotIn("Entendi", Crivo().responder("Netuno tem ventos fracos?")[1])

    def test_lexico_tem_reservados_sem_palavras_de_treino(self):
        import json
        from lexico_pt import CAMINHO
        dados = json.loads(CAMINHO.read_text(encoding="utf-8"))
        palavras = lambda parte: {w for k in dados[parte] for _, a, b in dados[parte][k] for w in (a, b)}
        self.assertFalse(palavras("treino") & palavras("reservados"))


try:
    import numpy  # noqa: F401
    TEM_NUMPY = True
except ImportError:
    TEM_NUMPY = False


@unittest.skipUnless(TEM_NUMPY, "vetores de palavras exigem NumPy")
class TestesVetores(unittest.TestCase):
    def test_vetores_do_repositorio_com_antonimos_proximos_ficam_desligados(self):
        # O treino de 100 mil artigos aproximou antônimos tanto quanto
        # sinônimos; sem a medida de antônimos, os vetores não são usados.
        self.assertFalse(VetoresPalavras().disponivel)

    def test_vetores_sem_controle_de_qualidade_ficam_desligados(self):
        with tempfile.TemporaryDirectory() as pasta:
            criar_vetores(pasta, [("fortes", "intensos")], controle_ok=False)
            self.assertFalse(VetoresPalavras(pasta).disponivel)
        with tempfile.TemporaryDirectory() as pasta:
            self.assertFalse(VetoresPalavras(pasta).disponivel)

    def test_uma_palavra_aproximada_com_aviso(self):
        with tempfile.TemporaryDirectory() as pasta:
            criar_vetores(pasta, [("fortes", "intensos"), ("chove", "chuva")])
            bot = Crivo()
            bot.compositor.vetores = VetoresPalavras(pasta)
            self.assertTrue(bot.compositor.vetores.disponivel)
            ident, resposta = bot.responder("Netuno tem ventos fortes?")
            self.assertIn("Entendi “fortes” como próximo de “intensos”", resposta)
            self.assertIn("ventos intensos", resposta)
            # Duas palavras sem correspondência exata: nada é aproximado.
            self.assertNotIn("Entendi", bot.responder("Netuno tem ventos fortes azuis?")[1])
            # Qualificador bloqueado continua bloqueado.
            self.assertNotIn("Entendi", bot.responder("Netuno tem ventos fortes mágicos?")[1])


if __name__ == "__main__":
    unittest.main()
