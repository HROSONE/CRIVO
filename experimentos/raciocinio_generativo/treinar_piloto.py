"""Ajusta pesos próprios em resposta direta e passos; teste só após seleção dev."""
import argparse
import copy
import hashlib
import json
import random
import shutil
import sys
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
sys.path[:0] = [str(PASTA), str(RAIZ), str(RAIZ / 'scripts')]
from piloto import STATUS, assinatura, contexto, corpus, exemplos_passos, executar, ler_literal, ler_premissa


def avaliar(modelo, bpe, casos, modo):
    import torch
    from pontuador_frases import _bytes_unicode
    vocab = {i: t for t, i in bpe.vocab.items()}
    bytes_ = {c: b for b, c in _bytes_unicode().items()}
    esp = bpe.especiais

    def gerar(texto):
        prompt = [esp['<documento>']] + bpe.codificar(texto) + [esp['<assistente>']]
        if len(prompt) + 40 > modelo.config.contexto:
            raise ValueError('Contexto excedido; não truncar evidências.')
        ids, fim = modelo.gerar(prompt, esp['<fim>'], max_tokens=40, temperatura=0,
                               proibidos=[esp[t] for t in ('<pad>', '<documento>', '<usuario>', '<assistente>')])
        texto = ''.join(vocab[i] for i in ids if i not in esp.values())
        return bytes(bytes_[c] for c in texto if c in bytes_).decode('utf-8', 'replace').strip() if fim else ''

    linhas = []
    for c in casos:
        if modo == 'passos':
            r = executar(c, gerar)
        else:
            t = gerar(contexto(c, [], 'resposta')).rstrip('.')
            r = dict(status=t if t in STATUS else None, passos=[], saidas=[t], motivo='resposta_direta')
        correto = r['status'] == c['status']
        fatos = [ler_premissa(p).consequente for p in c['premissas'] if not ler_premissa(p).antecedentes]
        fatos += [ler_literal(p['conclusao']) for p in r['passos']]
        alvo = ler_literal(c['objetivo'])
        necessario = c['status'] in ('sustentado', 'refutado')
        desejado = alvo if c['status'] == 'sustentado' else alvo.oposto()
        completo = assinatura(desejado) in {assinatura(f) for f in fatos}
        # Modelo direto tem classificação, não prova. Seu acerto é relatado
        # separadamente; não imputar prova que ele não produziu.
        r.update(id=c['id'], esperado=c['status'], correto=correto,
                 prova_completa=correto and completo if necessario else None,
                 contrato=correto and (not necessario or completo),
                 ood_estrutura=c['ood_estrutura'], profundidade=c['profundidade'], modo=c['modo'])
        linhas.append(r)
    def resumir(ls):
        necessarias = [r for r in ls if r['prova_completa'] is not None]
        return dict(n=len(ls), classificacoes_corretas=sum(r['correto'] for r in ls),
                    contratos_completos=sum(r['contrato'] for r in ls),
                    provas_necessarias=len(necessarias), provas_completas=sum(bool(r['prova_completa']) for r in necessarias),
                    passos_aceitos=sum(len(r['passos']) for r in ls),
                    falhas_protocolo=sum(r['motivo'] == 'protocolo_invalido' for r in ls))
    return dict(total=resumir(linhas), ood=resumir([r for r in linhas if r['ood_estrutura']]),
                por_modo={m: resumir([r for r in linhas if r['modo'] == m]) for m in ('positivo','negativo','ausente','conflito')},
                casos=linhas)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--saida', type=Path, required=True)
    ap.add_argument('--passos', type=int, default=400)
    ap.add_argument('--lote', type=int, default=6)
    ap.add_argument('--lr', type=float, default=0.00015)
    ap.add_argument('--avaliar-a-cada', type=int, default=100)
    args = ap.parse_args()
    if args.passos < 1 or args.lote < 1 or args.avaliar_a_cada < 1 or args.lr <= 0:
        ap.error('Passos, lote, intervalo e taxa de aprendizagem devem ser positivos.')
    producao = (RAIZ / 'artefatos').resolve()
    destino = args.saida.resolve()
    if destino == producao or producao in destino.parents:
        ap.error('O piloto não pode gravar na pasta de artefatos de produção.')
    import numpy as np
    import torch
    from pontuador_frases import BPE
    from treinar_codificador_sentido import construir
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    dados, hashes = corpus()
    args.saida.mkdir(parents=True, exist_ok=True)
    # Manifests e teste ficam congelados em disco antes de otimizar.
    for s, casos in dados.items():
        (args.saida / (s + '.json')).write_text(json.dumps(casos, ensure_ascii=False, indent=2) + '\n')
    (args.saida / 'manifest.json').write_text(json.dumps(hashes, indent=2) + '\n')
    base = RAIZ / 'artefatos/geracao_pt'
    bpe = BPE(base / 'tokenizer.json')
    esp = bpe.especiais
    resultados = dict(corpus_sha256=hashes, configuracao=vars(args).copy(), modelos={},
                      base_sha256=hashlib.sha256((base / 'pesos_numpy.npz').read_bytes()).hexdigest(),
                      torch=torch.__version__, numpy=np.__version__, semente=8104)
    resultados['configuracao']['saida'] = str(args.saida)
    for modo in ('direto', 'passos'):
        torch.manual_seed(8104)
        rng = random.Random(8104)
        modelo, cfg = construir(base)
        exemplos = ([e for c in dados['treino'] for e in exemplos_passos(c)] if modo == 'passos' else
                    [(contexto(c, [], 'resposta'), c['status']) for c in dados['treino']])
        seqs = []
        for p, a in exemplos:
            prompt = [esp['<documento>']] + bpe.codificar(p) + [esp['<assistente>']]
            alvo = bpe.codificar(a) + [esp['<fim>']]
            if len(prompt) + len(alvo) > cfg['contexto']:
                raise ValueError('Exemplo excede contexto.')
            seqs.append((prompt, alvo))
        antes = avaliar(modelo, bpe, dados['dev'], modo)
        print(modo, 'antes', antes['total'], flush=True)
        opt = torch.optim.AdamW(modelo.parameters(), lr=args.lr, weight_decay=0.01)
        historico, melhor, melhor_estado = [], None, None
        inicio = time.monotonic()
        tokens_alvo = tokens_contexto = 0
        for passo in range(1, args.passos + 1):
            modelo.train()
            lote = [seqs[rng.randrange(len(seqs))] for _ in range(args.lote)]
            largura = max(len(p) + len(a) for p, a in lote)
            x = torch.zeros((len(lote), largura), dtype=torch.long)
            y = torch.full_like(x, -100)
            for i, (p, a) in enumerate(lote):
                s = p + a
                x[i, :len(s)] = torch.tensor(s)
                y[i, len(p)-1:len(s)-1] = torch.tensor(a)
                tokens_alvo += len(a)
                tokens_contexto += len(p)
            opt.zero_grad()
            _, perda = modelo(x, y)
            perda.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.)
            opt.step()
            if passo % 25 == 0:
                print(modo, 'passo', passo, 'perda', round(float(perda.detach()), 4),
                      'segundos', round(time.monotonic()-inicio, 1), flush=True)
            if passo % args.avaliar_a_cada == 0 or passo == args.passos:
                dev = avaliar(modelo, bpe, dados['dev'], modo)
                t = dev['total']
                pontuacao = ((t['contratos_completos'], t['classificacoes_corretas']) if modo == 'passos' else
                             (t['classificacoes_corretas'], 0))
                historico.append(dict(passo=passo, dev=t, perda=float(perda.detach())))
                print(modo, 'dev', passo, t, flush=True)
                if melhor is None or pontuacao > melhor:
                    melhor, melhor_passo = pontuacao, passo
                    melhor_estado = copy.deepcopy(modelo.state_dict())
        modelo.load_state_dict(melhor_estado)
        pasta = args.saida / modo
        pasta.mkdir(exist_ok=True)
        np.savez_compressed(pasta / 'pesos_numpy.npz', **{k:v.cpu().numpy().astype(np.float16) for k,v in melhor_estado.items()})
        shutil.copyfile(base / 'tokenizer.json', pasta / 'tokenizer.json')
        meta = dict(base=dict(config=cfg), controle=dict(aprovado=False),
                    papel='piloto de ' + modo, corpus_sha256=hashes,
                    treino=dict(passos=args.passos, melhor_passo=melhor_passo, exemplos=len(exemplos),
                                tokens_alvo=tokens_alvo, tokens_contexto=tokens_contexto, lr=args.lr,
                                lote=args.lote, semente=8104), pesos_externos=False)
        (pasta / 'meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')
        # Avaliar os pesos exportados em FP16, recarregados em FP32 como no executor.
        modelo, _ = construir(pasta)
        resultados['modelos'][modo] = dict(antes_dev=antes, historico=historico,
                                          escolhido=melhor_passo, meta=meta,
                                          dev=avaliar(modelo,bpe,dados['dev'],modo),
                                          teste=avaliar(modelo,bpe,dados['teste'],modo))
        (args.saida / 'resultado.json').write_text(json.dumps(resultados, ensure_ascii=False, indent=2) + '\n')
        print(modo, 'TESTE', resultados['modelos'][modo]['teste']['total'], flush=True)
    print('Concluído:', args.saida / 'resultado.json', flush=True)


if __name__ == '__main__':
    main()
