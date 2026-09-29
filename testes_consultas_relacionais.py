"""Contratos de resposta, contraprovas e grafos novos para o consultor.

São testes de desenvolvimento. Dados sintéticos verificam reutilização
do algoritmo; não demonstram compreensão irrestrita de português.
"""
import copy
import itertools
import json
import random
import tempfile
import unittest
from pathlib import Path

from avaliar_consultas import CASOS, executar_caso
from consultas_relacionais import ConsultasRelacionais, MAX_EXIBIDOS
from crivo import Crivo
from raciocinio import GrafoRaciocinio
from web_core import responder_web


def grafo_sintetico(total=30, semente=821):
    rng = random.Random(semente)
    entidades = {"raiz": {"nome": "zutrins"},
                 "ca": {"nome": "tavros"}, "cb": {"nome": "mivros"},
                 "cc": {"nome": "dovros"},
                 "prop": {"nome": "brilho violeta", "tipo": "caracteristica"},
                 "alvo": {"nome": "nex"}, "final": {"nome": "lus"}}
    fatos = [{"sujeito": c, "relacao": "tipo_de", "objeto": "raiz"}
             for c in ("ca", "cb", "cc")]
    fatos += [{"sujeito": "ca", "relacao": "disjunto_de", "objeto": "cb"},
              {"sujeito": "ca", "relacao": "tem_caracteristica", "objeto": "prop"},
              {"sujeito": "alvo", "relacao": "orbita", "objeto": "final"}]
    categorias, orbitas, propriedades = {}, set(), set()
    for i in range(total):
        ident = "objeto_" + str(i)
        entidades[ident] = {"nome": "zumo{:03d}".format(i)}
        categoria = rng.choice(("ca", "cb", "cc"))
        categorias[ident] = categoria
        fatos.append({"sujeito": ident, "relacao": "tipo_de", "objeto": categoria})
        if rng.randrange(2):
            fatos.append({"sujeito": ident, "relacao": "orbita", "objeto": "alvo"})
            orbitas.add(ident)
        if rng.randrange(2):
            fatos.append({"sujeito": ident, "relacao": "tem_caracteristica", "objeto": "prop"})
            propriedades.add(ident)
        if categoria == "ca":
            propriedades.add(ident)
    rng.shuffle(fatos)
    return {"versao": 1, "entidades": entidades, "fatos": fatos}, categorias, orbitas, propriedades


class TestesConsultasRelacionais(unittest.TestCase):
    def test_sonda_de_36_respostas_e_dialogos(self):
        for caso in CASOS:
            with self.subTest(pergunta=caso[1]):
                resultado = executar_caso(caso)
                self.assertTrue(resultado["passou"], resultado)

    def test_intersecoes_ineditas_com_oraculo_independente(self):
        # O esperado é construído a partir das atribuições do gerador,
        # sem chamar o provador ou ler o resultado do parser para criá-lo.
        for semente in (17, 81, 204, 981):
            dados, categorias, orbitas, propriedades = grafo_sintetico(80, semente)
            motor = ConsultasRelacionais(GrafoRaciocinio(dados))
            esperado = {e for e in orbitas & propriedades if categorias[e] == "ca"}
            condicoes = ["orbitam nex", "têm brilho violeta", "não são mivros"]
            for ordem in itertools.permutations(condicoes):
                pergunta = "Quais zutrins " + " e ".join(ordem) + "?"
                plano = motor.analisar(pergunta)
                obtido = {e for e, _ in motor.executar(plano)}
                self.assertEqual(obtido, esperado)

    def test_orbita_nao_e_transitiva_nem_simetrica(self):
        dados, _, orbitas, _ = grafo_sintetico()
        motor = ConsultasRelacionais(GrafoRaciocinio(dados))
        resultado = motor.executar(motor.analisar("Quem orbita lus?"))
        self.assertEqual({e for e, _ in resultado}, {"alvo"})
        self.assertFalse(orbitas & {e for e, _ in resultado})
        resultado = motor.executar(motor.analisar("O que é orbitado por lus?"))
        self.assertEqual(resultado, [])

    def test_reuso_da_gramatica_em_todas_as_arestas_positivas(self):
        motor = Crivo().consultas_relacionais
        g = motor.grafo
        verbos = {"tipo_de": "é", "parte_de": "faz parte de",
                  "tem_caracteristica": "tem", "orbita": "orbita"}
        for tipo, verbo in verbos.items():
            for sujeito, objetos in g.arestas[tipo].items():
                for objeto in objetos:
                    q = "Quem " + verbo + " " + g.nomes[objeto] + "?"
                    with self.subTest(pergunta=q, sujeito=sujeito):
                        resposta = motor.executar(motor.analisar(q))
                        self.assertIn(sujeito, {e for e, _ in resposta})

    def test_nome_composto_com_e_e_validado_inteiro(self):
        dados = {"versao": 1, "entidades": {
            "x": {"nome": "arte e ciência"}, "c": {"nome": "grupo experimental"}},
            "fatos": [{"sujeito": "x", "relacao": "tipo_de", "objeto": "c"}]}
        motor = ConsultasRelacionais(GrafoRaciocinio(dados))
        plano = motor.analisar("Liste grupo experimental")
        self.assertEqual([e for e, _ in motor.executar(plano)], ["x"])
        self.assertEqual(motor.responder("Quem é arte e ciência?")[0], "logica:desconhecido")

    def test_nao_descarta_modalidade_alternativa_ou_modificador(self):
        perguntas = (
            "Quais animais podem ter penas?",
            "Quais animais têm penas ou possuem oito patas?",
            "Quais animais são aves se chover?",
            "Quais animais são aves quânticas?",
            "Quais animais têm penas falsas?",
            "Quem orbita o Sol amanhã?",
            "Quais animais não são insetos e têm asas?",
            "A Terra é um planeta e o gato é um mamífero?",
            "O pinguim é ave e talvez tenha penas?",
        )
        for pergunta in perguntas:
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], "duvida")

    def test_negacao_nao_se_baseia_na_falta_de_fatos(self):
        motor = Crivo().consultas_relacionais
        resultados = motor.executar(motor.analisar("Quais animais não são insetos?"))
        self.assertEqual({e for e, _ in resultados}, {"aranha", "aracnideo"})
        # Outros animais não têm essa incompatibilidade cadastrada.
        self.assertEqual(Crivo().responder("O gato é mamífero e não é inseto?")[0],
                         "logica:desconhecido")
        self.assertEqual(Crivo().responder("O pinguim é ave e não é vertebrado?")[0],
                         "logica:conjuncao_falsa")

    def test_prova_negativa_basta_para_refutar_conjuncao(self):
        ident, resposta = Crivo().responder("A aranha é inseto e orbita o Sol?")
        self.assertEqual(ident, "logica:conjuncao_falsa")
        self.assertIn("desconhecido", resposta)
        self.assertIn("incompatível", resposta)

    def test_contexto_expira_em_todas_as_rotas(self):
        for intermediaria in ("Oi", "Quanto custa um robô quântico?",
                              "O que é HTML?", "Quem orbita Marte?", "mais"):
            with self.subTest(intermediaria=intermediaria):
                bot = Crivo()
                bot.responder("Quais animais têm penas?")
                bot.responder(intermediaria)
                self.assertIsNone(bot.contexto_consulta)
                self.assertEqual(bot.responder("Desses, quais são aves?")[0], "duvida")

    def test_contexto_nao_reintroduz_itens_removidos(self):
        bot = Crivo()
        bot.responder("Quais astros fazem parte do Sistema Solar?")
        bot.responder("Desses, quais orbitam o Sol?")
        self.assertNotIn("lua", bot.contexto_consulta)
        ident, _ = bot.responder("Desses, quais são satélites naturais?")
        self.assertEqual(ident, "logica:desconhecido")
        self.assertIsNone(bot.contexto_consulta)

    def test_contexto_aponta_apenas_para_itens_exibidos(self):
        dados, _, _, _ = grafo_sintetico(60)
        motor = ConsultasRelacionais(GrafoRaciocinio(dados))
        _, texto, contexto = motor.responder("Liste zutrins")
        self.assertEqual(len(contexto), MAX_EXIBIDOS)
        self.assertIn("Exibindo", texto)
        plano = motor.analisar("Desses, quais têm brilho violeta?", contexto)
        self.assertLessEqual({e for e, _ in motor.executar(plano)}, set(contexto))

    def test_api_reconstroi_filtros_e_sinaliza_provas(self):
        r = responder_web({"message": "Desses, quais orbitam o Sol?",
                           "history": ["Quais astros fazem parte do Sistema Solar?"]})
        self.assertEqual(r["id"], "logica:consulta")
        self.assertTrue(r["has_proof"])
        self.assertEqual(r["mechanism"], "consulta_relacional")
        self.assertNotIn("Lua", r["response"].split("\n")[0])
        for q in ("Quem orbita Marte?", "Quais animais não têm penas?",
                  "O gato é mamífero e orbita o Sol?"):
            self.assertFalse(responder_web({"message": q})["has_proof"])
        self.assertEqual(responder_web({"message": "Desses, quais têm penas?"})["id"], "duvida")

    def test_grafo_permanece_inalterado(self):
        g = Crivo().raciocinio
        original = copy.deepcopy(g.__dict__)
        motor = ConsultasRelacionais(g)
        for _, q, _, _, _ in CASOS:
            motor.responder(q)
        self.assertEqual(g.__dict__, original)

    def test_base_personalizada_nao_importa_fatos_globais(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "conhecimento.json"
            caminho.write_text(json.dumps([{"id": "teste", "topico": "animais",
                                           "perguntas": ["exemplo"], "resposta": "Só exemplo."}]), encoding="utf-8")
            bot = Crivo(caminho)
            self.assertIsNone(bot.consultas_relacionais.grafo)
            self.assertNotEqual(bot.responder("Quem orbita a Terra?")[0], "logica:consulta")

    def test_ensinar_invalida_contexto(self):
        bot = Crivo()
        bot.responder("Quais animais têm penas?")
        bot.ensinar("exemplo_novo", "animais", ["pergunta nova"], "resposta", salvar=False)
        self.assertIsNone(bot.contexto_consulta)

    def test_limite_de_condicoes(self):
        q = "Quais animais " + " e ".join(["têm penas"] * 7) + "?"
        self.assertEqual(Crivo().responder(q)[0], "duvida")

    def test_detecta_condicoes_impossiveis_sem_inventar_exemplares(self):
        for q in ("Quais animais são aves e não são aves?",
                  "Quais animais são aves e não são vertebrados?",
                  "Quais animais são insetos e são aracnídeos?",
                  "Quais animais não são animais?"):
            with self.subTest(pergunta=q):
                r = responder_web({"message": q})
                self.assertEqual(r["id"], "logica:consulta_impossivel")
                self.assertTrue(r["has_proof"])
                self.assertIn("incompat", r["response"])
        r = Crivo().responder("A Lua é inseto e não é inseto?")
        self.assertEqual(r[0], "logica:conjuncao_falsa")
        self.assertIn("condições", r[1])

    def test_falta_de_incompatibilidade_nao_impossibilita_consulta(self):
        for q in ("Quais animais são mamíferos e são aves?",
                  "Quais planetas têm penas?",
                  "Quais animais têm penas e não são insetos?"):
            self.assertEqual(Crivo().responder(q)[0], "logica:desconhecido")

    def test_nao_captura_qualquer_pergunta_com_quem(self):
        motor = Crivo().consultas_relacionais
        self.assertIsNone(motor.responder("Quem ganhou a copa de 2014?"))
        self.assertIsNone(motor.responder("Quem inventou o avião?"))
        # Textos editoriais exatos continuam prioritários e completos.
        r = Crivo().responder("Quais são os planetas?")
        self.assertEqual(r[0], "planetas")
        self.assertIn("Netuno", r[1])


if __name__ == "__main__":
    unittest.main()
