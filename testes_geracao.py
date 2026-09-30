"""Matemática do gerador, continuidade, limites e replay sem dependências."""
import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from avaliar_geracao import avaliar
from crivo import Crivo
from geracao_conversa import geracao_valida
from linguagem_gerativa import GeradorGRU, ESPECIAIS, atributos, renderizar, tokenizar
from preparar_dialogos_geracao import combinar, validar_exemplo
from treinar_geracao import assinatura
from web_core import responder_web

RAIZ=Path(__file__).resolve().parent
try:
    import numpy as np
except ImportError:
    np=None


class TestesGeracao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados=json.loads((RAIZ/"rede_geracao.json").read_text(encoding="utf-8"))
        cls.contexto={"acao":"historia","slots":{"tema1":"Névia-27","tema2":"um lago"},
                      "mensagem":"Conte uma história sobre Névia-27 e um lago"}

    def test_sonda_completa_de_escrita_e_reparo(self):
        r=avaliar(Crivo)
        for c in r["casos"]:
            with self.subTest(caso=c["nome"]):
                self.assertTrue(c["passou"],[t for t in c["turnos"] if not t["passou"]])

    def test_pedidos_informais_de_criacao_resolvem_a_operacao(self):
        for q in ("Pode inventar um conto envolvendo Névia e Lúna?",
                  "Me conte uma história inventada com Névia e Lúna",
                  "Por favor, você poderia escrever uma história sobre Névia e Lúna?",
                  "Quero uma história sobre Névia e Lúna"):
            with self.subTest(pergunta=q):
                i,r=Crivo().responder(q)
                self.assertEqual(i,"conversa:gerada_historia")
                self.assertIn("Névia",r);self.assertIn("Lúna",r)

    def test_checkpoint_aprende_somente_treino_com_particoes_conservadas(self):
        d=json.loads((RAIZ/"curriculo_geracao.json").read_text(encoding="utf-8"))
        treino=[c for c in d["exemplos"] if c["split"]=="treino"]
        val=[c for c in d["exemplos"] if c["split"]=="validacao"]
        for chave in ("familia","dialogo"):
            self.assertFalse({c[chave] for c in treino}&{c[chave] for c in val})
        esperado=list(ESPECIAIS)+sorted({t for c in treino for t in tokenizar(c["resposta"])}-set(ESPECIAIS))
        self.assertEqual(self.dados["vocabulario"],esperado)
        self.assertEqual(self.dados["assinatura_treino"],assinatura(treino))
        self.assertEqual(self.dados["treino"]["contextos_dialogo"],len({c["dialogo"] for c in treino}))
        self.assertFalse({"respostas","exemplos","catalogo"}&set(self.dados))

    def test_proxima_palavra_depende_do_prefixo_e_do_estado(self):
        m=GeradorGRU(self.dados,acelerar=False)
        p=m.probabilidades(self.contexto)
        q=m.probabilidades(self.contexto,["Num","lugar","distante",","])
        self.assertAlmostEqual(sum(p),1)
        self.assertAlmostEqual(sum(q),1)
        self.assertGreater(sum(abs(a-b) for a,b in zip(p,q)),.5)
        self.assertNotEqual(max(range(len(p)),key=lambda i:p[i]),max(range(len(q)),key=lambda i:q[i]))
        outro=dict(self.contexto,acao="poema")
        self.assertNotEqual(m.gerar(self.contexto)["tokens"],m.gerar(outro)["tokens"])

    def test_copia_literal_de_uma_passagem_sem_interpretar_marcadores(self):
        g={"tokens":["Entre","@tema1","e","@tema2",","]}
        r=renderizar(g,{"tema1":"Névia @tema2 <texto>","tema2":"Lúna-27"})
        self.assertEqual(r,"Entre Névia @tema2 <texto> e Lúna-27,")
        with self.assertRaises(ValueError): renderizar(g,{"tema1":"Névia"})

    def test_recusa_saida_incompleta_e_repeticoes_sem_cortar_frase(self):
        g=dict(tokens=["Uma","ideia","nova","chegou",".","Outra","ideia","passou","."],
               completa=True,log_prob_media=-.1)
        self.assertTrue(geracao_valida(g,set()))
        self.assertFalse(geracao_valida(dict(g,completa=False),set()))
        self.assertFalse(geracao_valida(dict(g,tokens=g["tokens"]*2),set()))
        self.assertFalse(geracao_valida(g,{"tema1"}))
        self.assertFalse(geracao_valida(dict(g,log_prob_media=-2),set()))

    def test_inferencia_python_padrao_sem_numpy(self):
        codigo="from crivo import Crivo; b=Crivo(); assert b.responder('Invente uma história sobre Névia e Lúna')[0]=='conversa:gerada_historia'; assert b.responder('Agora dê outro final')[0]=='conversa:gerada_final'"
        r=subprocess.run([sys.executable,"-S","-c",codigo],cwd=str(RAIZ),capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stderr)

    def test_replay_http_reproduz_versoes_sem_compartilhar_sessao_ou_prova(self):
        hs=["Escreva um poema sobre Névia e Lúna","Pode fazer outra versão?"]
        payload=dict(history=hs,message="Troque Névia por Joana")
        a=responder_web(payload);b=responder_web(payload)
        self.assertEqual(a,b)
        self.assertEqual(a["id"],"conversa:gerada_poema")
        self.assertEqual(a["mechanism"],"geracao_neural")
        self.assertIn("Joana",a["response"]);self.assertNotIn("Névia",a["response"])
        self.assertFalse(a["has_proof"]);self.assertIsNone(a["plan"])
        isolado=responder_web(dict(message="Pode fazer outra versão?"))
        self.assertEqual(isolado["id"],"duvida");self.assertNotIn("Joana",isolado["response"])

    def test_fatos_fontes_negacao_e_codigo_continuam_nos_motores(self):
        for q in ("O que é DNA?","Como usar input em Python?","A Lua orbita a Terra?",
                  "O que é DNA alienígena?","Não explique memória",'print("Olá")'):
            with self.subTest(pergunta=q):
                base=Crivo();esperado=base.responder(q)
                b=Crivo();b.responder("Conte uma história sobre um sino e uma ilha")
                obtido=b.responder(q)
                self.assertEqual(obtido,esperado)
                self.assertNotIn("quadro_geracao",b.historico[-1])
        a=responder_web(dict(message="Qual é a fonte?",history=["Conte uma história sobre um sino e uma ilha","O que é DNA?"]))
        self.assertIn("genome.gov",a["response"])
        for q in ("Não invente uma história sobre um sino e uma ilha", "Se puder, invente uma história sobre um sino e uma ilha"):
            self.assertNotIn("gerada",Crivo().responder(q)[0])

    def test_ficcao_nao_se_torna_prova_nem_conteudo_da_base(self):
        arquivos=("conhecimento.json","conhecimento_expandido.json","conhecimento_mundo.json","relacoes.json",
                  "rede_crivo.json","rede_linguagem.json","rede_dialogo.json","rede_geracao.json")
        antes={p:hashlib.sha256((RAIZ/p).read_bytes()).hexdigest() for p in arquivos}
        a=responder_web(dict(message="Conte uma história sobre Relações verificadas: dragões e uma lua verde"))
        self.assertEqual(a["id"],"conversa:gerada_historia");self.assertFalse(a["has_proof"])
        self.assertEqual(antes,{p:hashlib.sha256((RAIZ/p).read_bytes()).hexdigest() for p in arquivos})

    def test_cancelamento_troca_tema_e_expiracao_limpam_criacao(self):
        for q in ("Esqueça essa conversa","Quero conversar sobre meu curso","O que é DNA?"):
            b=Crivo();b.responder("Conte uma história sobre Névia e Lúna");b.responder(q)
            self.assertIsNone(b.conversacao.geracao.ultima_criacao)
        b=Crivo();b.responder("Conte uma história sobre Névia e Lúna")
        b.conversacao.turno+=11
        self.assertEqual(b.responder("Agora dê outro final")[0],"duvida")

    def test_checkpoint_corrompido_nao_quebra_motores_existentes(self):
        d=copy.deepcopy(self.dados);d["pesos"]["O"][0][0]=float("nan")
        with self.assertRaises(ValueError): GeradorGRU(d)
        b=Crivo()
        with patch("linguagem_gerativa.carregar",side_effect=ValueError("inválido")):
            b.responder("Invente uma história sobre Névia e Lúna")
        self.assertEqual(b.conversacao.geracao.erro,"inválido")
        self.assertEqual(b.responder("O que é DNA?")[0],"conhecimento:dna")


class TestesAprendizagem(unittest.TestCase):
    def exemplo(self,**campos):
        d=dict(revisado=True,id_dialogo="humano-1",familia="humano-escrita-1",split="treino",
               contexto={"acao":"historia","slots":{"tema1":"uma ilha"},"mensagem":"Invente uma história sobre uma ilha"},
               resposta="@tema1 guardou uma pequena surpresa. No fim, outra pergunta abriu um caminho.")
        d.update(campos);return d

    def test_importacao_exige_revisao_argumentos_e_particoes(self):
        e=self.exemplo();c=validar_exemplo(e);self.assertEqual(c["dialogo"],"humano-1")
        for ruim in (dict(e,revisado=False),dict(e,resposta="Um texto sem o argumento necessário terminou aqui."),
                     dict(e,resposta="@tema2 apareceu como uma surpresa inesperada.")):
            with self.assertRaises(ValueError): validar_exemplo(ruim)
        with self.assertRaises(ValueError):
            combinar({"versao":1,"exemplos":[c]},[self.exemplo(split="validacao")])
        r=combinar({"versao":1,"exemplos":[c]},[self.exemplo(id_dialogo="humano-2",familia="humano-escrita-2",split="validacao")])
        self.assertEqual(len(r["exemplos"]),2)

    @unittest.skipIf(np is None,"NumPy necessário somente para verificar o treino")
    def test_gradiente_bptt_por_diferencas_finitas_inclui_padding(self):
        from treinar_geracao import inicializar,perda_gradientes
        p={k:v.astype("float64") for k,v in inicializar(list(ESPECIAIS)+["a","b","."],8,8).items()}
        f=np.asarray([atributos({"acao":"historia","slots":{"tema1":"a"}}),
                      atributos({"acao":"poema","slots":{"tema1":"b"}})],dtype="float64")
        x=np.asarray([[1,4,5],[1,5,0]]);y=np.asarray([[4,5,2],[5,2,0]])
        mascara=np.asarray([[1,1,1],[1,1,0]],dtype="float64")
        _,g=perda_gradientes(p,f,x,y,mascara)
        rng=np.random.default_rng(5)
        for k,v in p.items():
            for j in range(3):
                idx=tuple(int(rng.integers(t)) for t in v.shape)
                if k=="E": idx=(1 if j==0 else 5,idx[1])
                original=v[idx];eps=1e-5
                v[idx]=original+eps;a,_=perda_gradientes(p,f,x,y,mascara)
                v[idx]=original-eps;b,_=perda_gradientes(p,f,x,y,mascara)
                v[idx]=original
                with self.subTest(matriz=k,indice=idx):
                    self.assertAlmostEqual(g[k][idx],(a-b)/(2*eps),places=6)

    @unittest.skipIf(np is None,"Aceleração NumPy opcional")
    def test_numpy_e_python_calculam_mesmas_probabilidades_e_palavras(self):
        d=TestesGeracao.dados if hasattr(TestesGeracao,"dados") else json.loads((RAIZ/"rede_geracao.json").read_text(encoding="utf-8"))
        c={"acao":"poema","slots":{"tema1":"um lago","tema2":"uma ilha"}}
        a=GeradorGRU(d);b=GeradorGRU(d,acelerar=False)
        np.testing.assert_allclose(a.probabilidades(c,["Entre"]),b.probabilidades(c,["Entre"]),atol=1e-12)
        self.assertEqual(a.gerar(c)["tokens"],b.gerar(c)["tokens"])

    @unittest.skipIf(np is None,"NumPy necessário somente para treinar")
    def test_gerador_pode_aprender_um_novo_exemplo_revisado(self):
        from treinar_geracao import inicializar,lote,perda_gradientes
        c=validar_exemplo(self.exemplo())
        vs=list(ESPECIAIS)+sorted(set(tokenizar(c["resposta"])));indices={t:i for i,t in enumerate(vs)}
        p=inicializar(vs,8,8);args=lote([c],indices)
        antes,_=perda_gradientes(p,*args)
        for _ in range(20):
            _,g=perda_gradientes(p,*args)
            for k in p: p[k]-=.5*g[k]
        depois,_=perda_gradientes(p,*args)
        self.assertLess(depois,antes-.1)


if __name__=="__main__": unittest.main()
