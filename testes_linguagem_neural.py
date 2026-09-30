"""Aprendizado de ordem, preservação de argumentos e integração real."""
import copy
import json
import unittest
from pathlib import Path

from crivo import Crivo
from linguagem_neural import LinguagemNeural
from rede_sequencial import RedeSequencial, atributos_frase, assinatura_atributos


class LinguagemNeuralTestes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = json.loads(Path(__file__).with_name("rede_linguagem.json").read_text(encoding="utf-8"))
        cls.rede = LinguagemNeural(cls.dados)

    def test_ordem_e_aprendida_em_pares_com_mesmas_palavras(self):
        a, b = "vermelho antes azul", "azul antes vermelho"
        self.assertEqual(atributos_frase(a, 48, ordem=False), atributos_frase(b, 48, ordem=False))
        self.assertNotEqual(atributos_frase(a, 48), atributos_frase(b, 48))
        r = RedeSequencial(["a", "b"], dimensao=48, ocultos=8)
        r.treinar([(atributos_frase(a, 48), "a"), (atributos_frase(b, 48), "b")], epocas=400, taxa=.15)
        self.assertEqual(r.prever(atributos_frase(a, 48))[0], "a")
        self.assertEqual(r.prever(atributos_frase(b, 48))[0], "b")

    def test_alvos_novos_e_ordem_da_comparacao(self):
        for a, b in (("Asteron Z9", "Nivora X8"), ("RNA", "DNA")):
            q = self.rede.analisar("Compare " + a + " com " + b + ".")
            self.assertEqual((q.ato, q.alvo, q.outro), ("comparar", a, b))
            inverso = self.rede.analisar("Compare " + b + " com " + a + ".")
            self.assertEqual((inverso.alvo, inverso.outro), (b, a))

    def test_nega_pedido_sem_confundir_nao_saber(self):
        negado = self.rede.analisar("Não me explique DNA.")
        duvida = self.rede.analisar("Não sei o que é DNA.")
        self.assertTrue(negado.negacao_pedido)
        self.assertFalse(duvida.negacao_pedido)
        self.assertEqual(duvida.ato, "definir")
        self.assertEqual(Crivo().responder("Não me explique DNA.")[0], "linguagem:negado")
        self.assertEqual(Crivo().responder("Não sei o que é DNA.")[0], "conhecimento:dna")

    def test_conserva_qualificador_e_condicao(self):
        q = self.rede.analisar("Me explica o que é DNA alienígena.")
        self.assertIn("alienígena", q.alvo)
        self.assertIn(Crivo().responder("Me ajuda a entender o que é DNA alienígena.")[0], ("fora", "duvida"))
        q = self.rede.analisar("O que é DNA se viver em outro universo?")
        self.assertEqual(q.condicao, "se viver em outro universo?")

    def test_fallback_preserva_relato_e_autoconversa(self):
        b = Crivo()
        b.responder("Quero conversar sobre trabalho")
        self.assertEqual(b.responder("Eu não consigo decidir")[0], "conversa:relato")
        self.assertEqual(Crivo().responder("O que você sente?")[0], "social:pensamento")

    def test_integracao_e_auditoria_sem_perder_original(self):
        b = Crivo()
        pergunta = "Me ajuda a entender o que é DNA."
        self.assertEqual(b.responder(pergunta)[0], "conhecimento:dna")
        self.assertEqual(b.historico[-1]["pergunta"], pergunta)
        self.assertEqual(b.historico[-1]["quadro_neural"]["alvo"], "DNA")
        b.responder("Organize em tópicos")
        self.assertEqual(b.ultimo_turno["id"], "escrita:topicos")

    def test_checkpoint_corrompido_e_atributos_incompativeis(self):
        dados = copy.deepcopy(self.dados)
        dados["assinatura_atributos"] = "incompativel"
        with self.assertRaises(ValueError):
            LinguagemNeural(dados)
        dados = copy.deepcopy(self.dados)
        dados["atos"]["w1"][0][0] = float("nan")
        with self.assertRaises(ValueError):
            LinguagemNeural(dados)
        self.assertEqual(self.dados["assinatura_atributos"], assinatura_atributos())

    def test_treino_e_validacao_nao_compartilham_familias_ou_alvos(self):
        ds = json.loads(Path(__file__).with_name("curriculo_linguagem_neural.json").read_text(encoding="utf-8"))
        treino = [c for c in ds["exemplos"] if c["split"] == "treino"]
        valid = [c for c in ds["exemplos"] if c["split"] == "validacao"]
        self.assertFalse({c["familia"] for c in treino} & {c["familia"] for c in valid})
        def alvos(casos):
            return {c["texto"][a:b] for c in casos for a, b in c["spans"].values()}
        self.assertFalse(alvos(treino) & alvos(valid))
        self.assertEqual({c["split"] for c in ds["exemplos"]}, {"treino", "validacao"})
