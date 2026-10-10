"""Contratos de fronteira: ficção, argumentos, aprovação e HTTP."""
import gzip
import json
import tempfile
import unittest
from pathlib import Path

from conversa_dialogo import conferir, carregar
from crivo import Crivo
from web_core import PedidoInvalido, responder_web

CANDIDATO = Path(__file__).parent / 'experimentos/dialogo_20261010/checkpoint_gru_dialogo.json.gz'


class TestesConversaDialogo(unittest.TestCase):
    def bot(self):
        return Crivo(checkpoint_dialogo_candidato=str(CANDIDATO))

    def test_historia_continuacao_final_e_autoria_conservam_personagem(self):
        b = self.bot()
        for t in ['Eu gosto de histórias sobre uma ariranha cartógrafa.',
                  'Escreva uma história com essa personagem em 5 frases.',
                  'Continue a história.', 'Agora muda o final: ela encontra um amigo.',
                  'Você escreveu essa história ou pegou de outro lugar?']:
            ident, texto = b.responder(t)
            if t.startswith('Eu'):
                continue
            self.assertIn('ariranha cartógrafa', texto)
            self.assertTrue(b.ultima_rota_natural['guarda']['aceita'])
        self.assertIn('gerador próprio', texto)
        self.assertEqual('historia', b.conversacao.geracao.ultima_escrita['tipo'])

    def test_detalhe_do_final_nao_se_torna_personagem_quando_falta_referente(self):
        b = self.bot()
        ident, texto = b.responder('Agora muda o final: ele encontra um amigo.')
        self.assertEqual('conversa:esclarecer', ident)
        self.assertFalse(b.dialogo_conversa.trace['usada'])
        self.assertIsNone(b.conversacao.geracao.ultima_escrita)
        self.assertNotIn('Ficção:', texto)

    def test_fatos_calculos_e_correcao_real_nao_passam_pelo_gerador(self):
        b = self.bot()
        for t in ['O que é diferença de potencial?', 'Quanto é 7 vezes 8?',
                  'Minha prima Pernélia gosta de tamarindo.',
                  'Pernélia mudou de ideia: agora gosta de graviola.',
                  'O que Pernélia gosta?']:
            _, texto = b.responder(t)
            self.assertFalse(b.dialogo_conversa.trace['usada'])
        self.assertIn('graviola', texto)
        f = b.memoria_sessao._atual('pessoa:pernelia', 'gosto')
        self.assertEqual('Pernélia mudou de ideia: agora gosta de graviola.', f['fonte']['texto'])

    def test_guarda_permite_parafrase_mas_bloqueia_nomes_numeros_e_troca_de_valor(self):
        modelo, _, _ = carregar(str(CANDIDATO.resolve()), CANDIDATO.stat().st_mtime_ns)
        ctx = dict(acao='historia',slots={'tema1':'uma ariranha cartógrafa'},mensagem='',historico=[],estilo='neutro')
        g = modelo.gerar(ctx)
        _, q = conferir(g,ctx,set(modelo.vocabulario),5)
        self.assertTrue(q['aceita'])
        for extra in ['Maria','42','prefere']:
            fake = dict(g,tokens=g['tokens']+[extra])
            _, q = conferir(fake,ctx,set(modelo.vocabulario),5)
            self.assertFalse(q['aceita'])
        fake = dict(g,tokens=[t for t in g['tokens'] if t != '@tema1'])
        _, q = conferir(fake,ctx,set(modelo.vocabulario),5)
        self.assertFalse(q['aceita'])

    def test_pesos_sem_aprovacao_nao_ativam_pela_rota_padrao(self):
        from unittest.mock import patch
        b = Crivo()
        rota = dict(peca='escrita',ato='historia',referentes=['ariranha'],personagem='ariranha',slots={'tema1':'ariranha'})
        with patch('conversa_dialogo.CHECKPOINT', CANDIDATO):
            r = b.dialogo_conversa.realizar(rota, 'Escreva uma história com ariranha.', b)
        self.assertIsNone(r)
        self.assertEqual('checkpoint_sem_aprovacao', b.dialogo_conversa.trace['motivo'])

    def test_json_publico_nao_pode_escolher_checkpoint(self):
        with self.assertRaises(PedidoInvalido):
            responder_web({'message':'Oi','checkpoint_dialogo_candidato':str(CANDIDATO)})

    def test_aprovado_true_sem_metricas_nao_ativa_o_checkpoint(self):
        from unittest.mock import patch
        dados = json.loads(gzip.decompress(CANDIDATO.read_bytes()))
        dados['controle'] = {'aprovado':True,'ativo_no_chat':True}
        with tempfile.TemporaryDirectory() as temp:
            arquivo = Path(temp)/'checkpoint.json.gz'
            arquivo.write_bytes(gzip.compress(json.dumps(dados).encode()))
            b = Crivo()
            rota = dict(peca='escrita',ato='historia',referentes=['ariranha'],personagem='ariranha',slots={'tema1':'ariranha'})
            with patch('conversa_dialogo.CHECKPOINT',arquivo):
                self.assertIsNone(b.dialogo_conversa.realizar(rota,'Escreva uma história com ariranha.',b))
            self.assertEqual('checkpoint_sem_aprovacao',b.dialogo_conversa.trace['motivo'])

    def test_api_replay_da_historia_usa_mesmos_pesos_e_argumentos(self):
        r = responder_web({'message':'Agora muda o final: ela encontra um amigo.',
                           'history':['Escreva uma história curta com uma ariranha cartógrafa.',
                                      'Continue a história.']}, checkpoint_dialogo_candidato=str(CANDIDATO))
        self.assertTrue(r['dialogue_generation']['usada'])
        self.assertTrue(r['dialogue_generation']['memoria_usada'])
        self.assertIn('ariranha cartógrafa',r['response'])
        self.assertIn('um amigo',r['response'])
        self.assertEqual('conversa',r['natural_routing']['guarda']['politica'])

    def test_rota_padrao_aprovada_entrega_historia_sem_mudar_memoria_real(self):
        b = Crivo()
        antes = list(b.memoria_sessao.afirmacoes)
        ident, texto = b.responder('Escreva uma história curta com uma ariranha cartógrafa.')
        self.assertEqual('conversa:gerada_historia',ident)
        self.assertTrue(b.dialogo_conversa.trace['usada'])
        self.assertFalse(b.dialogo_conversa.trace['experimental'])
        self.assertEqual(antes,b.memoria_sessao.afirmacoes)
        self.assertIn('ariranha cartógrafa',texto)


if __name__ == '__main__':
    unittest.main()
