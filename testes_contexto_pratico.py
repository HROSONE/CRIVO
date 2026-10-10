"""Regressões semânticas: hipótese, correção, retomada e fidelidade a quantidades."""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from crivo import Crivo
from orientacao_pratica import rotear,executar,conferir
from dialogo_situado import minutos_declarados

class TestesContextoPratico(unittest.TestCase):
    def test_tempo_por_extenso_nao_aprende_crenca_citacao_ou_hipotese(self):
        self.assertEqual('15',minutos_declarados('Tenho quinze minutos por dia.'))
        self.assertEqual('20',minutos_declarados('Quero estudar matemática e tenho vinte minutos.'))
        for t in ['Se eu tenho quinze minutos, por onde começo?', 'Acho que tenho quinze minutos.', 'Ela disse: "Tenho quinze minutos".', 'Quero estudar matemática e se tenho vinte minutos, começo?']:
            self.assertIsNone(minutos_declarados(t))
        b=Crivo();b.responder('Quero estudar frações e tenho 17 minutos.')
        b.responder('Se eu tiver vinte minutos, me dê uma atividade para começar.')
        self.assertIn('17 minutos',b.responder('Quanto tempo eu disse que tinha?')[1])
        b.responder('Não tenho tempo agora.')
        self.assertIn('não informou quanto tempo',b.responder('Quanto tempo eu disse que tinha?')[1])

    def test_retomada_recupera_exercicio_em_vez_do_desenho(self):
        b=Crivo();b.responder('Quero estudar frações e tenho 13 minutos.')
        b.responder('Pode dar um exemplo de 4/9 + 1/6?')
        b.responder('Agora quero desenhar um passarinho com lápis.')
        b.responder('Desenhei o corpo. O que faço depois?')
        b.responder('Não quero mais desenhar. Quero voltar às frações.')
        _,r=b.responder('Pode dar um exemplo?')
        self.assertIn('11/18',r);self.assertIn('13 minutos',r);self.assertNotIn('passarinho',r)
        _,resumo=b.responder('Quanto tempo eu disse que tinha?')
        self.assertNotIn('Você pediu uma explicação',resumo)
        b=Crivo();b.responder('Quero desenhar um peixe.')
        self.assertIsNone(rotear('Quero voltar às frações.',b))
        b=Crivo();b.responder('Quero estudar matemática.')
        self.assertIsNone(rotear('Quero voltar às frações.',b))

    def test_guarda_recusa_tempo_e_vasos_inventados(self):
        b=Crivo();b.responder('Quero começar uma horta no pátio.')
        b.responder('Tenho dois vasos. Por onde começo?')
        rota=rotear('Me dê uma ação concreta.',b);(_,r),_=executar(rota)
        self.assertTrue(conferir(rota,r)['aceita'])
        self.assertFalse(conferir(rota,r.replace('dois vasos','quatro vasos'))['aceita'])
        self.assertFalse(conferir(rota,r+' Você tem vinte minutos.')['aceita'])
        b=Crivo();b.responder('Quero estudar frações e tenho 13 minutos.')
        rota=rotear('Pode dar um exemplo?',b);(_,r),_=executar(rota)
        self.assertFalse(conferir(rota,r.replace('13 minutos','15 minutos'))['aceita'])

    def test_horta_observada_nao_e_substituida_pela_sombra_condicional(self):
        b=Crivo();b.responder('Quero começar uma horta no pátio.')
        b.responder('Observei: o local recebe sol de manhã.')
        b.responder('Tenho dois vasos.')
        b.responder('Se eu tiver cinco vasos, muda alguma coisa?')
        b.responder('E se eu tiver apenas sombra?')
        _,r=b.responder('Qual informação ainda está faltando?')
        self.assertIn('sol de manhã',r);self.assertFalse(b.ultima_rota_natural['hipotese'])
        self.assertEqual('sol de manhã',b.ultima_rota_natural['luz'])
        self.assertEqual('dois vasos',b.ultima_rota_natural['vasos'])
        b.responder('Não tenho dois vasos.')
        b.responder('Qual informação ainda está faltando?')
        self.assertIsNone(b.ultima_rota_natural['vasos'])
        self.assertNotIn('plante',r)

    def test_objetivo_e_restricoes_nao_se_tornam_tarefa_generica(self):
        b=Crivo();b.responder('Quero estudar matemática e tenho vinte minutos.')
        self.assertEqual('estudar matemática',b.ultima_rota_natural['objetivo'])
        b.responder('Tenho dificuldade em frações.')
        self.assertIn('vinte minutos',b.responder('Me dê uma atividade para começar.')[1])
        self.assertIsNone(rotear('Tenho saudade da minha avó.',b))
        b.responder('Agora quero organizar uma viagem.')
        self.assertIsNone(rotear('Como começo?',b))

    def test_forma_singular_e_local_novo_nao_viram_dados_de_outro_exemplo(self):
        b=Crivo();b.responder('Quero desenhar uma bicicleta com caneta.')
        _,r=b.responder('Fiz um círculo. O que faço depois?')
        self.assertNotIn('esses dois círculos',r);self.assertIn('Se essa forma',r)
        b=Crivo();b.responder('Quero começar uma horta no pátio.')
        _,r=b.responder('O que eu deveria fazer amanhã?')
        self.assertIn('pátio',r);self.assertNotIn('terraço',r)

    def test_corpus_congelado_e_checkpoint_aprovado_intactos(self):
        h=Path(__file__).parent/'experimentos/contexto_pratico_20261010'
        self.assertEqual(40,sum(len(s['turnos']) for s in json.loads((h/'sondas.json').read_text())['sessoes']))
        for f,sha in [('sondas.json','SHA256'),('criterios.json','SHA256-criterios')]:
            self.assertEqual((h/sha).read_text().split()[0],hashlib.sha256((h/f).read_bytes()).hexdigest())
        self.assertEqual('4e5894e2fe4a23bab63cb3a6b8a69da023a2b07b43829a7e706e6528bd1e780d',hashlib.sha256((h.parent/'diversidade_dialogo_20261010/checkpoint_base_133.json.gz').read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()
