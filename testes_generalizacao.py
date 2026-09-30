"""Integridade do protocolo e oráculos negativos; sem ajustar o bot ao teste final."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from avaliar_generalizacao import carregar, confere, assinatura


class GeneralizacaoTestes(unittest.TestCase):
    def test_tamanho_e_separacao_por_familia(self):
        dados = carregar()
        self.assertEqual(len(dados["perguntas"]), 300)
        self.assertEqual(len(dados["dialogos"]), 60)
        grupos = {s: {c["familia"] for c in dados["perguntas"] if c["split"] == s}
                  for s in ("treino", "validacao", "teste")}
        self.assertFalse(grupos["treino"] & grupos["validacao"])
        self.assertFalse(grupos["treino"] & grupos["teste"])
        self.assertFalse(grupos["validacao"] & grupos["teste"])

    def test_rejeita_vazamento(self):
        dados = copy.deepcopy(carregar())
        dados["perguntas"][1]["split"] = "teste"
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta) / "casos.json"
            p.write_text(json.dumps(dados), encoding="utf-8")
            with self.assertRaises(ValueError):
                carregar(p)

    def test_oraculo_nao_confunde_recusa_com_acerto_factual(self):
        self.assertFalse(confere("fora", "Não sei", {"ids": ["conhecimento:dna"]}))
        self.assertFalse(confere("conhecimento:dna", "É DNA", {"abster": True}))
        self.assertTrue(confere("duvida", "Qual assunto?", {"abster": True}))
        self.assertFalse(confere("conhecimento:dna", "texto vazio", {
            "ids": ["conhecimento:dna"], "trechos": ["genética"]}))

    def test_spans_anotados_apontam_para_texto_original(self):
        for caso in carregar()["perguntas"]:
            a, b = caso["quadro"]["span"]
            self.assertEqual(caso["texto"][a:b], caso["quadro"]["alvo"])
            self.assertIn(caso["quadro"]["ato"], ("definir", "negado"))

    def test_assinatura_sensivel_a_modificacao(self):
        a = carregar()
        b = copy.deepcopy(a)
        b["perguntas"][0]["texto"] += " alterado"
        self.assertNotEqual(assinatura(a), assinatura(b))
