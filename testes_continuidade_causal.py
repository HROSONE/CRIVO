"""Contratos de estado, fronteira factual e isolamento da continuação própria."""
import copy,gzip,hashlib,json,unittest
from pathlib import Path
from types import SimpleNamespace
import conversa_dialogo as cd
ROOT=Path(__file__).resolve().parent;H=ROOT/'experimentos/continuidade_causal_20261010'
class TestesContinuidadeCausal(unittest.TestCase):
 def bot(self,evento='Ela perdeu um apito turquesa',classe='perda',passo=0,ident='conversa:gerada_continuacao'):
  e=dict(tipo='historia',turno=1,slots=dict(tema1='uma viscacha cartógrafa',tema2='um farol âmbar',relato=evento),classe_escrita=classe,evento_escrita=evento,passo_causal=passo,continuidade_causal=bool(passo))
  return SimpleNamespace(conversacao=SimpleNamespace(turno=2,geracao=SimpleNamespace(ultima_escrita=e,MAX_INTERVALO=10)),historico=[dict(id=ident)])
 def test_elipse_seleciona_objeto_sem_recopiar_declaracao(self):
  b=self.bot();r=cd.contexto_escrita('E depois?',b)
  self.assertEqual('perda',r['classe_escrita']);self.assertEqual('um apito turquesa',r['slots']['relato']);self.assertTrue(r['continuidade_causal'])
  self.assertEqual('uma viscacha cartógrafa',r['slots']['tema1'])
  self.assertEqual('um farol âmbar',r['slots']['tema2'])
  self.assertEqual(0,r['passo_causal'])
  for comando in ('Continue a história.','Continue.','Continue mais um pouco.','Continue de onde parou.','Não repita a cena anterior.'):
   self.assertTrue(cd.contexto_escrita(comando,b)['continuidade_causal'],comando)
 def test_nao_retoma_historia_antiga_apos_fato(self):
  r=cd.contexto_escrita('E depois?',self.bot(ident='fisica:potencial'))
  self.assertEqual('esclarecimento',r['peca']);self.assertEqual('continuidade_incerta',r['ato']);self.assertNotIn('slots',r)
 def test_elipse_pratica_usa_objetivo_atual_antes_de_esclarecer(self):
  from crivo import Crivo
  b=Crivo();b.responder('Quero aprender a desenhar um peixe com lápis e papel.')
  _,r=b.responder('E agora?')
  self.assertEqual('orientacao',b.ultima_rota_natural['peca']);self.assertIn('qual parte do peixe',r)
  self.assertFalse(b.dialogo_conversa.trace['usada'])
  b.responder('O que é diferença de potencial?')
  _,r=b.responder('E agora?')
  self.assertEqual('continuidade_incerta',b.ultima_rota_natural['ato']);self.assertIn('?',r)
 def test_quinto_passo_esclarece_sem_reiniciar_arco(self):
  b=self.bot(passo=4);r=cd.contexto_escrita('Mais um passo.',b)
  self.assertEqual('esclarecimento',r['peca'])
  self.assertEqual('corrigir',cd.contexto_escrita('Faça um final tranquilo.',b)['ato'])
  b.historico[-1]['id']='conversa:esclarecer'
  self.assertEqual('corrigir',cd.contexto_escrita('Faça um final tranquilo.',b)['ato'])
 def test_usuario_pode_concluir_apos_limite_de_continuacao(self):
  from crivo import Crivo
  b=Crivo(checkpoint_dialogo_candidato=str(H/'checkpoint_gru_dialogo.json.gz'))
  b.responder('Conte uma história sobre uma irara em uma oficina verde.')
  b.responder('Ela perdeu um broche azul. Continue a partir disso.')
  for _ in range(4):
   _,r=b.responder('Continue a história.')
   self.assertTrue(b.dialogo_conversa.trace['usada'],r)
   self.assertIn('broche azul',r)
  _,r=b.responder('Continue a história.')
  self.assertEqual('continuidade_incerta',b.ultima_rota_natural['ato']);self.assertIn('?',r)
  _,r=b.responder('Faça um final tranquilo.')
  self.assertTrue(b.dialogo_conversa.trace['usada'],r);self.assertIn('A história terminou.',r)
 def test_objeto_nao_extraivel_exige_esclarecimento(self):
  r=cd.contexto_escrita('E agora?',self.bot(evento='A personagem parou para pensar',classe='encontro'))
  self.assertEqual('esclarecimento',r['peca'])
 def test_guardas_bloqueiam_reverter_estado_e_inventar_numero_nome(self):
  self.assertFalse(cd.conferir_estado_causal(['A','personagem','procurou','o','objeto','perdido','.'],'recuperacao'))
  self.assertFalse(cd.conferir_estado_causal(['O','objeto','recuperado','.'],'perda'))
  self.assertTrue(cd.conferir_estado_causal(['A','busca','terminou','.'],'recuperacao'))
  d=json.loads(gzip.decompress((H/'checkpoint_gru_dialogo.json.gz').read_bytes()));c=dict(slots={'tema1':'uma viscacha'})
  for t in ('17','Maria'):
   _,g=cd.conferir(dict(completa=True,tokens=['Ficção',':','@tema1','.','A','personagem',t,'.','O','trabalho','terminou','.']),c,d['vocabulario'])
   self.assertFalse(g['aceita'])
 def test_declaracao_real_nao_entra_na_ficcao(self):
  self.assertIsNone(cd.contexto_escrita('Eu perdi um apito turquesa. E agora?',self.bot()))
  self.assertTrue(cd.contexto_escrita('Avance sem repetir o que eu disse.',self.bot())['continuidade_causal'])
 def test_original_false_e_mesma_arquitetura(self):
  d=json.loads(gzip.decompress((H/'checkpoint_gru_dialogo.json.gz').read_bytes()));b=json.loads(gzip.decompress((H/'checkpoint_base_134.json.gz').read_bytes()))
  self.assertEqual({'aprovado':False,'ativo_no_chat':False},d['controle']);self.assertFalse(cd.aprovacao_valida(d))
  self.assertEqual(b['vocabulario'],d['vocabulario']);self.assertEqual(b['assinatura_atributos'],d['assinatura_atributos']);self.assertEqual(85130,d['treino']['parametros'])
  exemplos=json.loads((H/'corpus_gru.json').read_text())['exemplos'];antigos=json.loads((H.parent/'diversidade_dialogo_20261010/corpus_gru.json').read_text())['exemplos']
  self.assertEqual(antigos,exemplos[:len(antigos)])
  entradas=json.loads((H/'sondas.json').read_text())['sessoes'];fonte=json.dumps(exemplos,ensure_ascii=False)
  for s in entradas[:10]:self.assertNotIn(s['personagem'],fonte);self.assertNotIn(s['evento'],fonte)
  for f,sha in [('sondas.json','SHA256'),('avaliar.py','SHA256-juiz'),('conversas_novas.json','SHA256-novas'),('sondas_aliases.json','SHA256-aliases'),('avaliar_aliases.py','SHA256-juiz-aliases')]:self.assertEqual((H/sha).read_text().split()[0],hashlib.sha256((H/f).read_bytes()).hexdigest())
 def test_aprovacao_exige_continuidade_folego_e_regressoes(self):
  d=json.loads(gzip.decompress((ROOT/'rede_dialogo_conversa.json.gz').read_bytes()))
  self.assertTrue(cd.aprovacao_valida(d));self.assertEqual(cd.ORIGEM_V7_SHA256,d['aprovacao']['checkpoint_origem_sha256'])
  for k,v in [('continuidade_motor',5),('continuidade_http',5),('continuidade_motor',11),('esclarecimentos_motor',1),('folego_http',1),('contradicoes_estado',1),('aliases_motor',2),('casos_http',109),('diversidade_http',7),('praticos_motor',39),('referentes_ausentes',1)]:
   with self.subTest(chave=k):
    falso=copy.deepcopy(d);falso['aprovacao']['metricas'][k]=v;self.assertFalse(cd.aprovacao_valida(falso))
  antigo=json.loads(gzip.decompress((H/'checkpoint_base_134.json.gz').read_bytes()));c=json.loads(gzip.decompress((H/'checkpoint_gru_dialogo.json.gz').read_bytes()));c.update(controle=antigo['controle'],aprovacao=antigo['aprovacao']);self.assertFalse(cd.aprovacao_valida(c))
 def test_preservacao_e_manifesto(self):
  m=json.loads((H/'manifesto.json').read_text())
  for grupo,base in [('arquivos_sha256',H),('pesos_preservados_sha256',ROOT),('experimentos_preservados_sha256',ROOT)]:
   for f,digest in m[grupo].items():self.assertEqual(digest,hashlib.sha256((base/f).read_bytes()).hexdigest(),f)
  for f,sha in [('avaliar_folego.py','SHA256-juiz-folego')]:self.assertEqual((H/sha).read_text().split()[0],hashlib.sha256((H/f).read_bytes()).hexdigest())
if __name__=='__main__':unittest.main()
