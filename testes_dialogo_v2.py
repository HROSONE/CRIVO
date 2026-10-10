"""Regressões públicas e fronteiras de intenção/dados no segundo treino."""
import gzip
import json
import unittest
from pathlib import Path

from crivo import Crivo
from conversa_dialogo import conferir
from linguagem_gerativa import GeradorGRU

H=Path(__file__).parent/'experimentos/dialogo_v2_20261010'

class TestesDialogoV2(unittest.TestCase):
    def bot(self):return Crivo(checkpoint_dialogo_candidato=str(H/'checkpoint_gru_dialogo.json.gz'))

    def test_escolha_apos_ambiguidade_preserva_campo_polaridade_e_fontes(self):
        b=self.bot()
        b.responder('Minha amiga Nuvéria não gosta de inhame. Minha amiga Fadrélia não gosta de quiabo.')
        b.responder('Do que ela não gosta?')
        n=len(b.memoria_sessao.afirmacoes)
        _,r=b.responder('Estou falando de Fadrélia.')
        self.assertIn('Fadrélia não gosta de quiabo',r)
        self.assertEqual(n,len(b.memoria_sessao.afirmacoes))
        self.assertFalse(b.dialogo_conversa.trace['usada'])

    def test_nome_desconhecido_nao_vira_nova_pessoa_e_mudanca_para_fato_e_respeitada(self):
        b=self.bot()
        b.responder('Meu primo Navrino gosta de pequi. Meu primo Tovrino gosta de pinhão.')
        b.responder('O que ele gosta?')
        _,r=b.responder('Quero saber de Zoltrino.')
        self.assertIn('Navrino',r);self.assertIn('Tovrino',r)
        self.assertNotIn('pessoa:zoltrino',b.memoria_sessao.entidades)
        ident,r=b.responder('O que é DNA?')
        self.assertTrue(ident.startswith('conhecimento:'))
        self.assertFalse(b.dialogo_conversa.trace['usada'])

    def test_retomada_usa_objetivo_declarado_e_nao_inventa_contexto_ausente(self):
        b=self.bot()
        b.responder('Quero desenhar um tamanduá viajante, mas só tenho papel reciclado.')
        b.responder('Vou descansar um pouco.')
        _,r=b.responder('Estou de volta. O que estávamos fazendo?')
        self.assertIn('tamanduá viajante',r);self.assertIn('papel reciclado',r)
        outro=self.bot();_,r=outro.responder('Voltei. O que estávamos fazendo?')
        self.assertNotIn('tamanduá',r)

    def test_personagem_cenario_detalhe_final_e_contagem_sem_nome_real(self):
        b=self.bot();antes=list(b.memoria_sessao.afirmacoes)
        for texto in ['Escreva uma história curta com uma anta exploradora e uma ilha distante.',
                      'Continue a história.','Agora muda o final: ela encontra um amigo.']:
            _,r=b.responder(texto)
            self.assertTrue(b.dialogo_conversa.trace['usada'])
            self.assertIn('anta exploradora',r);self.assertIn('ilha distante',r)
        self.assertIn('um amigo',r)
        self.assertEqual('uma ilha distante',b.conversacao.geracao.ultima_escrita['slots']['tema2'])
        variante=b.conversacao.geracao.ultima_escrita['variante']
        _,r=b.responder('Não invente um nome para a personagem.')
        self.assertNotIn('cancelado',r)
        _,r=b.responder('Escreva a história em 5 frases.')
        import re
        self.assertEqual(5,len(re.findall(r'[^.!?]+[.!?](?:\s|$)',r)))
        self.assertIn('um amigo',r)
        self.assertEqual(variante,b.conversacao.geracao.ultima_escrita['variante'])
        self.assertEqual(antes,b.memoria_sessao.afirmacoes)

    def test_cancelamento_real_continua_cancelando_e_ficcao_nao_vira_fato(self):
        b=self.bot();b.responder('Escreva uma história curta com uma anta exploradora.')
        _,r=b.responder('Não escreva a história.')
        self.assertIn('cancelado',r)
        _,r=b.responder('O que é uma célula?')
        self.assertFalse(b.dialogo_conversa.trace['usada'])
        self.assertNotIn('anta',r)

    def test_corpus_particionado_checkpoint_isolado_e_parametros_nao_aumentam(self):
        d=json.loads((H/'corpus_gru.json').read_text());m=json.loads(gzip.decompress((H/'checkpoint_gru_dialogo.json.gz').read_bytes()))
        self.assertEqual({'aprovado':False,'ativo_no_chat':False},m['controle'])
        self.assertLessEqual(m['treino']['parametros'],88969)
        splits={}
        for e in d['exemplos']:splits.setdefault(e['dialogo'],set()).add(e['split'])
        self.assertTrue(all(len(s)==1 for s in splits.values()))

    def test_amigo_do_final_nao_vira_cenario_na_continuacao(self):
        b=self.bot();b.responder('Escreva uma história curta com uma anta exploradora.')
        b.responder('Agora muda o final: ela encontra um amigo.')
        _,r=b.responder('Continue a história.')
        self.assertFalse(b.dialogo_conversa.trace['usada'])
        self.assertIn('um amigo',r)
        self.assertNotIn('em um amigo',r)

    def test_variantes_geradas_conservam_argumentos_sem_nomes_numeros_livres(self):
        m=GeradorGRU(json.loads(gzip.decompress((H/'checkpoint_gru_dialogo.json.gz').read_bytes())))
        distintas=set()
        for variante in range(8):
            ctx=dict(acao='historia',slots={'tema1':'uma anta exploradora','tema2':'uma ilha distante'},
                     mensagem='',historico=[],estilo='neutro',variante=variante)
            g=m.gerar(ctx);t,q=conferir(g,ctx,set(m.vocabulario),5)
            self.assertTrue(q['aceita'],q);distintas.add(t)
            fake=dict(g,tokens=g['tokens']+['Maria','42'])
            _,q=conferir(fake,ctx,set(m.vocabulario));self.assertFalse(q['aceita'])
        self.assertGreaterEqual(len(distintas),6)

if __name__=='__main__':unittest.main()
