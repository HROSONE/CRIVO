"""Segunda etapa: fichas planetarias cientificas, sem confundir com treino neural."""
import unittest

from crivo import Crivo, PASTA
from curriculo_mundo import carregar_base, ler_curriculo


PLANETAS = ("Mercúrio", "Vênus", "Terra", "Marte",
            "Júpiter", "Saturno", "Urano", "Netuno")


class TestesSistemaSolar(unittest.TestCase):
    def test_oito_planetas_com_mecanismo_origem_e_limites(self):
        dados = ler_curriculo(PASTA / "conhecimento_mundo.json")
        por_nome = {item["nome"]: item for item in dados["itens"] if item["area"] == "astronomia"}
        for nome in PLANETAS:
            with self.subTest(planeta=nome):
                self.assertIn(nome, por_nome)
                item = por_nome[nome]
                self.assertEqual(item["fatos"][0]["papel"], "definicao")
                self.assertGreaterEqual(len(item["fatos"]), 5)
                self.assertTrue(any(f.get("aspecto") == "formacao" for f in item["fatos"]))
                self.assertTrue(any(f.get("aspecto") == "funcionamento" for f in item["fatos"]))
                self.assertTrue(any(f["papel"] == "limite" for f in item["fatos"]))
                self.assertTrue(all(f["fonte"] in dados["fontes"] for f in item["fatos"]))

    def test_definicoes_individuais_sem_trocar_planetas(self):
        for nome in PLANETAS:
            with self.subTest(planeta=nome):
                identificador, texto = Crivo().responder("O que é " + nome + "?")
                self.assertEqual(identificador,
                                 "conhecimento:mundo_" + {
                                     "Mercúrio": "mercurio", "Vênus": "venus",
                                     "Terra": "terra", "Marte": "marte",
                                     "Júpiter": "jupiter", "Saturno": "saturno",
                                     "Urano": "urano", "Netuno": "netuno"
                                 }[nome], (nome, texto))
                self.assertIn(nome, texto)

    def test_origem_e_funcionamento_nao_misturam_conteudos(self):
        for pergunta, palavra in (
            ("Como se forma Mercúrio?", "grãos"),
            ("Como funciona Vênus?", "estufa"),
            ("Como funciona a Terra?", "campo magnético"),
            ("Como funciona Júpiter?", "hidrogênio"),
            ("Como funciona Saturno?", "anéis"),
            ("Como funciona Urano?", "inclinação"),
            ("Como funciona Netuno?", "ventos"),
        ):
            with self.subTest(pergunta=pergunta):
                identificador, resposta = Crivo().responder(pergunta)
                self.assertEqual(identificador, "escrita:explicacao", (pergunta, resposta))
                self.assertIn(palavra.lower(), resposta.lower())

    def test_sem_perda_das_consultas_anteriores(self):
        for pergunta, esperado in (
            ("fale sobre Mercúrio", "mercurio"),
            ("fale sobre Marte", "marte"),
            ("fale sobre Júpiter", "maior_planeta"),
            ("fale sobre Saturno", "aneis"),
            ("Quantos planetas existem no nosso sistema solar?", "planetas"),
        ):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], esperado)

    def test_exemplos_neurais_nao_duplicam_perguntas_existentes(self):
        base = carregar_base(PASTA / "conhecimento.json")
        from composicao_textual import normalizar
        perguntas = [normalizar(q) for e in base for q in e["perguntas"]]
        for nome in ("fale sobre mercúrio", "fale sobre marte", "fale sobre saturno"):
            with self.subTest(pergunta=nome):
                self.assertEqual(perguntas.count(normalizar(nome)), 1)

    def test_evidencia_causal_legada_nao_se_perde_por_nome_novo(self):
        self.assertEqual(Crivo().responder("Por que Marte tem cor de ferrugem?")[0],
                         "marte")
        for pergunta in ("Por que Marte tem cor de ferrugem quântica alienígena?",
                         "Por que Marte cura depressão?"):
            self.assertEqual(Crivo().responder(pergunta)[0], "fora")

    def test_exemplo_desconhecido_nao_vira_planeta_real(self):
        self.assertEqual(Crivo().responder("O que é o planeta Zorvax-913?")[0], "fora")


if __name__ == "__main__":
    unittest.main()
