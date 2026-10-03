import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from interpretacao_estruturas import executar,analisar,validar_valor
from busca_estados import buscar_com_reparo,candidatos


class EstruturasTestes(unittest.TestCase):
    def test_operadores_e_curto_circuito(self):
        self.assertEqual(executar('return entrada * -3;',4)['resultado'],-12)
        self.assertTrue(executar('return entrada >= 0 && entrada <= 2;',2)['resultado'])
        self.assertFalse(executar('return false && ausente;',2)['resultado'])
        self.assertTrue(executar('return true || ausente;',2)['resultado'])
        self.assertTrue(executar('return entrada !== 1;',2)['resultado'])

    def test_arrays_objetos_aliases_e_tracos(self):
        codigo='let a = [{x: 1}]; let obj = a[0]; obj.x = 3; let out = []; out.push(a[0].x); return out;'
        r=executar(codigo,0);self.assertEqual(r['resultado'],[3])
        self.assertEqual(r['tracos'][0]['depois']['a'],[{'x':1}])
        self.assertTrue(any(t['tipo']=='metodo_manual' for t in r['tracos']))
        entrada=[1,2];executar('let xs = entrada; xs[0] = 4; return xs;',entrada)
        self.assertEqual(entrada,[1,2])
        self.assertFalse(executar('return [1].includes(true);',0)['resultado'])

    def test_ordem_dos_efeitos_na_atribuicao(self):
        codigo='let xs = [0,0,0]; let ys = []; xs[ys.push(0) - 1] += ys.push(1); return xs;'
        self.assertEqual(executar(codigo,0)['resultado'],[2,0,0])

    def test_texto_utf16_e_espacos_js(self):
        self.assertEqual(executar('return entrada.length;','💻')['resultado'],2)
        self.assertEqual(executar('return entrada.slice(1);','a💻b')['resultado'],'💻b')
        self.assertEqual(executar('return entrada.trim();','\ufeff á \u00a0')['resultado'],'á')
        self.assertEqual(executar('return entrada.trim();','\u0085x\u0085')['resultado'],'\u0085x\u0085')

    def test_limites_e_apis_bloqueadas(self):
        for c in ('return process.exit();','return entrada.constructor;','return eval(entrada);','return entrada.map(entrada);'):
            with self.subTest(c=c),self.assertRaises(ValueError):executar(c,0)
        for c,x in (('return entrada[0];',[]),('return entrada[-1];',[1]),('while (true) {} return 0;',0),('return entrada * 16;',64)):
            with self.subTest(c=c),self.assertRaises(ValueError):executar(c,x)
        with self.assertRaises(ValueError):validar_valor([0]*17)
        with self.assertRaises(ValueError):validar_valor({'__proto__':1})
        with self.assertRaises(ValueError):validar_valor(float('nan'))

    def test_rede_sem_fallback_e_limites_mutacao(self):
        with patch('interpretacao_estruturas.efeito_exato',side_effect=AssertionError('Oráculo acessado')):
            r=executar('let x = entrada + 1; return x;',1,previsor=lambda *a:7)
        self.assertEqual(r['resultado'],7)
        with self.assertRaises(ValueError):executar('let xs = entrada.slice(0); xs.push(1); return xs;',[0]*16)

    def test_reparo_sem_acesso_a_reservados(self):
        dev=[dict(entrada=0,saida=True),dict(entrada=3,saida=False)]
        extras=[dict(entrada=2,saida=True),dict(entrada=1,saida=True)]
        r=buscar_com_reparo(dev,'numero',extras,max_reparos=2)
        self.assertFalse(r['casos_reservados_consultados']);self.assertGreater(r['reparos'],0)
        self.assertTrue(r['final']['atende_desenvolvimento'])
        for c in dev+extras:self.assertEqual(executar(r['final']['corpo'],c['entrada'])['resultado'],c['saida'])
        self.assertEqual(len(dev),2)

    def test_protocolo_preserva_separadores_unicode(self):
        from verificacao_codigo import verificar,sandbox_disponivel
        if not sandbox_disponivel():self.skipTest('Runtime isolado indisponível')
        texto='\u0085x\u2028y\u2029z'
        r=verificar('function resolver(s) { return s; }','javascript',[dict(entrada=[texto],saida=texto)])
        self.assertTrue(r['funcional'],r)

    def test_v1_congelada(self):
        from scripts.experimento_estados_v2 import congelada
        self.assertEqual(congelada()['commit'],'21545b9a9270d3d4e474ce34616112a770ddb6df')
        self.assertTrue(candidatos('array'))


@unittest.skipUnless(importlib.util.find_spec('numpy'),'NumPy opcional ausente')
class RedesTestes(unittest.TestCase):
    def test_particoes_e_reversoes_nao_eliminadas(self):
        from rede_estruturas import dados,grupo,particao
        rs=dados();numericas=[r for r in rs if r['op']=='-']
        self.assertEqual(len(numericas),1089)
        r=next(r for r in numericas if r['a']==1 and r['b']==2)
        q=next(r for r in numericas if r['a']==2 and r['b']==1)
        self.assertEqual(r['split'],q['split']);self.assertNotEqual(r['resultado'],q['resultado'])
        splits={}
        for r in rs:splits.setdefault(grupo(r),set()).add(r['split'])
        self.assertTrue(all(len(s)==1 for s in splits.values()))

    def test_gradientes_tipos_e_persistencia(self):
        import numpy as np
        from rede_estruturas import RedeEstruturas,features_num,vetor_indice
        r=RedeEstruturas();x=np.asarray([features_num('<',1,2),features_num('===',1,1)]);y=np.asarray([1,1])
        _,gs=r.loss_mlp(x,y,'n')
        for k,idx in (('nw1',(0,1)),('nb1',(0,)),('nw2',(1,1)),('nb2',(0,))):
            p=r.parametros[k];old=p[idx];h=1e-5;p[idx]=old+h;a=r.loss_mlp(x,y,'n')[0];p[idx]=old-h;b=r.loss_mlp(x,y,'n')[0];p[idx]=old
            self.assertAlmostEqual(float(gs[k][idx]),(a-b)/(2*h),places=7)
        with tempfile.TemporaryDirectory() as d:
            r.salvar(d);restaurada=RedeEstruturas.carregar(d)
            for k,v in r.parametros.items():np.testing.assert_array_equal(v,restaurada.parametros[k])
        with self.assertRaises(ValueError):vetor_indice([True],0)
        with self.assertRaises(ValueError):r.prever('desconhecido',1,2)
        with self.assertRaises(ValueError):r.prever('*',17,0)

    def test_gradientes_estruturais_e_regressao(self):
        import numpy as np
        from rede_estruturas import RedeEstruturas,features_num
        r=RedeEstruturas()
        x=r.arit_features(np.asarray([features_num('+',1,2),features_num('-',4,3)]));y=np.asarray([3,1])
        xx=np.asarray([[1.]+[0.]*15,[0.,1.]+[0.]*14]);q=xx.copy();yi=np.asarray([4,-2])
        casos=[('arit',(2,),lambda:r.loss_linear(x,y,'arit')),('indice',(0,0),lambda:r.loss_indice(xx,q,yi)),('indice_bias',(0,),lambda:r.loss_indice(xx,q,yi))]
        mask=np.asarray([[1.]*3+[0.]*13+[1.],[1.]*8+[0.]*8+[1.]])
        casos.append(('comprimento',(1,),lambda:r.loss_linear(mask,np.asarray([3,8]),'comprimento')))
        for k,idx,f in casos:
            _,g=f();p=r.parametros[k];old=p[idx];h=1e-5;p[idx]=old+h;a=f()[0];p[idx]=old-h;b=f()[0];p[idx]=old
            self.assertAlmostEqual(float(g[k][idx]),(a-b)/(2*h),places=7)

    def test_multiplicacao_compoe_previsoes_sem_oraculo(self):
        from rede_estruturas import RedeEstruturas
        r=RedeEstruturas();r.parametros['arit'][:]=[0,0,1,1,1,-1]
        with patch('rede_estruturas.efeito_exato',side_effect=AssertionError('Oráculo acessado')):
            self.assertEqual(r.prever('*',-4,-3),12)


if __name__=='__main__':unittest.main()
