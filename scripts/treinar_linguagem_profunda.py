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


class Corpus:
    def __init__(self, caminho, contexto, conferir=True):
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
        self.contexto = contexto

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
            if split == 'treino' and len(self.humanos[split]) and len(self.sinteticos[split]):
                # Metade do lote humano; contar janelas sintéticas como humanos
                # ou deixar 10 mil padrões dominarem centenas de árvores é errado.
                indices = np.concatenate([rng.choice(self.humanos[split], tamanho // 2),
                    rng.choice(self.sinteticos[split], tamanho - tamanho // 2)])
                rng.shuffle(indices)
            else:
                indices = rng.integers(0, n, size=tamanho)
            x = np.asarray(self.x[split][indices], dtype=np.int64)
            y = np.asarray(self.y[split][indices], dtype=np.int64)
        return torch.from_numpy(x).to(dispositivo), torch.from_numpy(y).to(dispositivo)


@torch.no_grad()
def avaliar(modelo, corpus, dispositivo, split='validacao', lotes=12, tamanho=8):
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
    p.add_argument('--retomar', action='store_true')
    p.add_argument('--parar-em', type=int, help='Pausa planejada sem mudar o horizonte do LR')
    p.add_argument('--ajustar-proprio', action='store_true', help='Permite novo corpus com o mesmo tokenizer/configuração; registra linhagem')
    p.add_argument('--inicial', help='Diretório do pré-treino próprio para iniciar SFT')
    p.add_argument('--dispositivo', default='cuda' if torch.cuda.is_available() else 'cpu')
    args = p.parse_args()
    if min(args.passos, args.lote, args.threads, args.avaliar_a_cada, args.salvar_a_cada) < 1:
        p.error('Contagens devem ser positivas')
    if not 0 <= args.repeticao_linguagem < 1 or args.lr <= 0:
        p.error('Taxa de aprendizado/repetição inválida')
    if args.ajustar_proprio and not (args.inicial or args.retomar): p.error('--ajustar-proprio requer --inicial ou --retomar')
    if args.retomar and args.inicial: p.error('Escolha retomada ou inicialização de uma etapa')
    if args.fase == 'dialogo' and not args.retomar and not args.inicial:
        p.error('SFT requer --inicial com pré-treino próprio')
    torch.set_num_threads(args.threads)
    torch.manual_seed(args.semente)
    rng = np.random.default_rng(args.semente)
    corpus = Corpus(args.corpus, args.contexto)
    config = Configuracao(vocabulario=corpus.manifesto['vocabulario'], dimensao=args.dimensao,
              camadas=args.camadas, cabecas=args.cabecas, contexto=args.contexto)
    assinatura, dados = assinatura_execucao(config, corpus, args.fase, args.lote, args.lr,
                                            args.semente, args.repeticao_linguagem)
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
        resultado = avaliar(modelo, corpus, args.dispositivo)
        historico.append({'passo': passo, 'avaliacao': resultado})
        print(json.dumps({'baseline': resultado, 'parametros': parametros}), flush=True)
    def salvar():
        estado = estado_checkpoint(modelo, otimizador, rng, passo, assinatura, dados,
                    historico, tokens_entrada, tokens_alvo, horizonte, inicial)
        salvar_atomico(estado, out / 'checkpoint.pt')
        campos = ('versao', 'config', 'modelo', 'passo', 'execucao', 'tokens_entrada', 'tokens_alvo', 'inicial')
        salvar_atomico({k: estado[k] for k in campos}, out / 'pesos.pt')
        relatorio = {k: v for k, v in estado.items() if k not in
                     ('modelo', 'otimizador', 'rng_numpy', 'rng_torch', 'rng_cuda')}
        relatorio.update(parametros=parametros, pesos_sha256=sha(out / 'pesos.pt'),
            segundos_esta_execucao=round(time.monotonic() - inicio, 2),
            passos_esta_execucao=passo - passo_inicio, inicializacao='aleatoria_do_zero' if not inicial else 'pretreino_proprio',
            versao_torch=torch.__version__, dispositivo=args.dispositivo)
        tmp = out / 'relatorio.json.tmp'
        tmp.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + '\n')
        os.replace(tmp, out / 'relatorio.json')
    limite = min(args.passos, args.parar_em) if args.parar_em is not None else args.passos
    if limite < passo: p.error('Pausa anterior ao checkpoint atual')
    while passo < limite:
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
        perda = modelo(x, y)[1]
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
        if passo % args.avaliar_a_cada == 0 or passo == limite:
            resultado = avaliar(modelo, corpus, args.dispositivo)
            historico.append({'passo': passo, 'avaliacao': resultado})
            print(json.dumps({'passo': passo, 'avaliacao': resultado}), flush=True)
        if passo % args.salvar_a_cada == 0 or passo == limite:
            salvar()
    salvar()
    print(json.dumps({'concluido': passo >= args.passos, 'pausado': passo < args.passos,
                      'passo': passo, 'tokens_alvo': tokens_alvo,
                      'saida': str(out)}), flush=True)


if __name__ == '__main__': main()
