"""Testes do pensador v2 no chat (pensador_crivo.py + raciocinio_ativo)."""
import json
import os
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "experimentos" / "pensador_20261012"))
import pensador_crivo as PN  # noqa: E402
from raciocinio_ativo import RaciocinioAtivo, ler_literal, ler_premissa  # noqa: E402


class Pesos(unittest.TestCase):
    def test_arquivo_conferido(self):
        self.assertTrue(PN.status()["ligado"], "pesos do pensador ausentes ou com SHA diferente")
        self.assertEqual(PN.status()["passo"], 13000)

    def test_acerta_nos_conjuntos_congelados(self):
        import gerar_pensador as G
        C = json.loads((RAIZ / "experimentos/pensador_20261012/conjuntos_pensador.json").read_text())
        ok = 0
        casos = C["blind_iid"][:60]
        for pr in casos:
            r = PN.pensar(G.para_premissas(pr), G.literal(*pr["pergunta"]))
            if pr["status"] == "indeterminado":
                ok += r["status"] == "indeterminado"
            else:
                ok += r["status"] == pr["status"] and r["prova"] is not None and G.conferir_prova(pr, r["status"], r["prova"])
        self.assertGreaterEqual(ok / len(casos), 0.95)


class NoChat(unittest.TestCase):
    def concluir(self, texto):
        r = RaciocinioAtivo()
        ident, resposta, _, _ = r.preparar(texto, 1)
        return r.ultimo, resposta

    def test_pensador_responde_e_e_conferido(self):
        d, resposta = self.concluir("Considere estas premissas: chove; se chove, então a rua molha; "
                                    "se a rua molha, então o chão escorrega; posso concluir que o chão escorrega?")
        self.assertEqual(d["status"], "sustentado")
        self.assertTrue(d["pensador"]["usado"])
        self.assertIn("meu pensador", resposta)
        self.assertEqual(len(d["provas"]), 3)

    def test_quando_ele_erra_fica_o_enumerador(self):
        # O treino quase não tem "se A então B; não B" (só deriva para frente): o pensador erra, a resposta não.
        d, resposta = self.concluir("Considere estas premissas: se estudo, então passo; não passo; posso concluir que estudo?")
        self.assertEqual(d["status"], "refutado")
        self.assertFalse(d["pensador"]["usado"])
        self.assertNotIn("meu pensador", resposta)
        self.assertTrue(resposta.startswith("Não:"))

    def test_proposta_errada_nunca_entra(self):
        import pensador_crivo
        original = pensador_crivo.pensar
        pensador_crivo.pensar = lambda p, a: {"status": "sustentado", "prova": [0], "voltas": 4}
        try:
            d, resposta = self.concluir("Considere estas premissas: se chove, então molha; posso concluir que molha?")
        finally:
            pensador_crivo.pensar = original
        self.assertEqual(d["status"], "indeterminado")
        self.assertFalse(d["pensador"]["usado"])

    def test_desligado(self):
        os.environ["CRIVO_DISABLE_PENSADOR"] = "1"
        PN._pesos.cache_clear()
        try:
            d, resposta = self.concluir("Considere estas premissas: chove; se chove, então molha; posso concluir que molha?")
        finally:
            del os.environ["CRIVO_DISABLE_PENSADOR"]
            PN._pesos.cache_clear()
        self.assertEqual(d["status"], "sustentado")
        self.assertFalse(d["pensador"]["usado"])

    def test_para_problema(self):
        ps = [ler_premissa("chove"), ler_premissa("se chove ou neva, então a estrada fecha")]
        pr = PN.para_problema(ps, ler_literal("a estrada fecha"))
        self.assertEqual(pr["atomos"], 3)
        self.assertEqual(pr["premissas"][1]["op"], "ou")
        self.assertIsNone(PN.para_problema(ps, ler_literal("faz sol")))


if __name__ == "__main__":
    unittest.main()
