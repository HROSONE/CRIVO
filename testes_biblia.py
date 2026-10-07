"""Conhecimento bíblico atribuído à TNM, referências e respostas verificáveis."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from curriculo_mundo import ler_curriculo
from crivo import Crivo
from scripts.catalogos.biblia import montar
from web_core import responder_web

RAIZ = Path(__file__).resolve().parent


class BibliaTNM(unittest.TestCase):
    def test_catalogo_integrado_e_reproduzivel(self):
        dados = json.loads((RAIZ / 'conhecimento_biblia.json').read_text())
        self.assertEqual(dados, montar())
        self.assertEqual(len(dados['itens']), 33)
        c = ler_curriculo(RAIZ / 'conhecimento_mundo.json')
        ids = {i['id'] for i in c['itens']}
        self.assertTrue({i['id'] for i in dados['itens']} <= ids)

    def test_fontes_oficiais_e_atribuicao_em_todos_os_fatos(self):
        d = montar()
        for f in d['fontes'].values():
            self.assertTrue(f['url'].startswith('https://www.jw.org/pt/biblioteca/biblia/biblia-de-estudo/'))
            self.assertEqual(f['tipo'], 'institucional_religiosa')
            self.assertFalse(f['reproducao_autorizada'])
            self.assertEqual(f['reutilizacao'], 'somente_referencia')
        for i in d['itens']:
            for f in i['fatos']:
                self.assertEqual(f['natureza'], 'religioso')
                self.assertIn(f['fonte'], d['fontes'])
                self.assertIn('Referência: ' + f['referencia_biblica'], f['texto'])
                self.assertTrue(any(m in f['texto'] for m in ('TNM', 'Tradução do Novo Mundo')))

    def test_nao_rotula_fonte_religiosa_como_ciencia(self):
        d = copy.deepcopy(montar())
        d['itens'][0]['fatos'][0]['natureza'] = 'cientifico'
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'biblia.json'
            p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError, 'religiosa'):
                ler_curriculo(p)

    def test_todas_as_fichas_respondem_a_definicao(self):
        b = Crivo(usar_geracao=False)
        for item in montar()['itens']:
            with self.subTest(item=item['nome']):
                ident, r = b.responder('O que é ' + item['nome'] + '?')
                self.assertEqual(ident, 'conhecimento:' + item['id'])
                self.assertIn('Referência:', r)
                self.assertNotRegex(r, r'\bé uma? na TNM\b')

    def test_pessoas_e_referencias_no_chat(self):
        for q, ident, termos in [
                ('Quem é Jeová?', 'jeova', ['Jeová', 'Salmos 83:18', 'Na TNM']),
                ('Qual é o nome de Deus?', 'jeova', ['Jeová', '83:18']),
                ('Quem foi Moisés?', 'moises', ['Jeová', 'Êxodo 3']),
                ('Quem é Jesus?', 'jesus', ['Filho', 'Pai', 'João 17']),
                ('Explique João 3:16', 'joao316', ['vida eterna', '3:16']),
                ('O que diz Salmos 83:18?', 'jeova', ['Jeová', '83:18']),
                ('O que é o Reino de Deus?', 'reino_deus', ['Mateus 6', 'TNM'])]:
            with self.subTest(q=q):
                r = responder_web({'message': q})
                self.assertEqual(r['id'], 'conhecimento:mundo_biblia_' + ident)
                self.assertFalse(r['has_proof'])
                for t in termos:
                    self.assertIn(t, r['response'])
                self.assertNotRegex(r['response'], r'\bé uma? na TNM\b')

    def test_resumo_e_fonte_correspondem_ao_trecho(self):
        h = ['Quem é Jeová?']
        resumo = responder_web({'message': 'Resuma isso', 'history': h})
        self.assertIn('Jeová', resumo['response'])
        self.assertIn('83:18', resumo['response'])
        fonte = responder_web({'message': 'Qual a fonte?', 'history': h + ['Resuma isso']})
        self.assertIn('Tradução do Novo Mundo', fonte['response'])
        self.assertIn('/salmos/83/', fonte['response'])
        self.assertNotIn('/salmos/23/', fonte['response'])

    def test_versiculo_sem_ficha_nao_inventa(self):
        for q in ['O que diz Salmos 83:19?', 'O que diz Obadias 1:8?', 'O que diz João 3:17?', 'Explique João 3:16 e Obadias 1:8',
                  'Explique João 3:16-9999', 'Explique João 3:16,18', 'Explique João 3:1600']:
            r = responder_web({'message': q})
            self.assertFalse(r['generation']['usada'])
            self.assertIn(r['id'], ('fora', 'duvida', 'leitura:aproximacao', 'social:nao_entendido'))
            self.assertIn('referência exata', r['response'])

    def test_abreviaturas_e_fonte_em_referencia_exata(self):
        r = responder_web({'message': 'Explique Sl 83:18'})
        self.assertEqual(r['id'], 'conhecimento:mundo_biblia_jeova')
        fonte = responder_web({'message': 'Qual a fonte?', 'history': ['Explique Sl 83:18']})
        self.assertIn('/salmos/83/', fonte['response'])
        for q in ['João 3:16', 'Jo3:16', 'Sl83:18']:
            r = responder_web({'message': q})
            self.assertTrue(r['id'].startswith('conhecimento:mundo_biblia_'))

    def test_multiplas_referencias_nao_respondem_somente_a_primeira(self):
        r = responder_web({'message': 'Explique João 3:16 e Sl 83:18'})
        self.assertEqual(r['id'], 'fora')
        self.assertIn('uma referência por vez', r['response'])

    def test_relato_pessoal_e_codigo_nao_sao_consulta_biblica(self):
        from referencias_biblicas import responder
        b = Crivo()
        self.assertIsNone(responder('Eu li João 3:16 hoje', b.compositor))
        self.assertIsNone(responder('Crie um poema sobre João 3:16', b.compositor))
        r = responder_web({'message': 'Corrija este código JS:\n```js\nreturn entrada - 2;\n```\nExemplos: [{"entrada":0,"saida":2}]'})
        self.assertIn('code_analysis', r)

    def test_gerador_nao_remove_atribuicao(self):
        def gerar(pergunta, fatos, **kwargs):
            return fatos[0].removeprefix('Na TNM, ')
        g = SimpleNamespace(disponivel=True, gerar=gerar)
        with patch('geracao_ancorada.geracao', return_value=g):
            b = Crivo()
            _, r = b.responder('Quem é Jeová?')
        self.assertTrue(r.startswith('Na TNM,'))
        self.assertFalse(b.ultima_geracao['usada'])
        self.assertEqual(b.ultima_geracao['motivo'], 'atribuicao_religiosa_nao_preservada')

    def test_gerador_nao_remove_referencia(self):
        g = SimpleNamespace(disponivel=True, gerar=lambda q, fs, **kw: fs[0].split(' Referência:')[0])
        with patch('geracao_ancorada.geracao', return_value=g):
            b = Crivo()
            _, r = b.responder('Quem é Jeová?')
        self.assertIn('Referência: Salmos 83:18.', r)
        self.assertFalse(b.ultima_geracao['usada'])


if __name__ == '__main__':
    unittest.main()
