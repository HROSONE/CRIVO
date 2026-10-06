"""Busca aprendida (busca_semantica.py): acha o fato pelo que a pergunta pede."""
import json
import tempfile
import unittest
from pathlib import Path

from busca_semantica import CAMINHO_MODELO, TRACOS, BuscaSemantica
from composicao_textual import CompositorTextual
from crivo import Crivo
from leitura_ficha import busca_aprendida

RAIZ = Path(__file__).resolve().parent


class TestesBuscaSemantica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.comp = Crivo().compositor
        cls.busca = busca_aprendida(cls.comp)

    def test_modelo_aprovado_e_so_com_evidencias(self):
        meta = json.loads(CAMINHO_MODELO.read_text(encoding="utf-8"))
        self.assertTrue(meta["controle"]["aprovado"])
        self.assertEqual(meta["tracos"], list(TRACOS))
        self.assertTrue(self.busca.aprendida)
        # O modelo pesa evidências, não decora ids nem palavras.
        self.assertEqual(len(meta["pesos"]), len(TRACOS))

    def test_pergunta_acha_o_fato_que_responde_e_nao_a_definicao(self):
        p, ident, i = self.busca.buscar("Quantos códons existem no código genético?", k=1)[0]
        self.assertEqual(ident, "mundo_codigo_genetico")
        self.assertIn("64 códons", self.comp.itens[ident]["fatos"][i]["texto"])

    def test_assunto_dado_restringe_a_ficha(self):
        # "igual em todos" → "quase universal": outras palavras, mesmo sentido.
        q, ficha = "O código genético é igual em todos os seres vivos?", "mundo_codigo_genetico"
        r = self.busca.buscar(q, k=3, assuntos={ficha})
        self.assertTrue(r)
        self.assertTrue(all(ident == ficha for _, ident, _ in r))
        self.assertIn("universal", self.comp.itens[ficha]["fatos"][r[0][2]]["texto"])
        self.assertAlmostEqual(sum(p for p, _, _ in self.busca.buscar(q, k=99, assuntos={ficha})), 1.0, places=6)

    def test_fato_novo_e_achado_sem_retreinar(self):
        dados = {"versao": 1, "fontes": {
            "ref": {"titulo": "Catálogo de teste", "url": "https://example.org/catalogo"}}, "itens": [
            {"id": "neril", "nome": "Neril", "fatos": [
                {"texto": "Neril é um peixe fictício do lago Torvo.", "papel": "definicao", "fonte": "ref"},
                {"texto": "Um Neril adulto vive cerca de 12 anos.", "papel": "detalhe", "fonte": "ref"},
                {"texto": "O Neril foi descrito por Ana Lima em 1931.", "papel": "detalhe", "fonte": "ref"}]},
            {"id": "torvo", "nome": "lago Torvo", "fatos": [
                {"texto": "O lago Torvo é um lago fictício de montanha.", "papel": "definicao", "fonte": "ref"}]}]}
        with tempfile.TemporaryDirectory() as pasta:
            m = CompositorTextual([], Path(pasta) / "ausente.json", lambda _: None, curriculo_mundo=dados)
            b = BuscaSemantica(m, vetores=self.busca.vetores)
            self.assertTrue(b.aprendida)
            for q, esperado in (("Quantos anos vive um Neril?", 1), ("Quem descreveu o Neril?", 2),
                                ("Quando o Neril foi descrito?", 2), ("O que é Neril?", 0)):
                with self.subTest(pergunta=q):
                    self.assertEqual(b.buscar(q, k=1)[0][1:], ("neril", esperado))

    def test_sem_modelo_a_ordem_e_a_do_bm25(self):
        b = BuscaSemantica(self.comp, caminho_modelo=RAIZ / "nao-existe.json", vetores=self.busca.vetores)
        self.assertFalse(b.aprendida)
        self.assertEqual({t for t, p in b.pesos.items() if p}, {"bm"})

    def test_catraca_teste_congelado_v2(self):
        # Só agregados. No treino (05/10): dentro da ficha 0,667 e acervo@5 0,979;
        # só BM25: 0,292 e 0,458.
        casos = json.loads((RAIZ / "avaliacoes/leitura_ficha_v2/teste.json").read_text(encoding="utf-8"))["casos"]
        casos = [c for c in casos if c["fato"] is not None and c["assunto"] in self.comp.itens]
        dentro = top5 = 0
        for c in casos:
            alvo = (c["assunto"], c["fato"])
            top5 += alvo in [r[1:] for r in self.busca.buscar(c["pergunta"], k=5)]
            dentro += self.busca.buscar(c["pergunta"], k=1, assuntos={c["assunto"]})[0][2] == c["fato"]
        self.assertGreaterEqual(dentro, 32)  # de 48
        self.assertGreaterEqual(top5, 46)


if __name__ == "__main__":
    unittest.main()
