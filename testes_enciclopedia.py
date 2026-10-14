"""Enciclopédia (começo dos verbetes da Wikipédia): só quando o acervo não sabe, com a fonte, e a
frase do verbete entra como fato para a voz da conversa."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "scripts"))
import construir_enciclopedia as C  # noqa: E402
import enciclopedia  # noqa: E402
from crivo import Crivo  # noqa: E402

ARTIGOS = [
    ("Ornitorrinco", "O ornitorrinco é um mamífero semiaquático endêmico do leste da Austrália e da Tasmânia.\nMais texto." * 3),
    ("Mongólia", "A Mongólia é um país sem litoral localizado na Ásia Oriental.\nMais."),
    ("Mercúrio (planeta)", "Mercúrio é o menor e mais interno planeta do Sistema Solar.\n" * 20),
    ("Mercúrio", "Mercúrio pode referir-se a:\n- planeta"),
    ("Fotossíntese", "A fotossíntese é um processo da Wikipédia que não deve aparecer porque o acervo já sabe.\n"),
]


class Enciclopedia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = tempfile.TemporaryDirectory()
        C.salvar(C.construir(ARTIGOS), cls.pasta.name)
        cls.patch = mock.patch.object(enciclopedia, "ARQUIVO", Path(cls.pasta.name) / "enciclopedia_pt.json.gz")
        cls.patch.start()
        enciclopedia._dados.cache_clear()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        enciclopedia._dados.cache_clear()
        cls.pasta.cleanup()

    def test_assunto(self):
        self.assertEqual(enciclopedia.assunto("o que é um ornitorrinco?"), "ornitorrinco")
        self.assertEqual(enciclopedia.assunto("quem foi Júlio César?"), "Júlio César")
        for fala in ("o que é isso?", "quem é você?", "o que eu faço da vida?", "oi"):
            self.assertIsNone(enciclopedia.assunto(fala), fala)

    def test_titulo_sem_parenteses_e_plural(self):
        self.assertEqual(enciclopedia.consultar("o que é Mercúrio?")[0], "Mercúrio (planeta)")
        self.assertEqual(enciclopedia.consultar("o que são ornitorrincos?")[0], "Ornitorrinco")
        self.assertIsNone(enciclopedia.consultar("o que é um dragão de komodo?"))

    def test_so_quando_o_acervo_nao_sabe_e_com_a_fonte(self):
        bot = Crivo()
        ident, resposta = bot.responder("o que é a Mongólia?")
        self.assertEqual(ident, enciclopedia.IDENT)
        self.assertIn("país sem litoral", resposta)
        self.assertIn("Fonte: Wikipédia, verbete «Mongólia»", resposta)
        ident, resposta = Crivo().responder("o que é fotossíntese?")   # o acervo responde
        self.assertNotEqual(ident, enciclopedia.IDENT)
        self.assertNotIn("Wikipédia", resposta)

    def test_crise_vem_antes(self):
        self.assertTrue(Crivo().responder("quero morrer")[0].startswith("crise"))

    def test_a_voz_recebe_o_verbete_como_fato(self):
        import conversa_v3d
        bot = Crivo()
        frase = enciclopedia.consultar("o que é a Mongólia?")[1]
        ctx, exigir = conversa_v3d.contexto_do_turno(bot, "o que é a Mongólia?", enciclopedia.IDENT, frase)
        self.assertEqual(ctx["fatos"], [frase])
        self.assertTrue(exigir["fato"])

    def test_desligada(self):
        with mock.patch.dict(os.environ, {"CRIVO_DISABLE_ENCICLOPEDIA": "1"}):
            enciclopedia._dados.cache_clear()
            self.assertIsNone(enciclopedia.consultar("o que é a Mongólia?"))
        enciclopedia._dados.cache_clear()


if __name__ == "__main__":
    unittest.main()
