"""Memória entre conversas (opcional, guardada só no navegador) e avaliação humana."""
import json
import tempfile
import unittest

from scripts.analisar_avaliacoes import resumir
from web_core import PedidoInvalido, responder_web

try:
    import numpy  # noqa: F401
    from analisador_frases import analisador
    LIGADO = analisador().disponivel
except ImportError:
    LIGADO = False


class TestesMemoriaNavegador(unittest.TestCase):
    def test_sem_memoria_a_resposta_nao_muda_de_formato(self):
        self.assertNotIn("memory", responder_web({"message": "oi"}))

    def test_memoria_invalida_e_recusada(self):
        for memoria in ([], {"x": 1}, {"nome": ""}, {"nome": "a" * 41}, {"relatos": ["x"] * 9},
                        {"temas": [["gripe", "mau", ""]]}, {"nomes": {"a": 3}}):
            with self.subTest(memoria=str(memoria)[:40]):
                with self.assertRaises(PedidoInvalido):
                    responder_web({"message": "oi", "memory": memoria})

    def test_nome_e_apelido_voltam_na_proxima_visita(self):
        r = responder_web({"message": "ele se chama Thor", "history": ["meu nome é Ana", "meu cachorro latiu a noite toda"],
                           "memory": {}})
        memoria = r["memory"]
        self.assertEqual(memoria["nome"], "Ana")
        self.assertEqual(memoria["nomes"].get("cachorro"), "Thor")
        json.dumps(memoria)  # serializável para o navegador
        oi = responder_web({"message": "oi", "memory": memoria})
        self.assertEqual(oi["id"], "social:oi")
        self.assertIn("Oi de novo, Ana", oi["response"])
        self.assertIn("Thor", oi["response"])

    @unittest.skipUnless(LIGADO, "analisador de frases desligado")
    def test_relato_de_outra_visita_responde_sem_virar_palpite(self):
        memoria = {"relatos": ["minha mãe está gripada", "meu cachorro latiu a noite toda"]}
        r = responder_web({"message": "o que eu te contei da minha mãe?", "memory": memoria})
        self.assertIn("sua mãe está gripada", r["response"])
        r = responder_web({"message": "por que ele latiu?", "memory": memoria})
        self.assertNotIn("palpite", r["response"])


class TestesAvaliacaoHumana(unittest.TestCase):
    def test_resumo_por_tipo(self):
        dados = {"avaliacoes": [{"id": "nocao:observacao", "nota": 1}, {"id": "nocao:reacao", "nota": -1},
                                {"id": "fora", "nota": -1}, {"id": "memoria:relato", "nota": 1}]}
        resumo, ruins = resumir(dados)
        self.assertEqual(resumo["avaliacoes"], 4)
        self.assertEqual(resumo["aprovacao"], 0.5)
        self.assertEqual(resumo["por_tipo"]["nocao"], {"boas": 1, "ruins": 1, "aprovacao": 0.5})
        self.assertEqual(len(ruins), 2)


if __name__ == "__main__":
    unittest.main()
