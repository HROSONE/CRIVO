"""Compreensão neural própria: só quando as regras não entendem, e confirmando.

A catraca usa o teste congelado avaliacoes/entendimento_v1 (escrito antes do
treino): os números só podem melhorar. Sem NumPy, a rede fica desligada.
"""
import unittest

try:
    import numpy  # noqa: F401
    TEM_NUMPY = True
except ImportError:
    TEM_NUMPY = False

from entendimento_neural import EntendimentoNeural, entendimento, guarda_vocabulario, normalizar
from web_core import responder_web


@unittest.skipUnless(TEM_NUMPY, "NumPy necessário à compreensão neural")
class CompreensaoNeural(unittest.TestCase):
    def test_pesos_aprovados_no_controle(self):
        motor = entendimento()
        self.assertTrue(motor.ativo, motor.motivo)
        self.assertTrue(motor.meta["controle"]["aprovado"])
        self.assertEqual(motor.meta["controle"]["falsos_fora"], 0)

    def test_sem_pesos_fica_desligada(self):
        motor = EntendimentoNeural("/caminho/que/nao/existe")
        self.assertFalse(motor.ativo)
        self.assertIsNone(motor.decidir("o que é DNA"))

    def test_formulacao_nova_vira_confirmacao(self):
        fala = "moro num ap pequeno, que planta da pra ter"
        r = responder_web({"message": fala})
        self.assertEqual(r["id"], "duvida")
        self.assertEqual(r["mechanism"], "compreensao_neural")
        self.assertEqual(r["neural_understanding"]["assunto"], "plantas_apartamento")
        self.assertIn("Você quis perguntar", r["response"])
        sim = responder_web({"message": "sim", "history": [fala]})
        self.assertEqual(sim["id"], "plantas_apartamento")
        nao = responder_web({"message": "não", "history": [fala]})
        self.assertEqual(nao["id"], "duvida")
        self.assertNotIn("zamioculca", nao["response"])

    def test_sujeito_desconhecido_nao_e_trocado(self):
        r = responder_web({"message": "Golfinho respira debaixo d'água?"})
        self.assertNotEqual(r["mechanism"], "compreensao_neural")
        self.assertNotIn("brânquias", r["response"])

    def test_fora_do_acervo_nao_vira_resposta(self):
        for texto in ("Quanto custa um apartamento em São Paulo?", "qual o signo de Isaac Newton",
                      "Como trocar o pneu da bicicleta?", "me recomenda um filme de terror"):
            r = responder_web({"message": texto})
            self.assertNotEqual(r["mechanism"], "compreensao_neural", texto)

    def test_negacao_nunca_e_reinterpretada(self):
        r = responder_web({"message": "O que a mitocôndria não faz?"})
        self.assertNotEqual(r["mechanism"], "compreensao_neural")
        self.assertNotIn("ATP", r["response"])

    def test_regras_continuam_com_prioridade(self):
        r = responder_web({"message": "O que é DNA?"})
        self.assertNotEqual(r["mechanism"], "compreensao_neural")

    def test_catraca_no_teste_congelado(self):
        from crivo import Crivo
        from scripts.avaliar_entendimento import avaliar
        resumo = avaliar(Crivo)["resumo"]
        self.assertGreaterEqual(resumo["positivos_corretos"], 45, resumo)
        self.assertGreaterEqual(resumo["negativos_corretos"], 49, resumo)
        self.assertGreaterEqual(resumo["confirmacoes_corretas"], 1, resumo)
        self.assertLessEqual(resumo["confirmacoes_erradas"], 0, resumo)
        self.assertEqual(resumo["sugestoes_em_negativos"], 0, resumo)


class GuardaDeVocabulario(unittest.TestCase):
    NOMES = {"mundo_newton": [normalizar("Isaac Newton"), normalizar("Newton")]}
    VOCAB = {"mundo_newton": frozenset(p[:5] for p in normalizar(
        "físico matemático inglês leis do movimento gravitação Principia cálculo luz cores"))}

    def test_nome_com_pedido_coberto_passa(self):
        for texto in ("quem foi Isaac Newton", "me fala sobre Newton", "tenho dúvida sobre Newton"):
            self.assertTrue(guarda_vocabulario(texto, "mundo_newton", self.NOMES, self.VOCAB), texto)

    def test_nome_com_pedido_alheio_e_recusado(self):
        for texto in ("qual o signo de Isaac Newton", "Newton tem frete grátis?", "telefone do Newton",
                      "as leis de Newton na Lua"):
            self.assertFalse(guarda_vocabulario(texto, "mundo_newton", self.NOMES, self.VOCAB), texto)

    def test_sem_nome_basta_uma_palavra_do_assunto(self):
        self.assertTrue(guarda_vocabulario("quem explicou a gravitação", "mundo_newton", self.NOMES, self.VOCAB))

    def test_semelhanca_de_letras_nao_basta(self):
        vocab = {"mundo_cerebro": frozenset(p[:5] for p in normalizar("órgão do sistema nervoso cérebro"))}
        self.assertFalse(guarda_vocabulario("O que é Ceres?", "mundo_cerebro", {}, vocab))


if __name__ == "__main__":
    unittest.main()
