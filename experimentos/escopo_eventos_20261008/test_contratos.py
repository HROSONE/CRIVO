"""Verifica semântica e procedência, sem pontuar o teste final."""
import unittest
from dados import construir
from normalizacao import normalizar,codificar
from base import ROOT
from tokenizers import Tokenizer
from modelo import recuperar

class Contratos(unittest.TestCase):
    def test_confirmacao_nao_restaura_preco_antigo(self):
        es=construir('treino',12)
        antes,hip,confirmado,retorno=es[1:]
        self.assertTrue(hip['hipotese']);self.assertFalse(confirmado['hipotese'])
        self.assertEqual(hip['argumentos'],confirmado['argumentos'])
        self.assertEqual(confirmado['argumentos'],retorno['argumentos'])
        self.assertNotEqual(antes['argumentos'],confirmado['argumentos'])

    def test_correcao_durante_hipotese_preserva_outro_fato(self):
        es=construir('treino',4)
        self.assertTrue(es[1]['hipotese']);self.assertFalse(es[2]['hipotese'])
        self.assertEqual(es[2]['argumentos'],es[3]['argumentos'])
        self.assertEqual(sum(a['turno']==2 for a in es[2]['argumentos'] if a),1)
        self.assertEqual(sum(a['turno']==0 for a in es[2]['argumentos'] if a),1)

    def test_normalizacao_nao_altera_fontes(self):
        tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'))
        for i in range(16):
            for e in construir('dev',i):
                c=codificar(tok,e)
                for sp,(a,b) in zip(e['argumentos']+[e['referente']],zip(c['pontos'][::2],c['pontos'][1::2])):
                    if sp:self.assertEqual(recuperar(c,a,b)['texto'],sp['texto'])

    def test_palavras_funcionais_nao_viram_entidades(self):
        # Sem valores/gold: a normalização só recebe o texto bruto.
        textos=['Estou comparando Azul e Verde.','Refaça Azul e Verde.',
                'Houve um erro no dado real de Azul; compare Azul e Verde.']
        for t in textos:
            _,_,mapa=normalizar([t])
            self.assertEqual(set(mapa),{'azul','verde'})

if __name__=='__main__':unittest.main()
