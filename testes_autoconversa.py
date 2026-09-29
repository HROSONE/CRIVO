"""Autoconversa, catálogo ativo e separação entre pedidos e perguntas pessoais."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo
from web_core import responder_web


class TestesAutoconversa(unittest.TestCase):
    def test_pacote_vercel_com_configuracao_compacta(self):
        raiz = Path(__file__).resolve().parent
        config = json.loads((raiz / "vercel.json").read_text())
        padrao = config["functions"]["api/chat.py"]["includeFiles"]
        self.assertLessEqual(len(padrao), 256)
        # Simula os arquivos do pacote sem usar os módulos instalados na
        # pasta original. Importar a API e responder prova a cobertura real.
        padroes = padrao[1:-1].split(",") if padrao.startswith("{") else [padrao]
        arquivos = {p for exp in padroes for p in raiz.glob(exp) if p.is_file()}
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta)
            for p in arquivos:
                shutil.copyfile(p, destino / p.name)
            (destino / "api").mkdir()
            shutil.copyfile(raiz / "api" / "chat.py", destino / "api" / "chat.py")
            script = (
                "import sys,json;sys.path.insert(0,sys.argv[1]);"
                "from api.chat import handler;from web_core import responder_web;"
                "qs=['Você pensa?','O que é Andrômeda?','A Lua orbita a Terra?'];"
                "print(json.dumps([responder_web({'message':q})['id'] for q in qs]))"
            )
            r = subprocess.run([sys.executable, "-I", "-c", script, pasta],
                               cwd=pasta, capture_output=True, text=True, timeout=10)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout), ["social:pensamento", "conhecimento:andromeda", "logica:orbita"])

    def test_sequencia_das_capturas(self):
        bot = Crivo()
        for q, ident in (
            ("oi", "social:oi"),
            ("o que você sabe fazer?", "social:assuntos"),
            ("só isso?", "social:assuntos"),
            ("o que é programação?", "prog_programar"),
            ("qual é seu nome?", "social:quem"),
            ("você pensa?", "social:pensamento"),
        ):
            with self.subTest(q=q):
                obtido, texto = bot.responder(q)
                self.assertEqual(obtido, ident)
                self.assertNotIn("lâmpada LED", texto)
        self.assertIn("processo", texto)
        self.assertIn("consciência", texto)

    def test_variacoes_sobre_processamento_e_experiencia(self):
        for q in ("O que você sente?", "Como você pensa?", "Como você funciona?"):
            self.assertEqual(Crivo().responder(q)[0], "social:pensamento")
        for sujeito in ("Você", "vc", "tu"):
            for predicado in ("pensa", "raciocina", "sente", "tem emoções",
                              "tem consciência", "é uma pessoa", "é consciente",
                              "consegue pensar", "pode raciocinar"):
                with self.subTest(sujeito=sujeito, predicado=predicado):
                    ident, texto = Crivo().responder(sujeito + " " + predicado + "?")
                    self.assertEqual(ident, "social:pensamento")
                    self.assertIn("consciência", texto)
                    self.assertNotIn("lâmpada", texto)

    def test_catalogo_mostra_funcoes_e_conhecimento_ampliado(self):
        for q in ("O que você sabe fazer?", "Quais são suas capacidades?",
                  "Como você pode me ajudar?", "O que vc consegue fazer?",
                  "Sobre o que você sabe falar?", "assuntos", "ajuda"):
            with self.subTest(q=q):
                ident, texto = Crivo().responder(q)
                self.assertEqual(ident, "social:assuntos")
                for palavra in ("textos", "resumos", "relações", "astronomia", "biologia", "fontes"):
                    self.assertIn(palavra, texto)

    def test_catalogo_personalizado_nao_anuncia_dados_ausentes(self):
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / "conhecimento.json"
            arq.write_text(json.dumps([{
                "id": "lum", "topico": "mundos fictícios", "perguntas": ["o que é lum"],
                "resposta": "Lum é um objeto de teste.",
            }]), encoding="utf-8")
            bot = Crivo(arq)
            _, texto = bot.responder("O que você sabe fazer?")
            self.assertIn("mundos fictícios", texto)
            for ausente in ("Andrômeda", "DNA", "Python", "grafo", "frutas", "fontes"):
                self.assertNotIn(ausente, texto)
            _, texto = bot.responder("Você raciocina?")
            self.assertNotIn("verifico relações", texto)

    def test_continuacao_da_autoconversa_e_expiracao(self):
        bot = Crivo()
        _, curto = bot.responder("O que você sabe fazer?")
        _, completo = bot.responder("Só isso?")
        self.assertGreater(len(completo), len(curto))
        self.assertIn("DNA", completo)
        bot.responder("O que é a Lua?")
        self.assertEqual(bot.responder("Só isso?")[0], "duvida")
        bot.responder("Você pensa?")
        self.assertEqual(bot.responder("Como assim?")[0], "social:pensamento")
        bot.responder("Oi")
        self.assertEqual(bot.responder("Como assim?")[0], "duvida")

    def test_perguntas_pessoais_desconhecidas_nao_recebem_fatos(self):
        for q in ("Você dorme?", "Vc sonha?", "Tu viaja?", "Você gosta de lâmpadas?",
                  "Você pensa nas estrelas?", "Como você dorme?",
                  "O que você pensa sobre lâmpadas?"):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], "social:nao_entendido")

    def test_pedidos_informativos_preservam_o_assunto(self):
        for q, esperado in (
            ("Você pode explicar o que é DNA?", "conhecimento:dna"),
            ("Você sabe o que é RNA?", "conhecimento:rna"),
            ("Você acha que a Terra é um planeta?", "logica:tipo_de"),
            ("Você pensa que o Sol é uma estrela?", "sol"),
            ("Você pode dizer se o golfinho é considerado mamífero?", "logica:tipo_de"),
            ("Você poderia escrever um texto sobre DNA?", "escrita:texto"),
            ("Qual a economia da lâmpada LED?", "lampada"),
            ("Você falou da Lua?", "contexto:sem_referencia"),
        ):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], esperado)

    def test_tema_de_terceiros_nao_e_autoconversa(self):
        for q in ("Os seres humanos pensam?", "Uma estrela sente?", "O Sol é consciente?"):
            self.assertNotEqual(Crivo().responder(q)[0], "social:pensamento")

    def test_api_reconstroi_autoconversa_e_isola_contexto(self):
        dado = responder_web({"message": "Só isso?", "history": ["O que você sabe fazer?"]})
        self.assertEqual(dado["id"], "social:assuntos")
        self.assertIn("DNA", dado["response"])
        self.assertFalse(dado["has_proof"])
        self.assertEqual(responder_web({"message": "Só isso?"})["id"], "duvida")
        dado = responder_web({"message": "Você pensa?", "history": ["O que é programação?"]})
        self.assertEqual(dado["id"], "social:pensamento")
        self.assertEqual(dado["mechanism"], "conversa_assistente")
        self.assertFalse(dado["has_proof"])
