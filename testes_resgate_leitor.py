"""Contratos do resgate final; fixtures sintéticas não medem qualidade neural."""
import json
import hashlib
import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

try:
    import numpy as np
except ImportError:
    np = None

from crivo import Crivo
from leitura_ficha import Leitura, LeituraFicha, TRACOS
from resgate_leitor import ResgateLeitor, TRACOS_RESGATE, evidencias
import estado_interno
from verificacao_campo_factual import verificar_campo


class Artefato(unittest.TestCase):
    def test_ausente_ou_nao_aprovado_nao_carrega_pesos(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            self.assertFalse(ResgateLeitor(pasta).disponivel)
            (pasta / "meta.json").write_text(json.dumps({"controle": {"aprovado": False}}))
            with patch("leitor_transformer.LeitorTransformer") as loader:
                self.assertFalse(ResgateLeitor(pasta).disponivel)
                loader.assert_not_called()

    def test_metadados_corrompidos_ficam_desligados(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            for meta in ([], None, {"controle": None}, {"controle": "aprovado"}):
                (pasta / "meta.json").write_text(json.dumps(meta))
                self.assertFalse(ResgateLeitor(pasta).disponivel)

    @unittest.skipIf(np is None, "NumPy ausente")
    def test_cabeca_exige_hash_formato_e_pesos_finitos(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            (pasta / "pesos_numpy.npz").write_bytes(b"base sintetica propria do teste")
            (pasta / "tokenizer.json").write_text("{}")
            meta = {"controle": {"aprovado": True}, "escopo": "resgate_aproximacao",
                    "verificacao": "campo_explicito_v1",
                    "tracos": list(TRACOS_RESGATE), "pesos": [0.0] * len(TRACOS_RESGATE),
                    "limiar": 0.8, "fontes": {}}
            base = SimpleNamespace(disponivel=True, modelo=SimpleNamespace(
                np=np, p={"cabeca.weight": np.zeros((1, 2)), "cabeca.bias": np.zeros(1)}))
            for pesos, valido in (({"cabeca.weight": np.ones((1, 2)), "cabeca.bias": np.ones(1)}, True),
                                   ({"cabeca.weight": np.ones((1, 3)), "cabeca.bias": np.ones(1)}, False),
                                   ({"cabeca.weight": np.full((1, 2), np.nan), "cabeca.bias": np.ones(1)}, False),
                                   ({"cabeca.weight": np.ones((1, 2)), "cabeca.bias": np.ones(1), "extra": np.ones(1)}, False)):
                np.savez(pasta / "cabeca_revisada.npz", **pesos)
                for nome, arquivo in (("base_sha256", "pesos_numpy.npz"), ("tokenizer_sha256", "tokenizer.json"),
                                      ("cabeca_sha256", "cabeca_revisada.npz")):
                    meta["fontes"][nome] = hashlib.sha256((pasta / arquivo).read_bytes()).hexdigest()
                (pasta / "meta.json").write_text(json.dumps(meta))
                with patch("leitor_transformer.LeitorTransformer", return_value=base):
                    self.assertEqual(ResgateLeitor(pasta, pasta).disponivel, valido)
            meta["fontes"]["cabeca_sha256"] = "0" * 64
            (pasta / "meta.json").write_text(json.dumps(meta))
            with patch("leitor_transformer.LeitorTransformer") as loader:
                self.assertFalse(ResgateLeitor(pasta, pasta).disponivel)
                loader.assert_not_called()

    def test_aprovacao_nao_ignora_contrato_hashes_ou_numeros_invalidos(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            meta = {"controle": {"aprovado": True}, "escopo": "resgate_aproximacao",
                    "verificacao": "campo_explicito_v1",
                    "tracos": list(TRACOS_RESGATE), "pesos": [0.0] * len(TRACOS_RESGATE),
                    "limiar": 0.8, "fontes": {}}
            for campo, invalido in (("tracos", []), ("pesos", [math.nan] * len(TRACOS_RESGATE)),
                                    ("limiar", math.inf), ("limiar", 1.1), ("fontes", {})):
                invalida = dict(meta, **{campo: invalido})
                (pasta / "meta.json").write_text(json.dumps(invalida))
                self.assertFalse(ResgateLeitor(pasta, pasta).disponivel)


class Evidencia(unittest.TestCase):
    def test_margens_usam_outros_fatos_e_ordem_do_treinamento(self):
        t = dict(zip(TRACOS, range(len(TRACOS))))
        x = evidencias([0.7, 0.9, 0.2], [0.6, 0.4, 0.1], 1, t)
        self.assertEqual(len(x), len(TRACOS_RESGATE))
        self.assertEqual(x[:2], [1.0, 0.9])
        self.assertAlmostEqual(x[2], 0.2)
        self.assertAlmostEqual(x[4], -0.2)
        self.assertEqual(x[5], t["relacao"])
        self.assertAlmostEqual(x[-1], math.log1p(3) / 3)

    def test_criterio_semantico_nunca_autoriza_afirmacao(self):
        leitor = LeituraFicha(Crivo(usar_geracao=False).compositor, resgate=False)
        l = Leitura("mundo_tita", 0, 1.0, 1.0, 10, "qual",
                    {"resgate_semantico": True, "todas": 1.0})
        self.assertFalse(leitor.afirma(l))
        self.assertEqual(leitor.decisao(l), "aproximar")


class CampoFactual(unittest.TestCase):
    def test_ano_de_publicacao_nao_e_contagem_de_capitulos(self):
        f = "O livro foi publicado em 1901 e contém uma história sobre viagens."
        self.assertIsNone(verificar_campo("Quantos capítulos tem o livro?", f, {"todas": 1}))
        self.assertEqual(verificar_campo("Quantos capítulos tem o livro?", "O livro tem 12 capítulos.", {}), "contagem")

    def test_data_nao_substitui_duracao_e_unidades_respeitam_dimensao(self):
        self.assertIsNone(verificar_campo("Quanto tempo dura a viagem?", "A viagem ocorreu em 1901.", {}))
        self.assertEqual(verificar_campo("Quanto tempo dura a viagem?", "A viagem dura três horas.", {}), "duracao")
        self.assertIsNone(verificar_campo("Qual é a massa do objeto?", "O objeto mede 12 metros.", {"todas": 1}))
        self.assertEqual(verificar_campo("Qual é a massa do objeto?", "O objeto pesa 12 kg.", {}), "massa")

    def test_fundamental_ou_cristal_nao_atribuem_criacao(self):
        self.assertIsNone(verificar_campo("Quem criou o método?", "O método é fundamental no estudo de cristais.", {}))
        self.assertEqual(verificar_campo("Quem criou o método?", "O método foi criado por Joana.", {}), "criacao")

    def test_velocidade_area_e_volume_nao_sao_comprimento(self):
        pergunta = "Qual é o comprimento do objeto?"
        for unidade in ("km/h", "m / s", "quilômetros por hora", "metros por segundo",
                        "km^2", "km²", "m³", "metros quadrados", "metros cúbicos"):
            with self.subTest(unidade=unidade):
                self.assertIsNone(verificar_campo(pergunta, "O objeto tem 12 " + unidade + ".", {}))
        for unidade in ("km", "m", "cm", "quilômetros", "metros", "anos-luz"):
            with self.subTest(unidade=unidade):
                self.assertEqual(verificar_campo(pergunta, "O objeto mede 12 " + unidade + ".", {}), "comprimento")

    def test_simbolos_da_unidade_e_da_moeda_sao_preservados(self):
        self.assertEqual(verificar_campo("Qual é a velocidade do veículo?", "O veículo alcança 12 km/h.", {}), "velocidade")
        self.assertEqual(verificar_campo("Qual é a temperatura do objeto?", "O objeto está a 12 °C.", {}), "temperatura")
        self.assertEqual(verificar_campo("Quanto custa o objeto?", "O objeto custa R$ 12.", {}), "preco")

    def test_citar_pessoa_nao_a_torna_autora(self):
        self.assertIsNone(verificar_campo("Quem escreveu o romance?", "A personagem conversa com Joana.", {}))
        self.assertEqual(verificar_campo("Quem escreveu o romance?", "O romance é uma obra de Joana.", {}), "autoria")

    def test_definir_estrutura_nao_enumera_composicao(self):
        self.assertIsNone(verificar_campo("Qual é a composição do aparelho?", "O aparelho ajuda a fabricar peças.", {"todas": 1}))
        self.assertEqual(verificar_campo("Qual é a composição do aparelho?", "O aparelho é formado por cobre e aço.", {}), "composicao")

    def test_nacionalidade_exige_pessoa_e_origem(self):
        f = "Joana é uma escritora brasileira."
        self.assertEqual(verificar_campo("De que país era Joana?", f, {}, area="pessoas"), "origem_pessoa")
        self.assertIsNone(verificar_campo("De que país era o planeta?", f, {}, area="astronomia"))

    def test_campo_generico_nao_passa_sem_todas_as_pistas(self):
        self.assertIsNone(verificar_campo("Como o processo funciona?", "O processo acontece em etapas.", {"todas": 0}))
        self.assertEqual(verificar_campo("Como o processo funciona?", "O processo acontece em etapas.", {"todas": 1}), "pistas")


class Sugestao(unittest.TestCase):
    def setUp(self):
        self.bot = Crivo(usar_geracao=False)
        self.leitor = LeituraFicha(self.bot.compositor, resgate=False)
        self.leitor.decisao = Mock(return_value=None)
        self.resgate = object.__new__(ResgateLeitor)
        self.resgate.disponivel = True
        self.resgate.verificar_campo = True
        self.resgate.pesos = [10.0] + [0.0] * (len(TRACOS_RESGATE) - 1)
        self.resgate.limiar = 0.8
        self.resgate.transformer = Mock()
        self.q = self.bot.compositor.interpretar("Quem escreveu Memórias Póstumas de Brás Cubas?")
        n = len(self.bot.compositor.itens[self.q.assunto]["fatos"])
        self.resgate.transformer.probabilidades.return_value = [0.9] + [0.1] * (n - 1)

    def test_sugestao_mantem_indice_da_ficha_e_indica_aproximacao(self):
        l = self.resgate.sugerir(self.leitor, self.q)
        self.assertIsNotNone(l)
        self.assertEqual(l.assunto, self.q.assunto)
        self.assertEqual(l.indice, 0)
        self.assertTrue(l.tracos["resgate_semantico"])
        self.assertEqual(l.tracos["campo_verificado"], "autoria")

    def test_resposta_literal_aceita_nao_consulta_transformer(self):
        self.leitor.decisao.return_value = "afirmar"
        self.assertIsNone(self.resgate.sugerir(self.leitor, self.q))
        self.resgate.transformer.probabilidades.assert_not_called()

    def test_probabilidade_invalida_ou_empate_nao_propoe_fato(self):
        n = len(self.resgate.transformer.probabilidades.return_value)
        for p in ([], [math.nan] * n, [1.1] * n, [0.9] * n):
            self.resgate.transformer.probabilidades.return_value = p
            self.assertIsNone(self.resgate.sugerir(self.leitor, self.q))

    def test_absoluto_negacao_e_pedido_nao_consultam_transformer(self):
        for q in ("Como o cérebro tem memória infinita?", "Titã não tem chuva?",
                  "Explique a chuva em Titã?"):
            quadro = self.bot.compositor.interpretar(q)
            self.assertIsNone(self.resgate.sugerir(self.leitor, quadro))
        self.resgate.transformer.probabilidades.assert_not_called()


class Integracao(unittest.TestCase):
    def test_resposta_existente_nao_consulta_resgate(self):
        bot = Crivo(usar_geracao=False)
        rescue = Mock()
        bot._leitura_ficha = LeituraFicha(bot.compositor, resgate=rescue)
        ident, resposta = bot.responder("O que é Júpiter?")
        self.assertIn("Júpiter", resposta)
        self.assertNotEqual(ident, "leitura:aproximacao")
        rescue.sugerir.assert_not_called()

    def test_autoria_e_pergunta_factual_mas_imperativo_fica_fora(self):
        bot = Crivo(usar_geracao=False)
        estado = estado_interno.construir(bot, "Quem escreveu Memórias Póstumas de Brás Cubas?")
        self.assertTrue(estado_interno._pode_ler(estado, autoria=True))
        for q in ("Escreva frases sobre Titã?", "Titã não tem chuva?", "Qual sua opinião sobre Titã?"):
            estado = estado_interno.construir(bot, q)
            self.assertFalse(estado_interno._pode_ler(estado, autoria=True))

    def test_apenas_recusa_final_e_revisavel_pode_ser_resgatada(self):
        bot = Crivo(usar_geracao=False)
        estado = estado_interno.construir(bot, "Chove em Titã?")
        rescue = Mock()
        bot._leitura_ficha = LeituraFicha(bot.compositor, resgate=rescue)
        for ident in ("duvida", "logica:desconhecido", "escrita:explicacao"):
            original = (ident, "Não tenho essa resposta.")
            self.assertEqual(estado_interno.resgatar(bot, estado, *original), original)
        rescue.sugerir.assert_not_called()

    def test_resgate_entrega_fato_inteiro_fonte_e_aviso(self):
        bot = Crivo(usar_geracao=False)
        estado = estado_interno.construir(bot, "Chove em Titã?")
        assunto = estado.entidade.id
        l = Leitura(assunto, 0, 0.99, 0.4, 0, "simnao",
                    {"resgate_semantico": True, "prob_transformer": 0.95, "campo_verificado": "pistas"})
        bot._leitura_ficha = LeituraFicha(bot.compositor, resgate=SimpleNamespace(sugerir=lambda *a: l))
        ident, resposta = estado_interno.resgatar(bot, estado, "fora", "Não tenho evidência.")
        self.assertEqual(ident, "leitura:aproximacao")
        self.assertTrue(resposta.startswith("Não tenho uma resposta exata"))
        self.assertIn(bot.compositor.itens[assunto]["fatos"][0]["texto"], resposta)
        self.assertTrue(bot.historico[-1]["leitura"]["semantic_rescue"])
        self.assertEqual(bot.historico[-1]["leitura"]["verified_field"], "pistas")
        self.assertEqual(estado.decisao["acao"], "aproximar")


if __name__ == "__main__":
    unittest.main()
