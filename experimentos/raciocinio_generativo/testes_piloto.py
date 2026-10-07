"""Contratos: isolamento de dados, provas e veto sem reparo de respostas."""
import unittest
from piloto import corpus, exemplos_passos, executar, contexto, interpretar
from responder_piloto import prova_da_resposta


class TestesPiloto(unittest.TestCase):
    def test_splits_reproduziveis_sem_entradas_compartilhadas(self):
        dados, hashes = corpus()
        self.assertEqual(hashes, corpus()[1])
        entradas = {s: {contexto(c, []) for c in cs} for s, cs in dados.items()}
        for a, b in [('treino','dev'), ('treino','teste'), ('dev','teste')]:
            self.assertFalse(entradas[a] & entradas[b])
        self.assertTrue(any(c['ood_estrutura'] for c in dados['teste']))
        self.assertFalse(any(c['ood_estrutura'] for c in dados['treino']))

    def test_todos_alvos_do_professor_tem_passos_verificaveis(self):
        dados, _ = corpus()
        for c in dados['treino']:
            exemplos = exemplos_passos(c)
            respostas = iter(a for _, a in exemplos)
            r = executar(c, lambda _: next(respostas))
            self.assertEqual(r['status'], c['status'])
            if c['status'] in ('sustentado', 'refutado'):
                self.assertTrue(prova_da_resposta(c, r))

    def test_nao_repara_saida_invalida_com_oraculo(self):
        c = dict(premissas=['O sensor responde', 'Se o sensor responde, então o painel liga'],
                 objetivo='O painel liga')
        r = executar(c, lambda _: 'não sei usar esse protocolo')
        self.assertIsNone(r['status'])
        self.assertEqual(r['motivo'], 'protocolo_invalido')

    def test_status_certo_sem_passos_nao_tem_prova(self):
        c = dict(premissas=['O sensor responde', 'Se o sensor responde, então o painel liga'],
                 objetivo='O painel liga')
        r = executar(c, lambda _: 'sustentado')
        self.assertFalse(prova_da_resposta(c, r))

    def test_modelo_nao_pode_citar_um_passo_futuro(self):
        c = dict(premissas=['O sensor responde', 'Se o sensor responde, então o painel liga'],
                 objetivo='O painel liga')
        r = executar(c, lambda _: 'p1|s0|O painel liga')
        self.assertIsNone(r['status'])
        self.assertEqual(r['motivo'], 'apoio_ausente_ou_futuro')

    def test_erro_de_polaridade_na_conclusao_e_vetado(self):
        c = dict(premissas=['O sensor responde', 'Se o sensor responde, então o painel liga'],
                 objetivo='O painel liga')
        r = executar(c, lambda _: 'p1|p0|O painel não liga')
        self.assertIsNone(r['status'])
        self.assertEqual(r['motivo'], 'consequente_incorreto')

    def test_indeterminado_nao_significa_refutado(self):
        d, _ = corpus()
        ausente = next(c for c in d['treino'] if c['modo'] == 'ausente')
        self.assertEqual(ausente['status'], 'indeterminado')
        self.assertIsNone(prova_da_resposta(ausente, dict(status='indeterminado', passos=[])))

    def test_protocolo_rejeita_texto_extra_e_ids_nao_permitidos(self):
        for t in ['p1|x0|O painel liga', 'p1|p0|O painel liga\nResposta: sim', '{}']:
            with self.assertRaises(ValueError):
                interpretar(t)


if __name__ == '__main__':
    unittest.main()
