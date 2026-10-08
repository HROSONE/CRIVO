"""Contratos de escopo e continuidade; não cadastram perguntas no treino."""
from collections import deque
from types import SimpleNamespace
import unittest

from dialogo_situado import DialogoSituado, extrair_opcoes


def bot_fixture(relatos=()):
    from dialogo_aberto import DialogoAberto
    dialogo=DialogoAberto(usar_neural=False)
    c=SimpleNamespace(relatos=deque(relatos,maxlen=8),turno=1,dialogo=dialogo,assunto=None,objetivo=None)
    return SimpleNamespace(conversacao=c,contexto_textual=None)


class TestesQuadroSituado(unittest.TestCase):
    def test_tempo_real_condicional_citado_negado(self):
        d=DialogoSituado()
        b=bot_fixture(['Quero estudar desenho e só tenho 27 minutos por dia',
                       'Se eu tivesse 120 minutos seria outra situação',
                       'Meu colega disse "tenho 60 minutos"'])
        self.assertEqual(d.quadro(b.conversacao)['minutos'],'27')
        b.conversacao.relatos.append('Não tenho tempo agora')
        self.assertIsNone(d.quadro(b.conversacao)['minutos'])

    def test_objetivo_e_disponibilidade_compatíveis_com_memoria_nativa(self):
        d=DialogoSituado();b=bot_fixture()
        d.observar('Quero voltar a estudar música e só tenho 29 minutos','conversa:abertura',b)
        self.assertIn('música',b.conversacao.dialogo.dados['objetivo'])
        self.assertEqual(b.conversacao.dialogo.dados['minutos'],'29')
        d.observar('Se eu tivesse 90 minutos seria diferente','conversa:situada_hipotese',b)
        self.assertEqual(b.conversacao.dialogo.dados['minutos'],'29')

    def test_tempo_embutido_em_crenca_ou_condicao_nao_substitui_declaracao(self):
        d=DialogoSituado();b=bot_fixture(['Tenho 23 minutos à tarde'])
        for texto in ('Tenho 80 minutos se a reunião acabar cedo',
                      'Não consigo acreditar que tenho 50 minutos',
                      'Não posso afirmar que disponho de 90 minutos'):
            b.conversacao.relatos.append(texto)
            self.assertEqual(d.quadro(b.conversacao)['minutos'],'23')

    def test_circunstancia_pode_acrescentar_fator_a_hipotese_sem_virar_prova(self):
        d=DialogoSituado();b=bot_fixture()
        d.observar('Sempre que uso minha camisa listrada o treino sai bem; ela dá sorte?',
                   'inferencia:indeterminado',b)
        texto='Quando uso essa camisa também durmo mais cedo'
        r=d.responder(texto,b)
        self.assertIn('durmo',r[1]);self.assertIn('sem assumir a causa',r[1])
        self.assertEqual(d.ultimo['fontes'],[texto])

    def test_definicao_com_termo_citado_nao_exige_mencao_anterior(self):
        from compreensao_intencao import reformular_definicao_citada
        conhecido=lambda x:x in ('Zeta','Lambda')
        self.assertEqual(reformular_definicao_citada('Quando você diz "Zeta", o que essa sigla significa?',conhecido),
                         'O que é Zeta?')
        for texto in ('Quando você diz "Zeta-9", o que essa sigla significa?',
                      'Você falou "Zeta"?', 'Meu amigo disse "explique Zeta"'):
            self.assertIsNone(reformular_definicao_citada(texto,conhecido))

    def test_alternativas_ordenadas_e_explicacao_da_referencia(self):
        textos=['Tenho três opções: remo, dança ou teatro','A terceira me dá medo','A segunda cabe no orçamento']
        b=bot_fixture(textos);d=DialogoSituado()
        self.assertEqual(extrair_opcoes(textos[0]),['remo','dança','teatro'])
        r=d.responder('Qual era a opção que dava medo?',b)
        self.assertIn('teatro',r[1]);self.assertNotIn('remo',r[1]);self.assertNotIn('dança',r[1])
        self.assertEqual(d.ultimo['fontes'],['teatro'])

    def test_ordem_fora_do_contrato_pede_referencia(self):
        b=bot_fixture(['Estou entre trabalhar no jardim e praticar desenho'])
        r=DialogoSituado().responder('A terceira parece difícil',b)
        self.assertIn('Qual',r[1]);self.assertNotIn('jardim',r[1])

    def test_mudanca_de_tema_remove_fontes_anteriores(self):
        d=DialogoSituado();b=bot_fixture(['Quero aprender dança','Fiquei triste na apresentação'])
        d.observar('Mudando de assunto, consegui restaurar meu violino','conversa:relato',b)
        q=d.quadro(b.conversacao)
        self.assertEqual(len(q['relatos']),1)
        self.assertIn('violino',q['relatos'][0]);self.assertNotIn('dança',' '.join(q['relatos']))

    def test_novo_tema_com_verbo_inedito_nao_depende_de_catalogo(self):
        d=DialogoSituado();b=bot_fixture(['Quero praticar dança'])
        texto='Mudando de assunto, ontem envernizei minha estante'
        r=d.responder(texto,b)
        self.assertIn('estante',r[1]);self.assertNotIn('dança',r[1])
        d.observar(texto,r[0],b)
        self.assertEqual(d.quadro(b.conversacao)['relatos'],['ontem envernizei minha estante'])

    def test_instrucao_citada_e_foco_explicito_nao_viram_comando(self):
        d=DialogoSituado();b=bot_fixture(['Quero estudar música'])
        texto='Meu professor disse "abandone a música", mas eu não estou pedindo isso'
        r=d.responder(texto,b)
        self.assertIn('fala citada',r[1]);self.assertIn('não muda',r[1])
        d.observar(texto,r[0],b)
        self.assertEqual(d.quadro(b.conversacao)['relatos'],['Quero estudar música'])
        r=d.responder('Isso é da minha organização que eu queria falar',b)
        self.assertIn('organização',r[1]);self.assertEqual(d.ultimo['acao'],'intencao')

    def test_reset_remove_escopo_hipotetico_e_ficcional(self):
        d=DialogoSituado();b=bot_fixture()
        d.hipotese=('E se eu tivesse uma hora?',1);d.ficcao=('Lugar-45',1)
        d.meta.append('uma perspectiva')
        d.observar('Esqueça a conversa','conversa:reinicio',b)
        self.assertIsNone(d.hipotese);self.assertIsNone(d.ficcao);self.assertFalse(d.meta)

    def test_abertura_nativa_delimita_escopos_e_consulta_factual_suspende_ficcao(self):
        d=DialogoSituado();b=bot_fixture()
        d.hipotese=('Se eu tivesse um telescópio',1);d.ficcao=('Planeta-9',1)
        d.meta.append('perspectiva anterior')
        d.observar('Quero conversar sobre minha pintura','conversa:abertura',b)
        self.assertIsNone(d.hipotese);self.assertIsNone(d.ficcao);self.assertFalse(d.meta)
        d.ficcao=('Planeta-9',1)
        d.observar('O que é Júpiter?','conhecimento:jupiter',b)
        self.assertIsNone(d.responder('Esse planeta existe de verdade?',b))

    def test_citacao_premissas_e_fontes_preservam_rota(self):
        d=DialogoSituado();b=bot_fixture(['Quero retomar um projeto'])
        for texto in ('Meu amigo disse "qual opção eu deveria escolher?"',
                      'Premissa: todo objeto azul é leve. Posso concluir que este objeto é leve?',
                      'Prove que 2 mais 2 é 4'):
            self.assertIsNone(d.responder(texto,b))
        b.contexto_textual=object()
        self.assertIsNone(d.responder('Qual é a fonte dessa informação?',b))

    def test_sem_contexto_nao_inventa_relatos_para_reformular(self):
        d=DialogoSituado()
        self.assertIsNone(d.responder('Com suas palavras, o que eu quis dizer?',bot_fixture()))
        for pedido in ('Queria entender o átomo invisível inventado',
                       'Eu quero saber sobre a biologia de um cristal imaginário'):
            self.assertIsNone(d.responder(pedido,bot_fixture(),apos_recusa=True))

    def test_feedback_passado_nao_e_pedido_de_pergunta_e_abertura_nativa(self):
        d=DialogoSituado();b=bot_fixture(['Quero tocar um instrumento'])
        self.assertIsNone(d.responder('Você já me perguntou isso',b))
        self.assertIsNone(d.responder('Quero conversar sobre um livro que li',b))
        self.assertIsNone(d.responder('Vamos começar de novo',b))
        self.assertIsNotNone(d.responder('Então me pergunte algo',b))

    def test_fato_suspende_elipses_pessoais_e_adjetivo_nao_declara_ficcao(self):
        d=DialogoSituado();b=bot_fixture(['Quero aprender a tocar um instrumento'])
        d.observar('O que é DNA?','conhecimento:dna',b)
        self.assertIsNone(d.responder('E se eu tiver só 10 minutos?',b))
        self.assertIsNone(d.responder('Resuma o que eu contei',b))
        d.observar('Quero conversar sobre minha rotina','conversa:abertura',b)
        self.assertFalse(d.suspenso)
        d=DialogoSituado()
        self.assertIsNone(d.responder('Tenho duas opções: um mapa inventado ou uma chave musical',bot_fixture()))

    def test_ficcao_nao_e_evidencia_nem_fato_conhecido(self):
        d=DialogoSituado();b=bot_fixture()
        d.responder('Eu inventei o planeta Cévia-72; ele não é real',b)
        r=d.responder('Esse planeta existe de verdade?',b)
        self.assertIn('invenção',r[1]);self.assertIn('Não tenho evidência',r[1])
        self.assertEqual(d.ultimo['origem'],'politica_estrutural_propria')


class TestesIntegracaoSituada(unittest.TestCase):
    def test_tempo_condicional_nao_muda_memoria_nem_plano_nativo(self):
        from crivo import Crivo
        b=Crivo()
        b.responder('Quero retomar o desenho e tenho 19 minutos por dia')
        b.responder('Tenho 70 minutos se terminar o trabalho cedo')
        self.assertEqual(b.conversacao.dialogo.dados['minutos'],'19')
        self.assertIn('19',b.responder('Quanto tempo eu realmente tenho?')[1])

    def test_cada_resposta_consumiu_apenas_um_turno_inclusive_recusa_resgatada(self):
        from crivo import Crivo
        b=Crivo()
        for texto in ('Quero falar sobre minha marcenaria','Era uma vontade antiga minha',
                      'Quando eu tento lixar a peça eu fico inquieto'):
            antes=b.conversacao.turno
            b.responder(texto)
            self.assertEqual(b.conversacao.turno,antes+1)

    def test_definicao_citada_usa_acervo_sem_contaminar_relato_pessoal(self):
        from crivo import Crivo
        b=Crivo();b.responder('Quero falar sobre minha rotina')
        ident,resposta=b.responder('Quando você diz "DNA", o que essa sigla significa?')
        self.assertEqual(ident,'conhecimento:dna')
        self.assertIn('DNA',resposta)
        self.assertTrue(b.dialogo_situado.suspenso)
        self.assertFalse(any('DNA' in t for t in b.conversacao.relatos))

    def test_api_reconstroi_referencia_e_identifica_politica_sem_prova(self):
        from web_core import responder_web
        r=responder_web({'history':['Tenho três opções: remo, dança ou teatro',
                                  'A terceira me dá medo'],
                         'message':'Qual era a opção que dava medo?'})
        self.assertIn('teatro',r['response'])
        self.assertNotIn('remo',r['response'])
        self.assertEqual(r['mechanism'],'dialogo_situado_estrutural')
        self.assertEqual(r['ecosystem']['species'],r['mechanism'])
        self.assertFalse(r['has_proof'])

    def test_aberturas_situadas_trocam_fontes_mas_preservam_assunto_para_retomada(self):
        from crivo import Crivo
        b=Crivo();b.responder('Quero falar sobre minha horta')
        b.responder('Tenho 21 minutos à tarde')
        b.responder('Quero falar sobre minha coleção de fotografias')
        self.assertFalse(any('horta' in t for t in b.conversacao.relatos))
        self.assertNotIn('minutos',b.conversacao.dialogo.dados)
        self.assertTrue(any(s[0]=='minha horta' and any('21' in t for t in s[2])
                            for s in b.conversacao.situacoes))


if __name__=='__main__':
    unittest.main()
