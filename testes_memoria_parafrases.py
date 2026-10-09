"""Transferência de formulações sem inventar fatos ou perder o escopo."""
import unittest
from memoria_sessao import MemoriaSessao


class TestesParafrasesMemoria(unittest.TestCase):
    def sessao(self):
        m = MemoriaSessao()
        m.processar('Azura é minha irmã.')
        m.processar('Nival é meu primo.')
        return m

    def test_consultas_equivalentes_preservam_proprietario(self):
        m = self.sessao()
        for t in ('Azura prefere chá de jabuticaba.', 'Nival prefere suco de manga.',
                  'A mala de Azura é azul.', 'A mala de Nival é verde.',
                  'A mala de Azura está no armário.', 'A mala de Nival está na varanda.'):
            m.processar(t)
        for query,value,wrong in (
                ('Você lembra o que Azura prefere?', 'chá de jabuticaba', 'suco de manga'),
                ('Você recorda o que Azura prefere?', 'chá de jabuticaba', 'suco de manga'),
                ('A mala de Azura é de que cor?', 'azul', 'verde'),
                ('Em que lugar está a mala de Azura?', 'armário', 'varanda')):
            with self.subTest(query=query):
                answer = m.processar(query)[1]
                self.assertIn('Azura', answer)
                self.assertIn(value, answer)
                self.assertNotIn(wrong, answer)
                self.assertNotIn('Nival', answer)
        self.assertIsNone(m.processar('O solo de Marte é de que cor?'))
        self.assertIsNone(m.processar('Em que lugar está o núcleo do Átomo?'))

    def test_objetivo_restricao_e_tempo_nao_misturam_pessoas(self):
        m = self.sessao()
        for t in ('Azura pretende terminar a escultura.', 'Nival quer revisar o mapa.',
                  'Azura não pode dirigir.', 'Nival pode dirigir.',
                  'Tenho apenas 27 minutos disponíveis.', 'Nival tem 65 minutos disponíveis.'):
            m.processar(t)
        self.assertIn('terminar a escultura', m.processar('O que Azura quer fazer?')[1])
        self.assertNotIn('revisar o mapa', m.processar('O que Azura quer fazer?')[1])
        self.assertIn('não pode dirigir', m.processar('O que Azura não pode fazer?')[1])
        self.assertIn('27 minutos', m.processar('Quantos minutos eu tenho disponíveis?')[1])
        self.assertNotIn('65 minutos', m.processar('Quantos minutos eu tenho disponíveis?')[1])
        m.processar('Tenho menos de 10 minutos disponíveis.')
        self.assertIn('27 minutos', m.processar('Quantos minutos eu tenho disponíveis?')[1])

    def test_correcao_composta_e_fontes_literais(self):
        m = self.sessao()
        m.processar('Azura prefere chá.')
        text = 'Azura não prefere mais chá; agora prefere suco.'
        m.processar(text)
        answer = m.processar('O que Azura prefere?')[1]
        self.assertIn('suco', answer)
        self.assertNotIn('chá', answer)
        self.assertEqual(m.ultimo['fontes'][0]['texto'], text)
        states = [f['status'] for f in m.afirmacoes if f['relacao'] == 'preferência']
        self.assertEqual(states, ['retirado', 'ativo'])
        text = 'Azura prefere pitanga; Nival prefere graviola.'
        m.processar(text)
        self.assertIn('graviola', m.processar('O que Nival prefere?')[1])
        self.assertNotIn('pitanga', m.processar('O que Nival prefere?')[1])
        self.assertEqual(m.ultimo['fontes'][0]['texto'], text)
        m.processar('Azura prefere café; faça uma história.')
        self.assertIn('pitanga', m.processar('O que Azura prefere?')[1])

    def test_compostas_hipoteticas_citadas_e_ambiguas_nao_atualizam(self):
        m = self.sessao()
        m.processar('Maelis é minha colega.')
        m.processar('Azura prefere chá.')
        for t in ('Se Azura prefere café; Nival prefere suco.',
                  '“Azura prefere café; Nival prefere suco”.',
                  'Azura prefere café; ela prefere leite.'):
            m.processar(t)
        self.assertIn('chá', m.processar('O que Azura prefere?')[1])
        self.assertNotIn('suco', m.processar('O que Nival prefere?')[1])

    def test_escolha_explicita_e_posse_por_pessoa(self):
        m = self.sessao()
        m.processar('Azura escolhe chá sem açúcar em vez de café.')
        self.assertIn('chá sem açúcar', m.processar('O que Azura prefere?')[1])
        self.assertNotIn('café', m.processar('O que Azura prefere?')[1])
        m.processar('Se Azura escolhe leite em vez de chá, o plano muda?')
        self.assertIn('chá sem açúcar', m.processar('O que Azura prefere?')[1])
        m.processar('Azura é dona da bolsa térmica.')
        m.processar('Nival é dono do caderno espiral.')
        self.assertIn('Azura', m.processar('A quem pertence a bolsa térmica?')[1])
        self.assertNotIn('Nival', m.processar('A quem pertence a bolsa térmica?')[1])
        self.assertIn('Nival', m.processar('A quem pertence o caderno espiral?')[1])

    def test_prefixo_correcao_preserva_outros_atributos(self):
        m = self.sessao()
        m.processar('A mala de Azura é azul.')
        m.processar('A mala de Azura está no armário.')
        m.processar('Correção: a mala de Azura é verde.')
        self.assertIn('verde', m.processar('A mala de Azura é de que cor?')[1])
        self.assertNotIn('azul', m.processar('A mala de Azura é de que cor?')[1])
        self.assertIn('armário', m.processar('Onde está a mala de Azura?')[1])
        self.assertEqual(len(m.correcoes), 1)


if __name__ == '__main__':
    unittest.main()
