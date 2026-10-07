"""Conteúdo avançado de física, biologia, sociologia e filosofia: as fichas
passam pela validação do currículo, têm fonte com licença registrada e
respondem a perguntas escritas de formas variadas."""
import json
import unittest
from pathlib import Path

from crivo import Crivo
from curriculo_mundo import ler_curriculo
from linguagem_conversa import normalizar

RAIZ = Path(__file__).resolve().parent
AREAS = ("fisica", "biologia", "sociologia", "filosofia")


class TestesConteudoAvancado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculo = ler_curriculo(RAIZ / "conhecimento_mundo.json")

    def test_cada_área_tem_conteúdo_amplo_e_com_fonte(self):
        for area in AREAS:
            with self.subTest(area=area):
                itens = [i for i in self.curriculo["itens"] if i["area"] == area
                         and i["fatos"][0]["fonte"].startswith("openstax_")]
                self.assertGreaterEqual(len(itens), 45)
                self.assertGreaterEqual(sum(len(i["fatos"]) for i in itens), 110)
                for item in itens:
                    for fato in item["fatos"]:
                        fonte = self.curriculo["fontes"][fato["fonte"]]
                        self.assertIn(fonte["reutilizacao"], ("CC-BY-4.0", "somente_referencia"))

    def test_perguntas_variadas_são_respondidas(self):
        casos = json.loads((RAIZ / "avaliacoes" / "conteudo_avancado_v1" / "casos.json").read_text(encoding="utf-8"))
        falhas = []
        for caso in casos["casos"]:
            resposta = Crivo().responder(caso["fala"])[1]
            if not any(normalizar(m) in normalizar(resposta) for m in caso["contem_algum"]):
                falhas.append((caso["fala"], resposta[:120]))
        self.assertEqual(falhas, [])

    def test_nome_próprio_mantém_maiúscula_depois_do_conectivo(self):
        # O conectivo pertence ao compositor; a geração tem redação própria.
        sem_voz = Crivo(usar_geracao=False)
        sem_voz.usar_voz = False
        resposta = sem_voz.responder("O que é anomia?")[1]
        self.assertIn("Além disso, Durkheim", resposta)
        sem_voz = Crivo(usar_geracao=False)
        sem_voz.usar_voz = False
        resposta = sem_voz.responder("O que é uma galáxia espiral?")[1]
        self.assertNotIn("Além disso, A ", resposta)
        # Com a voz própria, o nome continua em maiúscula em qualquer posição.
        for usar_geracao in (False, True):
            with self.subTest(geracao=usar_geracao):
                resposta = Crivo(usar_geracao=usar_geracao).responder("O que é anomia?")[1]
                self.assertIn("Durkheim", resposta)
                self.assertNotIn("durkheim", resposta)


if __name__ == "__main__":
    unittest.main()
