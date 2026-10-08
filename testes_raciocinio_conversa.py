"""Invariantes da memória, cálculo, negação e prova; casos de desenvolvimento."""
from copy import deepcopy
from decimal import Decimal
import unittest
from raciocinio_conversa import RaciocinioConversa


class TestesRaciocinioConversa(unittest.TestCase):
    def test_custo_composto_revisado_sem_dupla_soma(self):
        d=RaciocinioConversa()
        d.responder('A opção azul custa 41 reais. A opção verde custa 19 reais mais 7 de frete. Qual custa menos?')
        self.assertEqual(d.ultimo['resultado'],dict(totais=['41','26'],menor=1,diferenca='15'))
        d.responder('O frete subiu para 28 reais. E agora?')
        self.assertEqual(d.ultimo['resultado'],dict(totais=['41','47'],menor=0,diferenca='6'))
        antes=deepcopy(d.custos)
        d.responder('O frete subiu para 28 reais. E agora?')
        self.assertEqual(d.custos,antes)

    def test_decimal_nao_usa_float_binario(self):
        d=RaciocinioConversa()
        d.responder('A primeira custa 0,30 reais. A segunda custa 0,10 reais mais 0,20 de taxa. Empata?')
        self.assertEqual(d.ultimo['resultado'],dict(totais=['0.3','0.3'],menor=None,diferenca='0'))

    def test_hipotese_custo_e_retomada_real(self):
        d=RaciocinioConversa()
        d.responder('O curso custa 48 reais. O livro custa 39 reais mais 12 de frete. Qual é menor?')
        antes=deepcopy(d.custos)
        d.responder('Se o frete fosse 3 reais, qual seria menor?')
        self.assertTrue(d.ultimo['hipotese'])
        self.assertEqual(d.ultimo['resultado']['totais'],['48','42'])
        self.assertEqual(d.custos,antes)
        d.responder('Qual era a diferença dos custos reais?')
        self.assertEqual(d.ultimo['resultado']['diferenca'],'3')

    def test_atualizacao_ambigua_nao_escolhe_componente_arbitrario(self):
        d=RaciocinioConversa()
        d.responder('A primeira custa 55 reais. A segunda custa 25 reais mais 9 de taxa. Qual custa menos?')
        antes=deepcopy(d.custos)
        d.responder('O transporte custa 18 reais. E agora?')
        self.assertEqual(d.custos,antes)
        self.assertEqual(d.ultimo['status'],'ambiguo')

    def test_taxas_com_mesmo_nome_exigem_opcao(self):
        d=RaciocinioConversa()
        d.responder('A primeira custa 41 reais mais 3 de frete. A segunda custa 19 reais mais 7 de frete. Qual custa menos?')
        antes=deepcopy(d.custos)
        d.responder('O frete custa 10 reais. E agora?')
        self.assertEqual(d.ultimo['status'],'ambiguo')
        self.assertEqual(d.custos,antes)

    def test_duracoes_e_saldo_parametrizados(self):
        for disponivel,a,b in [(50,11,17),(29,13,16),(12,7,14),(120,41,58)]:
            d=RaciocinioConversa()
            d.responder('Tenho %s minutos. A tarefa leva %s minutos e a volta leva %s minutos. Quanto sobra?'%(disponivel,a,b))
            self.assertEqual(Decimal(d.ultimo['resultado']['restante']),Decimal(disponivel-a-b))

    def test_horas_e_hipotese_preservam_realidade(self):
        d=RaciocinioConversa()
        d.responder('Tenho 2 horas. A ida leva 48 minutos e a volta leva 49 minutos. Cabe?')
        d.responder('Se eu tivesse 1 hora, caberia?')
        self.assertEqual(d.ultimo['resultado']['restante'],'-37')
        self.assertEqual(d.disponivel,Decimal(120))

    def test_negacao_de_conhecimento_nao_vira_disponibilidade(self):
        d=RaciocinioConversa()
        d.responder('Tenho 31 minutos. A atividade leva 18 minutos. Quanto sobra?')
        for s in ['Não posso afirmar que tenho 90 minutos.', 'Tenho 50 minutos se o chefe sair cedo.',
                  'Meu amigo disse "Tenho 80 minutos. A atividade leva 2 minutos".',
                  'Acho que tenho 200 minutos.']:
            d.responder(s)
            self.assertEqual(d.disponivel,Decimal(31))
            self.assertEqual(d.tempos,{'atividade':Decimal(18)})

    def test_agendas_atualizacao_negacao_e_intersecao(self):
        d=RaciocinioConversa()
        d.responder('Nina pode segunda ou sábado. Ravi só pode sábado. Quando podemos marcar?')
        self.assertEqual(d.ultimo['resultado']['dias'],['sabado'])
        d.responder('Ravi também pode segunda. E agora?')
        self.assertEqual(d.ultimo['resultado']['dias'],['segunda','sabado'])
        d.responder('Nina não pode mais sábado. Qual dia resta?')
        self.assertEqual(d.ultimo['resultado']['dias'],['segunda'])
        d.responder('Ravi agora só pode quarta. Temos dia em comum?')
        self.assertEqual(d.ultimo['resultado']['dias'],[])

    def test_novo_participante_precisa_informar_agenda(self):
        d=RaciocinioConversa()
        d.responder('Nina pode quinta. Ravi pode quinta. Qual dia dá?')
        d.responder('Lena também participa. Quando podemos reunir?')
        self.assertEqual(d.ultimo['status'],'incompleto')
        d.responder('Lena pode quinta. E agora?')
        self.assertEqual(d.ultimo['resultado']['dias'],['quinta'])

    def test_requisito_desconhecido_nao_e_negativo(self):
        d=RaciocinioConversa()
        d.responder('Para entrar precisa de selo e chave. Ravi tem selo. Cumpre os requisitos?')
        self.assertEqual(d.ultimo['resultado']['status'],'indeterminado')
        self.assertNotIn('chave',d.posses['ravi'])
        d.responder('Ravi não tem chave. E agora?')
        self.assertEqual(d.ultimo['resultado']['status'],'refutado')
        self.assertTrue(d.ultimo['prova']['provas'])
        d.responder('Ravi ganhou chave. E agora?')
        self.assertEqual(d.ultimo['resultado']['status'],'sustentado')

    def test_ou_requer_apenas_um_item_e_nao_inventa_o_outro(self):
        d=RaciocinioConversa()
        d.responder('Para entrar precisa de selo ou chave. Ravi tem selo. Cumpre a regra?')
        self.assertEqual(d.ultimo['resultado']['status'],'sustentado')
        self.assertNotIn('chave',d.posses['ravi'])

    def test_negacao_local_nao_contamina_posse_positiva(self):
        d=RaciocinioConversa()
        d.responder('Para entrar precisa de selo ou chave. Ravi não tem chave, mas tem selo. Cumpre?')
        self.assertTrue(d.posses['ravi']['selo'])
        self.assertFalse(d.posses['ravi']['chave'])
        self.assertEqual(d.ultimo['resultado']['status'],'sustentado')

    def test_hipotese_posse_nao_apaga_negacao_real(self):
        d=RaciocinioConversa()
        d.responder('Para entrar precisa de selo e chave. Ravi tem selo, mas não tem chave. Pode entrar?')
        d.responder('Se ele recebesse uma chave, conseguiria entrar?')
        self.assertEqual(d.ultimo['resultado']['status'],'sustentado')
        self.assertFalse(d.posses['ravi']['chave'])

    def test_fontes_usuario_e_hipotese_nao_saida(self):
        d=RaciocinioConversa();s='Tenho 28 minutos. A tarefa leva 9 minutos. Quanto sobra?'
        d.responder(s)
        self.assertTrue(d.ultimo['atualizacoes'])
        self.assertEqual({e['fonte'] for e in d.eventos},{s})
        self.assertEqual({e['origem'] for e in d.eventos},{'usuario'})

    def test_reset_e_isolamento(self):
        a=RaciocinioConversa();b=RaciocinioConversa()
        a.responder('Tenho 19 minutos. A tarefa leva 8 minutos. Cabe?')
        self.assertIsNone(b.responder('Quanto tempo sobra?'))
        a.responder('Vamos começar de novo.')
        self.assertIsNone(a.responder('Quanto tempo sobra?'))

    def test_pergunta_nao_altera_fato_e_unidade_estranha_nao_vira_reais(self):
        d=RaciocinioConversa()
        d.responder('A primeira custa 49 reais. A segunda custa 36 reais. Qual custa menos?')
        antes=deepcopy(d.custos)
        d.responder('A primeira custa 100 reais?')
        self.assertEqual(d.custos,antes)
        for s in ['A primeira custa 90 dólares. E agora?','A primeira custa 30 centavos. E agora?']:
            self.assertIsNone(d.responder(s))
            self.assertEqual(d.custos,antes)

    def test_transferencia_nao_inventa_exclusividade(self):
        d=RaciocinioConversa()
        d.responder('Para entrar precisa de selo e chave. Ravi tem chave. Nina tem selo. Cumpre a regra?')
        d.responder('Ravi deu sua chave para Nina. Ela cumpre a regra?')
        self.assertEqual(d.ultimo['resultado']['status'],'sustentado')
        self.assertNotIn('chave',d.posses['ravi'])
        d.responder('Ravi tem uma chave. Nina pode quarta. Ravi pode quinta. Qual dia dá?')
        d.responder('Ravi perdeu a chave. Cumpre a regra?')
        self.assertEqual(d.ultimo['entradas']['pessoa'],'ravi')

    def test_agenda_interrogada_nao_se_torna_declaracao(self):
        d=RaciocinioConversa()
        d.responder('Nina pode segunda. Ravi pode segunda. Qual dia dá?')
        antes=deepcopy(d.agendas)
        d.responder('Nina não pode segunda?')
        self.assertEqual(d.agendas,antes)

    def test_memoria_e_tarefas_limitadas(self):
        d=RaciocinioConversa()
        for i in range(70):
            d.responder('Tenho %s minutos. A tarefa leva 8 minutos. Cabe?'%(30+i))
        self.assertLessEqual(len(d.eventos),48)
        self.assertLessEqual(len(d.tempos),6)
        self.assertLessEqual(len(d.fontes),32)

    def test_conflito_na_mesma_fala_nao_vira_prova(self):
        d=RaciocinioConversa()
        d.responder('Para entrar precisa de selo e chave. Ravi tem selo. Cumpre a regra?')
        antes=deepcopy(d.posses)
        d.responder('Ravi tem chave e não tem chave. Cumpre a regra?')
        self.assertEqual(d.ultimo['status'],'conflito')
        self.assertNotIn('prova',d.ultimo)
        self.assertEqual(d.posses,antes)


class TestesIntegracaoRaciocinioConversa(unittest.TestCase):
    def test_motor_e_web_conservam_argumentos_e_operacao(self):
        from crivo import Crivo
        from web_core import responder_web
        a='Tenho 49 minutos. A ida leva 18 minutos e a tarefa leva 14 minutos. Cabe?'
        b='A tarefa demora 23 minutos. E agora?'
        bot=Crivo(usar_linguagem_neural=False,usar_geracao=False)
        bot.responder(a);r=bot.responder(b)
        self.assertEqual(bot.historico[-1]['raciocinio_conversa']['resultado']['restante'],'8')
        web=responder_web(dict(message=b,history=[a]))
        self.assertEqual(web['conversational_reasoning']['resultado']['restante'],'8')
        self.assertEqual(web['response'],r[1])
        self.assertFalse(web['generation']['usada'])

    def test_acervo_e_formal_preservados(self):
        from crivo import Crivo
        bot=Crivo(usar_linguagem_neural=False,usar_geracao=False)
        bot.responder('Tenho 45 minutos. A tarefa leva 9 minutos. Quanto sobra?')
        ident,resp=bot.responder('O que é DNA?')
        self.assertNotEqual(ident,'conversa:raciocinio')
        self.assertNotIn('Sobram',resp)
        self.assertEqual(bot.raciocinio_conversa.disponivel,Decimal(45))


if __name__=='__main__':unittest.main()
