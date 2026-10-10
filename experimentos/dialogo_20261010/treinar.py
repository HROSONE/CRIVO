"""Ajusta somente pesos próprios em corpus autoral; nunca aprova nem ativa."""
import argparse
import gzip
import hashlib
import json
import math
import sys
import time
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
sys.path.insert(0, str(ROOT))
import numpy as np
from dialogo_seq2seq import vocabulario_treino
from treinar_dialogo_seq2seq import (inicializar, lote, perda_gradientes, avaliar_perda,
                                    ler_corpus, checkpoint, assinatura)


def inicializar_proprio(base, treino, semente):
    vocabulario = vocabulario_treino(treino, limite=len(base['vocabulario']))
    p = inicializar(vocabulario, base['ocultos'], base['embeddings'], base['buckets'], semente)
    anteriores = {t: i for i, t in enumerate(base['vocabulario'])}
    for k in p:
        if k not in ('E', 'O', 'bo'):
            p[k] = np.asarray(base['pesos'][k], dtype='float32')
    antigos = {k: np.asarray(base['pesos'][k], dtype='float32') for k in ('E', 'O', 'bo')}
    for j, token in enumerate(vocabulario):
        if token in anteriores:
            i = anteriores[token]
            p['E'][j] = antigos['E'][i]
            p['O'][:, j] = antigos['O'][:, i]
            p['bo'][j] = antigos['bo'][i]
    parametros = sum(a.size for a in p.values())
    assert parametros <= base['treino']['parametros'], 'Não aumentar parâmetros'
    return p, vocabulario


def executar(epocas=12, semente=20261010):
    corpus = H / 'corpus.json'
    treino, validacao = ler_corpus(corpus, limite_fonte=192, limite_resposta=96)
    base_path = ROOT / 'rede_dialogo_seq2seq.json.gz'
    base = json.loads(gzip.decompress(base_path.read_bytes()))
    p, vocabulario = inicializar_proprio(base, treino, semente)
    indices = {t: i for i, t in enumerate(vocabulario)}
    config = {'epocas_max': epocas, 'semente': semente, 'lote': 32, 'taxa': .0008,
              'clip_gradiente': 5, 'paciencia': 4, 'fonte_tokens': 192, 'resposta_tokens': 96}
    inicial = avaliar_perda(p, validacao, indices, base['buckets'], 192, 96)
    melhor_valor, melhor, melhor_epoca = inicial['entropia_cruzada'], {k: a.copy() for k, a in p.items()}, 0
    m = {k: np.zeros_like(a) for k, a in p.items()}
    v = {k: np.zeros_like(a) for k, a in p.items()}
    rng = np.random.default_rng(semente)
    passo, sem_melhoria, historico = 0, 0, []
    inicio = time.monotonic()
    print('Parâmetros', sum(a.size for a in p.values()), 'treino', len(treino), 'validação', len(validacao), flush=True)
    for epoca in range(1, epocas + 1):
        ordem = rng.permutation(len(treino)).tolist()
        perda_total, tokens_total = 0., 0
        for inicio_lote in range(0, len(ordem), config['lote']):
            casos = [treino[i] for i in ordem[inicio_lote:inicio_lote + config['lote']]]
            batch = lote(casos, indices, base['buckets'], 192, 96)
            perda, grad = perda_gradientes(p, batch)
            if not math.isfinite(perda) or any(not np.isfinite(g).all() for g in grad.values()):
                raise ValueError('Perda/gradiente não finito')
            n = int(batch['mascara'].sum())
            perda_total += perda * n
            tokens_total += n
            escala = min(1., config['clip_gradiente'] / max(1e-12, math.sqrt(sum(float((g*g).sum()) for g in grad.values()))))
            passo += 1
            for k in p:
                g = grad[k] * escala
                m[k] = .9*m[k] + .1*g
                v[k] = .999*v[k] + .001*g*g
                p[k] -= config['taxa'] * (m[k] / (1 - .9**passo)) / (np.sqrt(v[k] / (1 - .999**passo)) + 1e-8)
        val = avaliar_perda(p, validacao, indices, base['buckets'], 192, 96)
        historico.append({'epoca': epoca, 'treino_entropia': perda_total / tokens_total, 'validacao': val})
        print('Época', epoca, 'treino', round(perda_total/tokens_total, 4), 'validação', round(val['entropia_cruzada'], 4), 'segundos', round(time.monotonic()-inicio, 1), flush=True)
        if val['entropia_cruzada'] < melhor_valor - 1e-5:
            melhor_valor, melhor_epoca = val['entropia_cruzada'], epoca
            melhor = {k: a.copy() for k, a in p.items()}
            sem_melhoria = 0
        else:
            sem_melhoria += 1
        if sem_melhoria >= config['paciencia']:
            break
    if melhor_epoca == 0:
        raise ValueError('O treino não melhorou a perda na validação; não salvar como checkpoint treinado.')
    meta = {'arquitetura': base['arquitetura'], 'controle': {'aprovado': False, 'ativo_no_chat': False},
            'base_sha256': hashlib.sha256(base_path.read_bytes()).hexdigest(),
            'corpus_sha256': hashlib.sha256(corpus.read_bytes()).hexdigest(),
            'casos_sha256': hashlib.sha256((H / 'casos_congelados.json').read_bytes()).hexdigest(),
            'assinatura_treino': assinatura(treino), 'assinatura_validacao': assinatura(validacao),
            'treino': dict(config, epoca_selecionada=melhor_epoca, epocas_executadas=len(historico),
                           parametros=sum(a.size for a in melhor.values()), exemplos=len(treino)),
            'limite': 'Ajuste supervisionado autoral; não aprovado para chat, não resolve conversa livre geral nem demonstra as metas da Fase 2.'}
    dados = checkpoint(melhor, vocabulario, base['ocultos'], base['embeddings'], base['buckets'], 192, **meta)
    destino = H / 'checkpoint_dialogo.json.gz'
    payload = json.dumps(dados, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    destino.write_bytes(gzip.compress(payload, mtime=0))
    relatorio = {'config': config, 'base_sha256': meta['base_sha256'], 'corpus_sha256': meta['corpus_sha256'],
                 'checkpoint_sha256': hashlib.sha256(destino.read_bytes()).hexdigest(),
                 'parametros_base': base['treino']['parametros'], 'parametros_novo': meta['treino']['parametros'],
                 'inicial_validacao': inicial, 'epoca_selecionada': melhor_epoca,
                 'historico': historico, 'segundos': round(time.monotonic()-inicio, 2),
                 'aprovado': False, 'numpy': np.__version__, 'python': sys.version.split()[0]}
    (H / 'treino.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + '\n')
    print('Checkpoint isolado salvo; aprovado=false; época', melhor_epoca, flush=True)
    return relatorio


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--epocas', type=int, default=12)
    parser.add_argument('--semente', type=int, default=20261010)
    args = parser.parse_args()
    executar(args.epocas, args.semente)
