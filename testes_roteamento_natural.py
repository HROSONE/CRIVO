"""Contratos de fonte e de entrega, incluindo falhas injetadas no executor.

Entradas vêm do conjunto real congelado. Saídas falsas servem apenas para
exercitar a guarda; não são casos adicionais nem pontos na avaliação.
"""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from memoria_sessao import MemoriaSessao
from raciocinio_conversa import RaciocinioConversa
from estado_interno import guardar_fidelidade

CASOS = {c['id']: c for c in json.loads((Path(__file__).parent /
         'experimentos/roteamento_natural_20261009/casos_congelados.json').read_text())['casos']}


class TestesRoteamentoNatural(unittest.TestCase):
    def test_composta_preserva_fonte_integral_e_correcao_da_pessoa(self):
        memoria = MemoriaSessao()
        entrada = CASOS['real-08']['entrada']['texto']
        memoria.processar(entrada)
        self.assertEqual(4, len(memoria.afirmacoes))
        self.assertTrue(all(f['fonte']['texto'] == entrada for f in memoria.afirmacoes))
        correcao = CASOS['real-09']['entrada']['texto']
        memoria.processar(correcao)
        self.assertEqual('cuscuz', memoria._atual('pessoa:brena', 'preferência')['valor'])
        self.assertEqual('bolo de fubá', memoria._atual('pessoa:tacio', 'preferência')['valor'])
        self.assertEqual(correcao, memoria._atual('pessoa:brena', 'preferência')['fonte']['texto'])

    def test_orcamento_corrigido_nao_confirma_reserva_hipotetica(self):
        r = RaciocinioConversa()
        c = CASOS['real-14']['entrada']
        historico = []
        for fala in c['anteriores']:
            r.responder(fala)
            historico.append({'pergunta':fala})
        r.planejar_contexto(c['texto'], historico, ['estudar inglês e lavar a louça'])
        self.assertNotIn('descanso', r.tempos)
        historico.append({'pergunta':c['texto']})
        atual = CASOS['real-16']['entrada']['texto']
        _, resposta = r.planejar_contexto(atual, historico, ['estudar inglês e lavar a louça'])
        self.assertIn('3 minutos para inglês', resposta)
        self.assertEqual('20', r.ultimo['resultado']['disponivel'])
        self.assertEqual(atual, r.ultimo['fontes']['tempo:disponivel']['fonte'])
        self.assertNotIn('descanso', r.tempos)
        self.assertTrue(r.ultimo['hipotese'])

    def test_rotulo_de_calculo_nao_licencia_receita(self):
        q = dict(operacao='tempo_restante', status='calculado',
                 entradas={'louça':'12', 'descanso':'5'},
                 resultado={'disponivel':'35','restante':'18'})
        bot = SimpleNamespace(raciocinio_conversa=SimpleNamespace(ultimo=q),
                              contexto_textual=None, historico=[{'id':'conversa:raciocinio'}])
        rota = dict(peca='calculo', ato='planejar', referentes=[], status='executado')
        ident, resposta = guardar_fidelidade(bot, rota, 'conversa:raciocinio',
                                            'Refogue arroz por 18 minutos.')
        self.assertEqual('conversa:esclarecer', ident)
        self.assertNotIn('arroz', resposta)
        self.assertFalse(rota['guarda']['aceita'])

    def test_rejeicao_nao_publica_nem_retoma_historia_invalida(self):
        geracao = SimpleNamespace(ultima_escrita={'texto':'rascunho rejeitado'}, ultima_criacao={})
        bot = SimpleNamespace(conversacao=SimpleNamespace(geracao=geracao),
                              contexto_textual=None, historico=[{'id':'conversa:gerada_historia'}])
        rota = dict(peca='escrita', ato='historia', referentes=['capivara astronauta'],
                    frases=5, status='executado', _escrita_anterior=None)
        ident, resposta = guardar_fidelidade(bot, rota, 'conversa:gerada_historia',
                    'Ficção:\nA capivara astronauta partiu. Ela voltou. Ela descansou.')
        self.assertEqual('conversa:esclarecer', ident)
        self.assertIn('capivara astronauta', resposta)
        self.assertIn('5 frases', resposta)
        self.assertIsNone(geracao.ultima_escrita)
        self.assertFalse(any(k.startswith('_') for k in bot.historico[-1]['natural_routing']))


if __name__ == '__main__':
    unittest.main()
