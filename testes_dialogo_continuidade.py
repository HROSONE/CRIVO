"""Contratos de continuidade com companhia e fronteiras factuais."""
import gzip
import json
import re
import unittest
from pathlib import Path
from crivo import Crivo
from conversa_dialogo import aprovacao_valida, conferir
from linguagem_gerativa import GeradorGRU
H=Path(__file__).parent/'experimentos/dialogo_continuidade_20261010'

class TestesDialogoContinuidade(unittest.TestCase):
    def bot(self):return Crivo(checkpoint_dialogo_candidato=str(H/'checkpoint_gru_dialogo.json.gz'))

    def test_amigo_sem_lugar_conserva_papel_apos_duas_continuacoes_e_reescrita(self):
        b=self.bot()
        for t in ['Conte uma aventura sobre uma jaguatirica ceramista.',
                  'Mude o final: ela encontra uma aliada.',
                  'Continue depois desse final.','Continue a história mais uma vez.',
                  'Reescreva essa história em cinco frases.']:
            _,r=b.responder(t)
            self.assertTrue(b.dialogo_conversa.trace['usada'],(t,r,b.dialogo_conversa.trace))
            self.assertIn('jaguatirica ceramista',r)
        self.assertIn('uma aliada',r)
        self.assertNotIn('em uma aliada',r)
        self.assertEqual({'tema1':'uma jaguatirica ceramista','detalhe':'uma aliada'},b.conversacao.geracao.ultima_escrita['slots'])
        self.assertEqual(5,len(re.findall(r'[^.!?]+[.!?](?:\s|$)',r)))

    def test_cenario_personagem_e_companhia_nao_trocam_de_papel(self):
        b=self.bot()
        for t in ['Conte uma história sobre um ouriço mensageiro em um castelo antigo.',
                  'Mude o final: ele encontra uma guia.','Continue depois desse final.',
                  'Continue a história mais uma vez.','Reescreva essa história em cinco frases.']:
            _,r=b.responder(t)
            self.assertTrue(b.dialogo_conversa.trace['usada'],(t,r,b.dialogo_conversa.trace))
            self.assertIn('ouriço mensageiro',r);self.assertIn('castelo antigo',r)
        self.assertIn('uma guia',r);self.assertNotIn('em uma guia',r)
        self.assertEqual('um castelo antigo',b.conversacao.geracao.ultima_escrita['slots']['tema2'])
        self.assertEqual('uma guia',b.conversacao.geracao.ultima_escrita['slots']['detalhe'])

    def test_nova_correcao_substitui_companhia_sem_torna_la_cenario(self):
        b=self.bot();b.responder('Conte uma aventura sobre uma jaguatirica ceramista.')
        b.responder('Mude o final: ela encontra uma aliada.')
        _,r=b.responder('Mude o final: ela encontra uma guia.')
        self.assertTrue(b.dialogo_conversa.trace['usada'],(r,b.dialogo_conversa.trace))
        self.assertIn('uma guia',r);self.assertNotIn('uma aliada',r)
        self.assertNotIn('tema2',b.conversacao.geracao.ultima_escrita['slots'])

    def test_nova_cena_avanca_e_reescrita_preserva_a_cena_mais_recente(self):
        b=self.bot();b.responder('Conte uma aventura sobre uma jaguatirica ceramista.')
        b.responder('Mude o final: ela encontra uma aliada.')
        _,primeira=b.responder('Continue depois desse final.')
        _,segunda=b.responder('Continue a história mais uma vez.')
        self.assertNotEqual(primeira,segunda)
        self.assertIn('uma aliada',segunda)
        _,reescrita=b.responder('Reescreva essa história em cinco frases.')
        self.assertEqual(segunda,reescrita)

    def test_referente_natural_e_restricao_nao_criam_personagem_literal_ou_cancelam(self):
        b=self.bot();b.responder('Conte uma aventura sobre uma seriema escultora.')
        _,r=b.responder('Quero uma história com essa personagem.')
        self.assertIn('seriema escultora',r);self.assertNotIn('história de essa personagem',r)
        _,r=b.responder('Não invente um nome para a personagem.')
        self.assertNotIn('cancelado',r)
        _,r=b.responder('Não escreva a história.')
        self.assertIn('cancelado',r)

    def test_ficcao_nao_polui_memoria_e_nova_pergunta_factual_nao_vira_historia(self):
        b=self.bot();antes=list(b.memoria_sessao.afirmacoes)
        b.responder('Conte uma aventura sobre uma seriema escultora.')
        b.responder('Mude o final: ela encontra uma aliada.')
        b.responder('Continue depois desse final.')
        self.assertEqual(antes,b.memoria_sessao.afirmacoes)
        ident,r=b.responder('O que é diferença de potencial?')
        self.assertTrue(ident.startswith('conhecimento:'));self.assertFalse(b.dialogo_conversa.trace['usada'])
        self.assertNotIn('seriema',r)
        outro=self.bot();ident,r=outro.responder('Continue depois desse final.')
        self.assertFalse(outro.dialogo_conversa.trace['usada'])
        self.assertIsNone(outro.conversacao.geracao.ultima_escrita)

    def test_oito_arcos_e_papeis_sem_contaminacao_da_sessao(self):
        d=json.loads(gzip.decompress((H/'checkpoint_gru_dialogo.json.gz').read_bytes()))
        self.assertEqual({'aprovado':False,'ativo_no_chat':False},d['controle'])
        self.assertFalse(aprovacao_valida(d));self.assertEqual(85581,d['treino']['parametros'])
        m=GeradorGRU(d)
        for v in range(8):
            for lugar in (False,True):
                slots={'tema1':'uma seriema escultora','detalhe':'uma aliada'}
                if lugar:slots['tema2']='um castelo antigo'
                ctx=dict(acao='continuacao',slots=slots,estilo='neutro',variante=v,mensagem='',historico=[])
                g=m.gerar(ctx);r,q=conferir(g,ctx,set(m.vocabulario),5)
                self.assertTrue(q['aceita'],(v,lugar,q,r))
                self.assertIn('com uma aliada',r)
                _,q=conferir(dict(g,tokens=g['tokens']+['Maria','42']),ctx,set(m.vocabulario));self.assertFalse(q['aceita'])
        corpus=json.loads((H/'corpus_gru.json').read_text());splits={}
        for e in corpus['exemplos']:splits.setdefault(e['dialogo'],set()).add(e['split'])
        self.assertTrue(all(len(s)==1 for s in splits.values()))
        casos=json.loads((H/'casos_congelados.json').read_text())['casos']
        old=json.loads((H.parent/'dialogo_v2_20261010/casos_congelados.json').read_text())['casos']
        self.assertEqual(old,casos[:43])

if __name__=='__main__':unittest.main()
