"""Contratos da memória: vínculo, literalidade, fonte e isolamento."""
import unittest

from memoria_sessao import MemoriaSessao


class TestesMemoriaSessao(unittest.TestCase):
    def test_renomear_pessoas_objetos_e_preferencias_preserva_relacao(self):
        for a, b, objeto, preferencia in (
                ('Lia', 'Maria', 'mochila', 'chá sem açúcar'),
                ('Áurea-X77', 'Nixor-Y21', 'caderno espiral', 'suco de pitanga')):
            with self.subTest(a=a):
                m = MemoriaSessao()
                m.processar(a + ' é minha irmã.')
                m.processar(b + ' é minha prima.')
                m.processar(a + ' tem uma ' + objeto + ' azul.')
                m.processar(b + ' tem uma ' + objeto + ' verde.')
                m.processar(a + ' prefere ' + preferencia + '.')
                r = m.processar('De que cor é a ' + objeto + ' de ' + a + '?')[1]
                self.assertIn(a, r)
                self.assertIn('azul', r)
                self.assertNotIn('verde', r)
                self.assertNotIn(b, r)
                self.assertIn(preferencia, m.processar('O que ' + a + ' prefere?')[1])

    def test_correcao_preserva_local_e_apos_retracao_nao_inventa_cor(self):
        m = MemoriaSessao()
        for s in ('Lia é minha irmã.', 'A mochila de Lia é azul.',
                  'A mochila de Lia está na gaveta.', 'Corrigindo: a mochila de Lia é verde.'):
            m.processar(s)
        self.assertIn('verde', m.processar('Qual é a cor da mochila de Lia?')[1])
        self.assertIn('gaveta', m.processar('Onde está a mochila de Lia?')[1])
        m.processar('Corrigindo: não sei a cor da mochila de Lia.')
        r = m.processar('De que cor é a mochila de Lia?')[1]
        self.assertIn('Não tenho', r)
        self.assertNotIn('azul', r)
        self.assertNotIn('verde', r)
        e = m.exportar()
        self.assertEqual([f['status'] for f in e['afirmacoes'] if f['relacao'] == 'cor'],
                         ['substituido', 'retirado'])
        self.assertEqual(len(e['correcoes']), 2)

    def test_hipoteses_perguntas_e_citacoes_nao_substituem_preferencia(self):
        m = MemoriaSessao()
        m.processar('Eu prefiro chá sem açúcar.')
        for s in ('Se eu prefiro café, isso muda algo?', 'Eu prefiro café?',
                  'Imagine que eu prefiro café.', 'Eu prefiro café se houver leite.',
                  '“Eu prefiro café”.', 'Lia disse que eu prefiro café.'):
            m.processar(s)
        r = m.processar('O que eu prefiro?')[1]
        self.assertIn('chá sem açúcar', r)
        self.assertNotIn('café', r)
        self.assertEqual(len(m.exportar()['afirmacoes']), 1)

    def test_atribuicao_relata_sem_promover_para_usuario(self):
        m = MemoriaSessao()
        m.processar('Eu prefiro café.')
        s = 'Lia disse que prefere chá.'
        m.processar(s)
        self.assertNotIn('chá', m.processar('O que eu prefiro?')[1])
        self.assertIn('chá', m.processar('O que Lia disse que prefere?')[1])
        self.assertEqual(m.ultimo['fontes'], [dict(origem='usuario', turno=2, texto=s)])
        self.assertEqual(m.exportar()['afirmacoes'][1]['escopo'], 'fala_reportada')

    def test_negacao_propria_retrai_sem_trocar_pessoa(self):
        m = MemoriaSessao()
        m.processar('Eu prefiro café.')
        m.processar('Corrigindo: eu não prefiro café.')
        self.assertNotIn('café', m.processar('O que eu prefiro?')[1])
        m.processar('Quero terminar o desenho.')
        m.processar('Não quero terminar o desenho.')
        self.assertNotIn('terminar o desenho', m.processar('Qual é o objetivo de eu?')[1])
        self.assertEqual(len(m.entidades), 1)

    def test_pronome_ambiguo_nao_usa_apenas_a_ultima_pessoa(self):
        m = MemoriaSessao()
        m.processar('Lia é minha irmã.')
        m.processar('Maria é minha prima.')
        m.processar('Lia prefere chá.')
        m.processar('Maria prefere café.')
        self.assertIn('qual pessoa', m.processar('O que ela prefere?')[1])
        self.assertEqual(m.ultimo['afirmacoes'], [])
        m.processar('Ela prefere suco.')
        self.assertEqual(len(m.exportar()['afirmacoes']), 4)

    def test_copia_isolamento_reinicio_e_mudanca_de_tema(self):
        a, b = MemoriaSessao(), MemoriaSessao()
        a.processar('Lia é minha irmã.')
        a.processar('Lia prefere chá.')
        a.processar('Mudando de assunto, vamos falar sobre chuva.')
        self.assertIn('chá', a.processar('O que Lia prefere?')[1])
        e = a.exportar()
        e['afirmacoes'].clear()
        self.assertEqual(len(a.afirmacoes), 2)
        self.assertNotIn('chá', b.processar('O que Lia prefere?')[1])
        a.processar('Esqueça tudo que eu contei aqui.')
        self.assertEqual(a.exportar()['afirmacoes'], [])
        self.assertNotIn('chá', a.processar('O que Lia prefere?')[1])

    def test_query_nunca_vira_fonte_e_negacao_nao_apaga_valor_diferente(self):
        m = MemoriaSessao()
        s = 'Lia prefere chá.'
        m.processar(s)
        m.processar('Lia não prefere café.')
        m.processar('O que Lia prefere?')
        m.processar('O que Lia prefere?')
        self.assertEqual(m.ultimo['fontes'][0]['texto'], s)
        self.assertEqual(len(m.afirmacoes), 1)

    def test_agenda_multiclausula_ficcao_e_pergunta_sem_evidencia_mantem_rotas(self):
        m = MemoriaSessao()
        self.assertIsNone(m.processar('Nina pode segunda ou sábado. Ravi pode sábado. Qual dia dá?'))
        self.assertIsNone(m.processar('Lia prefere café.', ficcao=True))
        self.assertIsNone(m.processar('Na história, Lia prefere café.'))
        self.assertIsNone(m.processar('Lia prefere café?'))
        self.assertEqual(m.exportar()['afirmacoes'], [])
        self.assertIsNone(m.processar('Onde está o núcleo do átomo?'))
        self.assertIsNone(m.processar('De que cor é o sangue do sapo?'))
        self.assertIsNone(m.processar('De que cor é o solo de Marte?'))
        self.assertIsNone(m.processar('Onde está o núcleo do Átomo?'))
        self.assertIsNone(m.processar('A quem pertence a Argentina?'))

    def test_pedidos_de_operacao_nao_inventam_pessoas_ou_objetivos(self):
        m = MemoriaSessao()
        for prefixo in ('Reformule:', 'Reformule', 'Reescreva:', 'Traduza:', 'Corrija:', 'Explique:'):
            with self.subTest(prefixo=prefixo):
                self.assertIsNone(m.processar(prefixo + ' Quero pedir ajuda sem cobrar uma resposta.'))
        self.assertEqual(m.exportar()['entidades'], [])
        self.assertEqual(m.exportar()['afirmacoes'], [])
        m.processar('Lia prefere chá.')
        self.assertIn('chá', m.processar('Resuma o que eu disse sobre Lia.')[1])


class TestesIntegracaoMemoriaSessao(unittest.TestCase):
    def test_chat_preserva_vinte_minutos_e_mochila_da_lia(self):
        from crivo import Crivo
        b = Crivo()
        for s in ('Lia é minha irmã.', 'Maria é minha prima.',
                  'Lia tem uma mochila azul.', 'Maria tem uma mochila verde.',
                  'Tenho 20 minutos disponíveis.', 'Maria tem 60 minutos disponíveis.'):
            b.responder(s)
        ident, resposta = b.responder('De que cor é a mochila da Lia?')
        self.assertEqual(ident, 'conversa:memoria_sessao')
        self.assertIn('Lia', resposta)
        self.assertIn('azul', resposta)
        self.assertNotIn('Maria', resposta)
        self.assertNotIn('verde', resposta)
        self.assertIn('20 minutos', b.responder('Quantos minutos eu tenho disponíveis?')[1])
        self.assertEqual(b.ultima_geracao['usada'], False)

    def test_web_reconstroi_historico_e_nao_compartilha_estado(self):
        from web_core import responder_web
        history = ['Lia é minha irmã.', 'Lia prefere chá.', 'Corrigindo: Lia prefere suco.']
        payload = dict(history=history, message='O que Lia prefere?')
        a = responder_web(payload)
        b = responder_web(payload)
        self.assertEqual(a['response'], b['response'])
        self.assertIn('suco', a['response'])
        self.assertNotIn('chá', a['response'])
        self.assertEqual(a['session_memory'], b['session_memory'])
        self.assertEqual(a['session_memory']['fontes'][0]['texto'], history[-1])
        vazio = responder_web(dict(message='O que Lia prefere?'))
        self.assertNotIn('suco', vazio['response'])
        self.assertNotIn('chá', vazio['response'])

    def test_rotas_factuais_crise_e_codigo_preservadas(self):
        from crivo import Crivo
        b = Crivo()
        b.responder('Lia prefere chá.')
        self.assertNotEqual(b.responder('O que é DNA?')[0], 'conversa:memoria_sessao')
        self.assertNotEqual(b.responder('Escreva uma função Python que soma dois números.')[0],
                            'conversa:memoria_sessao')
        ident, _ = b.responder('Quero me matar agora.')
        self.assertTrue(ident.startswith('crise:'), ident)

    def test_reinicio_nativo_limpa_a_memoria_nova(self):
        from crivo import Crivo
        b = Crivo()
        b.responder('Lia prefere chá.')
        ident, _ = b.responder('Esqueça essa conversa')
        self.assertEqual(ident, 'conversa:reinicio')
        self.assertEqual(b.memoria_sessao.exportar()['afirmacoes'], [])
        self.assertNotIn('chá', b.responder('O que Lia prefere?')[1])


if __name__ == '__main__':
    unittest.main()
