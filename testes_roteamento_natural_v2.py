"""Contratos de polaridade, referência e fonte; sem treinamento do gerador."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from crivo import Crivo
from compreensao_intencao import encaminhar_declaracao_natural, rotear_natural
from estado_interno import guardar_fidelidade
from memoria_sessao import MemoriaSessao

H = Path(__file__).parent / 'experimentos/roteamento_natural_v2_20261009'
CASOS = {c['id']: c for c in json.loads((H/'casos_congelados.json').read_text())['casos']}


class TestesRoteamentoNaturalV2(unittest.TestCase):
    def bot_memoria(self):
        memoria = MemoriaSessao()
        bot = SimpleNamespace(memoria_sessao=memoria, dialogo_situado=SimpleNamespace(ficcao=False),
                              compositor=SimpleNamespace(resolver=lambda _: None))
        return bot

    def observar(self, bot, texto):
        nativa = bot.memoria_sessao.processar(texto)
        return encaminhar_declaracao_natural(texto, bot, nativa)

    def test_gosto_negativo_e_correcao_preservam_falas_sem_inferir_permissao(self):
        bot = self.bot_memoria()
        inicial = CASOS['pos-02']['entrada']['anteriores'][0]
        self.observar(bot, inicial)
        m = bot.memoria_sessao
        self.assertEqual('kiwi', m._atual('pessoa:zaurelio', 'gosto')['valor'])
        self.assertEqual('leite', m._atual('pessoa:zaurelio', 'não gosta')['valor'])
        self.assertIsNone(m._atual('pessoa:zaurelio', 'preferência'))
        self.assertFalse(any(f['relacao'].startswith('permissão:') for f in m.afirmacoes))
        self.assertTrue(all(f['fonte']['texto'] == inicial for f in m.afirmacoes))
        correcao = CASOS['pos-03']['entrada']['anteriores'][1]
        self.observar(bot, correcao)
        gosto = m._atual('pessoa:zaurelio', 'gosto')
        self.assertEqual(('manga', correcao), (gosto['valor'], gosto['fonte']['texto']))
        self.assertEqual('leite', m._atual('pessoa:zaurelio', 'não gosta')['valor'])

    def test_citacao_hipotese_ficcao_e_pergunta_nao_viram_declaracao(self):
        bot = self.bot_memoria()
        frases = ['Minha prima Ruvélia gosta de ameixa?',
                  'Se minha prima Ruvélia gosta de ameixa, o que ofereço?',
                  'Analise: "Minha prima Ruvélia gosta de ameixa."',
                  'Na história: minha prima Ruvélia gosta de ameixa.']
        for f in frases:
            self.observar(bot, f)
        self.assertEqual([], bot.memoria_sessao.afirmacoes)
        bot.dialogo_situado.ficcao = True
        self.observar(bot, 'Minha prima Ruvélia gosta de ameixa.')
        self.assertEqual([], bot.memoria_sessao.afirmacoes)

    def test_pronome_ambiguo_nao_atualiza_pessoas_nem_troca_por_numero(self):
        bot = Crivo(usar_geracao=False)
        bot.responder(CASOS['pos-07']['entrada']['anteriores'][0])
        antes = bot.memoria_sessao.exportar()['afirmacoes']
        bot.responder('Ele mudou de ideia: agora gosta de acerola.')
        self.assertEqual(antes, bot.memoria_sessao.afirmacoes)
        rota = rotear_natural(CASOS['pos-07']['entrada']['texto'], bot)
        self.assertEqual('esclarecimento', rota['peca'])
        self.assertEqual({'Talveno', 'Orestino'}, set(rota['referentes']))

    def _testar_guarda(self, memoria, ids, resposta, **extras):
        bot = SimpleNamespace(memoria_sessao=memoria, contexto_textual=None,
                              historico=[{'id':'conversa:memoria_sessao','memoria_sessao':{'afirmacoes':ids}}])
        rota = dict(peca='memoria', ato='consultar', sujeitos=['pessoa:nerubia'],
                    referentes=['Nerúbia'], status='executado', **extras)
        ident, _ = guardar_fidelidade(bot, rota, 'conversa:memoria_sessao', resposta)
        self.assertEqual('conversa:esclarecer', ident)
        self.assertFalse(rota['guarda']['aceita'])

    def test_prefere_nao_prova_o_que_nao_gosta_mesmo_com_id_de_memoria(self):
        m = MemoriaSessao()
        m.processar(CASOS['pos-06']['entrada']['anteriores'][0])
        f = m._atual('pessoa:nerubia', 'preferência')
        self._testar_guarda(m, [f['id']], 'Nerúbia prefere chá de hibisco.',
                          afirmacoes_esperadas=[], dado_desconhecido=True)

    def test_guarda_rejeita_troca_de_pessoa_negacao_extra_e_fato_substituido(self):
        m = MemoriaSessao()
        m.processar('Minha amiga Nerúbia prefere chá de hibisco.')
        f = m._atual('pessoa:nerubia', 'preferência')
        self._testar_guarda(m, [f['id']], 'Nerúbia recebeu a informação: Maria prefere chá de hibisco.')
        self._testar_guarda(m, [f['id']], 'Nerúbia prefere chá de hibisco. Nerúbia não prefere chá de hibisco.')
        m.processar('Nerúbia prefere água de coco.')
        self._testar_guarda(m, [f['id']], 'Nerúbia prefere chá de hibisco.')

    def test_reserva_usa_a_unidade_explicita_e_preserva_fonte_original(self):
        bot = Crivo(usar_geracao=False)
        for f in CASOS['pos-12']['entrada']['anteriores']:
            bot.responder(f)
        texto = CASOS['pos-12']['entrada']['texto']
        ident, resposta = bot.responder(texto)
        self.assertEqual('conversa:raciocinio', ident)
        self.assertIn('25 minutos', resposta)
        self.assertEqual(texto, bot.raciocinio_conversa.ultimo['fontes']['tempo:descanso']['fonte'])
        self.assertIsNone(rotear_natural('Separa 5 para descanso.', bot))

    def test_qualificador_factual_desconhecido_nao_e_descartado(self):
        bot = Crivo(usar_geracao=False)
        _, resposta = bot.responder('Agora me diga a cor de Marte na dimensão inventada.')
        self.assertIn('Marte na dimensão inventada', resposta)
        self.assertNotIn('avermelhada', resposta)


if __name__ == '__main__':
    unittest.main()
