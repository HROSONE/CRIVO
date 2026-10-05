import importlib.util
from pathlib import Path
import tempfile
import unittest

from scripts.compreensao_contrastiva import gerar, DOMINIOS


class ParticoesContrastes(unittest.TestCase):
    def test_entidades_e_pedidos_reservados_nao_entram_no_treino(self):
        for tipo in ('pessoas','objetos','lugares'):
            conjuntos=[set(DOMINIOS[s][tipo]) for s in DOMINIOS]
            for i,a in enumerate(conjuntos):
                for b in conjuntos[i+1:]:self.assertFalse(a & b)
        pedidos=[]
        for s in DOMINIOS:
            pedidos.append({c['mensagem'] for p in gerar(s) for c in p['casos']})
        for i,a in enumerate(pedidos):
            for b in pedidos[i+1:]:self.assertFalse(a & b)

    def test_contextos_opostos_nao_admitem_resposta_constante(self):
        for s in DOMINIOS:
            ps=gerar(s)
            self.assertEqual(len({p['id'] for p in ps}),len(ps))
            for p in ps:
                self.assertEqual({c['correta'] for c in p['casos']},{0,1})
                self.assertNotEqual(*p['opcoes'])
                self.assertNotEqual(*[c['mensagem'] for c in p['casos']])


DISPONIVEL=all(importlib.util.find_spec(n) for n in ('torch','tokenizers','numpy'))


@unittest.skipUnless(DISPONIVEL,'Requer dependências opcionais de treino')
class MatematicaContrastes(unittest.TestCase):
    def test_gradiente_rejeita_ambas_as_respostas_trocadas(self):
        import torch
        from scripts.compreensao_contrastiva import perdas
        scores=torch.tensor([[0.,1.],[1.,0.]],requires_grad=True)
        loss,_,_=perdas(scores,torch.tensor([0,1]));loss.backward()
        self.assertLess(float(scores.grad[0,0]),0)
        self.assertGreater(float(scores.grad[0,1]),0)
        self.assertLess(float(scores.grad[1,1]),0)
        self.assertGreater(float(scores.grad[1,0]),0)

    def test_mascara_nao_supervisiona_pedido_e_recusa_corte(self):
        from testes_linguagem_profunda import TestesMatematicaLinguagem
        from scripts.compreensao_contrastiva import lote
        from linguagem_profunda import codificar_texto
        t=TestesMatematicaLinguagem().tokenizer();t.encode_special_tokens=True
        par=gerar('treino')[0]
        x,y,c=lote(t,[par],512)
        for i in range(4):
            alvo=codificar_texto(t,par['opcoes'][i%2])+[t.token_to_id('<fim>')]
            self.assertEqual(y[i][y[i]!=-100].tolist(),alvo)
            self.assertEqual(int((y[i,:3]==-100).sum()),3)
        with self.assertRaises(ValueError):lote(t,[par],4)

    def test_retomada_adam_rng_igual_ao_treino_continuo(self):
        import contextlib
        from dataclasses import asdict
        import io
        import json
        from types import SimpleNamespace
        import torch
        from linguagem_profunda import Configuracao,LinguagemProfunda,VERSAO
        from testes_dialogo_integro import TestesDialogoIntegro
        from scripts.treinar_compreensao_contrastiva import executar,sha
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);m=TestesDialogoIntegro().fixture(p/'corpus')
            m['contexto']=256
            (p/'corpus/manifesto.json').write_text(json.dumps(m))
            t=TestesDialogoIntegro().tokenizer();conf=Configuracao(vocabulario=t.get_vocab_size(),dimensao=8,camadas=1,cabecas=2,contexto=256)
            torch.manual_seed(57);modelo=LinguagemProfunda(conf)
            (p/'inicial').mkdir();t.save(str(p/'inicial/tokenizer.json'))
            torch.save(dict(versao=VERSAO,config=asdict(conf),modelo=modelo.state_dict(),passo=0,
                execucao={'tokenizer_sha256':sha(p/'inicial/tokenizer.json')}),p/'inicial/pesos.pt')
            opts=dict(inicial=str(p/'inicial'),corpus=str(p/'corpus'),passos=4,lote=1,lr=.0001,
                semente=71,peso_contraste=1.,peso_replay=.5,avaliar_a_cada=2,threads=1,
                max_segundos=100,dispositivo='cpu',retomar=False,parar_em=None)
            with contextlib.redirect_stdout(io.StringIO()):
                executar(SimpleNamespace(**dict(opts,saida=str(p/'continuo'))))
                executar(SimpleNamespace(**dict(opts,saida=str(p/'blocos'),parar_em=2)))
                executar(SimpleNamespace(**dict(opts,saida=str(p/'blocos'),retomar=True)))
            a=torch.load(p/'continuo/checkpoint.pt',weights_only=True)
            b=torch.load(p/'blocos/checkpoint.pt',weights_only=True)
            self.assertEqual(a['passo'],b['passo']);self.assertEqual(a['rng_numpy'],b['rng_numpy'])
            self.assertTrue(torch.equal(a['rng_torch'],b['rng_torch']))
            for k,v in a['modelo'].items():self.assertTrue(torch.equal(v,b['modelo'][k]),k)
            for k,v in a['otimizador']['state'].items():
                for n,w in v.items():self.assertTrue(torch.equal(w,b['otimizador']['state'][k][n]))


if __name__=='__main__':unittest.main()
