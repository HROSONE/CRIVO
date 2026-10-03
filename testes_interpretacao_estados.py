import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from interpretacao_estados import analisar,executar,javascript,sintetizar
from rede_efeitos import dados,particao,features


class InterpretacaoTestes(unittest.TestCase):
    def test_precedencia_e_estado(self):
        r=executar('let saldo = entrada + 2 - 1; saldo -= 3; return saldo;',10)
        self.assertEqual(r['resultado'],8)
        estados=[x for x in r['tracos'] if x['tipo']=='estado']
        self.assertEqual(estados[0]['antes'],{'entrada':10})
        self.assertEqual(estados[0]['depois']['saldo'],11)
        self.assertEqual(estados[1]['depois']['saldo'],8)
        self.assertEqual(executar('return -entrada + 3;',2)['resultado'],1)

    def test_condicao_laco_e_comparacao_exata(self):
        codigo='let n = entrada; while (n < 3) { n += 1; } if (n === 3) { return 1; } else { return 0; }'
        self.assertEqual(executar(codigo,0)['resultado'],1)
        self.assertEqual(executar(codigo,5)['resultado'],0)
        self.assertIs(executar('return entrada === 2;',2)['resultado'],True)

    def test_sem_apis_host_e_limites(self):
        for c in ('import fs from "fs";','return process.exit();','return eval(entrada);','return entrada[0];','return entrada * 3;'):
            with self.subTest(c=c),self.assertRaises(ValueError):analisar(c)
        for c in ('while (entrada === 0) { } return 1;','return 999;','return inexistente;','const n = 0; n = 1; return n;',
                  'entrada = 1; return entrada;','let n = 1; let n = 2; return n;','if (entrada) {return 1;} return 0;','let n=1;'):
            with self.subTest(c=c),self.assertRaises(ValueError):executar(c,0)
        with self.assertRaises(ValueError):executar('return entrada;',True)
        with self.assertRaises(ValueError):executar('return entrada;',65)

    def test_neural_sem_fallback_oraculo(self):
        with patch('interpretacao_estados.efeito_exato',side_effect=AssertionError('Oráculo acessado')):
            r=executar('let x = entrada + 2; return x;',1,previsor=lambda op,a,b:7)
        self.assertEqual(r['resultado'],7)
        self.assertEqual(r['tracos'][0]['origem'],'rede')

    def test_dados_reservados_e_reversoes(self):
        rs=dados();self.assertEqual(len(rs),1156)
        self.assertEqual({r['split'] for r in rs},{'treino','validacao','teste'})
        for r in rs:self.assertEqual(r['split'],particao(r['op'],r['b'],r['a']))
        with self.assertRaises(ValueError):features('+',9,0)

    def test_sintese_e_casos_ambiguos(self):
        r=sintetizar([dict(entrada=x,saida=x+2) for x in (-2,0,3)])
        self.assertIsNotNone(r['codigo'])
        self.assertEqual(executar(r['corpo'],-4)['resultado'],-2)
        self.assertIn('function resolver(entrada)',r['codigo'])
        self.assertIn('entrada: number',javascript('return entrada;',typescript=True))
        # Contrato contraditório não produz uma solução; bool não é inteiro.
        self.assertIsNone(sintetizar([dict(entrada=1,saida=True),dict(entrada=1,saida=1)])['codigo'])
        with self.assertRaises(ValueError):sintetizar([])
        with self.assertRaises(ValueError):sintetizar([dict(entrada=True,saida=1)])
        with self.assertRaises(ValueError):executar([('retornar',('num',1))],0)


@unittest.skipUnless(importlib.util.find_spec('numpy'),'NumPy opcional ausente')
class RedeTestes(unittest.TestCase):
    def test_gradiente_numerico(self):
        import numpy as np
        from rede_efeitos import RedeEfeitos
        r=RedeEfeitos(ocultas=4);x=np.asarray([features('+',1,2),features('<',2,1)]);y=np.asarray([3,0])
        _,gs=r.perda_gradientes(x,y)
        for p,g,indice in ((r.w1,gs[0],(0,1)),(r.b1,gs[1],(2,)),(r.w2,gs[2],(1,0)),(r.b2,gs[3],(0,)),(r.wn,gs[4],(2,))):
            original=p[indice];h=1e-5
            p[indice]=original+h;a=r.perda_gradientes(x,y)[0]
            p[indice]=original-h;b=r.perda_gradientes(x,y)[0];p[indice]=original
            self.assertAlmostEqual(float(g[indice]),(a-b)/(2*h),places=7)

    def test_aprendizado_persistencia_e_particoes(self):
        import numpy as np
        from rede_efeitos import RedeEfeitos
        rs=[r for r in dados() if r['split']=='treino'];r=RedeEfeitos(ocultas=16)
        x=np.asarray([features(t['op'],t['a'],t['b']) for t in rs]);y=np.asarray([int(t['resultado']) for t in rs])
        antes=r.perda_gradientes(x,y)[0];r.treinar(rs,passos=100)
        self.assertLess(r.perda_gradientes(x,y)[0],antes)
        with self.assertRaises(ValueError):r.treinar([next(t for t in dados() if t['split']=='teste')],passos=1)
        with tempfile.TemporaryDirectory() as d:
            r.salvar(d);out=RedeEfeitos.carregar(d)
            np.testing.assert_array_equal(r.forward(x)[1],out.forward(x)[1])
            np.testing.assert_array_equal(r.wn,out.wn)
            np.savez(Path(d)/'rede.npz',w1=np.zeros((1,1)),b1=r.b1,w2=r.w2,b2=r.b2)
            with self.assertRaises(ValueError):RedeEfeitos.carregar(d)
