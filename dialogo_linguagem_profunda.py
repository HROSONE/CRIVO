"""Adaptador opcional do candidato causal ao chat; sem cache de conversas."""
from functools import lru_cache
from pathlib import Path
import hashlib


def _sha(caminho):
    h = hashlib.sha256()
    with open(caminho, 'rb') as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloco)
    return h.hexdigest()


@lru_cache(maxsize=2)
def _carregar(pasta, assinatura_pesos, assinatura_tokenizer):
    """Carrega checkpoints atuais e a exportação legada do leitor 17M.

    A exportação original do leitor foi feita antes do campo ``versao`` ser
    adicionado a ``linguagem_profunda.carregar``. Ela continua segura: exige
    o SHA exato dos pesos/tokenizer conhecidos, metadados autorais e a
    arquitetura 8192/384/8/8/256 antes de instanciar o modelo.
    """
    from linguagem_profunda import carregar
    import torch
    torch.set_num_threads(3)
    try:
        return carregar(pasta)
    except KeyError as exc:
        if exc.args != ('versao',):
            raise

    from tokenizers import Tokenizer
    from linguagem_profunda import Configuracao, LinguagemProfunda
    from motor_dialogo_17m import PESOS_SHA256, TOKENIZER_SHA256
    pasta = Path(pasta)
    pesos = pasta / 'pesos.pt'
    tokenizer_path = pasta / 'tokenizer.json'
    if _sha(pesos) != PESOS_SHA256 or _sha(tokenizer_path) != TOKENIZER_SHA256:
        raise ValueError('Export legado não corresponde à base Transformer 17M aprovada')
    estado = torch.load(pesos, map_location='cpu', weights_only=True)
    if estado.get('passo') != 20000 or estado.get('execucao', {}).get('pesos_externos') is not False:
        raise ValueError('Metadados incompatíveis com a base Transformer 17M')
    esperado = {'vocabulario': 8192, 'dimensao': 384, 'camadas': 8,
                'cabecas': 8, 'contexto': 256, 'dropout': 0.1}
    if estado.get('config') != esperado:
        raise ValueError('Arquitetura incompatível com a base Transformer 17M')
    if estado.get('execucao', {}).get('tokenizer_sha256') != TOKENIZER_SHA256:
        raise ValueError('Tokenizador incompatível com a base Transformer 17M')
    modelo = LinguagemProfunda(Configuracao(**estado['config']))
    modelo.load_state_dict(estado['modelo'])
    if sum(p.numel() for p in modelo.parameters()) != 17428224:
        raise ValueError('Contagem de parâmetros inesperada na base Transformer 17M')
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    tokenizer.encode_special_tokens = True
    modelo.eval()
    return modelo, tokenizer, estado


def carregar_modelo(pasta):
    pasta = Path(pasta).resolve()
    if not (pasta / 'pesos.pt').exists() and (pasta / 'pesos_numpy.npz').exists():
        from gerador_dialogo_numpy import carregar
        modelo = carregar(pasta)
        return modelo, None, {'passo': modelo.modelo.meta['passo']}
    arquivos = [pasta / 'pesos.pt', pasta / 'tokenizer.json']
    assinaturas = [(p.stat().st_mtime_ns, p.stat().st_size) for p in arquivos]
    return _carregar(str(pasta), *assinaturas)


def responder(pasta, mensagem, historico):
    if not (Path(pasta) / 'pesos.pt').exists() and (Path(pasta) / 'pesos_numpy.npz').exists():
        from gerador_dialogo_numpy import carregar
        return carregar(pasta).responder(mensagem, historico)
    from linguagem_profunda import ESPECIAIS, fonte_dialogo
    from geracao_incremental import gerar
    modelo, tokenizer, estado = carregar_modelo(pasta)
    fonte = fonte_dialogo(tokenizer, mensagem, historico, modelo.config.contexto)
    ids, terminou = gerar(modelo, fonte, tokenizer.token_to_id('<fim>'), max_tokens=160,
        temperatura=.7, semente=42,
        proibidos=[tokenizer.token_to_id(t) for t in ESPECIAIS[:-1]])
    return {'texto': tokenizer.decode(ids), 'completa': terminou,
            'tokens': len(ids), 'passo': estado['passo'], 'modelo': 'transformer_leitor_17m'}


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
