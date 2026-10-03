"""Causalidade, texto literal, perdas de SFT e retomada real do novo laboratório."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

DISPONIVEL = all(importlib.util.find_spec(n) for n in ('torch', 'tokenizers', 'numpy'))
ROOT = Path(__file__).resolve().parent


class TestesCuradoriaPublica(unittest.TestCase):
    def registro(self, pedido, resposta, fonte=None):
        from scripts.curar_instrucoes_publicas import FONTE
        return {'metadata': FONTE if fonte is None else fonte,
                'conversations': [{'role':'user', 'content':pedido},
                                  {'role':'assistant', 'content':resposta}]}

    def test_selecao_deterministica_preserva_textos_e_raiz(self):
        from scripts.curar_instrucoes_publicas import selecionar, pares
        a = self.registro('  Quero entender ação!\n', 'Uma resposta com ação.')
        a['conversations'] += [{'role':'user','content':'E depois?'},
                               {'role':'assistant','content':'Vamos pensar nas consequências.'}]
        b = self.registro('quero entender AÇÃO!', 'Uma outra resposta.')
        docs, _ = selecionar([a,b,a], limite=2)
        self.assertEqual(docs, selecionar([a,a,b], limite=2)[0])
        self.assertEqual(len(docs),2)
        self.assertEqual(docs[0]['grupo'],docs[1]['grupo'])
        self.assertEqual(docs[0]['split'],docs[1]['split'])
        completo = next(d for d in docs if len(d['conversations']) == 4)
        exemplos = list(pares(completo))
        self.assertEqual(exemplos[0]['mensagem'],a['conversations'][0]['content'])
        self.assertEqual(exemplos[1]['historico'][0]['texto'],a['conversations'][0]['content'])
        self.assertEqual(exemplos[1]['historico'][1]['texto'],a['conversations'][1]['content'])

    def test_recusa_fonte_incorreta_estrutura_identidade_e_reservados(self):
        from scripts.curar_instrucoes_publicas import selecionar
        errado = self.registro('pedido','resposta', fonte='https://outra-fonte')
        estrutura = self.registro('pedido','resposta'); estrutura['conversations'][0]['role']='system'
        identidade = self.registro('Qual seu nome?','Sou ChatGPT.')
        reservado = self.registro('pedido exclusivo','RESPOSTA Reservada')
        docs, stats = selecionar([errado,estrutura,identidade,reservado], reservados=['resposta reservada'])
        self.assertEqual(docs,[])
        for k in ['outra_fonte_licenca','estrutura_recusada','identidade_externa','sobreposicao_avaliacao_humana']:
            self.assertEqual(stats[k],1)

    def test_alvo_duplicado_entre_particoes_nao_entra_no_treino(self):
        from scripts.curar_instrucoes_publicas import selecionar, digest
        pedidos = {}
        for i in range(1000):
            t = 'pedido diferente ' + str(i)
            b = int(digest(t)[:8],16) % 100
            pedidos.setdefault('treino' if b >= 5 else 'reservado',t)
            if len(pedidos) == 2: break
        docs, stats = selecionar([self.registro(t,'Mesmo alvo compartilhado') for t in pedidos.values()])
        self.assertEqual(docs,[])
        self.assertEqual(stats['conversas_alvos_entre_particoes'],2)


class TestesIntegracaoSemDependencias(unittest.TestCase):
    def test_padrao_nao_importa_torch_e_cliente_nao_escolhe_checkpoint(self):
        from web_core import responder_web, PedidoInvalido
        with patch('dialogo_linguagem_profunda.carregar_modelo', side_effect=AssertionError('Não ativar candidato')):
            self.assertEqual(responder_web({'message': 'O que é DNA?'})['id'], 'conhecimento:dna')
        with self.assertRaises(PedidoInvalido):
            responder_web({'message':'oi', 'modelo_linguagem':'/tmp/nao-confiar'})

    def test_candidato_livre_usa_historico_sem_rota_antiga_e_nao_cria_fatos(self):
        from crivo import Crivo
        bot = Crivo(modelo_linguagem='/candidato')
        camada = bot.conversacao.contextual
        with patch('dialogo_linguagem_profunda.responder', return_value={
                'texto':'Pode me contar um pouco mais do que aconteceu?', 'completa':True}) as gerar, \
             patch.object(camada, '_compreender', side_effect=AssertionError('Não depender do classificador')):
            bot.responder('Quero conversar sobre uma sensação estranha')
            bot.responder('Como podemos explorar essa sensação?')
        self.assertEqual(gerar.call_count, 2)
        self.assertTrue(gerar.call_args.args[2])
        self.assertFalse(camada.ultimo_quadro['aceita'])
        self.assertIsNone(camada.memoria.contexto()['objetivo'])
        self.assertIsNone(bot.ultimo_turno.get('prova_origem'))

    def test_fato_conhecido_preserva_resposta_com_candidato(self):
        from crivo import Crivo
        with patch('dialogo_linguagem_profunda.responder', side_effect=AssertionError('Não interceptar fato')):
            self.assertEqual(Crivo(modelo_linguagem='/candidato').responder('O que é DNA?')[0], 'conhecimento:dna')


@unittest.skipUnless(DISPONIVEL, 'Laboratório opcional requer requirements-treino.txt; CI próprio instala e executa')
class TestesMatematicaLinguagem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        torch.set_num_threads(1)

    def tokenizer(self):
        from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders
        from linguagem_profunda import ESPECIAIS
        t = Tokenizer(models.BPE())
        t.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
        t.decoder = decoders.ByteLevel()
        t.train_from_iterator(['Português: ação, reflexão e diálogo.'],
            trainers.BpeTrainer(vocab_size=280, special_tokens=ESPECIAIS,
                               initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
        t.encode_special_tokens = True
        return t

    def test_atencao_nao_acessa_tokens_futuros(self):
        import torch
        from linguagem_profunda import Configuracao, LinguagemProfunda
        torch.manual_seed(7)
        m = LinguagemProfunda(Configuracao(vocabulario=32, dimensao=24, camadas=2,
                            cabecas=3, contexto=8, dropout=0.)).eval()
        a = torch.tensor([[3, 4, 5, 6, 7]])
        b = torch.tensor([[3, 4, 5, 18, 19]])
        torch.testing.assert_close(m(a)[0][:, :3], m(b)[0][:, :3], rtol=0, atol=0)

    def test_cache_preserva_logits_inclusive_ao_reiniciar_posicoes(self):
        import torch
        from linguagem_profunda import Configuracao,LinguagemProfunda
        from geracao_incremental import CacheCausal
        torch.manual_seed(19)
        m = LinguagemProfunda(Configuracao(vocabulario=32,dimensao=24,camadas=2,
                             cabecas=3,contexto=8,dropout=.1)).eval()
        ids = [4,7,9]
        cache = CacheCausal(m,ids)
        for token in [11,12,13,14,15,16,17]:
            esperado = m(torch.tensor([ids[-8:]]))[0][0,-1]
            torch.testing.assert_close(cache.logits,esperado,rtol=1e-5,atol=1e-6)
            self.assertFalse(cache.logits.requires_grad)
            ids.append(token);cache.avancar(token)
        torch.testing.assert_close(cache.logits,m(torch.tensor([ids[-8:]]))[0][0,-1],rtol=1e-5,atol=1e-6)

    def test_cache_e_referencia_geram_mesmos_tokens_com_semente_fixa(self):
        import torch
        from linguagem_profunda import Configuracao,LinguagemProfunda
        from geracao_incremental import gerar
        torch.manual_seed(29)
        m = LinguagemProfunda(Configuracao(vocabulario=32,dimensao=24,camadas=2,
                             cabecas=3,contexto=12,dropout=.1)).eval()
        args = {'fim':31,'max_tokens':16,'temperatura':.7,'top_k':12,'semente':8,'proibidos':[0,1]}
        self.assertEqual(gerar(m,[3,5,8],**args),m.gerar([3,5,8],**args))

    def test_texto_unicode_e_marcadores_citados_sao_literais(self):
        from linguagem_profunda import codificar_texto, ESPECIAIS
        t = self.tokenizer()
        texto = 'Oi, Жулия! 🧠\nEscrevi <assistente> no papel.'
        ids = codificar_texto(t, texto)
        self.assertEqual(t.decode(ids), texto)
        self.assertFalse(set(ids) & {t.token_to_id(e) for e in ESPECIAIS})

    def test_sft_aprende_alvo_inteiro_uma_vez_sem_perda_no_usuario(self):
        from scripts.preparar_linguagem_profunda import janelas_dialogo
        from linguagem_profunda import codificar_texto
        t = self.tokenizer()
        ex = {'mensagem':'Pergunta com informação privada apenas no contexto.',
              'historico':[{'papel':'usuario','texto':'Mensagem antiga.'}],
              'resposta':'Uma resposta longa, íntegra e com acentos. ' * 30}
        janelas = janelas_dialogo(t, ex, 32)
        alvos = [a for _, y in janelas for a in y if a != -100]
        self.assertEqual(alvos, codificar_texto(t, ex['resposta']) + [t.token_to_id('<fim>')])
        self.assertTrue(all(len(x) <= 32 and len(x) == len(y) for x,y in janelas))

    def test_historico_descarta_turno_inteiro_e_preserva_mensagem_atual(self):
        from linguagem_profunda import fonte_dialogo, segmentos_dialogo
        t = self.tokenizer()
        hist = [{'papel':'usuario', 'texto':'antigo ' * 100},
                {'papel':'assistente', 'texto':'Recente.'}]
        segmentos, atual = segmentos_dialogo(t, 'Mensagem atual.', hist)
        fonte = fonte_dialogo(t, 'Mensagem atual.', hist, len(atual) + len(segmentos[-1]))
        self.assertEqual(fonte, segmentos[-1] + atual)
        with self.assertRaises(ValueError): fonte_dialogo(t, 'x ' * 200, [], 16)

    def fixture_corpus(self, pasta):
        import numpy as np
        t = self.tokenizer(); t.save(str(pasta / 'tokenizer.json'))
        rng = np.random.default_rng(13)
        for split in ('treino','validacao','teste'):
            rng.integers(5,t.get_vocab_size(),size=1024,dtype=np.uint16).astype('<u2').tofile(pasta / ('linguagem_'+split+'.bin'))
            x = rng.integers(5,t.get_vocab_size(),size=(8,16),dtype=np.int32)
            y = x.copy(); y[:,:8] = -100
            np.save(pasta / ('dialogo_'+split+'_x.npy'),x)
            np.save(pasta / ('dialogo_'+split+'_y.npy'),y)
            np.save(pasta / ('dialogo_'+split+'_origem.npy'),np.array([0,1]*4,dtype=np.int8))
        arquivos = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pasta.iterdir()}
        (pasta/'manifesto.json').write_text(json.dumps({'contexto':16,'vocabulario':t.get_vocab_size(),'arquivos':arquivos}))

    def test_retomada_cli_reproduz_modelo_e_adam_sem_perder_rng(self):
        import torch
        with tempfile.TemporaryDirectory() as td:
            pasta = Path(td); corpus = pasta/'corpus'; corpus.mkdir(); self.fixture_corpus(corpus)
            base = [sys.executable,str(ROOT/'scripts/treinar_linguagem_profunda.py'),
                    '--corpus',str(corpus),'--passos','4','--lote','2','--dimensao','24',
                    '--camadas','1','--cabecas','3','--contexto','16','--threads','1']
            for args in ([*base,'--saida',str(pasta/'inteiro')],
                         [*base,'--saida',str(pasta/'retomado'),'--parar-em','2'],
                         [*base,'--saida',str(pasta/'retomado'),'--retomar']):
                r = subprocess.run(args,capture_output=True,text=True,timeout=90)
                self.assertEqual(r.returncode,0,r.stderr)
            a = torch.load(pasta/'inteiro/checkpoint.pt',weights_only=True)
            b = torch.load(pasta/'retomado/checkpoint.pt',weights_only=True)
            for nome, peso in a['modelo'].items():
                self.assertTrue(torch.equal(peso,b['modelo'][nome]),nome)
            for chave, estado in a['otimizador']['state'].items():
                for nome, valor in estado.items():
                    self.assertTrue(torch.equal(valor,b['otimizador']['state'][chave][nome]))
            self.assertTrue(torch.equal(a['rng_torch'],b['rng_torch']))
            self.assertEqual(a['rng_numpy'],b['rng_numpy'])
            self.assertEqual(a['tokens_alvo'],b['tokens_alvo'])

    def test_melhor_checkpoint_e_parada_preservam_ultimo_estado(self):
        from scripts import treinar_linguagem_profunda as treinador
        from contextlib import redirect_stdout
        import io
        with tempfile.TemporaryDirectory() as td:
            pasta=Path(td);corpus=pasta/'corpus';corpus.mkdir();self.fixture_corpus(corpus)
            def medicao(ce):
                return {f:dict(entropia_cruzada=ce,perplexidade=2.,tokens_avaliados=8,particao='validacao')
                        for f in ('linguagem','dialogo')}
            args=['treinador','--corpus',str(corpus),'--saida',str(pasta/'treino'),
                  '--passos','10','--lote','2','--dimensao','24','--camadas','1',
                  '--cabecas','3','--contexto','16','--threads','1','--fase','linguagem',
                  '--avaliar-a-cada','1','--salvar-a-cada','1','--selecionar-melhor',
                  '--paciencia-validacoes','1','--dispositivo','cpu']
            with patch.object(sys,'argv',args), patch.object(treinador,'avaliar',
                    side_effect=[medicao(3.),medicao(2.),medicao(2.5)]), redirect_stdout(io.StringIO()):
                treinador.main()
            ultimo=json.loads((pasta/'treino/relatorio.json').read_text())
            melhor=json.loads((pasta/'treino/melhor/relatorio.json').read_text())
            self.assertEqual(ultimo['passo'],2);self.assertEqual(melhor['passo'],1)
            self.assertEqual(melhor['historico'][-1]['avaliacao']['linguagem']['entropia_cruzada'],2.)
            self.assertTrue((pasta/'treino/checkpoint.pt').is_file())
            self.assertEqual(melhor['pesos_sha256'],treinador.sha(pasta/'treino/melhor/pesos.pt'))
            self.assertEqual(melhor['execucao']['selecao']['paciencia'],1)

    def test_checkpoint_recusa_tokenizer_alterado(self):
        import torch
        from dataclasses import asdict
        from linguagem_profunda import Configuracao,LinguagemProfunda,carregar
        t = self.tokenizer()
        with tempfile.TemporaryDirectory() as td:
            pasta = Path(td); t.save(str(pasta/'tokenizer.json'))
            config = Configuracao(vocabulario=t.get_vocab_size(), dimensao=24,camadas=1,cabecas=3,contexto=16)
            torch.save({'versao':1,'config':asdict(config),'modelo':LinguagemProfunda(config).state_dict(),
                        'execucao':{'tokenizer_sha256': 'hash_incorreto'}}, pasta/'pesos.pt')
            with self.assertRaisesRegex(ValueError,'Tokenizador'): carregar(pasta)

    def test_pesos_publicados_carregam_com_tokenizer_e_relatorio_correspondentes(self):
        from linguagem_profunda import carregar
        pasta = ROOT / 'artefatos' / 'linguagem_profunda'
        modelo, tokenizer, estado = carregar(pasta)
        report = json.loads((pasta/'relatorio.json').read_text())
        self.assertEqual(estado['execucao']['fase'],'dialogo')
        self.assertEqual(hashlib.sha256((pasta/'pesos.pt').read_bytes()).hexdigest(),report['pesos_sha256'])
        self.assertEqual(estado['passo'],report['passo'])
        self.assertEqual(sum(p.numel() for p in modelo.parameters()),report['parametros'])
        self.assertEqual(tokenizer.get_vocab_size(),estado['config']['vocabulario'])

    def test_migracao_de_carga_nao_aceita_corpus_ou_codigo_de_modelo_diferente(self):
        from scripts.treinar_linguagem_profunda import retomada_compativel
        original = 'abb5ac3d5882ed39425b0d4066ab8e5848210d20fb5c498cdbe09e0311d1de2d'
        anterior = {'codigo_treinador':original,'codigo_modelo':'modelo_igual','corpus':'dados_iguais'}
        digest = hashlib.sha256(json.dumps(anterior,sort_keys=True).encode()).hexdigest()
        estado = {'assinatura':digest,'execucao':anterior}
        atual = dict(anterior,codigo_treinador='treinador_com_carga_cpu')
        self.assertTrue(retomada_compativel(estado,'assinatura_atual',atual))
        for campo in ('codigo_modelo','corpus'):
            self.assertFalse(retomada_compativel(estado,'assinatura_atual',dict(atual,**{campo:'alterado'})))


if __name__ == '__main__': unittest.main()
