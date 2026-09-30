"""Regressões de fontes, retratações, retomada e memória de escrita."""
import unittest

from crivo import Crivo
from pedidos_gerativos import reflexao


class ContextoGerativoTestes(unittest.TestCase):
    def pessoal(self):
        b=Crivo()
        b.responder("Quero aprender a tocar flauta")
        b.responder("Tenho 15 minutos à noite")
        return b

    def test_fato_suspende_objetivo_para_pedido_implicito(self):
        b=self.pessoal();b.responder("O que é fotossíntese?")
        g=b.conversacao.geracao
        p=g._contexto("Me sugira um próximo passo",b,b.conversacao)
        self.assertNotEqual((p or {}).get("acao"),"plano")

    def test_fato_suspende_escuta_alternativa_reparo_e_hipotese_pessoais(self):
        b=self.pessoal();b.responder("O que é fotossíntese?")
        for q in ("Me dê outra possibilidade","Essa resposta não me ajudou",
                  "Você entendeu o que eu quis dizer?","E se eu tiver só 10 minutos?"):
            with self.subTest(pergunta=q):
                p=b.conversacao.geracao._contexto(q,b,b.conversacao)
                self.assertNotIn("acao",p or {})

    def test_consulta_com_tempo_nao_vira_retratacao_de_disponibilidade(self):
        for q in ("Não consigo entender como funciona o tempo de execução do código Python",
                  "Não posso entender o que é tempo"):
            with self.subTest(pergunta=q):
                b=self.pessoal()
                self.assertNotEqual(b.responder(q)[0],"conversa:relato")
                self.assertEqual(b.conversacao.dialogo.dados.get("minutos"),"15")

    def test_objetivo_expira_junto_com_fontes_da_geracao(self):
        b=self.pessoal();b.conversacao.turno+=11
        g=b.conversacao.geracao
        self.assertIsNone(g._objetivo(b.conversacao))
        self.assertNotIn("acao",g._contexto("Me sugira um próximo passo",b,b.conversacao))

    def test_redeclaracao_do_mesmo_objetivo_renova_a_fonte(self):
        b=self.pessoal();b.conversacao.turno+=11
        b.responder("Quero aprender a tocar flauta")
        self.assertEqual(b.conversacao.geracao._objetivo(b.conversacao),"aprender a tocar flauta")

    def test_disponibilidade_condicional_nao_vira_tempo_incondicional(self):
        b=self.pessoal()
        b.responder("Tenho 45 minutos se terminar o trabalho cedo")
        self.assertEqual(b.conversacao.dialogo.dados.get("minutos"),"15")
        self.assertIn("se terminar",b.conversacao.geracao._restricao(b.conversacao))

    def test_pedido_pendente_nao_consume_consulta_desconhecida_ou_cancelamento(self):
        for q in ("Explique o conceito de xenocéu","Como funciona a rede astrólux",
                  "Defina o termo nuberímetro","Liste vantagens do mecanismo astrólux",
                  "Por favor não escreva isso","Você pode não fazer a história","Cancelar esse pedido"):
            with self.subTest(pergunta=q):
                b=Crivo();b.responder("Crie uma história")
                p=b.conversacao.geracao._contexto(q,b,b.conversacao)
                self.assertNotIn("acao",p or {})
                self.assertIsNone(b.conversacao.geracao.pendente)

    def test_retratacao_de_tempo_substitui_restricao_positiva(self):
        b=self.pessoal()
        self.assertEqual(b.responder("Não tenho mais tempo à noite")[0],"conversa:relato")
        self.assertNotIn("minutos",b.conversacao.dialogo.dados)
        p=b.conversacao.geracao._contexto("Me sugira um próximo passo",b,b.conversacao)
        self.assertEqual(p["slots"]["restricao"],"Não tenho mais tempo à noite")
        _,texto=b.responder("Como posso organizar isso?")
        self.assertNotIn("Você tem 15 minutos",texto)

    def test_negar_crenca_na_disponibilidade_nao_altera_tempo_declarado(self):
        for q in ("Não consigo acreditar que tenho 45 minutos",
                  "Não posso afirmar que disponho de 45 minutos"):
            with self.subTest(pergunta=q):
                b=self.pessoal();b.responder(q)
                self.assertEqual(b.conversacao.dialogo.dados.get("minutos"),"15")

    def test_retomada_restaura_fontes_do_assunto_certo(self):
        b=self.pessoal();b.responder("Quero conversar sobre uma viagem")
        b.responder("Eu quero visitar uma cidade pequena")
        self.assertEqual(b.responder("Vamos retomar aprender a tocar flauta")[0],"conversa:retomada")
        p=b.conversacao.geracao._contexto("Resuma o que eu contei",b,b.conversacao)
        self.assertIn("flauta",p["slots"]["detalhe"])
        self.assertIn("15 minutos",p["slots"]["relato"])
        self.assertNotIn("cidade",str(p))

    def test_cancelar_pedido_incompleto_nao_transforma_negacao_em_tema(self):
        b=Crivo();self.assertEqual(b.responder("Crie uma história")[0],"duvida")
        ident,_=b.responder("Não quero mais isso")
        self.assertNotIn("gerada_historia",ident)
        self.assertIsNone(b.conversacao.geracao.pendente)

    def test_reflexao_condicional_preserva_enquadramento_de_hipotese(self):
        p=reflexao("Se meu chefe não respondeu, posso concluir que ele me odeia?")
        self.assertTrue(p["hipotese"])
        self.assertEqual(p["slots"]["premissa"],"meu chefe não respondeu")
        self.assertEqual(p["slots"]["conclusao"],"ele me odeia")
        b=self.pessoal()
        self.assertIn("esclarecer",b.conversacao.geracao._contexto("Separe o que eu sei do que estou supondo",b,b.conversacao))

    def test_justificativa_nao_finge_explicar_nova_resposta_pessoal(self):
        b=Crivo();b.responder("Crie uma história sobre um lago e um robô")
        b.responder("Quero conversar sobre minha apresentação")
        b.responder("Fiquei nervoso e esqueci uma parte")
        self.assertIsNone(b.conversacao.geracao.ultima_decisao)

    def test_continuacao_usa_a_cena_da_escrita_apos_exploracao(self):
        b=Crivo();i,_=b.responder("Crie uma história sobre um lago e um robô")
        self.assertEqual(i,"conversa:gerada_historia")
        g=b.conversacao.geracao;escrita=g.ultima_escrita["texto"]
        b.responder("Me faça uma pergunta sobre a história")
        p=g._contexto("Continue a história",b,b.conversacao)
        self.assertEqual(p["acao"],"continuacao")
        self.assertIn(p["slots"]["detalhe"],escrita)


if __name__=="__main__": unittest.main()
