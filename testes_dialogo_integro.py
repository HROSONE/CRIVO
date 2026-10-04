import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

DISPONIVEL=all(importlib.util.find_spec(n) for n in ('torch','tokenizers','numpy'))

@unittest.skipUnless(DISPONIVEL,'Requer dependências opcionais de treino')
class TestesDialogoIntegro(unittest.TestCase):
    def tokenizer(self):
        from testes_linguagem_profunda import TestesMatematicaLinguagem
        return TestesMatematicaLinguagem().tokenizer()

    def exemplo(self,**kw):
        e=dict(mensagem='Oi',resposta='Olá.',historico=[],origem='humano_oasst2',grupo='h1',familia='humano',split='treino')
        e.update(kw);return e

    def fixture(self,p):
        import numpy as np
        from scripts.preparar_dialogo_integro import sha
        p.mkdir();t=self.tokenizer();t.save(str(p/'tokenizer.json'))
        treino=[self.exemplo(),self.exemplo(grupo='h2',historico=[dict(papel='usuario',texto='longo '*200)]),
                self.exemplo(grupo='autoral:1',familia='conversa',origem='sintetico_autoral_assistente'),
                self.exemplo(grupo='calculado:1',familia='conversa',origem='sintetico_autoral_assistente')]
        for split in ('treino','validacao','teste'):
            es=treino if split=='treino' else [self.exemplo(split=split,grupo=split)]
            (p/('dialogos_'+split+'.jsonl')).write_text(''.join(json.dumps(e)+'\n' for e in es))
            for nome in ('x','y'):np.save(p/('dialogo_'+split+'_'+nome+'.npy'),np.zeros((len(es),64),dtype=np.int32))
            for nome in ('par','origem','familia'):np.save(p/('dialogo_'+split+'_'+nome+'.npy'),np.zeros(len(es),dtype=np.int32))
            (p/('linguagem_'+split+'.bin')).write_bytes(b'ab'*512)
        m=dict(contexto=64,particoes={'treino':{'familias':{'humano':0,'conversa':1}}},arquivos={f.name:sha(f) for f in p.iterdir()})
        (p/'manifesto.json').write_text(json.dumps(m));return m

    def test_toda_fonte_visivel_e_somente_resposta_supervisionada(self):
        from scripts.preparar_dialogo_integro import exemplo_integro
        from linguagem_profunda import segmentos_dialogo,codificar_texto
        t=self.tokenizer();e=self.exemplo(historico=[dict(papel='usuario',texto='A'),dict(papel='assistente',texto='B')])
        segmentos,atual=segmentos_dialogo(t,e['mensagem'],e['historico']);fonte=sum(segmentos,[])+atual
        alvo=codificar_texto(t,e['resposta'])+[t.token_to_id('<fim>')]
        x,y=exemplo_integro(t,e,64)
        self.assertEqual(x[:len(fonte)],fonte)
        self.assertEqual([n for n in y if n!=-100],alvo)
        self.assertEqual(y[:len(fonte)-1],[-100]*(len(fonte)-1))
        self.assertIsNone(exemplo_integro(t,e,len(fonte)+len(alvo)-2))
        self.assertEqual(len(exemplo_integro(t,e,len(fonte)+len(alvo)-1)[0]),len(fonte)+len(alvo)-1)

    def test_derivacao_preserva_reservas_replay_e_original(self):
        from scripts.preparar_dialogo_integro import preparar,sha
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);m=self.fixture(p/'origem');antes=sha(p/'origem/manifesto.json')
            r=preparar(p/'origem',p/'novo')
            self.assertEqual(r['contagens']['humanos_retidos'],1)
            self.assertEqual(r['contagens']['humanos_fora_contexto'],1)
            self.assertEqual(r['contagens']['calculados_separados'],1)
            for nome,digest in m['arquivos'].items():
                self.assertEqual(sha(p/'origem'/nome),digest)
                if 'validacao' in nome or 'teste' in nome or nome.startswith('linguagem_'):
                    self.assertEqual(sha(p/'novo'/nome),digest)
            self.assertEqual(sha(p/'origem/manifesto.json'),antes)
            with self.assertRaises(FileExistsError):preparar(p/'origem',p/'novo')

    def test_corpus_adulterado_nao_cria_saida(self):
        from scripts.preparar_dialogo_integro import preparar
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.fixture(p/'origem');(p/'origem/tokenizer.json').write_text('{}')
            with self.assertRaises(ValueError):preparar(p/'origem',p/'novo')
            self.assertFalse((p/'novo').exists())

    def test_sonda_nao_coloca_alvo_humano_no_historico(self):
        from scripts.avaliar_dialogo_integro import avaliar
        from linguagem_profunda import codificar_texto
        from types import SimpleNamespace
        t=self.tokenizer();t.encode_special_tokens=True
        item=dict(grupo='autoral:val',familia='conversa',turnos=[dict(papel=p,texto=v) for p,v in
             [('usuario','A'),('assistente','REFERENCIA 1'),('usuario','B'),('assistente','REFERENCIA 2')]])
        fontes=[]
        def fonte(tokenizer,msg,historico,contexto):
            fontes.append(list(historico));return [1]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'pesos.pt').write_bytes(b'pesos')
            with patch('scripts.avaliar_dialogo_integro.cenarios',return_value=[item]), \
                 patch('linguagem_profunda.carregar',return_value=(SimpleNamespace(config=SimpleNamespace(contexto=64)),t,{'passo':1})), \
                 patch('linguagem_profunda.fonte_dialogo',side_effect=fonte), \
                 patch('geracao_incremental.gerar',return_value=(codificar_texto(t,'Resposta gerada.'),True)):
                r=avaliar(p,p,1)
            self.assertEqual(fontes[0],[])
            self.assertEqual(fontes[1][1]['texto'],'Resposta gerada.')
            self.assertNotIn('REFERENCIA',str(fontes))
            self.assertEqual(r['turnos'],2)

if __name__=='__main__':unittest.main()
