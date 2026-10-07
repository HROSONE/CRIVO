"""Codificador de sentido (codificador_sentido.py): o Transformer próprio como
traço da busca."""
import unittest

try:
    import numpy  # noqa: F401
    TEM_NUMPY = True
except ImportError:
    TEM_NUMPY = False


@unittest.skipUnless(TEM_NUMPY, "o codificador roda em NumPy")
class CodificadorSentido(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from codificador_sentido import codificador
        cls.cod = codificador()

    def test_aprovado_e_sem_pesos_externos(self):
        self.assertTrue(self.cod.disponivel, self.cod.motivo)
        self.assertTrue(self.cod.meta["controle"]["aprovado"])
        self.assertFalse(self.cod.meta["pesos_externos"])

    def test_acervo_e_lote_vazios(self):
        self.assertEqual(self.cod.codificar([], "pergunta").shape[0], 0)
        self.assertEqual(self.cod.vetores_fatos([]).shape[0], 0)
        from types import SimpleNamespace
        from busca_semantica import BuscaSemantica
        comp = SimpleNamespace(itens={}, aliases={})
        busca = BuscaSemantica(comp)
        self.assertIsNone(busca.proximidades("Qual a capital?"))
        self.assertEqual(busca.buscar("Qual a capital?"), [])

    def test_vetores_normalizados(self):
        v = self.cod.codificar(["Quem pintou a Mona Lisa?", "O que é fotossíntese?"], "pergunta")
        for linha in v:
            self.assertAlmostEqual(float((linha * linha).sum()), 1.0, places=4)

    def test_todo_fato_do_acervo_tem_vetor_pre_calculado(self):
        # Catálogo mudou? Rode scripts/instalar_sentido.py.
        from busca_semantica import fatos_do_acervo
        from codificador_sentido import chave
        from crivo import Crivo
        faltam = [t for _, _, t in fatos_do_acervo(Crivo().compositor) if chave(t) not in self.cod._cache]
        self.assertEqual(faltam, [], "%d fatos sem vetor; rode scripts/instalar_sentido.py" % len(faltam))

    def test_pergunta_fica_mais_perto_do_fato_que_responde(self):
        fatos = ["Leonardo da Vinci pintou a Mona Lisa e A Última Ceia.",
                 "A fotossíntese transforma luz, água e gás carbônico em açúcar e oxigênio."]
        v = self.cod.codificar(fatos, "fato")
        q = self.cod.codificar(["Como as plantas fabricam o próprio alimento?"], "pergunta")[0]
        self.assertGreater(float(v[1] @ q), float(v[0] @ q))

    def test_busca_usa_o_traco_e_pode_ser_desligada(self):
        from crivo import Crivo
        from leitura_ficha import busca_aprendida
        busca = busca_aprendida(Crivo().compositor)
        self.assertIsNotNone(busca.proximidades("Quem pintou a Mona Lisa?"))
        busca.usar_denso = False
        try:
            self.assertIsNone(busca.proximidades("Quem pintou a Mona Lisa?"))
        finally:
            busca.usar_denso = True


if __name__ == "__main__":
    unittest.main()
