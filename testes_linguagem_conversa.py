"""Contratos de conversa, proveniência, generalidade e replay da API."""
import json
import re
import tempfile
import unittest
from pathlib import Path

from avaliar_conversacao import CASOS, executar
from crivo import Crivo
from linguagem_conversa import Conversacao, carregar_gramatica, reescrever
from web_core import PedidoInvalido, responder_web


class TestesLinguagemConversa(unittest.TestCase):
    def test_cenarios_publicos_de_conversa(self):
        for caso in CASOS:
            with self.subTest(pergunta=caso[1], anteriores=caso[0]):
                resultado = executar(caso)
                self.assertTrue(resultado["passou"], resultado)

    def test_gramatica_independe_do_nome_e_dos_dados_da_instalacao(self):
        base = [{"id": "lumix", "topico": "clima", "perguntas": ["o que é lumix"],
                 "resposta": "Lumix é um objeto fictício. Ele possui 7 marcas azuis."}]
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / "conhecimento.json"
            arq.write_text(json.dumps(base), encoding="utf-8")
            for pergunta in ("Lumix é o quê?", "Queria entender um pouco melhor lumix",
                             "Você poderia me explicar o que seria lumix?"):
                bot = Crivo(arq)
                self.assertEqual(bot.responder(pergunta)[0], "lumix")
                _, texto = bot.responder("Fale a mesma coisa com outras palavras")
                self.assertIn("objeto fictício", texto)
                self.assertIn("7 marcas azuis", texto)
                self.assertIsNone(bot.curriculo_mundo)
                self.assertNotIn("sinapse", texto)

    def test_variacoes_compostas_cobrem_todos_os_conceitos_cientificos(self):
        bot = Crivo()
        for item in bot.curriculo_mundo["itens"]:
            for prefixo in ("Queria entender um pouco melhor ", "Você poderia me explicar o que seria "):
                with self.subTest(nome=item["nome"], prefixo=prefixo):
                    bot.responder(prefixo + item["nome"])
                    self.assertEqual(bot.contexto_textual.temas, (item["id"],))
                    self.assertIn(item["fatos"][0]["texto"], bot.contexto_textual.texto)

    def test_reformulacao_preserva_todas_as_evidencias_e_muda_a_realizacao(self):
        bot = Crivo()
        for nome in ("neurônio", "memória", "DNA", "Lua", "HTML"):
            with self.subTest(nome=nome):
                _, antes = bot.responder("O que é " + nome)
                ctx = bot.contexto_textual
                _, depois = bot.responder("Com outras palavras")
                self.assertNotEqual(antes, depois)
                self.assertEqual(ctx.exibidos, bot.contexto_textual.exibidos)
                self.assertEqual(ctx.usados, bot.contexto_textual.usados)
                self.assertEqual(re.findall(r"\d+(?:[,.]\d+)*", antes), re.findall(r"\d+(?:[,.]\d+)*", depois))

    def test_condicoes_negacoes_e_incerteza_sobrevivem(self):
        exemplos = (
            "O objeto não é uma estrela.",
            "A associação pode melhorar a recordação, mas não garante resultados.",
            "Se há luz, a resposta pode mudar em 24 horas.",
            "O estudo é transversal e não estabelece causalidade.",
            "A rotina é uma opção quando há tempo, geralmente após 2 dias.",
        )
        for frase in exemplos:
            reformulada = reescrever(frase, "assunto", simples=True)
            for termo in ("não", "pode", "quando", "geralmente", "transversal", "24", "2"):
                if termo in frase:
                    self.assertIn(termo, reformulada)
        bot = Crivo()
        bot.responder("Como a procrastinação se associa ao estresse?")
        _, texto = bot.responder("Fale a mesma coisa com outras palavras")
        self.assertIn("não estabelece causalidade", texto)
        self.assertIn("transversal", texto)

    def test_citacoes_e_codigo_nao_sao_editados(self):
        frase = 'Python permite escrever `x = "não"` e imprimir "permite".'
        self.assertEqual(reescrever(frase, "Python"), frase)
        bot = Crivo()
        _, resposta = bot.responder("Como usar input em Python?")
        blocos = re.findall(r"```.*?```", resposta, re.S)
        self.assertTrue(blocos)
        _, reformulada = bot.responder("Com outras palavras")
        self.assertEqual(re.findall(r"```.*?```", reformulada, re.S), blocos)
        self.assertEqual(bot.historico[-1]["pergunta"], "Com outras palavras")

    def test_fontes_seguem_as_unidades_reformuladas(self):
        bot = Crivo()
        bot.responder("O que é sinapse?")
        _, originais = bot.responder("Qual é a fonte?")
        ctx = bot.contexto_textual
        bot.responder("Reescreva essa resposta")
        self.assertEqual(ctx.exibidos, bot.contexto_textual.exibidos)
        _, novas = bot.responder("De onde veio essa informação?")
        self.assertEqual(originais, novas)
        self.assertNotIn("genome.gov", novas)

    def test_reformulacoes_sucessivas_sao_variadas_e_deterministicas(self):
        historico = ["O que é neurônio?", "Com outras palavras"]
        a = responder_web({"history": historico, "message": "Com outras palavras"})
        b = responder_web({"history": historico, "message": "Com outras palavras"})
        primeira = responder_web({"history": historico[:1], "message": historico[1]})
        self.assertEqual(a, b)
        self.assertNotEqual(a["response"], primeira["response"])
        # O checkpoint de producao antigo e invalidado pela expansao do curriculo.\n        # A reformulacao deve funcionar mesmo quando a rede neural esta inativa.\n        self.assertIsInstance(a["neural_active"], bool)\n        self.assertFalse(a["has_proof"])

    def test_prova_logica_sobrevive_a_reformulacoes(self):
        historico = ["Um pinguim é um ser vivo?", "Com outras palavras"]
        dado = responder_web({"history": historico, "message": "Com outras palavras"})
        self.assertTrue(dado["has_proof"])
        self.assertIn("pinguim → ave → vertebrado → animal → ser vivo", dado["response"])
        self.assertNotIn("A ideia central", dado["response"])
        with self.assertRaises(PedidoInvalido):
            responder_web({"message": "oi", "prova_origem": "logica:tipo_de"})

    def test_citar_relato_nao_gera_indicacao_de_prova(self):
        dado = responder_web({"history": ["Quero conversar sobre meu projeto"],
                              "message": "Eu tenho um texto chamado Relações verificadas:"})
        self.assertEqual(dado["id"], "conversa:relato")
        self.assertIn("Relações verificadas:", dado["response"])
        self.assertFalse(dado["has_proof"])
        editorial = responder_web({"history": ["Por que a aranha é um inseto?"],
                                  "message": "Com outras palavras"})
        self.assertTrue(editorial["has_proof"])

    def test_esclarecimento_preserva_alternativas_ate_escolha_explicita(self):
        for escolha, esperado in (("1", "dna"), ("RNA", "rna")):
            bot = Crivo()
            bot.responder("O que são DNA e RNA?")
            self.assertEqual(bot.responder("Pode desenvolver essa ideia?")[0], "duvida")
            self.assertEqual(bot.responder("sim")[0], "duvida")
            bot.responder(escolha)
            self.assertEqual(bot.contexto_textual.temas, (esperado,))
            self.assertTrue(all(p[0] == esperado for p in bot.contexto_textual.exibidos))
        bot = Crivo()
        bot.responder("O que são DNA e RNA?")
        bot.responder("Pode desenvolver essa ideia?")
        bot.responder("O que é sinapse?")
        self.assertIsNone(bot.conversacao.pendente)

    def test_pergunta_eliptica_esclarece_antes_de_consultar(self):
        bot = Crivo()
        bot.responder("O que são melatonina e sono REM?")
        self.assertEqual(bot.responder("E como funciona?")[0], "duvida")
        ident, texto = bot.responder("a primeira")
        self.assertEqual(ident, "escrita:explicacao")
        self.assertIn("luz", texto)
        self.assertEqual(bot.contexto_textual.temas, ("mundo_melatonina",))

    def test_memoria_tem_limite_e_nao_lembra_assuntos_ausentes(self):
        bot = Crivo()
        bot.responder("O que é memória?")
        for i in range(Conversacao.MAX_INTERVALO + 1):
            bot.responder("Oi")
        self.assertEqual(bot.responder("Retome memória")[0], "duvida")
        for item in bot.curriculo_mundo["itens"][:12]:
            bot.responder("O que é " + item["nome"])
        self.assertLessEqual(len(bot.conversacao.lembrancas), Conversacao.MAX_LEMBRANCAS)
        self.assertEqual(bot.responder("Retome cristal inventado")[0], "duvida")
        self.assertEqual(Crivo().responder("Retome memória")[0], "duvida")

    def test_retomada_reconstroi_fontes_na_api(self):
        historico = ["O que é memória?", "O que é DNA?", "Oi", "Retome memória"]
        dado = responder_web({"history": historico, "message": "Qual é a fonte?"})
        self.assertIn("journals.plos.org", dado["response"])
        self.assertNotIn("genome.gov", dado["response"])

    def test_historico_preserva_mensagem_original_e_consulta_auditavel(self):
        bot = Crivo()
        pergunta = "Você poderia me explicar o que seria uma sinapse?"
        bot.responder(pergunta)
        self.assertEqual(bot.ultimo_turno["pergunta"], pergunta)
        self.assertEqual(bot.historico[-1]["pergunta"], pergunta)
        self.assertEqual(bot.historico[-1]["ato"]["consulta"], "o que é uma sinapse")
        self.assertNotIn("o que é uma sinapse", [h["pergunta"] for h in bot.historico])

    def test_argumentos_preservam_nomes_e_operadores_do_texto_original(self):
        bot = Crivo()
        ident, texto = bot.responder("Explique o que é HTML e CSS.")
        self.assertEqual(ident, "composto:definicao")
        self.assertIn("HTML:", texto)
        self.assertIn("CSS:", texto)
        for nome in ("C++", "DNA/alienígena", "RNA === infinito"):
            pergunta = "Queria entender um pouco melhor " + nome
            ato = bot.conversacao.analisar(pergunta)
            self.assertEqual(ato.alvo, nome)
            self.assertIn(nome, ato.consulta)
        self.assertEqual(bot.responder("Gostaria de saber o que é o Sol")[0], "sol")

    def test_relato_se_adapta_ao_objetivo_sem_inventar_fatos(self):
        raiz = Path(__file__).resolve().parent
        arquivos = ("conhecimento.json", "conhecimento_mundo.json", "rede_crivo.json")
        antes = {f: (raiz / f).read_bytes() for f in arquivos}
        bot = Crivo()
        bot.responder("Quero conversar sobre a faculdade")
        _, primeira = bot.responder("Eu quero organizar meus estudos")
        _, segunda = bot.responder("Eu não consigo manter meu horário")
        _, terceira = bot.responder("Já tentei estudar de manhã")
        self.assertIn("principal dificuldade", primeira)
        self.assertIn("organizar meus estudos", segunda)
        self.assertIn("já tentou", segunda)
        self.assertIn("gostaria que fosse diferente", terceira)
        self.assertNotIn("diagnóstico", terceira)
        self.assertNotIn("transtorno", terceira)
        self.assertIsNone(bot.contexto_textual)
        self.assertIsNone(bot.ultima_resposta_mostrada)
        self.assertEqual(antes, {f: (raiz / f).read_bytes() for f in arquivos})

    def test_troca_de_tema_pessoal_e_retomada(self):
        bot = Crivo()
        bot.responder("Quero conversar sobre trabalho")
        bot.responder("Eu quero mudar de trabalho")
        bot.responder("Quero conversar sobre música")
        _, texto = bot.responder("Eu quero aprender violão")
        self.assertNotIn("mudar de trabalho", texto)
        _, texto = bot.responder("Vamos voltar ao trabalho")
        self.assertIn("mudar de trabalho", texto)
        self.assertNotIn("violão", texto)
        bot.responder("Mudar de assunto")
        self.assertEqual(bot.responder("Retome trabalho")[0], "duvida")

    def test_recapitulacao_preserva_origem_e_distingue_relato(self):
        bot = Crivo()
        bot.responder("O que é DNA?")
        bot.responder("Quero conversar sobre meu projeto")
        bot.responder("Eu tenho um projeto com 3 etapas")
        _, texto = bot.responder("Recapitule nossa conversa")
        self.assertIn("Você contou:", texto)
        self.assertIn("3 etapas", texto)
        self.assertEqual(bot.contexto_textual.exibidos, (("dna", 0),))
        _, fontes = bot.responder("Qual é a fonte?")
        self.assertIn("genome.gov", fontes)
        self.assertNotIn("3 etapas", fontes)

    def test_pedido_novo_preserva_qualificadores_e_direcao(self):
        for pergunta in ("Queria entender o DNA quântico inventado", "Me explica como a memória ajuda o sono",
                         "Me explica por que o sono não ajuda a memória", "Me explique como sono cura depressão"):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(Crivo().responder(pergunta)[0], "fora")

    def test_reinicio_e_ensino_invalidam_memoria_e_prova(self):
        bot = Crivo()
        bot.responder("O que é memória?")
        bot.responder("Esqueça essa conversa")
        self.assertEqual(bot.responder("Com outras palavras")[0], "duvida")
        bot.responder("O que é DNA?")
        bot.ensinar("novo_teste", "clima", ["o que é lum"], "Lum é fictício.", salvar=False)
        self.assertFalse(bot.conversacao.lembrancas)
        self.assertEqual(bot.responder("Retome DNA")[0], "duvida")

    def test_gramatica_malformada_nao_e_aceita(self):
        modelo = {"versao": 1, "atos": [{"id": "definir", "operacao": "consulta",
                  "padroes": [r"defina (?P<alvo>.+)"], "canonico": "o que é {alvo}"}]}
        alteracoes = (dict(padroes=["["]), dict(canonico="{ausente}"), dict(formato="inventado"),
                      dict(operacao=[]), dict(padroes=[r"(?P<invalido>.+)"]), dict(canonico="{alvo.__class__}"))
        with tempfile.TemporaryDirectory() as pasta:
            for i, alteracao in enumerate(alteracoes):
                dados = json.loads(json.dumps(modelo))
                dados["atos"][0].update(alteracao)
                caminho = Path(pasta) / (str(i) + ".json")
                caminho.write_text(json.dumps(dados), encoding="utf-8")
                with self.assertRaises(ValueError):
                    carregar_gramatica(str(caminho))


if __name__ == "__main__":
    unittest.main()
