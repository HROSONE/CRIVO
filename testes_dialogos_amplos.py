"""Integridade de dados, contexto, amostragem e retomada da nova rodada GPU."""
import ast
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).parent
DISPONIVEL=all(importlib.util.find_spec(n) for n in ('torch','numpy','tokenizers'))


@unittest.skipUnless(DISPONIVEL,'Preparação opcional requer ferramentas de treino')
class DialogosAmpliados(unittest.TestCase):
    def test_cenarios_inteiros_e_ids_unicos(self):
        from scripts.curriculo_dialogos_amplos import exemplos_amplos
        es=list(exemplos_amplos());grupos={};ids=set()
        self.assertGreater(len(es),4500)
        for e in es:
            self.assertNotIn(e['source_id'],ids);ids.add(e['source_id'])
            grupos.setdefault(e['grupo'],set()).add(e['split'])
            self.assertEqual(e['origem'],'sintetico_autoral_assistente')
            for i,h in enumerate(e['historico']):
                self.assertEqual(h['papel'],'usuario' if i%2==0 else 'assistente')
        self.assertTrue(all(len(s)==1 for s in grupos.values()))
        self.assertGreater(sum(bool(e['historico']) for e in es),3000)

    def test_codigo_dos_exercicios_concorda_com_javascript_real(self):
        if not importlib.util.find_spec('quickjs'):self.skipTest('QuickJS opcional')
        import quickjs
        from scripts.curriculo_dialogos_amplos import exemplos_amplos
        ctx=quickjs.Context()
        for e in exemplos_amplos():
            if not e['grupo'].startswith('calculado:programacao:'):continue
            n=int(e['grupo'].rsplit(':',1)[1]);arr=[n-3,n+1,n+5]
            if not e['historico']:
                codigo=f'JSON.stringify({arr}.map(x => x*2))'
            elif len(e['historico'])==2:
                codigo=f'JSON.stringify({arr}.filter(x => x>{n}))'
            else:continue
            esperado=json.loads(ctx.eval(codigo))
            self.assertIn(str(esperado),e['resposta'])

    def test_novo_contexto_preserva_orcamento_de_tokens_e_pesos_proprios(self):
        from scripts.experimento_transformer_16m import carregar_config
        d,c,n=carregar_config(ROOT/'configs/transformer_16m_dialogos.json')
        self.assertEqual((n,c.contexto),(15953664,512))
        self.assertEqual(d['pretreino']['passos']*d['pretreino']['lote']*c.contexto,184320000)
        self.assertFalse(d['pesos_externos']);self.assertFalse(d['promocao_automatica'])

    def test_corpus_v2_isola_fontes_alvos_arvores_e_nao_corta_contexto_autoral(self):
        from scripts.preparar_conversa_gerativa import preparar
        from scripts.preparar_linguagem_profunda import normalizar
        from scripts.treinar_linguagem_profunda import Corpus
        from linguagem_profunda import segmentos_dialogo,codificar_texto
        from tokenizers import Tokenizer
        humanos=[dict(mensagem='Pedido humano '+s,resposta='Resposta humana exclusiva '+s,
                      historico=[],grupo='humano_'+s,source_id='fixture_'+s,split=s,
                      origem='humano_oasst2',familia='humano') for s in ('treino','validacao','teste')]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);fonte=p/'fonte';fonte.write_text('fixture local')
            with patch('scripts.curar_oasst2_completo.selecionar_completo',return_value=(humanos,{})),patch('builtins.print'):
                preparar(p/'corpus',fonte,ROOT/'artefatos/linguagem_profunda/tokenizer.json',
                         dialogos_amplos=True,oasst2_completo=fonte,contexto=512)
            dados=Corpus(p/'corpus',512,podar_padding=True)
            t=Tokenizer.from_file(str(p/'corpus/tokenizer.json'));t.encode_special_tokens=True
            vistos={k:{} for k in ('grupo','fonte','alvo')}
            for s in ('treino','validacao','teste'):
                for l in (p/'corpus'/f'dialogos_{s}.jsonl').read_text().splitlines():
                    e=json.loads(l)
                    chaves={'grupo':e['grupo'],'fonte':tuple(normalizar(h['texto']) for h in e['historico'])+(normalizar(e['mensagem']),),'alvo':normalizar(e['resposta'])}
                    for k,v in chaves.items():
                        self.assertIn(vistos[k].setdefault(v,s),[s])
                    if e['origem']!='humano_oasst2':
                        seg,atual=segmentos_dialogo(t,e['mensagem'],e['historico'])
                        self.assertLessEqual(sum(map(len,seg))+len(atual)+len(codificar_texto(t,e['resposta']))+1,513)
            self.assertEqual(dados.manifesto['amostragem_dialogo']['fracao_humana'],.75)
            path=p/'corpus/dialogo_treino_par.npy';path.write_bytes(path.read_bytes()+b'alteracao')
            with self.assertRaisesRegex(ValueError,'Corpus alterado'):
                Corpus(p/'corpus',512)

    def test_fonte_completa_corrompida_e_recusada(self):
        from scripts.curar_oasst2_completo import selecionar_completo
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'origem.gz';p.write_bytes(b'nao e uma fonte publica verificada')
            with self.assertRaisesRegex(ValueError,'revisão pública'):
                selecionar_completo(p,p)

    def test_exportacoes_nao_duplicam_mensagens_e_recusam_conflitos_e_erros_ancestrais(self):
        from scripts import curar_oasst2_completo as curador
        from scripts.curar_dialogos_humanos import revisada
        from scripts.preparar_linguagem_profunda import sha
        def msg(id,role,parent=None,text='Texto de teste sem identidade externa.'):
            return dict(message_id=id,message_tree_id='raiz',role=role,parent_id=parent,text=text,
                        lang='pt-BR',review_result=True,synthetic=False,deleted=False,
                        labels={k:{'value':0} for k in ('spam','lang_mismatch','pii','not_appropriate','hate_speech','sexual_content','toxicity','violence')})
        root=msg('raiz','prompter');a=msg('alvo','assistant','raiz');b=msg('alvo2','assistant','raiz',text='Outra resposta apenas para a fixture.')
        self.assertTrue(revisada(root))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'completo.gz'
            def escrever(ms):
                with gzip.open(p,'wt') as f:
                    for m in ms:f.write(json.dumps(m)+'\n')
            escrever([root,a,b])
            with patch.object(curador,'ler_mensagens',return_value=[root,a]),patch.dict(curador.FONTES['oasst2_completo'],{'sha256':sha(p)}):
                es,_=curador.selecionar_completo('ready',p)
                self.assertEqual({e['source_id'] for e in es},{'alvo','alvo2'})
                self.assertEqual(sum(e['fonte_exportacao']=='completa' for e in es),1)
                with patch.dict(curador.RECUSAS_CONTEUDO,{'raiz':'erro na raiz'}):
                    self.assertEqual(curador.selecionar_completo('ready',p)[0],[])
            diferente=dict(a,text='Texto conflitante');escrever([root,diferente,b])
            with patch.object(curador,'ler_mensagens',return_value=[root,a]),patch.dict(curador.FONTES['oasst2_completo'],{'sha256':sha(p)}):
                with self.assertRaisesRegex(ValueError,'conflita'):
                    curador.selecionar_completo('ready',p)

    @staticmethod
    def fixture(p):
        import numpy as np
        from testes_linguagem_profunda import TestesMatematicaLinguagem
        from scripts.preparar_linguagem_profunda import sha
        TestesMatematicaLinguagem().fixture_corpus(p)
        manifesto=json.loads((p/'manifesto.json').read_text())
        pares=np.array([0]+[1]*30+[2]+[3]*100,dtype=np.int32)
        origens=np.array([1]*31+[0]*101,dtype=np.int8)
        familias=np.array([0]*31+[1]+[2]*100,dtype=np.int16)
        x=np.repeat((pares+1)[:,None],16,axis=1).astype(np.int32);y=x.copy()
        for split in ('treino','validacao','teste'):
            for nome,a in (('x',x),('y',y),('par',pares),('origem',origens),('familia',familias)):
                np.save(p/f'dialogo_{split}_{nome}.npy',a)
        manifesto['amostragem_dialogo']=dict(fracao_humana=.75,pares_uniformes=True,sinteticos_por_familia=True)
        manifesto['arquivos']={f.name:sha(f) for f in p.iterdir() if f.name!='manifesto.json'}
        (p/'manifesto.json').write_text(json.dumps(manifesto))

    def test_amostragem_nao_prioriza_respostas_longas_nem_familias_numerosas(self):
        import numpy as np
        from scripts.treinar_linguagem_profunda import Corpus
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);self.fixture(p);c=Corpus(p,16);rng=np.random.default_rng(42)
            contagens={i:0 for i in range(1,5)}
            for _ in range(200):
                x,_=c.lote('treino','dialogo',12,rng,'cpu')
                ids=x[:,0].tolist()
                self.assertEqual(sum(i<=2 for i in ids),9)
                for i in ids:contagens[i]+=1
            self.assertTrue(.4<contagens[1]/(contagens[1]+contagens[2])<.6)
            self.assertTrue(.4<contagens[3]/(contagens[3]+contagens[4])<.6)
            with self.assertRaisesRegex(ValueError,'Não combinar'):
                Corpus(p,16,equilibrar_familias=True)

    def test_retomada_ampla_preserva_adam_rng_e_respeita_parada_validacao(self):
        import torch
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);corpus=p/'corpus';corpus.mkdir();self.fixture(corpus)
            base=[sys.executable,str(ROOT/'scripts/treinar_linguagem_profunda.py'),'--corpus',str(corpus),
                  '--passos','4','--lote','4','--dimensao','24','--camadas','1','--cabecas','3',
                  '--contexto','16','--threads','1','--dispositivo','cpu','--avaliar-a-cada','2','--salvar-a-cada','2']
            def rodar(args):
                r=subprocess.run(args,capture_output=True,text=True,timeout=90)
                self.assertEqual(r.returncode,0,r.stderr)
            rodar(base+['--saida',str(p/'pre')])
            sft=base+['--fase','dialogo','--selecionar-melhor','--selecao-humana','--repeticao-linguagem','0']
            rodar(sft+['--saida',str(p/'inteiro'),'--inicial',str(p/'pre')])
            rodar(sft+['--saida',str(p/'blocos'),'--inicial',str(p/'pre'),'--parar-em','2'])
            rodar(sft+['--saida',str(p/'blocos'),'--retomar'])
            a=torch.load(p/'inteiro/checkpoint.pt',weights_only=True);b=torch.load(p/'blocos/checkpoint.pt',weights_only=True)
            self.assertEqual(a['historico'],b['historico']);self.assertEqual(a['rng_numpy'],b['rng_numpy'])
            self.assertTrue(torch.equal(a['rng_torch'],b['rng_torch']))
            for k,v in a['modelo'].items():self.assertTrue(torch.equal(v,b['modelo'][k]),k)
            for k,estado in a['otimizador']['state'].items():
                for campo,v in estado.items():self.assertTrue(torch.equal(v,b['otimizador']['state'][k][campo]))
            parada=sft+['--passos','8','--lr','1e-20','--paciencia-validacoes','2']
            rodar(parada+['--saida',str(p/'parada'),'--inicial',str(p/'pre')])
            antes=torch.load(p/'parada/checkpoint.pt',weights_only=True)
            report=json.loads((p/'parada/relatorio.json').read_text())
            self.assertTrue(report['parada_validacao']);self.assertFalse(report['pausado']);self.assertEqual(antes['passo'],4)
            rodar(parada+['--saida',str(p/'parada'),'--retomar'])
            depois=torch.load(p/'parada/checkpoint.pt',weights_only=True)
            self.assertEqual(antes['passo'],depois['passo']);self.assertEqual(antes['historico'],depois['historico'])
            self.assertTrue(torch.equal(antes['rng_torch'],depois['rng_torch']))

    def test_baseline_de_contexto_menor_preserva_todos_os_alvos_retidos(self):
        from scripts.avaliar_conversa_gerativa import janelas_retidas
        from scripts.preparar_linguagem_profunda import janelas_dialogo
        from linguagem_profunda import codificar_texto
        from tokenizers import Tokenizer
        from types import SimpleNamespace
        t=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));t.encode_special_tokens=True
        es=[dict(mensagem='Explique o resultado '+str(i),resposta='uma resposta longa e completa '*40,
                 historico=[dict(papel='usuario',texto='Este histórico não é alvo.')],origem=origem)
            for i,origem in enumerate(('humano_oasst2','sintetico_autoral_assistente'))]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'dialogos_validacao.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in es))
            cp=SimpleNamespace(caminho=p,manifesto={'contexto':512})
            x,y,o=janelas_retidas(cp,t,128,'validacao')
            self.assertEqual(x.shape[1],128)
            esperado=codificar_texto(t,es[0]['resposta'])+[t.token_to_id('<fim>')]
            for origem in (0,1):
                self.assertEqual(y[o==origem][y[o==origem]!=-100].tolist(),esperado)
            self.assertEqual(int((y!=-100).sum()),sum(sum(a!=-100 for a in alvo)
                for e in es for _,alvo in janelas_dialogo(t,e,512)))

    def test_notebook_amplo_usa_experimento_separado_e_codigo_executavel(self):
        n=json.loads((ROOT/'notebooks/treinar_dialogos_amplos_colab.ipynb').read_text())
        for i,c in enumerate(n['cells']):
            if c['cell_type']=='code':compile(''.join(c['source']),f'cell{i}','exec')
        inicio=''.join(n['cells'][1]['source'])
        self.assertIn('MyDrive/CRIVO/dialogos-amplos-v2',inicio)
        self.assertIn('configs/transformer_16m_dialogos.json',inicio)
        self.assertIn('parada_validacao',''.join(n['cells'][9]['source']))
        fonte=''.join(n['cells'][1]['source']);arvore=ast.parse(fonte)
        funcao=next(x for x in arvore.body if isinstance(x,ast.FunctionDef) and x.name=='treinar_etapa')
        chamadas=[]
        def bloco(etapa):
            chamadas.append(etapa)
            return dict(passo=2,horizonte=10,parada_validacao=True)
        env=dict(BLOCOS_POR_EXECUCAO=10,treinar_bloco=bloco)
        exec(compile(ast.Module(body=[funcao],type_ignores=[]),'etapa-colab','exec'),env)
        env['treinar_etapa']('dialogo');self.assertEqual(chamadas,['dialogo'])


if __name__=='__main__':unittest.main()
