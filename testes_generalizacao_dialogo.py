"""Isolamento e uso do trecho anterior; não aprova conversa livre."""
import copy
import gzip
import hashlib
import json
import unittest
from pathlib import Path

from conversa_dialogo import aprovacao_valida
from linguagem_gerativa import GeradorGRU, renderizar, tokenizar

ROOT = Path(__file__).resolve().parent
H = ROOT / 'experimentos/generalizacao_dialogo_20261010'


class TestesGeneralizacaoDialogo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads((H / 'corpus_gru.json').read_text())
        cls.dados = json.loads(gzip.decompress((H / 'checkpoint_gru_dialogo.json.gz').read_bytes()))

    def test_pesos_isolados_e_aprovacao_nao_pode_ser_copiada(self):
        self.assertEqual({'aprovado': False, 'ativo_no_chat': False}, self.dados['controle'])
        self.assertFalse(aprovacao_valida(self.dados))
        base = json.loads(gzip.decompress((H / 'checkpoint_base_130.json.gz').read_bytes()))
        adulterado = copy.deepcopy(self.dados)
        adulterado['controle'] = base['controle']
        adulterado['aprovacao'] = base['aprovacao']
        self.assertFalse(aprovacao_valida(adulterado))
        self.assertEqual('0873ad29e80433d8ff032231302e70654b0f479f09627f7d04f7d0511d57c382',
                         hashlib.sha256((H / 'checkpoint_base_130.json.gz').read_bytes()).hexdigest())
        self.assertTrue(aprovacao_valida(json.loads(gzip.decompress((ROOT / 'rede_dialogo_conversa.json.gz').read_bytes()))))
        self.assertLessEqual(self.dados['treino']['parametros'], 85581)

    def test_particoes_inteiras_e_entidades_novas_fora_do_corpus(self):
        grupos = {}
        entidades = {'treino': set(), 'validacao': set()}
        for e in self.corpus['exemplos']:
            grupos.setdefault(e['dialogo'], set()).add(e['split'])
            if e['dialogo'].startswith('sequencia-'):
                entidades[e['split']].update(e['contexto']['slots'].values())
        self.assertTrue(all(len(s) == 1 for s in grupos.values()))
        self.assertTrue(entidades['treino'].isdisjoint(entidades['validacao']))
        texto = json.dumps(self.corpus, ensure_ascii=False)
        for entidade in ('caranguejo relojoeiro', 'doninha ceramista', 'anta confeiteira',
                         'costureira numa oficina pequena', 'quati jardineiro', 'paca mecânica'):
            self.assertNotIn(entidade, texto)
        antigos = json.loads((H.parent / 'orientacao_pratica_20261010/casos_congelados.json').read_text())['casos']
        atuais = json.loads((H / 'casos_congelados.json').read_text())['casos']
        self.assertEqual(antigos, atuais[:79])
        self.assertEqual(114, len(atuais))

    def test_sequencia_livre_usa_propria_saida_e_depende_do_trecho_anterior(self):
        modelo = GeradorGRU(self.dados)
        exemplos = [e for e in self.corpus['exemplos'] if e['split'] == 'validacao'
                    and e['dialogo'].startswith('sequencia-')]
        grupo = [e for e in exemplos if e['dialogo'] == exemplos[0]['dialogo']]
        anterior = grupo[0]['contexto']['resposta_anterior']
        recentes = set()
        for e in grupo:
            contexto = copy.deepcopy(e['contexto'])
            contexto['slots'] = dict(contexto['slots'], tema1='um texugo gravador')
            contexto['resposta_anterior'] = anterior
            gerada = modelo.gerar(contexto, max_tokens=128)
            self.assertTrue(gerada['completa'])
            self.assertEqual(tokenizar(e['resposta']), gerada['tokens'])
            cega = modelo.gerar(dict(contexto, resposta_anterior=''), max_tokens=128)
            self.assertNotEqual(gerada['tokens'], cega['tokens'])
            texto = renderizar(gerada, contexto['slots'])
            self.assertNotIn(texto, recentes)
            self.assertIn('um texugo gravador', texto)
            recentes.add(texto)
            anterior = texto
        self.assertEqual(8, len(recentes))

    def test_manifesto_preserva_evidencia_e_reprovacao_da_integracao(self):
        manifesto = json.loads((H / 'manifesto.json').read_text())
        for nome, esperado in manifesto['arquivos_sha256'].items():
            self.assertEqual(esperado, hashlib.sha256((H / nome).read_bytes()).hexdigest(), nome)
        for nome, esperado in manifesto['pesos_preservados_sha256'].items():
            arquivo = H / 'checkpoint_base_130.json.gz' if nome == 'rede_dialogo_conversa.json.gz' else ROOT / nome
            self.assertEqual(esperado, hashlib.sha256(arquivo.read_bytes()).hexdigest(), nome)
        resultado = json.loads((H / 'piloto_final_congelados_motor.json').read_text())
        self.assertFalse(manifesto['promocao']['aprovada'])
        self.assertGreater(resultado['resumo']['casos_com_referentes_ausentes'], 0)
        self.assertEqual(manifesto['promocao']['resumo'], resultado['resumo'])


if __name__ == '__main__':
    unittest.main()
