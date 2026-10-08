"""Transferência de argumentos e fronteira entre relato e ficção."""
from copy import deepcopy
import unittest
from argumentos_conversa import ArgumentosConversa


class TestesArgumentosConversa(unittest.TestCase):
    def test_dilema_e_alternativa_conservam_fontes_sem_decidir(self):
        d=ArgumentosConversa()
        a='Estou dividido entre fazer um curso e terminar meu jardim. Podemos pensar juntos?'
        d.responder(a)
        d.responder('O diploma não é o principal. Quero aprender, mas estou sem tempo.')
        d.responder('E se eu começasse apenas um módulo? O que acha?')
        r=d.responder('Resume meu dilema e a alternativa.')
        self.assertIn('fazer um curso',r[1]);self.assertIn('terminar meu jardim',r[1])
        self.assertIn('sem tempo',r[1]);self.assertIn('apenas um módulo',r[1])
        self.assertEqual(d.ultimo['fontes'][0],dict(origem='usuario',texto=a))
        self.assertFalse(d.ultimo['prova_logica'])
        self.assertEqual(d.ultimo['fontes'][-1]['origem'],'hipotese')

    def test_associacao_e_correcao_nao_recebem_diagnostico(self):
        d=ArgumentosConversa()
        d.responder('Quando vejo o farol, lembro das visitas à minha prima. O que essa ligação sugere?')
        r=d.responder('Não é medo. É uma sensação de alegria. Você entendeu?')
        self.assertIn('alegria',r[1]);self.assertIn('não medo',r[1])
        self.assertEqual(d.ultimo['sentimento'],'alegria')
        self.assertEqual(d.ultimo['associacao']['lembranca'],'visitas à minha prima')

    def test_cena_nao_atualiza_fatos_pessoais(self):
        d=ArgumentosConversa()
        d.responder('Quando escuto um sino, penso nas visitas à minha prima. O que essa associação sugere?')
        antes=deepcopy(d.associacao)
        fontes=deepcopy(d.fontes)
        r=d.responder('Transformar essa memória em uma cena curta: tenta.')
        self.assertIn('sino',r[1]);self.assertIn('prima',r[1])
        self.assertEqual(d.ultimo['escopo'],'ficcao')
        self.assertEqual(d.associacao,antes);self.assertEqual(d.fontes,fontes)
        d.responder('Agora muda o narrador para uma criança curiosa.')
        self.assertEqual(d.ultimo['narrador'],'primeira_pessoa_curiosa')

    def test_citacao_e_factual_nao_criam_objetivos(self):
        d=ArgumentosConversa()
        self.assertIsNone(d.responder('Meu colega disse "Estou dividido entre vencer e comprar uma casa".'))
        self.assertEqual(d.objetivos,[])
        self.assertIsNone(d.responder('O que é DNA?'))
        self.assertIsNone(d.responder('Meu colega disse que estou dividido entre vencer e viajar.'))
        self.assertEqual(d.objetivos,[])

    def test_novo_assunto_e_consulta_factual_nao_repetem_dilema(self):
        d=ArgumentosConversa()
        d.responder('Estou dividido entre viajar e estudar. Podemos pensar juntos?')
        self.assertIsNone(d.responder('Resuma a história de Napoleão.'))
        self.assertIsNone(d.responder('Resuma meu livro.'))
        d.responder('Quero falar sobre a minha festa.')
        self.assertIsNone(d.responder('Resume meu dilema.'))

    def test_hipotese_nao_cria_memoria_real(self):
        d=ArgumentosConversa()
        d.responder('Estou dividido entre viajar e estudar. Podemos pensar juntos?')
        d.responder('Se quando vejo o sino eu lembro da viagem, como seria?')
        self.assertIsNone(d.associacao)

    def test_isolamento_reset_e_limites(self):
        a=ArgumentosConversa();b=ArgumentosConversa()
        a.responder('Estou dividido entre viajar e estudar. O que acha?')
        self.assertIsNone(b.responder('Resume meu dilema.'))
        for i in range(20):a.responder('Quero aprender assunto %s.'%i)
        self.assertLessEqual(len(a.objetivos),4);self.assertLessEqual(len(a.fontes),12)
        a.responder('Vamos começar de novo.')
        self.assertIsNone(a.responder('Resume meu dilema.'))


class TestesIntegracaoArgumentos(unittest.TestCase):
    def test_web_retoma_alternativa_e_nao_declara_prova(self):
        from web_core import responder_web
        r=responder_web(dict(message='Resume meus objetivos e essa alternativa.',history=[
            'Estou dividido entre pintar e cuidar do jardim. Podemos pensar juntos?',
            'Quero aprender, mas estou cansado.',
            'E se eu fizesse apenas uma pintura pequena? O que muda?']))
        self.assertEqual(r['id'],'conversa:argumentos')
        self.assertIn('jardim',r['response']);self.assertIn('pintura pequena',r['response'])
        self.assertFalse(r['has_proof']);self.assertFalse(r['generation']['usada'])
        self.assertIsNotNone(r['conversational_arguments'])
        self.assertNotIn('conversational_reasoning',r)

    def test_uma_resposta_um_turno(self):
        from crivo import Crivo
        b=Crivo(usar_linguagem_neural=False,usar_geracao=False)
        for s in ['Estou dividido entre nadar e trabalhar. Podemos pensar juntos?',
                  'Quero descansar, mas estou cansado.',
                  'E se eu aceitasse apenas um turno? O que muda?']:
            antes=b.conversacao.turno;id_,_=b.responder(s)
            self.assertEqual(b.conversacao.turno,antes+1)
            self.assertEqual(id_,'conversa:argumentos')


if __name__=='__main__':unittest.main()
