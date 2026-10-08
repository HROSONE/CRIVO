"""Ajuste contrastivo do leitor próprio já treinado; nunca pré-treina do zero."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys
import time

import numpy as np
import torch
from torch import nn


def sha256(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def carregar(origem, dispositivo):
    from linguagem_profunda import Configuracao, LinguagemProfunda
    from pontuador_frases import BPE
    origem = Path(origem)
    meta = json.loads((origem / 'meta.json').read_text(encoding='utf-8'))
    with np.load(origem / 'pesos_numpy.npz', allow_pickle=False) as z:
        config = json.loads(str(z['meta'].item()))
        chaves = ('vocabulario', 'dimensao', 'camadas', 'cabecas', 'contexto', 'dropout')
        cfg = Configuracao(**{k: config[k] for k in chaves})
        if config['tokenizer_sha256'] != sha256(origem / 'tokenizer.json'):
            raise ValueError('Tokenizador não corresponde aos pesos existentes.')

        class Leitor(nn.Module):
            def __init__(self):
                super().__init__()
                self.base = LinguagemProfunda(cfg)
                self.cabeca = nn.Linear(cfg.dimensao, 1)

            def forward(self, ids, ultimos):
                b = self.base
                x = b.embedding(ids) + b.posicao(torch.arange(ids.shape[1], device=ids.device))
                for bloco in b.blocos:
                    x = bloco(x)
                x = b.norm(x)
                return self.cabeca(x[torch.arange(len(ids), device=ids.device), ultimos]).squeeze(-1)

        modelo = Leitor()
        estado = {}
        for nome, tensor in modelo.state_dict().items():
            chave = nome[5:] if nome.startswith('base.') else nome
            if chave not in z or tuple(z[chave].shape) != tuple(tensor.shape):
                raise ValueError('Peso ausente ou formato incompatível: ' + chave)
            estado[nome] = torch.from_numpy(np.array(z[chave], dtype=np.float32, copy=True))
        modelo.load_state_dict(estado, strict=True)
    return modelo.to(dispositivo), BPE(origem / 'tokenizer.json'), meta


def configurar_ajuste(modelo, camadas):
    if not 1 <= camadas <= len(modelo.base.blocos):
        raise ValueError('Número de camadas inválido.')
    for parametro in modelo.parameters():
        parametro.requires_grad_(False)
    for modulo in list(modelo.base.blocos[-camadas:]) + [modelo.base.norm, modelo.cabeca]:
        for parametro in modulo.parameters():
            parametro.requires_grad_(True)


def modo_treino(modelo, camadas):
    modelo.train()
    for bloco in modelo.base.blocos[:-camadas]:
        bloco.eval()


def perda_grupo(logits, alvo):
    # Fatos da MESMA ficha competem; zero representa "nenhum responde".
    alvo_rank = len(logits) if alvo is None else alvo
    ranking = torch.nn.functional.cross_entropy(
        torch.cat([logits, logits.new_zeros(1)])[None],
        torch.tensor([alvo_rank], device=logits.device))
    y = torch.zeros_like(logits)
    if alvo is not None:
        y[alvo] = 1
    binaria = torch.nn.functional.binary_cross_entropy_with_logits(
        logits, y, pos_weight=logits.new_tensor(max(1, min(4, len(logits) - 1))))
    return ranking + .5 * binaria


def atualizar(modelo, bpe, grupos, rng, opt, lote, camadas, dispositivo):
    from scripts.treinar_leitor_transformer import lote_tensores
    positivos, negativos = grupos
    if not positivos or not negativos:
        raise ValueError('Treino exige exemplos respondíveis e sem resposta.')
    amostra = [rng.choice(negativos if rng.random() < .25 else positivos) for _ in range(lote)]
    pares, limites = [], []
    for pergunta, fatos, alvo in amostra:
        ini = len(pares)
        pares.extend((pergunta, fato) for fato in fatos)
        limites.append((ini, len(pares), alvo))
    ids, ultimos = lote_tensores(pares, bpe, modelo.base.config.contexto, dispositivo)
    modo_treino(modelo, camadas)
    opt.zero_grad(set_to_none=True)
    logits = modelo(ids, ultimos)
    perda = torch.stack([perda_grupo(logits[a:b], alvo) for a, b, alvo in limites]).mean()
    if not torch.isfinite(perda):
        raise RuntimeError('Perda não finita; treino interrompido.')
    perda.backward()
    torch.nn.utils.clip_grad_norm_([p for p in modelo.parameters() if p.requires_grad], 1.)
    opt.step()
    return float(perda.detach())


def gravar_checkpoint(caminho, modelo, opt, rng, passo, assinatura, melhor):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    estado = {'modelo': modelo.state_dict(), 'otimizador': opt.state_dict(),
              'rng_python': rng.getstate(), 'rng_torch': torch.get_rng_state(),
              'rng_cuda': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
              'passo': passo, 'assinatura': assinatura, 'melhor': melhor}
    temporario = caminho.with_suffix('.tmp')
    torch.save(estado, temporario)
    temporario.replace(caminho)


def retomar(caminho, modelo, opt, rng, assinatura):
    estado = torch.load(caminho, map_location='cpu', weights_only=True)
    if estado['assinatura'] != assinatura:
        raise ValueError('Checkpoint de outro código, corpus, pesos ou configuração. Use outra pasta.')
    modelo.load_state_dict(estado['modelo'], strict=True)
    opt.load_state_dict(estado['otimizador'])
    rng.setstate(estado['rng_python'])
    torch.set_rng_state(estado['rng_torch'])
    if estado['rng_cuda']:
        if not torch.cuda.is_available():
            raise ValueError('Checkpoint de GPU exige GPU para a continuação.')
        torch.cuda.set_rng_state_all(estado['rng_cuda'])
    return estado['passo'], estado['melhor']


def exportar(modelo, origem, saida, meta_original, passo, metricas, baseline):
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(origem) / 'tokenizer.json', saida / 'tokenizer.json')
    config = vars(modelo.base.config).copy()
    config.update(passo=passo, tokenizer_sha256=sha256(saida / 'tokenizer.json'))
    pesos = {k: v.detach().float().cpu().numpy().astype(np.float16)
             for k, v in modelo.base.state_dict().items()}
    pesos['cabeca.weight'] = modelo.cabeca.weight.detach().float().cpu().numpy()
    pesos['cabeca.bias'] = modelo.cabeca.bias.detach().float().cpu().numpy()
    np.savez_compressed(saida / 'pesos_numpy.npz', meta=np.array(json.dumps(config)), **pesos)
    meta = json.loads(json.dumps(meta_original))
    meta['validacao_tutor'] = metricas
    meta['ajuste_contrastivo'] = {'passos_adicionais': passo, 'baseline_tutor': baseline,
                                'origem_sha256': sha256(Path(origem) / 'pesos_numpy.npz'),
                                'objetivo': 'ranking de fatos da mesma ficha e nenhuma resposta'}
    meta['controle'] = {'aprovado': False, 'criterio': 'Requer ganho no controle e testes congelados.'}
    (saida / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', required=True)
    ap.add_argument('--origem', required=True)
    ap.add_argument('--saida', required=True)
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--passos', type=int, default=1000)
    ap.add_argument('--lote', type=int, default=4, help='Perguntas por passo, com todos os fatos de cada ficha')
    ap.add_argument('--camadas', type=int, default=2)
    ap.add_argument('--lr', type=float, default=1e-5)
    ap.add_argument('--avaliar-a-cada', type=int, default=200)
    ap.add_argument('--checkpoint-a-cada', type=int, default=100)
    ap.add_argument('--max-horas', type=float, default=1.5)
    ap.add_argument('--dispositivo', default='cuda')
    args = ap.parse_args()
    if min(args.passos, args.lote, args.avaliar_a_cada, args.checkpoint_a_cada) <= 0:
        ap.error('Passos, lote e intervalos devem ser positivos.')
    if args.dispositivo == 'cuda' and not torch.cuda.is_available():
        ap.error('Selecione GPU no Colab.')
    sys.path.insert(0, str(Path(args.repo).resolve()))
    sys.path.insert(0, str(Path(args.repo).resolve() / 'scripts'))
    from scripts.treinar_leitor_transformer import exemplos_sinteticos, exemplos_tutor, avaliar
    from crivo import Crivo
    torch.set_num_threads(2)
    torch.manual_seed(20261008)
    comp = Crivo().compositor
    grupos = exemplos_sinteticos(comp, random.Random(20261008))
    validacao = exemplos_tutor(comp)
    # Usa os mesmos assuntos excluídos do treinador original; tutor/congelados nunca treinam.
    modelo, bpe, meta_original = carregar(args.origem, args.dispositivo)
    configurar_ajuste(modelo, args.camadas)
    opt = torch.optim.AdamW([p for p in modelo.parameters() if p.requires_grad], lr=args.lr, weight_decay=.01)
    rng = random.Random(20261008)
    corpus_sha = hashlib.sha256(json.dumps([grupos, validacao], ensure_ascii=False).encode()).hexdigest()
    assinatura = {'origem': sha256(Path(args.origem) / 'pesos_numpy.npz'),
                  'tokenizador': sha256(Path(args.origem) / 'tokenizer.json'),
                  'codigo': sha256(__file__), 'corpus': corpus_sha,
                  'lr': args.lr, 'lote': args.lote, 'camadas': args.camadas,
                  'dispositivo': args.dispositivo, 'torch': str(torch.__version__),
                  'modelo': sha256(Path(args.repo) / 'linguagem_profunda.py'),
                  'sequencia': sha256(Path(args.repo) / 'leitor_transformer.py'),
                  'treinador_base': sha256(Path(args.repo) / 'scripts/treinar_leitor_transformer.py')}
    grupos = ([g for g in grupos if g[2] is not None], [g for g in grupos if g[2] is None])
    saida = Path(args.saida)
    baseline_path = saida / 'baseline.json'
    saida.mkdir(parents=True, exist_ok=True)
    checkpoint = Path(args.checkpoint)
    if checkpoint.exists():
        if not baseline_path.exists() or not (saida / 'melhor' / 'pesos_numpy.npz').exists():
            raise ValueError('Checkpoint sem baseline ou melhor candidato; restaure a pasta completa.')
        baseline = json.loads(baseline_path.read_text())
        passo, melhor = retomar(checkpoint, modelo, opt, rng, assinatura)
    else:
        baseline = avaliar(modelo, bpe, modelo.base.config.contexto, validacao, args.dispositivo)
        baseline_path.write_text(json.dumps(baseline, indent=2) + '\n')
        passo, melhor = 0, baseline
        exportar(modelo, args.origem, saida / 'melhor', meta_original, 0, baseline, baseline)
    if passo > args.passos:
        raise ValueError('O checkpoint já ultrapassou o horizonte solicitado.')
    print('Base existente:', meta_original['base']['passo_pretreino'], 'passos de pré-treino; mantida.', flush=True)
    print('Baseline tutor:', baseline, '| retomando ajuste no passo', passo, flush=True)
    inicio, passo_inicial = time.monotonic(), passo
    tempo_treino = 0.
    while passo < args.passos:
        inicio_passo = time.monotonic()
        perda = atualizar(modelo, bpe, grupos, rng, opt, args.lote, args.camadas, args.dispositivo)
        tempo_treino += time.monotonic() - inicio_passo
        passo += 1
        fim_tempo = args.max_horas > 0 and time.monotonic() - inicio >= args.max_horas * 3600
        if passo % 20 == 0:
            seg = tempo_treino / max(1, passo - passo_inicial)
            print('passo %d/%d perda %.4f | %.2fs/passo | treino restante ~%.1fmin (avaliações à parte)' %
                  (passo, args.passos, perda, seg, (args.passos - passo) * seg / 60), flush=True)
        if passo % args.avaliar_a_cada == 0 or passo == args.passos or fim_tempo:
            metricas = avaliar(modelo, bpe, modelo.base.config.contexto, validacao, args.dispositivo)
            print('Validação tutor:', metricas, flush=True)
            sem_regressao = all(metricas[k] >= baseline[k] for k in ('acerto_fato', 'auc_respondivel'))
            if sem_regressao and sum(metricas[k] for k in ('acerto_fato', 'auc_respondivel')) > sum(
                    melhor[k] for k in ('acerto_fato', 'auc_respondivel')):
                melhor = metricas
                exportar(modelo, args.origem, saida / 'melhor', meta_original, passo, metricas, baseline)
        if passo % args.checkpoint_a_cada == 0 or passo == args.passos or fim_tempo:
            gravar_checkpoint(checkpoint, modelo, opt, rng, passo, assinatura, melhor)
            print('Checkpoint único gravado:', passo, flush=True)
        if fim_tempo:
            print('Pausado por tempo; execute esta célula novamente para continuar.', flush=True)
            break
    relatorio = {'baseline': baseline, 'melhor_tutor': melhor, 'passos_adicionais': passo,
                 'concluido': passo == args.passos, 'aprovado': False, 'assinatura': assinatura}
    (saida / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(relatorio, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
