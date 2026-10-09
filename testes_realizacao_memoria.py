"""Consumo do estado atual, guardas de fonte e integração neural real."""
import copy
import unittest
from unittest.mock import patch

from memoria_sessao import MemoriaSessao
from realizacao_memoria import realizar


class GeradorControlado:
    disponivel = True

    def __init__(self, resposta=None):
        self.resposta = resposta
        self.chamadas = []
        self.bpe = self

    def codificar(self, texto):
        return list(range(len(texto.split())))

    def prompt(self, pergunta, fatos):
        return [ord(c) for c in pergunta + '\n' + '\n'.join(fatos)]

    def gerar(self, pergunta, fatos, diagnostico=None):
        self.chamadas.append((pergunta, copy.deepcopy(fatos)))
        diagnostico.update(tentativas=1, motivo='gerada' if self.resposta is None else 'guarda_rejeitou')
        return self.resposta if self.resposta is not None else fatos[0]


class TestesFonteDoRealizador(unittest.TestCase):
    def memoria(self):
        m = MemoriaSessao()
        m.processar('Lia prefere chá.')
        m.processar('Maria prefere café.')
        m.processar('O que Lia prefere?')
        return m

    def test_modelo_recebe_somente_sujeito_e_valor_consultados(self):
        m, g = self.memoria(), GeradorControlado()
        snapshot = m.exportar()
        resposta, trace = realizar('O que Lia prefere?', m, g)
        self.assertEqual(g.chamadas, [('O que Lia prefere?', ['Lia prefere chá.'])])
        self.assertIn('Lia prefere chá', resposta)
        self.assertNotIn('Maria', resposta)
        self.assertTrue(trace['leu_memoria'])
        self.assertTrue(trace['usada'])
        self.assertEqual(m.exportar(), snapshot)
        self.assertEqual(trace['evidencias'][0]['fonte']['texto'], 'Lia prefere chá.')

    def test_pergunta_constante_com_estado_corrigido_muda_input_e_saida(self):
        m, g = self.memoria(), GeradorControlado()
        a, ta = realizar('O que Lia prefere?', m, g)
        m.processar('Corrigindo: Lia prefere suco.')
        m.processar('O que Lia prefere?')
        b, tb = realizar('O que Lia prefere?', m, g)
        self.assertNotEqual(a, b)
        self.assertIn('suco', b)
        self.assertNotIn('chá', b)
        self.assertNotEqual(ta['passagens'][0]['prompt_sha256'], tb['passagens'][0]['prompt_sha256'])
        self.assertEqual(g.chamadas[-1][1], ['Lia prefere suco.'])

    def test_referencia_retraida_e_hipotese_nao_chegam_na_rede(self):
        for alteracao in ('retirado', 'hipotetico'):
            m, g = self.memoria(), GeradorControlado()
            idx = m.ultimo['afirmacoes'][0]
            m.afirmacoes[idx]['status' if alteracao == 'retirado' else 'escopo'] = alteracao
            resposta, trace = realizar('O que Lia prefere?', m, g)
            self.assertIsNone(resposta)
            self.assertFalse(trace['leu_memoria'])
            self.assertEqual(g.chamadas, [])

    def test_ausencia_e_ambiguidade_nao_chamam_modelo(self):
        m, g = MemoriaSessao(), GeradorControlado()
        m.processar('O que Lia prefere?')
        self.assertIsNone(realizar('O que Lia prefere?', m, g)[0])
        for s in ('Lia é minha irmã.', 'Maria é minha prima.',
                  'Lia prefere chá.', 'Maria prefere café.'):
            m.processar(s)
        m.processar('O que ela prefere?')
        self.assertIsNone(realizar('O que ela prefere?', m, g)[0])
        self.assertEqual(g.chamadas, [])

    def test_troca_de_pessoa_valor_e_polaridade_rejeitadas(self):
        for texto in ('Maria prefere chá.', 'Lia prefere café.', 'Lia não prefere chá.'):
            with self.subTest(texto=texto):
                resposta, trace = realizar('O que Lia prefere?', self.memoria(), GeradorControlado(texto))
                self.assertIsNone(resposta)
                self.assertFalse(trace['usada'])
                self.assertEqual(trace['motivo'], 'fato_da_sessao_nao_preservado')

    def test_nenhum_fato_e_cortado_para_caber_no_prompt(self):
        m, g = self.memoria(), GeradorControlado()
        idx = m.ultimo['afirmacoes'][0]
        m.afirmacoes[idx]['valor'] = ' '.join(['palavra'] * 180)
        self.assertIsNone(realizar('O que Lia prefere?', m, g)[0])
        self.assertEqual(g.chamadas, [])

    def test_fala_atribuida_preserva_atribuicao(self):
        m, g = MemoriaSessao(), GeradorControlado()
        m.processar('Lia disse que prefere chá.')
        m.processar('O que Lia disse que prefere?')
        resposta, trace = realizar('O que Lia disse que prefere?', m, g)
        self.assertIn('Lia disse que prefere chá', resposta)
        self.assertEqual(trace['evidencias'][0]['escopo'], 'fala_reportada')

    def test_rejeicao_de_uma_passagem_nao_publica_resumo_parcial(self):
        m = self.memoria()
        m.processar('Lia quer terminar o mapa.')
        m.processar('Resuma o que eu disse sobre Lia.')
        g = GeradorControlado('Lia prefere chá.')
        resposta, trace = realizar('Resuma o que eu disse sobre Lia.', m, g)
        self.assertIsNone(resposta)
        self.assertFalse(trace['usada'])
        self.assertEqual(len(g.chamadas), 2)


class TestesIntegracaoRealizador(unittest.TestCase):
    def test_transformer_proprio_recebe_correcao_e_preserva_identificador(self):
        from geracao_ancorada import geracao
        if not geracao().disponivel:
            self.skipTest('Pesos próprios ou NumPy indisponíveis')
        from crivo import Crivo
        b = Crivo(usar_linguagem_neural=False, usar_interpretador_perguntas=False)
        b.responder('Lia prefere chá.')
        ident, a = b.responder('O que Lia prefere?')
        self.assertEqual(ident, 'conversa:memoria_sessao')
        self.assertTrue(b.ultima_geracao['usada'])
        pa = b.ultima_geracao['passagens'][0]['prompt_sha256']
        b.responder('Corrigindo: Lia prefere café.')
        ident, c = b.responder('O que Lia prefere?')
        self.assertEqual(ident, 'conversa:memoria_sessao')
        self.assertIn('café', c)
        self.assertNotIn('chá', c)
        self.assertTrue(b.ultima_geracao['usada'])
        self.assertNotEqual(pa, b.ultima_geracao['passagens'][0]['prompt_sha256'])
        self.assertNotEqual(a, c)

    def test_recuo_e_chave_desligada_preservam_resposta_de_memoria(self):
        from crivo import Crivo
        b = Crivo(usar_linguagem_neural=False, usar_interpretador_perguntas=False)
        b.responder('Lia prefere chá.')
        with patch('geracao_ancorada.geracao', return_value=GeradorControlado('Maria prefere café.')):
            ident, resposta = b.responder('O que Lia prefere?')
        self.assertEqual(ident, 'conversa:memoria_sessao')
        self.assertIn('Lia prefere chá', resposta)
        self.assertFalse(b.ultima_geracao['usada'])
        b.usar_geracao_sessao = False
        with patch('geracao_ancorada.geracao', side_effect=AssertionError('Rede não deveria ser chamada')):
            b.responder('O que Lia prefere?')
        self.assertFalse(b.ultima_geracao['usada'])
