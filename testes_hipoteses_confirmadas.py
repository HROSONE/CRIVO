"""Invariantes de escopo, fontes, confirmação e replay da conversa real."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import random
import unittest

from raciocinio_conversa import RaciocinioConversa


class TestesHipotesesConfirmadas(unittest.TestCase):
    def tempo(self):
        b=RaciocinioConversa()
        b.responder('Tenho 80 minutos. A ida leva 12 minutos e a tarefa leva 14 minutos. Quanto sobra?')
        b.responder('Se eu tivesse 32 minutos, caberia?')
        return b

    def test_consulta_usa_alternativa_sem_modificar_os_fatos(self):
        b=self.tempo();antes=(b.disponivel,deepcopy(b.tempos))
        b.responder('Quanto sobraria?')
        self.assertEqual(b.ultimo['resultado']['restante'],'6')
        self.assertTrue(b.ultimo['hipotese'])
        self.assertEqual((b.disponivel,b.tempos),antes)
        self.assertEqual(b._hipotese_pendente['turno'],2)

    def test_confirmacao_conserva_origem_literal_e_fonte_da_confirmacao(self):
        b=self.tempo();fonte=b._hipotese_pendente['fontes']['tempo:disponivel']
        texto='Confirmo essa hipótese como fato.'
        b.responder(texto)
        f=b.ultimo['fontes']['tempo:disponivel']
        self.assertEqual(f['fonte'],fonte['fonte'])
        self.assertEqual(f['turno'],2)
        self.assertEqual(f['origem'],'usuario_confirmado')
        self.assertEqual(f['confirmacao'],dict(turno=3,fonte=texto))
        self.assertFalse(b.ultimo['hipotese'])
        b.responder('Volte aos fatos.')
        self.assertEqual(b.disponivel,Decimal(32))
        self.assertEqual(b.ultimo['resultado']['restante'],'6')
        self.assertFalse(b.ultimo['hipotese'])

    def test_descarte_preserva_valor_ja_confirmado(self):
        b=self.tempo();b.responder('Confirmo essa hipótese como fato.')
        b.responder('Se eu tivesse 10 minutos, caberia?')
        b.responder('Descarte essa hipótese.')
        self.assertEqual(b.ultimo['resultado']['restante'],'6')
        self.assertEqual(b.disponivel,Decimal(32))
        self.assertIsNone(b._hipotese_pendente)

    def test_nova_hipotese_parte_dos_fatos_e_nao_da_alternativa(self):
        b=RaciocinioConversa()
        b.responder('O curso custa 48 reais. O livro custa 39 reais mais 12 de frete. Qual custa menos?')
        b.responder('Se o frete fosse 3 reais, qual seria menor?')
        b.responder('Se o livro fosse 4 reais, qual seria menor?')
        self.assertEqual(b.ultimo['resultado']['totais'],['48','16'])
        b.responder('Confirmo essa hipótese como fato.')
        self.assertEqual(b.custos[1]['componentes'],dict(livro=Decimal(4),frete=Decimal(12)))

    def test_confirmacao_de_um_dominio_preserva_os_outros(self):
        b=self.tempo();b.responder('Descarte essa hipótese.')
        b.responder('O curso custa 48 reais. O livro custa 39 reais mais 12 de frete. Qual custa menos?')
        b.responder('Se o frete fosse 3 reais, qual seria menor?')
        b.responder('Confirmo essa hipótese como fato.')
        self.assertEqual(b.disponivel,Decimal(80))
        self.assertEqual(b.tempos,dict(ida=Decimal(12),tarefa=Decimal(14)))
        self.assertEqual(b.fontes['tempo:disponivel']['origem'],'usuario')

    def test_correcao_real_encerra_hipotese_sem_aplicar_valores_antigos(self):
        b=self.tempo();b.responder('Tenho 45 minutos. Quanto sobra?')
        self.assertEqual(b.disponivel,Decimal(45))
        self.assertIsNone(b._hipotese_pendente)
        b.responder('Confirmo essa hipótese como fato.')
        self.assertEqual(b.ultimo['status'],'incompleto')
        self.assertEqual(b.disponivel,Decimal(45))

    def test_consulta_factual_descarta_a_alternativa(self):
        b=self.tempo();b.responder('Quanto tempo real sobra?')
        self.assertFalse(b.ultimo['hipotese'])
        self.assertEqual(b.ultimo['resultado']['restante'],'54')
        self.assertIsNone(b._hipotese_pendente)

    def test_confirmacao_sem_hipotese_nao_inventa_dado(self):
        b=RaciocinioConversa()
        b.responder('Confirmo essa hipótese como fato.')
        self.assertEqual(b.ultimo['status'],'incompleto')
        self.assertIsNone(b.disponivel)
        self.assertFalse(b.custos)
        self.assertFalse(b.ultimo['fontes'])

    def test_sim_negacao_citacao_e_pergunta_nao_confirmam(self):
        for texto in ['Sim.', 'Confirmado.', 'Não confirme essa hipótese.',
                      '"Confirmo essa hipótese como fato."',
                      'Confirmo essa hipótese como fato?',
                      'Acho que confirmo essa hipótese como fato.',
                      'Você confirma essa hipótese?']:
            with self.subTest(texto=texto):
                b=self.tempo();pendente=deepcopy(b._hipotese_pendente)
                b.responder(texto)
                self.assertEqual(b.disponivel,Decimal(80))
                self.assertEqual(b._hipotese_pendente,pendente)

    def test_hipotese_ambigua_nao_deixa_confirmar_a_anterior(self):
        b=RaciocinioConversa()
        b.responder('O curso custa 48 reais. O livro custa 39 reais mais 12 de frete. Qual custa menos?')
        b.responder('Se o frete fosse 3 reais, qual seria menor?')
        b.responder('Se o transporte fosse 8 reais, qual seria menor?')
        self.assertEqual(b.ultimo['status'],'ambiguo')
        b.responder('Confirmo essa hipótese como fato.')
        self.assertEqual(b.ultimo['status'],'incompleto')
        self.assertEqual(b.custos[1]['componentes']['frete'],Decimal(12))

    def test_condicional_fora_da_gramatica_nao_confirma_cenario_antigo(self):
        b=self.tempo()
        b.responder('Se a ida durasse 20 minutos, caberia?')
        b.responder('Confirmo essa hipótese como fato.')
        self.assertEqual(b.ultimo['status'],'incompleto')
        self.assertEqual(b.disponivel,Decimal(80))

    def test_confirmacao_nao_ressuscita_hipotese_apos_reset(self):
        b=self.tempo();b.responder('Vamos começar de novo.')
        b.responder('Confirmo essa hipótese como fato.')
        self.assertEqual(b.ultimo['status'],'incompleto')
        self.assertIsNone(b.disponivel)

    def test_sem_vazamento_entre_instancias(self):
        a=self.tempo();b=RaciocinioConversa()
        b.responder('Confirmo essa hipótese como fato.')
        self.assertIsNone(b.disponivel)
        self.assertIsNotNone(a._hipotese_pendente)

    def test_estado_limitado_sem_snapshots_recursivos(self):
        b=self.tempo()
        for n in range(100):
            b.responder('Se eu tivesse %s minutos, caberia?'%(n+1))
            b.responder('Quanto sobraria?')
        self.assertLessEqual(len(b.eventos),48)
        self.assertLessEqual(len(b.fontes),32)
        self.assertNotIn('_hipotese_pendente',b._hipotese_pendente['estado'])
        self.assertEqual(b.disponivel,Decimal(80))

    def test_invariantes_parametrizadas_de_confirmacao_e_descarte(self):
        rng=random.Random(20261009)
        for _ in range(80):
            real,hip,gasto=[rng.randrange(1,2000) for _ in range(3)]
            b=RaciocinioConversa()
            b.responder('Tenho %s minutos. A tarefa leva %s minutos. Quanto sobra?'%(real,gasto))
            b.responder('Se eu tivesse %s minutos, caberia?'%hip)
            self.assertEqual(b.disponivel,Decimal(real))
            confirmar=bool(rng.randrange(2))
            b.responder('Confirmo essa hipótese como fato.' if confirmar else 'Descarte essa hipótese.')
            self.assertEqual(b.disponivel,Decimal(hip if confirmar else real))
            b.responder('Quanto tempo real sobra?')
            self.assertEqual(Decimal(b.ultimo['resultado']['restante']),Decimal((hip if confirmar else real)-gasto))


class TestesIntegracaoHipotesesConfirmadas(unittest.TestCase):
    def test_mesmos_valores_e_fontes_no_motor_e_no_replay_web(self):
        from crivo import Crivo
        from web_core import responder_web
        path=Path(__file__).parent/'experimentos/confirmacao_hipoteses_20261009/controle.json'
        for c in json.loads(path.read_text())['sessoes']:
            with self.subTest(dominio=c['id']):
                b=Crivo(usar_linguagem_neural=False,usar_geracao=False)
                turnos=[t['texto'] for t in c['turnos'][:4]]
                for texto in turnos:b.responder(texto)
                web=responder_web(dict(message=turnos[-1],history=turnos[:-1]),usar_geracao=False)
                self.assertEqual(web['conversational_reasoning'],b.historico[-1]['raciocinio_conversa'])
                self.assertEqual(web['conversational_reasoning']['resultado'],c['turnos'][3]['resultado'])
                self.assertFalse(web['conversational_reasoning']['hipotese'])
                self.assertEqual(web['generation']['usada'],False)


class TestesHTTPHipotesesConfirmadas(unittest.TestCase):
    def test_confirmacao_atravessa_http_com_fontes_e_valor_corretos(self):
        import threading
        from urllib.request import Request, urlopen
        from web_local import criar_servidor
        server=criar_servidor('127.0.0.1',0)
        thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.02},daemon=True)
        thread.start()
        try:
            payload=dict(history=[
                'Tenho 80 minutos. A ida leva 12 minutos e a tarefa leva 14 minutos. Quanto sobra?',
                'Se eu tivesse 32 minutos, caberia?',
                'Confirmo essa hipótese como fato.',
            ],message='Quanto tempo real sobra?')
            request=Request('http://127.0.0.1:%s/api/chat'%server.server_address[1],
                            data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=20) as response:
                self.assertEqual(response.status,200)
                raw=json.loads(response.read())
            r=raw['conversational_reasoning']
            self.assertEqual(r['resultado'],dict(disponivel='32',gasto='26',restante='6'))
            self.assertFalse(r['hipotese'])
            self.assertEqual(r['fontes']['tempo:disponivel']['confirmacao']['fonte'],payload['history'][2])
        finally:
            server.shutdown();server.server_close();thread.join(timeout=5)


if __name__=='__main__':unittest.main()
