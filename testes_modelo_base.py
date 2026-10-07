"""Integração, indisponibilidade e separação entre geração e prova."""
import unittest
import json
from unittest.mock import patch, MagicMock
from modelo_base import ModeloBase
from crivo import Crivo
from web_core import responder_web


class Provedor:
    modelo='modelo-teste'
    def __init__(self,erro=False):self.chamadas=[];self.erro=erro
    def gerar(self,p,contexto='',historico=()):
        self.chamadas.append((p,contexto,list(historico)))
        if self.erro:raise OSError('indisponível')
        return 'Resposta do modelo com contexto.'


class TestesModeloBase(unittest.TestCase):
    def test_sem_endpoint_nao_habilita_rede(self):
        with patch.dict('os.environ',{},clear=True):self.assertIsNone(ModeloBase.do_ambiente())

    def test_configuracao_rejeita_urls_com_credenciais(self):
        for url in ('file:///tmp/p','https://usuario:senha@host/v1','https://host/v1?key=segredo'):
            with self.assertRaises(ValueError):ModeloBase(url,'m')

    def test_protocolo_rejeita_resposta_truncada(self):
        resposta=MagicMock()
        resposta.__enter__.return_value.read.return_value=json.dumps(
            {'choices':[{'finish_reason':'length','message':{'content':'texto parcial'}}]}).encode()
        with patch('urllib.request.urlopen',return_value=resposta):
            with self.assertRaises(ValueError):ModeloBase('http://localhost:1/v1','m').gerar('resuma')

    def test_conteudo_original_chega_ao_modelo_sem_certificacao(self):
        p=Provedor();r=responder_web({'message':'Resuma este texto: A coleta falhou. A equipe refez a coleta.'},modelo_base=p)
        self.assertEqual(r['response'],'Resposta do modelo com contexto.')
        self.assertIn('A coleta falhou',p.chamadas[0][1])
        self.assertTrue(r['external_ai']);self.assertFalse(r['has_proof'])
        self.assertNotIn('content_analysis',r)
        self.assertEqual(r['mechanism'],'modelo_base')

    def test_replay_nao_chama_provedor(self):
        p=Provedor();responder_web({'message':'Resuma isso','history':['Texto: A coleta falhou. A equipe refez a coleta.']},modelo_base=p)
        self.assertEqual(len(p.chamadas),1)

    def test_indisponibilidade_conserva_resposta_local(self):
        p=Provedor(erro=True);r=responder_web({'message':'Resuma este texto: A coleta falhou. A equipe refez a coleta.'},modelo_base=p)
        self.assertEqual(r['id'],'texto:resumo');self.assertFalse(r['base_generation']['used'])
        self.assertEqual(r['base_generation']['reason'],'provider_unavailable')

    def test_referencia_exata_nao_e_substituida(self):
        p=Provedor();r=responder_web({'message':'Explique João 3:16'},modelo_base=p)
        self.assertFalse(p.chamadas);self.assertIn('Referência:',r['response'])

    def test_crise_nao_e_encaminhada(self):
        p=Provedor();b=Crivo(modelo_base=p);b.responder('Vou me matar agora')
        self.assertFalse(p.chamadas)

    def test_correcao_neural_nao_exibe_diff_de_outro_motor(self):
        p=Provedor();r=responder_web({'message':'Corrija este texto: eu nao sei escrever'},modelo_base=p)
        self.assertTrue(r['base_generation']['used']);self.assertNotIn('text_correction',r)

    def test_alteracoes_sao_da_correcao_realmente_mostrada(self):
        b=Crivo(modelo_base=Provedor());b.responder('Corrija este texto: eu nao sei escrever')
        corrigido=b.analise_conteudo.correcao['corrigido']
        ident,texto=b.responder('Mostre as alterações')
        self.assertEqual(ident,'texto:alteracoes')
        self.assertEqual(b.ultima_correcao_texto['metodo'],'modelo_base')
        self.assertEqual(corrigido,'Resposta do modelo com contexto.')
        self.assertIn('Resposta',texto)


if __name__=='__main__':unittest.main()
