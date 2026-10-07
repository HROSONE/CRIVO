"""Lacunas de conhecimento (06/10/2026): catálogos novos e mecanismos gerais.

Catálogos: países, estados do Brasil, esporte, história complementar, saúde
básica, ciência do dia a dia, cidadania e cultura. Mecanismos: entrada antiga
que só coincide pela metade com a pergunta não responde por ela; ficha ampla
citada de passagem não cala a resposta prática; pessoas pelo sobrenome; grafia
acentuada distinta ("Pelé" × "pele").
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "scripts"))

CATALOGOS = ("paises", "estados_brasil", "esporte", "historia_complementar", "saude_basica",
             "ciencia_cotidiana", "cidadania", "cultura")

_BOT = None


def bot():
    global _BOT
    if _BOT is None:
        from crivo import Crivo
        _BOT = Crivo()
    return _BOT


def perguntar(texto):
    from crivo import Crivo
    return Crivo().responder(texto)


class Catalogos(unittest.TestCase):
    def test_geradores_reproduzem_os_arquivos(self):
        pasta = RAIZ / "scripts" / "catalogos"
        with tempfile.TemporaryDirectory() as tmp:
            for nome in CATALOGOS:
                destino = Path(tmp) / ("%s.json" % nome)
                subprocess.run([sys.executable, "%s.py" % nome, str(destino)], cwd=pasta, check=True)
                self.assertEqual(json.loads(destino.read_text(encoding="utf-8")),
                                 json.loads((RAIZ / ("conhecimento_%s.json" % nome)).read_text(encoding="utf-8")),
                                 nome)

    def test_catalogos_entram_no_curriculo(self):
        from curriculo_mundo import ler_curriculo
        ids = {i["id"] for i in ler_curriculo(RAIZ / "conhecimento_mundo.json")["itens"]}
        for nome in CATALOGOS:
            dados = json.loads((RAIZ / ("conhecimento_%s.json" % nome)).read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(dados["itens"]), 25, nome)
            self.assertTrue({i["id"] for i in dados["itens"]} <= ids, nome)

    def test_verificador_do_acervo_sem_erros(self):
        # O verificador compara com o HEAD do git; cópia sem histórico não tem base.
        if subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True).returncode != 0:
            self.skipTest("sem repositório git para comparar com o HEAD")
        saida = subprocess.run([sys.executable, "scripts/verificar_acervo.py"], cwd=RAIZ,
                               capture_output=True, text=True)
        self.assertEqual(saida.returncode, 0, saida.stdout[-2000:])


class Mecanismos(unittest.TestCase):
    def test_entrada_antiga_pela_metade_nao_responde(self):
        # "maior país" não é "maior animal"; "escravidão no Brasil" não é
        # "climas do Brasil"; beber água não é regar planta.
        for texto, errado in (("Qual é o maior país do mundo?", "maior_animal"),
                              ("Quando acabou a escravidão no Brasil?", "climas_brasil"),
                              ("Quanta água devo beber por dia?", "regar")):
            self.assertNotEqual(perguntar(texto)[0], errado, texto)

    def test_sinonimo_desconhecido_continua_na_entrada_antiga(self):
        self.assertEqual(perguntar("de quanto em quanto tempo eu molho meu vasinho?")[0], "regar")

    def test_ficha_ampla_nao_cala_resposta_pratica(self):
        for texto, ident in (("cachorro pode comer chocolate?", "cuidar_cachorro"),
                             ("como poupar água em casa?", "agua"),
                             ("por que no Natal faz calor aqui?", "natal_verao")):
            self.assertEqual(perguntar(texto)[0], ident, texto)

    def test_definicao_nao_vira_entrada_pratica(self):
        ident, resposta = perguntar("O que é energia?")
        self.assertNotEqual(ident, "energia")

    def test_pessoa_pelo_sobrenome(self):
        ident, resposta = perguntar("Quem foi Beethoven?")
        self.assertIn("1770", resposta)

    def test_grafia_acentuada_distinta(self):
        self.assertIn("futebol", perguntar("Quem foi Pelé?")[1])
        self.assertIn("órgão", perguntar("O que é a pele?")[1])

    def test_onde_fica_sem_outras_pistas(self):
        self.assertIn("África", perguntar("Onde fica o Egito?")[1])


class Sonda(unittest.TestCase):
    def test_sonda_de_desenvolvimento(self):
        # 06/10/2026: antes 109 certos, 13 errados; depois 159 e 4.
        from avaliar_lacunas import avaliar
        r = avaliar("dev")
        self.assertGreaterEqual(r["certo"], 155, r)
        self.assertLessEqual(r["errado"], 5, r)


if __name__ == "__main__":
    unittest.main()
