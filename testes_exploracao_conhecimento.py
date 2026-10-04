"""Evidências preservadas, associações sem causalidade e diversidade limitada."""
import unittest
from types import SimpleNamespace

from crivo import Crivo
from evidencias_conversa import IndiceEvidencias
from exploracao_conhecimento import ExploradorConhecimento
from web_core import responder_web


class TestesExploracao(unittest.TestCase):
    def setUp(self):
        self.bot = Crivo()

    def test_propostas_com_fontes_e_trechos_inteiros(self):
        self.bot.responder('Explore ideias sobre sono')
        dados = self.bot.historico[-1]['exploracao_conhecimento']
        self.assertEqual(dados['status'], 'propostas')
        self.assertEqual(len(dados['propostas']), 3)
        self.assertEqual(len({p['tipo'] for p in dados['propostas']}), 3)
        for p in dados['propostas']:
            self.assertFalse(p['comprovada_no_mundo'])
            self.assertTrue(p['evidencias'])
            for e in p['evidencias']:
                self.assertEqual(e['texto'], self.bot.compositor.itens[e['assunto']]['fatos'][e['indice']]['texto'])
                self.assertTrue(e['fontes'])
        _, texto = self.bot.responder('Quais fontes?')
        urls = [f['url'] for p in dados['propostas'] for e in p['evidencias'] for f in e['fontes']]
        self.assertTrue(any(u in texto for u in urls))
        self.assertNotIn('exploracao_conhecimento', self.bot.historico[-1])

    def test_mais_ideias_sem_repeticao_com_limite(self):
        chaves = set()
        for i in range(7):
            self.bot.responder('Explore ideias sobre sono' if i == 0 else 'Mais ideias')
            dados = self.bot.historico[-1]['exploracao_conhecimento']
            novas = {p['chave'] for p in dados['propostas']}
            self.assertTrue(novas.isdisjoint(chaves))
            chaves.update(novas)
            self.assertLessEqual(len(chaves), 12)
            self.assertLessEqual(len(novas), 3)
        self.assertEqual(dados['status'], 'esgotado')

    def test_replay_web_fontes_sem_marcar_proposta_como_prova(self):
        r = responder_web({'message': 'Mais ideias', 'history': ['Explore ideias sobre sono']})
        self.assertEqual(r['mechanism'], 'exploracao_conhecimento')
        self.assertFalse(r['has_proof'])
        self.assertTrue(r['knowledge_exploration']['propostas'])
        oi = responder_web({'message': 'Oi', 'history': ['Explore ideias sobre sono']})
        self.assertNotIn('knowledge_exploration', oi)

    def test_dois_alvos_somente_ligacoes_desses_alvos(self):
        self.bot.responder('Explore ideias sobre sono e ritmo circadiano')
        dados = self.bot.historico[-1]['exploracao_conhecimento']
        self.assertEqual(len(dados['temas']), 2)
        for p in dados['propostas']:
            self.assertTrue({e['assunto'] for e in p['evidencias']} <= set(dados['temas']))
        self.assertTrue(dados['propostas'])

    def test_qualificadores_negacao_e_alvo_desconhecido_nao_sao_apagados(self):
        for mensagem in ['Explore ideias sobre sono lunar', 'Explore ideias sobre planeta inexistente',
                         'Explore ideias sobre não sono', 'Explore ideias sobre sono e algo que não sei']:
            self.bot.responder(mensagem)
            dados = self.bot.historico[-1]['exploracao_conhecimento']
            self.assertEqual(dados['status'], 'nao_resolvido')
            self.assertFalse(dados['propostas'])
        self.assertIsNone(ExploradorConhecimento().preparar('não explore ideias sobre sono', self.bot, 1))

    def test_sessao_expira_e_reinicio_limpa(self):
        self.bot.responder('Explore ideias sobre sono')
        e = self.bot.conversacao.explorador
        e.preparar('Mais ideias', self.bot, e.turno + 11)
        self.assertEqual(e.ultimo['status'], 'sem_tema')
        self.bot.responder('Explore ideias sobre sono')
        self.bot.responder('vamos começar de novo')
        self.assertFalse(e.ids)

    def test_associacao_lexical_preserva_limites_sem_inventar_relacao(self):
        class Catalogo:
            itens = {
                'a': {'nome': 'luminar', 'fatos': [{'texto': 'O efeito luminar pode apresentar cintilação em certas condições.', 'fontes': ['f']}]},
                'b': {'nome': 'cendal', 'fatos': [{'texto': 'A cintilação cendal não implica aquecimento.', 'fontes': ['f']}]},
                'c': {'nome': 'azur', 'fatos': [{'texto': 'Cintilação sem fonte.', 'fontes': []}]}}
            fontes = {'f': {'titulo': 'Fonte de teste', 'url': 'https://example.org/fonte'}}
            aliases = {'fulgor': {'a', 'b'}, 'luminar': {'a'}, 'cendal': {'b'}}
            ligacoes_mundo = comparacoes_mundo = []
            def resolver(self, texto):
                ids = self.aliases.get(texto, set())
                return next(iter(ids)) if len(ids) == 1 else None
        comp = Catalogo()
        bot = SimpleNamespace(compositor=comp, planejador=SimpleNamespace(indice=IndiceEvidencias(comp)))
        explorador = ExploradorConhecimento()
        resultado = explorador.preparar('Explore ideias sobre luminar', bot, 1)
        associados = [p for p in explorador.ultimo['propostas'] if p['tipo'] == 'associacao_lexical']
        self.assertEqual(len(associados), 1)
        self.assertIn('sem provar relação ou causalidade', associados[0]['apoio'])
        self.assertIn('pode apresentar', resultado[1])
        self.assertIn('não implica aquecimento', resultado[1])
        self.assertTrue(all(e['assunto'] != 'c' for p in explorador.ultimo['propostas'] for e in p['evidencias']))
        explorador.preparar('Explore ideias sobre fulgor', bot, 2)
        self.assertEqual(explorador.ultimo['status'], 'nao_resolvido')
