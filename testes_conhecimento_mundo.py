"""Currículo, proveniência, relações completas e integração com a rede original."""
import copy
import fnmatch
import json
import tempfile
import unittest
from pathlib import Path

from avaliar_mundo import CASOS, avaliar
from composicao_textual import CompositorTextual
from crivo import Crivo, PASTA
from curriculo_mundo import carregar_base, entradas_mundo, ler_curriculo
from rede_neural import RedeCrivo, treinar_base
from web_core import responder_web


class TestesConhecimentoMundo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculo = ler_curriculo(PASTA / 'conhecimento_mundo.json')

    def test_sonda_publica_separada_do_treino(self):
        resultado = avaliar()
        self.assertEqual(resultado['acertos'], resultado['total'],
                         [r for r in resultado['casos'] if not r['passou']])
        exemplos = {q.lower().strip(' .?!') for e in entradas_mundo(self.curriculo)
                    for q in e['perguntas']}
        self.assertFalse(exemplos & {c[1].lower().strip(' .?!') for c in CASOS})

    def test_todo_conceito_tem_definicao_e_fontes_cientificas(self):
        for item in self.curriculo['itens']:
            with self.subTest(conceito=item['nome']):
                self.assertEqual(item['fatos'][0]['papel'], 'definicao')
                for fato in item['fatos']:
                    # Filosofia e sociologia não são ciência natural: têm natureza própria.
                    proprias = {'filosofia': ('filosofico',), 'sociologia': ('social',)}.get(item['area'], ())
                    self.assertIn(fato['natureza'], ('cientifico', 'psicologico', 'orientacao') + proprias)
                    for fonte in [fato['fonte']] + fato.get('fontes', []):
                        self.assertIn(fonte, self.curriculo['fontes'])
                        metadata = self.curriculo['fontes'][fonte]
                        self.assertIn(metadata['tipo'], ('institucional_cientifica', 'artigo_cientifico', 'catalogo_tecnico'))
                        self.assertTrue(metadata['credito'])
                        self.assertTrue(metadata['direitos_url'].startswith('https://'))
                        self.assertIn(metadata['reutilizacao'],
                                      ('dominio_publico', 'CC-BY-4.0', 'permissao_institucional',
                                       'somente_referencia'))
                        if metadata['reutilizacao'] == 'somente_referencia':
                            self.assertIs(metadata.get('reproducao_autorizada'), False)

    def test_fontes_correspondem_ao_fato_da_relacao(self):
        b = Crivo()
        b.responder('Como o sono contribui para a memória?')
        _, texto = b.responder('Fontes')
        self.assertIn('/why-sleep-important', texto)
        self.assertNotIn('/stages-of-sleep', texto)
        self.assertNotIn('nimh.nih.gov', texto)

    def test_apenas_ciencia_com_credito_e_sem_causalidade_inventada(self):
        b = Crivo()
        _, ciencia = b.responder('O que é biomimética?')
        self.assertNotIn('Criador', ciencia)
        _, fonte = b.responder('Fontes')
        self.assertIn('nist.gov', fonte)
        b.responder('Como a procrastinação se associa ao estresse?')
        _, fonte = b.responder('Fontes')
        self.assertIn('Beutel ME', fonte)
        self.assertIn('10.1371/journal.pone.0148054', fonte)
        self.assertEqual(b.responder('Por que a procrastinação pode aumentar o estresse?')[0], 'fora')

    def test_classificacao_atual_do_sono_com_fonte_cientifica(self):
        b = Crivo()
        _, atual = b.responder('Como funciona o sono NREM?')
        self.assertIn('três estágios', atual)
        self.assertNotIn('quatro', atual)
        _, fontes = b.responder('Fontes')
        self.assertIn('nhlbi.nih.gov', fontes)
        _, explicacao = b.responder('O que é sono NREM?')
        self.assertIn('três', explicacao)
        self.assertNotIn('quatro', explicacao)

    def test_relacoes_nao_descartam_negacao_qualificadores_ou_direcao(self):
        for q in ['O sono não ajuda a memória?', 'O sono ajuda a memória de extraterrestres?',
                  'Por que a memória ajuda o sono?', 'Por que toda procrastinação cura o estresse?',
                  'Como ansiedade social causa depressão?', 'O hipocampo consolida toda memória perfeitamente?']:
            with self.subTest(pergunta=q):
                b = Crivo()
                self.assertEqual(b.responder(q)[0], 'fora')
                self.assertIsNone(b.contexto_textual)

    def test_detalhe_nao_cadastrado_nao_vira_definicao_aproximada(self):
        for q in ['Qual é a função da constelação?', 'Como funciona a memória declarativa?',
                  'Dê um exemplo de melatonina.']:
            with self.subTest(pergunta=q):
                self.assertEqual(Crivo().responder(q)[0], 'fora')

    def test_limites_de_saude_individual(self):
        for q in ['Diagnostique minha depressão.', 'Qual medicamento usar para ansiedade?',
                  'Qual dose de melatonina uma criança precisa?',
                  'Tenho tristeza, estou com depressão?']:
            with self.subTest(pergunta=q):
                self.assertEqual(Crivo().responder(q)[0], 'fora')

    def test_api_reconstroi_funcao_e_proveniencia(self):
        r = responder_web({'message': 'Qual é a fonte?',
                           'history': ['Como funciona a adesão da lagartixa?']})
        self.assertEqual(r['id'], 'escrita:fontes')
        self.assertIn('nist.gov/news-events/news/2022/07/', r['response'])
        self.assertEqual(r['mechanism'], 'composicao_factual')
        self.assertFalse(r['has_proof'])

    def test_ensinar_salva_so_base_editorial_e_recarrega_curriculo(self):
        base = (PASTA / 'conhecimento.json').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / 'conhecimento.json'
            arq.write_text(base, encoding='utf-8')
            (Path(pasta) / 'conhecimento_mundo.json').write_text(
                json.dumps(self.curriculo), encoding='utf-8')
            b = Crivo(arq)
            b.ensinar('objeto_ficticio', 'mundo', ['o que é objeto fictício'], 'É um exemplo fictício.')
            persistido = json.loads(arq.read_text(encoding='utf-8'))
            self.assertFalse(any(e.get('origem_curriculo') == 'mundo' for e in persistido))
            novo = Crivo(arq)
            self.assertEqual(len(novo.base), len(b.base))
            self.assertEqual(novo.responder('O que é sinapse?')[0], 'conhecimento:mundo_sinapse')
            self.assertEqual(novo.responder('O que é objeto fictício?')[0], 'objeto_ficticio')

    def test_base_temporaria_nao_herda_curriculo_global(self):
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / 'base.json'
            arq.write_text(json.dumps([{'id': 'teste', 'topico': 'clima',
                'perguntas': ['o que é zunto'], 'resposta': 'Zunto é um exemplo fictício.'}]), encoding='utf-8')
            b = Crivo(arq)
            self.assertIsNone(b.curriculo_mundo)
            self.assertEqual(b.responder('O que é hipocampo?')[0], 'fora')

    def test_mesma_populacao_no_bot_e_na_rede(self):
        base = carregar_base(PASTA / 'conhecimento.json')
        bot = Crivo()
        self.assertEqual(base, bot.base)
        self.assertEqual({e['id'] for e in base if e.get('origem_curriculo') == 'mundo'},
                         bot.compositor.mundo_ids)

    def test_api_inclui_curriculo_modulos_e_checkpoint_no_pacote(self):
        config = json.loads((PASTA / 'vercel.json').read_text(encoding='utf-8'))
        padrao = config['functions']['api/chat.py']['includeFiles']
        padroes = padrao.strip('{}').split(',')
        for nome in ('conhecimento_mundo.json', 'curriculo_mundo.py',
                     'composicao_textual.py', 'rede_neural.py', 'rede_crivo.json'):
            with self.subTest(arquivo=nome):
                self.assertTrue((PASTA / nome).is_file())
                self.assertTrue(any(fnmatch.fnmatchcase(nome, p) for p in padroes))

    def test_curriculo_malformado_e_rejeitado(self):
        mutacoes = [
            lambda d: d['itens'][0].update(id=[]),
            lambda d: d['itens'][0].update(fatos=['inválido']),
            lambda d: d['itens'][0]['fatos'][0].update(fonte=[]),
            lambda d: d['itens'][0]['fatos'][0].update(natureza='cientifico_sem_fonte'),
            lambda d: d['itens'][0]['fatos'][0].update(fontes=['ausente']),
            lambda d: d['itens'].append(copy.deepcopy(d['itens'][0])),
            lambda d: d['fontes']['nci_cerebro'].update(tipo='fonte_nao_cientifica'),
            lambda d: d['fontes']['nci_cerebro'].update(url='http://example.org'),
            lambda d: d['fontes']['nci_cerebro'].update(reutilizacao='desconhecida'),
            lambda d: d['fontes']['nci_cerebro'].update(reutilizacao=[]),
            lambda d: d['fontes']['nci_cerebro'].update(direitos_url=''),
            lambda d: d['fontes']['nci_cerebro'].update(credito=''),
            lambda d: d['itens'][0]['fatos'][0].update(natureza='religioso'),
            lambda d: d['ligacoes'][0].update(destino='mundo_ausente'),
            lambda d: d['ligacoes'][0].update(origem=[]),
            lambda d: d['ligacoes'][0].update(indice_fato=999),
            lambda d: d['comparacoes'][0].update(indice_fato=True),
        ]
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / 'curriculo.json'
            for mutar in mutacoes:
                d = copy.deepcopy(self.curriculo)
                mutar(d)
                arq.write_text(json.dumps(d), encoding='utf-8')
                with self.assertRaises(ValueError):
                    ler_curriculo(arq)

    def test_rejeita_curriculo_duplicado_na_base_editorial(self):
        base = carregar_base(PASTA / 'conhecimento.json')
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / 'base.json'
            arq.write_text(json.dumps(base), encoding='utf-8')
            with self.assertRaises(ValueError):
                carregar_base(arq, self.curriculo)

    def test_mesmo_motor_para_conceitos_ineditos_e_rede_offline(self):
        # Nomes e relação artificiais: não existe regra para estes temas no código.
        dados = dict(versao=1, fontes={'teste': self.curriculo['fontes']['nci_cerebro']},
            itens=[dict(id='mundo_zunto', nome='zunto', area='ficcao', aliases=['zuntos'],
                fatos=[dict(texto='Zunto é um objeto fictício.', papel='definicao', natureza='cientifico', fonte='teste'),
                       dict(texto='Zunto aciona torva no exemplo fictício.', papel='detalhe', natureza='cientifico', fonte='teste', aspecto='funcao')]),
                   dict(id='mundo_torva', nome='torva', area='ficcao', aliases=[],
                fatos=[dict(texto='Torva é uma peça fictícia.', papel='definicao', natureza='cientifico', fonte='teste')])],
            ligacoes=[dict(origem='mundo_zunto', destino='mundo_torva', indice_fato=1, verbos=['aciona'])])
        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta) / 'conhecimento.json'
            base.write_text(json.dumps([dict(id='oi', topico='saudacao', perguntas=['oi'], resposta='Olá.')]), encoding='utf-8')
            arq = base.with_name('conhecimento_mundo.json')
            arq.write_text(json.dumps(dados), encoding='utf-8')
            self.assertEqual(Crivo(base).responder('Como zunto aciona torva?')[0], 'escrita:relacao')
            self.assertEqual(Crivo(base).responder('Como torva aciona zunto?')[0], 'fora')
            self.assertEqual(Crivo(base).responder('Para que serve zunto?')[0], 'escrita:explicacao')
            pesos = base.with_name('rede_crivo.json')
            treinar_base(base, pesos, epocas=2, ocultos=4, dimensao=32, modo='portugues')
            rede = RedeCrivo.carregar(pesos)
            self.assertEqual(set(rede.rotulos), {'oi', 'mundo_zunto', 'mundo_torva'})
            b = Crivo(base)
            self.assertIsNotNone(b.rede, b.erro_rede)
            self.assertIsNone(b.erro_rede)
            self.assertEqual(b.responder('Como zunto aciona torva?')[0], 'escrita:relacao')
            # Mudar exemplos invalida os pesos anteriores, sem impedir os fatos.
            dados['itens'][0]['aliases'].append('zutano')
            arq.write_text(json.dumps(dados), encoding='utf-8')
            b = Crivo(base)
            self.assertIsNone(b.rede)
            self.assertIsNotNone(b.erro_rede)
            self.assertEqual(b.responder('O que é zutano?')[0], 'conhecimento:mundo_zunto')


if __name__ == '__main__':
    unittest.main()
