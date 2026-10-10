"""Contratos do experimento; não equipara padrões autorais a conversa livre."""
import copy
import gzip
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from conversa_dialogo import aprovacao_valida
from linguagem_gerativa import GeradorGRU, atributos

ROOT = Path(__file__).resolve().parent
H = ROOT / 'experimentos/escrita_acontecimentos_20261010'


class TestesEscritaAcontecimentos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads((H / 'corpus_gru.json').read_text())
        cls.dados = json.loads(gzip.decompress((H / 'checkpoint_gru_dialogo.json.gz').read_bytes()))
        spec = importlib.util.spec_from_file_location('piloto_acontecimentos', H / 'piloto_runtime/conversa_dialogo.py')
        cls.piloto = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.piloto)

    def test_congelados_e_particoes_nao_foram_alterados(self):
        self.assertEqual((H.parent / 'generalizacao_dialogo_20261010/casos_congelados.json').read_bytes(),
                         (H / 'casos_congelados.json').read_bytes())
        grupos = {}
        for e in self.corpus['exemplos']:
            grupos.setdefault(e['dialogo'], set()).add(e['split'])
        self.assertTrue(all(len(s) == 1 for s in grupos.values()))
        texto = json.dumps(self.corpus, ensure_ascii=False)
        for entidade in ('caranguejo relojoeiro', 'anta confeiteira', 'quati jardineiro', 'paca mecânica'):
            self.assertNotIn(entidade, texto)

    def test_candidato_isolado_nao_herda_aprovacao(self):
        self.assertEqual({'aprovado': False, 'ativo_no_chat': False}, self.dados['controle'])
        self.assertFalse(aprovacao_valida(self.dados))
        self.assertLessEqual(self.dados['treino']['parametros'], 85581)
        adulterado = copy.deepcopy(self.dados)
        ativo = json.loads(gzip.decompress((H.parent / 'generalizacao_dialogo_20261010/checkpoint_base_130.json.gz').read_bytes()))
        adulterado.update(controle=ativo['controle'], aprovacao=ativo['aprovacao'])
        self.assertFalse(aprovacao_valida(adulterado))

    def test_aprovacao_exige_regressao_e_estrutura_avaliada(self):
        ativo = json.loads(gzip.decompress((ROOT / 'rede_dialogo_conversa.json.gz').read_bytes()))
        self.assertTrue(aprovacao_valida(ativo))
        alterado = copy.deepcopy(ativo)
        alterado['aprovacao']['metricas']['casos_antigos_http'] = 78
        self.assertFalse(aprovacao_valida(alterado))
        alterado = copy.deepcopy(ativo)
        alterado['vocabulario'][-1] = 'Maria'
        self.assertFalse(aprovacao_valida(alterado))

    def test_classes_nao_colidem_no_contexto(self):
        vetores = {}
        for e in self.corpus['exemplos']:
            if not e['id'].startswith('evento-'):
                continue
            c = dict(acao='continuacao', slots={'tema1':'uma personagem'}, estilo='neutro',
                     variante=0, mensagem=e['contexto']['mensagem'], historico=[], resposta_anterior='')
            vetores[e['familia']] = tuple(atributos(c))
        self.assertEqual(12, len(vetores))
        self.assertEqual(12, len(set(vetores.values())))

    def test_geracao_contrafactual_reage_sem_prefixo_alvo(self):
        modelo = GeradorGRU(self.dados)
        saidas = {}
        for classe in ('perda','recuperacao','ajuda','caixa_vazia','retorno','costura'):
            c = dict(acao='continuacao', slots={'tema1':'uma personagem','relato':'Um acontecimento declarado'},
                     estilo='neutro',variante=0,mensagem='acontecimento '+classe+' estado_'+classe,
                     historico=[],resposta_anterior='')
            g = modelo.gerar(c, max_tokens=128)
            self.assertTrue(g['completa'])
            self.assertIn('@relato', g['tokens'])
            self.assertTrue(self.piloto.reacao_adequada(g['tokens'], classe), classe)
            saidas[classe] = tuple(g['tokens'])
        self.assertEqual(6, len(set(saidas.values())))
        self.assertFalse(self.piloto.reacao_adequada(['Ficção',':','@relato','A','personagem','guardou','o','objeto','.'], 'ajuda'))

    def test_correcao_ficcional_nao_ressuscita_perda_nem_vira_fato_real(self):
        e = dict(tipo='historia',turno=1,slots={'tema1':'uma ariranha','tema2':'um jardim','relato':'A personagem perdeu um broche'},texto='Ficção.')
        bot = SimpleNamespace(conversacao=SimpleNamespace(turno=2,geracao=SimpleNamespace(ultima_escrita=e,MAX_INTERVALO=10)))
        r = self.piloto.contexto_escrita('O broche já foi recuperado. Continue.', bot)
        self.assertEqual('recuperacao', r['classe_escrita'])
        self.assertNotIn('perdeu', r['slots']['relato'])
        r = self.piloto.contexto_escrita('Agora muda o final: elas encontram o broche.', bot)
        self.assertEqual('corrigir', r['ato'])
        self.assertNotIn('detalhe', r['slots'])
        self.assertNotIn('perdeu', r['slots']['relato'])
        pedido = self.piloto.contexto_escrita('Ela pede ajuda a uma vizinha. Continue.', bot)
        self.assertEqual('companhia', pedido['classe_escrita'])
        self.assertEqual('uma vizinha', pedido['slots']['detalhe'])
        resposta = self.piloto.contexto_escrita('O bilhete pede ajuda. Faça a personagem responder.', bot)
        self.assertEqual('ajuda', resposta['classe_escrita'])
        self.assertIsNone(self.piloto.contexto_escrita('Eu perdi meu broche. Continue.', bot))
        self.assertIsNone(self.piloto.contexto_escrita('Não escreva uma história.', bot))

    def test_hashes_da_evidencia(self):
        m = json.loads((H / 'manifesto.json').read_text())
        for nome, sha in m['arquivos_sha256'].items():
            self.assertEqual(sha, hashlib.sha256((H / nome).read_bytes()).hexdigest(), nome)
        for nome, sha in m['pesos_preservados_sha256'].items():
            self.assertEqual(sha, hashlib.sha256((ROOT / nome).read_bytes()).hexdigest(), nome)


if __name__ == '__main__':
    unittest.main()
