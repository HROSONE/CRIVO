"""Orientação em variações inéditas, correções e mudanças de tarefa."""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from crivo import Crivo
from orientacao_pratica import conferir, executar, rotear
from web_core import responder_web

class TestesOrientacaoPratica(unittest.TestCase):
    def test_desenho_preserva_restricao_material_forma_relato_e_correcao(self):
        b=Crivo();b.responder('Quero desenhar um peixe dourado com caneta.')
        b.responder('Não tenho borracha. Como começo?')
        _,r=b.responder('Fiz um oval. O que faço agora?')
        self.assertIn('oval',r);self.assertNotIn('círculo',r)
        _,r=b.responder('Errei a cauda. Como corrijo?')
        self.assertIn('sem apagar',r);self.assertNotIn('apague',r)
        self.assertTrue(b.ultima_rota_natural['guarda']['aceita'])
        b.responder('Agora tenho uma borracha.')
        _,r=b.responder('Errei a cauda. Como corrijo?')
        self.assertIn('apague',r)

    def test_declaracao_e_pergunta_no_mesmo_turno_preservam_tempo_e_objetivo(self):
        b=Crivo();_,r=b.responder('Quero desenhar um peixe prateado. Só tenho cinco minutos. Como começo?')
        self.assertIn('peixe prateado',r);self.assertIn('cinco minutos',r)
        self.assertEqual('orientacao',b.ultima_rota_natural['peca'])

    def test_fracoes_verifica_expressao_inedita_reformula_e_corrige_resposta(self):
        b=Crivo();b.responder('Quero estudar frações.')
        _,r=b.responder('Pode dar um exemplo de 2/5 + 1/3?')
        self.assertIn('11/15',r)
        primeira=r
        _,r=b.responder('Não entendi. Explique de outro jeito.')
        self.assertNotEqual(primeira,r);self.assertIn('partes',r);self.assertIn('11/15',r)
        _,r=b.responder('Deu 2/3. Está certo?')
        self.assertIn('não confere',r);self.assertIn('11/15',r)
        _,r=b.responder('Deu 11/15. Está certo?')
        self.assertIn('correta',r)
        _,r=b.responder('Qual é a fonte?')
        self.assertIn('cálculo exato',r);self.assertNotIn('http',r)
        self.assertFalse(b.dialogo_conversa.trace['usada'])

    def test_resultado_sem_exercicio_e_assunto_desconhecido_exigem_esclarecimento(self):
        b=Crivo();b.responder('Quero organizar meus estudos de matemática.')
        _,r=b.responder('Me dê uma atividade para começar.')
        self.assertIn('qual tópico',r);self.assertNotIn('1/2',r)
        b=Crivo();b.responder('Quero estudar frações.')
        _,r=b.responder('Deu 7/9. Está certo?')
        self.assertIn('qual exercício',r);self.assertNotIn('não confere',r)

    def test_horta_nao_inventa_condicoes_e_hipotese_nao_vira_observacao(self):
        b=Crivo();b.responder('Quero começar uma horta no meu terraço.')
        b.responder('Tenho três vasos vazios. Por onde começo?')
        _,r=b.responder('E se não tiver sol?')
        self.assertIn('hipótese',r);self.assertIn('luz',r);self.assertNotIn('plante',r)
        self.assertNotIn('varanda',r);self.assertIn('terraço',r)
        self.assertTrue(b.ultima_rota_natural['quadro_pratico']['hipotese'])
        _,r=b.responder('O que você ainda precisa saber para me orientar?')
        self.assertIn('espaço',r);self.assertIn('três vasos',r)
        self.assertNotIn('Você não tem sol',r)
        self.assertFalse(b.ultima_rota_natural['quadro_pratico']['hipotese'])

    def test_fato_calculo_memoria_e_historia_tem_prioridade_e_suspende_tarefa_antiga(self):
        b=Crivo();b.responder('Quero desenhar um peixe prateado.')
        ident,r=b.responder('O que é diferença de potencial?')
        self.assertTrue(ident.startswith('conhecimento:'));self.assertFalse(b.dialogo_conversa.trace['usada'])
        b.responder('Pode dar um exemplo?')
        self.assertNotEqual('orientacao',(b.ultima_rota_natural or {}).get('peca'))
        b=Crivo();b.responder('Quero desenhar um peixe prateado.')
        b.responder('Minha prima Jovrélia gosta de cajá.')
        _,r=b.responder('O que minha prima gosta?')
        self.assertIn('cajá',r);self.assertEqual('memoria',b.ultima_rota_natural['peca'])
        b=Crivo();b.responder('Quero desenhar um peixe prateado.')
        _,r=b.responder('Conte uma história sobre uma anta mensageira.')
        self.assertTrue(b.dialogo_conversa.trace['usada']);self.assertIn('anta mensageira',r)
        b.responder('E agora?')
        self.assertNotEqual('orientacao',(b.ultima_rota_natural or {}).get('peca'))

    def test_cancelamento_citacao_objetivo_desconhecido_e_mudanca_de_objetivo(self):
        b=Crivo();self.assertIsNone(rotear('Como começo?',b))
        b.responder('Ele disse: "Quero desenhar um peixe".')
        self.assertIsNone(rotear('Como começo?',b))
        b=Crivo();b.responder('Quero desenhar um peixe prateado.')
        self.assertIsNone(rotear('Não quero desenhar. Como começo?',b))
        b.responder('Não quero desenhar mais.')
        self.assertIsNone(rotear('E agora?',b))
        b=Crivo();b.responder('Quero desenhar um peixe prateado.')
        b.responder('O que é uma zorbélula inexistente?')
        self.assertIsNone(rotear('E agora?',b))
        b=Crivo();b.responder('Quero desenhar um peixe prateado.')
        b.responder('Agora quero organizar uma viagem.')
        self.assertIsNone(rotear('Como começo?',b))

    def test_guarda_rejeita_troca_de_objetivo_material_e_calculo_adulterado(self):
        b=Crivo();b.responder('Quero estudar frações.')
        rota=rotear('Pode dar um exemplo de 2/5 + 1/3?',b)
        (_,r),_=executar(rota)
        self.assertTrue(conferir(rota,r)['aceita'])
        adulterada=copy.deepcopy(rota);adulterada['quadro_pratico']['calculo']['denominador']=10
        self.assertFalse(conferir(adulterada,r)['aceita'])
        self.assertFalse(conferir(rota,r.replace('2/5 vira 6/15','2/5 vira 6/10'))['aceita'])
        self.assertFalse(conferir(rota,'Vamos preparar arroz.')['aceita'])
        b=Crivo();b.responder('Quero desenhar um peixe com caneta.')
        b.responder('Não tenho borracha.')
        rota=rotear('Errei a cauda. Como corrijo?',b)
        self.assertFalse(conferir(rota,'Para '+rota['objetivo']+', apague a cauda.')['aceita'])

    def test_http_replay_e_pesos_e_casos_anteriores_intactos(self):
        r=responder_web({'message':'Não sei desenhar. Qual é o primeiro traço?',
                         'history':['Quero desenhar um peixe prateado.','Só tenho cinco minutos. Como começo?']})
        self.assertEqual('orientacao',r['natural_routing']['peca'])
        self.assertTrue(r['natural_routing']['guarda']['aceita'])
        self.assertIn('oval',r['response']);self.assertIn('cinco minutos',r['response'])
        self.assertFalse(r['dialogue_generation']['usada'])
        raiz=Path(__file__).parent;h=raiz/'experimentos/orientacao_pratica_20261010'
        antigo=json.loads((raiz/'experimentos/dialogo_continuidade_20261010/casos_congelados.json').read_text())['casos']
        self.assertEqual(antigo,json.loads((h/'casos_congelados.json').read_text())['casos'][:61])
        self.assertEqual('0873ad29e80433d8ff032231302e70654b0f479f09627f7d04f7d0511d57c382',hashlib.sha256((raiz/'rede_dialogo_conversa.json.gz').read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()
