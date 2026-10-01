"""Desenvolvimento do microcircuito em dados ficticios, SEM os itens v1 retidos."""
import unittest

from cortex_associativo import CortexAssociativo, normalizar


def palavras(texto):
    resultado = []
    for termo in normalizar(texto).split():
        if len(termo) > 4 and termo.endswith("s"):
            termo = termo[:-1]
        resultado.append(termo)
    return resultado


class TestesCortexAssociativo(unittest.TestCase):
    def setUp(self):
        self.itens = {
            "cristero": {
                "nome": "Cristero", "fatos": [
                    {"papel": "definicao", "texto": "Cristero é um objeto inventado.", "fonte": "ref"},
                    {"papel": "detalhe", "aspecto": "funcionamento", "fonte": "ref",
                     "texto": "Sua crosta luminosa reflete ondas e dispersa luz visível."},
                    {"papel": "detalhe", "aspecto": "funcionamento", "fonte": "ref",
                     "texto": "Seu núcleo magnético movimenta partículas elétricas e produz pulsos no campo."},
                    {"papel": "detalhe", "aspecto": "formacao", "fonte": "ref",
                     "texto": "Sua origem ocorre na junção de poeira prateada e pequenos grãos."},
                    {"papel": "detalhe", "aspecto": "funcionamento", "fonte": "semfonte",
                     "texto": "Uma prova inventada nunca deve ser emitida."}
                ],
            },
            "velario": {
                "nome": "Velário", "fatos": [
                    {"papel": "definicao", "texto": "Velário é outro objeto fictício.", "fonte": "ref"},
                    {"papel": "detalhe", "aspecto": "funcionamento", "fonte": "ref",
                     "texto": "Uma hélice interna agita líquido cristalino em pequenas bolhas."}
                ],
            },
        }
        self.aliases = {"cristero": {"cristero"}, "velario": {"velario"}}
        self.rede = CortexAssociativo(self.itens, self.aliases, {"ref":{"url":"https://example.org"}},
                                     palavras)

    def test_competicao_separa_fato_do_mesmo_assunto(self):
        ativacao = self.rede.associar(
            "De que modo Cristero dispersa luz pela crosta luminosa?")
        self.assertIsNotNone(ativacao)
        self.assertEqual((ativacao.conceito, ativacao.indice, ativacao.fonte),
                         ("cristero", 1, "ref"))
        self.assertGreater(ativacao.potencia, ativacao.concorrente)

    def test_nao_confunde_entidades_ou_condicionais(self):
        for pergunta in (
            "Como Cristero e Velário dispersam luz?",
            "Como Cristero dispersa luz se fosse feito de chocolate?",
            "De que modo Cristero produz ouro por magia?",
            "Como Cristero produz pulsos no núcleo de estrelas alienígenas?",
            "Por que Cristero cura doenças?",
        ):
            with self.subTest(pergunta=pergunta):
                self.assertIsNone(self.rede.associar(pergunta))

    def test_nao_usar_conceito_sem_fonte_confiavel(self):
        self.assertNotIn(("cristero", 4), self.rede.unidades)
        self.assertIsNone(self.rede.associar(
            "De que modo Cristero emite prova inventada?"))

    def test_plasticidade_local_so_com_revisao(self):
        chave = ("cristero", 1)
        outra = dict(self.rede.sinapses[("cristero", 2)])
        antes = self.rede.sinapses[chave]["luminosa"]
        with self.assertRaises(ValueError):
            self.rede.ajustar_com_prova("cristero", 1, "luminosa", True)
        with self.assertRaises(ValueError):
            self.rede.ajustar_com_prova("cristero", 1, "inexistente", True,
                                      autorizado=True)
        self.rede.ajustar_com_prova("cristero", 1, "luminosa", False, autorizado=True)
        self.assertLess(self.rede.sinapses[chave]["luminosa"], antes)
        self.assertEqual(outra, self.rede.sinapses[("cristero", 2)])
        self.rede.ajustar_com_prova("cristero", 1, "luminosa", True, autorizado=True)
        self.assertGreater(self.rede.sinapses[chave]["luminosa"], antes * .6)

    def test_reproducibilidade_mesma_evidencia(self):
        outra = CortexAssociativo(self.itens, self.aliases,
                                  {"ref":{"url":"https://example.org"}}, palavras)
        self.assertEqual(self.rede.associar("Como Cristero dispersa luz na crosta luminosa?"),
                         outra.associar("Como Cristero dispersa luz na crosta luminosa?"))


if __name__ == "__main__":
    unittest.main()
