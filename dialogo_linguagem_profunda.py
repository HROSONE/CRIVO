"""Adaptador opcional do candidato causal ao chat; sem cache de conversas."""
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=2)
def _carregar(pasta, assinatura_pesos, assinatura_tokenizer):
    from linguagem_profunda import carregar
    import torch
    torch.set_num_threads(3)
    return carregar(pasta)


def carregar_modelo(pasta):
    pasta = Path(pasta).resolve()
    arquivos = [pasta / 'pesos.pt', pasta / 'tokenizer.json']
    assinaturas = [(p.stat().st_mtime_ns, p.stat().st_size) for p in arquivos]
    return _carregar(str(pasta), *assinaturas)


def responder(pasta, mensagem, historico):
    from linguagem_profunda import ESPECIAIS, fonte_dialogo
    from geracao_incremental import gerar
    modelo, tokenizer, estado = carregar_modelo(pasta)
    fonte = fonte_dialogo(tokenizer, mensagem, historico, modelo.config.contexto)
    ids, terminou = gerar(modelo, fonte, tokenizer.token_to_id('<fim>'), max_tokens=160,
        temperatura=.7, semente=42,
        proibidos=[tokenizer.token_to_id(t) for t in ESPECIAIS[:-1]])
    return {'texto': tokenizer.decode(ids), 'completa': terminou,
            'tokens': len(ids), 'passo': estado['passo'], 'modelo': 'transformer_causal_do_zero'}


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo',required=True)
    parser.add_argument('--mensagem')
    args = parser.parse_args()
    if args.mensagem:
        print(json.dumps(responder(args.modelo,args.mensagem,[]),ensure_ascii=False))
    else:
        carregar_modelo(args.modelo)
        historico = []
        while True:
            try: mensagem = input('Você: ')
            except (EOFError,KeyboardInterrupt): break
            if mensagem.strip() == '/sair': break
            try: saida = responder(args.modelo,mensagem,historico)
            except ValueError as exc:
                print(str(exc));continue
            print('CRIVO experimental:',saida['texto'])
            historico.extend([{'papel':'usuario','texto':mensagem},
                              {'papel':'assistente','texto':saida['texto']}])
            historico = historico[-24:]
