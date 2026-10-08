import unittest
from normalizar import normalizar,codificar
from modelo import recuperar
from comum import ROOT
from tokenizers import Tokenizer

class Normalizacao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));cls.tok.encode_special_tokens=True

    def item(self,turnos):
        return codificar(self.tok,{'turnos':turnos,'argumentos':[None]*3,'referente':None})

    def test_trocar_nomes_preserva_entrada_neural(self):
        a=self.item(['O plano Safira custa 213 reais. Jade custa 289 reais. Compare Jade e Safira.'])
        b=self.item(['O plano Brisa custa 213 reais. Lago custa 289 reais. Compare Lago e Brisa.'])
        self.assertEqual(a['ids'],b['ids'])

    def test_fontes_preservam_nome_original(self):
        texto='No caso de Safira, o valor é 213 reais.';a=texto.index('Safira')
        e={'turnos':[texto],'argumentos':[None]*3,'referente':{'turno':0,'inicio':a,'fim':a+6,'texto':'Safira'}}
        item=codificar(self.tok,e);start,end=item['pontos'][-2:]
        self.assertEqual(recuperar(item,start,end),e['referente'])

    def test_nao_reaplica_alias_e_nao_funde_entidades(self):
        textos,_,nomes=normalizar(['Lia custa 20 reais. Ana custa 30 reais. Compare Ana e Lia.'])
        self.assertEqual(textos,['Beto custa 20 reais. Ana custa 30 reais. Compare Ana e Beto.'])
        self.assertEqual(nomes,{'ana':'Ana','lia':'Beto'})

    def test_limite_recusa_colisao(self):
        with self.assertRaises(ValueError):normalizar(['Ana Beto Caio Dora Iara Rui Lia Leo Zeca'])

if __name__=='__main__':unittest.main()
