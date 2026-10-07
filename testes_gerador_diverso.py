"""Regressões de contaminação e volume ilusório no currículo do gerador."""
import copy
import json
from pathlib import Path
import unittest
from scripts.auditar_gerador_diverso import auditar

ROOT = Path(__file__).resolve().parent


class AuditoriaGerador(unittest.TestCase):
    def setUp(self):
        self.politica = json.loads((ROOT/'configs/curriculo_gerador_diverso.json').read_text())
        self.exemplos = [json.loads(l) for l in (ROOT/'dados/gerador_diverso_semente.jsonl').read_text().splitlines()]

    def erros(self, exemplos):
        return {e['erro'] for e in auditar(exemplos, self.politica)['erros']}

    def test_semente_nao_finge_corpus_pronto(self):
        r = auditar(self.exemplos, self.politica)
        self.assertFalse(r['apto_para_treino_completo'])
        self.assertEqual(len(r['cobertura']['treino']['dominio']), 12)
        self.assertEqual(len(r['cobertura']['treino']['tarefa']), 6)
        self.assertEqual(r['quase_duplicados'], [])
        self.assertIn('revisao_humana_pendente', self.erros(self.exemplos))

    def test_mudar_numeros_nao_cria_diversidade(self):
        a = copy.deepcopy(self.exemplos[1]); b = copy.deepcopy(a)
        b.update(id='outra', grupo='outro', source_id='outro')
        for k in ('conteudo', 'mensagem', 'resposta'):
            b[k] = b[k].replace('20', '30').replace('5', '7')
        self.assertIn('quase_duplicados', self.erros([a, b]))

    def test_texto_nao_atravessa_particoes_com_nova_pergunta(self):
        a = self.exemplos[0]; b = dict(a, id='novo', grupo='outro', source_id='outro', split='teste',
                                    mensagem='Qual a explicação?', resposta='A nuvem bloqueou parte da luz.')
        self.assertIn('vazamento_entre_particoes', self.erros([a, b]))

    def test_grupo_nao_atravessa_particoes_com_outro_texto(self):
        a, b = self.exemplos[:2]
        b = dict(b, grupo=a['grupo'], split='validacao')
        self.assertIn('vazamento_entre_particoes', self.erros([a, b]))

    def test_par_exato_e_resposta_repetida_detectados(self):
        self.assertIn('par_duplicado', self.erros([self.exemplos[0]] * 2))
        a, b = self.exemplos[:2]
        self.assertIn('resposta_repetida', self.erros([a, dict(b, resposta=a['resposta'])]))

    def test_corpus_vazio_e_metadados_ausentes_reprovam(self):
        self.assertFalse(auditar([], self.politica)['apto_para_treino_completo'])
        self.assertIn('campos_ausentes', self.erros([{'mensagem': 'Olá'}]))

    def test_conteudo_curto_repetido_nao_conta_como_novo_assunto(self):
        a, b = self.exemplos[:2]
        self.assertIn('conteudo_duplicado_em_outro_grupo', self.erros([
            dict(a, conteudo='Uma frase curta.'), dict(b, conteudo='Uma frase curta.')]))

    def test_gate_aceita_fixture_com_metas_explicitamente_reduzidas(self):
        # Fixture testa o caminho positivo, não reduz as metas do corpus real.
        politica = dict(self.politica, dominios=['astronomia'], tarefas=['explicar'])
        for k in politica:
            if k.startswith('min_'):
                politica[k] = 1
            if k.startswith('max_fracao_'):
                politica[k] = 1.0
        exemplos = [dict(ex, dominio='astronomia', tarefa='explicar', split=split, revisao='humana_aprovada')
                    for ex, split in zip(self.exemplos[:3], ('treino', 'validacao', 'teste'))]
        self.assertTrue(auditar(exemplos, politica)['apto_para_treino_completo'])


if __name__ == '__main__':
    unittest.main()
