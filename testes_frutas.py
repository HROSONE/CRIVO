"""Contrato da categoria frutas, escrito ANTES da implementação do motor.

Perguntas por classe, espécie e comparação não podem depender de frases
exatas cadastradas como perguntas nem de um modelo externo.
"""
import json
import unittest
from pathlib import Path

from crivo import Crivo
from web_core import responder_web


class TestesConhecimentoFrutas(unittest.TestCase):
    def test_corpus_vasto_e_validado(self):
        from frutas import ConhecimentoFrutas
        banco = ConhecimentoFrutas.carregar(Path(__file__).with_name("frutas.json"))
        self.assertGreaterEqual(len(banco.itens), 45)
        self.assertEqual(len(banco.itens), len(set(banco.itens)))
        self.assertIn("maca", banco.aliases)
        self.assertIn("bananas", banco.aliases)
        self.assertIn("macas", banco.aliases)
        self.assertIn("morango", banco.aliases)
        self.assertIn("tomate", banco.aliases)

    def test_definicoes_especificas_sem_confundir_processo(self):
        exemplos = {
            "O que é uma maçã?": ("maca", "macieira"),
            "Explique o que é banana.": ("banana", "bananeira"),
            "Defina laranja.": ("laranja", "cítrico"),
            "O que é um abacaxi?": ("abacaxi", "flores"),
            "E o que são bananas?": ("banana", "bananeira"),
            "O que é um morango?": ("morango", "receptáculo"),
            "O que é um tomate?": ("tomate", "fruto"),
            "O que é uma manga?": ("manga", "fruto"),
            "O que são jabuticabas?": ("jabuticaba", "fruto"),
        }
        for pergunta, (ident, sinal) in exemplos.items():
            with self.subTest(pergunta=pergunta):
                obtido, resposta = Crivo().responder(pergunta)
                self.assertEqual(obtido, "frutas:" + ident)
                self.assertIn(sinal, resposta.lower())
                self.assertNotIn("Polinização é o transporte", resposta)

    def test_consultas_composicionais(self):
        casos = (
            ("Banana tem sementes?", "banana", "variedades cultivadas"),
            ("Uma maçã tem sementes?", "maca", "sementes"),
            ("Morango tem as sementes do lado de fora?", "morango", "aquênios"),
            ("Tomate é fruta ou legume?", "tomate", "botânica"),
            ("Pepino é uma fruta?", "pepino", "botânica"),
            ("Azeitona é uma fruta?", "azeitona", "botânica"),
            ("Qual o tipo botânico da maçã?", "maca", "pomo"),
            ("Qual o tipo botânico do abacaxi?", "abacaxi", "múltiplo"),
            ("Que tipo de fruto é um morango?", "morango", "agregado"),
            ("Qual a diferença entre maçã e pera?", "comparar", "pera"),
            ("Liste frutas cítricas", "grupo:citricas", "laranja"),
            ("Me dê exemplos de frutas de caroço", "grupo:drupas", "pêssego"),
            ("O que é uma fruta?", "fruto", "sementes"),
            ("Qual é a diferença entre fruto e fruta?", "conceito", "botânica"),
        )
        for pergunta, identificador, sinal in casos:
            with self.subTest(pergunta=pergunta):
                obtido, resposta = Crivo().responder(pergunta)
                esperado = ("fruto" if identificador == "fruto" else "frutas:" + identificador)
                self.assertTrue(obtido.startswith(esperado), obtido)
                self.assertIn(sinal, resposta.lower())

    def test_pergunta_aberta_nao_confunde_frutas_com_fatos_ausentes(self):
        perguntas = (
            "O que é uma fruta quântica?",
            "O que é uma maçã quântica?",
            "Qual o preço da maçã hoje?",
            "Maçã cura diabetes?",
            "Quem inventou a banana?",
            "Qual o tipo botânico do pão?",
            "Qual fruta tem menos agrotóxicos no mercado agora?",
            "Quais frutas causam reações alérgicas fatais?",
        )
        for pergunta in perguntas:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertNotEqual(ident, "frutas:maca")
                self.assertNotEqual(ident, "frutas:banana")
                self.assertNotIn("A maçã é o fruto", resposta)

    def test_contexto_curto_ajuda_na_referencia_mas_nao_inventa(self):
        bot = Crivo()
        ident, _ = bot.responder("Qual é o tipo botânico da maçã?")
        self.assertEqual(ident, "frutas:maca")
        ident, resposta = bot.responder("E a banana?")
        self.assertEqual(ident, "frutas:banana")
        self.assertIn("baga", resposta.lower())
        bot = Crivo()
        ident, resposta = bot.responder("E a banana?")
        self.assertIn(ident, ("fora", "duvida", "frutas:desconhecido"))

    def test_nao_estraga_perguntas_antigas_ou_conceitos_compostos(self):
        casos = (
            ("O que é uma árvore?", "arvore"),
            ("Como as flores viram frutos?", "polinizacao"),
            ("Por que as folhas caem no outono?", "folhas_outono"),
            ("O que são tipos de dados?", "prog_tipos"),
            ("O que é uma árvore binária?", "fora"),
            ("O que é a Via Láctea?", "via_lactea"),
        )
        for pergunta, esperado in casos:
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], esperado)

    def test_mesma_regra_funciona_para_todo_o_catalogo(self):
        from frutas import ConhecimentoFrutas
        banco = ConhecimentoFrutas.carregar(Path(__file__).with_name("frutas.json"))
        bot = Crivo()
        for item in banco.itens.values():
            nome = item["nome"]
            with self.subTest(nome=nome, prova="definicao"):
                ident, resposta = bot.responder("O que é uma " + nome + "?")
                self.assertEqual(ident, "frutas:" + item["id"])
                self.assertIn(item["descricao"][:24], resposta)
            with self.subTest(nome=nome, prova="sementes"):
                ident, resposta = bot.responder(nome + " tem sementes?")
                self.assertEqual(ident, "frutas:" + item["id"])
                self.assertIn(item["sementes"], resposta)
            with self.subTest(nome=nome, prova="grupo"):
                ident, resposta = bot.responder(
                    "Qual é o tipo botânico de " + nome + "?")
                self.assertEqual(ident, "frutas:" + item["id"])
                self.assertIn(banco.grupos[item["tipo"]], resposta)

    def test_lista_eh_amostra_e_nao_afirma_cobertura_universal(self):
        bot = Crivo()
        for pergunta in ("Liste 8 frutas", "Liste frutas cítricas",
                         "Me dê exemplos de frutas de caroço"):
            with self.subTest(pergunta=pergunta):
                ident, resposta = bot.responder(pergunta)
                self.assertTrue(ident.startswith("frutas:grupo:"))
                self.assertIn("cadastrad", resposta)

    def test_base_customizada_nao_recebe_dados_por_acidente(self):
        import tempfile
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "conhecimento.json"
            arquivo.write_text(json.dumps([{
                "id": "teste", "topico": "plantas",
                "perguntas": ["diga oi", "cumprimente"],
                "resposta": "Oi."}], ensure_ascii=False),
                encoding="utf-8")
            bot = Crivo(arquivo)
            self.assertIsNone(bot.frutas)
            self.assertNotEqual(bot.responder("O que é uma banana?")[0],
                                "frutas:banana")

    def test_deploy_servidor_inclui_o_catalogo_e_motor(self):
        config = json.loads((Path(__file__).resolve().parent /
                             "vercel.json").read_text(encoding="utf-8"))
        files = config["functions"]["api/chat.py"]["includeFiles"]
        self.assertIn("frutas.py", files)
        self.assertIn("frutas.json", files)

    def test_web_real_sem_outro_modelo_ou_endpoint_especial(self):
        result = responder_web({"message": "O que é uma maçã?",
                                "history": ["O que são frutos?"]})
        self.assertEqual(result["id"], "frutas:maca")
        self.assertIn("macieira", result["response"].lower())
        self.assertFalse(result.get("external_ai", False))
        result = responder_web({"message": "E a banana?",
                                "history": ["Qual o tipo botânico da maçã?"]})
        self.assertEqual(result["id"], "frutas:banana")
        self.assertIn("baga", result["response"].lower())

    def test_corpus_nao_cria_contradicoes_obvias(self):
        from frutas import ConhecimentoFrutas
        banco = ConhecimentoFrutas.carregar(Path(__file__).with_name("frutas.json"))
        for item in banco.itens.values():
            with self.subTest(item=item["nome"]):
                self.assertIn(item["tipo"], banco.grupos)
                self.assertTrue(item["descricao"])
                self.assertTrue(item["sementes"])
                self.assertIsInstance(item["culinaria"], bool)
                self.assertIn(item["id"], banco.aliases.values())


if __name__ == "__main__":
    unittest.main()
