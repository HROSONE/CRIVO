"""Contratos de análise de textos inéditos, fidelidade e isolamento de fonte."""
import unittest
from analise_conteudo import AnaliseConteudo, pedido, unidades
from web_core import PedidoInvalido, responder_web

FONTE = ('O projeto depende de testes. Os testes reduzem erros. '
         'Porém, o projeto está atrasado. O projeto está pronto. O projeto não está pronto.')


class TestesAnaliseConteudo(unittest.TestCase):
    def test_relato_preserva_conversa_e_texto_pessoal_aceita_analise(self):
        relato = 'Fui ao ensaio cedo, mas o ônibus atrasou e perdi a primeira música.'
        self.assertIsNone(pedido('Resuma este relato: ' + relato))
        r = responder_web({'message': 'Resuma este relato: ' + relato})
        self.assertEqual(r['id'], 'conversa:gerada_resumo')
        r = responder_web({'message': 'Resuma este texto: ' + relato})
        self.assertEqual(r['id'], 'texto:resumo')

    def test_resumo_preserva_fonte_offsets_e_negacoes(self):
        a = AnaliseConteudo()
        ident, resposta = a.responder('Resuma este texto em 2 frases: ' + FONTE)
        self.assertEqual(ident, 'texto:resumo')
        self.assertEqual(len(a.ultima['selecionadas']), 2)
        self.assertLess(len(a.ultima['selecionadas']), a.ultima['unidades'])
        for e in a.ultima['evidencias']:
            self.assertEqual(FONTE[e['inicio']:e['fim']], e['texto'])
            self.assertIn(e['texto'], resposta)

    def test_padrao_e_oposicao_tem_evidencias_sem_prova(self):
        r = responder_web({'message': 'Identifique os padrões nesta sequência de ideias: ' + FONTE})
        a = r['content_analysis']
        self.assertEqual(r['mechanism'], 'analise_conteudo')
        self.assertFalse(r['has_proof'])
        self.assertFalse(r['generation']['usada'])
        op = next(p for p in a['padroes'] if p['tipo'] == 'oposicao_literal')
        self.assertEqual(op['estatuto'], 'hipotese')
        self.assertEqual(len(op['evidencias']), 2)
        ids = {e['id'] for e in a['evidencias']}
        self.assertTrue(all(set(p['evidencias']) <= ids for p in a['padroes']))

    def test_resumo_nao_apaga_o_lado_negado_de_uma_oposicao(self):
        a = AnaliseConteudo()
        _, r = a.responder('Resuma em 1 frase: O projeto está pronto. O projeto não está pronto.')
        self.assertIn('O projeto está pronto.', r)
        self.assertIn('O projeto não está pronto.', r)
        self.assertIn('exceda', r)

    def test_resumo_nao_repete_frases_iguais(self):
        a = AnaliseConteudo()
        a.responder('Resuma este texto: ' + 'Os testes terminaram. ' * 10)
        self.assertEqual(len(a.ultima['selecionadas']), 1)

    def test_sem_padrao_nao_inventa_tema(self):
        a = AnaliseConteudo()
        _, r = a.responder('Identifique padrões: Cristais brilham. Cavalos dormem. Trens circulam.')
        self.assertEqual(a.ultima['padroes'], [])
        self.assertIn('Não encontrei', r)

    def test_condicoes_diferentes_nao_sao_oposicao_literal(self):
        a = AnaliseConteudo()
        a.responder('Analise este texto: Hoje o projeto está pronto. Ontem o projeto não está pronto.')
        self.assertFalse(any(p['tipo'] == 'oposicao_literal' for p in a.ultima['padroes']))

    def test_replay_resumo_padroes_e_fonte(self):
        h = ['Texto: ' + FONTE]
        for q in ('Resuma isso', 'E os padrões?', 'Qual a fonte?'):
            r = responder_web({'message': q, 'history': h})
            self.assertEqual(r['mechanism'], 'analise_conteudo', r)
            self.assertEqual(r['content_analysis']['origem'], 'conteudo_enviado')
            h.append(q)
        self.assertIn('conteúdo enviado por você', r['response'])
        self.assertNotIn('http', r['response'])

    def test_troca_de_assunto_e_requisicao_isolada_nao_vazam_fonte(self):
        a = AnaliseConteudo()
        a.responder('Texto: Informação particular inédita.')
        a.responder('Oi')
        self.assertIsNone(a.responder('Resuma isso'))
        r = responder_web({'message': 'Resuma o texto enviado'})
        self.assertEqual(r['id'], 'texto:pedir_conteudo')
        self.assertNotIn('particular', r['response'])

    def test_conteudo_nao_e_memoria_pessoal_nem_acervo(self):
        r = responder_web({'message': 'Analise este conteúdo: Meu nome é Joana. Eu gosto de correr.', 'memory': {}})
        self.assertNotEqual(r['memory'].get('nome'), 'Joana')
        self.assertEqual(r['content_analysis']['origem'], 'conteudo_enviado')

    def test_listas_numeradas_e_decimais(self):
        fonte = '1. O custo foi 3,14 reais.\n2. A meta foi 5.25 unidades.\n3. Os testes terminaram.'
        us = unidades(fonte)
        self.assertEqual(len(us), 3)
        self.assertIn('5.25', us[1]['texto'])
        for e in us:
            self.assertEqual(fonte[e['inicio']:e['fim']], e['texto'])

    def test_texto_longo_aceito_so_no_contrato_de_conteudo(self):
        fonte = 'O relatório registra testes com resultados consistentes e custos detalhados. ' * 30
        q = 'Resuma este texto: ' + fonte
        r = responder_web({'message': q})
        self.assertEqual(r['id'], 'texto:resumo')
        self.assertEqual(responder_web({'message': 'E os padrões?', 'history': [q]})['id'], 'texto:padroes')
        for mensagem in ('x' * 1201, 'Analise este texto: ' + 'x' * 12001):
            with self.assertRaises(PedidoInvalido):
                responder_web({'message': mensagem})

    def test_texto_citado_longo_e_pedido_combinado(self):
        p = pedido('Resuma e identifique padrões: ' + FONTE)
        self.assertEqual(p.modo, 'analise')
        r = responder_web({'message': 'Resuma este texto "' + FONTE + '"'})
        self.assertEqual(r['id'], 'texto:resumo')

    def test_conteudo_invalido_nao_reutiliza_anterior(self):
        a = AnaliseConteudo()
        a.responder('Texto: Texto particular anterior.')
        a.responder('Texto: ')
        self.assertIsNone(a.responder('Resuma isso'))

    def test_reflexivo_e_logo_da_marca_nao_implicam_condicao_ou_conclusao(self):
        a = AnaliseConteudo()
        a.responder('Analise este conteúdo: A equipe se reuniu. O logo da marca mudou.')
        self.assertFalse(any(p['tipo'] in ('condicao', 'conclusao_apresentada') for p in a.ultima['padroes']))

    def test_limite_agregado_do_historico(self):
        with self.assertRaises(PedidoInvalido):
            responder_web({'message': 'Resuma isso', 'history': ['Texto: ' + 'x' * 9000] * 3})


if __name__ == '__main__':
    unittest.main()
