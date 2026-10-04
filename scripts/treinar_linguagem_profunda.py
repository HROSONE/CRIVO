"""Pré-treino/SFT do Transformer causal próprio, com retomada exata de Adam/RNG.

Não baixa pesos e não promove candidato ao motor normal. Dados e tokenizer
devem ser preparados pelo script de corpus e conferidos por SHA-256.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
from linguagem_profunda import Configuracao, LinguagemProfunda, VERSAO


def sha(caminho):
    h = hashlib.sha256()
    with open(caminho, 'rb') as f:
        for bloco in iter(lambda: f.read(1048576), b''):
            h.update(bloco)
    return h.hexdigest()


def salvar_atomico(estado, caminho):
    caminho = Path(caminho)
    tmp = caminho.with_name(caminho.name + '.tmp')
    torch.save(estado, tmp)
    os.replace(tmp, caminho)


def perda_por_resposta(logits, alvos):
    """Cada resposta contribui igualmente; respostas longas não dominam o lote."""
    perdas = torch.nn.functional.cross_entropy(logits.transpose(1, 2), alvos,
                                               ignore_index=-100, reduction='none')
    contagens = (alvos != -100).sum(1)
    validos = contagens > 0
    if not validos.any():
        raise ValueError('Lote sem respostas supervisionadas')
    return (perdas.sum(1)[validos] / contagens[validos]).mean()


class Corpus:
    def __init__(self, caminho, contexto, conferir=True,equilibrar_familias=False,podar_padding=False):
        self.caminho = Path(caminho)
        self.manifesto = json.loads((self.caminho / 'manifesto.json').read_text())
        self.assinatura = sha(self.caminho / 'manifesto.json')
        if contexto != self.manifesto['contexto']:
            raise ValueError('Contexto do corpus difere do modelo')
        if conferir:
            for nome, digest in self.manifesto['arquivos'].items():
                if sha(self.caminho / nome) != digest:
                    raise ValueError('Corpus alterado: ' + nome)
        self.linguagem, self.x, self.y, self.humanos, self.sinteticos = {}, {}, {}, {}, {}
        for split in ('treino', 'validacao', 'teste'):
            self.linguagem[split] = np.memmap(self.caminho / ('linguagem_' + split + '.bin'),
                                            dtype='<u2', mode='r')
            self.x[split] = np.load(self.caminho / ('dialogo_' + split + '_x.npy'), mmap_mode='r')
            self.y[split] = np.load(self.caminho / ('dialogo_' + split + '_y.npy'), mmap_mode='r')
            origem = np.load(self.caminho / ('dialogo_' + split + '_origem.npy'))
            self.humanos[split] = np.flatnonzero(origem == 1)
            self.sinteticos[split] = np.flatnonzero(origem == 0)
        self.pares_amplos = {}
        politica = self.manifesto.get('amostragem_dialogo')
        if politica is not None:
            if (set(politica) != {'fracao_humana','pares_uniformes','sinteticos_por_familia'}
                or politica['pares_uniformes'] is not True or politica['sinteticos_por_familia'] is not True
                or isinstance(politica['fracao_humana'],bool)
                or not isinstance(politica['fracao_humana'],(int,float))
                or not 0 < politica['fracao_humana'] < 1):
                raise ValueError('Política de diálogos amplos inválida')
            if equilibrar_familias:
                raise ValueError('Não combinar equilíbrio legado com amostragem por pares')
            self.fracao_humana = politica['fracao_humana']
            for split in ('treino','validacao','teste'):
                arrays=[]
                for sufixo in ('par','familia','origem'):
                    path=self.caminho/f'dialogo_{split}_{sufixo}.npy'
                    if path.name not in self.manifesto['arquivos']:
                        raise ValueError('Amostragem exige índices com hash no manifesto')
                    a=np.load(path)
                    if a.ndim!=1 or a.dtype.kind not in 'iu' or len(a)!=len(self.x[split]):
                        raise ValueError('Índices de pares incompatíveis')
                    arrays.append(a)
                pares,familias,origens=arrays
                if not np.isin(origens,[0,1]).all() or (pares<0).any():
                    raise ValueError('Origem ou par inválido')
                hs=[];ss={}
                for par in np.unique(pares):
                    indices=np.flatnonzero(pares==par)
                    if len(np.unique(origens[indices]))!=1 or len(np.unique(familias[indices]))!=1:
                        raise ValueError('Par mistura origem ou família')
                    if origens[indices[0]]==1: hs.append(indices)
                    else: ss.setdefault(int(familias[indices[0]]),[]).append(indices)
                if split=='treino' and (not hs or not ss):
                    raise ValueError('Corpus amplo exige humanos e autorais no treino')
                self.pares_amplos[split]=(hs,list(ss.values()))
        self.contexto = contexto
        self.podar_padding = podar_padding
        self.grupos = {}
        if equilibrar_familias:
            for split in ('treino','validacao','teste'):
                path=self.caminho/('dialogo_'+split+'_familia.npy')
                if not path.exists() or path.name not in self.manifesto['arquivos']:
                    raise ValueError('Equilíbrio exige grupos de família com hash no manifesto')
                ids=np.load(path)
                if len(ids)!=len(self.x[split]):raise ValueError('Grupos incompatíveis com as janelas')
                self.grupos[split]=[np.flatnonzero(ids==i) for i in np.unique(ids)]


    def lote(self, split, fase, tamanho, rng, dispositivo):
        if fase == 'linguagem':
            seq = self.linguagem[split]
            if len(seq) < self.contexto + 1:
                raise ValueError('Partição de linguagem pequena demais')
            inicios = rng.integers(0, len(seq) - self.contexto, size=tamanho)
            x = np.stack([seq[i:i + self.contexto] for i in inicios]).astype(np.int64)
            y = np.stack([seq[i + 1:i + self.contexto + 1] for i in inicios]).astype(np.int64)
        else:
            n = len(self.x[split])
            if not n: raise ValueError('Partição sem diálogos')
            if split == 'treino' and self.pares_amplos:
                hs,fs=self.pares_amplos[split]
                base=tamanho*self.fracao_humana
                nh=int(base)+int(rng.random()<base-int(base))
                indices=[]
                for _ in range(nh):
                    janelas=hs[rng.integers(len(hs))]
                    indices.append(rng.choice(janelas))
                for _ in range(tamanho-nh):
                    familia=fs[rng.integers(len(fs))]
                    janelas=familia[rng.integers(len(familia))]
                    indices.append(rng.choice(janelas))
                indices=np.asarray(indices);rng.shuffle(indices)
            elif split == 'treino' and self.grupos:
                gs=self.grupos[split]
                indices=np.asarray([rng.choice(gs[i]) for i in rng.integers(0,len(gs),size=tamanho)])
            elif split == 'treino' and len(self.humanos[split]) and len(self.sinteticos[split]):
                # Metade do lote humano; contar janelas sintéticas como humanos
                # ou deixar 10 mil padrões dominarem centenas de árvores é errado.
                indices = np.concatenate([rng.choice(self.humanos[split], tamanho // 2),
                    rng.choice(self.sinteticos[split], tamanho - tamanho // 2)])
                rng.shuffle(indices)
            else:
                indices = rng.integers(0, n, size=tamanho)
            x = np.asarray(self.x[split][indices], dtype=np.int64)
            y = np.asarray(self.y[split][indices], dtype=np.int64)
        if fase=='dialogo' and self.podar_padding:
            posicoes=np.flatnonzero(np.any(y!=-100,axis=0))
            if not len(posicoes):raise ValueError('Lote sem alvos supervisionados')
            ultimo=int(posicoes[-1])+1;x=x[:,:ultimo];y=y[:,:ultimo]
        return torch.from_numpy(x).to(dispositivo), torch.from_numpy(y).to(dispositivo)


@torch.no_grad()
def avaliar(modelo, corpus, dispositivo, split='validacao', lotes=12, tamanho=8, humanos=False):
    modelo.eval()
    resultado = {}
    for fase in ('linguagem', 'dialogo'):
        rng = np.random.default_rng(92017)
        soma, tokens = 0., 0
        for _ in range(lotes):
            x, y = corpus.lote(split, fase, tamanho, rng, dispositivo)
            n = int((y != -100).sum())
            perda = float(modelo(x, y)[1])
            soma += perda * n; tokens += n
        ce = soma / tokens
        resultado[fase] = {'entropia_cruzada': ce, 'perplexidade': math.exp(min(ce, 30)),
                           'tokens_avaliados': tokens, 'particao': split}
    if humanos:
        indices = corpus.humanos[split]
        if not len(indices):
            raise ValueError('Seleção humana exige diálogos humanos na validação')
        soma, tokens = 0., 0
        # Todos os alvos humanos reservados, sem reposição nem sintéticos.
        for inicio in range(0, len(indices), tamanho):
            ix = indices[inicio:inicio + tamanho]
            x = torch.tensor(np.asarray(corpus.x[split][ix], dtype=np.int64), device=dispositivo)
            y = torch.tensor(np.asarray(corpus.y[split][ix], dtype=np.int64), device=dispositivo)
            n = int((y != -100).sum())
            if not n:
                continue
            soma += float(modelo(x, y)[1]) * n
            tokens += n
        if not tokens:
            raise ValueError('Validação humana sem alvos supervisionados')
        ce = soma / tokens
        resultado['dialogo_humano'] = dict(entropia_cruzada=ce,
            perplexidade=math.exp(min(ce, 30)), tokens_avaliados=tokens,
            janelas=len(indices), particao=split, origem='humano_oasst2', completa=True)
    return resultado


def assinatura_execucao(config, corpus, fase, lote, lr, semente, repeticao):
    dados = {'config': asdict(config), 'corpus': corpus.assinatura, 'fase': fase,
             'tokenizer_sha256': corpus.manifesto['arquivos']['tokenizer.json'],
             'lote': lote, 'lr': lr, 'semente': semente, 'repeticao_linguagem': repeticao,
             'codigo_modelo': sha(ROOT / 'linguagem_profunda.py'),
             'codigo_treinador': sha(Path(__file__))}
    return hashlib.sha256(json.dumps(dados, sort_keys=True).encode()).hexdigest(), dados


def retomada_compativel(estado, assinatura, dados):
    if estado['assinatura'] == assinatura:
        return True
    # Única migração admitida: a versão inicial carregava estados RNG CUDA
    # em CUDA com map_location. Carregar em CPU corrige isso e não muda os
    # cálculos, Adam ou RNG. Todos os demais dados/códigos continuam iguais.
    anterior = estado.get('execucao', {})
    original = 'abb5ac3d5882ed39425b0d4066ab8e5848210d20fb5c498cdbe09e0311d1de2d'
    digest = hashlib.sha256(json.dumps(anterior, sort_keys=True).encode()).hexdigest()
    return (anterior.get('codigo_treinador') == original and digest == estado['assinatura']
            and {k:v for k,v in anterior.items() if k != 'codigo_treinador'} ==
                {k:v for k,v in dados.items() if k != 'codigo_treinador'})


def estado_checkpoint(modelo, otimizador, rng, passo, assinatura, dados, historico,
                      tokens_entrada, tokens_alvo, horizonte, inicial):
    return {'versao': VERSAO, 'config': asdict(modelo.config), 'modelo': modelo.state_dict(),
            'otimizador': otimizador.state_dict(), 'rng_numpy': json.dumps(rng.bit_generator.state),
            'rng_torch': torch.get_rng_state(),
            'rng_cuda': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
            'passo': passo, 'assinatura': assinatura, 'execucao': dados,
            'historico': historico, 'tokens_entrada': tokens_entrada, 'tokens_alvo': tokens_alvo,
            'horizonte': horizonte, 'inicial': inicial}



from scripts.selecao_programacao import pontuacao_validacao

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus', required=True)
    p.add_argument('--saida', required=True)
    p.add_argument('--fase', choices=('linguagem', 'dialogo'), default='linguagem')
    p.add_argument('--passos', type=int, default=2000, help='Passo total desejado; pode ampliar na retomada')
    p.add_argument('--lote', type=int, default=12)
    p.add_argument('--dimensao', type=int, default=192)
    p.add_argument('--camadas', type=int, default=4)
    p.add_argument('--cabecas', type=int, default=6)
    p.add_argument('--contexto', type=int, default=256)
    p.add_argument('--lr', type=float, default=.0008)
    p.add_argument('--semente', type=int, default=20261001)
    p.add_argument('--threads', type=int, default=3)
    p.add_argument('--avaliar-a-cada', type=int, default=200)
    p.add_argument('--salvar-a-cada', type=int, default=100)
    p.add_argument('--repeticao-linguagem', type=float, default=.2,
                   help='Fração de passos de SFT com pré-treino para reduzir esquecimento')
    p.add_argument('--selecionar-melhor', action='store_true', help='Salva melhor validação em melhor/ sem substituir checkpoint de retomada')
    p.add_argument('--selecao-humana', action='store_true',
                   help='SFT: selecionar pela CE de todos os alvos humanos de validação, sem sintéticos')
    p.add_argument('--paciencia-validacoes', type=int, default=0, help='Parar após N avaliações sem melhora; zero desativa')
    p.add_argument('--equilibrar-familias',action='store_true')
    p.add_argument('--podar-padding',action='store_true')
    p.add_argument('--perda-por-resposta', action='store_true',
                   help='SFT: média por resposta, evitando domínio dos alvos longos')
    p.add_argument('--peso-tokens-logicos',type=float,default=1.)
    p.add_argument('--validacao-funcional', action='store_true', help='Selecionar SFT por código correto na validação, compilação, término e CE')
    p.add_argument('--tsc', help='Compilador TS para validação funcional')
    p.add_argument('--retomar', action='store_true')
    p.add_argument('--max-segundos', type=int, help='Pausa com checkpoint após orçamento de tempo da etapa')
    p.add_argument('--parar-em', type=int, help='Pausa planejada sem mudar o horizonte do LR')
    p.add_argument('--ajustar-proprio', action='store_true', help='Permite novo corpus com o mesmo tokenizer/configuração; registra linhagem')
    p.add_argument('--inicial', help='Diretório do pré-treino próprio para iniciar SFT')
    p.add_argument('--dispositivo', default='cuda' if torch.cuda.is_available() else 'cpu')
    args = p.parse_args()
    if min(args.passos, args.lote, args.threads, args.avaliar_a_cada, args.salvar_a_cada) < 1:
        p.error('Contagens devem ser positivas')
    if args.validacao_funcional and (args.fase != 'dialogo' or not args.selecionar_melhor or not args.tsc):
        p.error('Validação funcional requer SFT, --selecionar-melhor e --tsc')
    if args.selecao_humana and (args.fase != 'dialogo' or not args.selecionar_melhor or args.validacao_funcional):
        p.error('--selecao-humana requer SFT, --selecionar-melhor e ausência de validação funcional')
    if args.paciencia_validacoes < 0 or args.paciencia_validacoes and not args.selecionar_melhor:
        p.error('Paciência não negativa exige --selecionar-melhor')
    if not math.isfinite(args.peso_tokens_logicos) or not 1<=args.peso_tokens_logicos<=16:p.error('Peso lógico deve estar entre 1 e 16')
    if args.peso_tokens_logicos!=1 and args.fase!='dialogo':p.error('Peso lógico é exclusivo do SFT')
    if args.perda_por_resposta and (args.fase != 'dialogo' or args.peso_tokens_logicos != 1):
        p.error('Perda por resposta exige SFT sem peso lógico adicional')
    if args.max_segundos is not None and args.max_segundos < 1: p.error('Orçamento deve ser positivo')
    if not 0 <= args.repeticao_linguagem < 1 or args.lr <= 0:
        p.error('Taxa de aprendizado/repetição inválida')
    if args.ajustar_proprio and not (args.inicial or args.retomar): p.error('--ajustar-proprio requer --inicial ou --retomar')
    if args.retomar and args.inicial: p.error('Escolha retomada ou inicialização de uma etapa')
    if args.fase == 'dialogo' and not args.retomar and not args.inicial:
        p.error('SFT requer --inicial com pré-treino próprio')
    torch.set_num_threads(args.threads)
    torch.manual_seed(args.semente)
    rng = np.random.default_rng(args.semente)
    corpus = Corpus(args.corpus,args.contexto,equilibrar_familias=args.equilibrar_familias,podar_padding=args.podar_padding)
    config = Configuracao(vocabulario=corpus.manifesto['vocabulario'], dimensao=args.dimensao,
              camadas=args.camadas, cabecas=args.cabecas, contexto=args.contexto)
    assinatura, dados = assinatura_execucao(config, corpus, args.fase, args.lote, args.lr,
                                            args.semente, args.repeticao_linguagem)
    if args.equilibrar_familias or args.podar_padding or args.peso_tokens_logicos!=1:
        dados['politica_sft']=dict(equilibrar_familias=args.equilibrar_familias,podar_padding=args.podar_padding,peso_tokens_logicos=args.peso_tokens_logicos,
            codigo_perda=sha(ROOT/'scripts/perda_programacao.py'))
        assinatura=hashlib.sha256(json.dumps(dados,sort_keys=True).encode()).hexdigest()
    if args.perda_por_resposta:
        dados['perda_por_resposta'] = True
        assinatura = hashlib.sha256(json.dumps(dados, sort_keys=True).encode()).hexdigest()
    if args.selecionar_melhor:
        criterio = ('entropia_cruzada_validacao_dialogo_humano_completa' if args.selecao_humana
                    else 'funcional_compilacao_termino_ce' if args.validacao_funcional
                    else 'entropia_cruzada_validacao_' + args.fase)
        dados['selecao'] = dict(criterio=criterio, paciencia=args.paciencia_validacoes,
                               avaliar_a_cada=args.avaliar_a_cada,
                               codigo_selecao=sha(ROOT/'scripts/selecao_programacao.py'))
        if args.validacao_funcional:
            dados['selecao']['fontes_sha256'] = {n:sha(ROOT/'dados/programacao'/n) for n in ('tarefas.json','curriculo.json','algoritmos.json','logica.json')}
            dados['selecao']['codigo_avaliador'] = sha(ROOT/'scripts/avaliar_programacao.py')
            dados['selecao']['codigo_verificador'] = sha(ROOT/'verificacao_codigo.py')
            dados['selecao']['codigo_selecao'] = sha(ROOT/'scripts/selecao_programacao.py')
        assinatura = hashlib.sha256(json.dumps(dados, sort_keys=True).encode()).hexdigest()
    out = Path(args.saida); out.mkdir(parents=True, exist_ok=True)
    if (out / 'checkpoint.pt').exists() and not args.retomar:
        p.error('Checkpoint existente; use --retomar ou outro diretório')
    modelo = LinguagemProfunda(config).to(args.dispositivo)
    otimizador = torch.optim.AdamW(modelo.parameters(), lr=args.lr, weight_decay=.01)
    passo, tokens_entrada, tokens_alvo = 0, 0, 0
    historico = []; horizonte = args.passos; inicial = None
    if args.retomar:
        # RNG exige ByteTensors CPU; load_state_dict move pesos/Adam aos parâmetros.
        estado = torch.load(out / 'checkpoint.pt', map_location='cpu', weights_only=True)
        if not retomada_compativel(estado, assinatura, dados):
            raise ValueError('Retomada incompatível: dados, código ou configuração mudaram')
        modelo.load_state_dict(estado['modelo']); otimizador.load_state_dict(estado['otimizador'])
        rng.bit_generator.state = json.loads(estado['rng_numpy'])
        torch.set_rng_state(estado['rng_torch'].cpu())
        if estado['rng_cuda'] and torch.cuda.is_available(): torch.cuda.set_rng_state_all(estado['rng_cuda'])
        passo = estado['passo']; tokens_entrada = estado['tokens_entrada']; tokens_alvo = estado['tokens_alvo']
        historico = estado['historico']; horizonte = estado['horizonte']; inicial = estado['inicial']
    elif args.inicial:
        pasta = Path(args.inicial)
        anterior = torch.load(pasta / 'pesos.pt', map_location=args.dispositivo, weights_only=True)
        if anterior['versao'] != VERSAO or anterior['config'] != asdict(config):
            raise ValueError('Inicialização incompatível com arquitetura própria')
        if sha(pasta / 'tokenizer.json') != corpus.manifesto['arquivos']['tokenizer.json'] or anterior['execucao']['tokenizer_sha256'] != corpus.manifesto['arquivos']['tokenizer.json']:
            raise ValueError('Inicialização com tokenizer diferente ou alterado')
        if not args.ajustar_proprio and anterior['execucao']['corpus'] != corpus.assinatura:
            raise ValueError('Inicialização incompatível com corpus/configuração próprios')
        if not args.ajustar_proprio and anterior['execucao']['fase'] != 'linguagem': raise ValueError('Esperava etapa de pré-treino')
        modelo.load_state_dict(anterior['modelo'])
        inicial = {'pesos_sha256': sha(pasta / 'pesos.pt'), 'passo': anterior['passo'],
                   'tokens_alvo': anterior['tokens_alvo'], 'corpus_anterior': anterior['execucao']['corpus'],
                   'ajuste_programacao': args.ajustar_proprio}
    shutil.copyfile(corpus.caminho / 'tokenizer.json', out / 'tokenizer.json')
    inicio = time.monotonic(); passo_inicio = passo
    parametros = sum(p.numel() for p in modelo.parameters())
    if not historico:
        resultado = avaliar(modelo, corpus, args.dispositivo, humanos=args.selecao_humana)
        historico.append({'passo': passo, 'avaliacao': resultado})
        print(json.dumps({'baseline': resultado, 'parametros': parametros}), flush=True)
    parou_validacao = False
    def salvar(pasta=out):
        pasta.mkdir(parents=True, exist_ok=True)
        if pasta != out:
            shutil.copyfile(corpus.caminho / 'tokenizer.json', pasta / 'tokenizer.json')
        estado = estado_checkpoint(modelo, otimizador, rng, passo, assinatura, dados,
                    historico, tokens_entrada, tokens_alvo, horizonte, inicial)
        salvar_atomico(estado, pasta / 'checkpoint.pt')
        campos = ('versao', 'config', 'modelo', 'passo', 'execucao', 'tokens_entrada', 'tokens_alvo', 'inicial')
        salvar_atomico({k: estado[k] for k in campos}, pasta / 'pesos.pt')
        relatorio = {k: v for k, v in estado.items() if k not in
                     ('modelo', 'otimizador', 'rng_numpy', 'rng_torch', 'rng_cuda')}
        relatorio.update(parametros=parametros, pesos_sha256=sha(pasta / 'pesos.pt'),
            segundos_esta_execucao=round(time.monotonic() - inicio, 2),
            passos_esta_execucao=passo - passo_inicio, inicializacao='aleatoria_do_zero' if not inicial else 'pretreino_proprio',
            versao_torch=torch.__version__, dispositivo=args.dispositivo,
            concluido=passo >= horizonte,
            pausado=passo < horizonte and not parou_validacao,
            parada_validacao=parou_validacao)
        tmp = pasta / 'relatorio.json.tmp'
        tmp.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + '\n')
        os.replace(tmp, pasta / 'relatorio.json')
    def medir_funcional():
        salvar(out / 'validacao_modelo')
        path = out / ('validacao_funcional_%06d.json' % passo)
        subprocess.run([sys.executable, str(ROOT/'scripts/avaliar_programacao.py'),
            '--modelo', str(out/'validacao_modelo'), '--saida', str(path), '--split','validacao',
            '--curriculo-validacao', '--reparos','0', '--tsc',str(args.tsc)], check=True, timeout=600)
        r = json.loads(path.read_text())
        if r['particao'] != 'validacao' or r['pesos_sha256'] != sha(out/'validacao_modelo/pesos.pt'):
            raise ValueError('Validação funcional não corresponde ao checkpoint')
        return {k:r[k] for k in ('particao','linguagens','pesos_sha256','fontes_sha256','isolamento')}
    if args.validacao_funcional and 'funcional' not in historico[-1]:
        historico[-1]['funcional'] = medir_funcional()
    melhor_pontuacao = max(pontuacao_validacao(h,args.fase,args.validacao_funcional,args.selecao_humana) for h in historico)
    sem_melhora = 0
    if args.selecionar_melhor and args.retomar:
        melhor_salvo = out / 'melhor' / 'relatorio.json'
        if not melhor_salvo.exists():
            raise ValueError('Melhor checkpoint ausente na retomada')
        best = json.loads(melhor_salvo.read_text())
        melhor_pontuacao = pontuacao_validacao(best['historico'][-1],args.fase,args.validacao_funcional,args.selecao_humana)
        sem_melhora = sum(h['passo'] > best['passo'] for h in historico)
    elif args.selecionar_melhor:
        salvar(out / 'melhor')
    pesos_logicos=None
    if args.peso_tokens_logicos!=1:
        from tokenizers import Tokenizer
        from scripts.perda_programacao import pesos_vocabulario,perda_ponderada
        pesos_logicos=pesos_vocabulario(Tokenizer.from_file(str(out/'tokenizer.json')),args.peso_tokens_logicos).to(args.dispositivo)
    parou_validacao = bool(args.paciencia_validacoes and sem_melhora >= args.paciencia_validacoes)
    limite = min(args.passos, args.parar_em) if args.parar_em is not None else args.passos
    if limite < passo: p.error('Pausa anterior ao checkpoint atual')
    ultimo_salvo = None
    while passo < limite and not parou_validacao:
        modelo.train()
        fase = args.fase
        if fase == 'dialogo' and rng.random() < args.repeticao_linguagem:
            fase = 'linguagem'
        x, y = corpus.lote('treino', fase, args.lote, rng, args.dispositivo)
        aquecimento = min(100, max(1, horizonte // 10))
        escala = min(1., (passo + 1) / aquecimento)
        if passo >= aquecimento:
            progresso = min(1., (passo - aquecimento) / max(1, horizonte - aquecimento))
            escala = .2 + .8 * .5 * (1 + math.cos(math.pi * progresso))
        for grupo in otimizador.param_groups: grupo['lr'] = args.lr * escala
        otimizador.zero_grad(set_to_none=True)
        if fase == 'dialogo' and args.perda_por_resposta:
            perda = perda_por_resposta(modelo(x)[0], y)
        else:
            perda = perda_ponderada(modelo(x)[0],y,pesos_logicos) if pesos_logicos is not None and fase=='dialogo' else modelo(x,y)[1]
        if not torch.isfinite(perda): raise FloatingPointError('Perda não finita; preservar último checkpoint')
        perda.backward(); torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.)
        otimizador.step()
        passo += 1; tokens_entrada += x.numel(); tokens_alvo += int((y != -100).sum())
        if passo % 20 == 0:
            linha = {'passo': passo, 'fase_lote': fase, 'perda_treino': float(perda.detach()),
                     'tokens_entrada': tokens_entrada, 'tokens_alvo': tokens_alvo,
                     'segundos': round(time.monotonic() - inicio, 2)}
            print(json.dumps(linha), flush=True)
            with open(out / 'progresso.jsonl', 'a') as f: f.write(json.dumps(linha) + '\n')
        if args.max_segundos and time.monotonic()-inicio >= args.max_segundos: limite = passo
        # Uma pausa operacional não é uma nova avaliação. A seleção e sua
        # paciência têm de ser iguais em execução contínua ou em blocos.
        if passo % args.avaliar_a_cada == 0 or passo == horizonte:
            resultado = avaliar(modelo, corpus, args.dispositivo, humanos=args.selecao_humana)
            historico.append({'passo': passo, 'avaliacao': resultado})
            if args.validacao_funcional: historico[-1]['funcional'] = medir_funcional()
            print(json.dumps({'passo': passo, 'avaliacao': resultado}), flush=True)
            if args.selecionar_melhor:
                valor = pontuacao_validacao(historico[-1],args.fase,args.validacao_funcional,args.selecao_humana)
                if valor > melhor_pontuacao:
                    melhor_pontuacao = valor; sem_melhora = 0
                    salvar(out / 'melhor')
                else:
                    sem_melhora += 1
                if args.paciencia_validacoes and sem_melhora >= args.paciencia_validacoes:
                    parou_validacao = True
                    salvar()
                    ultimo_salvo = passo
                    print(json.dumps(dict(parada_validacao=True, passo=passo, melhor_pontuacao=melhor_pontuacao)), flush=True)
                    break
        if passo % args.salvar_a_cada == 0 or passo == limite:
            salvar()
            ultimo_salvo = passo
    if ultimo_salvo != passo:
        salvar()
    print(json.dumps({'concluido': passo >= args.passos, 'pausado': passo < args.passos and not parou_validacao, 'parada_validacao': parou_validacao,
                      'passo': passo, 'tokens_alvo': tokens_alvo,
                      'saida': str(out)}), flush=True)


if __name__ == '__main__': main()
