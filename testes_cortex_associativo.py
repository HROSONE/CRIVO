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

    def test_sujeito_inicial_com_entidade_secundaria_documentada(self):
        # Um conceito citado no complemento nao pode disputar a funcao de
        # sujeito da pergunta. Testa a regra em entidades INVENTADAS.
        self.itens["cristero"]["fatos"][2]["texto"] = (
            "O núcleo magnético de Cristero emite pulsos que atravessam "
            "a atmosfera de Velário.")
        rede = CortexAssociativo(self.itens, self.aliases,
                                 {"ref": {"url": "https://example.org"}}, palavras)
        for pergunta in (
            "De que modo Cristero emite pulsos magnéticos na atmosfera de Velário?",
            "Como o Cristero emite pulsos magnéticos na atmosfera de Velário?",
        ):
            with self.subTest(pergunta=pergunta):
                ativa = rede.associar(pergunta)
                self.assertIsNotNone(ativa)
                self.assertEqual((ativa.conceito, ativa.indice),
                                 ("cristero", 2))
        # Sujeito invertido nao autoriza inverter uma relacao na fonte.
        self.assertIsNone(rede.associar(
            "Como Velário emite pulsos magnéticos de Cristero?"))

    def test_multiplos_sujeitos_qualificadores_e_alvo_implicito(self):
        self.itens["cristero"]["fatos"][2]["texto"] = (
            "O núcleo magnético de Cristero emite pulsos que atravessam "
            "a atmosfera de Velário.")
        rede = CortexAssociativo(self.itens, self.aliases,
                                 {"ref": {"url": "https://example.org"}}, palavras)
        for pergunta in (
            "De que modo Cristero e Velário emitem pulsos magnéticos?",
            "Como Cristero ou Velário emitem pulsos magnéticos?",
            "Como Cristero com Velário emite pulsos magnéticos?",
            "Como a atmosfera de Velário emite pulsos magnéticos de Cristero?",
            "Como Cristero não emite pulsos magnéticos na atmosfera de Velário?",
            "Como Cristero emite pulsos magnéticos se Velário fosse fictício?",
            "Como Cristero emite pulsos mágicos na atmosfera de Velário?",
        ):
            with self.subTest(pergunta=pergunta):
                self.assertIsNone(rede.associar(pergunta))

    def test_parte_pertencente_a_entidade_e_identificada_sem_treinar_pergunta(self):
        for pergunta, esperado in (
            ("Como o núcleo magnético de Cristero movimenta partículas elétricas?",
             ("cristero", 2)),
            ("De que modo a crosta luminosa de Cristero dispersa luz visível?",
             ("cristero", 1)),
            ("Como a hélice interna de Velário agita líquido cristalino?",
             ("velario", 1)),
        ):
            with self.subTest(pergunta=pergunta):
                memoria = self.rede.associar(pergunta)
                self.assertIsNotNone(memoria)
                self.assertEqual((memoria.conceito, memoria.indice), esperado)
        for pergunta in (
            "Como o núcleo magnético de Cristero e Velário movimenta partículas elétricas?",
            "Como a crosta luminosa de Cristero produz ouro?",
            "Como a crosta luminosa de Cristero dispersa luz sem ondas?",
            "Como o núcleo magnético de Cristero não movimenta partículas elétricas?",
        ):
            with self.subTest(pergunta=pergunta):
                self.assertIsNone(self.rede.associar(pergunta))

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

    def test_compositor_emite_prova_e_contexto_da_sinapse_vencedora(self):
        import tempfile
        from pathlib import Path
        from composicao_textual import CompositorTextual
        curriculo = {
            "versao":1, "fontes":{"ref":{"titulo":"Fonte de laboratorio",
                                           "url":"https://example.org/laboratorio"}},
            "itens":[dict(id=chave, nome=dados["nome"], aliases=[],
                         fatos=[f for f in dados["fatos"] if f["fonte"]=="ref"])
                     for chave, dados in self.itens.items()],
        }
        with tempfile.TemporaryDirectory() as pasta:
            motor = CompositorTextual([], Path(pasta) / "nao-existe.json",
                                      lambda texto: None, curriculo)
            pergunta = "De que modo Cristero dispersa luz pela crosta luminosa?"
            ident, texto, contexto = motor.responder(pergunta)
            self.assertEqual(ident, "escrita:explicacao")
            self.assertIn("crosta luminosa", texto)
            self.assertNotIn("hélice interna", texto)
            self.assertEqual(contexto.exibidos, (("cristero", 1),))
            self.assertEqual(contexto.origem, "conhecimento")
            _, fonte, _ = motor.responder("fontes", contexto)
            self.assertIn("https://example.org/laboratorio", fonte)
            self.assertIsNone(motor.responder(
                "De que modo Cristero produz moedas pela crosta luminosa?"))

    def test_persistencia_validada_e_rejeicao_de_corrupcao(self):
        import json
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "ajustes.json"
            chave = ("cristero", 1)
            self.rede.ajustar_com_prova("cristero", 1, "luminosa", False,
                                      autorizado=True)
            peso = self.rede.sinapses[chave]["luminosa"]
            self.rede.salvar_ajustes(destino)
            nova = CortexAssociativo(self.itens, self.aliases,
                                     {"ref":{"url":"https://example.org"}}, palavras)
            nova.carregar_ajustes(destino)
            self.assertEqual(nova.sinapses[chave]["luminosa"], peso)
            falso = json.loads(destino.read_text(encoding="utf-8"))
            falso["sinapses"]["cristero:1"]["inexistente"] = 1.0
            destino.write_text(json.dumps(falso), encoding="utf-8")
            with self.assertRaises(ValueError):
                nova.carregar_ajustes(destino)
            falso["sinapses"]["cristero:1"].pop("inexistente")
            falso["assinatura_conhecimento"] = "forjada"
            destino.write_text(json.dumps(falso), encoding="utf-8")
            with self.assertRaises(ValueError):
                nova.carregar_ajustes(destino)
            self.assertEqual(nova.sinapses[chave]["luminosa"], peso)

    def test_reproducibilidade_mesma_evidencia(self):
        outra = CortexAssociativo(self.itens, self.aliases,
                                  {"ref":{"url":"https://example.org"}}, palavras)
        self.assertEqual(self.rede.associar("Como Cristero dispersa luz na crosta luminosa?"),
                         outra.associar("Como Cristero dispersa luz na crosta luminosa?"))


if __name__ == "__main__":
    unittest.main()
