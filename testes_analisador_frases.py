"""Analisador de frases: tokenização, árvore máxima, controle de qualidade,
paridade torch × NumPy e o notebook do Colab. Não exige pesos treinados."""
import itertools
import json
import tempfile
import unittest
from pathlib import Path

import analisador_frases as af

try:
    import numpy as np
except ImportError:
    np = None
try:
    import torch  # noqa: F401
except ImportError:
    torch = None

RAIZ = Path(__file__).resolve().parent


class TestesTokenizador(unittest.TestCase):
    def test_contracoes_cliticos_e_fala_informal(self):
        t = af.Tokenizador({"do": ("de", "o"), "na": ("em", "a")})
        self.assertEqual(t("Tô na casa do João, abriu-se a porta? pra mim 3,5 guarda-chuva"),
                         ["Estou", "em", "a", "casa", "de", "o", "João", ",", "abriu", "se", "a", "porta",
                          "?", "para", "mim", "3,5", "guarda-chuva"])

    def test_regra_de_lema_ida_e_volta(self):
        for forma, lema in (("abriu", "abrir"), ("meninas", "menina"), ("é", "ser"), ("PT", "PT")):
            self.assertEqual(af.aplicar_regra_lema(forma, af.regra_lema(forma, lema)), lema.lower())


@unittest.skipUnless(np is not None, "NumPy necessário")
class TestesArvore(unittest.TestCase):
    def test_arvore_maxima_igual_a_forca_bruta(self):
        rng = np.random.default_rng(7)
        for _ in range(150):
            n = int(rng.integers(2, 7))
            S = rng.normal(size=(n, n))
            pais = af.arvore_maxima(S, np)
            self.assertIsNone(af._ciclo(list(pais)))
            self.assertEqual(sum(1 for d in range(1, n) if pais[d] == 0), 1)
            melhor = max(
                sum(S[d, h[d - 1]] for d in range(1, n))
                for h in itertools.product(range(n), repeat=n - 1)
                if all(h[d - 1] != d for d in range(1, n)) and list(h).count(0) == 1
                and af._ciclo([-1] + list(h)) is None)
            self.assertAlmostEqual(sum(S[d, pais[d]] for d in range(1, n)), melhor)

    def test_sem_pesos_ou_abaixo_do_minimo_fica_desligado(self):
        with tempfile.TemporaryDirectory() as pasta:
            self.assertFalse(af.AnalisadorFrases(pasta).disponivel)
            np.savez(Path(pasta) / "modelo.npz", x=np.zeros(1))
            meta = {"avaliacao": {"teste": {"upos": 0.95, "uas": 0.5, "las": 0.4}}, "contracoes": {}}
            (Path(pasta) / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
            a = af.AnalisadorFrases(pasta)
            self.assertFalse(a.disponivel)
            self.assertIn("controle de qualidade", a.motivo)
            self.assertIn("desligado", af.explicar("A menina abriu o guarda-chuva.", a))


@unittest.skipUnless(np is not None and torch is not None, "PyTorch necessário (treino)")
class TestesParidadeBiafim(unittest.TestCase):
    def test_execucao_numpy_reproduz_o_torch(self):
        import sys
        sys.path.insert(0, str(RAIZ / "scripts"))
        import treinar_analisador_biafim as tb
        frases = [[{"forma": f, "lema": f.lower(), "classe": c, "pai": p, "ligacao": l}
                   for f, c, p, l in s] for s in (
            [("A", "DET", 2, "det"), ("menina", "NOUN", 3, "nsubj"), ("abriu", "VERB", 0, "root"),
             ("o", "DET", 5, "det"), ("guarda-chuva", "NOUN", 3, "obj"), (".", "PUNCT", 3, "punct")],
            [("Choveu", "VERB", 0, "root"), ("ontem", "ADV", 1, "advmod")],
        )]
        vetores = (["a", "menina", "o", "choveu"], np.random.default_rng(0).normal(size=(4, 64)).astype(np.float32))
        v = tb.Vocab(frases, vetores, min_freq=1)
        torch.manual_seed(0)
        modelo = tb.Biafim(v)
        with torch.no_grad():  # pesos biafins não nulos para a paridade ser informativa
            for p in (modelo.U_arco, modelo.u_arco, modelo.U_rot):
                p.normal_(0, 0.1)
        modelo.eval()
        pesos, meta = tb.exportar(modelo, v, {"contracoes": {}, "lemas_fixos": {}})
        original = af.carregar_vetores
        af.carregar_vetores = lambda np_, pasta=None: vetores
        try:
            numpy_ = af.AnalisadorBiafim.de_pesos(pesos, meta)
        finally:
            af.carregar_vetores = original
        self.assertLess(tb.conferir_paridade(modelo, numpy_, frases, v, "cpu"), 1e-4)
        palavras = numpy_.analisar_formas(["A", "menina", "abriu", "o", "guarda-chuva", "."])
        self.assertEqual(len(palavras), 6)
        self.assertEqual(sum(1 for p in palavras if p.pai == 0), 1)


class TestesNotebookEOrigem(unittest.TestCase):
    def test_notebook_valido_e_aponta_para_arquivos_do_repositorio(self):
        nb = json.loads((RAIZ / "notebooks" / "treinar_analisador_colab.ipynb").read_text(encoding="utf-8"))
        codigo = "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
        self.assertIn("scripts/treinar_analisador_biafim.py", codigo)
        self.assertIn("dados/origem_ud_bosque.json", codigo)
        self.assertTrue((RAIZ / "scripts" / "treinar_analisador_biafim.py").exists())
        self.assertEqual(nb["metadata"]["accelerator"], "GPU")

    def test_origem_fixada_com_licenca_e_sha(self):
        origem = json.loads((RAIZ / "dados" / "origem_ud_bosque.json").read_text(encoding="utf-8"))
        self.assertEqual(origem["licenca"], "CC BY-SA 4.0")
        self.assertEqual(len(origem["commit"]), 40)
        self.assertEqual(len(origem["sha256"]), 3)
        self.assertIn(origem["commit"], origem["url_base"])



@unittest.skipUnless(np is not None, "NumPy necessário")
class TestesModeloDoRepositorio(unittest.TestCase):
    def test_modelo_publicado_passa_no_controle_e_analisa_o_exemplo(self):
        a = af.AnalisadorFrases()
        self.assertTrue(a.disponivel, a.motivo)
        palavras = {p.forma: p for p in a.analisar("A menina abriu o guarda-chuva porque começou a chover.")}
        abriu = palavras["abriu"]
        self.assertEqual((abriu.pai, abriu.lema), (0, "abrir"))
        self.assertEqual(palavras["menina"].ligacao, "nsubj")
        self.assertEqual(palavras["guarda-chuva"].ligacao, "obj")
        self.assertEqual(palavras["porque"].ligacao, "mark")


if __name__ == "__main__":
    unittest.main()
