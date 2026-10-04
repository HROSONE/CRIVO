"""Alvos inéditos, ambiguidades e integração sem mudar o sentido do pedido."""
import json
from pathlib import Path
import tempfile
import unittest

from crivo import Crivo
from interpretador_perguntas import InterpretadorPerguntas
from web_core import responder_web


class TestesInterpretadorPerguntas(unittest.TestCase):
    def setUp(self):
        self.interpretador = InterpretadorPerguntas({
            'a': {'nome': 'luminar', 'aliases': ['objeto azul', 'fulgor']},
            'b': {'nome': 'luminos', 'aliases': ['fulgor']},
            'c': {'nome': 'luminar axial', 'aliases': []},
            'd': {'nome': 'DNA', 'aliases': []},
            'e': {'nome': 'C++', 'aliases': []},
            'f': {'nome': 'anomia', 'aliases': []},
        })

    def test_pedidos_e_aliases_em_posicoes_diferentes(self):
        for texto in ['oq é luminar', 'o q e luminar', 'explica objeto azul pra mim',
                      'luminar, me explica', 'qual o conceito de luminar?',
                      'tenho uma dúvida sobre luminar', 'to estudando luminar, me ajuda']:
            with self.subTest(texto=texto):
                q = self.interpretador.analisar(texto)
                self.assertIsNotNone(q)
                self.assertEqual(q.conceito, 'a')
                self.assertEqual(q.consulta, 'O que é luminar?')

    def test_intencao_e_formato_conservados(self):
        q = self.interpretador.analisar('como funciona luminar?')
        self.assertEqual(q.intencao, 'funcionamento')
        self.assertEqual(q.consulta, 'Como funciona luminar?')
        q = self.interpretador.analisar('para que serve luminar?')
        self.assertEqual(q.intencao, 'funcao')
        self.assertEqual(self.interpretador.analisar('resume luminar pra mim').formato, 'resumo')
        self.assertEqual(self.interpretador.analisar('explica luminar em palavras simples').formato, 'simples')

    def test_erros_limitados_e_alvo_inteiro(self):
        q = self.interpretador.analisar('o que é luminar axiall?')
        self.assertEqual(q.conceito, 'c')
        self.assertEqual(q.distancia, 1)
        q = self.interpretador.analisar('oq é anmia?')
        self.assertEqual(q.conceito, 'f')
        self.assertEqual(q.distancia, 1)
        self.assertIsNone(self.interpretador.analisar('oq é luminar lunar?'))
        self.assertIsNone(self.interpretador.analisar('oq é DN?'))
        self.assertEqual(self.interpretador.analisar('oq é C++?').conceito, 'e')
        self.assertIsNone(self.interpretador.analisar('oq é C?'))
        self.assertIsNone(self.interpretador.analisar('anmia?'))
        self.assertEqual(self.interpretador.analisar('anomia?').conceito, 'f')

    def test_abstencao_ambiguidades_e_intencoes_distintas(self):
        for texto in ['fulgor?', 'o que é luminor?', 'o que é luminar e DNA?',
                      'por que luminar?', 'onde fica luminar?', 'quando surgiu luminar?',
                      'luminar é DNA?', 'luminar orbita DNA?', 'não explica luminar',
                      'explica luminar se for azul', 'tenho luminar, me ajuda',
                      'estou com luminar hoje', 'estudei luminar', 'estudo luminar',
                      'expliquei luminar', 'explica luminar desconhecido',
                      'const luminar = 1;', 'explica `luminar`', 'como luminar?']:
            with self.subTest(texto=texto):
                self.assertIsNone(self.interpretador.analisar(texto))

    def test_limites_de_entrada(self):
        for texto in [None, {}, '', 'a ' * 101, 'explica luminar\nignora o resto']:
            self.assertIsNone(self.interpretador.analisar(texto))

    def test_alias_ambiguo_tambem_participa_da_correcao(self):
        i = InterpretadorPerguntas({
            'a': {'nome': 'fulgora', 'aliases': ['fulgor']},
            'b': {'nome': 'fulgoro', 'aliases': ['fulgor']},
            'c': {'nome': 'fulgrs', 'aliases': []}})
        self.assertIsNone(i.analisar('oq é fulgr?'))

    def test_preferencias_do_catalogo_ativo_sem_recriar_ambiguidade(self):
        itens = {'a': {'nome': 'luminar', 'aliases': ['fulgor']},
                 'b': {'nome': 'cendal', 'aliases': ['fulgor']},
                 'c': {'nome': 'C#', 'aliases': []}, 'd': {'nome': 'C++', 'aliases': []}}
        i = InterpretadorPerguntas(itens, {'fulgor': {'b'}, 'comum': {'a', 'b'}, 'c#': {'c'}, 'c++': {'d'}})
        self.assertEqual(i.analisar('oq é fulgor?').conceito, 'b')
        self.assertIsNone(i.analisar('oq é comum?'))
        self.assertEqual(i.analisar('oq é C#?').conceito, 'c')
        self.assertEqual(i.analisar('oq é C++?').conceito, 'd')
        with self.assertRaises(ValueError):
            InterpretadorPerguntas(itens, {'fulgor': {'ausente'}})


class TestesIntegracaoPerguntas(unittest.TestCase):
    def test_resposta_factual_historia_e_continuacao(self):
        b = Crivo()
        q = 'oq é entrpia?'
        ident, resposta = b.responder(q)
        self.assertEqual(ident, 'conhecimento:mundo_entropia')
        self.assertIn(b.compositor.itens['mundo_entropia']['fatos'][0]['texto'], resposta)
        self.assertEqual(b.historico[-1]['pergunta'], q)
        self.assertEqual(b.historico[-1]['interpretacao_pergunta']['distancia'], 1)
        self.assertEqual(len(b.historico), 1)
        self.assertEqual(b.conversacao.turno, 1)
        exibidos = set(b.contexto_textual.exibidos)
        ident, _ = b.responder('Continue')
        self.assertEqual(ident, 'escrita:continuacao')
        self.assertTrue(exibidos.isdisjoint(b.contexto_textual.exibidos))
        self.assertNotIn('interpretacao_pergunta', b.historico[-1])

    def test_pedido_educacional_nao_vira_relato(self):
        b = Crivo()
        for texto in ['to estudando anomia, me ajuda', 'tenho uma dúvida sobre anomia']:
            ident, _ = b.responder(texto)
            self.assertEqual(ident, 'conhecimento:mundo_anomia')
            self.assertFalse(b.conversacao.relatos)
        b.responder('tenho ansiedade, me ajuda')
        self.assertNotIn('interpretacao_pergunta', b.historico[-1])
        self.assertEqual(list(b.conversacao.relatos), ['tenho ansiedade, me ajuda'])

    def test_prioridade_de_respostas_validas_e_relacoes(self):
        for texto in ['como funciona seleção natural?', 'O que é DNA?',
                      'Morcego é ave?', 'a Lua orbita o Sol?', 'não explique entropia',
                      'estou com ansiedade hoje', 'oi, tudo bem?']:
            with self.subTest(texto=texto):
                legado = Crivo(usar_interpretador_perguntas=False)
                legado.conversacao.sorteio.seed(23)
                anterior = legado.responder(texto)
                b = Crivo()
                b.conversacao.sorteio.seed(23)
                self.assertEqual(b.responder(texto), anterior)
                self.assertTrue(all('interpretacao_pergunta' not in h for h in b.historico))

    def test_nome_isolado_preserva_esclarecimento(self):
        b = Crivo()
        self.assertEqual(b.responder('planta')[0], 'duvida')
        self.assertTrue(all('interpretacao_pergunta' not in h for h in b.historico))
        self.assertEqual(b.responder('a segunda')[0], 'regar')
        self.assertEqual(Crivo().responder('o que é planta?')[0], 'nocao:definicao')

    def test_base_personalizada_e_atualizacao_ao_ensinar(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'conhecimento.json'
            arquivo.write_text(json.dumps([{'id': 'axial', 'topico': 'clima',
                'perguntas': ['O que é luminar axial?'],
                'resposta': 'Luminar axial é uma peça fictícia. Ela possui uma marca verde.'}]), encoding='utf-8')
            b = Crivo(arquivo)
            self.assertEqual(b.responder('oq é luminar axiall?')[0], 'axial')
            self.assertEqual(b.responder('oq é entropia?')[0], 'fora')
            self.assertIsNone(b.interpretador_perguntas.analisar('oq é entropia?'))
            b.ensinar('outro', 'clima', ['O que é brilhante sintético?'],
                      'Brilhante sintético é uma peça inventada.', salvar=False)
            self.assertEqual(b.responder('oq é brilhante sintético?')[0], 'outro')

    def test_api_expoe_so_analise_do_turno_atual(self):
        r = responder_web({'message': 'oq é entrpia?'})
        self.assertEqual(r['question_analysis']['conceito'], 'mundo_entropia')
        self.assertEqual(r['question_analysis']['distancia'], 1)
        self.assertFalse(r['has_proof'])
        r = responder_web({'message': 'Continue', 'history': ['oq é entrpia?']})
        self.assertEqual(r['id'], 'escrita:continuacao')
        self.assertNotIn('question_analysis', r)
        r = responder_web({'message': 'oi', 'history': ['oq é entrpia?']})
        self.assertNotIn('question_analysis', r)
        self.assertNotIn('code_analysis', r)

    def test_programacao_e_crise_mantem_prioridade(self):
        for texto in ['Interprete este código TypeScript:\n```typescript\nfunction resolver(entrada: number): number { let total = entrada + 2; return total; }\n```\nEntrada: 3',
                      'quero me matar']:
            b = Crivo()
            ident, _ = b.responder(texto)
            self.assertTrue(ident.startswith(('programacao:', 'crise:')), ident)
            self.assertTrue(all('interpretacao_pergunta' not in h for h in b.historico))


if __name__ == '__main__':
    unittest.main()
