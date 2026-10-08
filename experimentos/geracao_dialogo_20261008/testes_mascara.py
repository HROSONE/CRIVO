import unittest
from rodada import ROOT,codificar
from tokenizers import Tokenizer

class Supervisao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));cls.tok.encode_special_tokens=True

    def test_so_resposta_atual_e_fim_recebem_perda(self):
        e={'historico':[{'papel':'usuario','texto':'A fita é azul.'},{'papel':'assistente','texto':'Entendi a cor.'}],
           'mensagem':'Troque para branca.','resposta':'Agora a fita é branca.'}
        c=codificar(self.tok,e);targets=[y for y in c['y'] if y!=-100]
        self.assertEqual(self.tok.decode(targets),'Agora a fita é branca.')
        self.assertEqual(targets[-1],self.tok.token_to_id('<fim>'))
        primeiro=c['y'].index(targets[0])
        self.assertEqual(c['x'][primeiro],self.tok.token_to_id('<assistente>'))

    def test_historico_grande_nao_e_truncado_silenciosamente(self):
        with self.assertRaises(ValueError):codificar(self.tok,{'historico':[], 'mensagem':'texto ' * 300,'resposta':'Resposta.'})

if __name__=='__main__':unittest.main()
