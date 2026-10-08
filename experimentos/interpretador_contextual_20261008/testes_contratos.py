"""Contratos semânticos independentes do corpus e roundtrip de fontes."""
import unittest
from decimal import Decimal
from modelo import executar, recuperar


def proposta(op, textos, ref=None):
    xs=[{'turno':i,'inicio':0,'fim':len(t),'texto':t} if t is not None else None for i,t in enumerate(textos)]
    return {'operacao':op,'argumentos':xs+[None]*(3-len(xs)),
            'referente':{'texto':ref} if ref else None,'hipotese':False}


class Contratos(unittest.TestCase):
    def test_decimal_sem_arredondamento_binario(self):
        r=executar(proposta('comparar_custos',['0,10','0,30']))
        self.assertEqual([Decimal(x) for x in r['resultado']['totais']], [Decimal('0.1'),Decimal('0.3')])
        self.assertEqual(Decimal(r['resultado']['diferenca']), Decimal('0.2'))
        self.assertEqual(r['resultado']['menor'], 0)

    def test_composicao_temporal_com_deficit(self):
        r=executar(proposta('tempo_restante',['15','11','7']))
        self.assertEqual(r['resultado'],{'disponivel':15,'gasto':18,'restante':-3})

    def test_ausencia_nao_e_negacao(self):
        r=executar(proposta('verificar_requisitos',['chave e selo','tem selo']))
        self.assertEqual(r['resultado']['status'],'indeterminado')
        r=executar(proposta('verificar_requisitos',['chave e selo','tem selo e não tem chave']))
        self.assertEqual(r['resultado']['status'],'refutado')

    def test_posse_contraditoria_preservada(self):
        r=executar(proposta('verificar_requisitos',['selo','tem selo e não tem selo']))
        self.assertEqual(r['resultado']['status'],'contraditorio')

    def test_rejeita_numero_misturado_com_texto(self):
        self.assertFalse(executar(proposta('comparar_custos',['10 reais','20']))['executavel'])

    def test_rejeita_codigo_como_argumento(self):
        self.assertFalse(executar(proposta('tempo_restante',["__import__('os')",'20']))['executavel'])

    def test_consulta_precisa_de_referente(self):
        self.assertFalse(executar(proposta('consultar_valor',['20']))['executavel'])

    def test_fonte_nao_pode_atravessar_turnos(self):
        item={'ids':[0,1,2,3], 'offsets':[(0,0,1),None,(1,0,1),None],
              'exemplo':{'turnos':['a','b']}}
        self.assertTrue(recuperar(item,0,2)['invalido'])
        self.assertIsNone(recuperar(item,3,3))


if __name__=='__main__':unittest.main()
