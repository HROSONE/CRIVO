"""Integração de conhecimento com evidência, limites e pesos preservados."""
import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from composicao_textual import CompositorTextual
from crivo import Crivo, PASTA
from curriculo_mundo import ler_curriculo
from rede_neural import assinatura_base


class TestesAstronomiaAvancada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifesto = json.loads((PASTA / "dados/integracao_astronomia_20261001.json").read_text(encoding="utf-8"))

    def test_definicoes_aliases_e_funcionamento_disponiveis_no_motor(self):
        b = Crivo()
        palavras = lambda t: " ".join(re.findall(r"\w+", t.casefold()))
        novos = [i for i in b.compositor.itens.values() if i["id"].startswith("astro_")]
        self.assertEqual(len(novos), self.manifesto["conceitos_novos"])
        for item in novos:
            for nome in [item["nome"]] + item.get("aliases", []):
                with self.subTest(nome=nome):
                    ident, texto = b.responder("O que é " + nome + "?")
                    self.assertEqual(ident, "conhecimento:" + item["id"])
                    # A voz pode ajustar pontuação e capitalização. Todas as
                    # palavras da evidência conservam ordem e multiplicidade.
                    self.assertIn(palavras(item["fatos"][0]["texto"]), palavras(texto))
            ident, texto = b.responder("Como funciona " + item["nome"] + "?")
            self.assertEqual(ident, "escrita:explicacao")
            self.assertIn(item["fatos"][1]["texto"], texto)

    def test_evidencias_fontes_e_retomada_do_assunto(self):
        b = Crivo()
        ident, texto = b.responder("Quais são as evidências de matéria escura?")
        self.assertEqual(ident, "escrita:explicacao")
        self.assertIn("não fotografias de partículas", texto)
        self.assertEqual(b.contexto_textual.temas, ("mundo_materia_escura",))
        _, fontes = b.responder("Qual é a fonte?")
        self.assertIn("dark-matters-influence", fontes)
        self.assertIn("hubbles-gravitational-lenses", fontes)
        self.assertNotIn("Borexino", fontes)
        ident, limites = b.responder("Quais são os limites disso?")
        self.assertEqual(ident, "escrita:explicacao")
        self.assertIn("massa total do halo", limites)

    def test_limites_cientificos_nao_se_convertem_em_conclusoes_indevidas(self):
        casos = (
            ("velocidade radial", "inclinação"),
            ("Encélado", "não demonstram organismos vivos"),
            ("buraco negro", "não é automaticamente"),
            ("paralaxe", "distância física negativa"),
            ("BAO", "modelo cosmológico"),
            ("kilonova", "modelos"),
        )
        for assunto, trecho in casos:
            with self.subTest(assunto=assunto):
                ident, texto = Crivo().responder("Quais são os limites de " + assunto + "?")
                self.assertEqual(ident, "escrita:explicacao")
                self.assertIn(trecho, texto)

    def test_alvo_completo_e_ausencia_de_evidencia_nao_aproximados(self):
        for q in ("Quais são as evidências de matéria escura que prova alienígenas?",
                  "Quais são os limites de BAO inventado?",
                  "Quais são as evidências de migração planetária?",
                  "Quais são os limites de isso?"):
            with self.subTest(pergunta=q):
                b = Crivo()
                self.assertEqual(b.responder(q)[0], "fora")
                self.assertIsNone(b.contexto_textual)

    def test_consulta_generica_com_conceito_inedito_fora_de_astronomia(self):
        dados = {"versao": 1, "fontes": {"a": {"titulo": "Experimento fictício A", "url": "https://example.org/a"},
                                          "b": {"titulo": "Experimento fictício B", "url": "https://example.org/b"}},
                 "itens": [{"id": "objeto_inedito", "nome": "lumitrama", "fatos": [
                     {"papel": "definicao", "texto": "Objeto fictício de teste.", "fonte": "a"},
                     {"papel": "detalhe", "aspecto": "evidencias", "texto": "O experimento B registrou uma marca violeta.", "fonte": "b"},
                     {"papel": "limite", "texto": "Uma marca não determina a origem do objeto.", "fonte": "a"}]}]}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "catalogo.json"
            p.write_text(json.dumps(dados), encoding="utf-8")
            c = CompositorTextual([], p, lambda _: None)
            ident, texto, ctx = c.responder("Qual é a evidência de lumitrama?", None)
            self.assertEqual(ident, "escrita:explicacao")
            self.assertIn("marca violeta", texto)
            fontes = c.responder("Fontes", ctx)[1]
            self.assertIn("https://example.org/b", fontes)
            self.assertNotIn("https://example.org/a", fontes)
            self.assertEqual(c.responder("Quais são os limites de lumitrama falsa?", ctx)[0], "fora")
            self.assertIn("Uma marca não determina", c.responder("Quais são as limitações dela?", ctx)[1])
            self.assertIn("marca violeta", c.responder("Qual é a evidência disso?", ctx)[1])

    def test_novos_fatos_tem_proveniencia_local_e_fontes_auditadas(self):
        b = Crivo()
        auditoria = json.loads((PASTA / "avaliacoes/fontes_astronomia_20261001.json").read_text(encoding="utf-8"))
        verificadas = {f["chave"] for f in auditoria["fontes"] if f["status"] == 200}
        self.assertEqual(verificadas, set(self.manifesto["novas_fontes"]))
        for mudanca in self.manifesto["mudancas"]:
            item = b.compositor.itens[mudanca["id"]]
            fato = item["fatos"][mudanca["indice"]]
            self.assertEqual(fato["fonte"], mudanca["fonte"])
            if "origem_pesquisa" in fato:
                self.assertTrue((PASTA / fato["origem_pesquisa"]).is_file())
            for chave in [fato["fonte"]] + fato.get("fontes", []):
                self.assertIn(chave, b.compositor.fontes)
        self.assertFalse(self.manifesto["certificacao_alterada"])
        self.assertFalse(self.manifesto["pesos_neurais_alterados"])

    def test_pesos_existentes_continuam_compativeis(self):
        b = Crivo()
        self.assertIsNotNone(b.rede, b.erro_rede)
        conhecidas = set(b.rede.rotulos)
        self.assertEqual(assinatura_base([e for e in b.base if e["id"] in conhecidas]), b.rede.assinatura_base)
        # Desde 2026-10-07, fichas novas do acervo não invalidam a rede: as
        # entradas que ela não conhece são todas do currículo do mundo.
        self.assertTrue(all(e.get("origem_curriculo") == "mundo" for e in b.base if e["id"] not in conhecidas))
        # 241 entradas até 2026-10-03; o conteúdo de física, biologia, sociologia
        # e filosofia acrescentou 206 conceitos e a rede foi retreinada. Em
        # 2026-10-05, história, geografia, pessoas, literatura e ciências
        # acrescentaram 164, com novo retreino. Em 2026-10-06, o acervo profundo
        # acrescentou 136 (artes, sociedade, saúde, tecnologia, exatas e mente).
        self.assertEqual(len(b.rede.rotulos), 747)
        self.assertGreaterEqual(len(b.base), 747)
        self.assertTrue(set(b.rede.rotulos).isdisjoint(
            i for i in b.compositor.itens if i.startswith("astro_")))

    def test_referencia_bibliografica_nao_presume_licenca(self):
        dados = json.loads((PASTA / "conhecimento_mundo.json").read_text(encoding="utf-8"))
        chave = next(k for k, f in dados["fontes"].items() if f.get("reutilizacao") == "somente_referencia")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "curriculo.json"
            p.write_text(json.dumps(dados), encoding="utf-8")
            self.assertIsNotNone(ler_curriculo(p))
            for valor in (True, None, "false"):
                invalido = copy.deepcopy(dados)
                invalido["fontes"][chave]["reproducao_autorizada"] = valor
                p.write_text(json.dumps(invalido), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "autorização"):
                    ler_curriculo(p)


if __name__ == "__main__":
    unittest.main()
