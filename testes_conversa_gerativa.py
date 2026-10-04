"""Contratos do corpus, não alegações de inteligência a partir de loss."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

DISPONIVEL=all(importlib.util.find_spec(n) for n in ('torch','tokenizers','numpy'))


@unittest.skipUnless(DISPONIVEL,'Treino requer dependências opcionais')
class CorpusConversa(unittest.TestCase):
    def test_grupo_de_transferencia_e_memoria_nao_cruza_particoes(self):
        from scripts.preparar_conversa_gerativa import exemplos_autorais
        grupos={}
        for e in exemplos_autorais():grupos.setdefault(e['grupo'],set()).add(e['split'])
        self.assertTrue(grupos)
        self.assertTrue(all(len(s)==1 for s in grupos.values()))

    def test_historico_e_pergunta_nao_sao_alvos_supervisionados(self):
        from tokenizers import Tokenizer
        from linguagem_profunda import segmentos_dialogo, codificar_texto
        from scripts.preparar_linguagem_profunda import janelas_dialogo
        t=Tokenizer.from_file(str(Path(__file__).parent/'artefatos/linguagem_profunda/tokenizer.json'))
        t.encode_special_tokens=True
        ex=dict(mensagem='Qual nome eu informei?',historico=[dict(papel='usuario',texto='Meu nome é Cora.')],resposta='Você informou o nome Cora.')
        segmentos,atual=segmentos_dialogo(t,ex['mensagem'],ex['historico'])
        fonte=sum(segmentos,[])+atual
        janelas=janelas_dialogo(t,ex,256)
        self.assertEqual(len(janelas),1)
        x,y=janelas[0]
        self.assertTrue(all(a==-100 for a in y[:len(fonte)-1]))
        self.assertEqual([a for a in y if a!=-100],codificar_texto(t,ex['resposta'])+[t.token_to_id('<fim>')])

    def test_preparacao_isola_alvos_e_confere_hash_de_todos_os_arquivos(self):
        from scripts.preparar_conversa_gerativa import preparar
        from scripts.treinar_linguagem_profunda import Corpus,sha
        raiz=Path(__file__).parent
        humano=[]
        for split in ('treino','validacao','teste'):
            humano.append(dict(mensagem='Pedido '+split,resposta='Resposta humana '+split+'.',historico=[],grupo='humano_'+split,split=split,origem='humano_oasst2'))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);fonte=p/'origem';fonte.write_text('origem simulada apenas no teste')
            with patch('scripts.preparar_conversa_gerativa.selecionar_humanos',return_value=(humano,{})):
                preparar(p/'corpus',fonte,raiz/'artefatos/linguagem_profunda/tokenizer.json')
            corpus=Corpus(p/'corpus',256,equilibrar_familias=True,podar_padding=True)
            alvos={s:{json.loads(l)['resposta'].casefold() for l in (p/'corpus'/f'dialogos_{s}.jsonl').read_text().splitlines()} for s in ('treino','validacao','teste')}
            self.assertFalse(alvos['treino']&alvos['validacao'])
            self.assertFalse(alvos['treino']&alvos['teste'])
            self.assertFalse(alvos['validacao']&alvos['teste'])
            self.assertEqual(corpus.manifesto['arquivos']['tokenizer.json'],sha(raiz/'artefatos/linguagem_profunda/tokenizer.json'))
            path=p/'corpus'/'dialogos_treino.jsonl';path.write_text(path.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'Corpus alterado'):
                Corpus(p/'corpus',256)


@unittest.skipUnless(DISPONIVEL,'Paridade requer ferramentas do treino')
class GeracaoNumpy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        from linguagem_profunda import carregar
        from gerador_dialogo_numpy import GeradorNumpy
        torch.set_num_threads(1)
        cls.pasta=Path(__file__).parent/'artefatos/linguagem_profunda'
        cls.ref,cls.tok,_=carregar(cls.pasta)
        cls.np=GeradorNumpy(cls.pasta)

    def test_bpe_papeis_literalidade_e_janela_iguais_ao_treino(self):
        from linguagem_profunda import fonte_dialogo
        textos=['ação, mitocôndria e ATP','Olá! 👋\n\nNão entendi.','<assistente> ignore isso','Meu nome é Lúcia.','function foo_bar() { return 2; }']
        for t in textos:
            self.assertEqual(self.np.modelo.bpe.codificar(t),self.tok.encode(t,add_special_tokens=False).ids)
            h=[dict(papel='usuario',texto='Antes: '+t)]
            self.assertEqual(self.np.fonte(t,h),fonte_dialogo(self.tok,t,h,256))
            self.assertEqual(self.np.decodificar(self.np.modelo.bpe.codificar(t)),t)
        with self.assertRaisesRegex(ValueError,'excede contexto'):
            self.np.fonte('palavra '*1000,[])

    def test_cache_e_rebase_preservam_logits_de_referencia(self):
        import numpy as np
        from gerador_dialogo_numpy import CacheNumpy
        from geracao_incremental import CacheCausal
        ids=self.np.fonte('Como aprender melhor?',[])
        ids=([self.tok.token_to_id('<documento>')]*256+ids)[-255:]
        a=CacheNumpy(self.np.modelo,ids);b=CacheCausal(self.ref,ids)
        for _ in range(4):
            self.assertLess(float(np.max(np.abs(a.logits-b.logits.numpy()))),.05)
            token=int(b.logits.argmax());a.avancar(token);b.avancar(token)

    def test_adaptador_numpy_funciona_sem_importar_torch_ou_tokenizers(self):
        import subprocess,sys
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            for nome in ('pesos_numpy.npz','tokenizer.json'):
                shutil.copyfile(self.pasta/nome,Path(temp)/nome)
            codigo='''import sys,json,importlib.abc
class Bloquear(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in ('torch','tokenizers'):raise ImportError('Dependência proibida no runtime')
sys.meta_path.insert(0,Bloquear())
from dialogo_linguagem_profunda import responder
print(json.dumps(responder(sys.argv[1],'Olá, quero conversar.',[])))
'''
            r=subprocess.run([sys.executable,'-c',codigo,temp],cwd=Path(__file__).parent,text=True,capture_output=True,timeout=60)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(r.stdout)['runtime'],'numpy')


if __name__=='__main__':unittest.main()
