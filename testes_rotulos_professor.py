"""Correção de rótulos do professor v7 (experimentos/v6_entendimento_20261019/rotulos_professor_v7.py): o arquivo de
correções tem só hashes (o texto do professor fica fora do repositório), as decisões são válidas e aplicar() tira,
troca e preserva como o v7e espera."""
import json
import re
import sys
import unittest
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "experimentos" / "v6_entendimento_20261019"
sys.path.insert(0, str(PASTA))
import rotulos_professor_v7 as R  # noqa: E402


class TestesRotulosProfessor(unittest.TestCase):
    def setUp(self):
        self.doc = R.carregar()

    def test_so_hashes_sem_texto_do_professor(self):
        self.assertEqual(self.doc["professor_arquivo_sha256"][:12], "b980bae0dc45")
        for k, c in self.doc["correcoes"].items():
            self.assertRegex(k, r"^[0-9a-f]{64}$")
            self.assertEqual(set(c), {"decisao", "motivo"})
        texto = R.ARQ.read_text(encoding="utf-8")
        self.assertNotIn("Você lembra que eu te disse", texto)

    def test_decisoes_validas_e_totais(self):
        cs = self.doc["correcoes"].values()
        for c in cs:
            self.assertTrue(c["decisao"] == "fora" or re.fullmatch(r"->[a-z_]+", c["decisao"]), c)
        self.assertEqual(self.doc["totais"]["fora"], sum(c["decisao"] == "fora" for c in cs))
        self.assertEqual(self.doc["totais"]["rotulo_trocado"], sum(c["decisao"] != "fora" for c in cs))
        self.assertEqual(sum(self.doc["totais"].values()), 601)

    def test_aplicar(self):
        falas = [{"situacao": "insulto", "fala": "péssimo pra caramba"},            # fora (sem alvo); aparece 2 vezes
                 {"situacao": "insulto", "fala": "péssimo pra caramba"},
                 {"situacao": "gosta", "fala": "Admiro tu, sabe?"},                 # muda para elogio_crivo
                 {"situacao": "insulto", "fala": "Você é um lixo andando"}]          # fica
        saida, rel = R.aplicar(falas)
        self.assertEqual([x["fala"] for x in saida], ["Admiro tu, sabe?", "Você é um lixo andando"])
        self.assertEqual(saida[0]["situacao"], "elogio_crivo")
        self.assertEqual(saida[0]["situacao_professor"], "gosta")
        self.assertEqual((rel["fora"], rel["rotulo_trocado"]), (2, 1))
        self.assertEqual(R.chave("cena:gosta", "x"), R.chave("gosta", "x"))

    def test_manifesto_v7e_confere(self):
        m = json.loads((PASTA / "manifesto_v7e.json").read_text(encoding="utf-8"))
        import hashlib
        for nome, arq in (("rotulos_professor_v7_sha256", PASTA / "rotulos_professor_v7.py"),
                          ("correcoes_professor_v7_sha256", R.ARQ)):
            self.assertEqual(m[nome], hashlib.sha256(arq.read_bytes()).hexdigest(), nome)


if __name__ == "__main__":
    unittest.main()
