"""Contratos de interpretação geral, pré-registrados antes da implementação.

Cobertura: conhecimentos de animais, plantas, astronomia e programação.
A ligação depende da estrutura do grafo e da existência de definições
cadastradas. Não simula uma LLM nem cria fatos do nada.
"""
import json
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from raciocinio import GrafoRaciocinio
from web_core import responder_web


class TestesComposicaoGeral(unittest.TestCase):
    def test_ancestral_comum_de_entidades_nao_hardcodadas(self):
        exemplos = (
            ("O que pinguim e tucano têm em comum?", "ave"),
            ("O que baleia e golfinho têm em comum?", "mamífero"),
            ("O que gato e cachorro têm em comum?", "mamífero"),
            ("O que Terra e Marte têm em comum?", "planeta"),
            ("Qual a semelhança entre Lua e Sol?", "astro"),
            ("O que sapo e jacaré têm em comum?", "vertebrado"),
        )
        for pergunta, ancestral in exemplos:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "logica:comum")
                self.assertIn(ancestral, resposta.lower())
                self.assertIn(" → ", resposta)
                self.assertIn("cadastrad", resposta.lower())

    def test_ligacao_entre_conceitos_com_provas(self):
        exemplos = (
            ("Qual é a relação entre a Terra e a Via Láctea?",
             "Terra → Sistema Solar → Via Láctea"),
            ("Como o Sol se relaciona com o Universo?",
             "Sol → Sistema Solar → Via Láctea → Universo"),
            ("Qual a relação entre o pinguim e o vertebrado?",
             "pinguim → ave → vertebrado"),
            ("Qual é a relação entre a Terra e a Lua?",
             "Lua --orbita--> Terra"),
        )
        for pergunta, prova in exemplos:
            with self.subTest(pergunta=pergunta):
                ident, resposta = Crivo().responder(pergunta)
                self.assertEqual(ident, "logica:ligacao")
                self.assertIn(prova, resposta)

    def test_relacao_desconhecida_nao_prova_falsidade(self):
        ident, resposta = Crivo().responder(
            "Qual é a relação entre gato e Sistema Solar?")
        self.assertEqual(ident, "logica:sem_ligacao")
        self.assertIn("não prova", resposta.lower())
        self.assertNotIn("impossível", resposta.lower())

    def test_condicoes_negadas_ou_hipoteses_nao_viram_fatos(self):
        for pergunta in (
            "O que pinguim e tucano NÃO têm em comum?",
            "Se gatos fossem estrelas, qual a relação com o Sol?",
            "Qual a relação entre pinguim e uma ave quântica?",
            "O que gato e computador têm em comum?",
        ):
            with self.subTest(pergunta=pergunta):
                ident, _ = Crivo().responder(pergunta)
                self.assertNotIn(ident, ("logica:comum", "logica:ligacao"))

    def test_raciocinio_fica_generico_em_novo_grafo_sintetico(self):
        from interpretacao_geral import InterpretadorGeral
        grafo = GrafoRaciocinio({
            "versao": 1,
            "entidades": {
                "x": {"nome": "gorb"},
                "y": {"nome": "flim"},
                "c": {"nome": "categoria fictícia"},
                "raiz": {"nome": "grupo fictício"},
                "outro": {"nome": "objeto sem ligação"},
            },
            "fatos": [
                {"sujeito": "x", "relacao": "tipo_de", "objeto": "c"},
                {"sujeito": "y", "relacao": "tipo_de", "objeto": "c"},
                {"sujeito": "c", "relacao": "tipo_de", "objeto": "raiz"},
            ],
        })
        m = InterpretadorGeral(grafo)
        id_, resposta = m.interpretar("O que gorb e flim têm em comum?")
        self.assertEqual(id_, "logica:comum")
        self.assertIn("categoria fictícia", resposta)
        self.assertNotIn("grupo fictício", resposta)
        id_, resposta = m.interpretar("Qual a relação entre gorb e grupo fictício?")
        self.assertEqual(id_, "logica:ligacao")
        self.assertIn("gorb → categoria fictícia → grupo fictício", resposta)
        id_, resposta = m.interpretar("Qual a relação entre gorb e objeto sem ligação?")
        self.assertEqual(id_, "logica:sem_ligacao")
        self.assertIn("não prova", resposta)

    def test_elipses_de_definicao_em_quatro_assuntos(self):
        casos = (
            (["O que é o Sol?", "E a Lua?"], ["sol", "lua"]),
            (["O que é HTML?", "E CSS?"], ["web_html", "web_css"]),
            (["O que é Git?", "E SQL?"], ["git_intro", "sql_intro"]),
            (["O que é fotossíntese?", "E uma árvore?"], ["fotossintese", "arvore"]),
            (["O que é a Via Láctea?", "E o Sol?"], ["via_lactea", "sol"]),
            (["O que é o Sol?", "E a Lua?", "E o Sol?"],
             ["sol", "lua", "sol"]),
        )
        for perguntas, esperado in casos:
            with self.subTest(perguntas=perguntas):
                bot = Crivo()
                obtido = [bot.responder(pergunta)[0] for pergunta in perguntas]
                self.assertEqual(obtido, esperado)
                self.assertEqual(bot.historico[-1]["pergunta"], perguntas[-1])

    def test_elipse_nao_inventa_definicao_de_termo_composto(self):
        bot = Crivo()
        bot.responder("O que é o Sol?")
        ident, resposta = bot.responder("E uma árvore binária?")
        self.assertIn(ident, ("fora", "duvida"))
        self.assertNotIn("Uma árvore é uma planta", resposta)
        bot = Crivo()
        bot.responder("O que é HTML?")
        ident, _ = bot.responder("E Rust?")
        self.assertIn(ident, ("fora", "duvida"))

    def test_contexto_definicional_expira_apos_outra_intencao(self):
        bot = Crivo()
        bot.responder("O que é HTML?")
        self.assertEqual(bot.contexto_geral, "definicao")
        bot.responder("Tudo bem com você?")
        self.assertIsNone(bot.contexto_geral)
        bot.responder("Como regar as plantas?")
        self.assertIsNone(bot.contexto_geral)

    def test_api_reconstroi_contexto_sem_salvar_estado(self):
        r = responder_web({
            "message": "E o CSS?",
            "history": ["O que é HTML?"],
        })
        self.assertEqual(r["id"], "web_css")
        self.assertIn("CSS", r["response"])
        r = responder_web({
            "message": "O que pinguim e tucano têm em comum?",
        })
        self.assertEqual(r["id"], "logica:comum")
        self.assertTrue(r["has_proof"])

    def test_preserva_esclarecimentos_e_questoes_existentes(self):
        bot = Crivo()
        self.assertEqual(bot.responder("planta")[0], "duvida")
        self.assertEqual(bot.responder("a segunda")[0], "regar")
        casos = (
            ("O que é uma árvore?", "arvore"),
            ("Por que as folhas caem no outono?", "folhas_outono"),
            ("Se todo flumbo é blim, todo blim é taro, então flumbo é taro?",
             "logica:hipotese"),
            ("Um pinguim é um ser vivo?", "logica:tipo_de"),
            ("Como usar input em Python?", "py_input"),
            ("O que são tipos de dados?", "prog_tipos"),
        )
        for pergunta, id_esperado in casos:
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], id_esperado)

    def test_base_personalizada_sem_grafo_nao_recebe_dados_padrao(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "conhecimento.json"
            path.write_text(json.dumps([{
                "id": "teste", "topico": "plantas",
                "perguntas": ["O que é blip?", "Explique blip"],
                "resposta": "Blip é um termo de teste."
            }]), encoding="utf-8")
            bot = Crivo(path)
            self.assertIsNone(bot.interpretador_geral.grafo)
            self.assertNotEqual(bot.responder("Qual a relação entre Terra e Lua?")[0],
                                "logica:ligacao")
            self.assertEqual(bot.responder("O que é blip?")[0], "teste")


if __name__ == "__main__":
    unittest.main()
