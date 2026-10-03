import importlib.util
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch


class ProtocoloTestes(unittest.TestCase):
    def test_baseline_v2_congelada(self):
        from scripts.experimento_precisao import congelada
        self.assertEqual(congelada()['commit'],'dbe6dbc18db71a724ce3a7a1566466ec9f19d2e4')


@unittest.skipUnless(importlib.util.find_spec('numpy'),'NumPy opcional ausente')
class PrecisaoTestes(unittest.TestCase):
    def test_cobertura_posicoes_e_arrays_reservados(self):
        from rede_precisa import dados
        from scripts.experimento_precisao import validar_reserva,BENCH
        import json,collections
        rs=dados();counts=collections.Counter(r['b'] for r in rs if r['split']=='treino' and r['op']=='indice')
        self.assertEqual(len(counts),16);self.assertGreater(counts[15],500)
        partes={}
        for r in rs:
            if r['op']=='indice':partes.setdefault(tuple(r['a']),set()).add(r['split'])
        self.assertTrue(all(len(s)==1 for s in partes.values()))
        validar_reserva(rs,json.loads(BENCH.read_text())['programas'])

    def test_gradiente_igualdade(self):
        import numpy as np
        from rede_precisa import RedePrecisa
        r=RedePrecisa();x=np.asarray([[0.,1.],[1.,1.],[9.,1.]]);y=np.asarray([1,0,0]);_,g=r.loss_igualdade(x,y)
        p=r.parametros['igualdade']
        for i in ((0,0),(0,1),(1,0),(1,1)):
            old=p[i];h=1e-5;p[i]=old+h;a=r.loss_igualdade(x,y)[0];p[i]=old-h;b=r.loss_igualdade(x,y)[0];p[i]=old
            self.assertAlmostEqual(float(g[i]),(a-b)/(2*h),places=7)

    def test_igualdade_depende_dos_pesos_sem_oraculo(self):
        from rede_precisa import RedePrecisa
        r=RedePrecisa();r.parametros['arit'][:]=[0,0,1,1,1,-1]
        r.parametros['igualdade'][:]=[[1,-1],[-.5,.5]]
        with patch('rede_precisa.efeito_exato',side_effect=AssertionError('Oráculo acessado')),patch('rede_estruturas.efeito_exato',side_effect=AssertionError('Oráculo acessado')):
            self.assertTrue(r.prever('===',2,2));self.assertFalse(r.prever('===',2,3));self.assertTrue(r.prever('!==',2,3))
            r.parametros['arit'][4:]=0
            # Se a rede de subtração erra o delta, a igualdade também pode errar.
            self.assertTrue(r.prever('===',2,3))
        with self.assertRaises(ValueError):r.prever('===',True,1)
        with self.assertRaises(ValueError):r.prever('===',17,1)

    def test_persistencia_e_separacao_formatos(self):
        import numpy as np
        from rede_precisa import RedePrecisa
        from rede_estruturas import RedeEstruturas
        r=RedePrecisa()
        with tempfile.TemporaryDirectory() as d:
            r.salvar(d);out=RedePrecisa.carregar(d)
            for k,v in r.parametros.items():np.testing.assert_array_equal(v,out.parametros[k])
            with self.assertRaises(ValueError):RedeEstruturas.carregar(d)
        with tempfile.TemporaryDirectory() as d:
            RedeEstruturas().salvar(d)
            with self.assertRaises(ValueError):RedePrecisa.carregar(d)

    def test_rejeita_particoes_e_lotes_invalidos(self):
        from rede_precisa import RedePrecisa
        r=RedePrecisa()
        with self.assertRaises(ValueError):r.treinar([dict(op='===',a=0,b=0,resultado=True,split='teste')],passos=1)
        with self.assertRaises(ValueError):r.treinar([dict(op='===',a=0,b=0,resultado=True,split='treino')],passos=1,lote=1)


if __name__=='__main__':unittest.main()
