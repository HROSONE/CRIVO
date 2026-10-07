"""Contratos do experimento; dublês verificam veto, não capacidade neural."""
import unittest
from modular import corpus_modular, executar_modular, exemplos_modulares, preparar, pergunta_apoio
from piloto import corpus, NOMES


class Duble:
    def __init__(self, estados=('E','A'), apoio=.9, regra=.9, texto='O painel liga'):
        self.estados=iter(estados); self.apoio=apoio; self.regra=regra; self.texto=texto
        self.redacoes=0; self.avaliadas=[]

    def classe(self, texto, classes):
        return next(self.estados)

    def probabilidade(self, texto, classe, classes):
        self.avaliadas.append(texto)
        if texto.startswith('Tarefa: apoio'):
            cond,fato=texto.split('Condição: ',1)[1].split('\nFato: ')
            return self.apoio if cond.lower()==fato.lower() else min(self.apoio,.6)
        return self.regra

    def redigir(self, texto):
        self.redacoes+=1
        return self.texto


def caso(fato='O sensor responde'):
    return dict(premissas=[fato,'Se o sensor responde, então o painel liga'],
                objetivo='O painel liga',status='sustentado')


class TestesModular(unittest.TestCase):
    def test_corpus_fixo_e_teste_novo(self):
        dados, hashes=corpus_modular()
        self.assertEqual(hashes,corpus_modular()[1])
        self.assertEqual(hashes['teste'],'4ea8d5cc387111c882ba6559c6fbcfd88684d910549235cd2b094cf3904fa5f9')
        self.assertEqual(len(dados['teste']),84)
        self.assertEqual(sum(c['ood_estrutura'] for c in dados['teste']),36)
        texto='\n'.join(p for c in dados['teste'] for p in c['premissas']).lower()
        for vocab in NOMES.values():
            for literal in vocab:
                self.assertNotIn(literal.lower(),texto)
        antigo, h=corpus()
        self.assertEqual(h,corpus()[1])
        self.assertNotEqual(h['teste'],hashes['teste'])

    def test_prova_neural_verificada(self):
        m=Duble(); r=executar_modular(caso(),m)
        self.assertEqual(r['status'],'sustentado')
        self.assertEqual(len(r['passos']),1)
        self.assertEqual(m.redacoes,1)

    def test_termino_correto_sem_prova_e_vetado(self):
        r=executar_modular(caso(),Duble(estados=('A',)))
        self.assertEqual(r['motivo'],'termino_sem_prova')
        self.assertIsNone(r['status'])

    def test_apoio_incorreto_nao_e_reparado(self):
        m=Duble(); r=executar_modular(caso('O radar gira'),m)
        self.assertTrue(r['motivo'].startswith('selecao:'))
        self.assertIsNone(r['status']); self.assertEqual(m.redacoes,0)
        self.assertFalse(r['passos'])

    def test_regra_rejeitada_nao_e_escolhida_pelo_verificador(self):
        m=Duble(regra=.4); r=executar_modular(caso(),m)
        self.assertEqual(r['motivo'],'regra_nao_selecionada')
        self.assertEqual(m.redacoes,0)

    def test_apoio_rejeitado_nao_e_preenchido(self):
        r=executar_modular(caso(),Duble(apoio=.4))
        self.assertEqual(r['motivo'],'apoio_nao_selecionado')

    def test_regra_invalida_nao_troca_para_alternativa_valida(self):
        c=caso()
        c['premissas'].append('Se o radar gira, então o painel liga')
        m=Duble(); r=executar_modular(c,m)
        self.assertEqual(r['trace'][0]['regra'],'p2')
        self.assertIsNone(r['status']); self.assertFalse(r['passos'])
        self.assertEqual(m.redacoes,0)

    def test_conjuncao_exige_todos_os_apoios(self):
        c=caso()
        c['premissas'][1]='Se o sensor responde e o radar gira, então o painel liga'
        r=executar_modular(c,Duble())
        self.assertIsNone(r['status']); self.assertFalse(r['passos'])
        self.assertTrue(r['motivo'].startswith('selecao:'))

    def test_ablação_simbolica_nao_conta_redacao_errada_como_neural(self):
        r=executar_modular(caso(),Duble(texto='O radar gira'))
        self.assertTrue(r['motivo'].startswith('redacao:'))
        self.assertIsNone(r['status'])
        m=Duble(texto='O radar gira'); r=executar_modular(caso(),m,'simbolica')
        self.assertEqual(r['status'],'sustentado'); self.assertEqual(m.redacoes,0)

    def test_passo_repetido_nao_e_progresso(self):
        r=executar_modular(caso(),Duble(estados=('E','E')))
        self.assertEqual(r['motivo'],'passo_repetido')
        self.assertEqual(len(r['passos']),1)

    def test_rotulos_de_apoio_preservam_polaridade(self):
        ex=exemplos_modulares([caso()])
        regras,fatos=preparar(caso(),[]); a=regras[0][1].antecedentes[0]
        self.assertIn((pergunta_apoio(a,fatos[0][1]),'1'),ex['apoio'])
        self.assertIn((pergunta_apoio(a,a.oposto()),'0'),ex['apoio'])

    def test_composicao_desconhecida_e_rejeitada(self):
        with self.assertRaises(ValueError):
            executar_modular(caso(),Duble(),'inexistente')


if __name__=='__main__':unittest.main()
