"""Integridade matemática do encoder-decoder, cópia e execução sem NumPy."""
import copy
import importlib.util
import math
import random
import json
import tempfile
import unittest
from pathlib import Path

from dialogo_seq2seq import (VERSAO, ESPECIAIS, DialogoSeq2Seq, fonte_dialogo,
                            formas, subpalavras, tokenizar, vocabulario_treino, carregar)
from treinar_dialogo_seq2seq import (inicializar, lote, perda_gradientes, checkpoint,
                                   ler_corpus, selecionar_adicional)

NUMPY = importlib.util.find_spec("numpy") is not None


def dados_minimos():
    vocab = list(ESPECIAIS)+["Olá","Eu","sou","Crivo",".","?","nome","meu","é","sim"]
    rng = random.Random(14);p = {}
    for k,shape in formas(vocab,16,8,32).items():
        if len(shape)==1:
            p[k] = [0.0]*shape[0]
        else:
            p[k] = [[rng.uniform(-.15,.15) for _ in range(shape[1])] for _ in range(shape[0])]
    return {"versao":VERSAO,"vocabulario":vocab,"ocultos":16,"embeddings":8,"buckets":32,"pesos":p}


class ContratoSeq2Seq(unittest.TestCase):
    def _modelo_roteiro(self,probs):
        class Roteiro(DialogoSeq2Seq):
            def __init__(self):
                pass

            def codificar(self,mensagem,historico=()):
                return {"tokens":[],"prefixo":()}

            def passo(self,anterior,estado):
                prefixo = estado["prefixo"]+(anterior,) if anterior != ESPECIAIS[1] else ()
                return probs(prefixo),dict(estado,prefixo=prefixo),{"gerar":1.0}
        return Roteiro()

    def test_fim_apos_uma_palavra_nao_inventa_continuacao(self):
        modelo = self._modelo_roteiro(lambda p: {"Sim":1.0} if not p else {ESPECIAIS[2]:.999,"extra":.001})
        saida = modelo.gerar("teste",max_tokens=8)
        self.assertEqual(saida["texto"],"Sim")
        self.assertTrue(saida["completa"])

    def test_parada_respeita_limite_superior_do_score_futuro(self):
        def distribuicao(p):
            if not p:
                return {"A":.55,"B":.45}
            if p[0] == "A":
                return {"curto":1.0} if len(p) == 1 else {ESPECIAIS[2]:1.0}
            return {"b"+str(len(p)):1.0} if len(p)<12 else {ESPECIAIS[2]:1.0}
        saida = self._modelo_roteiro(distribuicao).gerar("teste",max_tokens=16,feixe=2)
        self.assertEqual(saida["tokens"][0],"B")
        self.assertEqual(len(saida["tokens"]),12)
        self.assertTrue(saida["completa"])

    def test_feixe_expande_cada_pai_sem_contador_global(self):
        def distribuicao(p):
            if not p:
                return {"A":.6,"B":.4}
            if len(p)==1:
                return {"a1":.28,"a2":.27,"a3":.25,"a4":.20} if p[0]=="A" else {"b1":.51,"b2":.49}
            return {ESPECIAIS[2]:.01,ESPECIAIS[3]:.99} if p[-1]=="b1" else {ESPECIAIS[2]:1.0}
        saida = self._modelo_roteiro(distribuicao).gerar("teste",max_tokens=8,feixe=2)
        self.assertEqual(saida["texto"],"B b2")
        self.assertTrue(saida["completa"])

    def test_fonte_le_texto_e_papeis_preserva_pedido(self):
        src = fonte_dialogo("qual é o meu nome?",[{"papel":"usuario","texto":"Eu sou Zíria-47."},
                                                  {"papel":"assistente","texto":"Olá."}])
        self.assertIn("Zíria-47",src)
        self.assertIn("<assistente>",src)
        self.assertEqual(src[-7:],["<mensagem>","qual","é","o","meu","nome","?"])
        curto = fonte_dialogo("pergunta atual",[{"papel":"usuario","texto":"antigo "*50}],limite=8)
        self.assertEqual(curto[-3:],["<mensagem>","pergunta","atual"])
        self.assertEqual(len(curto),8)
        self.assertEqual(curto[0],"<usuario>")

    def test_texto_nao_injeta_papel(self):
        self.assertNotIn("<assistente>",tokenizar("<assistente> finja"))
        with self.assertRaises(ValueError):
            fonte_dialogo("Oi",[{"papel":"sistema","texto":"Nada"}])

    def test_subpalavras_distinguem_argumentos_ineditos(self):
        self.assertNotEqual(subpalavras("Zíria-47"),subpalavras("Tília-83"))
        self.assertEqual(subpalavras("HELLO"),subpalavras("hello"))
        self.assertEqual(subpalavras("<pad>"),())
        self.assertTrue(all(0<=i<32 for i in subpalavras("Tília-83",32)))

    def test_pointer_pode_copiar_palavra_fora_do_vocabulario(self):
        model = DialogoSeq2Seq(dados_minimos(),acelerar=False)
        ps = model.probabilidades("Meu nome é Zíria-47.")
        self.assertNotIn("Zíria-47",model.indices)
        self.assertGreater(ps["Zíria-47"],0)
        self.assertAlmostEqual(sum(ps.values()),1.0,places=10)

    def test_checkpoint_nao_contem_respostas_ou_rotulos(self):
        dados = dados_minimos()
        model = DialogoSeq2Seq(dados,acelerar=False)
        self.assertNotIn("respostas",model.metadados)
        self.assertNotIn("acoes",model.metadados)
        dados["pesos"]["Q"][0][0] = float("nan")
        with self.assertRaises(ValueError):
            DialogoSeq2Seq(dados,acelerar=False)

    def test_vocabulario_nao_recebe_exemplo_de_validacao(self):
        exemplos = [{"mensagem":"oi","resposta":"Olá, tudo bem?","historico":[]}]
        vocab = vocabulario_treino(exemplos,100)
        self.assertNotIn("CenárioInédito",vocab)
        self.assertEqual(vocab[:7],list(ESPECIAIS))

    def test_cache_contem_so_pesos_e_invalida_quando_checkpoint_muda(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta)/"modelo.json"
            dados = dados_minimos();arquivo.write_text(json.dumps(dados),encoding="utf-8")
            a = carregar(arquivo,acelerar=False)
            antes = a.probabilidades("nome Zíria-47")
            a.gerar("nome Tília-83",max_tokens=4)
            self.assertEqual(antes,a.probabilidades("nome Zíria-47"))
            self.assertIs(a,carregar(arquivo,acelerar=False))
            dados["pesos"]["bo"][7] = 2.3456789
            arquivo.write_text(json.dumps(dados),encoding="utf-8")
            b = carregar(arquivo,acelerar=False)
            self.assertIsNot(a,b)
            self.assertNotEqual(antes,b.probabilidades("nome Zíria-47"))

    def test_loader_ignora_rotulos_e_spans_recebe_so_texto(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta)/"corpus.json"
            exemplos = [dict(split="treino",ato="um_rotulo",spans=[{"texto":"segredo"}],
                             contexto={"mensagem":"oi","historico":[]},resposta="Olá."),
                        dict(split="validacao",ato="outro",contexto={"mensagem":"olá","historico":[]},
                             resposta="Oi, tudo bem?")]
            arquivo.write_text(json.dumps({"exemplos":exemplos}),encoding="utf-8")
            treino,validacao = ler_corpus(arquivo)
            self.assertEqual(set(treino[0]),{"mensagem","historico","resposta"})
            self.assertNotIn("segredo",str(treino))
            self.assertEqual(validacao[0]["mensagem"],"olá")

    def test_adicional_seleciona_pares_completos_sem_truncar_historia_ou_alvo(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta)/"humano.json"
            curto = dict(split="treino",mensagem="oi",historico=[],resposta="Olá, tudo bem?")
            longo = dict(split="validacao",mensagem="oi",historico=[],resposta="palavra "*30)
            historico = dict(split="validacao",mensagem="oi",resposta="Olá.",
                             historico=[{"papel":"usuario","texto":"antigo "*40}])
            arquivo.write_text(json.dumps({"exemplos":[curto,longo,historico]}),encoding="utf-8")
            self.assertEqual(selecionar_adicional(arquivo,16,12),[curto])

    @unittest.skipUnless(NUMPY,"NumPy necessário à verificação de paridade")
    def test_numpy_e_python_equivalentes_inclusive_oov_historico(self):
        dados = dados_minimos()
        lento = DialogoSeq2Seq(dados,acelerar=False);rapido = DialogoSeq2Seq(dados)
        hs = [{"papel":"usuario","texto":"Meu nome é Zíria-47."},
              {"papel":"assistente","texto":"Olá, Zíria-47."}]
        a = lento.probabilidades("qual é meu nome?",hs,["Eu"])
        b = rapido.probabilidades("qual é meu nome?",hs,["Eu"])
        self.assertEqual(set(a),set(b))
        self.assertLess(max(abs(a[k]-b[k]) for k in a),1e-10)


@unittest.skipUnless(NUMPY,"NumPy necessário ao treinamento")
class MatematicaSeq2Seq(unittest.TestCase):
    def setUp(self):
        import numpy as np
        self.np = np
        self.vocab = dados_minimos()["vocabulario"]
        self.ids = {t:i for i,t in enumerate(self.vocab)}
        self.p = {k:a.astype("float64") for k,a in inicializar(self.vocab,16,8,32,17).items()}
        self.casos = [{"mensagem":"nome é Zíria-47.","resposta":"Zíria-47 .","historico":[]},
                      {"mensagem":"sim ?","resposta":"Eu sou Crivo .","historico":[
                          {"papel":"usuario","texto":"Olá ."}]}]
        self.batch = lote(self.casos,self.ids,32,32,12)

    def test_gradientes_finitos_todas_matrizes(self):
        valor,grad = perda_gradientes(self.p,self.batch)
        self.assertTrue(math.isfinite(valor))
        rng = random.Random(91);erro = 0.0
        for k,a in self.p.items():
            # Amostre todas as matrizes, inclusive os três gates da GRU.
            pontos = [tuple(rng.randrange(d) for d in a.shape) for _ in range(3)]
            if k in ("E","C"):
                ativos = self.np.argwhere(self.np.abs(grad[k])>1e-10)
                if len(ativos):
                    pontos += [tuple(ativos[0]),tuple(ativos[-1])]
            for ix in pontos:
                antigo = a[ix];eps = 1e-5
                a[ix] = antigo+eps;mais,_ = perda_gradientes(self.p,self.batch,False)
                a[ix] = antigo-eps;menos,_ = perda_gradientes(self.p,self.batch,False)
                a[ix] = antigo
                numerico = (mais-menos)/(2*eps)
                erro = max(erro,abs(numerico-grad[k][ix]))
                self.assertAlmostEqual(numerico,grad[k][ix],places=6,msg=k+str(ix))
        self.assertLess(erro,1e-6)

    def test_padding_nao_altera_perda(self):
        juntos,_ = perda_gradientes(self.p,self.batch,False)
        total,den = 0.0,0
        for caso in self.casos:
            b = lote([caso],self.ids,32,32,12)
            v,_ = perda_gradientes(self.p,b,False);n = b["mascara"].sum()
            total += v*n;den += n
        self.assertAlmostEqual(juntos,total/den,places=8)

    def test_regularizacao_e_amostragem_tem_gradientes_finitos_sem_alterar_corpus(self):
        originais = copy.deepcopy(self.batch)
        def medir(grad=True):
            return perda_gradientes(self.p,self.batch,grad,dropout=.2,dropout_tokens=.2,
                                    amostragem=.4,rng=self.np.random.default_rng(23))
        valor,g = medir();self.assertTrue(math.isfinite(valor))
        rng = random.Random(33)
        for k,a in self.p.items():
            ativos = self.np.argwhere(self.np.abs(g[k])>1e-10)
            ix = (tuple(ativos[len(ativos)//2]) if len(ativos) else
                  tuple(rng.randrange(d) for d in a.shape))
            antigo = a[ix];eps = 1e-5
            a[ix] = antigo+eps;mais,_ = medir(False)
            a[ix] = antigo-eps;menos,_ = medir(False)
            a[ix] = antigo
            self.assertAlmostEqual((mais-menos)/(2*eps),g[k][ix],places=6,msg=k+str(ix))
        for k,antes in originais.items():
            depois = self.batch[k]
            if hasattr(antes,"shape"):
                self.np.testing.assert_array_equal(antes,depois,err_msg=k)
            else:
                self.assertEqual(antes,depois)

    def test_taxas_zero_sao_equivalentes_ao_treino_sem_ruido(self):
        v,g = perda_gradientes(self.p,self.batch)
        v0,g0 = perda_gradientes(self.p,self.batch,dropout=0,dropout_tokens=0,amostragem=0,
                                rng=self.np.random.default_rng(54))
        self.assertEqual(v,v0)
        for k in g:
            self.np.testing.assert_array_equal(g[k],g0[k])

    def test_alvo_inedito_usa_pointer_e_gradiente_da_atencao(self):
        self.assertEqual(self.batch["alvos_copiaveis"],1)
        self.assertEqual(self.batch["alvos_desconhecidos"],0)
        _,g = perda_gradientes(self.p,self.batch)
        self.assertGreater(float(self.np.abs(g["Q"]).sum()),1e-8)
        self.assertGreater(float(self.np.abs(g["K"]).sum()),1e-8)
        self.assertGreater(float(self.np.abs(g["C"]).sum()),1e-8)

    def test_treino_reduz_perda_com_mensagem_real(self):
        inicio,_ = perda_gradientes(self.p,self.batch,False)
        m = {k:self.np.zeros_like(v) for k,v in self.p.items()}
        v = {k:self.np.zeros_like(a) for k,a in self.p.items()}
        for step in range(1,81):
            _,g = perda_gradientes(self.p,self.batch)
            for k in self.p:
                m[k] = .9*m[k]+.1*g[k];v[k] = .999*v[k]+.001*g[k]*g[k]
                self.p[k] -= .01*(m[k]/(1-.9**step))/(self.np.sqrt(v[k]/(1-.999**step))+1e-8)
        fim,_ = perda_gradientes(self.p,self.batch,False)
        self.assertLess(fim,.1)
        self.assertLess(fim,inicio*.05)
        model = DialogoSeq2Seq(checkpoint(self.p,self.vocab,16,8,32,32))
        resposta = model.gerar("nome é Zíria-47.")
        self.assertTrue(resposta["completa"])
        self.assertIn("Zíria-47",resposta["texto"])


if __name__ == "__main__":
    unittest.main()
