"""Contratos de diálogo real, isolamento, argumentos e replay HTTP."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from avaliar_bate_papo import avaliar
from crivo import Crivo
from dialogo_neural import DialogoNeural
from raciocinio_dialogo import RaciocinioDialogo
from web_core import responder_web


RAIZ = Path(__file__).resolve().parent


class TestesBatePapo(unittest.TestCase):
    def test_dialogos_completos_com_criterios_independentes_do_treino(self):
        resultado = avaliar(Crivo)
        for c in resultado["casos"]:
            with self.subTest(dialogo=c["nome"]):
                self.assertTrue(c["passou"], [t for t in c["turnos"] if not t["passou"]])

    def test_api_reconstroi_nome_preferencia_e_plano_sem_vazar_sessao(self):
        for historico, pergunta, esperado, trechos in (
            (["Meu nome é Joana"], "Como eu me chamo?", "conversa:memoria", ["Joana"]),
            (["Eu gosto de cerâmica"], "O que eu gosto de fazer?", "conversa:memoria", ["cerâmica"]),
            (["Quero montar uma horta", "Só tenho 30 minutos por dia"], "Como posso organizar isso?", "conversa:planejamento", ["horta", "30 minutos", "18 min"]),
        ):
            with self.subTest(pergunta=pergunta):
                dado = responder_web(dict(message=pergunta, history=historico))
                self.assertEqual(dado["id"], esperado)
                self.assertFalse(dado["has_proof"])
                for trecho in trechos:
                    self.assertIn(trecho, dado["response"])
                self.assertEqual(dado, responder_web(dict(message=pergunta, history=historico)))
        isolado = responder_web(dict(message="Como eu me chamo?"))
        self.assertNotIn("Joana", isolado["response"])
        self.assertIn("ainda não me disse", Crivo().responder("Qual é meu nome?")[1])

    def test_trocar_tema_nao_aplica_objetivo_anterior_ao_novo(self):
        bot = Crivo()
        bot.responder("Quero conversar sobre meu curso")
        bot.responder("Quero aprender a fotografar")
        bot.responder("Só tenho 40 minutos por dia")
        bot.responder("Quero conversar sobre minha viagem")
        _, resposta = bot.responder("Me ajuda a montar um plano")
        self.assertNotIn("fotografar", resposta)
        self.assertNotIn("40 minutos", resposta)
        bot.responder("Vamos voltar ao meu curso")
        _, resposta = bot.responder("Me ajuda a montar um plano")
        self.assertIn("fotografar", resposta)
        self.assertIn("40 minutos", resposta)

    def test_negacao_do_objetivo_nao_mantem_objetivo_antigo(self):
        bot = Crivo()
        bot.responder("Quero aprender a fotografar")
        bot.responder("Não quero mais aprender a fotografar")
        _, resposta = bot.responder("Qual é meu objetivo?")
        self.assertNotIn("Seu objetivo declarado", resposta)
        self.assertNotIn("Seu objetivo declarado", bot.responder("Me ajuda a montar um plano")[1])

    def test_declara_nome_nao_faz_busca_factual_ou_normaliza_nome(self):
        for nome in ("João Silva", "Névia", "Ana-Clara", "Maíra"):
            with self.subTest(nome=nome):
                bot = Crivo()
                bot.responder("Meu nome é " + nome)
                ident, resposta = bot.responder("Como eu me chamo?")
                self.assertEqual(ident, "conversa:memoria")
                self.assertIn(nome, resposta)
        bot = Crivo()
        bot.responder("Meu nome é uma frase com palavras demais para um nome")
        self.assertNotIn("nome", bot.conversacao.dialogo.dados)

    def test_relato_nao_altera_bases_pesos_ou_prova(self):
        arquivos = ("conhecimento.json", "conhecimento_expandido.json", "conhecimento_mundo.json", "relacoes.json", "rede_crivo.json", "rede_linguagem.json", "rede_dialogo.json")
        antes = {p: hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in arquivos}
        bot = Crivo()
        bot.responder("Meu nome é Joana")
        bot.responder("Eu acho que todo gato voa")
        self.assertNotEqual(bot.responder("Um gato voa?")[0], "conversa:hipotese")
        self.assertEqual(antes, {p: hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in arquivos})

    def test_fatos_codigo_fontes_e_modificadores_preservam_motor(self):
        for pergunta in ("O que é DNA?", "Como usar input em Python?", "A Lua orbita a Terra?",
                         "O que é DNA alienígena?", "Não explique memória",
                         "Não faço ideia do que é DNA", "Eu não quero que você explique sinapse",
                         'print("Meu nome é Joana")'):
            with self.subTest(pergunta=pergunta):
                bot = Crivo()
                bot.responder("Meu nome é Joana")
                bot.responder("Quero montar uma horta")
                ident, _ = bot.responder(pergunta)
                self.assertFalse(ident.startswith("conversa:"), ident)
        bot = Crivo()
        bot.responder("Quero conversar sobre meu curso")
        ident, resposta = bot.responder("Não faço ideia do que é DNA")
        self.assertEqual(ident, "conhecimento:dna")
        self.assertIn("genética", resposta)
        self.assertEqual(bot.responder("Eu não pedi uma explicação sobre DNA")[0], "linguagem:negado")
        dado = responder_web(dict(history=["O que é DNA?", "E o RNA, faz a mesma coisa?"], message="Qual é a fonte?"))
        self.assertEqual(dado["id"], "escrita:fontes")
        self.assertIn("genome.gov", dado["response"])

    def test_comparacao_eliptica_esclarece_do_que_fala(self):
        self.assertEqual(Crivo().responder("E o RNA, faz a mesma coisa?")[0], "duvida")
        bot = Crivo()
        bot.responder("O que são DNA e RNA?")
        self.assertEqual(bot.responder("E a memória, faz a mesma coisa?")[0], "duvida")
        ident, texto = bot.responder("1")
        self.assertNotEqual(ident, "conversa:relato")
        self.assertEqual(bot.historico[-1]["ato"]["consulta"], "qual é a diferença entre DNA e memória")

    def test_consultas_sem_interrogacao_e_sem_entrada_exata_durante_relato(self):
        perguntas = {"planta precisa de sol": "sol_sombra", "como organizar a geladeira": "geladeira",
                     "por que as aves voam": "aves", "horta em vaso": "horta"}
        base = json.loads((RAIZ / "conhecimento.json").read_text(encoding="utf-8"))
        for entrada in base:
            entrada["perguntas"] = [p for p in entrada["perguntas"] if p not in perguntas]
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "base.json"
            caminho.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
            for pergunta, esperado in perguntas.items():
                with self.subTest(pergunta=pergunta):
                    bot = Crivo(caminho)
                    bot.responder("Quero conversar sobre meus planos")
                    bot.responder("Meu nome é Joana")
                    self.assertEqual(bot.responder(pergunta)[0], esperado)
                    self.assertIn("Joana", bot.responder("Qual é meu nome?")[1])

    def test_memoria_e_historico_sao_limitados(self):
        bot = Crivo()
        for i in range(30):
            bot.responder("Meu nome é Pessoa " + str(i))
        self.assertLessEqual(len(bot.conversacao.dialogo.dados), 12)
        self.assertLessEqual(len(bot.conversacao.relatos), 8)
        self.assertLessEqual(len(bot.historico), 20)
        bot.responder("Esqueça essa conversa")
        self.assertFalse(bot.conversacao.dialogo.dados)
        self.assertFalse(bot.conversacao.raciocinio_dialogo.regras)

    def test_premissas_dao_encadeamento_sem_inverter_ou_contaminar_base(self):
        bot = Crivo()
        ident, texto = bot.responder("Se todo Mivor é um Nexo e todo Nexo é roxo, um Mivor é roxo?")
        self.assertEqual(ident, "conversa:hipotese")
        self.assertIn("Mivor → Nexo → roxo", texto)
        self.assertIn("não um fato novo", texto)
        self.assertIn("Não consigo concluir", bot.responder("Então um Nexo é um Mivor?")[1])
        self.assertNotEqual(bot.responder("O que é Mivor?")[0], "conversa:hipotese")
        outro = Crivo()
        self.assertNotEqual(outro.responder("Então um Mivor é roxo?")[0], "conversa:hipotese")

    def test_premissas_negativas_contradicao_e_ciclo(self):
        motor = RaciocinioDialogo()
        r = motor.preparar("Se todo Mivor é um Nexo e todo Nexo não é roxo, um Mivor é roxo?", 1)
        self.assertTrue(r[1].startswith("Não"))
        self.assertIn("última relação é negativa", r[1])
        r = motor.preparar("Se todo Mivor é um Nexo e todo Mivor não é Nexo, um Mivor é Nexo?", 2)
        self.assertIn("conflito", r[1])
        r = motor.preparar("Se todo Mivor é um Nexo e todo Nexo é um Mivor, um Mivor é um Nexo?", 3)
        self.assertTrue(r[1].startswith("Sim"))
        self.assertIsNone(motor.preparar("Se todo Mivor geralmente é um Nexo, um Mivor é um Nexo?", 4))

    def test_contas_preservam_decimal_unidade_e_qualificadores(self):
        motor = RaciocinioDialogo()
        for frase, total in (("Comprei duas canetas por 2,50 reais cada. Quanto gastei?", "R$ 5,00"),
                             ("Comprei 7 peças por 12 reais cada", "R$ 84"),
                             ("Comprei um caderno por 20 reais cada", "R$ 20")):
            with self.subTest(frase=frase):
                self.assertIn(total, motor.preparar(frase, 1)[1])
                self.assertIn(total, motor.preparar("Quanto gastei?", 2)[1])
                self.assertIsNone(motor.preparar("Quanto gastei?", 4))
        for frase in ("Comprei três livros por 20 reais cada com desconto. Quanto gastei?",
                      "Comprei três livros por 20 reais cada e devolvi um. Quanto gastei?",
                      "Comprei três livros por 20 dólares cada. Quanto gastei?"):
            self.assertIsNone(motor.preparar(frase, 1))

    def test_curriculo_particoes_e_checkpoint_auditaveis(self):
        from rede_sequencial import assinatura
        dados = json.loads((RAIZ / "curriculo_dialogo.json").read_text(encoding="utf-8"))
        treino = [c for c in dados["exemplos"] if c["split"] == "treino"]
        validacao = [c for c in dados["exemplos"] if c["split"] == "validacao"]
        self.assertFalse({c["familia"] for c in treino} & {c["familia"] for c in validacao})
        self.assertFalse({c["texto"] for c in treino} & {c["texto"] for c in validacao})
        checkpoint = json.loads((RAIZ / "rede_dialogo.json").read_text(encoding="utf-8"))
        self.assertEqual(checkpoint["assinatura_treino"], assinatura(treino))
        modelo = DialogoNeural(checkpoint)
        self.assertEqual(modelo.analisar("Meu nome é Névia", "livre")["ato"], "relato")
        checkpoint["assinatura_atributos"] = "invalida"
        with self.assertRaises(ValueError):
            DialogoNeural(checkpoint)

    def test_inferencia_nao_depende_de_numpy(self):
        comando = "from crivo import Crivo; b=Crivo(); b.responder('Meu nome é Joana'); assert 'Joana' in b.responder('Como eu me chamo?')[1]"
        resultado = subprocess.run([sys.executable, "-S", "-c", comando], cwd=str(RAIZ), capture_output=True, text=True)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)


if __name__ == "__main__":
    unittest.main()
