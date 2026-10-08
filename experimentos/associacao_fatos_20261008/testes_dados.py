"""Contratos semânticos do novo corpus e da gramática de cópia."""
import unittest
from gerar import construir
from comum import ROOT
from modelo import codificar, esperado
from decodificar import mod
from tokenizers import Tokenizer

class Contratos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'))
        cls.tok.encode_special_tokens=True

    def test_preco_distrator_nao_e_argumento(self):
        e=construir('treino',0)[0]
        self.assertIn('Cobre é 150 reais',e['turnos'][0])
        self.assertEqual(esperado(e)['resultado'],{'totais':[141,121],'menor':1,'diferenca':20})

    def test_negacao_ausencia_e_contradicao_sao_distintas(self):
        self.assertEqual([esperado(construir('treino',i)[0])['resultado']['status']
            for i in [1,3,5,7]],['provado','refutado','indeterminado','contraditorio'])

    def test_retorno_nao_persiste_hipotese(self):
        for i in range(20):
            a,b,c,d=construir('treino',i)
            self.assertTrue(c['hipotese']);self.assertFalse(d['hipotese'])
            self.assertEqual(esperado(b)['resultado'],esperado(d)['resultado'])
            self.assertEqual(b['argumentos'],d['argumentos'])

    def test_gramatica_contem_todos_os_alvos_sem_usar_rotulos(self):
        for split in ['treino','dev','teste']:
            for i in range(24):
                for e in construir(split,i):
                    item=codificar(self.tok,e)
                    # Detectores recebem somente falas e offsets, sem alvos.
                    item['exemplo']={'turnos':e['turnos']}
                    tipos=['numero','numero'] if i%2==0 else ['regra','posse']
                    for span,tipo in zip(e['argumentos'],tipos):
                        possibles=[r for _,r in mod.candidatos(item,tipo)]
                        self.assertIn(span,possibles)

if __name__=='__main__':unittest.main()
