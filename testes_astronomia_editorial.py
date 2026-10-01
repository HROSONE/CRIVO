"""Testes de desenvolvimento: ampliação editorial de astronomia, sem alegar treino neural."""
import unittest
from crivo import Crivo, PASTA
from curriculo_mundo import ler_curriculo

NOVOS = ("planeta", "satélite natural", "asteroide", "meteoroide", "meteorito", "cinturão de kuiper", "nuvem de oort", "unidade astronômica", "órbita", "disco protoplanetário", "acréscimo planetário", "protoestrela", "planetesimal", "diferenciação planetária", "zona habitável", "fusão estelar", "evolução estelar")

class TestesAstronomiaEditorial(unittest.TestCase):
    def test_conceitos_e_proveniencia(self):
        curriculo = ler_curriculo(PASTA / "conhecimento_mundo.json")
        por_nome = {i["nome"]: i for i in curriculo["itens"]}
        for nome in NOVOS:
            with self.subTest(nome=nome):
                self.assertIn(nome, por_nome)
                item = por_nome[nome]
                self.assertEqual(item["fatos"][0]["papel"], "definicao")
                self.assertIn(item["fatos"][0]["fonte"], curriculo["fontes"])
                self.assertEqual(item["area"], "astronomia")

    def test_consulta_basica_de_assuntos_distintos(self):
        bot = Crivo()
        for nome in NOVOS:
            with self.subTest(nome=nome):
                identificador, resposta = bot.responder("O que é " + nome + "?")
                self.assertTrue(identificador.startswith("conhecimento:mundo_"), (nome, identificador))
                self.assertTrue(resposta.strip())

    def test_desconhecido_nao_recebe_resposta_inventada(self):
        for pergunta in ("O que é o planeta Zorvax-913?", "O que é a estrela Fictícia-XY99?"):
            with self.subTest(pergunta=pergunta):
                identificador, _ = Crivo().responder(pergunta)
                self.assertEqual(identificador, "fora")


    def test_formacao_e_mecanismos_documentados(self):
        curriculo = ler_curriculo(PASTA / "conhecimento_mundo.json")
        from pathlib import Path
        import json
        expandido = json.loads((PASTA / "conhecimento_expandido.json").read_text(encoding="utf-8"))
        itens = {item["nome"].lower(): item for item in expandido["itens"]}
        itens.update({item["nome"].lower(): item for item in curriculo["itens"]})
        fontes = dict(expandido["fontes"])
        fontes.update(curriculo["fontes"])
        expectativas = {
            "planeta": ("formacao", "funcionamento"),
            "estrela": ("formacao", "funcionamento"),
            "sistema solar": ("formacao", "funcionamento"),
            "disco protoplanetário": ("definicao", "detalhe"),
            "acréscimo planetário": ("definicao", "detalhe"),
            "protoestrela": ("definicao", "detalhe"),
            "planetesimal": ("definicao", "detalhe"),
            "diferenciação planetária": ("definicao", "detalhe"),
            "zona habitável": ("definicao", "limite"),
        }
        for nome, papeis in expectativas.items():
            with self.subTest(conceito=nome):
                self.assertIn(nome, itens)
                fatos = itens[nome]["fatos"]
                self.assertGreaterEqual(len(fatos), 3)
                self.assertTrue(all(f["fonte"] in fontes for f in fatos))
                for aspecto in papeis:
                    self.assertTrue(any(f["papel"] == aspecto or f.get("aspecto") == aspecto for f in fatos), (nome, aspecto))

    def test_limites_cientificos_explicitos(self):
        curriculo = ler_curriculo(PASTA / "conhecimento_mundo.json")
        import json
        expandido = json.loads((PASTA / "conhecimento_expandido.json").read_text(encoding="utf-8"))
        itens = {item["nome"].lower(): item for item in expandido["itens"]}
        itens.update({item["nome"].lower(): item for item in curriculo["itens"]})
        for nome in ("planeta", "estrela", "sistema solar", "zona habitável"):
            with self.subTest(conceito=nome):
                self.assertTrue(any(f["papel"] == "limite" for f in itens[nome]["fatos"]))


    def test_formacao_e_funcionamento_sao_consultaveis(self):
        casos = (
            ("Como se forma uma estrela?", "escrita:explicacao", ("nuvens moleculares", "protoestrela")),
            ("Como nasce uma estrela?", "escrita:explicacao", ("nuvens moleculares", "protoestrela")),
            ("Como se forma um planeta?", "escrita:explicacao", ("discos de gás", "planetesimais")),
            ("Como surgiu o sistema solar?", "escrita:explicacao", ("4,6 bilhões", "disco")),
            ("Como funciona uma estrela?", "escrita:explicacao", ("fusão", "núcleo")),
            ("Como funciona o sistema solar?", "escrita:explicacao", ("gravidade", "órbitas")),
        )
        for pergunta, esperado, palavras in casos:
            with self.subTest(pergunta=pergunta):
                obtido, resposta = Crivo().responder(pergunta)
                self.assertEqual(obtido, esperado, (pergunta, resposta))
                for palavra in palavras:
                    self.assertIn(palavra.lower(), resposta.lower())

    def test_aspectos_multiplos_sem_fatos_repetidos_ou_adivinhados(self):
        """Um aspecto pode ter várias evidências independentes, não conclusões inventadas."""
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta) / "conhecimento.json"
            base.write_text(json.dumps([dict(id="ola", topico="social",
                perguntas=["oi"], resposta="Oi.")]), encoding="utf-8")
            curriculo = dict(versao=1, fontes={"f": ler_curriculo(PASTA / "conhecimento_mundo.json")["fontes"]["nasa_glossario"]},
                itens=[dict(id="mundo_brilum", nome="brilum", area="ficcao", aliases=[],
                    fatos=[
                        dict(texto="Brilum é uma estrela fictícia.", fonte="f",
                             papel="definicao", natureza="cientifico"),
                        dict(texto="Brilum surge quando grãos fictícios colidem.", fonte="f",
                             papel="detalhe", aspecto="formacao", natureza="cientifico"),
                        dict(texto="A fase seguinte recebe matéria do disco.", fonte="f",
                             papel="detalhe", aspecto="formacao", natureza="cientifico"),
                    ])])
            (Path(pasta) / "conhecimento_mundo.json").write_text(
                json.dumps(curriculo), encoding="utf-8")
            bot = Crivo(base)
            ident, texto = bot.responder("Como se forma brilum?")
            self.assertEqual(ident, "escrita:explicacao")
            self.assertIn("grãos fictícios", texto)
            self.assertIn("recebe matéria", texto)
            self.assertEqual(bot.responder("Como se forma zirvax?")[0], "fora")


    def test_nova_terminologia_nao_bloqueia_consultas_anteriores(self):
        pares = (
            ("quantos planetas existem no nosso sistema solar?", "planetas"),
            ("plutão ainda é considerado planeta?", "plutao"),
            ("qual planeta é o maior de todos?", "maior_planeta"),
            ("A Lua orbita Júpiter?", "logica:desconhecido"),
            ("A Lua orbita o Sol?", "logica:desconhecido"),
            ("A Via Láctea faz parte da Terra?", "logica:desconhecido"),
        )
        for pergunta, esperado in pares:
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], esperado)



    def test_sem_dupla_identidade_para_termos_ja_conhecidos(self):
        """A expansão aprofunda conceitos anteriores em vez de inventar IDs concorrentes."""
        import json
        from composicao_textual import normalizar
        mundo = ler_curriculo(PASTA / "conhecimento_mundo.json")
        expandido = json.loads((PASTA / "conhecimento_expandido.json").read_text(encoding="utf-8"))
        nomes_mundo = {normalizar(i["nome"]) for i in mundo["itens"]}
        nomes_exp = {normalizar(i["nome"]) for i in expandido["itens"]}
        self.assertFalse(nomes_mundo & nomes_exp, nomes_mundo & nomes_exp)
        for nome in ("galáxia", "estrela", "sistema solar", "exoplaneta",
                     "nebulosa", "buraco negro", "ano-luz"):
            with self.subTest(conceito=nome):
                item = next(i for i in expandido["itens"] if normalizar(i["nome"]) == normalizar(nome))
                self.assertTrue(any(f["fonte"].startswith("nasa_") for f in item["fatos"]))
                self.assertTrue(any(f["papel"] == "limite" for f in item["fatos"]))
                self.assertLessEqual(len(item["fatos"]), 12)

    def test_primeiro_modulo_requer_limites_para_todos_os_termos(self):
        curriculo = ler_curriculo(PASTA / "conhecimento_mundo.json")
        astronomia = [x for x in curriculo["itens"] if x["area"] == "astronomia"]
        self.assertGreaterEqual(len(astronomia), 20)
        for item in astronomia:
            with self.subTest(conceito=item["nome"]):
                self.assertEqual(item["fatos"][0]["papel"], "definicao")
                self.assertTrue(any(f["papel"] == "limite" for f in item["fatos"]))
                self.assertTrue(all(f["fonte"] in curriculo["fontes"] for f in item["fatos"]))
                self.assertTrue(all(curriculo["fontes"][f["fonte"]]["direitos_url"].startswith("https://")
                                    for f in item["fatos"]))

if __name__ == "__main__":
    unittest.main()
