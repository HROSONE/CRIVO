import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from diagnostico_estados import (analisar, avaliar, comparar_efeitos, diagnosticar,
                                 executar, fonte_bloco, gerar_edicoes)


class DiagnosticoTestes(unittest.TestCase):
    def test_serializacao_preserva_alias_e_chaves_com_nomes_de_tags(self):
        fontes = [
            'let xs = [1, 2]; let ys = xs; ys[0] += 3; return xs;',
            'let o = {bin: 3, var: 4}; return o.bin + o.var;',
            'let xs = [0, 0]; let ys = []; xs[ys.push(0) - 1] += ys.push(1); return xs;',
            'if (false && entrada[9] > 0) { return 1; } else { return 2; }',
            'return "var + trim";',
        ]
        for codigo in fontes:
            canonico = fonte_bloco(analisar(codigo))
            self.assertEqual(executar(codigo, [])['resultado'], executar(canonico, [])['resultado'])
            resultado = executar(codigo, [])['resultado']
            self.assertTrue(avaliar(canonico, [{'entrada': [], 'saida': resultado}])[0]['correto'])
            gerar_edicoes(codigo, [{'entrada': [], 'saida': executar(codigo, [])['resultado']}])

    def test_insercao_corrige_loop_e_preserva_entrada(self):
        codigo = 'let total = 0; let i = 0; while (i < entrada.length) { total += entrada[i]; } return total;'
        cs = [{'entrada': [0, 0], 'saida': 0}, {'entrada': [], 'saida': 0}]
        original = copy.deepcopy(cs)
        r = diagnosticar(codigo, cs)
        self.assertIn('Orçamento', r['inicial'][0]['erro'])
        self.assertGreater(len(r['inicial'][0]['tracos']), 0)
        self.assertEqual(r['inicial'][0]['estado_final']['i'], 0)
        self.assertEqual(r['hipotese']['tipo'], 'inserir_incremento')
        self.assertEqual(executar(r['corpo_corrigido'], [8, -2, 4])['resultado'], 10)
        self.assertEqual(cs, original)
        self.assertFalse(r['casos_reservados_consultados'])

    def test_localiza_hipotese_e_recusa_promessa_de_intencao(self):
        r = diagnosticar('return entrada - 3;', [{'entrada': 2, 'saida': 5}, {'entrada': 0, 'saida': 3}])
        self.assertEqual(r['primeiro_exemplo_falho'], 0)
        self.assertEqual(r['hipotese']['caminho_ast'], [0, 1])
        self.assertIn('hipótese', r['explicacao'])
        self.assertEqual(executar(r['corpo_corrigido'], -7)['resultado'], -4)
        nao = diagnosticar('return entrada;', [{'entrada': 1, 'saida': {'x': 8}}], verificacoes=1)
        self.assertFalse(nao['atende_desenvolvimento'])
        self.assertIsNone(nao['corpo_corrigido'])

    def test_tracos_distinguem_erro_da_rede_do_codigo(self):
        from interpretacao_estruturas import efeito_exato
        def ruim(op, a, b=0):
            return efeito_exato(op, a, b) + 1 if op == '+' else efeito_exato(op, a, b)
        r = comparar_efeitos('return (entrada + 2) - 1;', 3, ruim)
        self.assertEqual(r['primeiro_efeito_divergente'], 0)
        self.assertEqual(r['efeito_exato']['resultado'], 5)
        self.assertEqual(r['efeito_rede']['resultado'], 6)
        self.assertIsNone(comparar_efeitos('return entrada + 2;', 3, efeito_exato)['primeiro_efeito_divergente'])

    def test_mutacao_de_entrada_nao_satisfaz_contrato(self):
        r = avaliar('entrada[0] = 4; return entrada;', [{'entrada': [1], 'saida': [4]}])[0]
        self.assertTrue(r['entrada_modificada'])
        self.assertFalse(r['correto'])

    def test_strings_nao_recebem_edicoes_de_operadores(self):
        cs = gerar_edicoes('return "a + b";', [{'entrada': 0, 'saida': 'a + b'}])
        self.assertEqual(cs, [])

    def test_contrato_rejeita_referencia_reservados_e_host(self):
        from scripts.diagnosticar_estados import carregar_contrato
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'c.json'
            for extra in ('reservados', 'referencia'):
                p.write_text(json.dumps(dict(codigo='return entrada;', desenvolvimento=[{'entrada':1,'saida':1}], **{extra: []})))
                with self.assertRaises(ValueError):
                    carregar_contrato(p)
        for c in ('return process.exit();', 'return eval("1");', 'return entrada.constructor;'):
            with self.assertRaises(ValueError):
                diagnosticar(c, [{'entrada': 1, 'saida': 1}])
        for limite, verificacoes in ((0, 1), (2000, 1), (10, 11), (10, 0)):
            with self.assertRaises(ValueError):
                diagnosticar('return entrada;', [{'entrada': 1, 'saida': 1}], limite=limite, verificacoes=verificacoes)

    def test_v3_baseline_congelada(self):
        # Sem importar o experimento (NumPy é opcional para o interpretador).
        import hashlib
        raiz = Path(__file__).resolve().parent
        c = json.loads((raiz/'dados/estados/v3-congelada.json').read_text())
        for nome, h in c['fontes_sha256'].items():
            self.assertEqual(hashlib.sha256((raiz/nome).read_bytes()).hexdigest(), h)


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'NumPy opcional ausente')
class RankingTestes(unittest.TestCase):
    def test_gradiente_ranking_e_aprendizado(self):
        import numpy as np
        from rede_reparos import RedeReparos, NOMES, loss_grad
        r = RedeReparos()
        x = np.random.default_rng(31).normal(size=(4, len(NOMES)))
        y = np.asarray([0., .5, 0., .5])
        _, grads = loss_grad(x, y, r.w, r.b, r.v)
        for p, g, idx in ((r.w, grads[0], (3, 7)), (r.b, grads[1], (4,)), (r.v, grads[2], (8,))):
            antigo = p[idx]
            h = 1e-5
            p[idx] = antigo + h
            a = loss_grad(x, y, r.w, r.b, r.v)[0]
            p[idx] = antigo - h
            b = loss_grad(x, y, r.w, r.b, r.v)[0]
            p[idx] = antigo
            self.assertAlmostEqual(float(g[idx]), (a-b)/(2*h), places=7)
        hist = r.treinar([dict(split='treino', features=x.tolist(), corretas=[0,1,0,1])], passos=150)
        self.assertLess(hist['loss_final'], hist['loss_inicial']-.1)
        with self.assertRaises(ValueError):
            r.treinar([dict(split='teste', features=x.tolist(), corretas=[0,1,0,1])])

    def test_ranking_depende_dos_pesos_e_nao_consulta_executor(self):
        import numpy as np
        from rede_reparos import RedeReparos
        inicial = [{'correto': False}]
        e = gerar_edicoes('return entrada - 2;', [{'entrada': 1, 'saida': 3}])[0]
        r = RedeReparos()
        with patch('diagnostico_estados.executar', side_effect=AssertionError('Executor acessado')):
            a = r.nota(e, inicial)
            r.v[:] = 0
            self.assertEqual(r.nota(e, inicial), 0)
            self.assertNotEqual(a, 0)
        with tempfile.TemporaryDirectory() as d:
            r.salvar(d)
            out = RedeReparos.carregar(d)
            np.testing.assert_array_equal(r.w, out.w)
            np.savez_compressed(Path(d)/'rede.npz', w=np.full_like(r.w, np.nan), b=r.b, v=r.v)
            with self.assertRaises(ValueError):
                RedeReparos.carregar(d)

    def test_montagem_treino_nao_acessa_outras_familias_nem_reserva(self):
        from scripts.experimento_diagnostico import BENCH, casos, montar_treino
        b = json.loads(BENCH.read_text())
        permitidos = {v['id'] for f in b['familias'] if f['split']=='treino' for v in f['variantes']}
        chamadas = []
        def guard(v, particao):
            self.assertIn(v['id'], permitidos)
            self.assertEqual(particao, 'desenvolvimento')
            chamadas.append(v['id'])
            return casos(v, particao)
        with patch('scripts.experimento_diagnostico.casos', side_effect=guard):
            grupos = montar_treino(b)
        self.assertEqual({g['id'] for g in grupos}, permitidos)
        self.assertEqual(set(chamadas), permitidos)
        self.assertTrue(all(sum(g['corretas']) for g in grupos))


if __name__ == '__main__':
    unittest.main()
