"""Contratos sem rede/modelo, gold ou leitura de painéis de avaliação."""
from copy import deepcopy
import inspect
import unittest
from ledger import aplicar


def neural(op='comparar_custos'):
    return {'operacao': op, 'confianca_operacao': .61,
            'argumentos': [None] * 3, 'referente': None, 'hipotese': True,
            'fontes': [], 'decodificacao': 'original'}


BASE = 'O plano Azul custa 23 reais. O plano Verde custa 35 reais. Compare Azul e Verde.'
CORR = 'Corrigindo Azul: o custo real é 41 reais. Compare Azul e Verde.'
HIP = 'Imagine Azul por 19 reais, sem alterar os fatos. Compare Azul e Verde.'


class Ledger(unittest.TestCase):
    def validar_fontes(self, turnos, proposta):
        for s in proposta['argumentos'] + [proposta['referente']]:
            if s:
                self.assertEqual(turnos[s['turno']][s['inicio']:s['fim']], s['texto'])

    def test_confirmar_preserva_fonte_hipotetica_como_fato(self):
        ts = [BASE, CORR, HIP,
              'A última hipótese aconteceu de verdade. Agora ela é fato. Compare Azul e Verde.',
              'Esqueça a simulação e use os preços reais corrigidos. Compare Azul e Verde.']
        for i, valor in [(1, '23'), (2, '41'), (3, '19'), (4, '19'), (5, '19')]:
            p, d = aplicar(ts[:i], neural())
            self.assertTrue(d['aplicado'], d)
            self.assertEqual(p['argumentos'][0]['texto'], valor)
            self.assertEqual(p['hipotese'], i == 3)
            self.validar_fontes(ts[:i], p)
        self.assertEqual(p['argumentos'][0]['turno'], 2)
        self.assertEqual(d['confirmacoes'], [3])

    def test_abandonar_restaura_ultima_correcao_real(self):
        ts = [BASE, CORR, HIP, 'Encerre o cenário hipotético e calcule com os fatos. Compare Azul e Verde.']
        p, d = aplicar(ts, neural()); self.assertTrue(d['aplicado'], d)
        self.assertEqual(p['argumentos'][0]['texto'], '41')
        self.assertEqual(p['argumentos'][0]['turno'], 1)
        self.assertFalse(p['hipotese'])

    def test_correcoes_reais_encerram_hipotese(self):
        ts = [BASE, HIP, 'Não é uma hipótese: Azul na verdade custa 44 reais. Compare Azul e Verde.']
        p, d = aplicar(ts, neural()); self.assertTrue(d['aplicado'], d)
        self.assertFalse(p['hipotese']); self.assertEqual(p['argumentos'][0]['texto'], '44')

    def test_hipotese_negada_nao_ocorrida_permanece_hipotese(self):
        ts = [BASE, 'Não aconteceu: imagine Azul por 18 reais em uma alternativa. Compare Azul e Verde.']
        p, d = aplicar(ts, neural()); self.assertTrue(d['aplicado'], d)
        self.assertTrue(p['hipotese']); self.assertEqual(p['argumentos'][0]['texto'], '18')

    def test_nova_hipotese_parte_do_real_e_nao_da_anterior(self):
        ts = [BASE, HIP, 'Suponha, em um novo cenário, Verde por 11 reais. Compare Azul e Verde.']
        p, d = aplicar(ts, neural()); self.assertTrue(d['aplicado'], d)
        self.assertEqual([s['texto'] for s in p['argumentos'][:2]], ['23', '11'])

    def test_entidade_e_ordem_da_pergunta_com_distratores(self):
        ts = ['O plano Cobre custa 99 reais. A entrega leva 8 dias. ' + BASE,
              'Compare Verde e Azul.']
        p, d = aplicar(ts, neural()); self.assertTrue(d['aplicado'], d)
        self.assertEqual([s['texto'] for s in p['argumentos'][:2]], ['35', '23'])
        self.validar_fontes(ts, p)

    def test_requisitos_pessoa_vinculada_e_mundo_aberto(self):
        ts = ['Para entrar são exigidos chave e selo. Ana tem chave. Rui tem chave e selo. Ana cumpre os requisitos?']
        p, d = aplicar(ts, neural('verificar_requisitos')); self.assertTrue(d['aplicado'], d)
        self.assertEqual(p['argumentos'][0]['texto'], 'chave e selo')
        self.assertEqual(p['argumentos'][1]['texto'], 'tem chave')
        self.assertEqual(p['referente']['texto'], 'Ana'); self.validar_fontes(ts, p)

    def test_inventario_confirmado_nao_e_descartado_no_retorno(self):
        ts = ['Para entrar são exigidos chave e selo. Ana tem chave. Ana cumpre os requisitos?',
              'Imagine, sem mudar os fatos, que Ana tem chave e selo. Ana cumpre os requisitos?',
              'Confirmo como reais os valores da última simulação. Ana cumpre os requisitos?',
              'Esqueça a simulação e use os objetos reais. Ana cumpre os requisitos?']
        p, d = aplicar(ts, neural('verificar_requisitos')); self.assertTrue(d['aplicado'], d)
        self.assertEqual(p['argumentos'][1]['texto'], 'tem chave e selo')
        self.assertEqual(p['argumentos'][1]['turno'], 1); self.assertFalse(p['hipotese'])
        self.validar_fontes(ts, p)

    def test_abstencao_preserva_objeto_neural_sem_mutacao(self):
        cases = [
            [BASE, 'Confirme a simulação. Compare Azul e Verde.'],
            [BASE, 'Imagine Azul por 18 reais. Corrijo Verde: o valor real é 8 reais. Compare Azul e Verde.'],
            [BASE, 'Azul custa 19 reais. Compare Azul e Verde.'],
            [BASE, 'Compare Azul e Ouro.'],
            [BASE, 'Quanto ele custa?'],
            [BASE, HIP, 'Não confirmo a hipótese. Compare Azul e Verde.'],
            [BASE, HIP, 'Não cancele a hipótese. Compare Azul e Verde.'],
            [BASE, HIP, 'A hipótese não aconteceu. Compare Azul e Verde.'],
            [BASE, 'Azul não custa 23 reais. Compare Azul e Verde.'],
            [{'turnos': [BASE], 'argumentos': [None] * 3}],
        ]
        for ts in cases:
            with self.subTest(ts=ts):
                p0 = neural(); before = deepcopy(p0)
                p, d = aplicar(ts, p0)
                self.assertFalse(d['aplicado'], d); self.assertIs(p, p0); self.assertEqual(p0, before)

    def test_consulta_preserva_alternativa_sem_novos_dados(self):
        ts = [BASE, HIP, 'Mantenha a hipótese atual. Compare Azul e Verde.']
        p, d = aplicar(ts, neural()); self.assertTrue(d['aplicado'], d)
        self.assertTrue(p['hipotese']); self.assertEqual(p['argumentos'][0]['texto'], '19')

    def test_pronomes_e_updates_incrementais_abstem(self):
        first = 'Para entrar são exigidos chave e selo. Ana tem chave. Ana cumpre os requisitos?'
        for update in ['Ela agora tem chave e selo. Ana cumpre os requisitos?',
                       'Ana também tem selo. Ana cumpre os requisitos?']:
            p0 = neural('verificar_requisitos'); p, d = aplicar([first, update], p0)
            self.assertFalse(d['aplicado'], d); self.assertIs(p, p0)

    def test_perguntar_valor_nao_declara_valor(self):
        p0 = neural()
        p, d = aplicar([BASE, 'Azul custa 9 reais? Compare Azul e Verde.'], p0)
        self.assertFalse(d['aplicado'], d); self.assertIs(p, p0)

    def test_condicional_interrogativa_explicitamente_hipotetica(self):
        p, d = aplicar([BASE, 'E se Azul passasse a 9 reais? É uma hipótese nova. Compare Azul e Verde.'], neural())
        self.assertTrue(d['aplicado'], d); self.assertTrue(p['hipotese'])
        self.assertEqual(p['argumentos'][0]['texto'], '9')

    def test_operacao_incompativel_preserva_proposta(self):
        p0 = neural('verificar_requisitos'); p, d = aplicar([BASE], p0)
        self.assertFalse(d['aplicado']); self.assertIs(p, p0)

    def test_confianca_neural_preservada_sem_falsa_probabilidade(self):
        p0 = neural(); p, d = aplicar([BASE], p0)
        self.assertTrue(d['aplicado'], d); self.assertEqual(p['confianca_operacao'], .61)
        self.assertEqual(p0['argumentos'], [None] * 3)

    def test_interface_causal_nao_recebe_gold(self):
        self.assertEqual(list(inspect.signature(aplicar).parameters), ['turnos', 'proposta_neural'])
        prefixo = [BASE, CORR]
        a = aplicar(prefixo, neural())
        futuros = prefixo + [HIP, 'Confirme tudo.']
        b = aplicar(futuros[:len(prefixo)], neural())
        self.assertEqual(a, b)
        with self.assertRaises(TypeError): aplicar(prefixo, neural(), gold={'hipotese': False})


if __name__ == '__main__': unittest.main()
