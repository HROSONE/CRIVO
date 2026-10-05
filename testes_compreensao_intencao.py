"""Intenção e contexto: as falhas observadas no site e formulações inéditas.

Cada caso vem de uma consulta real ao site publicado (05/10/2026) ou de uma
formulação nova escrita depois, para medir generalização e não só memorização.
Os controles negativos garantem que a camada nova não captura o que não é dela.
"""
import unittest

from compreensao_intencao import EstadoConversa, Inferencia, calcular, reformular_finalidade
from pedidos_gerativos import criacao
from web_core import responder_web


def conversar(*mensagens, memoria=None):
    pedido = {"message": mensagens[-1], "history": list(mensagens[:-1])}
    if memoria is not None:
        pedido["memory"] = memoria
    return responder_web(pedido)


class FalhasDoSite(unittest.TestCase):
    """As consultas que falharam no site agora usam intenção e contexto."""

    def test_mesma_intencao_em_outra_formulacao(self):
        r = conversar("Pra que a célula precisa da mitocôndria?")
        self.assertIn("ATP", r["response"])
        self.assertEqual(r["id"], conversar("Para que serve a mitocôndria?")["id"])

    def test_tarefa_do_dia_nao_vira_previsao_do_tempo(self):
        r = conversar("Hoje eu quero terminar o relatório de vendas.", "O que eu quero fazer hoje?")
        self.assertEqual(r["id"], "contexto:objetivo")
        self.assertIn("terminar o relatório de vendas", r["response"])
        self.assertNotIn("meteorologia", r["response"])

    def test_sem_tarefa_informada_admite_em_vez_de_chutar(self):
        r = conversar("O que eu quero fazer hoje?")
        self.assertEqual(r["id"], "contexto:objetivo_desconhecido")
        self.assertNotIn("meteorologia", r["response"])

    def test_relato_com_nao_nao_e_negacao_logica(self):
        r = conversar("Estou cansado e sinto que não avanço")
        self.assertFalse(r["id"].startswith(("logica:", "inferencia:", "contexto:restricao")))
        self.assertNotIn("negação", r["response"].lower())

    def test_preferencia_de_explicacao_e_lembrada(self):
        r = conversar("Prefiro explicações curtas com exemplos.", "Como eu prefiro as explicações?")
        self.assertEqual(r["id"], "contexto:preferencia")
        self.assertIn("curtas com exemplos", r["response"])

    def test_pergunta_pratica_usa_ficha_de_typescript(self):
        r = conversar("Uma interface do TypeScript valida um JSON em tempo de execução?")
        self.assertEqual(r["id"], "pratica:ts_apagamento")
        self.assertTrue(r["response"].startswith("Não."))
        self.assertEqual(r["mechanism"], "consulta_pratica")
        self.assertIn("Fontes:", r["response"])

    def test_subtracao_com_sinal_unicode(self):
        for texto in ("Quanto é 30000 − 15000?", "Quanto é 30000 - 15000?", "quanto e 30.000 - 15.000"):
            r = conversar(texto)
            self.assertEqual(r["id"], "calculo:aritmetica", texto)
            self.assertTrue(r["response"].endswith("= 15.000"), r["response"])

    def test_consequencia_com_premissas_em_linguagem_comum(self):
        r = conversar("Se chove, a rua fica molhada. Está chovendo. O que acontece com a rua?")
        self.assertEqual(r["id"], "inferencia:conclusao")
        self.assertIn("a rua fica molhada", r["response"])
        self.assertIn("premissas", r["response"])

    def test_investigador_de_memoria_conduz_a_conversa(self):
        conversa = ["Meu servidor Node está consumindo cada vez mais memória, o que pode ser?",
                    "Estou olhando o heap", "continua crescendo depois do GC",
                    "não, o cache fica estável", "sim, a fila de pedidos cresce"]
        ids = [conversar(*conversa[:i + 1])["id"] for i in range(len(conversa))]
        self.assertEqual(ids[:-1], ["investigacao:pergunta"] * 4)
        final = conversar(*conversa)
        self.assertEqual(final["id"], "investigacao:conclusao")
        self.assertIn("Pedidos pendentes", final["response"].split("Descartadas")[0])
        self.assertIn("Cache sem limite", final["response"].split("Descartadas")[1])
        self.assertIn("nodejs.org", final["response"])

    def test_instrucao_da_historia_nao_vira_nome(self):
        pedido = criacao("Escreva uma história curta sobre um farol abandonado, com uma personagem chamada Lia.")
        self.assertEqual(pedido["slots"], {"tema1": "Lia", "tema2": "um farol abandonado"})
        r = conversar("Escreva uma história curta sobre um farol abandonado, com uma personagem chamada Lia.")
        self.assertIn("Lia", r["response"])
        self.assertNotIn("personagem chamada", r["response"])


class FormulacoesIneditas(unittest.TestCase):
    """Frases escritas depois da implementação, para conferir generalização."""

    def test_finalidade_em_varias_formas(self):
        for texto, termo in (("Por que o DNA é tão importante?", "genétic"),
                             ("Pra que a planta precisa da clorofila?", "energia"),
                             ("Qual a utilidade dos ribossomos?", "proteína"),
                             ("O que a mitocôndria faz na célula?", "ATP")):
            self.assertIn(termo, conversar(texto)["response"], texto)

    def test_objetivos_preferencias_e_restricoes(self):
        casos = ((("Meu objetivo hoje é estudar para a prova de química.", "Qual é a minha meta de hoje?"),
                  "prova de química"),
                 (("Estou trabalhando num aplicativo de receitas.", "Em que eu estou trabalhando?"),
                  "aplicativo de receitas"),
                 (("Amanhã preciso entregar a apresentação do projeto.", "Você lembra o que eu preciso fazer?"),
                  "apresentação"),
                 (("Prefiro respostas diretas, sem rodeios.", "Qual é a minha preferência?"), "diretas"),
                 (("Evite termos técnicos.", "O que eu pedi para você evitar?"), "termos técnicos"))
        for mensagens, termo in casos:
            self.assertIn(termo, conversar(*mensagens)["response"], mensagens)

    def test_contas_em_portugues(self):
        for texto, esperado in (("Quanto dá 1250 + 750?", "2.000"), ("Calcule 12 vezes 12", "144"),
                                ("quanto é 100 dividido por 8?", "12,5"), ("Quanto é 15% de 200?", "30"),
                                ("quanto é dois mais dois", "4"), ("quanto é a raiz quadrada de 81", "9")):
            self.assertTrue(conversar(texto)["response"].endswith("= " + esperado), texto)

    def test_inferencias_validas_e_falacias(self):
        self.assertIn("derrama", conversar(
            "Se o leite ferve, ele derrama. O leite ferveu. O que acontece com o leite?")["response"])
        tollens = conversar("Se eu treino, fico mais forte. Eu não fiquei mais forte. Eu treinei?")
        self.assertEqual(tollens["id"], "inferencia:nao")
        self.assertIn("modus tollens", tollens["response"])
        consequente = conversar("Se a luz acende, a sala fica clara. A sala está clara. A luz acendeu?")
        self.assertEqual(consequente["id"], "inferencia:indeterminado")
        self.assertIn("afirmar o consequente", consequente["response"])
        antecedente = conversar("Se chove, a rua fica molhada. Não está chovendo. A rua está molhada?")
        self.assertIn("negar o antecedente", antecedente["response"])

    def test_premissas_espalhadas_em_turnos(self):
        r = conversar("Se a bateria acaba, o celular desliga.", "A bateria acabou.", "O celular desliga?")
        self.assertEqual(r["id"], "inferencia:sim")

    def test_outra_forma_de_relatar_memoria_crescendo(self):
        r = conversar("Minha API em Node usa cada vez mais memória com o tempo")
        self.assertEqual(r["id"], "investigacao:pergunta")
        self.assertIn("heap", r["response"])

    def test_outra_pergunta_pratica_de_typescript(self):
        r = conversar("O tipo do TypeScript garante que o JSON da API está certo em tempo de execução?")
        self.assertEqual(r["id"], "pratica:ts_apagamento")

    def test_personagem_e_cenario_em_outra_ordem(self):
        self.assertEqual(criacao("Crie um conto sobre uma menina chamada Ana e um dragão")["slots"],
                         {"tema1": "Ana", "tema2": "um dragão"})
        self.assertEqual(criacao("Invente uma história sobre um robô chamado Zeca que aprende a cozinhar")["slots"],
                         {"tema1": "Zeca"})
        self.assertEqual(criacao("Escreva uma história sobre um gato e uma lua")["slots"],
                         {"tema1": "um gato", "tema2": "uma lua"})


class ControlesNegativos(unittest.TestCase):
    """A camada nova não pode capturar falas que não são dela."""

    def test_quanto_sem_conta_nao_e_calculo(self):
        for texto in ("Quanto é a distância da Terra até a Lua?", "Quanto custa 3 maçãs?", "1999"):
            self.assertIsNone(calcular(texto), texto)

    def test_nao_sei_nao_e_restricao(self):
        self.assertIsNone(EstadoConversa().interpretar("Não sei o que fazer da vida"))
        self.assertFalse(conversar("Não sei o que fazer da vida")["id"].startswith("contexto:"))

    def test_pedido_ao_assistente_nao_e_objetivo(self):
        self.assertIsNone(EstadoConversa().interpretar("Quero saber o que é DNA"))
        self.assertIn("DNA", conversar("Quero saber o que é DNA")["response"])

    def test_memoria_humana_nao_abre_investigacao_de_heap(self):
        self.assertFalse(conversar("Minha memória anda ruim, esqueço tudo")["id"].startswith("investigacao:"))

    def test_premissas_explicitas_continuam_no_raciocinio_ativo(self):
        r = conversar("Considere estas premissas: chove; se chove, então a rua molha",
                      "O que falta para concluir que a rua molha?")
        self.assertEqual(r["mechanism"], "raciocinio_ativo")

    def test_quantificadores_ficam_com_o_grafo(self):
        self.assertIsNone(Inferencia().responder("Se todo gato é mamífero, e Tom é gato, Tom é mamífero?"))

    def test_relato_com_condicao_nao_vira_conclusao_logica(self):
        for texto in ("Quando chove, fico triste. Hoje choveu.",
                      "Quando eu era criança, morava no interior. Hoje moro na cidade.",
                      "Se eu perder o emprego, vou ficar arrasado. Perdi o emprego."):
            self.assertIsNone(Inferencia().responder(texto), texto)
            self.assertFalse(conversar(texto)["id"].startswith("inferencia:"), texto)

    def test_finalidade_sem_ficha_nao_inventa_assunto(self):
        self.assertIsNone(reformular_finalidade("Pra que serve o zorblax?", lambda alvo: False))

    def test_conta_absurda_nao_trava(self):
        self.assertIsNone(calcular("quanto é 9 ** 9 ** 9"))
        self.assertEqual(calcular("Quanto é 1/0?")[0], "calculo:indefinido")


class MemoriaEntreConversas(unittest.TestCase):
    def test_objetivos_e_preferencias_vao_para_a_memoria_opcional(self):
        r = conversar("Hoje quero revisar o contrato.", memoria={})
        self.assertEqual(r["memory"]["objetivos"], ["revisar o contrato"])
        depois = conversar("O que eu quero fazer hoje?", memoria=r["memory"])
        self.assertIn("revisar o contrato", depois["response"])

    def test_memoria_antiga_sem_campos_novos_continua_valida(self):
        r = conversar("Oi", memoria={"nome": "Ana"})
        self.assertNotIn("objetivos", r["memory"])

    def test_preferencia_curta_encurta_resposta_longa(self):
        estado = EstadoConversa()
        estado.observar("Prefiro explicações curtas.")
        longa = ("Primeira frase explica. Segunda frase completa. Terceira frase detalha muito mais. "
                 "Quarta frase continua detalhando sem parar, com mais e mais informação desnecessária. "
                 "Quinta frase acrescenta ainda outro detalhe que poucas pessoas pediram.\n"
                 "Fontes: https://exemplo.org")
        curta = estado.aplicar("conhecimento:x", longa)
        self.assertTrue(curta.startswith("Primeira frase explica. Segunda frase completa."))
        self.assertIn("Fontes: https://exemplo.org", curta)
        self.assertNotIn("Terceira", curta)
        self.assertEqual(estado.aplicar("social:oi", longa), longa)


if __name__ == "__main__":
    unittest.main()
