"""Contratos de orçamento, retração e isolamento das extensões estruturais."""
import json
import unittest
from unittest.mock import patch

from correcao_relatos import corrigir_relatos
from interpretacao_estruturas import executar
from programacao_chat import MotorCodigoChat
from sintese_composta import buscar_composta


class SinteseCompostaTestes(unittest.TestCase):
    def test_orcamento_total_e_compatibilidade_com_busca_inicial(self):
        casos = [dict(entrada=0, saida=1), dict(entrada=2, saida=7)]
        m = MotorCodigoChat()
        m.responder(json.dumps(dict(acao='gerar', desenvolvimento=casos)))
        self.assertTrue(m.ultimo['atende_desenvolvimento'])
        self.assertEqual(executar(m.ultimo['corpo'], -5)['resultado'], -14)
        self.assertLessEqual(m.ultimo['verificadas'], 1000)
        self.assertFalse(m.ultimo['casos_reservados_consultados'])
        with patch('programacao_chat.buscar_composta', side_effect=AssertionError('Mudou baseline')):
            m.responder(json.dumps(dict(acao='gerar', desenvolvimento=[dict(entrada=0,saida=2),dict(entrada=3,saida=5)])))
        self.assertEqual(m.ultimo['origem'], 'baseline_v3')

    def test_orcamento_esgotado_nao_inicia_fallback(self):
        r = dict(corpo=None, codigo=None, verificadas=1000, atende_desenvolvimento=False)
        with patch('programacao_chat.buscar', return_value=r), patch(
                'programacao_chat.buscar_composta', side_effect=AssertionError('Excedeu orçamento')):
            m = MotorCodigoChat()
            m.responder(json.dumps(dict(acao='gerar',desenvolvimento=[dict(entrada=1,saida=5)])))
            self.assertEqual(m.ultimo['verificadas'], 1000)
        self.assertEqual(buscar_composta([dict(entrada=1,saida=5)], 'numero', 0)['verificadas'], 0)

    def test_reducao_negativos_vazio_e_entrada_preservada(self):
        casos = [dict(entrada=[-3,-8,-5],saida=-3), dict(entrada=[],saida=None)]
        r = buscar_composta(casos, 'array', 2)
        self.assertTrue(r['atende_desenvolvimento'])
        entrada = [-9,-4,-18]
        e = executar(r['corpo'], entrada)
        self.assertEqual(e['resultado'], -4)
        self.assertEqual(e['estado']['entrada'], entrada)
        self.assertEqual(entrada, [-9,-4,-18])

    def test_gramatica_incompativel_abstem_sem_falsa_correcao(self):
        r = buscar_composta([dict(entrada=1,saida='um')], 'numero', 1000)
        self.assertFalse(r['atende_desenvolvimento'])
        self.assertIsNone(r['corpo'])
        self.assertLessEqual(r['verificadas'], 1000)
        from scripts.experimento_diagnostico import congelada
        self.assertTrue(congelada())


class CorrecaoRelatosTestes(unittest.TestCase):
    def test_preserva_clausula_independente_e_nao_edita_fonte(self):
        fonte = ['Meu nome é Lora, e meu projeto se chama Flume']
        r = corrigir_relatos('Corrigindo, Flume é minha oficina, eu escrevi errado', fonte)
        self.assertEqual(r[0], 'Meu nome é Lora')
        self.assertNotIn('projeto', ' '.join(r))
        self.assertEqual(fonte, ['Meu nome é Lora, e meu projeto se chama Flume'])
        r2 = corrigir_relatos('Quer dizer, Flume é minha escola', r)
        self.assertNotIn('oficina', ' '.join(r2))

    def test_citacao_hipotese_negacao_sem_referencia_e_ambiguidade(self):
        original = ['Meu projeto se chama Flume']
        for t in ('Se Flume é minha oficina', 'Corrigindo, Flume é minha oficina?',
                  'Corrigindo, "Flume é minha oficina"', 'Corrigindo, Flume não é minha oficina',
                  'Corrigindo, Outro é minha oficina'):
            with self.subTest(texto=t):
                self.assertIsNone(corrigir_relatos(t, original))
        t = 'Corrigindo, Flume é minha oficina'
        for relatos in (original*2, ['Meu projeto não se chama Flume'],
                        ['Se meu projeto se chama Flume'], ['Meu amigo disse "meu projeto se chama Flume"']):
            self.assertIsNone(corrigir_relatos(t, relatos))

    def test_snapshot_retomada_tambem_retrata_relacao(self):
        from linguagem_conversa import Conversacao
        c = Conversacao(usar_neural=False)
        c.relatos.append('Meu cachorro se chama Brisa')
        c.situacoes.append(('relato', None, tuple(c.relatos), 1, 1))
        c.dialogo.preparar_memoria_explicita('Corrigindo, Brisa é meu gato', c)
        self.assertNotIn('cachorro', ' '.join(c.situacoes[0][2]))
        self.assertIn('gato', ' '.join(c.situacoes[0][2]))

    def test_http_replay_correcao_reset_e_historico_fonte(self):
        from web_core import responder_web
        mensagens = ['Meu cachorro se chama Brisa', 'Corrigindo, Brisa é meu gato']
        r = responder_web(dict(message='O que eu contei mesmo?', history=mensagens))
        texto = r['response'].lower()
        self.assertIn('gato', texto)
        self.assertNotIn('cachorro', texto)
        self.assertEqual(mensagens[0], 'Meu cachorro se chama Brisa')
        r = responder_web(dict(message='Do que eu queria cuidar mesmo?', history=[
            'Quero cuidar da minha horta', 'Agora esqueça tudo que eu contei aqui']))
        self.assertIn('conversa', r['response'].lower())
        self.assertNotIn('suculenta', r['response'].lower())
        self.assertNotIn('horta', r['response'].lower())


if __name__ == '__main__':
    unittest.main()
