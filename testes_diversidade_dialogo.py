"""Aprovação dos pesos próprios e diversidade sem contar argumentos copiados."""
import copy
import gzip
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

from conversa_dialogo import aprovacao_valida, ORIGEM_V6_SHA256, conferir, reacao_adequada
from linguagem_gerativa import GeradorGRU

ROOT = Path(__file__).resolve().parent
H = ROOT / 'experimentos/diversidade_dialogo_20261010'
spec = importlib.util.spec_from_file_location('juiz_diversidade', H / 'avaliar.py')
juiz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(juiz)


class TestesDiversidadeDialogo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidato = json.loads(gzip.decompress((H / 'checkpoint_gru_dialogo.json.gz').read_bytes()))
        # Regressão da aprovação V6 usa o arquivo histórico preservado.
        cls.ativo = json.loads(gzip.decompress((ROOT / 'experimentos/continuidade_causal_20261010/checkpoint_base_134.json.gz').read_bytes()))

    def test_candidato_nao_pode_herdar_aprovacao(self):
        self.assertEqual({'aprovado': False, 'ativo_no_chat': False}, self.candidato['controle'])
        self.assertFalse(aprovacao_valida(self.candidato))
        antigo = json.loads(gzip.decompress((H / 'checkpoint_base_133.json.gz').read_bytes()))
        falso = copy.deepcopy(self.candidato)
        falso.update(controle=antigo['controle'], aprovacao=antigo['aprovacao'])
        self.assertFalse(aprovacao_valida(falso))
        self.assertTrue(aprovacao_valida(antigo))

    def test_aprovacao_exige_diversidade_utilidade_e_regressoes(self):
        self.assertTrue(aprovacao_valida(self.ativo))
        self.assertEqual(ORIGEM_V6_SHA256, self.ativo['aprovacao']['checkpoint_origem_sha256'])
        for chave, valor in [('diversidade_motor', 7), ('diversidade_http', 7),
                             ('diversidade_problemas_fidelidade', 1), ('praticos_http', 39),
                             ('praticos_motor', 39), ('casos_motor', 109),
                             ('casos_antigos_http', 78), ('referentes_ausentes', 1)]:
            with self.subTest(chave=chave):
                falso = copy.deepcopy(self.ativo)
                falso['aprovacao']['metricas'][chave] = valor
                self.assertFalse(aprovacao_valida(falso))
        falso = copy.deepcopy(self.ativo)
        falso['aprovacao']['treino_reproduzido_byte_a_byte'] = False
        self.assertFalse(aprovacao_valida(falso))

    def test_vocabulario_ou_pesos_adulterados_nao_aprovam(self):
        falso = copy.deepcopy(self.ativo)
        falso['vocabulario'][-1] = 'Maria'
        self.assertFalse(aprovacao_valida(falso))
        falso = copy.deepcopy(self.ativo)
        chave = next(iter(falso['pesos']))
        falso['pesos'][chave] = []
        self.assertFalse(aprovacao_valida(falso))

    def test_trocar_so_objetos_nao_conta_como_diversidade(self):
        d = json.loads((H / 'baseline_motor.json').read_text())
        m = juiz.pontuar(d)
        self.assertEqual(0, m['sessoes_aprovadas'])
        self.assertEqual(8, m['corpos_distintos_total'])
        self.assertEqual(0, m['problemas_fidelidade'])

    def test_variantes_livres_reagem_sem_prefixo_alvo(self):
        modelo = GeradorGRU(self.candidato)
        classes = ('perda', 'recuperacao', 'encontro', 'caixa_vazia', 'retorno',
                   'devolucao', 'ajuda', 'conserto', 'costura', 'companhia')
        for classe in classes:
            saidas = set()
            for variante in range(4):
                c = dict(acao='continuacao', slots={'tema1': 'uma cotia artesã',
                         'relato': 'Um acontecimento declarado'}, estilo='neutro',
                         variante=variante, mensagem='acontecimento '+classe+' estado_'+classe,
                         historico=[], resposta_anterior='')
                g = modelo.gerar(c, max_tokens=96)
                texto, guarda = conferir(g, c, modelo.vocabulario)
                self.assertTrue(guarda['aceita'], (classe, variante, guarda))
                self.assertTrue(reacao_adequada(g['tokens'], classe), classe)
                self.assertIn('uma cotia artesã', texto)
                saidas.add(tuple(g['tokens']))
            self.assertGreaterEqual(len(saidas), 3, classe)

    def test_guarda_continua_rejeitando_argumento_perdido_e_numero(self):
        c = dict(slots={'tema1': 'uma cotia'})
        g = dict(completa=True, tokens=['Ficção', ':', 'A', 'personagem', '.'])
        _, guarda = conferir(g, c, self.candidato['vocabulario'])
        self.assertFalse(guarda['aceita'])
        g['tokens'] = ['Ficção', ':', '@tema1', '17', '.']
        _, guarda = conferir(g, c, self.candidato['vocabulario'])
        self.assertFalse(guarda['aceita'])

    def test_mesma_arquitetura_e_hashes_congelados(self):
        base = json.loads(gzip.decompress((H / 'checkpoint_base_133.json.gz').read_bytes()))
        self.assertEqual(base['vocabulario'], self.candidato['vocabulario'])
        self.assertEqual(base['assinatura_atributos'], self.candidato['assinatura_atributos'])
        self.assertEqual(85130, self.candidato['treino']['parametros'])
        self.assertEqual(321, len(self.candidato['vocabulario']))
        for nome, arquivo in [('sondas.json', 'SHA256'), ('avaliar.py', 'SHA256-juiz')]:
            self.assertEqual((H / arquivo).read_text().split()[0],
                             hashlib.sha256((H / nome).read_bytes()).hexdigest())

    def test_experimentos_e_pesos_anteriores_preservados(self):
        m = json.loads((H / 'manifesto.json').read_text())
        for grupo in ('pesos_preservados_sha256', 'experimentos_preservados_sha256'):
            for nome, digest in m[grupo].items():
                self.assertEqual(digest, hashlib.sha256((ROOT / nome).read_bytes()).hexdigest(), nome)
        for nome, digest in m['arquivos_sha256'].items():
            self.assertEqual(digest, hashlib.sha256((H / nome).read_bytes()).hexdigest(), nome)


if __name__ == '__main__':
    unittest.main()
