"""Invariantes de evidência, revisão e investigação; não mede inteligência."""
from dataclasses import asdict
import unittest

from investigacao_memoria import criar_investigacao, explicar
from workspace_cognitivo import MemoriaInvestigacao, Investigador, Hipotese, Pergunta


class MemoriaComOrigem(unittest.TestCase):
    def test_hipotese_geracao_e_citacao_nao_substituem_relato(self):
        m=MemoriaInvestigacao()
        original=m.registrar('cache','estavel','usuario','turno:1')
        for origem in ('hipotese','gerador','citacao'):
            m.registrar('cache','cresce',origem,'proposta:'+origem)
        self.assertEqual(m.observacoes()['cache'],original)
        self.assertEqual(len(m.episodios()),4)

    def test_correcao_preserva_rastro_e_replay_antigo_nao_reverte(self):
        m=MemoriaInvestigacao()
        a=m.registrar('fila','cresce','usuario','turno:1')
        b=m.registrar('fila','estavel','usuario','turno:2')
        self.assertEqual(b.substitui,a.id)
        self.assertEqual(m.registrar('fila','cresce','usuario','turno:1'),a)
        self.assertEqual(m.observacoes()['fila'],b)
        self.assertEqual(len(m.episodios()),2)

    def test_repeticao_nao_certifica_e_origem_nao_verifica_sozinha(self):
        m=MemoriaInvestigacao()
        for i in range(8):m.registrar('alegacao','Dijkstra nunca funciona com pesos negativos','usuario',str(i))
        e=asdict(m.observacoes()['alegacao'])
        self.assertEqual(e['origem'],'usuario')
        self.assertNotIn('verificada',e)
        with self.assertRaises(ValueError):m.registrar('heap','cresce','instrumento','')

    def test_orcamento_e_isolamento(self):
        a,b=MemoriaInvestigacao(3),MemoriaInvestigacao()
        for i in range(9):a.registrar('campo'+str(i),'valor','usuario',str(i))
        self.assertEqual(len(a.episodios()),3)
        self.assertEqual(b.episodios(),())
        a.limpar();self.assertEqual(a.observacoes(),{})
        for n in (True,0,65):
            with self.assertRaises(ValueError):MemoriaInvestigacao(n)


class ControleInvestigacao(unittest.TestCase):
    def novo(self, **observacoes):
        i=criar_investigacao()
        i.observar(dict(runtime='node',metrica='heap',**observacoes),'caso:1')
        return i

    def test_esclarece_ambiente_antes_de_simular_gc(self):
        i=criar_investigacao()
        r=i.investigar();self.assertEqual(r['campo'],'runtime')
        self.assertEqual(r['workspace']['hipoteses'],[])
        i.observar({'runtime':'node'},'turno:1')
        self.assertEqual(i.investigar()['campo'],'metrica')

    def test_rss_nao_e_heap_e_ambiente_outro_exige_outro_modelo(self):
        for dado in ({'runtime':'node','metrica':'rss'},{'runtime':'outro'}):
            i=criar_investigacao();i.observar(dado,'medicao-informada')
            r=i.investigar()
            self.assertEqual(r['acao'],'fora_de_escopo')
            self.assertEqual(r['workspace']['hipoteses'],[])
            self.assertFalse(r['comprovado'])
            self.assertIn('RSS',explicar(r))

    def test_escolhe_pergunta_que_diferencia_crescimento_transitorio(self):
        i=self.novo();antes=i.memoria.episodios();r=i.investigar()
        self.assertEqual(r['campo'],'pos_gc')
        self.assertEqual(len(r['workspace']['alternativas']),3)
        self.assertFalse(r['comprovado'])
        self.assertEqual(i.memoria.episodios(),antes)
        self.assertLessEqual(len(r['passos']),6)

    def test_causas_podem_coexistir_e_uma_restante_nao_e_prova(self):
        i=self.novo(pos_gc='cresce',cache='cresce',fila='cresce')
        r=i.investigar()
        comp={h['id'] for h in r['workspace']['hipoteses'] if not h['contradicoes']}
        self.assertEqual(comp,{'retencao','cache','fila'})
        self.assertFalse(any(h['comprovada'] for h in r['workspace']['hipoteses']))
        self.assertEqual(r['acao'],'investigar_fora_do_modelo')
        i.observar({'cache':'estavel','fila':'estavel'},'correcao:2')
        r=i.investigar()
        self.assertEqual([h['id'] for h in r['workspace']['hipoteses'] if not h['contradicoes']],['retencao'])
        self.assertFalse(r['comprovado'])
        self.assertIn('não comprova',explicar(r))

    def test_revisao_reabre_hipoteses_sem_carregar_conclusao_antiga(self):
        i=self.novo(pos_gc='cresce',cache='cresce')
        a=i.investigar()
        self.assertTrue(next(h for h in a['workspace']['hipoteses'] if h['id']=='transitorio')['contradicoes'])
        i.observar({'pos_gc':'estavel'},'correcao:2')
        b=i.investigar()
        self.assertFalse(next(h for h in b['workspace']['hipoteses'] if h['id']=='transitorio')['contradicoes'])
        self.assertEqual(b['acao'],'investigar_fora_do_modelo')
        self.assertEqual(a['workspace']['observacoes']['pos_gc']['valor'],'cresce')

    def test_gerador_nao_pode_fabricar_uma_medicao(self):
        i=self.novo()
        with self.assertRaises(ValueError):i.observar({'pos_gc':'cresce'},'resposta:1',origem='gerador')
        i.memoria.registrar('pos_gc','cresce','hipotese','simulacao:1')
        self.assertEqual(i.investigar()['campo'],'pos_gc')

    def test_validacao_atomica_e_snapshot_isolado(self):
        i=self.novo()
        antigo=i.memoria.episodios()
        with self.assertRaises(ValueError):i.observar({'cache':'cresce','fila':'nao-sei'},'invalido')
        self.assertEqual(i.memoria.episodios(),antigo)
        r=i.investigar();r['workspace']['observacoes']['metrica']['valor']='rss'
        self.assertEqual(i.investigar()['workspace']['observacoes']['metrica']['valor'],'heap')

    def test_transferencia_para_outro_modelo_sem_frases_de_diagnostico_js(self):
        i=Investigador([
            Hipotese('energia','O sensor não recebe energia.',(('tensao',('ausente',)),)),
            Hipotese('conexao','O enlace não transmite dados.',(('enlace',('interrompido',)),)),
        ],[
            Pergunta('tensao','Há tensão na entrada?',('presente','ausente'),1.),
            Pergunta('enlace','Há transmissão no enlace?',('funcional','interrompido'),8.),
        ])
        self.assertEqual(i.investigar()['campo'],'tensao')
        i.observar({'tensao':'presente'},'sensor:1',origem='instrumento')
        self.assertEqual(i.investigar()['campo'],'enlace')
        i.observar({'enlace':'funcional'},'sensor:2',origem='instrumento')
        r=i.investigar()
        self.assertEqual(r['acao'],'rever_modelo')
        self.assertFalse(r['comprovado'])

    def test_sem_nova_evidencia_nao_habilita_um_loop_infinito(self):
        i=self.novo()
        primeiro=i.investigar();episodios=i.memoria.episodios()
        for _ in range(25):self.assertEqual(i.investigar(),primeiro)
        self.assertEqual(i.memoria.episodios(),episodios)

    def test_orcamento_numerico_e_modelo_inconsistente_sao_recusados(self):
        hs=[Hipotese('h','Hipótese de teste.',(('x',('a',)),))]
        for custo in (True,0.,float('inf'),float('nan'),1e-320):
            with self.assertRaises(ValueError):
                Investigador(hs,[Pergunta('x','Qual valor?',('a','b'),custo)])
        with self.assertRaises(ValueError):
            Investigador(hs,[Pergunta('x','Qual valor?',('a','b'))],dominio=(('x','a'),('x','b')))


if __name__=='__main__':unittest.main()
