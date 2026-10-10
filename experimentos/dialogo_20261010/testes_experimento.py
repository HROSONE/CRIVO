"""Contratos de isolamento, congelamento e proveniência do treino."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(H))
from avaliar import ler_modelo
from dialogo_seq2seq import DialogoSeq2Seq
from linguagem_gerativa import GeradorGRU, tokenizar


class ContratosExperimento(unittest.TestCase):
    def test_conjunto_congelado_preserva_os_35_casos_reais(self):
        path = H / 'casos_congelados.json'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), (H / 'SHA256').read_text().split()[0])
        dados = json.loads(path.read_text())
        original = H.parent / 'roteamento_natural_v2_20261009/casos_congelados.json'
        self.assertEqual(dados['originais_sha256'], hashlib.sha256(original.read_bytes()).hexdigest())
        self.assertEqual(len(dados['casos']), 37)
        for a, b in zip(json.loads(original.read_text())['casos'], dados['casos']):
            self.assertEqual(a, {k: b[k] for k in a})

    def test_particoes_nao_compartilham_sessoes_nem_entradas(self):
        dados = json.loads((H / 'corpus.json').read_text())
        treino = [e for e in dados['exemplos'] if e['split'] == 'treino']
        val = [e for e in dados['exemplos'] if e['split'] == 'validacao']
        self.assertEqual((len(treino), len(val)), (2304, 576))
        self.assertFalse({e['id_dialogo'] for e in treino} & {e['id_dialogo'] for e in val})
        chave = lambda e: json.dumps(e['contexto'], sort_keys=True, ensure_ascii=False)
        self.assertFalse({chave(e) for e in treino} & {chave(e) for e in val})
        self.assertEqual(len({chave(e) for e in treino + val}), len(treino + val))
        testes = {c['entrada']['texto'] for c in json.loads((H / 'casos_congelados.json').read_text())['casos']}
        self.assertFalse(testes & {e['contexto']['mensagem'] for e in treino + val})

    def test_pesos_ativos_permanecem_intactos(self):
        antes = json.loads((H / 'pesos_ativos_antes.json').read_text())
        for nome, sha in antes.items():
            with self.subTest(arquivo=nome):
                self.assertEqual(hashlib.sha256((ROOT / nome).read_bytes()).hexdigest(), sha)

    def test_checkpoint_carregavel_mas_sem_aprovacao(self):
        dados = ler_modelo(H / 'checkpoint_dialogo.json.gz')
        self.assertEqual(dados['controle'], {'aprovado': False, 'ativo_no_chat': False})
        self.assertEqual(dados['corpus_sha256'], hashlib.sha256((H / 'corpus.json').read_bytes()).hexdigest())
        self.assertEqual(dados['casos_sha256'], hashlib.sha256((H / 'casos_congelados.json').read_bytes()).hexdigest())
        base = ler_modelo(ROOT / 'rede_dialogo_seq2seq.json.gz')
        self.assertEqual(dados['base_sha256'], hashlib.sha256((ROOT / 'rede_dialogo_seq2seq.json.gz').read_bytes()).hexdigest())
        modelo = DialogoSeq2Seq(dados)
        self.assertLessEqual(dados['treino']['parametros'], base['treino']['parametros'])
        self.assertEqual((modelo.ocultos, modelo.embeddings), (base['ocultos'], base['embeddings']))

    def test_segundo_corpus_conserva_particoes_e_argumentos(self):
        original = json.loads((H / 'corpus.json').read_text())
        dados = json.loads((H / 'corpus_gru.json').read_text())
        self.assertEqual(dados['corpus_origem_sha256'], hashlib.sha256((H / 'corpus.json').read_bytes()).hexdigest())
        self.assertEqual(len(dados['exemplos']), len(original['exemplos']))
        for a, b in zip(original['exemplos'], dados['exemplos']):
            self.assertEqual((a['id'], a['split']), (b['id'], b['split']))
            for token in tokenizar(b['resposta']):
                if token.startswith('@'):
                    self.assertTrue(b['contexto']['slots'].get(token[1:]), (b['id'], token))

    def test_checkpoint_gru_isolado_sem_aumentar_parametros(self):
        dados = ler_modelo(H / 'checkpoint_gru_dialogo.json.gz')
        base = ler_modelo(ROOT / 'rede_geracao.json')
        GeradorGRU(dados)
        self.assertEqual(dados['controle'], {'aprovado': False, 'ativo_no_chat': False})
        self.assertLessEqual(dados['treino']['parametros'], base['treino']['parametros'])
        self.assertEqual((dados['ocultos'], dados['embeddings']), (base['ocultos'], base['embeddings']))
        for campo, caminho in [('base_sha256', ROOT / 'rede_geracao.json'),
                               ('corpus_sha256', H / 'corpus_gru.json'),
                               ('casos_sha256', H / 'casos_congelados.json')]:
            self.assertEqual(dados[campo], hashlib.sha256(caminho.read_bytes()).hexdigest())

    def test_manifesto_corresponde_aos_artefatos_publicados(self):
        dados = json.loads((H / 'manifesto.json').read_text())
        for nome, sha in dados['arquivos'].items():
            with self.subTest(arquivo=nome):
                self.assertEqual(hashlib.sha256((H / nome).read_bytes()).hexdigest(), sha)
        for nome, sha in dados['codigo_proprio_reutilizado'].items():
            self.assertEqual(hashlib.sha256((ROOT / nome).read_bytes()).hexdigest(), sha)


if __name__ == '__main__':
    unittest.main()
