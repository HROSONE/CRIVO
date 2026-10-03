"""Conhecimento, planos de texto, fontes e diálogo com dados inéditos."""
import copy
import json
import re
import random
import tempfile
import unittest
from pathlib import Path

from avaliar_escrita import CASOS, executar
from composicao_textual import CompositorTextual, normalizar
from crivo import Crivo, PASTA
from web_core import responder_web


class TestesComposicaoTextual(unittest.TestCase):
    def test_sonda_de_32_casos(self):
        for caso in CASOS:
            with self.subTest(pergunta=caso[1], historico=caso[0]):
                r = executar(caso)
                self.assertTrue(r["passou"], r)

    def test_todos_os_novos_conceitos_e_aliases(self):
        b = Crivo()
        for ident in sorted(b.compositor.expandidos):
            item = b.compositor.itens[ident]
            for nome in [item["nome"]] + item.get("aliases", []):
                with self.subTest(nome=nome):
                    obtido, resposta = b.responder("O que é " + nome + "?")
                    self.assertEqual(obtido, item.get("id_resposta", "conhecimento:" + ident))
                    self.assertIn(item["fatos"][0]["texto"], resposta)

    def test_300_combinacoes_sem_respostas_para_cada_par(self):
        bot = Crivo()
        m = bot.compositor
        nomes = sorted(m.expandidos)
        # Cobertura de todos os conceitos, mais pares sorteados antes das saídas.
        # O produto completo cresceu de ~300 para 13.695 pares; esta regressão
        # deve escalar linearmente com o acervo, mantendo a matriz reproduzível.
        pares = {tuple(sorted(p)) for p in zip(nomes, nomes[1:] + nomes[:1])}
        pares = {p for p in pares if p[0] != p[1]}
        limite = min(len(nomes) * (len(nomes) - 1) // 2, max(300, len(nomes)))
        rng = random.Random(20261003)
        while len(pares) < limite:
            pares.add(tuple(sorted(rng.sample(nomes, 2))))
        self.assertEqual({n for p in pares for n in p}, set(nomes))
        self.assertEqual(len(pares), limite)
        for a, b in sorted(pares):
            q = "Escreva um texto sobre " + m.itens[a]["nome"] + " e " + m.itens[b]["nome"]
            with self.subTest(par=(a, b)):
                ident, texto = bot.responder(q)
                ctx = bot.contexto_textual
                self.assertEqual(ident, "escrita:texto")
                self.assertEqual(ctx.temas, (a, b))
                for alvo in (a, b):
                    self.assertIn(normalizar(m.itens[alvo]["fatos"][0]["texto"]), normalizar(texto))
                for origem, indice in ctx.exibidos:
                    self.assertIn(normalizar(m.itens[origem]["fatos"][indice]["texto"]), normalizar(texto))

    def test_composicao_em_base_sintetica_sem_nomes_conhecidos(self):
        base = [
            {"id": "lum", "topico": "clima", "perguntas": ["o que é lum"],
             "resposta": "Lum é um objeto fictício. Lum possui uma marca verde."},
            {"id": "zor", "topico": "clima", "perguntas": ["o que é zor"],
             "resposta": "Zor é um objeto fictício. Zor possui uma marca azul."}]
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / "conhecimento.json"
            arq.write_text(json.dumps(base), encoding="utf-8")
            b = Crivo(arq)
            ident, texto = b.responder("Escreva um texto sobre lum e zor")
            self.assertEqual(ident, "escrita:texto")
            self.assertIn("verde", texto)
            self.assertIn("azul", texto)
            self.assertNotIn("porque", texto.lower())
            self.assertEqual(b.responder("O que é Andrômeda?")[0], "fora")
            self.assertFalse(b.compositor.expandidos)

    def test_resumo_e_topicos_transformam_so_o_que_foi_mostrado(self):
        b = Crivo()
        _, original = b.responder("O que é DNA?")
        antes = b.contexto_textual
        _, curto = b.responder("Mais curto")
        self.assertLess(len(curto), len(original))
        self.assertTrue(set(b.contexto_textual.exibidos) <= set(antes.exibidos))
        self.assertNotIn("bases", curto)
        _, topicos = b.responder("Em tópicos")
        self.assertTrue(topicos.startswith("- "))
        self.assertEqual(b.contexto_textual.exibidos, (("dna", 0),))

    def test_continuacao_nao_repete_nem_inventa(self):
        b = Crivo()
        b.responder("O que é Andrômeda?")
        anteriores = set(b.contexto_textual.usados)
        ident, texto = b.responder("Continue")
        self.assertEqual(ident, "escrita:continuacao")
        self.assertTrue(anteriores.isdisjoint(b.contexto_textual.exibidos))
        self.assertNotIn("2,5 milhões", texto)
        self.assertEqual(b.responder("Continue")[0], "escrita:fim")

    def test_limite_de_frases_e_cobertura_dos_temas(self):
        for formato in ("texto", "resumo", "roteiro"):
            b = Crivo()
            ident, texto = b.responder("Escreva um " + formato + " sobre DNA em duas frases")
            self.assertEqual(ident, "escrita:" + formato)
            self.assertEqual(len(re.findall(r"[.!?](?:\s|$)", texto)), 2)
        self.assertEqual(Crivo().responder("Escreva um texto sobre DNA e RNA em uma frase")[0], "duvida")

    def test_pedidos_corteses_e_resumo_nomeado(self):
        for q, ident in (("Você poderia escrever um texto sobre DNA?", "escrita:texto"),
                         ("Pode criar um roteiro sobre a Lua?", "escrita:roteiro"),
                         ("Resuma o DNA", "escrita:resumo")):
            self.assertEqual(Crivo().responder(q)[0], ident)

    def test_troca_de_assunto_e_expiracao(self):
        for q in ("Oi", "O que é um cristal inventado?", "Quanto custa viajar para uma estrela?"):
            b = Crivo()
            b.responder("O que é DNA?")
            b.responder(q)
            self.assertIsNone(b.contexto_textual)
            self.assertEqual(b.responder("Mais curto")[0], "duvida")
        b = Crivo()
        b.responder("Escreva um resumo sobre DNA")
        b.responder("E o RNA?")
        self.assertEqual(b.contexto_textual.temas, ("rna",))
        self.assertNotIn("dna", b.contexto_textual.temas)

    def test_pronomes_com_referencia_unica_e_prova(self):
        b = Crivo()
        b.responder("O que é Andrômeda?")
        ident, resposta = b.responder("Ela é uma estrela?")
        self.assertEqual(ident, "logica:negacao_comprovada")
        self.assertIn("galáxia", resposta)
        self.assertEqual(Crivo().responder("Ela é uma estrela?")[0], "duvida")
        b = Crivo()
        b.responder("Escreva um texto sobre o Sol e a Lua")
        self.assertEqual(b.responder("Ela é uma estrela?")[0], "duvida")

    def test_perguntas_coordenadas_com_conhecimento_novo(self):
        b = Crivo()
        ident, texto = b.responder("O que são DNA e RNA?")
        self.assertEqual(ident, "escrita:explicacao")
        self.assertIn("DNA", texto)
        self.assertIn("RNA", texto)
        self.assertEqual(b.responder("O que é andromeda e uma estrela?")[0], "duvida")

    def test_fontes_sao_de_unidades_utilizadas(self):
        b = Crivo()
        b.responder("O que é DNA?")
        _, fontes = b.responder("Qual é a fonte?")
        self.assertIn("genome.gov", fontes)
        self.assertNotIn("nasa", fontes.lower())
        b.responder("O que é o Sol?")
        _, fontes = b.responder("Qual é a fonte?")
        self.assertIn("não tem uma fonte externa", fontes)
        self.assertNotIn("https://", fontes)
        b.responder("O que é uma variável?")
        _, fontes = b.responder("Qual é a fonte?")
        self.assertIn("https://", fontes)
        self.assertNotIn("não tem uma fonte", fontes)

    def test_referente_nao_pode_ser_adivinhado(self):
        b = Crivo()
        b.responder("O que é a Lua?")
        self.assertNotEqual(b.responder("Qual o nome desse braço?")[0], "conhecimento:braco_orion")
        b.responder("O que é Via Láctea?")
        b.responder("Oi")
        self.assertEqual(b.responder("Qual é o nome desse braço?")[0], "contexto:sem_referencia")

    def test_modificadores_desconhecidos_nao_sao_descartados(self):
        for q in ("Escreva um texto sobre DNA e um sistema alienígena",
                  "Escreva um texto sobre Andrômeda que prove a colisão amanhã",
                  "Escreva um resumo sobre uma árvore binária",
                  "Escreva um texto sobre vírus com recomendações de remédio",
                  "Escreva um texto sobre buraco negro em alemão"):
            self.assertEqual(Crivo().responder(q)[0], "fora")

    def test_dados_malformados_sao_rejeitados(self):
        original = json.loads((PASTA / "conhecimento_expandido.json").read_text())
        alteracoes = [
            lambda d: d["itens"][0]["fatos"][0].update(fonte="ausente"),
            lambda d: d["itens"].append(copy.deepcopy(d["itens"][0])),
            lambda d: d["fontes"]["dna"].update(url="javascript:erro"),
            lambda d: d["referencias"][0].update(destino="ausente"),
            lambda d: d["aliases_preferidos"][0].update(substitui="ausente"),
            lambda d: d["itens"][0].update(id_resposta="ausente"),
        ]
        base = json.loads((PASTA / "conhecimento.json").read_text())
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "curriculo.json"
            for alterar in alteracoes:
                dados = copy.deepcopy(original)
                alterar(dados)
                arquivo.write_text(json.dumps(dados), encoding="utf-8")
                with self.assertRaises(ValueError):
                    CompositorTextual(base, arquivo, Crivo._alvo_definicao)

    def test_api_reconstroi_escrita_sem_prova_logica_falsa(self):
        r = responder_web({"message": "Em tópicos", "history": ["Escreva um texto sobre DNA e RNA"]})
        self.assertEqual(r["id"], "escrita:topicos")
        self.assertEqual(r["mechanism"], "composicao_factual")
        self.assertFalse(r["has_proof"])
        self.assertIn("DNA", r["response"])
        self.assertIn("RNA", r["response"])
        self.assertEqual(responder_web({"message": "Em tópicos"})["id"], "duvida")

    def test_conhecimento_permanece_inalterado(self):
        caminhos = [PASTA / n for n in ("conhecimento.json", "conhecimento_expandido.json", "relacoes.json")]
        antes = [p.read_bytes() for p in caminhos]
        b = Crivo()
        for q in ("Escreva um texto sobre DNA e RNA", "Mais curto", "Em tópicos", "Continue", "Qual é a fonte?"):
            b.responder(q)
        self.assertEqual(antes, [p.read_bytes() for p in caminhos])

    def test_todos_os_oito_planetas_no_grafo(self):
        r = Crivo().responder("Quais planetas orbitam o Sol?")
        self.assertEqual(r[0], "logica:consulta")
        lista = r[1].split("\n")[0]
        for nome in ("Mercúrio", "Vênus", "Terra", "Marte", "Júpiter", "Saturno", "Urano", "Netuno"):
            self.assertIn(nome, lista)


if __name__ == "__main__":
    unittest.main()
