"""Integridade de memória e inferência; nenhum painel fechado é aberto."""
from copy import deepcopy
import unittest
import torch
from apoio import ROOT,INICIAL
from preparo import normalizar,codificar
from rede import carregar
from rede_eventos import carregar as carregar_antigo
from modelo import lote
from decodificar import proposta_limitada
from corpus_memoria import estados,supervisionar
from dados import construir
from tokenizers import Tokenizer

class Integridade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1);torch.manual_seed(20261015)
        cls.tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));cls.tok.encode_special_tokens=True
        cls.m,_=carregar(cls.tok);cls.m.eval()

    def test_consulta_com_ponto_define_ordem(self):
        _,_,ns=normalizar(['Verde custa 35 reais. Azul custa 23 reais. Entre Azul e Verde, apresente a diferença.'])
        self.assertEqual(ns,{'azul':'Ana','verde':'Beto'})

    def test_confirmacao_promove_fonte_da_hipotese(self):
        es=estados(construir('treino',12))
        self.assertNotEqual(es[2]['bancos_gold'][0],es[2]['bancos_gold'][2])
        self.assertEqual(es[3]['bancos_gold'][0],es[2]['bancos_gold'][2])
        self.assertEqual(es[4]['bancos_gold'][0],es[3]['bancos_gold'][0])
        self.assertTrue(all(s is None or s['turno']<=2 for s in es[4]['bancos_gold'][0]))

    def test_legado_sem_bancos_reais_confiaveis_e_mascarado(self):
        e=construir('treino',0)[1];e['bancos_gold']=[None,None,e['argumentos']+[e['referente']]]
        c=supervisionar(codificar(self.tok,e));self.assertEqual(c['bancos_validos'],[False]*8+[True]*4)

    def test_inicializacao_equivale_pesos_anteriores(self):
        c=codificar(self.tok,construir('treino',0)[-1]);x,l=lote([c],self.tok.token_to_id('<pad>'))
        old,_=carregar_antigo(INICIAL);old.eval();self.m.train()
        with torch.no_grad():a=old(x,l);b=self.m(x,l)
        for k in ['operacao','escopo','pontos']:self.assertTrue(torch.equal(a[k],b[k]),k)
        self.assertFalse(self.m.corpo.training)
        self.assertTrue(all(not p.requires_grad for p in self.m.corpo.parameters()))

    def test_gold_nao_muda_previsao(self):
        e=estados(construir('treino',12))[-1];outro=deepcopy(e)
        outro.update(argumentos=[None]*3,referente=None,hipotese=not e['hipotese'],evento='hipotese',trajetoria='futuro alterado',bancos_gold=[[None]*4]*3)
        a=codificar(self.tok,e);b=codificar(self.tok,outro)
        self.assertEqual(a['ids'],b['ids']);self.assertEqual(a['offsets'],b['offsets'])
        x,l=lote([a],self.tok.token_to_id('<pad>'));self.m.eval()
        with torch.no_grad():logits=self.m(x,l)
        self.assertEqual(proposta_limitada(a,logits,0),proposta_limitada(b,logits,0))

if __name__=='__main__':unittest.main()
