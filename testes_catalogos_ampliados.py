"""Catálogos de história, geografia, pessoas, literatura e ciências (05/10/2026).

Conferem integração com o currículo, fontes válidas, perguntas reais e o
cuidado de não reformular perguntas cujo alvo não tem ficha.
"""
import json
import unittest
from pathlib import Path

from compreensao_intencao import reformular_identidade
from curriculo_mundo import ler_curriculo
from web_core import responder_web

RAIZ = Path(__file__).resolve().parent
CATALOGOS = ("historia", "geografia", "pessoas", "literatura", "ciencias")


def perguntar(texto, historico=()):
    return responder_web({"message": texto, "history": list(historico)})


class Integracao(unittest.TestCase):
    def test_catalogos_entram_no_curriculo_validado(self):
        curriculo = ler_curriculo(RAIZ / "conhecimento_mundo.json")
        ids = {i["id"] for i in curriculo["itens"]}
        for nome in CATALOGOS:
            dados = json.loads((RAIZ / ("conhecimento_%s.json" % nome)).read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(dados["itens"]), 20, nome)
            self.assertTrue({i["id"] for i in dados["itens"]} <= ids, nome)

    def test_todo_fato_tem_fonte_https_com_direitos(self):
        for nome in CATALOGOS:
            dados = json.loads((RAIZ / ("conhecimento_%s.json" % nome)).read_text(encoding="utf-8"))
            for fonte in dados["fontes"].values():
                self.assertTrue(fonte["url"].startswith("https://"))
                self.assertTrue(fonte["direitos_url"].startswith("https://"))
            for item in dados["itens"]:
                self.assertEqual(item["fatos"][0]["papel"], "definicao", item["id"])

    def test_geradores_reproduzem_os_arquivos(self):
        import subprocess
        import sys
        import tempfile
        pasta = RAIZ / "scripts" / "catalogos"
        with tempfile.TemporaryDirectory() as tmp:
            for nome in CATALOGOS:
                destino = Path(tmp) / ("%s.json" % nome)
                subprocess.run([sys.executable, "%s.py" % nome, str(destino)], cwd=pasta, check=True,
                               env={"CRIVO_RAIZ": str(RAIZ), "PATH": ""})
                self.assertEqual(json.loads(destino.read_text(encoding="utf-8")),
                                 json.loads((RAIZ / ("conhecimento_%s.json" % nome)).read_text(encoding="utf-8")),
                                 nome)


class PerguntasReais(unittest.TestCase):
    def test_quem_foi_e_o_que_foi_usam_a_ficha(self):
        for texto, ident, termo in (
                ("Quem foi Marie Curie?", "conhecimento:mundo_marie_curie", "radioatividade"),
                ("Quem foi Zumbi dos Palmares?", "conhecimento:mundo_zumbi_dos_palmares", "Palmares"),
                ("Quem foi Einstein?", "conhecimento:mundo_albert_einstein", "relatividade"),
                ("O que foi a Revolução Francesa?", "conhecimento:mundo_revolucao_francesa", "1789"),
                ("Quem escreveu Dom Casmurro?", "conhecimento:mundo_dom_casmurro", "Machado de Assis"),
                ("Quando foi a abolição da escravidão no Brasil?", "conhecimento:mundo_abolicao_brasil", "1888"),
                ("O que aconteceu na Segunda Guerra Mundial?", "conhecimento:mundo_segunda_guerra", "1939")):
            r = perguntar(texto)
            self.assertEqual(r["id"], ident, texto)
            self.assertIn(termo, r["response"], texto)

    def test_assuntos_novos_respondem_com_fonte(self):
        for texto, termo in (("O que é o Cerrado?", "savana"), ("O que é um número primo?", "divisível"),
                             ("O que é inflação?", "preços"), ("O que é enredo?", "acontecimentos"),
                             ("O que é a tabela periódica?", "número atômico"), ("O que é pH?", "ácido")):
            self.assertIn(termo, perguntar(texto)["response"], texto)
        fonte = perguntar("Qual é a fonte?", ["O que é a Mesopotâmia?"])
        self.assertIn("openstax.org", fonte["response"])

    def test_pessoa_platao_nao_e_mais_apelido_da_teoria_das_formas(self):
        self.assertEqual(perguntar("Quem foi Platão?")["id"], "conhecimento:mundo_platao")
        self.assertEqual(perguntar("O que é a teoria das formas?")["id"], "conhecimento:mundo_teoria_formas")


class SemFichaNaoReformula(unittest.TestCase):
    def test_alvos_sem_ficha_ou_genericos(self):
        conhecidos = {"marie curie", "dom casmurro"}
        reconhecer = lambda alvo: alvo.casefold() in conhecidos
        for texto in ("Quem é você?", "O que foi isso?", "Quem descobriu o Brasil?",
                      "Quem foi o primeiro presidente?", "Quem foi Marie Curie na Lua?"):
            self.assertIsNone(reformular_identidade(texto, reconhecer), texto)
        self.assertEqual(reformular_identidade("Quem foi Marie Curie?", reconhecer), "O que é Marie Curie?")
        self.assertEqual(perguntar("Quem é você?")["id"], "social:quem")


if __name__ == "__main__":
    unittest.main()
