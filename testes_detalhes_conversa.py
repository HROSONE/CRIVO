"""Continuidade de escolhas pessoais; não demonstra geração livre ou causalidade."""
import unittest

from dialogo_situado import DialogoSituado
from testes_dialogo_situado import bot_fixture


class TestesEscopoDetalhes(unittest.TestCase):
    def test_relato_nativo_preserva_receio_sem_celebrar(self):
        from linguagem_conversa import Conversacao
        c = Conversacao(usar_neural=False)
        c.assunto = 'projeto pessoal'
        texto = 'Quero apresentar meu trabalho, mas tenho medo de errar.'
        _, resposta, _, _ = c._relato(texto)
        self.assertIn('medo de errar', resposta)
        self.assertIn('avaliar', resposta)
        self.assertNotIn('que legal', resposta.lower())
        self.assertEqual(list(c.relatos), [texto])

    def test_declaracao_sem_prefixo_pessoal_entra_com_fonte_literal(self):
        d = DialogoSituado()
        b = bot_fixture(['Quero escolher um curso'])
        texto = 'O curso noturno cabe na minha rotina, o outro exige uma viagem.'
        self.assertIsNone(d.responder(texto, b))
        r = d.responder(texto, b, apos_recusa=True)
        self.assertIn(texto.rstrip('.'), r[1])
        self.assertEqual(d.ultimo['fontes'], [*b.conversacao.relatos, texto])
        d.observar(texto, r[0], b)
        self.assertIn(texto, d.quadro(b.conversacao)['relatos'])

    def test_condicoes_citacoes_e_pedidos_nao_viram_fatos_pessoais(self):
        b = bot_fixture(['Quero escolher um curso'])
        d = DialogoSituado()
        for texto in (
            'O curso cabe na minha rotina se eu mudar de horário.',
            'O curso talvez caiba na minha rotina.',
            'Um colega disse que eu devia mudar de curso.',
            'O anúncio diz "minha rotina ficará livre".',
            'Explique o meu algoritmo de ordenação.',
            'Por favor calcule a minha despesa.',
            'Como funciona o meu aparelho',
        ):
            with self.subTest(texto=texto):
                self.assertIsNone(d.responder(texto, b, apos_recusa=True))
        self.assertEqual(list(b.conversacao.relatos), ['Quero escolher um curso'])

    def test_nao_usa_criterios_antigos_em_comparacao_factual_explicita(self):
        d = DialogoSituado()
        b = bot_fixture(['Quero escolher um curso', 'Meu orçamento é limitado'])
        for texto in ('Me ajuda a comparar os planetas Júpiter e Marte?',
                      'Compare minhas opções de algoritmos: busca linear e binária.'):
            self.assertIsNone(d.responder(texto, b))

    def test_sem_contexto_ou_apos_consulta_factual_nao_recicla_relato(self):
        d = DialogoSituado()
        texto = 'A casa fica perto dos meus amigos.'
        self.assertIsNone(d.responder(texto, bot_fixture()))
        b = bot_fixture(['Quero mudar de casa', 'Minha prioridade é o espaço'])
        d.observar('O que é DNA?', 'conhecimento:dna', b)
        self.assertIsNone(d.responder(texto, b))
        self.assertIsNone(d.responder('Compare essas opções.', b))

    def test_fala_de_outra_pessoa_nao_muda_objetivo_ou_disponibilidade(self):
        d = DialogoSituado()
        b = bot_fixture(['Quero terminar meu desenho', 'Tenho 21 minutos'])
        texto = 'Uma amiga sugeriu que eu devia abandonar o desenho, mas discordo.'
        r = d.responder(texto, b)
        self.assertIn('outra pessoa', r[1])
        d.observar(texto, r[0], b)
        q = d.quadro(b.conversacao)
        self.assertEqual(q['objetivo'], 'Quero terminar meu desenho')
        self.assertEqual(q['minutos'], '21')
        self.assertNotIn(texto, q['relatos'])


class TestesIntegracaoDetalhes(unittest.TestCase):
    def test_comparacao_recupera_condicoes_declaradas_em_outro_assunto(self):
        from crivo import Crivo
        b = Crivo()
        entradas = ['Quero mudar de casa, mas tenho receio de me arrepender.',
                    'A casa menor fica perto dos meus amigos; a maior exige uma viagem longa.',
                    'Espaço ajuda, mas minha prioridade é passar menos tempo no trânsito.']
        for texto in entradas:
            antes = b.conversacao.turno
            _, resposta = b.responder(texto)
            self.assertNotIn('não entendi', resposta.lower())
            self.assertEqual(b.conversacao.turno, antes + 1)
        _, resposta = b.responder('Compare essas opções sem escolher por mim.')
        for texto in entradas:
            self.assertIn(texto.rstrip('.'), resposta)
        self.assertNotIn('Que opções você está considerando', resposta)
        self.assertEqual(b.dialogo_situado.ultimo['fontes'], entradas)
        self.assertEqual(list(b.conversacao.relatos), entradas)

    def test_receio_nao_e_celebrado_com_diferentes_aberturas(self):
        from crivo import Crivo
        for texto in ('Quero mudar de casa, mas tenho medo de me arrepender.',
                      'Estou pensando em trocar de emprego, mas tenho receio de me arrepender.'):
            with self.subTest(texto=texto):
                _, resposta = Crivo().responder(texto)
                self.assertIn('avaliar', resposta)
                for elogio in ('que legal', 'que bom', 'boa!', 'principal dificuldade'):
                    self.assertNotIn(elogio, resposta.lower())

    def test_sugestao_indireta_preserva_objetivo_sem_elogio(self):
        from crivo import Crivo
        b = Crivo()
        b.responder('Quero terminar minha pesquisa.')
        objetivo = b.conversacao.objetivo
        _, resposta = b.responder('Uma colega disse que eu devia desistir, mas não concordo.')
        self.assertIn('outra pessoa', resposta)
        self.assertNotIn('Boa!', resposta)
        self.assertEqual(b.conversacao.objetivo, objetivo)
        self.assertEqual(list(b.conversacao.relatos), ['Quero terminar minha pesquisa.'])

    def test_web_reconstroi_criterios_sem_vazar_para_sessao_vazia(self):
        from web_core import responder_web
        historico = ['Quero escolher um curso, mas tenho receio de me arrepender.',
                     'O curso de manhã cabe no meu orçamento, o da noite tem aulas práticas.',
                     'Experiência importa, mas minha prioridade é reduzir as despesas.']
        r = responder_web({'history': historico, 'message': 'Me ajuda a comparar sem decidir por mim?'})
        for texto in historico:
            self.assertIn(texto.rstrip('.'), r['response'])
        isolado = responder_web({'message': 'Me ajuda a comparar sem decidir por mim?'})
        self.assertNotIn('aulas práticas', isolado['response'])
        self.assertNotIn('reduzir as despesas', isolado['response'])


if __name__ == '__main__':
    unittest.main()
