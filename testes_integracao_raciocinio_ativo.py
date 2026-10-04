"""Contrato de conversa, prioridades e hipóteses sem contaminar o acervo."""
import json
from pathlib import Path
import unittest

from crivo import Crivo
from web_core import responder_web


class TestesIntegracaoRaciocinioAtivo(unittest.TestCase):
    def test_casos_frozen_atravessam_api_e_replay(self):
        casos = json.loads((Path(__file__).parent / 'avaliacoes/raciocinio_ativo_v1/dev.json').read_text())['casos']
        for c in casos:
            with self.subTest(c=c['id']):
                r = responder_web({'message': c['message'], 'history': c['history']})
                self.assertEqual(r['mechanism'], 'raciocinio_ativo')
                self.assertFalse(r['has_proof'])
                d = r['reasoning']
                self.assertFalse(d['comprovado_no_mundo'])
                self.assertEqual(d['origem'], 'premissas_da_sessao')
                if 'status' in c:
                    self.assertEqual(d['status'], c['status'])
                if 'operation' in c:
                    self.assertEqual(d['operacao'], c['operation'])
                if 'assumption' in c:
                    self.assertTrue(any(l['texto'] == c['assumption'] for p in d['propostas'] for l in p['suposicoes']))

    def test_conhecimento_curado_continua_factual(self):
        r = responder_web({'message': 'Posso concluir que pinguim é um ser vivo?'})
        self.assertEqual(r['id'], 'logica:tipo_de')
        self.assertTrue(r['has_proof'])
        self.assertNotIn('reasoning', r)

    def test_prioridade_crise_codigo_e_ausencia_de_rastro_antigo(self):
        historia = ['Considere estas premissas: chove; se chove, então a rua molha']
        for pergunta in ['Oi', 'O que é DNA?', 'não explique DNA', 'quero me matar', 'Analise este JavaScript:\n```js\nconst x = 1;\n```']:
            with self.subTest(pergunta=pergunta):
                r = responder_web({'message': pergunta, 'history': historia})
                self.assertNotIn('reasoning', r)
                self.assertNotIn('knowledge_exploration', r)

    def test_hipotese_nao_altera_grafo_curriculo_ou_memoria(self):
        b = Crivo()
        original = json.dumps(b.curriculo_mundo, sort_keys=True)
        grafo = repr(b.raciocinio.arestas)
        b.responder('Considere estas premissas: chove; se chove, então a rua molha')
        b.responder('Que hipóteses você sugere?')
        self.assertEqual(json.dumps(b.curriculo_mundo, sort_keys=True), original)
        self.assertEqual(repr(b.raciocinio.arestas), grafo)
        self.assertFalse(b.conversacao.relatos)
        b.responder('vamos começar de novo')
        b.responder('Posso concluir que a rua molha?')
        self.assertEqual(b.historico[-1]['raciocinio_ativo']['status'], 'sem_premissas')

    def test_hipotese_antiga_e_pergunta_condicional_comum_preservadas(self):
        b = Crivo()
        i, resposta = b.responder('Suponha que todo flumbo é blim e todo blim é taro. Então flumbo é taro?')
        self.assertEqual(i, 'conversa:hipotese')
        self.assertIn('flumbo', resposta)
        self.assertNotIn('raciocinio_ativo', b.historico[-1])
        b.responder('Suponha que todo flumbo é blim e todo blim é taro')
        i, _ = b.responder('Então flumbo é taro?')
        self.assertEqual(i, 'conversa:hipotese')
        self.assertNotIn('raciocinio_ativo', b.historico[-1])
        b.responder('E se eu estudar Python?')
        self.assertNotIn('raciocinio_ativo', b.historico[-1])
