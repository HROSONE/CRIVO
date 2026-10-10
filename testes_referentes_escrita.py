"""Regressões de contexto ficcional, limites de fonte e isolamento de pesos."""
import hashlib,json,unittest
from pathlib import Path
from crivo import Crivo
from conversa_dialogo import resolver_objeto_escrita
H=Path(__file__).resolve().parent/'experimentos/referentes_escrita_20261010'
class TestesReferentesEscrita(unittest.TestCase):
 def test_pronome_recupera_objeto_e_continuacao_preserva_estado(self):
  b=Crivo();b.responder('Conte uma história sobre uma irara em uma oficina âmbar.')
  b.responder('Ela perdeu uma carteira violeta. Continue a partir disso.')
  _,r=b.responder('Ela a recuperou. Continue a partir disso.')
  self.assertIn('carteira violeta',r);self.assertEqual('recuperacao',b.dialogo_conversa.trace['classe_escrita'])
  self.assertEqual('uma carteira violeta',b.dialogo_conversa.trace['resolucao_objeto']['objeto'])
  _,r=b.responder('E agora?')
  self.assertTrue(b.dialogo_conversa.trace['continuidade_causal']);self.assertIn('carteira violeta',r)
  self.assertNotIn('objeto perdido',r);self.assertNotIn('perdeu',r)
 def test_correcao_substitui_objeto_sem_mudar_personagem_ou_cenario(self):
  b=Crivo();b.responder('Conte uma história sobre uma cutia em uma oficina pérola.')
  b.responder('Ela perdeu um broche verde. Continue a partir disso.')
  b.responder('Corrigindo: não era um broche verde, era um broche marfim.')
  _,r=b.responder('Continue a história.')
  for v in ('uma cutia','uma oficina pérola','um broche marfim'):self.assertIn(v,r)
  self.assertNotIn('broche verde',r);self.assertEqual('perda',b.dialogo_conversa.trace['classe_escrita'])
 def test_ambiguidades_negacao_e_estado_antigo_nao_inventam_resolucao(self):
  for obj,entrada,ativo in (
   ('um mapa e uma bússola','Ele o recuperou. Continue.',True),
   ('uma carteira violeta','Ele o recuperou. Continue.',True),
   ('uma carteira violeta','Ela não a recuperou. Continue.',True),
   ('uma carteira violeta','Corrigindo: não era azul, era vermelho.',True),
   ('uma carteira violeta','Ela a recuperou. Continue.',False)):
   e=dict(slots=dict(tema1='uma cutia',tema2='uma oficina',relato='Ela perdeu '+obj),classe_escrita='perda',evento_escrita='Ela perdeu '+obj)
   original=json.dumps(e,sort_keys=True)
   with self.subTest(obj=obj,entrada=entrada):
    r=resolver_objeto_escrita(entrada,e,ativo)
    self.assertEqual('esclarecimento',r['peca']);self.assertNotIn('slots',r)
    self.assertEqual(original,json.dumps(e,sort_keys=True))
  self.assertIsNone(resolver_objeto_escrita('Eu a recuperei.',e,True))
  self.assertIsNone(resolver_objeto_escrita('Não era queijo, era presunto.',None,False))
  self.assertIsNone(resolver_objeto_escrita('Não era uma carteira violeta, era uma carteira jade.',e,False))
 def test_conserto_com_pronome_e_fronteira_factual(self):
  b=Crivo();b.responder('Conte uma história sobre uma lontra em uma casa âmbar.')
  b.responder('Ela encontrou uma bolsa jade. Continue a partir disso.')
  _,r=b.responder('Ela tenta consertá-la. Continue a partir disso.')
  self.assertIn('bolsa jade',r);self.assertEqual('conserto',b.dialogo_conversa.trace['classe_escrita'])
  b.responder('O que é diferença de potencial?');_,r=b.responder('Ela a recuperou. Continue a partir disso.')
  self.assertEqual('esclarecimento',b.ultima_rota_natural['peca']);self.assertFalse(b.dialogo_conversa.trace['usada']);self.assertIn('Qual objeto',r)
 def test_entradas_juiz_e_pesos_sao_os_congelados(self):
  for f,d in [('casos.json','SHA256'),('avaliar.py','SHA256-juiz')]:
   self.assertEqual((H/d).read_text().split()[0],hashlib.sha256((H/f).read_bytes()).hexdigest())
  self.assertEqual('28d05179e4dda05473a5bdb0a3963d8e032b3d3e9c5d6d60a77404310545d4e8',hashlib.sha256((H.parent.parent/'rede_dialogo_conversa.json.gz').read_bytes()).hexdigest())
  protocolo=json.loads((H/'protocolo.json').read_text())
  self.assertFalse(protocolo['houve_treino'])
  for arquivo,digest in protocolo['experimento_anterior_preservado_sha256'].items():
   self.assertEqual(digest,hashlib.sha256((H.parent.parent/arquivo).read_bytes()).hexdigest(),arquivo)
if __name__=='__main__':unittest.main()
