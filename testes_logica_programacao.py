"""Lógica contrastiva, avaliação por casos, equilíbrio e objetivo de SFT."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from scripts.gerar_logica_programacao import aplicar,gerar
from scripts.selecao_programacao import pontuacao_validacao
ROOT=Path(__file__).resolve().parent
DISPONIVEL=all(importlib.util.find_spec(n) for n in ('torch','numpy','tokenizers'))


class TestesLogicaDados(unittest.TestCase):
    def test_composicoes_diferenciam_ordem_operador_e_limite(self):
        self.assertEqual(aplicar([-1,1],'filtrar_primeiro','maior','somar','lista',2,0),[3])
        self.assertEqual(aplicar([-1,1],'transformar_primeiro','maior','somar','lista',2,0),[1,3])
        self.assertEqual(aplicar([-1,0,1],'filtrar_primeiro','maior_igual','subtrair','soma',2,0),-3)
        self.assertEqual(aplicar([-3,2],'filtrar_primeiro','impar','escalar','lista',-2,0),[6])

    def test_generator_reproduz_dados_e_reserva_familias_e_alvos(self):
        dados=json.loads((ROOT/'dados/programacao/logica.json').read_text())['tarefas'];self.assertEqual(gerar(),dados)
        familias={};alvos={}
        for t in dados:
            familias.setdefault(t['familia'],set()).add(t['split']);alvos.setdefault(t['resposta'],set()).add(t['split'])
            self.assertNotEqual(t['contraprova']['esperado'],t['contraprova']['obtido'])
            self.assertNotEqual(t['resposta'],t['codigo_incorreto'])
            if t['tipo']=='reparo':self.assertIn('Diagnóstico:',t['mensagem'])
        self.assertEqual(len(familias),144)
        self.assertTrue(all(len(x)==1 for x in list(familias.values())+list(alvos.values())))
        reservadas={t['familia'] for t in json.loads((ROOT/'dados/programacao/tarefas.json').read_text())['tarefas'] if t['split']=='teste'}
        self.assertFalse(reservadas & familias.keys())

    def test_casos_desempatam_sem_trocar_aprovacao_completa_por_parcial(self):
        def r(n,parcial,ce):return dict(avaliacao={'dialogo':{'entropia_cruzada':ce}},funcional={'linguagens':{'javascript':dict(corretas=n,taxa_acerto_casos_por_tarefa=parcial,compilam=2,completas=2)}})
        self.assertGreater(pontuacao_validacao(r(1,.1,4),'dialogo',True),pontuacao_validacao(r(0,.9,.1),'dialogo',True))
        self.assertGreater(pontuacao_validacao(r(0,.5,4),'dialogo',True),pontuacao_validacao(r(0,.2,.1),'dialogo',True))


@unittest.skipUnless(importlib.util.find_spec('quickjs') and shutil.which('node'),'VM e Node opcionais')
class TestesCasosIsolados(unittest.TestCase):
    def test_contraexemplo_e_acerto_parcial_nao_aprovam_tarefa(self):
        from verificacao_codigo import verificar
        r=verificar('function resolver(n) { return n*2; }','javascript',[
            dict(entrada=[0],saida=0),dict(entrada=[2],saida=4),dict(entrada=[3],saida=7)])
        self.assertTrue(r['executado']);self.assertFalse(r['funcional']);self.assertEqual(r['casos_corretos'],2)
        self.assertEqual(r['contraexemplos'][0]['obtido'],6)
        self.assertEqual(r['contraexemplos'][0]['esperado'],7)

    def test_mutacao_e_protocolo_ambiguo_nao_ganham_acerto(self):
        from verificacao_codigo import verificar
        r=verificar('function resolver(xs) { xs.push(1); return xs.length; }','javascript',[dict(entrada=[[0]],saida=2)])
        self.assertFalse(r['funcional']);self.assertEqual(r['casos_corretos'],0)
        self.assertTrue(r['contraexemplos'][0]['entrada_alterada'])
        r=verificar('function resolver(n) { console.log = x => "CRIVO_RESULTADO:{}\\n" + x; return n; }','javascript',[dict(entrada=[1],saida=1)])
        self.assertFalse(r['funcional']);self.assertEqual(r['casos_corretos'],0)

    def test_typescript_confere_assinatura_contra_as_entradas(self):
        import os
        from verificacao_codigo import verificar
        tsc=os.environ.get('CRIVO_TSC')
        if not tsc:self.skipTest('TSC opcional')
        casos=[dict(entrada=[[1,2]],saida=[1,2])]
        r=verificar('function resolver(xs: number): number { return xs; }','typescript',casos,tsc=tsc)
        self.assertFalse(r['compila'])
        r=verificar('function resolver(xs: number[]): number[] { return xs; }','typescript',casos,tsc=tsc)
        self.assertTrue(r['compila']);self.assertTrue(r['funcional'])


@unittest.skipUnless(DISPONIVEL,'Dependências do laboratório opcionais')
class TestesLogicaTreino(unittest.TestCase):
    def test_perda_logica_mascara_prompt_e_preserva_marcadores(self):
        import torch
        import torch.nn.functional as F
        from scripts.perda_programacao import perda_ponderada,pesos_vocabulario
        from testes_linguagem_profunda import TestesMatematicaLinguagem
        from linguagem_profunda import ESPECIAIS
        tok=TestesMatematicaLinguagem().tokenizer();w=pesos_vocabulario(tok,4)
        for s in ESPECIAIS:self.assertEqual(float(w[tok.token_to_id(s)]),1.)
        for n in tok.encode('2+3').ids:self.assertEqual(float(w[n]),4.)
        logits=torch.tensor([[[1.,2.,3.],[3.,2.,1.],[1.,3.,2.]]],requires_grad=True)
        y=torch.tensor([[-100,1,2]]);weights=torch.tensor([1.,1.,4.])
        esperado=(F.cross_entropy(logits[0,1:2],torch.tensor([1]))+4*F.cross_entropy(logits[0,2:3],torch.tensor([2])))/5
        loss=perda_ponderada(logits,y,weights);torch.testing.assert_close(loss,esperado);loss.backward()
        self.assertTrue(torch.equal(logits.grad[0,0],torch.zeros(3)))

    def test_amostragem_equilibra_familias_e_poda_so_padding(self):
        import numpy as np
        import torch
        from scripts.treinar_linguagem_profunda import Corpus
        from linguagem_profunda import Configuracao,LinguagemProfunda
        from testes_linguagem_profunda import TestesMatematicaLinguagem
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);TestesMatematicaLinguagem().fixture_corpus(p)
            for split in ('treino','validacao','teste'):
                x=np.zeros((100,16),dtype=np.int32);x[99,:8]=1
                y=np.full_like(x,-100);y[:,:8]=x[:,:8]
                np.save(p/f'dialogo_{split}_x.npy',x);np.save(p/f'dialogo_{split}_y.npy',y)
                np.save(p/f'dialogo_{split}_origem.npy',np.zeros(100,dtype=np.int8))
                np.save(p/f'dialogo_{split}_familia.npy',np.array([0]*99+[1]))
            m=json.loads((p/'manifesto.json').read_text());m['arquivos']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.iterdir() if f.name!='manifesto.json'}
            (p/'manifesto.json').write_text(json.dumps(m))
            c=Corpus(p,16,equilibrar_familias=True,podar_padding=True)
            x,y=c.lote('treino','dialogo',1000,np.random.default_rng(42),'cpu')
            self.assertEqual(x.shape[1],8);self.assertTrue(400<int(x[:,0].sum())<600)
            torch.set_num_threads(1);modelo=LinguagemProfunda(Configuracao(vocabulario=m['vocabulario'],dimensao=24,camadas=1,cabecas=3,contexto=16,dropout=0)).eval()
            xp=F_pad(x[:2],8,0);yp=F_pad(y[:2],8,-100)
            torch.testing.assert_close(modelo(x[:2],y[:2])[1],modelo(xp,yp)[1])


def F_pad(x,n,value):
    import torch.nn.functional as F
    return F.pad(x,(0,n),value=value)


if __name__=='__main__':unittest.main()
