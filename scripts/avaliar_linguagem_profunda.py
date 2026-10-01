"""Teste reservado e amostras integrais do candidato causal, sem ajustar pesos.

Perplexidade mede previsão de tokens com prefixos reais; amostras livres são
registradas separadamente e exigem revisão de conteúdo e contexto.
"""
import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
from linguagem_profunda import carregar, fonte_dialogo, ESPECIAIS
from geracao_incremental import gerar
from scripts.treinar_linguagem_profunda import Corpus, sha


@torch.no_grad()
def avaliar_completo(modelo, corpus, dispositivo, split='teste', lote=8):
    modelo.eval()
    resultado = {}
    seq = corpus.linguagem[split]
    contexto = modelo.config.contexto
    soma, tokens, corretos = 0., 0, 0
    for primeiro in range(0, len(seq) - 1, contexto * lote):
        xs, ys = [], []
        for i in range(primeiro, min(len(seq) - 1, primeiro + contexto * lote), contexto):
            x = np.asarray(seq[i:i + contexto],dtype=np.int64)
            y = np.asarray(seq[i + 1:i + contexto + 1],dtype=np.int64)
            n = len(y)
            xs.append(np.pad(x[:n], (0,contexto - n)))
            ys.append(np.pad(y, (0,contexto - n), constant_values=-100))
        x = torch.tensor(np.stack(xs),device=dispositivo)
        y = torch.tensor(np.stack(ys),device=dispositivo)
        logits, perda = modelo(x,y)
        n = int((y != -100).sum()); soma += float(perda) * n; tokens += n
        corretos += int(((logits.argmax(-1) == y) & (y != -100)).sum())
    ce = soma / tokens
    resultado['linguagem'] = {'tokens':tokens, 'entropia_cruzada':ce,
                             'perplexidade':math.exp(ce),'acuracia_token':corretos/tokens}
    soma, tokens, corretos = 0., 0, 0
    for i in range(0,len(corpus.x[split]),lote):
        x = torch.tensor(np.asarray(corpus.x[split][i:i+lote],dtype=np.int64),device=dispositivo)
        y = torch.tensor(np.asarray(corpus.y[split][i:i+lote],dtype=np.int64),device=dispositivo)
        logits, perda = modelo(x,y)
        n = int((y != -100).sum()); soma += float(perda) * n; tokens += n
        corretos += int(((logits.argmax(-1) == y) & (y != -100)).sum())
    ce = soma / tokens
    resultado['dialogo_humano'] = {'tokens':tokens,'entropia_cruzada':ce,
                                 'perplexidade':math.exp(ce),'acuracia_token':corretos/tokens}
    return resultado


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modelo',required=True)
    p.add_argument('--corpus',required=True)
    p.add_argument('--saida',required=True)
    p.add_argument('--amostras',type=int,default=12)
    p.add_argument('--threads',type=int,default=3)
    args = p.parse_args()
    torch.set_num_threads(args.threads)
    modelo,tokenizer,estado = carregar(args.modelo)
    corpus = Corpus(args.corpus,modelo.config.contexto)
    if estado['execucao']['corpus'] != corpus.assinatura:
        raise ValueError('Teste não pertence ao corpus do treino')
    resultado = avaliar_completo(modelo,corpus,'cpu')
    pares = [json.loads(l) for l in (Path(args.corpus)/'dialogos_teste.jsonl').read_text().splitlines()]
    amostras, recusados = [], 0
    grupos = set()
    for ex in pares:
        if ex['grupo'] in grupos or len(amostras) >= args.amostras:
            continue
        try:
            fonte = fonte_dialogo(tokenizer,ex['mensagem'],ex['historico'],modelo.config.contexto)
        except ValueError:
            recusados += 1; continue
        grupos.add(ex['grupo'])
        ids,fim = gerar(modelo,fonte,tokenizer.token_to_id('<fim>'),max_tokens=160,
            temperatura=.7,semente=42,
            proibidos=[tokenizer.token_to_id(t) for t in ESPECIAIS[:-1]])
        amostras.append(dict(ex, gerado=tokenizer.decode(ids), completa=fim,
                            tokens_gerados=len(ids)))
    report = {'versao':1,'modelo_sha256':sha(Path(args.modelo)/'pesos.pt'),
        'corpus_sha256':corpus.assinatura,'passo':estado['passo'],
        'fase':estado['execucao']['fase'],'particao':'teste',
        'avaliacao_completa':resultado,'amostras_livres':amostras,
        'pedidos_acima_contexto_recusados':recusados,
        'limites':['Métricas de tokens não certificam diálogo coerente ou compreensão.',
                   'Amostras preservam erros do modelo e requerem revisão humana.',
                   'Textos públicos não são automaticamente fatos verificados do Crivo.']}
    Path(args.saida).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'avaliacao':resultado,'amostras':len(amostras),'saida':args.saida},ensure_ascii=False))


if __name__ == '__main__': main()
