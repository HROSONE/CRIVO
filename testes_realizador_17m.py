"""Voz experimental do 17M: desligada por padrão, travada por SHA e conferida antes de falar."""
import os
import unittest
from unittest import mock

import quadro_fala
import realizador_17m
from crivo import Crivo


class Falso:
    """Realizador de teste: devolve a frase que o teste mandar."""
    def __init__(self, texto, terminou=True):
        self.texto, self.terminou, self.chamadas = texto, terminou, []

    def realizar(self, quadro, mensagem):
        self.chamadas.append((quadro, mensagem))
        return self.texto, self.terminou


class Travas(unittest.TestCase):
    def test_desligado_por_padrao(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR", None)
            self.assertFalse(realizador_17m.habilitado())
            bot = Crivo()
            bot.responder("O que é a Lua?")
            self.assertNotIn("realizador", bot.historico[-1])

    def test_duas_travas(self):
        with mock.patch.dict(os.environ, {"CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR": "1"}):
            os.environ.pop("CRIVO_REALIZADOR_DIR", None)
            self.assertFalse(realizador_17m.habilitado())

    def test_pesos_errados_nao_carregam(self):
        with self.assertRaises(Exception):
            realizador_17m.Realizador(realizador_17m.RAIZ)  # sem pesos aprovados aqui

    def test_formato_e_o_do_treino(self):
        self.assertTrue(hasattr(realizador_17m.formato(), "avaliar_saida"))


class Api(unittest.TestCase):
    def test_status_publico(self):
        st = realizador_17m.status()
        self.assertEqual(st["pesos_sha256"], realizador_17m.PESOS_SHA256)
        self.assertTrue(st["decisao"]["site_publico"])
        self.assertEqual(st["decisao"]["padrao_linha_de_comando"], "desligado")
        self.assertFalse(st["external_ai"])

    def test_resposta_da_api_sem_travas_nao_mostra_voz(self):
        from web_core import responder_web
        os.environ.pop("CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR", None)
        self.assertNotIn("experimental_voice", responder_web({"message": "Meu gato se chama Tupo."}))


class Numpy(unittest.TestCase):
    """Os pesos NumPy do site: conferidos pelo SHA, com prazo, ligados só no servidor."""

    def test_pesos_do_site_carregam(self):
        voz = realizador_17m.numpy_do_site()
        self.assertIsNotNone(voz, "artefatos/realizador_pt ausente ou com SHA diferente")
        self.assertEqual(voz.prazo, realizador_17m.PRAZO_SITE)
        self.assertTrue(realizador_17m.status()["site"]["ligado"])

    def test_npz_diferente_e_recusado(self):
        with mock.patch.object(realizador_17m, "NPZ_SHA256", "0" * 64):
            with self.assertRaises(RuntimeError):
                realizador_17m.RealizadorNumpy()

    def test_prazo_estourado_nao_termina(self):
        voz = realizador_17m.numpy_do_site()
        voz_curta = object.__new__(realizador_17m.RealizadorNumpy)
        voz_curta.__dict__.update(voz.__dict__, prazo=1e-9)
        _, terminou = voz_curta.realizar({"ato": "acolher", "sentimento": "triste"}, "Estou triste hoje.")
        self.assertFalse(terminou)

    def test_site_usa_a_voz_e_a_linha_de_comando_nao(self):
        from web_core import responder_web
        os.environ.pop("CRIVO_DISABLE_REALIZADOR", None)
        # Com a v3 D ligada ela fala em tudo (conversa_v3d.py); a fase 3 é a voz quando ela está desligada.
        with mock.patch.dict(os.environ, {"CRIVO_DISABLE_CONVERSA_V3D": "1"}):
            r = responder_web({"message": "Meu gato se chama Tupo."}, voz_17m=True)
        self.assertTrue(r["experimental_voice"]["used"], r["experimental_voice"])
        self.assertIn("Tupo", r["response"])
        with mock.patch.dict(os.environ, {"CRIVO_DISABLE_REALIZADOR": "1", "CRIVO_DISABLE_CONVERSA_V3D": "1"}):
            r = responder_web({"message": "Meu gato se chama Tupo."}, voz_17m=True)
            self.assertNotIn("experimental_voice", r)
        self.assertNotIn("experimental_voice", responder_web({"message": "Meu gato se chama Tupo."}))


class PacoteDoSite(unittest.TestCase):
    """Só os arquivos que a Vercel leva (vercel.json): a voz precisa falar lá também."""

    def test_voz_fala_no_pacote_da_vercel(self):
        import json
        import shutil
        import subprocess
        import sys
        import tempfile
        from pathlib import Path
        raiz = Path(realizador_17m.RAIZ)
        padrao = json.loads((raiz / "vercel.json").read_text())["functions"]["api/chat.py"]["includeFiles"]
        arquivos = {p for exp in padrao.strip("{}").split(",") for p in raiz.glob(exp) if p.is_file()}
        arquivos.add(raiz / "api" / "chat.py")
        with tempfile.TemporaryDirectory() as pasta:
            for p in arquivos:
                destino = Path(pasta) / p.relative_to(raiz)
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, destino)
            script = ("import sys,json;sys.path.insert(0,sys.argv[1]);from web_core import responder_web;"
                      "r=responder_web({'message':'Meu gato se chama Tupo.'},voz_17m=True);"
                      "print(json.dumps([r.get('conversation_voice') or r['experimental_voice'],r['response']]))")
            ambiente = {k: v for k, v in os.environ.items() if k not in ("CRIVO_DISABLE_REALIZADOR",
                                                                          "CRIVO_DISABLE_CONVERSA_V3D")}
            # As duas vozes falam no pacote: a v3 D (padrão) e a fase 3 (com a D desligada).
            for extra in ({}, {"CRIVO_DISABLE_CONVERSA_V3D": "1"}):
                r = subprocess.run([sys.executable, "-I", "-c", script, pasta], cwd=pasta, capture_output=True,
                                   text=True, timeout=120, env={**ambiente, **extra})
                self.assertEqual(r.returncode, 0, r.stderr)
                voz, texto = json.loads(r.stdout.strip().splitlines()[-1])
                self.assertTrue(voz["used"], (extra, voz))
                self.assertIn("Tupo", texto)


class Adaptador(unittest.TestCase):
    def quadro(self, *falas):
        bot = Crivo()
        for f in falas:
            ident, resp = bot.responder(f)
        return quadro_fala.quadro_do_turno(bot, falas[-1], ident, resp)

    def test_atos(self):
        self.assertEqual(self.quadro("Meu gato se chama Tupo.")["ato"], "registrar")
        self.assertEqual(self.quadro("Meu gato se chama Tupo.", "Qual é o nome do meu gato?"),
                         {"ato": "recordar", "relacao": "gato", "nome": "Tupo"})
        # A pessoa corrigiu a própria informação: registro novo, sem "desculpa, errei".
        self.assertEqual(self.quadro("Meu gato se chama Tupo.", "Na verdade, meu gato se chama Dano."),
                         {"ato": "registrar", "relacao": "gato", "nome": "Dano"})
        q = self.quadro("O que é a Lua?")
        self.assertEqual(q["ato"], "explicar")
        self.assertTrue(q["fatos"])
        self.assertEqual(self.quadro("Estou triste hoje."), {"ato": "acolher", "sentimento": "triste"})
        self.assertEqual(self.quadro("O que é um zorblax?"), {"ato": "nao_sei", "assunto": "zorblax"})

    def test_atos_da_porta_v3(self):
        self.assertEqual(self.quadro("Você é o quê?"), {"ato": "falar_de_si", "ponto": "quem_e"})
        self.assertEqual(self.quadro("Você sente alguma coisa?"), {"ato": "falar_de_si", "ponto": "sentir"})
        self.assertEqual(self.quadro("Você é só um robô."), {"ato": "falar_de_si", "ponto": "robo"})
        self.assertEqual(self.quadro("Preciso de uma ajuda."), {"ato": "esclarecer", "falta": "detalhe"})
        self.assertEqual(self.quadro("Quem fundou a empresa Zorvek?"), {"ato": "nao_sei", "assunto": "Zorvek"})
        # Sem nome próprio o 17M troca o assunto ("jato"): fica o "não sei" do próprio CRIVO.
        self.assertIsNone(self.quadro("Como funciona um motor a jato?"))
        self.assertIsNone(self.quadro("Oi, tudo bem?"))
        self.assertIsNone(self.quadro("Você é uma IA?"))
        self.assertIsNone(self.quadro("tem como uma pessoa morrer dormindo?"))
        self.assertIsNone(self.quadro("Quero morrer"))

    def test_pergunta_aberta_sem_resposta_diz_que_nao_sabe(self):
        _, texto = Crivo().responder("Quem inventou o carro?")
        self.assertIn("ainda não sei", texto)
        self.assertNotIn("não entendi", texto)
        _, texto = Crivo().responder("tem como uma pessoa morrer dormindo?")
        self.assertNotIn("chutar", texto)

    def test_sem_quadro_fica_o_texto_de_sempre(self):
        self.assertIsNone(self.quadro("Quanto é 2 mais 2?"))
        # Relação que o realizador não treinou (feminino) e cumprimento com período do dia.
        self.assertIsNone(self.quadro("Tenho uma irmã chamada Lia."))
        self.assertIsNone(self.quadro("Boa noite!"))
        # Resposta com aviso ("Vale lembrar que…") além dos fatos: o aviso não pode sumir.
        self.assertIsNone(self.quadro("O que é um buraco negro?"))
        self.assertIsNone(self.quadro("Escreva um texto sobre a Lua em duas frases."))


class Conferencia(unittest.TestCase):
    def falar(self, frase_falsa, *falas):
        bot = Crivo()
        bot.realizador = Falso(frase_falsa)
        for f in falas:
            ident, texto = bot.responder(f)
        return bot, texto

    def test_frase_aprovada_e_usada(self):
        bot, texto = self.falar("Que legal! Tupo é um nome bonito. Me conta mais sobre seu gato?",
                                "Meu gato se chama Tupo.")
        self.assertEqual(texto, "Que legal! Tupo é um nome bonito. Me conta mais sobre seu gato?")
        self.assertTrue(bot.historico[-1]["realizador"]["usada"])

    def test_nome_trocado_volta_ao_texto_de_sempre(self):
        bot, texto = self.falar("Que legal! Tupe é um nome bonito.", "Meu gato se chama Tupo.")
        self.assertIn("Tupo", texto)
        self.assertNotIn("Tupe", texto)
        self.assertIn("reprovado", bot.historico[-1]["realizador"]["motivo"])

    def test_relacao_trocada_volta_ao_texto_de_sempre(self):
        bot, texto = self.falar("Anotado: seu irmão se chama Tupo. Gostei do nome!", "Meu gato se chama Tupo.")
        self.assertNotIn("irmão", texto)
        self.assertIn("relacao_certa", bot.historico[-1]["realizador"]["motivo"])
        bot, texto = self.falar("Tupo. Que nome diferente. Como é seu nome?", "Meu gato se chama Tupo.")
        self.assertNotIn("seu nome", texto)

    def test_fato_alterado_volta_ao_texto_de_sempre(self):
        bot, texto = self.falar("Claro! A Lua é o satélite artificial da Terra.", "O que é a Lua?")
        self.assertIn("satélite natural", texto)
        self.assertFalse(bot.historico[-1]["realizador"]["usada"])

    def test_sem_fim_volta_ao_texto_de_sempre(self):
        bot = Crivo()
        bot.realizador = Falso("Sinto muito que você esteja se sentindo assim.", terminou=False)
        _, texto = bot.responder("Estou triste hoje.")
        self.assertFalse(bot.historico[-1]["realizador"]["usada"])

    def test_revisao_ainda_confere(self):
        bot, _ = self.falar("Sinto muito por isso. Respira com calma; se quiser desabafar, eu escuto.",
                            "Estou triste hoje.")
        self.assertTrue(bot.historico[-1]["realizador"]["usada"])
        self.assertIsNotNone(bot.estado_interno.revisao)


if __name__ == "__main__":
    unittest.main()
