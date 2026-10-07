"""Função, contexto e comparação no chat ativo, sem pesos externos."""
import tempfile
import unittest
from pathlib import Path

from composicao_textual import CompositorTextual
from crivo import Crivo
from web_core import responder_web


class TestesFuncoesContextuais(unittest.TestCase):
    def test_pergunta_real_e_parafrases_selecionam_funcao(self):
        for q in ('Qual é o papel da mitocôndria dentro de uma célula?',
                  'Para que serve a mitocôndria na célula?',
                  'O que a mitocôndria faz na célula?',
                  'Qual é a utilidade da mitocôndria?'):
            with self.subTest(pergunta=q):
                b = Crivo()
                ident, texto = b.responder(q)
                self.assertEqual(ident, 'escrita:explicacao')
                self.assertIn('ATP', texto)
                self.assertIn('respiração celular', texto)
                self.assertNotIn('linhagem materna', texto)
                # A definição (respiração celular e ATP) vem primeiro; desde o
                # acervo de 2026-10-06 outra função documentada pode acompanhá-la.
                exibidos = b.contexto_textual.exibidos
                self.assertEqual(exibidos[0], ('mundo_mitocondria', 0))
                self.assertLessEqual(len(exibidos), 2)
                self.assertTrue(all(e == 'mundo_mitocondria' for e, _ in exibidos))

    def test_funcao_nao_depende_de_um_topico_ou_etiqueta(self):
        for q, esperado in (
            ('Qual é a função do ribossomo na célula?', 'proteínas'),
            ('Qual é o papel do sono na memória?', 'consolidação'),
            ('O que o DNA faz?', 'informações genéticas'),
        ):
            with self.subTest(pergunta=q):
                ident, texto = Crivo().responder(q)
                self.assertEqual(ident, 'escrita:explicacao')
                self.assertIn(esperado, texto)

    def test_qualificador_e_contexto_sem_evidencia_nao_sao_apagados(self):
        for q in ('Qual é o papel da mitocôndria numa célula fictícia?',
                  'Qual é o papel da mitocôndria no Sol?',
                  'Qual é a função da constelação?',
                  'Qual é a função da mitocôndria de extraterrestres?',
                  'Compare mitocôndria com ribossomo de extraterrestres.'):
            with self.subTest(pergunta=q):
                self.assertEqual(Crivo().responder(q)[0], 'fora')

    def test_negacao_nao_recebe_funcao_positiva(self):
        b = Crivo()
        ident, texto = b.responder('O que a mitocôndria não faz?')
        self.assertIn(ident, ('fora', 'duvida'))
        self.assertNotIn('ATP', texto)
        self.assertIsNone(b.contexto_textual)

    def test_funcao_nao_oculta_respostas_exatas_de_programacao(self):
        for q, esperado in (('para que serve um algoritmo', 'prog_algoritmo'),
                            ('para que serve uma variável', 'prog_variavel')):
            with self.subTest(pergunta=q):
                b = Crivo()
                ident, texto = b.responder(q)
                self.assertEqual(ident, esperado)
                entrada = next(e for e in b.base if e['id'] == esperado)
                self.assertIn(entrada['resposta'], texto)

    def test_comparacao_sem_ficha_de_pergunta_por_par(self):
        for q in ('Qual a diferença entre mitocôndria e ribossomo?',
                  'Compare mitocôndria com ribossomo.'):
            with self.subTest(pergunta=q):
                b = Crivo()
                ident, texto = b.responder(q)
                self.assertEqual(ident, 'escrita:comparacao')
                self.assertIn('ATP', texto)
                self.assertIn('montam proteínas', texto)
                self.assertEqual(set(b.contexto_textual.temas),
                                 {'mundo_mitocondria', 'mundo_ribossomo'})
                fontes = b.responder('Fontes')[1]
                self.assertIn('openstax.org', fontes)
                self.assertIn('genome.gov', fontes)

    def test_comparacao_preserva_antecedente_e_fontes(self):
        b = Crivo()
        ident, texto = b.responder('Qual a diferença entre clorofila e proteína?')
        self.assertEqual(ident, 'escrita:comparacao')
        self.assertIn('energia solar', texto)
        self.assertIn('reações químicas', texto)
        for e, i in b.contexto_textual.exibidos:
            self.assertIn(b.compositor.itens[e]['fatos'][i]['texto'], texto)
        proteina = b.compositor.resolver('proteína')
        self.assertIn((proteina, 0), b.contexto_textual.exibidos)

    def test_comparacao_nao_trata_alias_legado_como_ficha_individual(self):
        # A entrada antiga reúne asteroide, cometa e meteoro. Seu primeiro
        # trecho descreve asteroides, não todos os nomes que apontam para ela.
        ident, texto = Crivo().responder('Compare asteroide com cometa.')
        self.assertNotEqual(ident, 'escrita:comparacao')
        self.assertNotIn('meteoro: Asteroides', texto)

    def test_api_reconstroi_funcao_e_troca_sujeito(self):
        for geracao in (False, True):
            with self.subTest(geracao=geracao):
                r = responder_web({'message': 'E o ribossomo?',
                                   'history': ['Qual é a função da mitocôndria?']},
                                  usar_geracao=geracao)
                self.assertEqual(r['id'], 'escrita:explicacao')
                self.assertIn('proteínas', r['response'])
                self.assertNotIn('ATP', r['response'])
                self.assertIn(r['mechanism'], ('composicao_factual', 'geracao_ancorada'))
                self.assertEqual(r['generation']['usada'], r['mechanism'] == 'geracao_ancorada')
                if not geracao:
                    self.assertEqual(r['mechanism'], 'composicao_factual')
                self.assertFalse(r['has_proof'])

    def test_api_fontes_da_funcao_real(self):
        r = responder_web({'message': 'Quais fontes?',
                           'history': ['Qual é o papel da mitocôndria dentro de uma célula?']})
        self.assertEqual(r['id'], 'escrita:fontes')
        self.assertIn('openstax.org', r['response'])

    def test_nomes_ineditos_contexto_e_comparacao(self):
        # Este catálogo não contém biologia nem perguntas/respostas prontas.
        dados = {'versao': 1, 'fontes': {
            'ref': {'titulo': 'Catálogo de teste', 'url': 'https://example.org/catalogo'}},
            'itens': []}
        for ident, nome, fato in (
            ('neril', 'Neril', 'Neril filtra água no recinto.'),
            ('torvo', 'Torvo', 'Torvo transporta água no recinto.'),
            ('recinto', 'recinto', 'Recinto é um espaço fictício.'),
            ('sol', 'Sol', 'Sol é uma estrela.'),
        ):
            dados['itens'].append({'id': ident, 'nome': nome, 'fatos': [
                {'texto': fato, 'papel': 'definicao', 'fonte': 'ref'}]})
        with tempfile.TemporaryDirectory() as pasta:
            m = CompositorTextual([], Path(pasta) / 'ausente.json', lambda _: None,
                                  curriculo_mundo=dados)
            for q in ('Qual é o papel de Neril dentro do recinto?',
                      'O que Neril faz no recinto?'):
                ident, texto, ctx = m.responder(q, None)
                self.assertEqual(ident, 'escrita:explicacao')
                self.assertEqual(texto, 'Neril filtra água no recinto.')
                self.assertEqual(ctx.exibidos, (('neril', 0),))
            self.assertEqual(m.responder('Qual é o papel de Neril no Sol?', None)[0], 'fora')
            ident, texto, ctx = m.responder('Compare Neril com Torvo.', None)
            self.assertEqual(ident, 'escrita:comparacao')
            self.assertIn('filtra', texto)
            self.assertIn('transporta', texto)
            self.assertEqual(ctx.exibidos, (('neril', 0), ('torvo', 0)))


if __name__ == '__main__':
    unittest.main()
