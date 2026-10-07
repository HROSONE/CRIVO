"""Pragmática conservadora: falas dirigidas, escopo curto e prioridades."""
import unittest

from conversa_assistente import identificar_contato, preparar_conversa, frustracao_recente
from crivo import Crivo
from web_core import responder_web


class TestesContatoContextual(unittest.TestCase):
    def test_contrato_dev_via_api(self):
        from scripts.avaliar_contato_contextual import avaliar
        r = avaliar()
        self.assertEqual(r['corretos'], r['casos'], [d for d in r['detalhes'] if not d['correto']])

    def test_vocativos_e_acentos(self):
        for saudacao in ('Eae', 'Eaê', 'E aí', 'Salve', 'Olá', 'Boa tarde'):
            for vocativo in ('véi', 'velho', 'parceira', 'minha amiga'):
                with self.subTest(saudacao=saudacao, vocativo=vocativo):
                    self.assertEqual(identificar_contato(saudacao + ', ' + vocativo + '!'), 'saudacao')
        self.assertEqual(Crivo().responder('Olá, véi!')[0], 'social:oi')

    def test_abertura_preserva_conteudo_e_simbolos(self):
        for conteudo in ('O que é C++?', 'Explique C#', 'Como usar !== em JavaScript?',
                         'O que é DNA e RNA?', 'Como não perder os dados?'):
            for abertura in ('Oi, velho!', 'Eae parceira', 'Salve, minha amiga;'):
                with self.subTest(conteudo=conteudo, abertura=abertura):
                    self.assertEqual(preparar_conversa(abertura + ' ' + conteudo), conteudo)
        self.assertEqual(Crivo().responder('Olá, velho! O que é HTML e CSS?')[0], 'composto:definicao')

    def test_criticas_completas_e_dirigidas(self):
        for q in ('Idiota!', 'Seu otário!', 'Sua imbecil!', 'Infeliz burro',
                  'Desgraçado!', 'Você é um lixo', 'Vai para o inferno', 'Seu burro'):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], 'social:critica')

    def test_criticas_repetidas_nao_repetem_a_mesma_resposta(self):
        bot = Crivo()
        respostas = [bot.responder(q)[1] for q in ('Sua resposta está ruim', 'Seu imbecil', 'Idiota', 'Seu otário', 'Idiota', 'Idiota')]
        self.assertEqual(len(set(respostas[:4])), 4)
        self.assertTrue(all(a != b for a, b in zip(respostas, respostas[1:])))

    def test_critica_composta_responde_pedido(self):
        for q in ('Idiota! O que é RNA?', 'Seu otário; mas o que é DNA?',
                  'Seu burro. O que é DNA?'):
            with self.subTest(q=q):
                self.assertIn(Crivo().responder(q)[0], ('conhecimento:dna', 'conhecimento:rna'))

    def test_interromper_nao_pede_mais_informacao(self):
        bot = Crivo()
        bot.responder('O que é DNA?')
        for q in ('Cala a boca então', 'Pare de falar', 'Não responda mais', 'Fique quieto'):
            ident, resposta = bot.responder(q)
            self.assertEqual(ident, 'social:interromper')
            self.assertNotIn('?', resposta)
            self.assertIsNone(bot.ultima_resposta_mostrada)
        self.assertEqual(bot.responder('O que é RNA?')[0], 'conhecimento:rna')

    def test_parar_cancelando_exercicio(self):
        bot = Crivo()
        self.assertEqual(bot.responder('Me testa sobre Marte')[0], 'estudo:pergunta')
        self.assertEqual(bot.responder('Pare de falar')[0], 'social:interromper')
        self.assertIsNone(bot.conversacao.quiz)
        self.assertEqual(bot.responder('O que é DNA?')[0], 'conhecimento:dna')

    def test_desistencia_em_exercicio_mantem_sentido_especifico(self):
        bot = Crivo()
        bot.responder('Me testa sobre Marte')
        ident, resposta = bot.responder('Desisto')
        self.assertEqual(ident, 'estudo:correcao')
        self.assertIn('A resposta é', resposta)

    def test_palavra_ambigua_depende_do_contexto(self):
        for palavra in ('Lixo', 'Burro'):
            with self.subTest(palavra=palavra):
                bot = Crivo()
                self.assertNotEqual(bot.responder(palavra)[0], 'social:critica')
                bot.responder('Você não me entendeu')
                bot.responder('O que é DNA?')
                self.assertEqual(bot.responder(palavra)[0], 'social:critica')

    def test_contexto_expira_e_reinicio_interrompe(self):
        for fim in (['Oi'], ['Vamos começar outra conversa'], ['O que é DNA?', 'O que é RNA?', 'O que é HTML?']):
            with self.subTest(fim=fim):
                bot = Crivo()
                bot.responder('Sua resposta é ruim')
                for q in fim:
                    bot.responder(q)
                self.assertNotEqual(bot.responder('Lixo')[0], 'social:critica')
        self.assertFalse(frustracao_recente([{'id': 'fora', 'pergunta': 'você é burro'}]))

    def test_contexto_nao_apaga_pedidos_explicitos(self):
        bot = Crivo()
        bot.responder('Você não me entendeu')
        for q in ('O que é lixo eletrônico?', 'Como reciclar lixo?', 'Um burro é um mamífero?',
                  'Meu amigo é um idiota', 'Não cale a boca', 'Eu sou burro',
                  'O que significa cala a boca?', 'Eu desisto de estudar química'):
            with self.subTest(q=q):
                self.assertNotIn(bot.responder(q)[0], ('social:critica', 'social:interromper', 'social:desistencia'))

    def test_boa_noite_preserva_despedida_depois_de_conversa(self):
        for q in ('Boa noite', 'Boa noite, Crivo!'):
            with self.subTest(q=q):
                self.assertEqual(Crivo().responder(q)[0], 'social:oi')
                bot = Crivo()
                for inicio in ('O que é DNA?', 'O que é RNA?', 'O que é HTML?', 'Sua resposta está ruim'):
                    bot.responder(inicio)
                self.assertEqual(bot.responder(q)[0], 'social:despedida')

    def test_despedida_cotidiana_encerra_frustracao(self):
        for q in ('Tchau', 'Boa noite, Crivo!'):
            with self.subTest(q=q):
                bot = Crivo()
                for inicio in ('O que é DNA?', 'O que é RNA?', 'O que é HTML?', 'Sua resposta está ruim'):
                    bot.responder(inicio)
                self.assertEqual(bot.responder(q)[0], 'social:despedida')
                self.assertNotEqual(bot.responder('Lixo')[0], 'social:critica')

    def test_citacoes_nao_sao_atos_dirigidos(self):
        for q in ('"Idiota"', '“Cala a boca”', '`Lixo`', "'Desisto'", 'Ela disse: idiota'):
            with self.subTest(q=q):
                self.assertIsNone(identificar_contato(q, True))
                self.assertNotIn(Crivo().responder(q)[0], ('social:critica', 'social:interromper', 'social:desistencia'))

    def test_crise_depois_de_encerramento_mantem_prioridade(self):
        bot = Crivo()
        bot.responder('Seu idiota')
        bot.responder('Cala a boca')
        ident, resposta = bot.responder('Vou morrer')
        self.assertEqual(ident, 'crise:suicidio')
        self.assertIn('188', resposta)
        self.assertIn('192', resposta)

    def test_api_reconstroi_contexto_sem_confiar_em_ids_do_cliente(self):
        r = responder_web({'message': 'Lixo', 'history': ['Você é confuso', 'O que é DNA?']})
        self.assertEqual(r['id'], 'social:critica')
        self.assertFalse(r['has_proof'])
        self.assertNotEqual(responder_web({'message': 'Lixo'})['id'], 'social:critica')

    def test_api_preserva_mensagem_original_e_metadados(self):
        q = 'Salve, velho! O que é DNA?'
        bot = Crivo()
        self.assertEqual(bot.responder(q)[0], 'conhecimento:dna')
        self.assertEqual(bot.historico[-1]['pergunta'], q)
        self.assertEqual(bot.ultimo_turno['pergunta'], q)
        r = responder_web({'message': q})
        self.assertEqual(r['mechanism'], 'composicao_factual')

    def test_conceitos_e_fontes_preservam_pesos(self):
        bot = Crivo()
        # 447 até 2026-10-03; 611 com os catálogos ampliados de 2026-10-05; 747 com o
        # acervo profundo de 2026-10-06; 1016 com as lacunas de 2026-10-07 (a
        # rede de 747 continua valendo para as entradas que conhece).
        self.assertEqual(len(bot.base), 1016)
        self.assertIsNotNone(bot.rede, bot.erro_rede)
        for q, ident, trecho, fonte in (
            ('O que é um humano?', 'conhecimento:ser_humano', 'Homo sapiens', 'humanorigins.si.edu'),
            ('O que é o vácuo?', 'conhecimento:vacuo', 'matéria', 'home.cern'),
        ):
            with self.subTest(q=q):
                self.assertEqual(bot.responder(q)[0], ident)
                self.assertIn(trecho, bot.ultima_resposta_mostrada)
                fontes = bot.responder('Quais fontes?')[1]
                self.assertIn(fonte, fontes)
                self.assertNotIn('não tenho', fontes.lower())
        for ident in ('ser_humano', 'vacuo'):
            item = bot.compositor.itens[ident]
            self.assertNotIn('id_resposta', item)
            for fato in item['fatos']:
                self.assertTrue(bot.compositor.fontes[fato['fonte']]['url'].startswith('https://'))


if __name__ == '__main__':
    unittest.main()
