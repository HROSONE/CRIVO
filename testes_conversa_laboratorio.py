"""Sequência reportada no laboratório e limites dos novos atos de conversa."""
import unittest
from crivo import Crivo
from web_core import responder_web

MENSAGENS = ['Oi', 'Péssimo', 'Meu dia foi meio triste', 'Você me entende?', 'Kkkkk',
             'Meu Deus. Você tá muito inteligente', 'Eu sou o Henrique.',
             'Kkk meu nome é Henrique', 'Eu sou seu Criador. Eu quem inventei você.',
             'Você entende de psicologia?']


class ConversaLaboratorio(unittest.TestCase):
    def test_sequencia_e_memoria_com_e_sem_classificador(self):
        for neural in (False, True):
            with self.subTest(neural=neural):
                b=Crivo(usar_linguagem_neural=neural)
                respostas=[b.responder(m) for m in MENSAGENS]
                self.assertEqual(respostas[1][0],'social:acolhimento')
                self.assertEqual(respostas[5][0],'social:elogio')
                for i in (6,7):
                    self.assertEqual(respostas[i][0],'conversa:apresentacao')
                    self.assertIn('Henrique',respostas[i][1])
                self.assertEqual(respostas[8][0],'conversa:criacao')
                self.assertIn('Você está me dizendo que criou o Crivo',respostas[8][1])
                self.assertNotIn('você quem inventou você',respostas[8][1])
                self.assertEqual(respostas[9][0],'social:capacidade')
                self.assertIn('Henrique',b.responder('qual é meu nome?')[1])
                self.assertEqual(b.exportar_memoria()['nome'],'Henrique')

    def test_replay_http_e_sessoes_independentes(self):
        for i in (1,5,6,8,9):
            r=responder_web(dict(message=MENSAGENS[i],history=MENSAGENS[:i]))
            self.assertNotEqual(r['id'],'social:nao_entendido')
            self.assertNotEqual(r['id'],'fora')
        r=responder_web(dict(message='qual é meu nome?',history=MENSAGENS))
        self.assertIn('Henrique',r['response'])
        self.assertIn('ainda não me disse',responder_web(dict(message='qual é meu nome?'))['response'])

    def test_nome_corrigido_preserva_grafia_e_nao_guarda_profissao(self):
        b=Crivo(usar_linguagem_neural=False)
        b.responder('Me chamo Ana-Clara')
        self.assertIn('Ana-Clara',b.responder('qual é meu nome?')[1])
        b.responder('Corrigindo, meu nome é João da Silva')
        self.assertIn('João da Silva',b.responder('qual é meu nome?')[1])
        for mensagem in ['Eu sou programador','Eu sou seu Criador','Eu sou triste',
                         'Se meu nome é Pedro, quem sou eu?', 'Ela disse "me chamo Maria"']:
            b.responder(mensagem)
            self.assertEqual(b.conversacao.dialogo.dados['nome'],'João da Silva')

    def test_nao_se_apropria_de_terceiros_negacoes_ou_perguntas_factuais(self):
        for mensagem in ['Meu amigo entende de psicologia','Você não é inteligente',
                         'Você sabe sobre isso porque leu meu nome?', 'O que é psicologia?']:
            with self.subTest(mensagem=mensagem):
                ident,_=Crivo(usar_linguagem_neural=False).responder(mensagem)
                self.assertNotIn(ident,('social:elogio','conversa:apresentacao'))
        ident,_=Crivo().responder('O que é psicologia?')
        self.assertNotEqual(ident,'social:capacidade')

    def test_estado_curto_exige_contexto_ou_declaracao(self):
        from conversa_cotidiana import _atos_pessoais
        b=Crivo(usar_linguagem_neural=False)
        self.assertIsNone(_atos_pessoais('Péssimo',b,'pessimo','conhecimento:marte'))
        self.assertIsNone(_atos_pessoais('Estou mal',b,'estou mal','conhecimento:marte'))


if __name__=='__main__':unittest.main()
